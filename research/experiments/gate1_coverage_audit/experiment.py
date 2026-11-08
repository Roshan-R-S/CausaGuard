"""Comprehensive falsification experiment runner for Gate 1 statistical safety bounds.

Performs:
1. Exact mathematical reproduction of the 88.82% undercoverage and 11.18% FSQ counterexample.
2. Comparison across 4 confidence procedures:
   - Existing Gate 1 Piecewise Student-t
   - Cluster-level Clopper-Pearson Exact Binomial Bound
   - Maurer-Pontil (2009) Empirical Bernstein Bound
   - Hall (1992) Skewness-Corrected Student-t Bound
3. Parameter sweeps across:
   - True risk theta in [0.010, 0.080]
   - Cluster counts K in {32, 64, 128, 256}
   - Intraclass correlation rho in [0.0, 1.0] (Beta-Binomial)
   - Cluster heterogeneity mixtures
4. Measures coverage, FSQ, unnecessary rejection, width, and computational overhead.
5. Emits machine-readable evidence to research/reviews/v071-gate1-statistical-coverage-audit.json.

STATUS: EXPLORATORY SCIENTIFIC RESEARCH — PRE-FREEZE NO-GO.
DO NOT MODIFY PRODUCTION CONTROLLER OR CONFIRMATORY PROTOCOLS.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

from .counterexample import (
    reproduce_exact_counterexample,
)
from .estimand import (
    ESTIMAND_CLUSTER_ANY_HARM,
    ESTIMAND_GATE1_STANDARD,
    ESTIMAND_MEAN_CLUSTER_RATE,
    ESTIMAND_PER_CASE,
)
from .methods import (
    ucb_cluster_clopper_pearson,
    ucb_empirical_bernstein_maurer_pontil,
    ucb_gate1_existing,
    ucb_hall_skewness_corrected_t,
)

ROOT = Path(__file__).resolve().parents[3]

EXPLORATORY_THETA_GRID = [
    0.010,
    0.020,
    0.023,
    0.025,
    0.035,
    0.040,
    0.045,
    0.049,
    0.050,
    0.0501,
    0.051,
    0.055,
    0.060,
    0.070,
    0.080,
]


def evaluate_exact_bernoulli_shock_methods(
    theta: float,
    k: int = 128,
    alpha: float = 0.050,
    tau_safe: float = 0.050,
) -> dict[str, Any]:
    """Exact enumeration over all K + 1 outcomes for four confidence procedures."""
    probs = [float(stats.binom.pmf(z, k, theta)) for z in range(k + 1)]

    methods = {
        "existing_gate1": [],
        "cluster_clopper_pearson": [],
        "empirical_bernstein": [],
        "hall_skewness_corrected": [],
    }

    # Evaluate bounds for each z in 0..K
    for z in range(k + 1):
        if z == 0:
            cluster_risks = np.zeros(k, dtype=np.float64)
        elif z == k:
            cluster_risks = np.ones(k, dtype=np.float64)
        else:
            cluster_risks = np.array([1.0] * z + [0.0] * (k - z), dtype=np.float64)

        methods["existing_gate1"].append(ucb_gate1_existing(cluster_risks, alpha, tau_safe).ucb)
        methods["cluster_clopper_pearson"].append(ucb_cluster_clopper_pearson(cluster_risks, alpha, tau_safe).ucb)
        methods["empirical_bernstein"].append(ucb_empirical_bernstein_maurer_pontil(cluster_risks, alpha, tau_safe).ucb)
        methods["hall_skewness_corrected"].append(ucb_hall_skewness_corrected_t(cluster_risks, alpha, tau_safe).ucb)

    evaluations = {}
    for name, ucbs in methods.items():
        # Coverage: P(UCB >= theta)
        cov = float(sum(p for p, u in zip(probs, ucbs) if u >= theta))
        # False Safety Qualification: P(UCB <= tau_safe) when theta > tau_safe
        fsq = float(sum(p for p, u in zip(probs, ucbs) if u <= tau_safe)) if theta > tau_safe else 0.0
        # Unnecessary Rejection: P(UCB > tau_safe) when theta <= tau_safe
        unnecessary_rej = float(sum(p for p, u in zip(probs, ucbs) if u > tau_safe)) if theta <= tau_safe else 0.0
        # Expected interval width: E[UCB - theta]
        expected_ucb = float(sum(p * u for p, u in zip(probs, ucbs)))
        mean_width = float(expected_ucb - theta)
        # Check non-monotonicity: UCB(1) < UCB(0)
        non_monotonic = bool(ucbs[1] < ucbs[0])

        evaluations[name] = {
            "coverage": cov,
            "fsq": fsq,
            "unnecessary_rejection": unnecessary_rej,
            "expected_ucb": expected_ucb,
            "mean_width": mean_width,
            "ucb_z0": ucbs[0],
            "ucb_z1": ucbs[1],
            "non_monotonic": non_monotonic,
            "undercovered": bool(cov < 1.0 - alpha - 1e-6),
        }

    return evaluations


def evaluate_beta_binomial_monte_carlo(
    theta: float = 0.0501,
    rho: float = 0.10,
    k: int = 128,
    n: int = 400,
    alpha: float = 0.050,
    tau_safe: float = 0.050,
    n_replications: int = 10000,
    random_seed: int = 40001001,  # Safe non-evaluative exploratory seed
) -> dict[str, Any]:
    """Monte Carlo evaluation under Beta-Binomial within-cluster correlation."""
    rng = np.random.default_rng(random_seed)

    if rho <= 1e-6:
        # Binomial independent cases within cluster
        counts = rng.binomial(n, theta, size=(n_replications, k))
        cluster_risks = counts / n
    elif rho >= 0.999:
        # Bernoulli common shock across all cases in cluster
        shocks = rng.binomial(1, theta, size=(n_replications, k))
        cluster_risks = shocks.astype(np.float64)
    else:
        # Beta-Binomial: beta parameters a, b
        a = theta * (1.0 - rho) / rho
        b = (1.0 - theta) * (1.0 - rho) / rho
        # Sample cluster probabilities p_k ~ Beta(a, b)
        p_clusters = rng.beta(a, b, size=(n_replications, k))
        counts = rng.binomial(n, p_clusters)
        cluster_risks = counts / n

    results = {}
    methods_fns = {
        "existing_gate1": ucb_gate1_existing,
        "cluster_clopper_pearson": ucb_cluster_clopper_pearson,
        "empirical_bernstein": ucb_empirical_bernstein_maurer_pontil,
        "hall_skewness_corrected": ucb_hall_skewness_corrected_t,
    }

    for name, fn in methods_fns.items():
        covered = 0
        fsq_count = 0
        unnecessary_rej_count = 0
        ucb_sum = 0.0

        t0 = time.perf_counter_ns()
        for rep in range(n_replications):
            r = cluster_risks[rep]
            res = fn(r, alpha=alpha, tau_safe=tau_safe)
            u = res.ucb
            ucb_sum += u
            if u >= theta:
                covered += 1
            if theta > tau_safe and u <= tau_safe:
                fsq_count += 1
            if theta <= tau_safe and u > tau_safe:
                unnecessary_rej_count += 1
        t1 = time.perf_counter_ns()
        overhead_us = (t1 - t0) / (n_replications * 1000.0)

        cov_rate = covered / n_replications
        # Wilson score confidence interval on coverage rate
        ci_low, ci_high = compute_wilson_ci(covered, n_replications, 0.05)

        results[name] = {
            "replications": n_replications,
            "empirical_coverage": cov_rate,
            "coverage_95_ci": [ci_low, ci_high],
            "fsq_rate": fsq_count / n_replications,
            "unnecessary_rejection_rate": unnecessary_rej_count / n_replications,
            "mean_ucb": ucb_sum / n_replications,
            "mean_overhead_us": overhead_us,
            "undercovered": bool(ci_high < 1.0 - alpha),
        }

    return results


def compute_wilson_ci(successes: int, trials: int, alpha: float = 0.05) -> tuple[float, float]:
    """Wilson score confidence interval for a binomial proportion."""
    if trials == 0:
        return 0.0, 1.0
    p = successes / trials
    z = float(stats.norm.ppf(1.0 - alpha / 2.0))
    denom = 1.0 + (z ** 2) / trials
    center = (p + (z ** 2) / (2.0 * trials)) / denom
    half = (z * math.sqrt(p * (1.0 - p) / trials + (z ** 2) / (4.0 * (trials ** 2)))) / denom
    return float(max(0.0, center - half)), float(min(1.0, center + half))


def build_audit_evidence_report() -> dict[str, Any]:
    """Execute full audit suite and compile scientific evidence JSON."""
    # 1. Exact reference counterexample reproduction
    exact_repro = reproduce_exact_counterexample(theta=0.0501, tau_safe=0.050, k=128, alpha=0.050)

    # 2. Coverage across exploratory theta grid
    exact_grid = {}
    for th in EXPLORATORY_THETA_GRID:
        exact_grid[f"theta_{th:.4f}"] = evaluate_exact_bernoulli_shock_methods(
            theta=th, k=128, alpha=0.050, tau_safe=0.050
        )

    # 3. Cluster sample size sweep (K in 32, 64, 128, 256) at theta = 0.0501
    k_sweep = {}
    for k_val in [32, 64, 128, 256]:
        k_sweep[f"k_{k_val}"] = evaluate_exact_bernoulli_shock_methods(
            theta=0.0501, k=k_val, alpha=0.050, tau_safe=0.050
        )

    # 4. Monte Carlo evaluation across ICC rho in [0.0, 0.05, 0.10, 0.25, 0.50, 0.80, 1.0]
    icc_sweep = {}
    for rho_val in [0.0, 0.05, 0.10, 0.25, 0.50, 0.80, 1.0]:
        icc_sweep[f"rho_{rho_val:.2f}"] = evaluate_beta_binomial_monte_carlo(
            theta=0.0501,
            rho=rho_val,
            k=128,
            n=400,
            n_replications=2000,  # Fast reproducible sweep
            random_seed=40001001 + int(rho_val * 100),
        )

    paths = [
        "research/experiments/gate1_coverage_audit/__init__.py",
        "research/experiments/gate1_coverage_audit/estimand.py",
        "research/experiments/gate1_coverage_audit/counterexample.py",
        "research/experiments/gate1_coverage_audit/methods.py",
        "research/experiments/gate1_coverage_audit/experiment.py",
    ]
    hashes = {}
    for p in paths:
        fp = ROOT / p
        if fp.exists():
            hashes[p] = hashlib.sha256(fp.read_bytes()).hexdigest()

    return {
        "title": "CausaGuard Gate 1 Statistical Safety-Bound Falsification Audit",
        "status": "EXPLORATORY SCIENTIFIC RESEARCH — PRE-FREEZE NO-GO",
        "baseline_commit": "cfa841ad5fd6dd5ad300b60554a6570b840a66db",
        "python_version": sys.version.split()[0],
        "production_authorization_modified": False,
        "confirmatory_seeds_used": False,
        "source_hashes": hashes,
        "formal_estimands": {
            "per_case_risk": ESTIMAND_PER_CASE.definition,
            "cluster_any_harm": ESTIMAND_CLUSTER_ANY_HARM.definition,
            "mean_cluster_rate": ESTIMAND_MEAN_CLUSTER_RATE.definition,
            "gate1_safety_standard": ESTIMAND_GATE1_STANDARD.definition,
        },
        "counterexample_reproduction": exact_repro.to_dict(),
        "exact_theta_grid_comparison": exact_grid,
        "cluster_sample_size_sweep": k_sweep,
        "intraclass_correlation_sweep": icc_sweep,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Path to write JSON evidence report")
    parser.add_argument("--reproduce-exact", action="store_true", help="Print exact counterexample reproduction")
    parser.add_argument("--assert-claims", action="store_true", help="Assert exact numerical reproduction of 88.82% and 11.18%")
    args = parser.parse_args(argv)

    try:
        report = build_audit_evidence_report()
    except Exception as e:
        sys.stderr.write(f"Error executing audit: {e}\n")
        return 2

    repro = report["counterexample_reproduction"]
    if args.reproduce_exact or not args.output:
        print("=" * 80)
        print("GATE 1 STATISTICAL SAFETY-BOUND FALSIFICATION: EXACT COUNTEREXAMPLE")
        print("=" * 80)
        print("Nominal Confidence Level:          1 - alpha = 0.950 (95.0%)")
        print("Operational Risk Threshold (tau):  0.050")
        print(f"Modeled True Risk (theta):         {repro['theta']:.4f}")
        print(f"Number of Clusters (K):            {repro['k_clusters']}")
        print(f"Exact Undercoverage Probability:   {1.0 - repro['exact_coverage']:.10f} ({100.0 * (1.0 - repro['exact_coverage']):.4f}%)")
        print(f"Exact Coverage (Claimed >= 95%):   {repro['exact_coverage']:.10f} ({100.0 * repro['exact_coverage']:.4f}%)")
        print(f"Exact False Safety Qualification:  {repro['exact_fsq']:.10f} ({100.0 * repro['exact_fsq']:.4f}%)")
        print(f"Non-Monotonicity (UCB[1] < UCB[0]): {repro['non_monotonicity_detected']} (UCB[0]={repro['ucb_z0']:.6f}, UCB[1]={repro['ucb_z1']:.6f})")
        print("=" * 80)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(report, indent=2, sort_keys=True)
        args.output.write_text(serialized + "\n", encoding="utf-8")
        print(f"Report written to {args.output}")

    if args.assert_claims:
        # Check that 88.8242% and 11.1758% are matched to 4 decimal places
        cov_pct = 100.0 * repro["exact_coverage"]
        fsq_pct = 100.0 * repro["exact_fsq"]
        if abs(cov_pct - 88.8242) > 0.0001:
            sys.stderr.write(f"Assertion failed: Coverage was {cov_pct:.6f}%, expected 88.8242%\n")
            return 1
        if abs(fsq_pct - 11.1758) > 0.0001:
            sys.stderr.write(f"Assertion failed: FSQ was {fsq_pct:.6f}%, expected 11.1758%\n")
            return 1
        if not repro["non_monotonicity_detected"]:
            sys.stderr.write("Assertion failed: Non-monotonicity not detected.\n")
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
