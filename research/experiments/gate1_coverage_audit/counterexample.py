"""Independent mathematical reproduction of the Gate 1 88.82% undercoverage counterexample.

Pure mathematical reference implementation without importing evaluate_confirmatory_v07_1.py.
Computes exact binomial probabilities and closed-form confidence bounds via exact enumeration.

STATUS: EXPLORATORY SCIENTIFIC RESEARCH — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from scipy import stats


@dataclass(frozen=True)
class CounterexampleResult:
    """Exact enumeration result for a specified risk parameter theta."""

    theta: float
    tau_safe: float
    k_clusters: int
    alpha: float
    exact_coverage: float
    exact_fsq: float
    non_monotonicity_detected: bool
    ucb_z0: float
    ucb_z1: float
    z_fail_threshold: int
    probabilities: list[float]
    ucbs: list[float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "theta": self.theta,
            "tau_safe": self.tau_safe,
            "k_clusters": self.k_clusters,
            "alpha": self.alpha,
            "exact_coverage": self.exact_coverage,
            "exact_fsq": self.exact_fsq,
            "non_monotonicity_detected": self.non_monotonicity_detected,
            "ucb_z0": self.ucb_z0,
            "ucb_z1": self.ucb_z1,
            "delta_ucb_z1_minus_z0": self.ucb_z1 - self.ucb_z0,
            "z_fail_threshold": self.z_fail_threshold,
        }


def compute_protocol_ucb(
    z: int,
    k: int = 128,
    alpha: float = 0.050,
) -> float:
    """Exact reproduction of the confirmatory protocol's piecewise UCB formula.

    - z == 0: Exact Clopper-Pearson bound on cluster failure: 1 - alpha^(1/K)
    - 1 <= z < K: Student-t clustered confidence bound with df = K - 1
    - z == K: Degenerate constant positive risk fail-closed: 1.0
    """
    if z < 0 or z > k:
        raise ValueError(f"z must be in [0, {k}], got {z}")

    if z == 0:
        return float(1.0 - (alpha ** (1.0 / k)))
    elif z == k:
        return 1.0
    else:
        # Clustered Bernoulli sample mean and standard error
        m = z / k
        # Sample variance: s^2 = (1 / (k - 1)) * [z * (1 - m)^2 + (k - z) * (0 - m)^2]
        # Algebraically simplifies to: s^2 = z * (k - z) / (k * (k - 1))
        # Standard error: se = s / sqrt(k) = sqrt(z * (k - z) / (k^2 * (k - 1)))
        var_sample = (z * (k - z)) / (k * (k - 1))
        se = math.sqrt(var_sample / k)
        t_crit = float(stats.t.ppf(1.0 - alpha, k - 1))
        return float(min(1.0, m + t_crit * se))


def reproduce_exact_counterexample(
    theta: float = 0.0501,
    tau_safe: float = 0.050,
    k: int = 128,
    alpha: float = 0.050,
) -> CounterexampleResult:
    """Exact enumeration of all K + 1 outcomes under the Bernoulli cluster shock model."""
    probs = [float(stats.binom.pmf(z, k, theta)) for z in range(k + 1)]
    ucbs = [compute_protocol_ucb(z, k, alpha) for z in range(k + 1)]

    # Coverage: P(UCB >= theta)
    cov = float(sum(p for p, u in zip(probs, ucbs) if u >= theta))

    # False Safety Qualification: P(UCB <= tau_safe) when theta > tau_safe
    fsq = float(sum(p for p, u in zip(probs, ucbs) if u <= tau_safe)) if theta > tau_safe else 0.0

    # Non-monotonicity: UCB(1) < UCB(0)
    non_monotonic = bool(ucbs[1] < ucbs[0])

    # Find the maximum z for which UCB <= tau_safe
    z_fsq_max = max(z for z in range(k + 1) if ucbs[z] <= tau_safe)

    return CounterexampleResult(
        theta=theta,
        tau_safe=tau_safe,
        k_clusters=k,
        alpha=alpha,
        exact_coverage=cov,
        exact_fsq=fsq,
        non_monotonicity_detected=non_monotonic,
        ucb_z0=ucbs[0],
        ucb_z1=ucbs[1],
        z_fail_threshold=z_fsq_max,
        probabilities=probs,
        ucbs=ucbs,
    )


def compute_coverage_curve(
    theta_grid: list[float],
    k: int = 128,
    alpha: float = 0.050,
    tau_safe: float = 0.050,
) -> list[dict[str, Any]]:
    """Compute exact coverage and FSQ across a grid of true operational risks."""
    results = []
    for th in theta_grid:
        res = reproduce_exact_counterexample(theta=th, tau_safe=tau_safe, k=k, alpha=alpha)
        results.append({
            "theta": th,
            "coverage": res.exact_coverage,
            "fsq": res.exact_fsq,
            "undercovered": bool(res.exact_coverage < 1.0 - alpha - 1e-6),
            "ucb_z0": res.ucb_z0,
            "ucb_z1": res.ucb_z1,
            "z_fail_threshold": res.z_fail_threshold,
        })
    return results
