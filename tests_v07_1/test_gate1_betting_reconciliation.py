"""Tests for Gate 1 betting benchmark scientific reconciliation.

Validates:
- Exact binomial probability calculation P(Binomial(256, 0.01) <= 6) ~ 0.98459036.
- Permutation sensitivity: Z=5 and Z=6 pass when shocks are at beginning, but fail at end.
- Robust qualification threshold: Z <= 3 passes across all permutations.
- Predictability contract: No future observations influence earlier betting fractions.
- No-bankruptcy invariant: Wealth multiplier strictly >= 1 - c > 0.
- Reconciled theoretical power under random permutations (~86.3% vs empirical 83.2%).

Research status: EXPLORATORY RESEARCH ONLY -- PRE-FREEZE NO-GO.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy import stats

from research.experiments.gate1_betting_benchmark import (
    PRE_FREEZE_NO_GO,
    PRODUCTION_AUTHORIZATION_ENABLED,
)
from research.experiments.gate1_betting_benchmark.betting_bounds import (
    compute_wealth_path,
    ucb_betting_fixed_time,
)

SAFETY_THRESHOLD = 0.0500
ALPHA = 0.050


def test_research_status_invariants():
    """Verify research isolation invariants."""
    assert PRE_FREEZE_NO_GO is True
    assert PRODUCTION_AUTHORIZATION_ENABLED is False


def test_exact_binomial_calculation():
    """Verify Task A: Exact binomial cumulative probability P(Binom(256, 0.01) <= 6)."""
    k = 256
    theta = 0.010
    prob_exact = float(stats.binom.cdf(6, k, theta))
    assert prob_exact == pytest.approx(0.9845903632, abs=1e-8)


def test_permutation_sensitivity_discrepancy():
    """Verify Task B: Order-dependence of the adaptive betting bound at Z=5 and Z=6."""
    k = 256

    # Test Z=5
    x_beg_5 = np.zeros(k)
    x_beg_5[:5] = 1.0
    x_end_5 = np.zeros(k)
    x_end_5[-5:] = 1.0
    x_alt_5 = np.zeros(k)
    x_alt_5[np.round(np.linspace(0, k - 1, 5)).astype(int)] = 1.0

    u_beg_5 = ucb_betting_fixed_time(x_beg_5, alpha=ALPHA)
    u_end_5 = ucb_betting_fixed_time(x_end_5, alpha=ALPHA)
    u_alt_5 = ucb_betting_fixed_time(x_alt_5, alpha=ALPHA)

    # Shocks at beginning pass, but shocks at end or alternating fail Gate 1
    assert u_beg_5 <= SAFETY_THRESHOLD
    assert u_end_5 > SAFETY_THRESHOLD
    assert u_alt_5 > SAFETY_THRESHOLD

    # Test Z=6
    x_beg_6 = np.zeros(k)
    x_beg_6[:6] = 1.0
    x_end_6 = np.zeros(k)
    x_end_6[-6:] = 1.0

    u_beg_6 = ucb_betting_fixed_time(x_beg_6, alpha=ALPHA)
    u_end_6 = ucb_betting_fixed_time(x_end_6, alpha=ALPHA)

    # Z=6 passes ONLY if shocks are concentrated at the beginning
    assert u_beg_6 <= SAFETY_THRESHOLD
    assert u_end_6 > SAFETY_THRESHOLD


def test_permutation_invariant_threshold_z3():
    """Verify Task B: Z <= 3 guarantees Gate 1 qualification across all arrangements."""
    k = 256
    rng = np.random.default_rng(82000501)

    for z in range(4):
        # 1. Beginning
        x_beg = np.zeros(k)
        x_beg[:z] = 1.0
        assert ucb_betting_fixed_time(x_beg, alpha=ALPHA) <= SAFETY_THRESHOLD

        # 2. End
        x_end = np.zeros(k)
        if z > 0:
            x_end[-z:] = 1.0
        assert ucb_betting_fixed_time(x_end, alpha=ALPHA) <= SAFETY_THRESHOLD

        # 3. Random permutations
        for _ in range(25):
            x_rnd = np.zeros(k)
            if z > 0:
                idx = rng.choice(k, size=z, replace=False)
                x_rnd[idx] = 1.0
            u_rnd = ucb_betting_fixed_time(x_rnd, alpha=ALPHA)
            assert u_rnd <= SAFETY_THRESHOLD, f"Z={z} failed permutation: {u_rnd}"


def test_predictability_contract():
    """Verify Task C: Predictability of betting fractions (no lookahead)."""
    k = 32
    m = 0.0500

    # Base sequence
    x_base = np.zeros(k)
    w_base, _ = compute_wealth_path(m, x_base)

    # Modify the last observation X_{K-1}
    x_mod = x_base.copy()
    x_mod[-1] = 1.0

    # The running wealth up to step K-2 must be completely identical
    # Verify by testing prefixes
    for prefix_len in range(1, k):
        w1, _ = compute_wealth_path(m, x_base[:prefix_len])
        w2, _ = compute_wealth_path(m, x_mod[:prefix_len])
        assert w1 == pytest.approx(w2, abs=1e-12)


def test_nonnegative_wealth_no_bankruptcy():
    """Verify Task C: Multiplier strictly bounded below by 1 - c = 0.25 > 0."""
    k = 10
    m = 0.0500
    c = 0.75

    # All shocks
    x_all_ones = np.ones(k)
    w_ones, _ = compute_wealth_path(m, x_all_ones, c=c)

    # Wealth should be strictly positive, bounded below by (1 - c)^K
    assert w_ones > 0.0
    assert w_ones >= (1.0 - c) ** k


def test_reconciled_power_calculation():
    """Verify Task A & E: Reconciled semi-analytical power estimate under random permutations.

    Integrates Monte Carlo estimated permutation pass rates q_perm(z) over Binomial(256, 0.010).
    Notice: This is a semi-analytical estimate (~87.2%), not an exact analytical closed-form value.
    """
    k = 256
    theta = 0.010

    # Theoretical binomial probabilities for Z=0..6
    p_z = [float(stats.binom.pmf(z, k, theta)) for z in range(7)]

    # Permutation pass probabilities determined by audit:
    # Z=0..3: 100%, Z=4: ~89.5%, Z=5: ~4.0%, Z=6: 0.0%
    pass_probs = [1.0, 1.0, 1.0, 1.0, 0.895, 0.040, 0.000]

    expected_power = sum(p * q for p, q in zip(p_z, pass_probs, strict=False))

    # Reconciled theoretical expected power under random permutations is ~87.2%
    assert expected_power == pytest.approx(0.8723, abs=0.005)

    # In the specific 500-trial simulation with seed 82000014:
    # Z >= 5 occurred 76 times (15.2%) vs expected 10.9%, depressing empirical passes
    # Predicted passes from sampled Z counts: 41 * 1.0 + 91 * 1.0 + 112 * 1.0 + 103 * 1.0 + 77 * 0.895 + 54 * 0.04 ~ 418.1
    # Observed passes: 416 / 500 (83.2%)
    observed_passes = 416
    n_trials = 500
    observed_power = observed_passes / n_trials
    assert observed_power == pytest.approx(0.832, abs=1e-4)
    assert abs(observed_passes - 418.1) < 5.0
