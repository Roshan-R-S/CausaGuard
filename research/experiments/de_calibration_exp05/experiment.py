"""Experiment 05: Prospective Calibration and Statistical Coverage in Data Engineering.

Evaluates empirical coverage, false safety qualification, and decision utility
of Clopper-Pearson calibrated credal uncertainty sets across sample size grids
and under intentional assumption violations (clustering, prevalence drift, sensor drift).
"""

from __future__ import annotations

import argparse
import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import scipy.stats as stats

# Operational constants matching Experiments 03 and 04
DEFAULT_PRIOR = 0.20  # pi_0 = 1/5
DEFAULT_AVAILABILITY = 0.91  # A = 91/100
SAFETY_THRESHOLD = 0.050  # tau_safe = 0.050
DEFAULT_ALPHA_CAL = 0.05  # alpha_cal = 0.05 for simultaneous 95% coverage

# Baseline data-generating model (Exp03/04 minimal counterexample)
TRUE_FP_STAR = 0.02
TRUE_FN_STAR = 0.24  # Misspecified nominal is 0.20

# Safe exploratory seed range (strictly outside reserved confirmatory seeds 70100001+, 70200001+, 60030001+)
EXPLORATORY_SEED_BASE = 50100001


@dataclass(frozen=True)
class Interval:
    """Closed interval [low, high] in [0, 1]."""

    low: float
    high: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.low <= 1.0) or not (0.0 <= self.high <= 1.0):
            raise ValueError(f"Interval bounds must be in [0, 1], got [{self.low}, {self.high}]")
        if self.low > self.high:
            raise ValueError(f"Lower bound exceeds upper bound: low={self.low} > high={self.high}")

    @property
    def width(self) -> float:
        return self.high - self.low

    def contains(self, x: float) -> bool:
        return self.low <= x <= self.high


@dataclass(frozen=True)
class CredalRates:
    """Rectangular credal set C = I_FP x I_FN."""

    fp: Interval
    fn: Interval

    def contains(self, fp_val: float, fn_val: float) -> bool:
        return self.fp.contains(fp_val) and self.fn.contains(fn_val)


@dataclass(frozen=True)
class RiskBounds:
    """Credal operational risk bounds and tri-state decision outcome."""

    lower_risk: float
    upper_risk: float
    lower_posterior: float
    upper_posterior: float
    status: str

    @property
    def qualifies(self) -> bool:
        """Declared safe: upper bound meets safety threshold."""
        return self.upper_risk <= SAFETY_THRESHOLD

    @property
    def disqualified(self) -> bool:
        """Declared unsafe: lower bound strictly exceeds threshold."""
        return self.lower_risk > SAFETY_THRESHOLD

    @property
    def inconclusive(self) -> bool:
        """Abstention: uncertainty spans the decision threshold."""
        return self.lower_risk <= SAFETY_THRESHOLD < self.upper_risk

    @property
    def width(self) -> float:
        return self.upper_risk - self.lower_risk

    def encloses(self, r: float) -> bool:
        return self.lower_risk <= r <= self.upper_risk


def clopper_pearson(k: int, n: int, alpha: float) -> tuple[float, float]:
    """Calculates exact two-sided Clopper-Pearson binomial confidence interval.

    Args:
        k: Number of observed successes/events.
        n: Total number of independent trials.
        alpha: Significance level (e.g. 0.025 for 97.5% confidence).

    Returns:
        (low, high) bounds in [0, 1].
    """
    if n <= 0:
        raise ValueError(f"Sample size n must be positive, got {n}")
    if not (0 <= k <= n):
        raise ValueError(f"Success count k must satisfy 0 <= k <= n, got k={k}, n={n}")
    if not (0.0 < alpha < 1.0):
        raise ValueError(f"Significance level alpha must be in (0, 1), got {alpha}")

    # Lower bound
    if k == 0:
        low = 0.0
    else:
        low = float(stats.beta.ppf(alpha / 2.0, k, n - k + 1))

    # Upper bound
    if k == n:
        high = 1.0
    else:
        high = float(stats.beta.ppf(1.0 - alpha / 2.0, k + 1, n - k))

    return max(0.0, low), min(1.0, high)


