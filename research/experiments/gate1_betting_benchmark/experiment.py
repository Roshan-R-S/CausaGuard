"""Comprehensive benchmark experiment evaluating Gate 1 betting bounds against empirical Bernstein and Clopper-Pearson.

Evaluates:
- Horizons: K in {128, 192, 256, 384, 512}
- True risks: theta in {0.005, 0.010, 0.020, 0.0500, 0.0501, 0.0600}
- Regimes:
  1. Cluster shock (worst-case Bernoulli R_k in {0, 1})
  2. Diffuse independent harm (R_k = sum(Y_{k,i})/N, N=400)
  3. ICC sweep rho in {0.0, 0.01, 0.05, 0.10, 0.25, 0.50, 1.00}
  4. Heterogeneous clusters (varying cluster sizes and mixed risks)

Research status: EXPLORATORY RESEARCH ONLY -- PRE-FREEZE NO-GO.
Confirmatory protocol draft, candidate controllers, and production authorization remain untouched.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from research.experiments.gate1_betting_benchmark import (
    PRE_FREEZE_NO_GO,
    PRODUCTION_AUTHORIZATION_ENABLED,
)
from research.experiments.gate1_betting_benchmark.betting_bounds import (
    theoretical_zero_event_bound,
    ucb_betting_anytime_cs,
    ucb_betting_fixed_time,
    ucb_cluster_clopper_pearson,
    ucb_empirical_bernstein_corrected,
    ucb_student_t,
)

BASE_EXPLORATORY_SEED = 82000001
SAFETY_THRESHOLD = 0.0500
ALPHA = 0.050


@dataclass
class RegimeResult:
    method: str
    k: int
    theta: float
    regime: str
    trials: int
    coverage: float
    fsq_rate: float
    qualification_power: float
    unnecessary_rejection: float
    mean_ucb: float
    std_ucb: float
    mean_latency_ms: float


def generate_cluster_shock_sample(k: int, theta: float, rng: np.random.Generator) -> np.ndarray:
    """Regime 1: Worst-case Bernoulli all-or-none cluster shocks (R_k in {0, 1})."""
    return (rng.uniform(0.0, 1.0, size=k) < theta).astype(np.float64)


def generate_diffuse_sample(
    k: int, n: int, theta: float, rng: np.random.Generator
) -> np.ndarray:
    """Regime 2: Independent diffuse harm within clusters (R_k = Binom(N, theta) / N)."""
    return rng.binomial(n, theta, size=k).astype(np.float64) / float(n)


def generate_icc_sample(
    k: int, n: int, theta: float, rho: float, rng: np.random.Generator
) -> np.ndarray:
    """Regime 3: Beta-binomial intra-cluster correlation."""
    if rho <= 1e-6:
        return generate_diffuse_sample(k, n, theta, rng)
    if rho >= 0.9999:
        return generate_cluster_shock_sample(k, theta, rng)

    # Beta parameters: alpha / (alpha + beta) = theta, rho = 1 / (alpha + beta + 1)
    s = (1.0 - rho) / rho
    alpha_beta = theta * s
    beta_beta = (1.0 - theta) * s

    p_k = rng.beta(alpha_beta, beta_beta, size=k)
    return rng.binomial(n, p_k).astype(np.float64) / float(n)


def generate_heterogeneous_sample(
    k: int, theta: float, rng: np.random.Generator
) -> np.ndarray:
    """Regime 4: Heterogeneous cluster sizes N_k in [200, 600] and risk variance."""
    half = k // 2
    theta_low = 0.5 * theta
    theta_high = 1.5 * theta

    n_k = rng.integers(200, 601, size=k)
    thetas = np.array([theta_low] * half + [theta_high] * (k - half), dtype=np.float64)
    rng.shuffle(thetas)

    return rng.binomial(n_k, thetas).astype(np.float64) / n_k.astype(np.float64)


def run_single_condition(
    k: int,
    theta: float,
    regime: str,
    trials: int = 500,
    n_cases: int = 400,
    rho: float = 0.05,
    seed: int = BASE_EXPLORATORY_SEED,
) -> dict[str, RegimeResult]:
    """Run Monte Carlo simulation for one condition across all 5 bounds."""
    rng = np.random.default_rng(seed)

    methods = [
        "betting_fixed",
        "betting_anytime",
        "empirical_bernstein",
        "clopper_pearson",
        "student_t",
    ]

    ucb_records: dict[str, list[float]] = {m: [] for m in methods}
    timing_records: dict[str, list[float]] = {m: [] for m in methods}

    for _ in range(trials):
        if regime == "cluster_shock":
            sample = generate_cluster_shock_sample(k, theta, rng)
        elif regime == "diffuse_harm":
            sample = generate_diffuse_sample(k, n_cases, theta, rng)
        elif regime == "icc_sweep":
            sample = generate_icc_sample(k, n_cases, theta, rho, rng)
        elif regime == "heterogeneous":
            sample = generate_heterogeneous_sample(k, theta, rng)
        else:
            sample = generate_cluster_shock_sample(k, theta, rng)

        # Evaluate betting_fixed
        t0 = time.perf_counter()
        u_bf = ucb_betting_fixed_time(sample, alpha=ALPHA)
        t_bf = (time.perf_counter() - t0) * 1000.0
        ucb_records["betting_fixed"].append(u_bf)
        timing_records["betting_fixed"].append(t_bf)

        # Evaluate betting_anytime
        t0 = time.perf_counter()
        u_ba = ucb_betting_anytime_cs(sample, alpha=ALPHA)
        t_ba = (time.perf_counter() - t0) * 1000.0
        ucb_records["betting_anytime"].append(u_ba)
        timing_records["betting_anytime"].append(t_ba)

        # Evaluate empirical_bernstein
        t0 = time.perf_counter()
        u_eb = ucb_empirical_bernstein_corrected(sample, alpha=ALPHA)
        t_eb = (time.perf_counter() - t0) * 1000.0
        ucb_records["empirical_bernstein"].append(u_eb)
        timing_records["empirical_bernstein"].append(t_eb)

        # Evaluate clopper_pearson
        t0 = time.perf_counter()
        u_cp = ucb_cluster_clopper_pearson(sample, alpha=ALPHA)
        t_cp = (time.perf_counter() - t0) * 1000.0
        ucb_records["clopper_pearson"].append(u_cp)
        timing_records["clopper_pearson"].append(t_cp)

        # Evaluate student_t
        t0 = time.perf_counter()
        u_st = ucb_student_t(sample, alpha=ALPHA)
        t_st = (time.perf_counter() - t0) * 1000.0
        ucb_records["student_t"].append(u_st)
        timing_records["student_t"].append(t_st)

    results = {}
    for m in methods:
        arr = np.array(ucb_records[m], dtype=np.float64)
        cov = float(np.mean(arr >= theta))
        qual = float(np.mean(arr <= SAFETY_THRESHOLD))

        if theta > SAFETY_THRESHOLD:
            fsq = qual
            power = 0.0
            unrec = 0.0
        else:
            fsq = 0.0
            power = qual
            unrec = 1.0 - power

        results[m] = RegimeResult(
            method=m,
            k=k,
            theta=theta,
            regime=regime,
            trials=trials,
            coverage=cov,
            fsq_rate=fsq,
            qualification_power=power,
            unnecessary_rejection=unrec,
            mean_ucb=float(np.mean(arr)),
            std_ucb=float(np.std(arr)),
            mean_latency_ms=float(np.mean(timing_records[m])),
        )

    return results


def run_full_benchmark_suite(
    output_path: Path | None = None,
    trials_per_condition: int = 500,
) -> dict[str, Any]:
    """Run full matrix across sample sizes, true thetas, and data regimes."""
    assert PRE_FREEZE_NO_GO is True
    assert PRODUCTION_AUTHORIZATION_ENABLED is False

    k_list = [128, 192, 256, 384, 512]
    theta_list = [0.005, 0.010, 0.020, 0.0500, 0.0501, 0.0600]

    all_results: list[dict[str, Any]] = []

    # 1. Cluster shock sweep
    print("--- Running Regime 1: Cluster Shocks ---")
    seed_counter = BASE_EXPLORATORY_SEED
    for k in k_list:
        for theta in theta_list:
            res = run_single_condition(
                k=k,
                theta=theta,
                regime="cluster_shock",
                trials=trials_per_condition,
                seed=seed_counter,
            )
            seed_counter += 1
            for r in res.values():
                all_results.append(asdict(r))

    # 2. Diffuse harm sweep
    print("--- Running Regime 2: Diffuse Harm ---")
    for k in [128, 256]:
        for theta in [0.005, 0.010, 0.020, 0.0501]:
            res = run_single_condition(
                k=k,
                theta=theta,
                regime="diffuse_harm",
                trials=trials_per_condition,
                seed=seed_counter,
            )
            seed_counter += 1
            for r in res.values():
                all_results.append(asdict(r))

    # 3. ICC sweep at K=256, theta=0.010
    print("--- Running Regime 3: ICC Sweep ---")
    icc_values = [0.0, 0.01, 0.05, 0.10, 0.25, 0.50, 1.00]
    for rho in icc_values:
        res = run_single_condition(
            k=256,
            theta=0.010,
            regime="icc_sweep",
            rho=rho,
            trials=trials_per_condition,
            seed=seed_counter,
        )
        seed_counter += 1
        for r in res.values():
            d = asdict(r)
            d["rho"] = rho
            all_results.append(d)

    # 4. Heterogeneous clusters
    print("--- Running Regime 4: Heterogeneous Clusters ---")
    for k in [128, 256]:
        for theta in [0.010, 0.0501]:
            res = run_single_condition(
                k=k,
                theta=theta,
                regime="heterogeneous",
                trials=trials_per_condition,
                seed=seed_counter,
            )
            seed_counter += 1
            for r in res.values():
                all_results.append(asdict(r))

    # Analytical edge-case calculations (zero events, single shock)
    analytical_summary = {}
    for k in k_list:
        analytical_summary[f"K_{k}"] = {
            "theoretical_bernoulli_zero_limit": theoretical_zero_event_bound(k, alpha=ALPHA),
            "betting_zero_event_ucb": ucb_betting_fixed_time(np.zeros(k), alpha=ALPHA),
            "empirical_bernstein_zero_event_ucb": ucb_empirical_bernstein_corrected(
                np.zeros(k), alpha=ALPHA
            ),
            "clopper_pearson_zero_event_ucb": ucb_cluster_clopper_pearson(
                np.zeros(k), alpha=ALPHA
            ),
        }

    payload = {
        "benchmark_metadata": {
            "experiment": "gate1_betting_benchmark",
            "author": "Antigravity (Gemini)",
            "status": "EXPLORATORY RESEARCH -- PRE-FREEZE NO-GO",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "safety_threshold": SAFETY_THRESHOLD,
            "nominal_alpha": ALPHA,
            "trials_per_condition": trials_per_condition,
        },
        "analytical_summary": analytical_summary,
        "empirical_results": all_results,
    }

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        print(f"Results written to: {output_path}")

    return payload


if __name__ == "__main__":
    report_json_path = (
        Path(__file__).parents[2]
        / "reviews"
        / "v071-gate1-betting-bounds-benchmark.json"
    )
    print("Executing Gate 1 Betting Bounds Benchmark Suite...")
    run_full_benchmark_suite(output_path=report_json_path, trials_per_condition=500)
    print("Benchmark complete.")
