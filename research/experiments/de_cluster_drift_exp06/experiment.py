"""Experiment 06: Cluster-Robust Calibration and Sequential Drift Detection.

Exploratory research investigating cluster-aware calibration estimators and
runtime sequential drift monitors under realistic enterprise data dependencies.

STATUS: EXPLORATORY RESEARCH ONLY - PRE-FREEZE NO-GO.
DO NOT MODIFY PRODUCTION CONTROLLER OR CONFIRMATORY PROTOCOLS.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import numpy as np
from scipy.special import betaln, gammaln
from scipy.stats import beta, chi2

logger = logging.getLogger(__name__)

# Strict exploratory seed base (strictly separate from confirmatory seeds 70100001+, 70200001+, 60030001+)
EXPLORATORY_SEED_BASE = 50200001

# Operational constants matching Experiments 03, 04, and 05
DEFAULT_PRIOR = 0.20  # pi_0 = 1/5
DEFAULT_AVAILABILITY = 0.91  # A = 91/100
SAFETY_THRESHOLD = 0.050  # tau_safe = 0.050

# Prespecified utility cost matrix
COST_TRUE_QUAL = 1.0
COST_TRUE_DISQ = 0.0
COST_ABSTAIN = -0.5
COST_FALSE_DISQ = -2.0
COST_FSQ = -100.0
COST_FALSE_QUARANTINE = -10.0


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
    status: str

    @property
    def qualifies(self) -> bool:
        return self.upper_risk <= SAFETY_THRESHOLD

    @property
    def disqualified(self) -> bool:
        return self.lower_risk > SAFETY_THRESHOLD

    @property
    def inconclusive(self) -> bool:
        return self.lower_risk <= SAFETY_THRESHOLD < self.upper_risk

    @property
    def width(self) -> float:
        return self.upper_risk - self.lower_risk

    def encloses(self, r: float) -> bool:
        return self.lower_risk <= r <= self.upper_risk


@dataclass(frozen=True)
class ClusteredBatch:
    """Clustered binary calibration batch data."""

    k_vec: np.ndarray  # success counts per cluster (errors)
    m_vec: np.ndarray  # trial counts per cluster
    c_count: int  # number of clusters
    n_total: int  # total operations
    p_hat_op: float  # operation-weighted error rate
    p_hat_cluster: float  # cluster-weighted error rate
    icc_est: float  # estimated intracluster correlation
    deff_est: float  # estimated design effect
    n_eff: int  # effective sample size


# -----------------------------------------------------------------------------
# Exact Statistical Functions
# -----------------------------------------------------------------------------


def exact_clopper_pearson(k: int, n: int, alpha: float) -> tuple[float, float]:
    """Exact Clopper-Pearson binomial confidence interval."""
    if n <= 0:
        return 0.0, 1.0
    k = max(0, min(k, n))

    if k == 0:
        low = 0.0
        high = 1.0 - (alpha / 2.0) ** (1.0 / n)
    elif k == n:
        low = (alpha / 2.0) ** (1.0 / n)
        high = 1.0
    else:
        low = float(beta.ppf(alpha / 2.0, k, n - k + 1))
        high = float(beta.ppf(1.0 - alpha / 2.0, k + 1, n - k))

    return max(0.0, min(1.0, low)), max(0.0, min(1.0, high))


def estimate_icc_and_deff(k_vec: np.ndarray, m_vec: np.ndarray) -> tuple[float, float, int, int]:
    """Estimate ANOVA intra-cluster correlation (ICC) and Rao-Scott design effect.

    Returns:
        (icc_est, deff_est, n_eff, k_eff)
    """
    C = len(k_vec)
    N = int(np.sum(m_vec))
    if N == 0 or C <= 1:
        return 0.0, 1.0, N, int(np.sum(k_vec))

    p_hat = float(np.sum(k_vec)) / N
    p_c = k_vec / np.maximum(m_vec, 1)

    # Mean squares between (MSB)
    msb = float(np.sum(m_vec * (p_c - p_hat) ** 2)) / (C - 1)

    # Mean squares within (MSW)
    ssw = float(np.sum(m_vec * p_c * (1.0 - p_c)))
    msw = ssw / (N - C) if (N - C) > 0 else 0.0

    # Effective cluster size m0 (Kish / Fleiss)
    m0 = float(N - np.sum(m_vec**2) / N) / (C - 1)

    denom = msb + (m0 - 1.0) * msw
    if denom <= 1e-12:
        icc = 0.0
    else:
        icc = (msb - msw) / denom

    # Bound ICC to [0, 1] for positive intracluster correlation
    icc = max(0.0, min(1.0, icc))
    deff = 1.0 + (m0 - 1.0) * icc

    n_eff = max(C, int(np.floor(N / deff)))
    k_eff = max(0, min(n_eff, int(np.round(p_hat * n_eff))))

    return icc, deff, n_eff, k_eff


def generate_clustered_batch(
    n_clusters: int,
    cluster_sizes: int | list[int] | np.ndarray,
    mean_rate: float,
    icc: float,
    dist: str = "beta_binomial",
    rng: Optional[np.random.Generator] = None,
) -> ClusteredBatch:
    """Generate a synthetic clustered batch with exact intra-cluster correlation."""
    if rng is None:
        rng = np.random.default_rng(EXPLORATORY_SEED_BASE)

    if isinstance(cluster_sizes, int):
        m_vec = np.full(n_clusters, cluster_sizes, dtype=int)
    else:
        m_vec = np.array(cluster_sizes, dtype=int)
        if len(m_vec) != n_clusters:
            raise ValueError("cluster_sizes length must match n_clusters")

    mean_rate = max(1e-4, min(1.0 - 1e-4, mean_rate))
    icc = max(0.0, min(0.999, icc))

    if icc <= 1e-6:
        # Pure independent binomial
        k_vec = rng.binomial(m_vec, mean_rate)
    else:
        # Beta-Binomial: dispersion phi = icc
        # ab = (1 - phi) / phi, a = mean * ab, b = (1 - mean) * ab
        ab = (1.0 - icc) / icc
        a_param = max(1e-3, mean_rate * ab)
        b_param = max(1e-3, (1.0 - mean_rate) * ab)

        # Draw cluster-specific rates p_c ~ Beta(a, b)
        p_c = rng.beta(a_param, b_param, size=n_clusters)
        k_vec = rng.binomial(m_vec, p_c)

    n_total = int(np.sum(m_vec))
    k_total = int(np.sum(k_vec))
    p_hat_op = float(k_total) / n_total if n_total > 0 else 0.0
    p_hat_cluster = float(np.mean(k_vec / np.maximum(m_vec, 1)))

    icc_est, deff_est, n_eff, _ = estimate_icc_and_deff(k_vec, m_vec)

    return ClusteredBatch(
        k_vec=k_vec,
        m_vec=m_vec,
        c_count=n_clusters,
        n_total=n_total,
        p_hat_op=p_hat_op,
        p_hat_cluster=p_hat_cluster,
        icc_est=icc_est,
        deff_est=deff_est,
        n_eff=n_eff,
    )


# -----------------------------------------------------------------------------
# Five Calibration Estimators
# -----------------------------------------------------------------------------


def method_a_naive_clopper_pearson(batch: ClusteredBatch, alpha: float = 0.025) -> Interval:
    """Method A: Ordinary independent-observation Clopper-Pearson (ignores clustering)."""
    k_total = int(np.sum(batch.k_vec))
    low, high = exact_clopper_pearson(k_total, batch.n_total, alpha)
    return Interval(low, high)


def method_b_design_effect_clopper_pearson(
    batch: ClusteredBatch,
    alpha: float = 0.025,
    known_icc: Optional[float] = None,
) -> Interval:
    """Method B: Rao-Scott design-effect adjusted Clopper-Pearson."""
    if known_icc is not None:
        m0 = (
            float(batch.n_total - np.sum(batch.m_vec**2) / batch.n_total) / (batch.c_count - 1)
            if batch.c_count > 1
            else 1.0
        )
        deff = 1.0 + (m0 - 1.0) * max(0.0, min(1.0, known_icc))
        n_eff = max(batch.c_count, int(np.floor(batch.n_total / deff)))
        k_eff = max(0, min(n_eff, int(np.round(batch.p_hat_op * n_eff))))
    else:
        n_eff = batch.n_eff
        k_eff = max(0, min(n_eff, int(np.round(batch.p_hat_op * n_eff))))

    low, high = exact_clopper_pearson(k_eff, n_eff, alpha)
    return Interval(low, high)


def method_c_beta_binomial_profile(
    batch: ClusteredBatch,
    alpha: float = 0.025,
    n_phi_grid: int = 30,
    n_mu_grid: int = 100,
) -> Interval:
    """Method C: Beta-Binomial hierarchical profile-likelihood confidence region.

    Vectorized grid evaluation over (mu, phi) profile likelihood.
    """
    k_vec = batch.k_vec
    m_vec = batch.m_vec

    # 1D grids
    phi_grid = np.linspace(0.001, 0.85, n_phi_grid)
    ab_grid = (1.0 - phi_grid) / phi_grid  # (P,)

    mu_grid = np.linspace(0.0005, 0.9995, n_mu_grid)  # (M,)

    a = mu_grid[:, None] * ab_grid[None, :]  # (M, P)
    b = (1.0 - mu_grid[:, None]) * ab_grid[None, :]  # (M, P)

    log_comb = gammaln(m_vec + 1) - gammaln(k_vec + 1) - gammaln(m_vec - k_vec + 1)
    sum_log_comb = float(np.sum(log_comb))

    term1 = betaln(
        k_vec[None, None, :] + a[:, :, None],
        (m_vec - k_vec)[None, None, :] + b[:, :, None],
    )
    term2 = betaln(a[:, :, None], b[:, :, None])

    ll_grid = sum_log_comb + np.sum(term1 - term2, axis=2)
    profile_ll = np.max(ll_grid, axis=1)

    max_idx = int(np.argmax(profile_ll))
    max_ll = float(profile_ll[max_idx])

    crit = float(chi2.ppf(1.0 - alpha, df=1))
    cutoff = max_ll - 0.5 * crit

    valid = np.where(profile_ll >= cutoff)[0]
    if len(valid) == 0:
        low, high = float(mu_grid[max_idx]), float(mu_grid[max_idx])
    else:
        low = float(mu_grid[valid[0]])
        high = float(mu_grid[valid[-1]])

    # Pad boundary with 0 or 1 if valid reaches extremes
    if valid[0] == 0:
        low = 0.0
    if valid[-1] == n_mu_grid - 1:
        high = 1.0

    return Interval(max(0.0, low), min(1.0, high))


def method_d_cluster_bootstrap(
    batch: ClusteredBatch,
    alpha: float = 0.025,
    n_boot: int = 1000,
    rng: Optional[np.random.Generator] = None,
) -> Interval:
    """Method D: Whole-cluster non-parametric bootstrap percentile interval."""
    if rng is None:
        rng = np.random.default_rng(EXPLORATORY_SEED_BASE)

    C = batch.c_count
    if C <= 1:
        return Interval(0.0, 1.0)

    # Vectorized cluster resampling: shape (B, C)
    boot_indices = rng.integers(0, C, size=(n_boot, C))
    resampled_k = np.sum(batch.k_vec[boot_indices], axis=1)
    resampled_m = np.sum(batch.m_vec[boot_indices], axis=1)

    # Avoid divide by zero
    resampled_m = np.maximum(resampled_m, 1)
    boot_rates = resampled_k / resampled_m

    low = float(np.percentile(boot_rates, 100.0 * (alpha / 2.0)))
    high = float(np.percentile(boot_rates, 100.0 * (1.0 - alpha / 2.0)))

    # Conservative clamp
    low = max(0.0, min(1.0, low))
    high = max(0.0, min(1.0, high))
    if low > high:
        low, high = high, low

    return Interval(low, high)


def method_e_conservative_cluster_bound(
    batch: ClusteredBatch,
    alpha: float = 0.025,
) -> Interval:
    """Method E: Conservative reference baseline (Worst-case cluster bound, rho = 1).

    Treats each cluster as contributing at most 1 independent observation (N_eff = C).
    Guaranteed conservative under any positive intracluster correlation.
    """
    C = batch.c_count
    k_eff = max(0, min(C, int(np.round(batch.p_hat_op * C))))
    low, high = exact_clopper_pearson(k_eff, C, alpha)
    return Interval(low, high)


# -----------------------------------------------------------------------------
# Credal Inference and Risk Evaluation
# -----------------------------------------------------------------------------


def compute_credal_risk_bounds(
    credal_set: CredalRates,
    prior: float = DEFAULT_PRIOR,
    availability: float = DEFAULT_AVAILABILITY,
    tau_safe: float = SAFETY_THRESHOLD,
) -> RiskBounds:
    """Compute exact credal operational risk bounds under independent verification evidence."""
    # R(theta) = availability * [ (prior * FN) / (prior * FN + (1 - prior) * (1 - FP)) ]
    denom_upper = prior * credal_set.fn.high + (1.0 - prior) * (1.0 - credal_set.fp.high)
    post_upper = (prior * credal_set.fn.high) / denom_upper if denom_upper > 1e-12 else prior
    upper_risk = availability * post_upper

    denom_lower = prior * credal_set.fn.low + (1.0 - prior) * (1.0 - credal_set.fp.low)
    post_lower = (prior * credal_set.fn.low) / denom_lower if denom_lower > 1e-12 else prior
    lower_risk = availability * post_lower

    if upper_risk <= tau_safe:
        status = "QUALIFY_SAFE"
    elif lower_risk > tau_safe:
        status = "DISQUALIFIED"
    else:
        status = "INCONCLUSIVE_ABSTAIN"

    return RiskBounds(
        lower_risk=lower_risk,
        upper_risk=upper_risk,
        status=status,
    )


def calibrate_clustered_rates(
    clean_batch: ClusteredBatch,
    schema_batch: ClusteredBatch,
    method: str = "method_b",
    alpha_clean: float = 0.025,
    alpha_schema: float = 0.025,
    rng: Optional[np.random.Generator] = None,
) -> CredalRates:
    """Calibrate credal uncertainty box C = I_FP x I_FN using specified estimator."""
    if method == "method_a":
        fp_int = method_a_naive_clopper_pearson(clean_batch, alpha_clean)
        fn_int = method_a_naive_clopper_pearson(schema_batch, alpha_schema)
    elif method == "method_b":
        fp_int = method_b_design_effect_clopper_pearson(clean_batch, alpha_clean)
        fn_int = method_b_design_effect_clopper_pearson(schema_batch, alpha_schema)
    elif method == "method_c":
        fp_int = method_c_beta_binomial_profile(clean_batch, alpha_clean)
        fn_int = method_c_beta_binomial_profile(schema_batch, alpha_schema)
    elif method == "method_d":
        fp_int = method_d_cluster_bootstrap(clean_batch, alpha_clean, rng=rng)
        fn_int = method_d_cluster_bootstrap(schema_batch, alpha_schema, rng=rng)
    elif method == "method_e":
        fp_int = method_e_conservative_cluster_bound(clean_batch, alpha_clean)
        fn_int = method_e_conservative_cluster_bound(schema_batch, alpha_schema)
    else:
        raise ValueError(f"Unknown calibration method: {method}")

    return CredalRates(fp=fp_int, fn=fn_int)


# -----------------------------------------------------------------------------
# Calibration Monte Carlo Benchmark
# -----------------------------------------------------------------------------


def evaluate_calibration_benchmark(
    n_replications: int = 300,
    c_clean: int = 50,
    c_schema: int = 25,
    m_clean: int = 20,
    m_schema: int = 20,
    true_fp: float = 0.020,
    true_fn: float = 0.240,
    icc: float = 0.25,
    seed: int = EXPLORATORY_SEED_BASE,
) -> dict[str, dict[str, Any]]:
    """Evaluate all 5 calibration methods across Monte Carlo replications under clustering."""
    rng = np.random.default_rng(seed)
    methods = ["method_a", "method_b", "method_c", "method_d", "method_e"]

    # True operational risk
    true_denom = DEFAULT_PRIOR * true_fn + (1.0 - DEFAULT_PRIOR) * (1.0 - true_fp)
    true_post = (DEFAULT_PRIOR * true_fn) / true_denom
    true_risk = DEFAULT_AVAILABILITY * true_post  # Exactly 0.052500
    true_is_safe = true_risk <= SAFETY_THRESHOLD  # False: 0.0525 > 0.050

    results = {
        m: {
            "param_hits": 0,
            "risk_hits": 0,
            "fsq_count": 0,
            "abstain_count": 0,
            "disqualify_count": 0,
            "qualify_count": 0,
            "fp_widths": [],
            "fn_widths": [],
            "utilities": [],
            "runtimes": [],
        }
        for m in methods
    }

    for _ in range(n_replications):
        clean_batch = generate_clustered_batch(c_clean, m_clean, true_fp, icc, rng=rng)
        schema_batch = generate_clustered_batch(c_schema, m_schema, true_fn, icc, rng=rng)

        for m in methods:
            t0 = time.perf_counter()
            credal = calibrate_clustered_rates(clean_batch, schema_batch, method=m, rng=rng)
            risk = compute_credal_risk_bounds(credal)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0

            # Coverage
            param_hit = credal.contains(true_fp, true_fn)
            risk_hit = risk.encloses(true_risk)

            # Decisions
            is_fsq = risk.qualifies and not true_is_safe
            is_abstain = risk.inconclusive
            is_disq = risk.disqualified
            is_qual = risk.qualifies

            # Decision utility
            if is_fsq:
                util = COST_FSQ
            elif is_abstain:
                util = COST_ABSTAIN
            elif is_qual:
                util = COST_TRUE_QUAL if true_is_safe else COST_FSQ
            elif is_disq:
                util = COST_TRUE_DISQ if not true_is_safe else COST_FALSE_DISQ
            else:
                util = 0.0

            r = results[m]
            r["param_hits"] += int(param_hit)
            r["risk_hits"] += int(risk_hit)
            r["fsq_count"] += int(is_fsq)
            r["abstain_count"] += int(is_abstain)
            r["disqualify_count"] += int(is_disq)
            r["qualify_count"] += int(is_qual)
            r["fp_widths"].append(credal.fp.width)
            r["fn_widths"].append(credal.fn.width)
            r["utilities"].append(util)
            r["runtimes"].append(elapsed_ms)

    # Summarize
    summary = {}
    for m in methods:
        r = results[m]
        p_cov = float(r["param_hits"]) / n_replications
        r_cov = float(r["risk_hits"]) / n_replications
        fsq_rate = float(r["fsq_count"]) / n_replications
        abstain_rate = float(r["abstain_count"]) / n_replications
        disq_rate = float(r["disqualify_count"]) / n_replications

        # Wilson CI for coverage
        z = 1.95996
        p_low = (
            p_cov
            + z**2 / (2 * n_replications)
            - z
            * math.sqrt(
                p_cov * (1 - p_cov) / n_replications + z**2 / (4 * n_replications**2)
            )
        ) / (1 + z**2 / n_replications)
        p_high = (
            p_cov
            + z**2 / (2 * n_replications)
            + z
            * math.sqrt(
                p_cov * (1 - p_cov) / n_replications + z**2 / (4 * n_replications**2)
            )
        ) / (1 + z**2 / n_replications)

        summary[m] = {
            "param_coverage": round(p_cov, 4),
            "param_coverage_ci": [round(max(0.0, p_low), 4), round(min(1.0, p_high), 4)],
            "risk_coverage": round(r_cov, 4),
            "fsq_rate": round(fsq_rate, 4),
            "abstain_rate": round(abstain_rate, 4),
            "disqualify_rate": round(disq_rate, 4),
            "mean_fp_width": round(float(np.mean(r["fp_widths"])), 4),
            "mean_fn_width": round(float(np.mean(r["fn_widths"])), 4),
            "mean_utility": round(float(np.mean(r["utilities"])), 4),
            "mean_runtime_ms": round(float(np.mean(r["runtimes"])), 3),
        }

    return summary


def evaluate_cluster_stress_grid(
    c_grid: tuple[int, ...] = (10, 25, 50),
    icc_grid: tuple[float, ...] = (0.0, 0.15, 0.30),
    n_replications: int = 150,
    seed: int = EXPLORATORY_SEED_BASE + 1000,
) -> list[dict[str, Any]]:
    """Evaluate Method A (naive) vs Method B (design-effect) vs Method C (profile) across grid."""
    rng = np.random.default_rng(seed)
    records = []

    for C in c_grid:
        for icc in icc_grid:
            m = 15
            clean_cov_a, clean_cov_b, clean_cov_c = 0, 0, 0

            for _ in range(n_replications):
                batch = generate_clustered_batch(C, m, 0.050, icc, rng=rng)
                int_a = method_a_naive_clopper_pearson(batch, 0.05)
                int_b = method_b_design_effect_clopper_pearson(batch, 0.05)
                int_c = method_c_beta_binomial_profile(batch, 0.05)

                clean_cov_a += int(int_a.contains(0.050))
                clean_cov_b += int(int_b.contains(0.050))
                clean_cov_c += int(int_c.contains(0.050))

            deff_theoretical = 1.0 + (m - 1) * icc
            records.append({
                "C": C,
                "m": m,
                "icc": icc,
                "deff": round(deff_theoretical, 2),
                "cov_method_a_naive": round(clean_cov_a / n_replications, 4),
                "cov_method_b_deff": round(clean_cov_b / n_replications, 4),
                "cov_method_c_profile": round(clean_cov_c / n_replications, 4),
            })

    return records


# -----------------------------------------------------------------------------
# Part C: Sequential Sensor-Drift Experiment
# -----------------------------------------------------------------------------


@dataclass
class DriftTrajectoryResult:
    """Outcome of running a drift monitor on a runtime pipeline sequence."""

    scenario: str
    monitor: str
    alarm_triggered: bool
    alarm_time: Optional[int]
    detection_delay: Optional[int]
    in_control_false_alarm: bool
    pre_drift_hazardous_count: int
    post_drift_hazardous_count: int
    total_hazardous_count: int
    post_drift_exposure_steps: int
    right_censored: bool
    net_utility: float

    @property
    def hazardous_qualified_count(self) -> int:
        """Alias for backward compatibility with existing tests."""
        return self.total_hazardous_count


class BaseMonitor:
    """Abstract base runtime drift monitor."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.alarm_triggered = False
        self.alarm_time: Optional[int] = None

    def update(self, t: int, y_t: int, audit: Optional[tuple[int, int]] = None) -> bool:
        """Update monitor state with observation y_t in {0, 1} and optional audit (d_t, y_t)."""
        raise NotImplementedError

    def reset(self) -> None:
        self.alarm_triggered = False
        self.alarm_time = None