def clopper_pearson_vectorized(
    k: np.ndarray, n: int, alpha: float
) -> tuple[np.ndarray, np.ndarray]:
    """Vectorized Clopper-Pearson exact confidence bounds across arrays of k."""
    low = np.zeros(len(k), dtype=float)
    high = np.ones(len(k), dtype=float)

    pos_mask = k > 0
    high_mask = k < n

    if np.any(pos_mask):
        low[pos_mask] = stats.beta.ppf(alpha / 2.0, k[pos_mask], n - k[pos_mask] + 1)
    if np.any(high_mask):
        high[high_mask] = stats.beta.ppf(1.0 - alpha / 2.0, k[high_mask] + 1, n - k[high_mask])

    return np.clip(low, 0.0, 1.0), np.clip(high, 0.0, 1.0)


def calibrate_credal_set(
    k_fp: int,
    n_clean: int,
    k_fn: int,
    n_schema: int,
    alpha_cal: float = DEFAULT_ALPHA_CAL,
) -> CredalRates:
    """Constructs a simultaneous 1 - alpha_cal confidence rectangle.

    Applies Bonferroni multiplicity allocation: alpha_1 = alpha_2 = alpha_cal / 2.
    Strictly isolated: does not receive true generating parameters.
    """
    if n_clean <= 0 or n_schema <= 0:
        # Fallback to vacuous bounds under insufficient data
        return CredalRates(fp=Interval(0.0, 1.0), fn=Interval(0.0, 1.0))

    alpha_dim = alpha_cal / 2.0
    fp_low, fp_high = clopper_pearson(k_fp, n_clean, alpha_dim)
    fn_low, fn_high = clopper_pearson(k_fn, n_schema, alpha_dim)

    return CredalRates(fp=Interval(fp_low, fp_high), fn=Interval(fn_low, fn_high))


def compute_exact_posterior(
    prior: float | np.ndarray,
    likelihood_clean: float | np.ndarray,
    likelihood_schema: float | np.ndarray,
) -> float | np.ndarray:
    """Computes standard Bayes posterior P(schema | evidence)."""
    clean_mass = (1.0 - prior) * likelihood_clean
    schema_mass = prior * likelihood_schema
    total = clean_mass + schema_mass
    if isinstance(total, np.ndarray):
        zero_mask = total <= 0.0
        res = np.zeros_like(total)
        res[~zero_mask] = schema_mass[~zero_mask] / total[~zero_mask]
        res[zero_mask] = prior if isinstance(prior, float) else prior[zero_mask]
        return res
    if total <= 0.0:
        return prior
    return schema_mass / total


def compute_credal_risk_bounds(
    credal: CredalRates,
    passed: bool,
    prior: float = DEFAULT_PRIOR,
    availability: float = DEFAULT_AVAILABILITY,
) -> RiskBounds:
    """Computes exact upper and lower operational risk bounds over credal box C.

    Uses the analytical corner extremum derivations from Experiment 04.
    """
    if passed:
        # Maximum posterior occurs at (FP_max, FN_max)
        post_upper = float(compute_exact_posterior(prior, 1.0 - credal.fp.high, credal.fn.high))
        # Minimum posterior occurs at (FP_min, FN_min)
        post_lower = float(compute_exact_posterior(prior, 1.0 - credal.fp.low, credal.fn.low))
    else:
        # Maximum posterior occurs at (FP_min, FN_min)
        post_upper = float(compute_exact_posterior(prior, credal.fp.low, 1.0 - credal.fn.low))
        # Minimum posterior occurs at (FP_max, FN_max)
        post_lower = float(compute_exact_posterior(prior, credal.fp.high, 1.0 - credal.fn.high))

    r_upper = availability * post_upper
    r_lower = availability * post_lower

    return RiskBounds(
        lower_risk=r_lower,
        upper_risk=r_upper,
        lower_posterior=post_lower,
        upper_posterior=post_upper,
        status="defined",
    )


