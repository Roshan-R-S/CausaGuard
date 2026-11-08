"""Alternative statistical confidence procedures for cluster-robust operational risk.

Implements and evaluates:
1. Procedure A: Existing Gate 1 Piecewise Student-t Procedure
2. Procedure B: Cluster-Level Exact Clopper-Pearson Binomial Bound (Conservative for theta)
3. Procedure C: Maurer-Pontil (2009) Empirical Bernstein Bound (Finite-sample valid for bounded [0,1])
4. Procedure D: Hall (1992) Skewness-Corrected Student-t Bound
5. Procedure E: Sensitivity Bounds under Unknown Intraclass Correlation (rho in [0, 1])

STATUS: EXPLORATORY SCIENTIFIC RESEARCH — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy import stats


@dataclass(frozen=True)
class ConfidenceProcedureResult:
    """Standardized output container for confidence bound procedures."""

    method_name: str
    point_estimate: float
    ucb: float
    alpha: float
    is_valid_finite_sample: bool
    assumptions: str
    gate1_passed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "method_name": self.method_name,
            "point_estimate": self.point_estimate,
            "ucb": self.ucb,
            "alpha": self.alpha,
            "is_valid_finite_sample": self.is_valid_finite_sample,
            "assumptions": self.assumptions,
            "gate1_passed": self.gate1_passed,
        }


# ==============================================================================
# Procedure A: Existing Gate 1 Piecewise Student-t
# ==============================================================================


def ucb_gate1_existing(
    cluster_risks: list[float] | np.ndarray,
    alpha: float = 0.050,
    tau_safe: float = 0.050,
) -> ConfidenceProcedureResult:
    """Existing Gate 1 procedure from evaluate_confirmatory_v07_1.py."""
    r = np.asarray(cluster_risks, dtype=np.float64)
    k = len(r)
    mean_r = float(np.mean(r))
    raw_std = float(np.std(r, ddof=1)) if k > 1 else 0.0
    std_r = 0.0 if (k <= 1 or raw_std <= 1e-12 or np.min(r) == np.max(r)) else raw_std
    se = std_r / np.sqrt(k) if k > 0 else 0.0

    if mean_r == 0.0:
        ucb = float(1.0 - (alpha ** (1.0 / k)))
        method = "existing_gate1_cp_zero_event"
        assumptions = "Bernoulli cluster failure with parameter q; requires zero failures"
        gate1_passed = bool(ucb <= tau_safe)
    elif std_r > 0.0:
        t_crit = float(stats.t.ppf(1.0 - alpha, k - 1))
        ucb = float(min(1.0, mean_r + t_crit * se))
        method = "existing_gate1_student_t"
        assumptions = "CLT asymptotic normality; vulnerable to finite-sample positive skewness"
        gate1_passed = bool(ucb <= tau_safe)
    else:
        # Constant positive risk across all clusters (fail-closed)
        ucb = 1.0
        method = "existing_gate1_degenerate_fail_closed"
        assumptions = "Constant positive risk across all clusters; degenerate t distribution"
        gate1_passed = False

    return ConfidenceProcedureResult(
        method_name=method,
        point_estimate=mean_r,
        ucb=ucb,
        alpha=alpha,
        is_valid_finite_sample=False,
        assumptions=assumptions,
        gate1_passed=gate1_passed,
    )


# ==============================================================================
# Procedure B: Cluster-Level Exact Clopper-Pearson Binomial Bound
# ==============================================================================


def ucb_cluster_clopper_pearson(
    cluster_risks: list[float] | np.ndarray,
    alpha: float = 0.050,
    tau_safe: float = 0.050,
) -> ConfidenceProcedureResult:
    """Exact Clopper-Pearson upper bound on cluster-level failure probability q_cluster.

    Because theta = E[R_k] <= P(R_k > 0) = q_cluster, this is an exact, mathematically
    guaranteed upper bound on operational risk theta valid under arbitrary within-cluster dependence.
    """
    r = np.asarray(cluster_risks, dtype=np.float64)
    k = len(r)
    # Number of clusters with at least one failure
    z = int(np.sum(r > 0.0))
    mean_r = float(np.mean(r))

    if z == 0:
        ucb = float(1.0 - (alpha ** (1.0 / k)))
    elif z == k:
        ucb = 1.0
    else:
        # One-sided 1 - alpha upper bound is Beta.ppf(1 - alpha, z + 1, k - z)
        ucb = float(stats.beta.ppf(1.0 - alpha, z + 1, k - z))

    gate1_passed = bool(ucb <= tau_safe)
    return ConfidenceProcedureResult(
        method_name="cluster_clopper_pearson_exact",
        point_estimate=mean_r,
        ucb=ucb,
        alpha=alpha,
        is_valid_finite_sample=True,
        assumptions="Independent Bernoulli cluster failure indicators; conservative for mean risk theta",
        gate1_passed=gate1_passed,
    )


# ==============================================================================
# Procedure C: Maurer-Pontil (2009) Empirical Bernstein Bound
# ==============================================================================


def ucb_empirical_bernstein_maurer_pontil(
    cluster_risks: list[float] | np.ndarray,
    alpha: float = 0.050,
    tau_safe: float = 0.050,
) -> ConfidenceProcedureResult:
    """Maurer and Pontil (2009) Theorem 4 empirical Bernstein bound.

    Finite-sample valid upper confidence bound for bounded random variables in [0, 1]
    without distributional or normality assumptions.
    """
    r = np.asarray(cluster_risks, dtype=np.float64)
    k = len(r)
    mean_r = float(np.mean(r))
    std_r = float(np.std(r, ddof=1)) if k > 1 else 0.0

    # Log term for Maurer & Pontil (2009) Theorem 4:
    # Theorem 4 uses ln(2 / delta) due to the union bound over true-variance deviation
    # and sample-variance concentration.
    log_term = float(math.log(2.0 / alpha))

    # Maurer & Pontil (2009) Theorem 4 bound for [0, 1] variables
    term_variance = math.sqrt((2.0 * (std_r ** 2) * log_term) / k)
    term_bound = (7.0 * log_term) / (3.0 * (k - 1)) if k > 1 else 1.0

    ucb = float(min(1.0, mean_r + term_variance + term_bound))
    gate1_passed = bool(ucb <= tau_safe)

    return ConfidenceProcedureResult(
        method_name="empirical_bernstein_maurer_pontil",
        point_estimate=mean_r,
        ucb=ucb,
        alpha=alpha,
        is_valid_finite_sample=True,
        assumptions="Independent bounded variables in [0, 1]; finite-sample valid",
        gate1_passed=gate1_passed,
    )


# ==============================================================================
# Procedure D: Hall (1992) Skewness-Corrected Student-t
# ==============================================================================


def ucb_hall_skewness_corrected_t(
    cluster_risks: list[float] | np.ndarray,
    alpha: float = 0.050,
    tau_safe: float = 0.050,
) -> ConfidenceProcedureResult:
    """Hall (1992) Cornish-Fisher / Edgeworth skewness-corrected Student-t bound.

    Expands the critical value to adjust for positive skewness gamma_1:
    t_corrected = t_alpha + (gamma_1 / (6 * sqrt(K))) * (2 * t_alpha^2 + 1).
    """
    r = np.asarray(cluster_risks, dtype=np.float64)
    k = len(r)
    mean_r = float(np.mean(r))
    std_r = float(np.std(r, ddof=1)) if k > 1 else 0.0

    if std_r <= 1e-12:
        if mean_r == 0.0:
            ucb = float(1.0 - (alpha ** (1.0 / k)))
        else:
            ucb = 1.0
    else:
        se = std_r / np.sqrt(k)
        t_base = float(stats.t.ppf(1.0 - alpha, k - 1))

        # Sample skewness (Fisher-Pearson coefficient of skewness)
        m3 = float(np.mean((r - mean_r) ** 3))
        skew = m3 / (std_r ** 3) if std_r > 0 else 0.0

        # Hall (1992) second-order Edgeworth adjustment term
        t_adj = t_base + (skew / (6.0 * math.sqrt(k))) * (2.0 * (t_base ** 2) + 1.0)
        ucb = float(min(1.0, mean_r + t_adj * se))

    gate1_passed = bool(ucb <= tau_safe)
    return ConfidenceProcedureResult(
        method_name="hall_skewness_corrected_t",
        point_estimate=mean_r,
        ucb=ucb,
        alpha=alpha,
        is_valid_finite_sample=False,
        assumptions="Asymptotic Edgeworth expansion; corrects first-order skewness error",
        gate1_passed=gate1_passed,
    )


# ==============================================================================
# Procedure E: Sensitivity Bounds under Unknown Intraclass Correlation
# ==============================================================================


def ucb_icc_sensitivity_bounds(
    cluster_risks: list[float] | np.ndarray,
    n_cases_per_cluster: int = 400,
    rho_grid: list[float] | None = None,
    alpha: float = 0.050,
) -> dict[str, Any]:
    """Compute sensitivity bounds across varying assumed intraclass correlations rho in [0, 1].

    Effective cluster size: K_eff = (K * N) / (1 + (N - 1) * rho).
    """
    if rho_grid is None:
        rho_grid = [0.0, 0.01, 0.05, 0.10, 0.25, 0.50, 0.80, 1.0]

    r = np.asarray(cluster_risks, dtype=np.float64)
    k = len(r)
    n = n_cases_per_cluster
    mean_r = float(np.mean(r))

    bounds_by_rho = {}
    for rho in rho_grid:
        deff = 1.0 + (n - 1.0) * rho
        k_eff = (k * n) / deff
        # Wilson or Clopper-Pearson equivalent effective sample size
        se_eff = math.sqrt(mean_r * (1.0 - mean_r) / k_eff) if (0.0 < mean_r < 1.0) else 0.0
        z_crit = float(stats.norm.ppf(1.0 - alpha))
        ucb_rho = float(min(1.0, mean_r + z_crit * se_eff))
        bounds_by_rho[f"rho_{rho:.2f}"] = {
            "rho": rho,
            "design_effect": deff,
            "k_effective": k_eff,
            "ucb": ucb_rho,
        }

    return {
        "point_estimate": mean_r,
        "k_clusters": k,
        "n_cases_per_cluster": n,
        "sensitivity_curve": bounds_by_rho,
    }