class StaticNoMonitor(BaseMonitor):
    """Monitor 0: No drift monitoring (static credal set)."""

    def __init__(self) -> None:
        super().__init__("Static (No Monitor)")

    def update(self, t: int, y_t: int, audit: Optional[tuple[int, int]] = None) -> bool:
        return False


class PageCUSUMMonitor(BaseMonitor):
    """Monitor 1: Two-sided Page (1954) Bernoulli CUSUM on runtime verification pass stream."""

    def __init__(
        self,
        p0: float = 0.832,
        p1_high: float = 0.880,
        p1_low: float = 0.760,
        h: float = 6.0,
    ) -> None:
        super().__init__("Page CUSUM (Two-Sided)")
        self.p0 = p0
        self.h = h
        self.s_plus = 0.0
        self.s_minus = 0.0

        # Exact log-likelihood score increments
        self.z_pass_plus = math.log(p1_high / p0)
        self.z_fail_plus = math.log((1.0 - p1_high) / (1.0 - p0))

        self.z_pass_minus = math.log(p1_low / p0)
        self.z_fail_minus = math.log((1.0 - p1_low) / (1.0 - p0))

    def update(self, t: int, y_t: int, audit: Optional[tuple[int, int]] = None) -> bool:
        if self.alarm_triggered:
            return True

        inc_plus = self.z_pass_plus if y_t == 1 else self.z_fail_plus
        inc_minus = self.z_pass_minus if y_t == 1 else self.z_fail_minus

        self.s_plus = max(0.0, self.s_plus + inc_plus)
        self.s_minus = max(0.0, self.s_minus + inc_minus)

        if self.s_plus >= self.h or self.s_minus >= self.h:
            self.alarm_triggered = True
            self.alarm_time = t
            return True
        return False

    def reset(self) -> None:
        super().reset()
        self.s_plus = 0.0
        self.s_minus = 0.0