def compute_frechet_risk_bounds(
    p_clean: float,
    p_schema: float,
    prior: float = 0.10,
    availability: float = DEFAULT_AVAILABILITY,
) -> RiskBounds:
    """Computes bivariate Frechet copula joint bounds and posterior risk."""
    clean_joint_low = max(0.0, 2.0 * p_clean - 1.0)
    clean_joint_high = p_clean

    schema_joint_low = max(0.0, 2.0 * p_schema - 1.0)
    schema_joint_high = p_schema

    # Worst case: schema mass high, clean mass low
    post_upper = float(compute_exact_posterior(prior, clean_joint_low, schema_joint_high))
    # Best case: schema mass low, clean mass high
    post_lower = float(compute_exact_posterior(prior, clean_joint_high, schema_joint_low))

    return RiskBounds(
        lower_risk=availability * post_lower,
        upper_risk=availability * post_upper,
        lower_posterior=post_lower,
        upper_posterior=post_upper,
        status="defined",
    )


def rate_confidence_interval(
    k_successes: int, n_total: int, confidence: float = 0.95, method: str = "wilson"
) -> tuple[float, float]:
    """Calculates confidence interval for an empirical Monte Carlo proportion.

    Methods:
        - 'wilson': Standard two-sided Wilson score interval.
        - 'rule_of_three': One-sided upper bound for zero events (3/n).
        - 'clopper_pearson': Exact two-sided Clopper-Pearson interval.
    """
    if n_total == 0:
        return 0.0, 1.0

    if method == "rule_of_three" and k_successes == 0:
        return 0.0, min(1.0, 3.0 / n_total)

    if method == "clopper_pearson":
        alpha = 1.0 - confidence
        low = (
            0.0
            if k_successes == 0
            else float(stats.beta.ppf(alpha / 2.0, k_successes, n_total - k_successes + 1))
        )
        high = (
            1.0
            if k_successes == n_total
            else float(stats.beta.ppf(1.0 - alpha / 2.0, k_successes + 1, n_total - k_successes))
        )
        return low, high

    # Standard two-sided Wilson score interval (valid for all 0 <= k <= n)
    z = float(stats.norm.ppf(1.0 - (1.0 - confidence) / 2.0))
    p_hat = k_successes / n_total
    denom = 1.0 + (z**2) / n_total
    center = (p_hat + (z**2) / (2.0 * n_total)) / denom
    half = (
        z * math.sqrt((p_hat * (1.0 - p_hat)) / n_total + (z**2) / (4.0 * (n_total**2)))
    ) / denom
    low = 0.0 if k_successes == 0 else max(0.0, center - half)
    high = 1.0 if k_successes == n_total else min(1.0, center + half)
    return low, high


# ==============================================================================
# Monte Carlo Simulation & Multi-Arm Benchmarking
# ==============================================================================


