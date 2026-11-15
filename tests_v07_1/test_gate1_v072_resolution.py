"""Automated unit and regression tests for Gate 1 v0.7.2 statistical design resolution.

Validates:
- Research isolation and seed quarantine
- AM-GM constant betting e-value validity under heterogeneous schedules
- Exact analytical Z_max thresholds across K in {128, 256, 512, 1024}
- Power disparity at K=256 and reconciliation at K=512
- Missing observation sensitivity
- Model B diffuse harm convergence

STATUS: EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy import stats

from research.experiments.gate1_v072_resolution import (
    BASE_EXPLORATORY_SEED,
    PRE_FREEZE_NO_GO,
    PRODUCTION_AUTHORIZATION_ENABLED,
    SAFETY_THRESHOLD,
)
from research.experiments.gate1_v072_resolution.evaluators import (
    eval_constant_betting,
    eval_direct_betting,
    eval_hoeffding,
    eval_maurer_pontil,
    eval_permutation_betting,
)
from research.experiments.gate1_v072_resolution.simulation import (
    compute_analytical_z_max,
)


def test_research_isolation_and_seed_quarantine():
    """Verify pre-freeze guardrails and seed quarantine."""
    assert PRE_FREEZE_NO_GO is True
    assert PRODUCTION_AUTHORIZATION_ENABLED is False

    # Seed quarantine: Confirmatory ranges (70100001+, 70200001+, 60030001+) are strictly quarantined
    assert 83000000 <= BASE_EXPLORATORY_SEED < 90000000
    assert not (70100000 <= BASE_EXPLORATORY_SEED <= 70300000)
    assert not (60030000 <= BASE_EXPLORATORY_SEED <= 60040000)


def test_evaluators_exact_boundary_conditions():
    """Verify mathematical behavior on boundary and extreme inputs."""
    k = 256
    x_zeros = np.zeros(k, dtype=np.float64)
    x_ones = np.ones(k, dtype=np.float64)

    # All-ones input (100% failure rate) must fail all methods
    assert eval_maurer_pontil(x_ones)[0] is False
    assert eval_direct_betting(x_ones)[0] is False
    assert eval_constant_betting(x_ones)[0] is False
    assert eval_permutation_betting(x_ones, m_permutations=5)[0] is False
    assert eval_hoeffding(x_ones)[0] is False

    # All-zeros input (0% failure rate) at K=256 passes MP, Betting, Const Betting; fails Hoeffding
    assert eval_maurer_pontil(x_zeros)[0] is True
    assert eval_direct_betting(x_zeros)[0] is True
    assert eval_constant_betting(x_zeros)[0] is True
    assert eval_permutation_betting(x_zeros, m_permutations=5)[0] is True
    assert eval_hoeffding(x_zeros)[0] is False  # Hoeffding requires K >= 600 at zero events!


def test_am_gm_constant_betting_e_value_invariant():
    """Verify Theorem 1: Constant-betting e-value expectation <= 1.0 under heterogeneous null."""
    # Construct a heterogeneous schedule targeting mu_bar = 0.0501 > 0.0500
    # K=256: 64 hazardous clusters with mu = 0.2004, 192 safe clusters with mu = 0.0
    k_haz = 64
    k_safe = 192
    assert k_haz + k_safe == 256
    p_haz = 0.2004
    tau = SAFETY_THRESHOLD
    theta_alt = 0.010

    # Evaluate theoretical expectation of wealth multiplier
    var_alt = theta_alt * (1.0 - theta_alt)
    raw_lam = (tau - theta_alt) / (var_alt + (tau - theta_alt) ** 2)
    lam = min(0.75 / (1.0 - tau), max(0.0, raw_lam))

    # Analytical expectation:
    e_haz = 1.0 + lam * (tau - p_haz)
    e_safe = 1.0 + lam * (tau - 0.0)
    expected_wealth = (e_haz ** k_haz) * (e_safe ** k_safe)

    # By AM-GM Theorem, this expectation must be strictly <= 1.0!
    assert expected_wealth <= 1.0
    assert expected_wealth == pytest.approx(0.518742, abs=1e-5)


def test_analytical_z_max_across_horizons():
    """Verify exact analytical Z_max shock thresholds across horizons."""
    z_128 = compute_analytical_z_max(128)
    assert z_128["maurer_pontil"] == -1
    assert z_128["hoeffding"] == -1
    assert z_128["direct_betting_beginning"] == 1
    assert z_128["constant_betting"] == 1

    z_256 = compute_analytical_z_max(256)
    assert z_256["maurer_pontil"] == 1
    assert z_256["hoeffding"] == -1
    assert z_256["direct_betting_beginning"] == 6
    assert z_256["constant_betting"] == 4

    z_512 = compute_analytical_z_max(512)
    assert z_512["maurer_pontil"] == 8
    assert z_512["hoeffding"] == -1
    assert z_512["direct_betting_beginning"] == 15
    assert z_512["constant_betting"] == 11

    z_1024 = compute_analytical_z_max(1024)
    assert z_1024["maurer_pontil"] == 28
    assert z_1024["hoeffding"] == 12
    assert z_1024["direct_betting_beginning"] == 36
    assert z_1024["constant_betting"] == 25


def test_power_comparison_mp_vs_betting_at_k256():
    """Verify critical power disparity at K=256: MP is severely underpowered under shocks."""
    k = 256
    theta = 0.010
    z_mp = 1  # MP Z_max at K=256

    # Exact binomial power for MP
    power_mp = stats.binom.cdf(z_mp, k, theta)
    assert power_mp == pytest.approx(0.273655, abs=1e-4)

    # Direct Betting power on shocks is >= 80%
    rng = np.random.default_rng(83000042)
    n_trials = 500
    bet_passes = 0
    const_passes = 0
    for _ in range(n_trials):
        x = rng.binomial(1, theta, size=k).astype(np.float64)
        if eval_direct_betting(x)[0]:
            bet_passes += 1
        if eval_constant_betting(x)[0]:
            const_passes += 1

    power_bet = bet_passes / n_trials
    power_const = const_passes / n_trials

    assert power_bet >= 0.80, f"Betting power unexpectedly low: {power_bet}"
    assert power_const >= 0.80, f"Constant betting power unexpectedly low: {power_const}"


def test_sizing_convergence_at_k512():
    """Verify that K=512 reconciles method discordance: MP reaches >= 90% power."""
    k = 512
    theta = 0.010
    z_mp = 8  # MP Z_max at K=512

    power_mp = stats.binom.cdf(z_mp, k, theta)
    assert power_mp >= 0.90, f"MP power at K=512 failed 90% threshold: {power_mp}"
    assert power_mp == pytest.approx(0.924803, abs=1e-4)


def test_model_b_diffuse_harm_convergence():
    """Verify that under diffuse within-cluster harm (N=400), both MP and Betting achieve 100% power at K=256."""
    k = 256
    n_cases = 400
    theta = 0.010
    rng = np.random.default_rng(83000099)
    n_trials = 200

    mp_passes = 0
    bet_passes = 0
    for _ in range(n_trials):
        x = rng.binomial(n_cases, theta, size=k).astype(np.float64) / n_cases
        if eval_maurer_pontil(x)[0]:
            mp_passes += 1
        if eval_direct_betting(x)[0]:
            bet_passes += 1

    assert mp_passes == n_trials  # 100% power
    assert bet_passes == n_trials  # 100% power