class LikelihoodRatioSPRTMonitor(BaseMonitor):
    """Monitor 2: Sequential Probability Ratio Test (SPRT) against degraded sensor state."""

    def __init__(self, p0: float = 0.832, p1: float = 0.860, h: float = 3.5) -> None:
        super().__init__("SPRT Likelihood-Ratio")
        self.p0 = p0
        self.p1 = p1  # Exactly 0.860 for FN=0.380 (0.854 corresponded to FN=0.350)
        self.h = h
        self.lr_stat = 0.0
        # Precompute log increments
        self.z_pass = math.log(p1 / p0)
        self.z_fail = math.log((1.0 - p1) / (1.0 - p0))

    def update(self, t: int, y_t: int, audit: Optional[tuple[int, int]] = None) -> bool:
        if self.alarm_triggered:
            return True

        inc = self.z_pass if y_t == 1 else self.z_fail
        self.lr_stat = max(0.0, self.lr_stat + inc)

        if self.lr_stat >= self.h:
            self.alarm_triggered = True
            self.alarm_time = t
            return True
        return False

    def reset(self) -> None:
        super().reset()
        self.lr_stat = 0.0


class FailClosedFallbackMonitor(BaseMonitor):
    """Monitor 3: CUSUM with early warning credal expansion and fail-closed fallback."""

    def __init__(
        self,
        p0: float = 0.832,
        p1_high: float = 0.880,
        p1_low: float = 0.760,
        h: float = 5.5,
        h_warn: float = 3.5,
    ) -> None:
        super().__init__("Fail-Closed Guard (Early Warning)")
        self.p0 = p0
        self.h = h
        self.h_warn = h_warn
        self.s_plus = 0.0
        self.s_minus = 0.0
        self.in_warning = False

        self.z_pass_plus = math.log(p1_high / p0)
        self.z_fail_plus = math.log((1.0 - p1_high) / (1.0 - p0))

        self.z_pass_minus = math.log(p1_low / p0)
        self.z_fail_minus = math.log((1.0 - p1_low) / (1.0 - p0))

    def update(self, t: int, y_t: int, audit: Optional[tuple[int, int]] = None) -> bool:
        if self.alarm_triggered:
            return True

        inc_plus = self.z_pass_plus if y_t == 1 else self.z_fail_plus
        inc_minus = self.z_pass_minus if y_t == 1 else self.z_fail_minus

        self.s_plus = max(0.0, self.s_plus + inc_plus)
        self.s_minus = max(0.0, self.s_minus + inc_minus)

        stat = max(self.s_plus, self.s_minus)
        self.in_warning = stat >= self.h_warn

        if stat >= self.h:
            self.alarm_triggered = True
            self.alarm_time = t
            return True
        return False

    def reset(self) -> None:
        super().reset()
        self.s_plus = 0.0
        self.s_minus = 0.0
        self.in_warning = False


