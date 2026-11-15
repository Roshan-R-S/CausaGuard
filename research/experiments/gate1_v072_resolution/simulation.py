"""Comprehensive simulation engine comparing Gate 1 designs and statistical methods.

Evaluates:
- Horizons: K in {128, 256, 512, 1024}
- Risk regimes: theta in {0.005, 0.010, 0.020, 0.035, 0.0500, 0.0501, 0.0700}
- Damage models:
  1. Model A: Worst-case cluster shocks (Bernoulli R_k in {0, 1})
  2. Model B: Diffuse within-cluster harm (N=400 cases per cluster)
  3. Model C: Heterogeneous cluster means (front-loaded, back-loaded, exchangeable, safe mixture)
- Sensitivity to missing data (5%, 10% random cluster dropouts)
- Catastrophic cluster shock thresholds (Z_max)
- Computational runtime profiling

STATUS: EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy import stats

from research.experiments.gate1_v072_resolution import (
    ALPHA,
    BASE_EXPLORATORY_SEED,
    SAFETY_THRESHOLD,
)
from research.experiments.gate1_v072_resolution.evaluators import (
    eval_constant_betting,
    eval_direct_betting,
    eval_hoeffding,
    eval_maurer_pontil,
    eval_permutation_betting,
)


@dataclass(frozen=True)
class SimulationSummary:
    horizons: list[int]
    thetas_evaluated: list[float]
    model_a_results: dict[str, Any]
    model_b_results: dict[str, Any]
    model_c_heterogeneous_results: dict[str, Any]
    catastrophic_shock_thresholds: dict[str, Any]
    missingness_sensitivity: dict[str, Any]
    computational_latencies_microseconds: dict[str, float]


def compute_analytical_z_max(k: int, tau: float = SAFETY_THRESHOLD, alpha: float = ALPHA) -> dict[str, int]:
    """Computes exact Z_max (maximum number of R_k = 1.0 clusters tolerated)."""
    # 1. Maurer-Pontil Z_max
    log_mp = math.log(2.0 / alpha)
    z_max_mp = -1
    for z in range(k + 1):
        r_bar = z / k
        if z == 0:
            var_r = 0.0
        else:
            var_r = (z * (1.0 - r_bar) ** 2 + (k - z) * (0.0 - r_bar) ** 2) / (k - 1)
        ucb = r_bar + math.sqrt((2.0 * var_r * log_mp) / k) + (7.0 * log_mp) / (3.0 * (k - 1))
        if ucb <= tau:
            z_max_mp = z
        else:
            break

    # 2. Hoeffding Z_max
    log_hoeff = math.log(1.0 / alpha)
    z_max_hoeff = -1
    for z in range(k + 1):
        r_bar = z / k
        ucb = r_bar + math.sqrt(log_hoeff / (2.0 * k))
        if ucb <= tau:
            z_max_hoeff = z
        else:
            break

    # 3. Direct Betting Z_max (beginning-shock arrangement)
    z_max_bet_beg = -1
    for z in range(k + 1):
        x = np.zeros(k, dtype=np.float64)
        x[:z] = 1.0
        qual, _ = eval_direct_betting(x, tau=tau, alpha=alpha)
        if qual:
            z_max_bet_beg = z
        else:
            break

    # 4. Constant Betting Z_max (permutation-invariant by construction!)
    z_max_const = -1
    for z in range(k + 1):
        x = np.zeros(k, dtype=np.float64)
        x[:z] = 1.0
        qual, _, _ = eval_constant_betting(x, tau=tau, alpha=alpha, theta_alt=0.010)
        if qual:
            z_max_const = z
        else:
            break

    return {
        "maurer_pontil": z_max_mp,
        "hoeffding": z_max_hoeff,
        "direct_betting_beginning": z_max_bet_beg,
        "constant_betting": z_max_const,
    }


def run_power_and_fsq_benchmark(
    n_trials: int = 2000,
    seed: int = BASE_EXPLORATORY_SEED,
) -> SimulationSummary:
    """Executes the full comparative simulation across horizons and risk regimes."""
    rng = np.random.default_rng(seed)
    horizons = [128, 256, 512, 1024]
    thetas = [0.005, 0.010, 0.020, 0.035, 0.0500, 0.0501, 0.0700]
    n_cases_per_cluster = 400

    # 1. Model A: Worst-case Bernoulli Cluster Shocks
    model_a_data: dict[str, dict[str, dict[str, float]]] = {
        m: {f"K_{k}": {} for k in horizons}
        for m in ["maurer_pontil", "direct_betting", "constant_betting", "hoeffding"]
    }

    z_max_table: dict[str, dict[str, int]] = {}

    for k in horizons:
        z_max_info = compute_analytical_z_max(k)
        z_max_table[f"K_{k}"] = z_max_info

        for theta in thetas:
            # Analytical Binomial power where exact
            z_mp = z_max_info["maurer_pontil"]
            pw_mp = float(stats.binom.cdf(z_mp, k, theta)) if z_mp >= 0 else 0.0
            model_a_data["maurer_pontil"][f"K_{k}"][f"theta_{theta:.4f}"] = pw_mp

            z_hf = z_max_info["hoeffding"]
            pw_hf = float(stats.binom.cdf(z_hf, k, theta)) if z_hf >= 0 else 0.0
            model_a_data["hoeffding"][f"K_{k}"][f"theta_{theta:.4f}"] = pw_hf

            # Monte Carlo for Direct Betting and Constant Betting
            bet_passes = 0
            const_passes = 0
            for _ in range(n_trials):
                x = rng.binomial(1, theta, size=k).astype(np.float64)

                q_bet, _ = eval_direct_betting(x, tau=SAFETY_THRESHOLD, alpha=ALPHA)
                if q_bet:
                    bet_passes += 1

                q_const, _, _ = eval_constant_betting(x, tau=SAFETY_THRESHOLD, alpha=ALPHA, theta_alt=0.010)
                if q_const:
                    const_passes += 1

            model_a_data["direct_betting"][f"K_{k}"][f"theta_{theta:.4f}"] = bet_passes / n_trials
            model_a_data["constant_betting"][f"K_{k}"][f"theta_{theta:.4f}"] = const_passes / n_trials

    # 2. Model B: Diffuse Within-Cluster Harm (N=400 cases)
    model_b_data: dict[str, dict[str, dict[str, float]]] = {
        m: {f"K_{k}": {} for k in horizons}
        for m in ["maurer_pontil", "direct_betting", "constant_betting", "hoeffding"]
    }

    for k in horizons:
        for theta in [0.010, 0.020, 0.0500, 0.0501]:
            mp_cnt = 0
            bet_cnt = 0
            const_cnt = 0
            hoeff_cnt = 0

            for _ in range(n_trials):
                # R_k is sample mean of 400 Bernoulli(theta) cases
                x = rng.binomial(n_cases_per_cluster, theta, size=k).astype(np.float64) / n_cases_per_cluster

                q_mp, _, _ = eval_maurer_pontil(x, tau=SAFETY_THRESHOLD, alpha=ALPHA)
                if q_mp:
                    mp_cnt += 1

                q_bet, _ = eval_direct_betting(x, tau=SAFETY_THRESHOLD, alpha=ALPHA)
                if q_bet:
                    bet_cnt += 1

                q_const, _, _ = eval_constant_betting(x, tau=SAFETY_THRESHOLD, alpha=ALPHA, theta_alt=0.010)
                if q_const:
                    const_cnt += 1

                q_hf, _ = eval_hoeffding(x, tau=SAFETY_THRESHOLD, alpha=ALPHA)
                if q_hf:
                    hoeff_cnt += 1

            model_b_data["maurer_pontil"][f"K_{k}"][f"theta_{theta:.4f}"] = mp_cnt / n_trials
            model_b_data["direct_betting"][f"K_{k}"][f"theta_{theta:.4f}"] = bet_cnt / n_trials
            model_b_data["constant_betting"][f"K_{k}"][f"theta_{theta:.4f}"] = const_cnt / n_trials
            model_b_data["hoeffding"][f"K_{k}"][f"theta_{theta:.4f}"] = hoeff_cnt / n_trials

    # 3. Model C: Heterogeneous Cluster Means Targeting Boundary mu_bar = 0.0501
    # Schedule: 25% hazardous clusters (mu = 0.2004), 75% safe clusters (mu = 0.0) -> mu_bar = 0.0501
    model_c_data: dict[str, Any] = {}

    for k in [128, 256, 512]:
        k_haz = k // 4
        k_safe = k - k_haz
        p_haz = 0.0501 * (k / k_haz)

        # C1: Front-loaded hazards (hazardous first)
        c1_bet_fsq, c1_const_fsq, c1_perm_fsq, c1_mp_fsq = 0, 0, 0, 0
        # C2: Back-loaded hazards (safe first)
        c2_bet_fsq, c2_const_fsq, c2_perm_fsq, c2_mp_fsq = 0, 0, 0, 0
        # C3: Exchangeable random permutation
        c3_bet_fsq, c3_const_fsq, c3_perm_fsq, c3_mp_fsq = 0, 0, 0, 0

        for _ in range(n_trials):
            haz_draw = rng.binomial(1, p_haz, size=k_haz).astype(np.float64)
            safe_draw = np.zeros(k_safe, dtype=np.float64)

            # C1
            x_c1 = np.concatenate([haz_draw, safe_draw])
            if eval_direct_betting(x_c1)[0]:
                c1_bet_fsq += 1
            if eval_constant_betting(x_c1)[0]:
                c1_const_fsq += 1
            if eval_permutation_betting(x_c1, m_permutations=10, seed=rng.integers(1e9))[0]:
                c1_perm_fsq += 1
            if eval_maurer_pontil(x_c1)[0]:
                c1_mp_fsq += 1

            # C2
            x_c2 = np.concatenate([safe_draw, haz_draw])
            if eval_direct_betting(x_c2)[0]:
                c2_bet_fsq += 1
            if eval_constant_betting(x_c2)[0]:
                c2_const_fsq += 1
            if eval_permutation_betting(x_c2, m_permutations=10, seed=rng.integers(1e9))[0]:
                c2_perm_fsq += 1
            if eval_maurer_pontil(x_c2)[0]:
                c2_mp_fsq += 1

            # C3
            x_c3 = rng.permutation(x_c1)
            if eval_direct_betting(x_c3)[0]:
                c3_bet_fsq += 1
            if eval_constant_betting(x_c3)[0]:
                c3_const_fsq += 1
            if eval_permutation_betting(x_c3, m_permutations=10, seed=rng.integers(1e9))[0]:
                c3_perm_fsq += 1
            if eval_maurer_pontil(x_c3)[0]:
                c3_mp_fsq += 1

        model_c_data[f"K_{k}"] = {
            "front_loaded_fsq": {
                "direct_betting_aGRAPA": c1_bet_fsq / n_trials,
                "constant_betting": c1_const_fsq / n_trials,
                "permutation_betting": c1_perm_fsq / n_trials,
                "maurer_pontil": c1_mp_fsq / n_trials,
            },
            "back_loaded_fsq": {
                "direct_betting_aGRAPA": c2_bet_fsq / n_trials,
                "constant_betting": c2_const_fsq / n_trials,
                "permutation_betting": c2_perm_fsq / n_trials,
                "maurer_pontil": c2_mp_fsq / n_trials,
            },
            "exchangeable_random_fsq": {
                "direct_betting_aGRAPA": c3_bet_fsq / n_trials,
                "constant_betting": c3_const_fsq / n_trials,
                "permutation_betting": c3_perm_fsq / n_trials,
                "maurer_pontil": c3_mp_fsq / n_trials,
            },
        }

    # 4. Sensitivity to Missing Observations (Cluster Dropouts)
    missingness_data: dict[str, Any] = {}
    for k in [256, 512]:
        for drop_rate in [0.05, 0.10]:
            k_eff = int(k * (1.0 - drop_rate))
            # Power under theta = 0.010 with reduced sample size
            pw_mp_drop = float(stats.binom.cdf(compute_analytical_z_max(k_eff)["maurer_pontil"], k_eff, 0.010))

            bet_cnt = 0
            const_cnt = 0
            for _ in range(n_trials):
                x = rng.binomial(1, 0.010, size=k_eff).astype(np.float64)
                if eval_direct_betting(x)[0]:
                    bet_cnt += 1
                if eval_constant_betting(x)[0]:
                    const_cnt += 1

            missingness_data[f"K_{k}_drop_{int(drop_rate*100)}pct"] = {
                "nominal_k": k,
                "effective_k": k_eff,
                "maurer_pontil_power": pw_mp_drop,
                "direct_betting_power": bet_cnt / n_trials,
                "constant_betting_power": const_cnt / n_trials,
            }

    # 5. Computational Latency Profiling (microseconds per evaluation at K=256)
    latencies: dict[str, float] = {}
    x_bench = np.full(256, 0.010, dtype=np.float64)

    # Maurer-Pontil
    t0 = time.perf_counter()
    for _ in range(1000):
        _ = eval_maurer_pontil(x_bench)
    latencies["maurer_pontil_us"] = (time.perf_counter() - t0) * 1e6 / 1000.0

    # Direct Betting (aGRAPA)
    t0 = time.perf_counter()
    for _ in range(1000):
        _ = eval_direct_betting(x_bench)
    latencies["direct_betting_aGRAPA_us"] = (time.perf_counter() - t0) * 1e6 / 1000.0

    # Constant Betting
    t0 = time.perf_counter()
    for _ in range(1000):
        _ = eval_constant_betting(x_bench)
    latencies["constant_betting_us"] = (time.perf_counter() - t0) * 1e6 / 1000.0

    # Permutation Betting (M=10)
    t0 = time.perf_counter()
    for _ in range(100):
        _ = eval_permutation_betting(x_bench, m_permutations=10)
    latencies["permutation_betting_M10_us"] = (time.perf_counter() - t0) * 1e6 / 100.0

    # Hoeffding
    t0 = time.perf_counter()
    for _ in range(1000):
        _ = eval_hoeffding(x_bench)
    latencies["hoeffding_us"] = (time.perf_counter() - t0) * 1e6 / 1000.0

    return SimulationSummary(
        horizons=horizons,
        thetas_evaluated=thetas,
        model_a_results=model_a_data,
        model_b_results=model_b_data,
        model_c_heterogeneous_results=model_c_data,
        catastrophic_shock_thresholds=z_max_table,
        missingness_sensitivity=missingness_data,
        computational_latencies_microseconds=latencies,
    )