def simulate_calibration_batch(
    n_clean: int,
    n_schema: int,
    fp_star: float,
    fn_star: float,
    n_reps: int,
    rng: np.random.Generator,
    passed_evidence: bool = True,
    icc: float = 0.0,
    cluster_size: int = 10,
    prior: float = DEFAULT_PRIOR,
    eval_fp: float | None = None,
    eval_fn: float | None = None,
) -> dict[str, Any]:
    """Simulates a batch of n_reps independent calibration-evaluation replications."""
    eval_fp_star = fp_star if eval_fp is None else eval_fp
    eval_fn_star = fn_star if eval_fn is None else eval_fn

    # 1. Generate calibration data
    if icc <= 0.0:
        k_fp = rng.binomial(n_clean, fp_star, size=n_reps)
        k_fn = rng.binomial(n_schema, fn_star, size=n_reps)
    else:
        # Clustered calibration data via Beta-Binomial
        n_clusters_clean = max(1, n_clean // cluster_size)
        ab_clean = (1.0 / icc) - 1.0
        a_c = max(0.01, fp_star * ab_clean)
        b_c = max(0.01, (1.0 - fp_star) * ab_clean)
        p_c = rng.beta(a_c, b_c, size=(n_reps, n_clusters_clean))
        k_clusters_c = rng.binomial(cluster_size, p_c)
        k_fp = np.sum(k_clusters_c, axis=1)

        n_clusters_schema = max(1, n_schema // cluster_size)
        ab_schema = (1.0 / icc) - 1.0
        a_s = max(0.01, fn_star * ab_schema)
        b_s = max(0.01, (1.0 - fn_star) * ab_schema)
        p_s = rng.beta(a_s, b_s, size=(n_reps, n_clusters_schema))
        k_clusters_s = rng.binomial(cluster_size, p_s)
        k_fn = np.sum(k_clusters_s, axis=1)

    # 2. Clopper-Pearson calibrated bounds
    alpha_dim = DEFAULT_ALPHA_CAL / 2.0
    fp_low, fp_high = clopper_pearson_vectorized(k_fp, n_clean, alpha_dim)
    fn_low, fn_high = clopper_pearson_vectorized(k_fn, n_schema, alpha_dim)

    # 3. Parameter Coverage Check (against calibration generating parameter)
    fp_covered = (fp_low <= fp_star) & (fp_star <= fp_high)
    fn_covered = (fn_low <= fn_star) & (fn_star <= fn_high)
    param_covered = fp_covered & fn_covered

    # 4. True Operational Risk (under evaluation distribution)
    true_post = float(
        compute_exact_posterior(
            prior,
            1.0 - eval_fp_star if passed_evidence else eval_fp_star,
            eval_fn_star if passed_evidence else 1.0 - eval_fn_star,
        )
    )
    true_risk = DEFAULT_AVAILABILITY * true_post
    true_qualifies = true_risk <= SAFETY_THRESHOLD

    # 5. Credal Decision Bounds
    if passed_evidence:
        post_upper = compute_exact_posterior(prior, 1.0 - fp_high, fn_high)
        post_lower = compute_exact_posterior(prior, 1.0 - fp_low, fn_low)
    else:
        post_upper = compute_exact_posterior(prior, fp_low, 1.0 - fn_low)
        post_lower = compute_exact_posterior(prior, fp_high, 1.0 - fn_high)

    upper_risk = DEFAULT_AVAILABILITY * post_upper
    lower_risk = DEFAULT_AVAILABILITY * post_lower

    risk_covered = (lower_risk <= true_risk) & (true_risk <= upper_risk)
    qualifies = upper_risk <= SAFETY_THRESHOLD
    disqualified = lower_risk > SAFETY_THRESHOLD
    abstention = (lower_risk <= SAFETY_THRESHOLD) & (upper_risk > SAFETY_THRESHOLD)

    false_safety_qual = qualifies & (not true_qualifies)
    unnecessary_reject = disqualified & true_qualifies

    # Decision utilities
    utilities = np.where(
        false_safety_qual,
        -100.0,
        np.where(
            qualifies & true_qualifies,
            1.0,
            np.where(
                disqualified & (not true_qualifies), 0.0, np.where(unnecessary_reject, -1.0, -0.5)
            ),
        ),
    )

    return {
        "n_reps": n_reps,
        "param_coverage": float(np.mean(param_covered)),
        "param_coverage_ci_95": list(rate_confidence_interval(int(np.sum(param_covered)), n_reps)),
        "risk_coverage": float(np.mean(risk_covered)),
        "risk_coverage_ci_95": list(rate_confidence_interval(int(np.sum(risk_covered)), n_reps)),
        "false_safety_qual_rate": float(np.mean(false_safety_qual)),
        "false_safety_qual_ci_95": list(
            rate_confidence_interval(int(np.sum(false_safety_qual)), n_reps)
        ),
        "abstention_rate": float(np.mean(abstention)),
        "abstention_ci_95": list(rate_confidence_interval(int(np.sum(abstention)), n_reps)),
        "unnecessary_reject_rate": float(np.mean(unnecessary_reject)),
        "mean_utility": float(np.mean(utilities)),
        "mean_fp_width": float(np.mean(fp_high - fp_low)),
        "mean_fn_width": float(np.mean(fn_high - fn_low)),
        "mean_risk_width": float(np.mean(upper_risk - lower_risk)),
        "true_risk": true_risk,
    }


def evaluate_sample_size_sensitivity(
    sample_sizes: list[int],
    n_reps: int = 1000,
    seed: int = EXPLORATORY_SEED_BASE,
) -> list[dict[str, Any]]:
    """Evaluates sensitivity of calibration coverage and bound width to N_cal."""
    results = []

    for n_cal in sample_sizes:
        n_clean = n_cal
        n_schema = max(10, n_cal // 2)
        # Dedicated deterministic seed per sample size ensures independent reproducibility
        rng_n = np.random.default_rng(seed + n_cal)

        batch = simulate_calibration_batch(
            n_clean=n_clean,
            n_schema=n_schema,
            fp_star=TRUE_FP_STAR,
            fn_star=TRUE_FN_STAR,
            n_reps=n_reps,
            rng=rng_n,
            passed_evidence=True,
        )

        results.append(
            {
                "n_cal": n_cal,
                "n_clean": n_clean,
                "n_schema": n_schema,
                "param_coverage": batch["param_coverage"],
                "param_coverage_ci_95": [round(x, 4) for x in batch["param_coverage_ci_95"]],
                "risk_coverage": batch["risk_coverage"],
                "risk_coverage_ci_95": [round(x, 4) for x in batch["risk_coverage_ci_95"]],
                "false_safety_qual_rate": batch["false_safety_qual_rate"],
                "false_safety_qual_ci_95": [round(x, 4) for x in batch["false_safety_qual_ci_95"]],
                "abstention_rate": batch["abstention_rate"],
                "abstention_ci_95": [round(x, 4) for x in batch["abstention_ci_95"]],
                "unnecessary_reject_rate": batch["unnecessary_reject_rate"],
                "mean_decision_utility": round(batch["mean_utility"], 4),
                "mean_fp_width": round(batch["mean_fp_width"], 4),
                "mean_fn_width": round(batch["mean_fn_width"], 4),
                "mean_risk_width": round(batch["mean_risk_width"], 4),
            }
        )

    return results


def run_monte_carlo_calibration_study(
    n_reps: int = 1000, seed: int = EXPLORATORY_SEED_BASE
) -> list[dict[str, Any]]:
    """Alias for evaluate_sample_size_sensitivity matching the public interface."""
    return evaluate_sample_size_sensitivity(
        [50, 100, 250, 500, 1000, 2000], n_reps=n_reps, seed=seed
    )


def run_five_arm_benchmark(
    n_reps: int = 1000, seed: int = EXPLORATORY_SEED_BASE
) -> dict[str, Any]:
    """Runs Phase 3 Five-Arm Benchmark comparison."""
    # Arm A: Point Bayes (Assumed nominal FP=0.02, FN=0.20)
    assumed_post = float(compute_exact_posterior(DEFAULT_PRIOR, 1.0 - 0.02, 0.20))
    assumed_risk = DEFAULT_AVAILABILITY * assumed_post
    true_post = float(compute_exact_posterior(DEFAULT_PRIOR, 1.0 - TRUE_FP_STAR, TRUE_FN_STAR))
    true_risk = DEFAULT_AVAILABILITY * true_post

    arm_a = {
        "arm": "Arm A (Point-Estimate Bayes)",
        "assumed_risk": round(assumed_risk, 5),
        "true_risk": round(true_risk, 5),
        "qualifies": bool(assumed_risk <= SAFETY_THRESHOLD),
        "false_safety_qualification": bool(assumed_risk <= SAFETY_THRESHOLD < true_risk),
        "abstention": False,
        "utility": -100.0 if (assumed_risk <= SAFETY_THRESHOLD < true_risk) else 1.0,
    }

    # Arm B: Oracle Credal Bayes (Centered on true model: [0.01, 0.03] x [0.20, 0.28])
    oracle_credal = CredalRates(
        fp=Interval(0.01, 0.03),
        fn=Interval(0.20, 0.28),
    )
    b_bounds = compute_credal_risk_bounds(oracle_credal, passed=True)
    arm_b = {
        "arm": "Arm B (Oracle Credal Bayes)",
        "lower_risk": round(b_bounds.lower_risk, 5),
        "upper_risk": round(b_bounds.upper_risk, 5),
        "qualifies": b_bounds.qualifies,
        "inconclusive": b_bounds.inconclusive,
        "false_safety_qualification": bool(b_bounds.qualifies and (true_risk > SAFETY_THRESHOLD)),
        "risk_enclosed": b_bounds.encloses(true_risk),
        "utility": -0.5 if b_bounds.inconclusive else (1.0 if b_bounds.qualifies else 0.0),
    }

    # Arm C: Finite-Sample Calibrated Credal Bayes (N_clean=1000, N_schema=500 across n_reps)
    # Uses seed + 1000 to match the N_cal = 1000 evaluation in sample size sensitivity
    rng_c = np.random.default_rng(seed + 1000)
    batch_c = simulate_calibration_batch(
        n_clean=1000,
        n_schema=500,
        fp_star=TRUE_FP_STAR,
        fn_star=TRUE_FN_STAR,
        n_reps=n_reps,
        rng=rng_c,
    )
    arm_c = {
        "arm": "Arm C (Finite-Sample Calibrated Credal, N=1000/500)",
        "parameter_coverage": round(batch_c["param_coverage"], 4),
        "false_safety_qualification_rate": round(batch_c["false_safety_qual_rate"], 4),
        "abstention_rate": round(batch_c["abstention_rate"], 4),
        "mean_utility": round(batch_c["mean_utility"], 4),
    }

    # Arm D: Undersampled / Misspecified Credal Bayes (N_clean=50, N_schema=25)
    # Uses seed + 50 to match the N_cal = 50 evaluation in sample size sensitivity
    rng_d = np.random.default_rng(seed + 50)
    batch_d = simulate_calibration_batch(
        n_clean=50,
        n_schema=25,
        fp_star=TRUE_FP_STAR,
        fn_star=TRUE_FN_STAR,
        n_reps=n_reps,
        rng=rng_d,
    )
    arm_d = {
        "arm": "Arm D (Undersampled Credal, N=50/25)",
        "parameter_coverage": round(batch_d["param_coverage"], 4),
        "false_safety_qualification_rate": round(batch_d["false_safety_qual_rate"], 4),
        "abstention_rate": round(batch_d["abstention_rate"], 4),
        "mean_utility": round(batch_d["mean_utility"], 4),
    }

    # Arm E: Dependence-Aware Credal Inference (Frechet copula bounds)
    p_clean = 0.92
    p_schema = 0.60
    e_bounds = compute_frechet_risk_bounds(p_clean, p_schema, prior=0.10)
    true_dep_risk = 0.05466728  # from Exp03 common source joint
    arm_e = {
        "arm": "Arm E (Dependence-Aware Frechet Credal)",
        "lower_risk": round(e_bounds.lower_risk, 5),
        "upper_risk": round(e_bounds.upper_risk, 5),
        "inconclusive": e_bounds.inconclusive,
        "false_safety_qualification": bool(
            e_bounds.qualifies and (true_dep_risk > SAFETY_THRESHOLD)
        ),
        "risk_enclosed": e_bounds.encloses(true_dep_risk),
        "utility": -0.5 if e_bounds.inconclusive else 0.0,
    }

    return {
        "arm_a_point": arm_a,
        "arm_b_oracle": arm_b,
        "arm_c_calibrated": arm_c,
        "arm_d_undersampled": arm_d,
        "arm_e_frechet": arm_e,
    }


def run_assumption_violation_scenarios(
    n_reps: int = 1000, seed: int = EXPLORATORY_SEED_BASE + 200
) -> dict[str, Any]:
    """Phase 5: Constructs explicit scenarios evaluating assumption violations."""
    rng = np.random.default_rng(seed)

    # 1. Baseline: Independent i.i.d. trials
    base_res = simulate_calibration_batch(
        1000, 500, TRUE_FP_STAR, TRUE_FN_STAR, n_reps=n_reps, rng=rng, icc=0.0
    )

    # 2. Clustered calibration trials (ICC = 0.25, cluster_size = 10)
    clust_res = simulate_calibration_batch(
        1000, 500, TRUE_FP_STAR, TRUE_FN_STAR, n_reps=n_reps, rng=rng, icc=0.25, cluster_size=10
    )

    # 3. Defect prevalence drift: True prevalence rises from 0.20 to 0.35 in operational evaluation
    drift_res = simulate_calibration_batch(
        1000, 500, TRUE_FP_STAR, TRUE_FN_STAR, n_reps=n_reps, rng=rng, prior=0.35
    )

    # 4. Sensor error rate drift: sensor degrades in evaluation (FP: 0.02->0.035, FN: 0.24->0.32)
    sensor_drift_res = simulate_calibration_batch(
        1000, 500, TRUE_FP_STAR, TRUE_FN_STAR, n_reps=n_reps, rng=rng, eval_fp=0.035, eval_fn=0.32
    )

    return {
        "scenario_1_independent_baseline": {
            "description": "Nominal independent i.i.d. calibration trials",
            "empirical_coverage": round(base_res["param_coverage"], 4),
            "false_safety_qual_rate": round(base_res["false_safety_qual_rate"], 4),
        },
        "scenario_2_clustered_calibration": {
            "description": "Clustered calibration trials (ICC=0.25, m=10) with standard Clopper-Pearson",
            "empirical_coverage": round(clust_res["param_coverage"], 4),
            "false_safety_qual_rate": round(clust_res["false_safety_qual_rate"], 4),
            "coverage_degradation": round(
                base_res["param_coverage"] - clust_res["param_coverage"], 4
            ),
        },
        "scenario_3_prevalence_drift": {
            "description": "Defect prevalence drifts from 0.20 to 0.35 post-calibration",
            "risk_bound_coverage": round(drift_res["risk_coverage"], 4),
            "false_safety_qual_rate": round(drift_res["false_safety_qual_rate"], 4),
        },
        "scenario_4_sensor_drift": {
            "description": "Sensor error rates degrade post-calibration (FN from 0.24 to 0.32)",
            "risk_bound_coverage": round(sensor_drift_res["risk_coverage"], 4),
            "false_safety_qual_rate": round(sensor_drift_res["false_safety_qual_rate"], 4),
        },
    }


def build_exp05_report() -> dict[str, Any]:
    """Executes the full Experiment 05 protocol and produces machine-readable report."""
    t0 = time.time()
    sample_sizes = [50, 100, 250, 500, 1000, 2000]

    sensitivity = evaluate_sample_size_sensitivity(sample_sizes, n_reps=1000)
    five_arm = run_five_arm_benchmark(n_reps=1000)
    violations = run_assumption_violation_scenarios(n_reps=1000)
    runtime = time.time() - t0

    return {
        "experiment": "Experiment 05: Prospective Calibration and Statistical Coverage",
        "status": "EXPLORATORY PRE-FREEZE NO-GO",
        "runtime_seconds": round(runtime, 4),
        "target_confidence": 1.0 - DEFAULT_ALPHA_CAL,
        "sample_size_sensitivity": sensitivity,
        "five_arm_benchmark": five_arm,
        "assumption_violations": violations,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Experiment 05 Calibration Study.")
    parser.add_argument("--export", type=str, default=None, help="Export JSON summary to path.")
    args = parser.parse_args()

    report = build_exp05_report()
    out = json.dumps(report, indent=2, sort_keys=True)
    if args.export:
        Path(args.export).write_text(out, encoding="utf-8")
        print(f"Exported Experiment 05 report to {args.export}")
    else:
        print(out)


if __name__ == "__main__":
    main()