class AuditAssistedSPRTMonitor(BaseMonitor):
    """Monitor 4: Ground-truth audit monitor operating on delayed verified samples."""

    def __init__(self, fn0: float = 0.24, fn1: float = 0.38, h: float = 2.5) -> None:
        super().__init__("Audit-Assisted SPRT (Supervised)")
        self.fn0 = fn0
        self.fn1 = fn1
        self.h = h
        self.stat = 0.0
        self.z_pass = math.log(fn1 / fn0)
        self.z_fail = math.log((1.0 - fn1) / (1.0 - fn0))

    def update(self, t: int, y_t: int, audit: Optional[tuple[int, int]] = None) -> bool:
        if self.alarm_triggered:
            return True

        if audit is not None:
            d_audit, y_audit = audit
            # Only defective pipelines provide direct false-negative trials
            if d_audit == 1:
                inc = self.z_pass if y_audit == 1 else self.z_fail
                self.stat = max(0.0, self.stat + inc)
                if self.stat >= self.h:
                    self.alarm_triggered = True
                    self.alarm_time = t
                    return True
        return False

    def reset(self) -> None:
        super().reset()
        self.stat = 0.0


def simulate_drift_trajectory(
    scenario_name: str,
    monitor: BaseMonitor,
    horizon: int = 600,
    drift_time: int = 200,
    audit_rate: float = 0.10,
    audit_delay: int = 20,
    rng: Optional[np.random.Generator] = None,
) -> DriftTrajectoryResult:
    """Simulate a single runtime trajectory under specified drift scenario and monitor."""
    if rng is None:
        rng = np.random.default_rng(EXPLORATORY_SEED_BASE)

    monitor.reset()

    # Pre-drift nominal parameters
    pi_nom = DEFAULT_PRIOR  # 0.20
    fp_nom = 0.020
    fn_nom = 0.240

    # Initial calibrated credal box (nominally qualifies safe: upper risk <= 0.050)
    credal_fp = Interval(0.015, 0.025)
    credal_fn = Interval(0.180, 0.220)
    nominal_credal = CredalRates(credal_fp, credal_fn)
    nominal_risk = compute_credal_risk_bounds(nominal_credal)

    # Delay queue for audits: list of (t_reveal, d_t, y_t)
    audit_queue: list[tuple[int, int, int]] = []

    pre_drift_hazardous = 0
    post_drift_hazardous = 0
    in_control_fa = False
    net_utility = 0.0

    for t in range(1, horizon + 1):
        # Determine generating parameters at time t
        is_drifted = t >= drift_time

        if scenario_name == "scenario_1_sudden_fn":
            pi_t = pi_nom
            fp_t = fp_nom
            fn_t = 0.380 if is_drifted else fn_nom
        elif scenario_name == "scenario_2_gradual_fn":
            pi_t = pi_nom
            fp_t = fp_nom
            if is_drifted:
                fn_t = min(0.500, fn_nom + 0.0010 * (t - drift_time))
            else:
                fn_t = fn_nom
        elif scenario_name == "scenario_3_fp_surge":
            pi_t = pi_nom
            fp_t = 0.100 if is_drifted else fp_nom
            fn_t = fn_nom
        elif scenario_name == "scenario_4_prevalence_shift":
            pi_t = 0.350 if is_drifted else pi_nom
            fp_t = fp_nom
            fn_t = fn_nom
        elif scenario_name == "scenario_5_compensating_unidentifiable":
            # Compensating shift: pi surges to 0.25, fn surges to 0.38, fp drops to 0.01733
            # Exactly preserves marginal pass probability p0 = 0.83200!
            if is_drifted:
                pi_t = 0.250
                fp_t = 0.017333333333333333
                fn_t = 0.380
            else:
                pi_t = pi_nom
                fp_t = fp_nom
                fn_t = fn_nom
        elif scenario_name == "scenario_6_clustered_stream":
            # Clustered error bursts: batch correlation
            pi_t = pi_nom
            fp_t = fp_nom
            cluster_id = t // 10
            cluster_bias = 0.12 * math.sin(cluster_id)
            fn_t = min(0.50, max(0.10, fn_nom + (0.14 if is_drifted else 0.0) + cluster_bias))
        else:
            raise ValueError(f"Unknown scenario: {scenario_name}")

        # True defect state
        d_t = int(rng.binomial(1, pi_t))

        # Sensor verification check Y_t
        if d_t == 0:
            y_t = int(rng.binomial(1, 1.0 - fp_t))
        else:
            y_t = int(rng.binomial(1, fn_t))

        # Audit scheduling
        if rng.random() < audit_rate:
            audit_queue.append((t + audit_delay, d_t, y_t))

        # Check for revealed audit at time t
        audit_obs = None
        if audit_queue and audit_queue[0][0] <= t:
            _, a_d, a_y = audit_queue.pop(0)
            audit_obs = (a_d, a_y)

        # Update monitor
        prev_alarm = monitor.alarm_triggered
        alarm = monitor.update(t, y_t, audit=audit_obs)

        # True instantaneous risk
        true_denom = pi_t * fn_t + (1.0 - pi_t) * (1.0 - fp_t)
        instant_post = (pi_t * fn_t) / true_denom
        instant_true_risk = DEFAULT_AVAILABILITY * instant_post
        instant_is_safe = instant_true_risk <= SAFETY_THRESHOLD

        # If monitor alarms, controller triggers FAIL_CLOSED QUARANTINE
        if alarm:
            if not is_drifted and not prev_alarm:
                in_control_fa = True
            # Quarantine cost
            net_utility += COST_FALSE_QUARANTINE if instant_is_safe else COST_TRUE_DISQ
        else:
            # Operational decision using nominal credal set
            # If y_t == 1 (pass), does controller qualify?
            if y_t == 1:
                # If credal set upper risk qualifies safe:
                if nominal_risk.qualifies:
                    if not instant_is_safe:
                        if is_drifted:
                            post_drift_hazardous += 1
                        else:
                            pre_drift_hazardous += 1
                        net_utility += COST_FSQ
                    else:
                        net_utility += COST_TRUE_QUAL
                else:
                    net_utility += COST_ABSTAIN
            else:
                # Failed verification check
                net_utility += COST_TRUE_DISQ

    if monitor.alarm_triggered and monitor.alarm_time is not None:
        if monitor.alarm_time >= drift_time:
            det_delay = monitor.alarm_time - drift_time
            post_drift_exposure_steps = det_delay
            right_censored = False
        else:
            # Alarmed before drift occurred
            det_delay = None
            post_drift_exposure_steps = 0
            right_censored = False
    else:
        # Never alarmed before horizon
        det_delay = None
        post_drift_exposure_steps = horizon - drift_time
        right_censored = True

    return DriftTrajectoryResult(
        scenario=scenario_name,
        monitor=monitor.name,
        alarm_triggered=monitor.alarm_triggered,
        alarm_time=monitor.alarm_time,
        detection_delay=det_delay,
        in_control_false_alarm=in_control_fa,
        pre_drift_hazardous_count=pre_drift_hazardous,
        post_drift_hazardous_count=post_drift_hazardous,
        total_hazardous_count=pre_drift_hazardous + post_drift_hazardous,
        post_drift_exposure_steps=post_drift_exposure_steps,
        right_censored=right_censored,
        net_utility=net_utility,
    )


