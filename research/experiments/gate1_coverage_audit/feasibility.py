"""Gate 1 statistical feasibility, sample size sizing, and monotonicity audit.

Provides independent mathematical functions to evaluate:
- Smallest achievable UCB at zero failures across sample sizes K.
- Minimum cluster count K required for Gate 1 qualification (UCB <= tau_safe).
- Maximum failure count Z_max permitted to pass Gate 1.
- Exact finite-sample coverage, false safety qualification (FSQ), and unnecessary rejection (UR).
- Proof and demonstration of monotonicity vs non-monotonicity across data vectors.
- Impact of unequal cluster sizes and intra-cluster correlation.

Research status: EXPLORATORY RESEARCH ONLY -- PRE-FREEZE NO-GO.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy import stats

from research.experiments.gate1_coverage_audit import (
    PRE_FREEZE_NO_GO,
    PRODUCTION_AUTHORIZATION_ENABLED,
)

assert PRE_FREEZE_NO_GO is True
assert PRODUCTION_AUTHORIZATION_ENABLED is False


@dataclass(frozen=True)
class FeasibilityMetrics:
    k_clusters: int
    method_name: str
    smallest_achievable_ucb: float
    qualification_possible_at_zero_events: bool
    max_passing_z: int  # -1 if impossible even at z=0
    min_required_k_at_zero_events: int


@dataclass(frozen=True)
class PolicyRiskEvaluation:
    k_clusters: int
    theta: float
    method_name: str
    coverage: float
    false_safety_qualification: float
    unnecessary_rejection: float
    qualification_power: float
    expected_ucb: float
    expected_width: float


def compute_zero_event_ucb(k: int, alpha: float = 0.050, method: str = "clopper_pearson") -> float:
    """Compute smallest achievable UCB when all observations are zero."""
    if k < 1:
        return 1.0

    if method in ("clopper_pearson", "existing_gate1"):
        return float(1.0 - (alpha ** (1.0 / k)))
    elif method == "empirical_bernstein":
        log_term = math.log(2.0 / alpha)
        return float((7.0 * log_term) / (3.0 * (k - 1))) if k > 1 else 1.0
    elif method == "hoeffding":
        log_term = math.log(1.0 / alpha)
        return float(math.sqrt(log_term / (2.0 * k)))
    else:
        raise ValueError(f"Unknown method: {method}")


def find_min_k_for_qualification(alpha: float = 0.050, tau_safe: float = 0.050, method: str = "clopper_pearson") -> int:
    """Find minimum cluster count K such that UCB(z=0) <= tau_safe."""
    if method in ("clopper_pearson", "existing_gate1"):
        # 1 - alpha^(1/K) <= tau_safe  <=>  K >= ln(alpha) / ln(1 - tau_safe)
        return int(math.ceil(math.log(alpha) / math.log(1.0 - tau_safe)))
    elif method == "empirical_bernstein":
        # Maurer & Pontil (2009) Theorem 4: 7 ln(2/alpha) / (3(K - 1)) <= tau_safe
        # <=> K - 1 >= 7 ln(2/alpha) / (3 tau_safe)
        log_term = math.log(2.0 / alpha)
        return int(math.ceil((7.0 * log_term) / (3.0 * tau_safe) + 1.0))
    elif method == "hoeffding":
        # sqrt(ln(1/alpha) / (2K)) <= tau_safe <=> K >= ln(1/alpha) / (2 tau_safe^2)
        log_term = math.log(1.0 / alpha)
        return int(math.ceil(log_term / (2.0 * (tau_safe ** 2))))
    else:
        raise ValueError(f"Unknown method: {method}")


def find_max_passing_z(
    k: int,
    alpha: float = 0.050,
    tau_safe: float = 0.050,
    method: str = "clopper_pearson",
) -> int:
    """Find maximum integer failure count Z <= K such that UCB(Z) <= tau_safe.

    Returns -1 if UCB > tau_safe even at Z=0.
    """
    z_max = -1
    log_term_eb = math.log(2.0 / alpha)

    for z in range(k + 1):
        if method == "clopper_pearson":
            if z == 0:
                u = 1.0 - (alpha ** (1.0 / k))
            elif z == k:
                u = 1.0
            else:
                u = float(stats.beta.ppf(1.0 - alpha, z + 1, k - z))
        elif method == "existing_gate1":
            if z == 0:
                u = 1.0 - (alpha ** (1.0 / k))
            else:
                m = z / k
                s2 = (z * (1.0 - m) ** 2 + (k - z) * (0.0 - m) ** 2) / (k - 1)
                s = math.sqrt(s2)
                u = min(1.0, m + float(stats.t.ppf(1.0 - alpha, k - 1)) * s / math.sqrt(k))
        elif method == "empirical_bernstein":
            m = z / k
            s2 = (z * (1.0 - m) ** 2 + (k - z) * (0.0 - m) ** 2) / (k - 1) if k > 1 else 0.0
            s = math.sqrt(s2)
            bound_term = (7.0 * log_term_eb) / (3.0 * (k - 1)) if k > 1 else 1.0
            var_term = math.sqrt(2.0 * s2 * log_term_eb / k)
            u = min(1.0, m + var_term + bound_term)
        else:
            raise ValueError(f"Unknown method: {method}")

        if u <= tau_safe:
            z_max = z
        else:
            break

    return z_max


def evaluate_cluster_count_feasibility(
    k_values: list[int],
    alpha: float = 0.050,
    tau_safe: float = 0.050,
) -> dict[str, list[FeasibilityMetrics]]:
    """Evaluate feasibility metrics across cluster counts for all candidate methods."""
    results: dict[str, list[FeasibilityMetrics]] = {
        "existing_gate1": [],
        "clopper_pearson": [],
        "empirical_bernstein": [],
    }

    for method in results:
        min_k = find_min_k_for_qualification(alpha=alpha, tau_safe=tau_safe, method=method)
        for k in k_values:
            ucb_0 = compute_zero_event_ucb(k=k, alpha=alpha, method=method)
            pass_0 = bool(ucb_0 <= tau_safe)
            z_max = find_max_passing_z(k=k, alpha=alpha, tau_safe=tau_safe, method=method)
            results[method].append(
                FeasibilityMetrics(
                    k_clusters=k,
                    method_name=method,
                    smallest_achievable_ucb=ucb_0,
                    qualification_possible_at_zero_events=pass_0,
                    max_passing_z=z_max,
                    min_required_k_at_zero_events=min_k,
                )
            )

    return results


def evaluate_policy_risk_performance(
    k: int,
    theta: float,
    alpha: float = 0.050,
    tau_safe: float = 0.050,
) -> dict[str, PolicyRiskEvaluation]:
    """Calculate exact binomial coverage, FSQ, UR, power, and expected UCB under Bernoulli shock."""
    probs = [float(stats.binom.pmf(z, k, theta)) for z in range(k + 1)]
    log_term_eb = math.log(2.0 / alpha)

    # Compute UCBs for all z in 0..k
    ucbs: dict[str, list[float]] = {
        "existing_gate1": [],
        "clopper_pearson": [],
        "empirical_bernstein": [],
    }

    for z in range(k + 1):
        # Existing Gate 1
        if z == 0:
            u_ex = 1.0 - (alpha ** (1.0 / k))
        else:
            m = z / k
            s2 = (z * (1.0 - m) ** 2 + (k - z) * (0.0 - m) ** 2) / (k - 1)
            s = math.sqrt(s2)
            u_ex = min(1.0, m + float(stats.t.ppf(1.0 - alpha, k - 1)) * s / math.sqrt(k))
        ucbs["existing_gate1"].append(u_ex)

        # Clopper-Pearson
        if z == 0:
            u_cp = 1.0 - (alpha ** (1.0 / k))
        elif z == k:
            u_cp = 1.0
        else:
            u_cp = float(stats.beta.ppf(1.0 - alpha, z + 1, k - z))
        ucbs["clopper_pearson"].append(u_cp)

        # Empirical Bernstein (Maurer & Pontil 2009 Theorem 4: ln(2/delta))
        m = z / k
        s2 = (z * (1.0 - m) ** 2 + (k - z) * (0.0 - m) ** 2) / (k - 1) if k > 1 else 0.0
        var_term = math.sqrt(2.0 * s2 * log_term_eb / k)
        bound_term = (7.0 * log_term_eb) / (3.0 * (k - 1)) if k > 1 else 1.0
        ucbs["empirical_bernstein"].append(min(1.0, m + var_term + bound_term))

    results = {}
    for method, u_list in ucbs.items():
        cov = float(sum(p for p, u in zip(probs, u_list) if u >= theta))
        fsq = float(sum(p for p, u in zip(probs, u_list) if u <= tau_safe)) if theta > tau_safe else 0.0
        ur = float(sum(p for p, u in zip(probs, u_list) if u > tau_safe)) if theta <= tau_safe else 0.0
        power = float(sum(p for p, u in zip(probs, u_list) if u <= tau_safe)) if theta <= tau_safe else 0.0
        exp_ucb = float(sum(p * u for p, u in zip(probs, u_list)))
        exp_width = float(sum(p * (u - theta) for p, u in zip(probs, u_list)))

        results[method] = PolicyRiskEvaluation(
            k_clusters=k,
            theta=theta,
            method_name=method,
            coverage=cov,
            false_safety_qualification=fsq,
            unnecessary_rejection=ur,
            qualification_power=power,
            expected_ucb=exp_ucb,
            expected_width=exp_width,
        )

    return results


def demonstrate_variance_non_monotonicity(k: int = 128, alpha: float = 0.050) -> dict[str, Any]:
    """Mathematically demonstrates that methods relying on sample standard deviation

    (Student-t and Empirical Bernstein) are NOT universally monotonic with respect
    to individual cluster risk increases.

    Setup: K-1 clusters with R_k = 1.0, 1 cluster with R_0 = 0.0.
    If R_0 is increased from 0.0 to 0.1, the unclipped UCB decreases because the
    reduction in sample variance exceeds the increase in the sample mean.
    """
    log_term_eb = math.log(2.0 / alpha)
    c_eb = math.sqrt((2.0 * log_term_eb) / k)
    t_crit = float(stats.t.ppf(1.0 - alpha, k - 1))
    c_t = t_crit / math.sqrt(k)
    term_bound_eb = (7.0 * log_term_eb) / (3.0 * (k - 1))

    # Initial vector: 1 zero, K-1 ones
    base = np.ones(k, dtype=np.float64)
    base[0] = 0.0

    m0 = float(np.mean(base))
    s0 = float(np.std(base, ddof=1))
    eb_ucb0 = m0 + c_eb * s0 + term_bound_eb
    t_ucb0 = m0 + c_t * s0

    # Perturbed vector: cluster 0 risk increased to 0.10
    mod = base.copy()
    mod[0] = 0.10
    m1 = float(np.mean(mod))
    s1 = float(np.std(mod, ddof=1))
    eb_ucb1 = m1 + c_eb * s1 + term_bound_eb
    t_ucb1 = m1 + c_t * s1

    # Exact Clopper-Pearson on the same vectors
    # At base: Z = K - 1 (127 ones)
    z0 = int(np.sum(base > 0))
    cp_ucb0 = float(stats.beta.ppf(1.0 - alpha, z0 + 1, k - z0))
    # At mod: Z = K (128 positive clusters)
    cp_ucb1 = 1.0

    return {
        "k": k,
        "base_vector_description": "1 cluster with risk 0.0, 127 clusters with risk 1.0",
        "perturbed_vector_description": "Cluster 0 risk increased from 0.0 to 0.10 (strict risk increase)",
        "empirical_bernstein": {
            "initial_unclipped_ucb": eb_ucb0,
            "perturbed_unclipped_ucb": eb_ucb1,
            "delta_ucb": eb_ucb1 - eb_ucb0,
            "is_non_monotonic": bool(eb_ucb1 < eb_ucb0),
        },
        "student_t": {
            "initial_unclipped_ucb": t_ucb0,
            "perturbed_unclipped_ucb": t_ucb1,
            "delta_ucb": t_ucb1 - t_ucb0,
            "is_non_monotonic": bool(t_ucb1 < t_ucb0),
        },
        "clopper_pearson": {
            "initial_ucb": cp_ucb0,
            "perturbed_ucb": cp_ucb1,
            "delta_ucb": cp_ucb1 - cp_ucb0,
            "is_non_monotonic": bool(cp_ucb1 < cp_ucb0),
        },
    }
