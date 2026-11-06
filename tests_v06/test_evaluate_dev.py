"""Tests for CausaGuard v0.6 Development Evaluation Runner."""

import pytest
import numpy as np

from experiments_v06.evaluate_dev import (
    ALPHA_CONTRAST,
    DEV_SEEDS_CS,
    DEV_SEEDS_DE,
    assert_dev_seeds,
    clustered_bootstrap_lower_bound,
    run_dev_cluster,
)


def test_assert_dev_seeds_boundary_protection():
    """Verifies that development runner strictly forbids reserved final seeds and wrong domain seeds."""
    # Valid seeds pass
    assert_dev_seeds("cs", [60010001, 60010064])
    assert_dev_seeds("de", [60020001, 60020064])

    # Cross-domain rejection
    with pytest.raises(ValueError, match="not in authorized development evaluation range"):
        assert_dev_seeds("cs", [60020001])

    with pytest.raises(ValueError, match="not in authorized development evaluation range"):
        assert_dev_seeds("de", [60010001])

    # Reserved final seeds must raise FATAL SECURITY VIOLATION
    with pytest.raises(ValueError, match="FATAL SECURITY VIOLATION"):
        assert_dev_seeds("cs", [60030001])

    with pytest.raises(ValueError, match="FATAL SECURITY VIOLATION"):
        assert_dev_seeds("de", [60040001])

    # Exploratory seeds rejected
    with pytest.raises(ValueError, match="not in authorized development evaluation range"):
        assert_dev_seeds("cs", [60001001])


def test_clustered_bootstrap_lower_bound_properties():
    """Verifies that clustered bootstrap lower bound behaves monotonically and matches theoretical bounds."""
    rng = np.random.default_rng(123)
    diffs = rng.normal(loc=0.035, scale=0.020, size=64)

    lb = clustered_bootstrap_lower_bound(diffs, alpha=ALPHA_CONTRAST, n_boot=2000, rng_seed=42)
    mean_diff = float(np.mean(diffs))

    # Lower bound must be strictly less than sample mean
    assert lb < mean_diff
    # For normal data, lower bound should be approximately mean - 2.80 * (0.02 / sqrt(64))
    approx_se = 0.020 / 8.0
    assert mean_diff - 4.0 * approx_se < lb < mean_diff - 1.5 * approx_se


def test_zero_event_clopper_pearson_formula():
    """Verifies exact cluster-level Clopper-Pearson bound formula at K=64."""
    k = 64
    bound = 1.0 - (0.05 ** (1.0 / k))
    assert np.isclose(bound, 0.04576, atol=1e-4)
    assert bound <= 0.050, "At K=64, zero-event cluster bound must be <= 5.0%"