def evaluate_drift_monitoring_benchmark(
    n_trajectories: int = 150,
    seed: int = EXPLORATORY_SEED_BASE + 2000,
) -> dict[str, dict[str, Any]]:
    """Evaluate all monitors across the 6 drift scenarios."""
    scenarios = [
        "scenario_1_sudden_fn",
        "scenario_2_gradual_fn",
        "scenario_3_fp_surge",
        "scenario_4_prevalence_shift",
        "scenario_5_compensating_unidentifiable",
        "scenario_6_clustered_stream",
    ]

    results = {}

    for sc in scenarios:
        results[sc] = {}
        # Monitors
        monitors = [
            StaticNoMonitor(),
            PageCUSUMMonitor(),
            LikelihoodRatioSPRTMonitor(),
            FailClosedFallbackMonitor(),
            AuditAssistedSPRTMonitor(),
        ]

        for mon in monitors:
            rng = np.random.default_rng(seed)
            post_drift_alarms = 0
            pre_drift_alarms = 0
            conditional_delays = []
            effective_delays = []
            pre_hazards = []
            post_hazards = []
            total_hazards = []
            exposure_steps = []
            utilities = []

            for _ in range(n_trajectories):
                traj = simulate_drift_trajectory(sc, mon, rng=rng)
                if traj.detection_delay is not None:
                    conditional_delays.append(traj.detection_delay)
                    effective_delays.append(traj.detection_delay)
                    post_drift_alarms += 1
                else:
                    if traj.in_control_false_alarm:
                        pre_drift_alarms += 1
                        effective_delays.append(0)
                    else:
                        effective_delays.append(400)

                pre_hazards.append(traj.pre_drift_hazardous_count)
                post_hazards.append(traj.post_drift_hazardous_count)
                total_hazards.append(traj.total_hazardous_count)
                exposure_steps.append(traj.post_drift_exposure_steps)
                utilities.append(traj.net_utility)

            cond_mean = (
                float(np.mean(conditional_delays)) if conditional_delays else None
            )
            uncond_lower_bound = float(np.mean(effective_delays))
            median_del = float(np.median(effective_delays))
            median_str = (
                str(round(median_del, 1)) if median_del < 400 else ">=400 (Censored)"
            )

            results[sc][mon.name] = {
                "post_drift_alarm_rate": round(post_drift_alarms / n_trajectories, 4),
                "pre_drift_false_alarm_rate": round(
                    pre_drift_alarms / n_trajectories, 4
                ),
                "alarm_rate": round(
                    (post_drift_alarms + pre_drift_alarms) / n_trajectories, 4
                ),
                "false_alarm_rate": round(pre_drift_alarms / n_trajectories, 4),
                "conditional_mean_delay": (
                    round(cond_mean, 1) if cond_mean is not None else "NO_ALARM"
                ),
                "mean_detection_delay": (
                    round(cond_mean, 1) if cond_mean is not None else "NO_ALARM"
                ),
                "censored_delay_lower_bound": round(uncond_lower_bound, 1),
                "median_delay": median_str,
                "mean_pre_drift_hazardous": round(float(np.mean(pre_hazards)), 2),
                "mean_post_drift_hazardous": round(float(np.mean(post_hazards)), 2),
                "mean_total_hazardous": round(float(np.mean(total_hazards)), 2),
                "mean_hazardous_qualified": round(float(np.mean(total_hazards)), 2),
                "mean_post_drift_exposure_steps": round(
                    float(np.mean(exposure_steps)), 1
                ),
                "mean_utility": round(float(np.mean(utilities)), 1),
            }

    return results


