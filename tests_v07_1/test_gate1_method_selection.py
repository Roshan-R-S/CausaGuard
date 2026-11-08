"""Tests for Gate 1 replacement method selection review.

Validates:
- Exact derivations of Model A (Cluster Shock) vs Model B (Independent Diffuse Harm).
- Power collapse of Cluster Clopper-Pearson under Model B (pass prob < 1e-200).
- Student-t validity under Model B vs failure under Model A.
- Poisson-binomial tail dominance and coverage conservatism under heterogeneous clusters.
- Sample size thresholds: K=128 infeasibility vs K=256 feasibility for Empirical Bernstein.

Research status: EXPLORATORY RESEARCH ONLY -- PRE-FREEZE NO-GO.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from scipy import stats

from research.experiments.gate1_coverage_audit import (
    PRE_FREEZE_NO_GO,
    PRODUCTION_AUTHORIZATION_ENABLED,
)


def test_research_status_and_flag_isolation():
    """Verify research isolation invariants."""
    assert PRE_FREEZE_NO_GO is True
    assert PRODUCTION_AUTHORIZATION_ENABLED is False


def test_task1_model_a_vs_model_b_derivations():
    """Verify exact derivations for Model A (Cluster Shock) vs Model B (Independent Harm).

    Parameters: K = 128 clusters, N = 400 cases/cluster, theta = 0.010.
    """
    k = 128
    n = 400
    theta = 0.010
    alpha = 0.050

    # Model A: Cluster shock
    # E[R_k] = theta = 0.010
    # P(R_k > 0) = theta = 0.010
    q_a = theta
    e_z_a = k * q_a
    pass_prob_a = float(stats.binom.cdf(2, k, q_a))

    assert q_a == pytest.approx(0.010, abs=1e-6)
    assert e_z_a == pytest.approx(1.28, abs=1e-6)
    assert pass_prob_a == pytest.approx(0.862522, abs=1e-4)

    # Model B: Independent per-case harm
    # E[R_k] = theta = 0.010
    # P(R_k > 0) = 1 - (1 - theta)^N = 1 - 0.99^400
    q_b = float(1.0 - (1.0 - theta) ** n)
    e_z_b = k * q_b
    pass_prob_b = float(stats.binom.cdf(2, k, q_b))

    assert q_b == pytest.approx(0.982046, abs=1e-4)
    assert e_z_b == pytest.approx(125.70, abs=0.1)
    # Clopper-Pearson pass probability is completely annihilated under Model B
    assert pass_prob_b < 1e-200
    assert pass_prob_b == pytest.approx(0.0, abs=1e-10)

    # Student-t behavior under Model B
    # Variance of R_k under Model B is theta * (1 - theta) / N
    var_rk = theta * (1.0 - theta) / n
    se_mean = math.sqrt(var_rk / k)
    t_crit = float(stats.t.ppf(1.0 - alpha, k - 1))
    expected_t_ucb = theta + t_crit * se_mean

    assert expected_t_ucb < 0.050
    assert expected_t_ucb == pytest.approx(0.01073, abs=1e-4)


def test_task1_power_collapse_across_thetas():
    """Verify that Cluster Clopper-Pearson suffers 100% false rejection under Model B across all safe thetas."""
    k = 128
    n = 400

    for theta in [0.005, 0.010, 0.020]:
        q_b = 1.0 - (1.0 - theta) ** n
        pass_prob_b = stats.binom.cdf(2, k, q_b)
        assert pass_prob_b < 1e-100, f"Pass prob unexpectedly high for theta={theta}: {pass_prob_b}"


def test_task3_poisson_binomial_tail_dominance():
    """Verify Hoeffding (1956) theorem: ordinary binomial has heavier tails than Poisson binomial.

    This ensures Clopper-Pearson coverage remains conservative under heterogeneous clusters.
    """
    k = 128
    q_bar = 0.0501
    # Heterogeneous q_k: half at 0.010, half at 0.0902
    q_k = np.array([0.010] * 64 + [0.0902] * 64, dtype=np.float64)
    assert np.isclose(np.mean(q_k), q_bar)

    # Compute exact PMF via DFT of characteristic function
    omega = 2 * np.pi * np.arange(k + 1) / (k + 1)
    exp_i_omega = np.exp(1j * omega)
    factors = (1.0 - q_k[:, None]) + q_k[:, None] * exp_i_omega[None, :]
    prod = np.prod(factors, axis=0)
    pb_pmf = np.maximum(0.0, np.fft.ifft(prod).real)

    # Ordinary binomial PMF
    bin_pmf = np.array([stats.binom.pmf(z, k, q_bar) for z in range(k + 1)])

    # Clopper-Pearson UCB
    alpha = 0.050
    ucbs = [1.0 - (alpha ** (1.0 / k)) if z == 0 else (1.0 if z == k else float(stats.beta.ppf(1.0 - alpha, z + 1, k - z))) for z in range(k + 1)]

    cov_pb = float(sum(p for p, u in zip(pb_pmf, ucbs) if u >= q_bar))
    cov_bin = float(sum(p for p, u in zip(bin_pmf, ucbs) if u >= q_bar))

    # Coverage is strictly >= 95% in both
    assert cov_pb >= 0.950
    assert cov_bin >= 0.950
    # PB is strictly more concentrated, yielding higher coverage (lower undercoverage risk)
    assert cov_pb > cov_bin
    assert cov_pb == pytest.approx(0.998761, abs=1e-4)


def test_task4_empirical_bernstein_sample_size_thresholds():
    """Verify Maurer & Pontil (2009) Theorem 4 corrected sample size thresholds.

    Theorem 4 published formula uses ln(2/delta), yielding ln(40) = 3.688879.
    """
    alpha = 0.050
    tau_safe = 0.050
    log_term = math.log(2.0 / alpha)

    # At K = 128:
    bound_128 = (7.0 * log_term) / (3.0 * (128 - 1))
    assert bound_128 > tau_safe
    assert bound_128 == pytest.approx(0.06777, abs=1e-4)

    # At K = 256:
    bound_256 = (7.0 * log_term) / (3.0 * (256 - 1))
    assert bound_256 < tau_safe
    assert bound_256 == pytest.approx(0.03375445, abs=1e-6)

    # At K = 256 under Model B (theta = 0.010, N = 400):
    var_rk = 0.010 * 0.990 / 400
    expected_eb_ucb_256 = 0.010 + math.sqrt(2.0 * var_rk * log_term / 256) + bound_256
    assert expected_eb_ucb_256 < tau_safe
    assert expected_eb_ucb_256 == pytest.approx(0.04460, abs=1e-4)


def test_task2_corrected_empirical_bernstein_calculations():
    """Verify Task 2 exact calculations under corrected Maurer & Pontil Theorem 4.

    For delta=0.05, tau_safe=0.050:
    - Zero-event bound at K=256: ~0.03375445.
    - Minimum K for zero-event qualification: 174.
    - Z=1 failure at K=256: UCB ~ 0.04827.
    - Z=2 failures at K=256: UCB ~ 0.05654.
    - Qualification requires Z <= 1.
    - Qualification probability at theta=0.010 is ~27.37% (not 52.78%).
    """
    k = 256
    alpha = 0.050
    tau_safe = 0.050
    log_term = math.log(2.0 / alpha)
    bound_term = (7.0 * log_term) / (3.0 * (k - 1))

    # Zero-event UCB
    assert bound_term == pytest.approx(0.03375445, abs=1e-6)

    # Z = 1 failure
    x1 = np.zeros(k)
    x1[0] = 1.0
    m1 = float(np.mean(x1))
    s1_sq = float(np.var(x1, ddof=1))
    ucb_z1 = m1 + math.sqrt(2.0 * s1_sq * log_term / k) + bound_term
    assert ucb_z1 <= tau_safe
    assert ucb_z1 == pytest.approx(0.048271, abs=1e-5)

    # Z = 2 failures
    x2 = np.zeros(k)
    x2[0] = 1.0
    x2[1] = 1.0
    m2 = float(np.mean(x2))
    s2_sq = float(np.var(x2, ddof=1))
    ucb_z2 = m2 + math.sqrt(2.0 * s2_sq * log_term / k) + bound_term
    assert ucb_z2 > tau_safe
    assert ucb_z2 == pytest.approx(0.056543, abs=1e-5)

    # Power for Bernoulli shock with theta = 0.010 requires Z <= 1
    pass_prob = float(stats.binom.cdf(1, k, 0.010))
    assert pass_prob == pytest.approx(0.273655, abs=1e-4)


def test_distinction_between_concentration_bounds_and_theoretical_lower_bound():
    """Verify that theoretical zero-event distribution-free lower bound is 1 - delta^(1/K).

    Hoeffding and Empirical Bernstein fail at K=128 due to inequality slack,
    not because a distribution-free bound is information-theoretically impossible.
    """
    k = 128
    alpha = 0.050
    tau_safe = 0.050

    # Theoretical lower bound on zero-event UCB for any valid distribution-free method
    # is the Bernoulli worst-case: 1 - delta^(1/K)
    theoretical_zero_bound = 1.0 - (alpha ** (1.0 / k))
    assert theoretical_zero_bound <= tau_safe
    assert theoretical_zero_bound == pytest.approx(0.023132, abs=1e-5)

    # Hoeffding and Empirical Bernstein exceed tau_safe due to concentration slack:
    hoeffding_128 = math.sqrt(math.log(1.0 / alpha) / (2.0 * k))
    assert hoeffding_128 > tau_safe
    assert hoeffding_128 == pytest.approx(0.10818, abs=1e-4)

    eb_128 = (7.0 * math.log(2.0 / alpha)) / (3.0 * (k - 1))
    assert eb_128 > tau_safe
    assert eb_128 == pytest.approx(0.06777, abs=1e-4)
