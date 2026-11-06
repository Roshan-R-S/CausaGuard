"""Tests for CausaGuard v0.6 Exploratory Variance Calibration & Power Audit."""

import pytest
import numpy as np

from experiments_v06.audit_power import (
    ALPHA_CONTRAST,
    DELTA_UTIL_MARGIN,
    EXPLORATORY_SEEDS,
    assert_safe_seeds,
    compute_mde,
    compute_power,
    compute_variance_ci,
    run_cluster,
)


def test_assert_safe_seeds_boundary_protection():
    """Verifies that seed boundary checks strictly reject reserved final seeds and unknown seeds."""
    # Authorized exploratory seeds pass
    assert_safe_seeds(EXPLORATORY_SEEDS)
    assert_safe_seeds([60001001, 60001005])

    # Reserved final seeds must raise ValueError
    with pytest.raises(ValueError, match="FATAL: Attempted to access reserved final evaluation seed"):
        assert_safe_seeds([60030001])

    with pytest.raises(ValueError, match="FATAL: Attempted to access reserved final evaluation seed"):
        assert_safe_seeds([60040010])

    # Out of range seeds must raise ValueError
    with pytest.raises(ValueError, match="not in authorized exploratory variance range"):
        assert_safe_seeds([12345])

    with pytest.raises(ValueError, match="not in authorized exploratory variance range"):
        assert_safe_seeds([60010001])  # Development evaluation seed not authorized for variance audit


def test_compute_power_analytical_properties():
    """Verifies theoretical properties of the small-sample non-central Student-t power model."""
    s_d = 0.018

    # 1. At null boundary delta == Delta_margin, power must equal alpha
    null_power = compute_power(s_d=s_d, k=10, delta=DELTA_UTIL_MARGIN)
    assert np.isclose(null_power, ALPHA_CONTRAST, atol=1e-5), f"Null power {null_power} != alpha {ALPHA_CONTRAST}"

    # 2. Monotonicity in effect size delta
    p_20 = compute_power(s_d=s_d, k=10, delta=0.020)
    p_30 = compute_power(s_d=s_d, k=10, delta=0.030)
    p_40 = compute_power(s_d=s_d, k=10, delta=0.040)
    assert null_power < p_20 < p_30 < p_40

    # 3. Monotonicity in cluster count K
    p_k10 = compute_power(s_d=s_d, k=10, delta=0.030)
    p_k24 = compute_power(s_d=s_d, k=24, delta=0.030)
    p_k32 = compute_power(s_d=s_d, k=32, delta=0.030)
    assert p_k10 < p_k24 < p_k32

    # 4. MDE decreases with K
    mde_10 = compute_mde(s_d=s_d, k=10, target_power=0.80)
    mde_24 = compute_mde(s_d=s_d, k=24, target_power=0.80)
    mde_32 = compute_mde(s_d=s_d, k=32, target_power=0.80)
    assert mde_10 > mde_24 > mde_32 > DELTA_UTIL_MARGIN


def test_compute_variance_ci():
    """Verifies Chi-squared confidence interval computation for sample standard deviation."""
    s_d = 0.015
    k = 10
    lower, upper = compute_variance_ci(s_d=s_d, k=k, confidence=0.95)
    assert 0.0 < lower < s_d < upper
    # For df=9, chi2_0.975 ~ 19.02, chi2_0.025 ~ 2.70
    # lower = sqrt(9 * 0.015^2 / 19.02) ~ 0.0103
    # upper = sqrt(9 * 0.015^2 / 2.70) ~ 0.0274
    assert 0.009 < lower < 0.012
    assert 0.024 < upper < 0.030


def test_run_cluster_structure_cs():
    """Verifies that run_cluster returns proper contrast structures and zero authorization violations on CS."""
    res = run_cluster(domain="cs", profile="iid", seed=60001001, n_cases=15)
    assert res["domain"] == "cs"
    assert res["profile"] == "iid"
    assert res["seed"] == 60001001
    assert res["n_cases"] == 15
    assert res["authorization_violations"] == 0

    assert "C1_macro" in res["paired_diffs"]
    assert "C2_repair" in res["paired_diffs"]
    assert "C3_verify_proceed" in res["paired_diffs"]

    for pol in ("cost_rule", "fixed_verify_repair_macro", "rules_repair", "always_verify_then_proceed"):
        assert pol in res["mean_utility"]
        assert pol in res["mean_risk"]
        assert 0.0 <= res["mean_risk"][pol] <= 1.0


def test_run_cluster_structure_de():
    """Verifies that run_cluster returns proper contrast structures and zero authorization violations on DE."""
    res = run_cluster(domain="de", profile="iid", seed=60001002, n_cases=15)
    assert res["domain"] == "de"
    assert res["profile"] == "iid"
    assert res["seed"] == 60001002
    assert res["n_cases"] == 15
    assert res["authorization_violations"] == 0

    assert "C1_macro" in res["paired_diffs"]
    assert "C2_repair" in res["paired_diffs"]
    assert "C3_verify_proceed" in res["paired_diffs"]

