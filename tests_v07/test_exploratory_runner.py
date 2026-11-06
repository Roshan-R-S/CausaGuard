"""Unit and invariant tests for CausaGuard v0.7 Exploratory Calibration Runner."""

from __future__ import annotations

import numpy as np
import pytest

from experiments_v07.audit_exploratory import (
    DELTA_HURDLE,
    EXPLORATORY_SEEDS,
    PER_CONTRAST_ALPHA,
    assert_exploratory_seeds,
    calculate_power_nct,
    compute_chi2_ci_sd,
    find_mde_nct,
    run_single_cluster,
)


def test_exploratory_seed_boundary_protection():
    """Verifies that the exploratory runner strictly rejects non-exploratory and reserved final seeds."""
    # Valid seeds pass
    assert_exploratory_seeds([70001001, 70001016])
    assert_exploratory_seeds(EXPLORATORY_SEEDS)

    # Out of exploratory range
    with pytest.raises(ValueError, match="not in authorized exploratory calibration range"):
        assert_exploratory_seeds([70001017])

    with pytest.raises(ValueError, match="not in authorized exploratory calibration range"):
        assert_exploratory_seeds([70001000])

    # Unsealed development confirmatory seeds must raise FATAL SECURITY VIOLATION
    with pytest.raises(ValueError, match="FATAL SECURITY VIOLATION"):
        assert_exploratory_seeds([70010001])

    with pytest.raises(ValueError, match="FATAL SECURITY VIOLATION"):
        assert_exploratory_seeds([70020001])

    # Reserved confirmatory final seeds must raise FATAL SECURITY VIOLATION
    with pytest.raises(ValueError, match="FATAL SECURITY VIOLATION"):
        assert_exploratory_seeds([70030001])

    with pytest.raises(ValueError, match="FATAL SECURITY VIOLATION"):
        assert_exploratory_seeds([70040001])

    with pytest.raises(ValueError, match="FATAL SECURITY VIOLATION"):
        assert_exploratory_seeds([60030001])


def test_chi2_confidence_interval_sd():
    """Asserts mathematical properties of Chi-squared confidence interval for SD."""
    sd = 0.045
    df = 15  # K=16
    ci_lower, ci_upper = compute_chi2_ci_sd(sd=sd, df=df, conf_level=0.95)

    assert ci_lower < sd < ci_upper
    # At df=15, 95% CI is approximately [0.739 * SD, 1.549 * SD]
    assert np.isclose(ci_lower, sd * np.sqrt(15.0 / 27.48839), atol=1e-5)
    assert np.isclose(ci_upper, sd * np.sqrt(15.0 / 6.26214), atol=1e-4)


def test_calculate_power_nct_exact_erratum_match():
    """Verifies exact noncentral-t power calculation against verified prospective erratum."""
    # Theoretical benchmark from erratum:
    # K=64, df=63, alpha=0.01/6, Delta=+0.015, delta=+0.030, SD=0.045 => 35.9697%
    power_erratum = calculate_power_nct(
        k=64,
        delta=0.030,
        delta_hurdle=DELTA_HURDLE,
        sd=0.045,
        alpha=PER_CONTRAST_ALPHA,
    )
    assert np.isclose(power_erratum, 0.359697, atol=1e-5)

    # Monotonicity in K: power increases with sample size
    power_k32 = calculate_power_nct(k=32, delta=0.030, sd=0.045)
    power_k128 = calculate_power_nct(k=128, delta=0.030, sd=0.045)
    assert power_k32 < power_erratum < power_k128

    # Monotonicity in effect size delta: larger effect gives higher power
    power_delta_035 = calculate_power_nct(k=64, delta=0.035, sd=0.045)
    assert power_delta_035 > power_erratum

    # Monotonicity in SD: smaller SD gives higher power
    power_sd_035 = calculate_power_nct(k=64, delta=0.030, sd=0.035)
    assert power_sd_035 > power_erratum


def test_find_mde_nct():
    """Verifies that MDE solver produces an effect size that yields exactly the target power."""
    mde = find_mde_nct(k=64, target_power=0.80, sd=0.045)
    # Check that evaluating power at the computed MDE returns 80.0%
    actual_power = calculate_power_nct(k=64, delta=mde, sd=0.045)
    assert np.isclose(actual_power, 0.80, atol=1e-4)


def test_run_single_cluster_reproducibility():
    """Verifies deterministic cluster execution on exploratory seeds."""
    res1 = run_single_cluster(domain="cs", seed=70001001, profile="iid", n_cases=20)
    res2 = run_single_cluster(domain="cs", seed=70001001, profile="iid", n_cases=20)

    for p in res1["policies"]:
        assert np.isclose(
            res1["policies"][p]["mean_utility"],
            res2["policies"][p]["mean_utility"],
            atol=1e-8,
        )
        assert res1["policies"][p]["auth_violations"] == 0
        assert res2["policies"][p]["auth_violations"] == 0