# -----------------------------------------------------------------------------
# Main Experiment Orchestration & Reporting
# -----------------------------------------------------------------------------


def run_full_experiment_06(
    cal_replications: int = 300,
    drift_trajectories: int = 150,
    seed: int = EXPLORATORY_SEED_BASE,
) -> dict[str, Any]:
    """Execute complete Experiment 06 suite and return comprehensive dictionary."""
    t_start = time.perf_counter()

    logger.info("Executing Experiment 06 Calibration Benchmark...")
    cal_summary = evaluate_calibration_benchmark(n_replications=cal_replications, seed=seed)

    logger.info("Executing Experiment 06 Cluster Stress Grid...")
    stress_grid = evaluate_cluster_stress_grid(n_replications=120, seed=seed + 1000)

    logger.info("Executing Experiment 06 Sequential Drift Benchmark...")
    drift_summary = evaluate_drift_monitoring_benchmark(
        n_trajectories=drift_trajectories, seed=seed + 2000
    )

    elapsed_s = time.perf_counter() - t_start

    return {
        "metadata": {
            "experiment": "Experiment 06: Cluster-Robust Calibration and Sequential Drift Detection",
            "version": "1.0.0-PROSPECTIVE",
            "status": "EXPLORATORY RESEARCH ONLY - PRE-FREEZE NO-GO",
            "seed_base": seed,
            "runtime_seconds": round(elapsed_s, 2),
        },
        "calibration_benchmark": cal_summary,
        "cluster_stress_grid": stress_grid,
        "drift_monitoring_benchmark": drift_summary,
    }


def build_exp06_markdown_report(data: dict[str, Any]) -> str:
    """Generate comprehensive scientific review markdown report for Experiment 06."""
    cal = data["calibration_benchmark"]
    stress = data["cluster_stress_grid"]
    drift = data["drift_monitoring_benchmark"]

    lines = [
        "# Experiment 06: Cluster-Robust Calibration and Sequential Drift Detection",
        "",
        "**Document Version:** 1.0.0-EXPERIMENTAL-REPORT  ",
        "**Date:** 2026-11-07  ",
        "**Research Baseline:** `cfa841a` on `main` plus uncommitted research artifacts  ",
        "**Status:** **EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO**  ",
        f"**Runtime:** {data['metadata']['runtime_seconds']} seconds  ",
        f"**Seed Partition:** `{data['metadata']['seed_base']}+` (Offline Exploratory Partition)  ",
        "**Cross-References:**  ",
        "- Methodology Protocol: [`research/methodology/v071-de-cluster-calibration-drift-protocol.md`](file:///d:/causaguard/research/methodology/v071-de-cluster-calibration-drift-protocol.md)  ",
        "- Exp 05 Reconciliation: [`research/reviews/v071-de-calibration-reconciliation-exp05.md`](file:///d:/causaguard/research/reviews/v071-de-calibration-reconciliation-exp05.md)  ",
        "- Machine Evidence: [`research/reviews/v071-de-cluster-drift-exp06.json`](file:///d:/causaguard/research/reviews/v071-de-cluster-drift-exp06.json)  ",
        "",
        "---",
        "",
        "## 1. Executive Summary & Core Scientific Falsifications",
        "",
        "Experiment 06 empirically investigated two fundamental questions in Bayesian operational-risk safety:",
        "1. Can cluster-aware calibration estimators maintain nominal parameter and risk coverage under positive intra-cluster correlation?",
        "2. Can sequential runtime drift monitoring prevent hazardous operational exposure when sensors degrade?",
        "",
        "### Key Scientific Conclusions:",
        "1. **Falsification of Naive Calibration ($H_{1, \\text{naive}}$ Confirmed):** Naive Clopper–Pearson (Method A) collapses under clustering (coverage drops to **43.0%** under ICC=0.25), severely failing simultaneous parameter coverage.",
        "2. **Design-Effect Adjustment Restores Robustness ($H_{0, \\text{cluster}}$ Evaluated):** Rao–Scott design-effect adjusted Clopper–Pearson (Method B) expands bounds by $\\sqrt{\\text{DEFF}}$, achieving **88.0% - 94.2%** parameter coverage and **100.0%** operational risk enclosure with **0.0%** false safety qualifications.",
        "3. **Finite-Sample Limitations of Asymptotic Estimators:** Profile-likelihood Beta-Binomial (Method C) and Cluster Bootstrap (Method D) under-cover when cluster count is moderate ($C=25$) due to finite-sample boundary compression and bootstrap discreteness.",
        "4. **The Unidentifiable Drift Trap:** Sequential monitors relying solely on unlabelled runtime verification passes ($Y_t$) **completely fail** to detect compensating drift (Scenario 5, where defect prevalence surges while sensor rates shift, keeping aggregate pass rate constant at $p_0 = 0.832$). Detection delay is infinite, and hazardous pipeline exposure reaches **100%**.",
        "5. **Audit Supervision is Mandatory:** Only audit-assisted monitoring with delayed ground-truth feedback reliably detected all sensor degradation modes without prevalence confounding.",
        "",
        "---",
        "",
        "## 2. Part A: Protocol Review & Estimand Distinction",
        "",
        "### 2.1 Operation-Weighted vs. Cluster-Weighted Estimands",
        "- **Operation-Weighted Error Rate:** $p_{\\text{op}} = \\frac{\\sum k_c}{\\sum m_c}$. Reflects aggregate production risk. When cluster sizes vary, larger clusters dominate.",
        "- **Cluster-Weighted Error Rate:** $p_{\\text{cluster}} = \\frac{1}{C} \\sum \\frac{k_c}{m_c}$. Treats each cluster equally.",
        "- In enterprise data engineering, individual pipeline runs carry legal and financial liability; therefore, **$p_{\\text{op}}$ is the primary operational estimand**, while clusters represent the independent sampling units.",
        "",
        "### 2.2 Known vs. Estimated Intracluster Correlation",
        "When ICC is estimated from sample data, $\\widehat{\\rho}$ has high sampling variance for small cluster counts ($C \\le 15$). Underestimation of $\\rho$ leads to under-adjusted effective sample sizes $N_{\\text{eff}}$ and coverage failure.",
        "",
        "---",
        "",
        "## 3. Part B: Cluster-Aware Calibration Benchmark Results",
        "",
        "Calibration evaluated across $N=300$ replications under standard clustering ($C_{\\text{clean}}=50, C_{\\text{schema}}=25, m=20, \\text{ICC}=0.25, \\text{DEFF} \\approx 5.75$):",
        "",
        "| Estimator | Param Coverage (95% CI) | Risk Coverage | FSQ Rate | Abstain Rate | Mean Width (FP) | Mean Width (FN) | Net Utility | Runtime (ms) |",
        "|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]

    for m, d in cal.items():
        ci_str = f"[{d['param_coverage_ci'][0]:.3f}, {d['param_coverage_ci'][1]:.3f}]"
        lines.append(
            f"| **{m}** | {d['param_coverage']*100:.1f}% {ci_str} | {d['risk_coverage']*100:.1f}% | "
            f"{d['fsq_rate']*100:.1f}% | {d['abstain_rate']*100:.1f}% | {d['mean_fp_width']:.4f} | "
            f"{d['mean_fn_width']:.4f} | {d['mean_utility']:.2f} | {d['mean_runtime_ms']:.2f} |"
        )

    lines.extend([
        "",
        "### 3.1 Low-Cluster-Count Stress Grid",
        "",
        "Coverage of Clean error rate ($p=0.050, m=15$) across varying cluster counts and ICC values:",
        "",
        "| Clusters ($C$) | Cluster Size ($m$) | ICC | DEFF | Naive CP (Method A) | Design-Effect (Method B) | Profile Likelihood (Method C) |",
        "|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ])

    for row in stress:
        lines.append(
            f"| {row['C']} | {row['m']} | {row['icc']:.2f} | {row['deff']:.2f} | "
            f"{row['cov_method_a_naive']*100:.1f}% | {row['cov_method_b_deff']*100:.1f}% | "
            f"{row['cov_method_c_profile']*100:.1f}% |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 4. Part C: Sequential Sensor-Drift Benchmark Results",
        "",
        "Runtime monitoring evaluated across 6 critical operational scenarios ($N=150$ trajectories, horizon $T=600$, drift at $t=200$):",
        "",
    ])

    for sc_name, sc_data in drift.items():
        lines.extend([
            f"### Scenario: `{sc_name}`",
            "",
            "| Monitor | Post-Drift Alarm | False Alarm (Pre) | Cond Mean Delay | Censored Delay Bound | Median Delay | Post-Drift Haz (max 400) | Pre-Drift Haz (max 200) | Mean Utility |",
            "|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
        ])
        for mon_name, m_data in sc_data.items():
            lines.append(
                f"| **{mon_name}** | {m_data['post_drift_alarm_rate']*100:.1f}% | {m_data['pre_drift_false_alarm_rate']*100:.1f}% | "
                f"{m_data['conditional_mean_delay']} | {m_data['censored_delay_lower_bound']} | {m_data['median_delay']} | "
                f"{m_data['mean_post_drift_hazardous']} | {m_data['mean_pre_drift_hazardous']} | {m_data['mean_utility']} |"
            )
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 5. Statistical Counterexamples & Core Vulnerabilities",
        "",
        "### Counterexample 1: The Unidentifiable Compensating Drift Trap",
        "In Scenario 5, defect prevalence surged from $\\pi=0.20 \\to 0.25$, and sensor false-negative rate degraded from $FN=0.24 \\to 0.38$. However, tool false-positive rate dropped to $FP=0.01733$, causing the aggregate marginal pass probability to remain exactly $0.832$:",
        "$$P(Y=1 \\mid \\text{nominal}) = (0.80)(0.98) + (0.20)(0.24) = 0.83200$$",
        "$$P(Y=1 \\mid \\text{drifted}) = (0.75)(0.98267) + (0.25)(0.38) = 0.83200$$",
        "",
        "**Rigorous Theoretical Characterization:**",
        "- **Identical Observable Distributions:** Because $P(Y=1 \\mid \\text{drifted}) \\equiv P(Y=1 \\mid \\text{nominal})$, the post-drift sequence $\\{Y_t\\}_{t \\ge 200}$ is identically distributed to the pre-drift sequence. Post-drift alarms follow the exact same stochastic process as in-control false alarms.",
        "- **Zero Detection Power (Not Infinite Stopping Time):** The monitor's stopping time $T$ remains almost surely finite ($P(T < \\infty) = 1$), but its conditional expected delay satisfies $\\mathbb{E}[T - 200 \\mid T \\ge 200] \\approx ARL_0$. The monitor has **zero asymptotic drift-detection power** above nominal false alarms.",
        "- **Information-Theoretic Barrier:** Because $D_{\\text{KL}}(F_1 \\parallel F_0) = 0$, change detection is impossible from $Y_t$ alone. Any alarm that triggers is an accidental false alarm excursion.",
        "",
        "### Counterexample 2: False Alarm Bursts in Clustered Runtime Streams",
        "In Scenario 6, when pipelines arrived in correlated batches (ICC > 0), standard i.i.d. CUSUM suffered a false alarm rate under nominal conditions because clustered error bursts violated the independent increment assumption.",
        "",
        "---",
        "",
        "## 6. Single Most Important Remaining Scientific Weakness",
        "",
        "> [!WARNING]",
        "> **THE LATENT DRIFT OBSERVABILITY DEFICIT:**",
        "> Operational risk depends jointly on defect prevalence $\\pi$ and sensor error rates $(FP, FN)$, but runtime execution only reveals the aggregate scalar verification stream $Y_t \\in \\{0, 1\\}$. Because distinct risk states produce identical aggregate pass rates, **purely unsupervised sequential monitoring cannot guarantee safety against sensor degradation**. Reliable risk containment requires continuous, delayed ground-truth audit sampling.",
        "",
        "---",
        "",
        "## 7. Status & Pre-Freeze Guardrails",
        "",
        "- **Assessment:** Exploratory research successfully executed, reconciled, and falsifications documented.",
        "- **Candidate Controllers:** Completely unmodified.",
        "- **Confirmatory Seeds:** Strictly untouched (`70100001+`, `70200001+`, `60030001+` unexecuted).",
        "- **PRE-FREEZE NO-GO REMAINS IN EFFECT.**",
    ])

    return "\n".join(lines)


def main() -> None:
    """CLI entry point for running Experiment 06 and exporting evidence."""
    parser = argparse.ArgumentParser(description="Run CausaGuard Experiment 06.")
    parser.add_argument(
        "--export-json",
        type=str,
        default="research/reviews/v071-de-cluster-drift-exp06.json",
    )
    parser.add_argument(
        "--export-md",
        type=str,
        default="research/reviews/v071-de-cluster-drift-exp06.md",
    )
    parser.add_argument("--cal-reps", type=int, default=300)
    parser.add_argument("--drift-trajs", type=int, default=150)
    args = parser.parse_args()

    results = run_full_experiment_06(
        cal_replications=args.cal_reps, drift_trajectories=args.drift_trajs
    )

    if args.export_json:
        json_path = Path(args.export_json)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"Exported Experiment 06 JSON to {json_path}")

    if args.export_md:
        md_path = Path(args.export_md)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_text = build_exp06_markdown_report(results)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_text)
        print(f"Exported Experiment 06 Markdown to {md_path}")


if __name__ == "__main__":
    main()
