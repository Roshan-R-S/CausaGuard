"""Acceptance and statistical falsification tests for Experiment 05.

Verifies Clopper-Pearson calibration, simultaneous coverage, sample-size sensitivity,
five-arm benchmarks, clustered sampling degradation, and AST boundary isolation.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from research.experiments.de_calibration_exp05 import experiment
from research.experiments.de_calibration_exp05.experiment import (
    DEFAULT_AVAILABILITY,
    EXPLORATORY_SEED_BASE,
    CredalRates,
    Interval,
    calibrate_credal_set,
    clopper_pearson,
    compute_credal_risk_bounds,
    evaluate_sample_size_sensitivity,
    rate_confidence_interval,
    run_assumption_violation_scenarios,
    run_five_arm_benchmark,
)


def test_interval_properties_and_validation():
    iv = Interval(0.01, 0.05)
    assert iv.low == 0.01
    assert iv.high == 0.05
    assert round(iv.width, 2) == 0.04
    assert iv.contains(0.03)
    assert not iv.contains(0.08)

    with pytest.raises(ValueError, match="exceeds upper bound"):
        Interval(0.10, 0.05)

    with pytest.raises(ValueError, match="must be in"):
        Interval(-0.01, 0.50)


def test_clopper_pearson_exact_calculation():
    # Boundary: k=0, n=100, alpha=0.05 -> lower=0, upper=1 - (alpha/2)^(1/n) = 1 - 0.025^(0.01) ~= 0.03622
    low_0, high_0 = clopper_pearson(0, 100, 0.05)
    assert low_0 == 0.0
    assert 0.0360 <= high_0 <= 0.0365

    # Boundary: k=n, n=100, alpha=0.05 -> lower=(alpha/2)^(1/n) ~= 0.96378, upper=1.0
    low_n, high_n = clopper_pearson(100, 100, 0.05)
    assert high_n == 1.0
    assert 0.9635 <= low_n <= 0.9640

    # Normal case: k=20, n=1000, alpha=0.025
    low_mid, high_mid = clopper_pearson(20, 1000, 0.025)
    assert 0.0110 <= low_mid <= 0.0120
    assert 0.0320 <= high_mid <= 0.0330

    # Invalid arguments
    with pytest.raises(ValueError, match="must be positive"):
        clopper_pearson(0, 0, 0.05)
    with pytest.raises(ValueError, match="satisfy 0 <= k <= n"):
        clopper_pearson(10, 5, 0.05)
    with pytest.raises(ValueError, match="must be in"):
        clopper_pearson(5, 10, 1.5)


def test_calibrate_credal_set_multiplicity():
    # Simultaneous alpha = 0.05 -> alpha_dim = 0.025 per dimension
    credal = calibrate_credal_set(k_fp=20, n_clean=1000, k_fn=100, n_schema=500, alpha_cal=0.05)
    assert isinstance(credal, CredalRates)
    assert 0.0110 <= credal.fp.low <= 0.0120
    assert 0.0320 <= credal.fp.high <= 0.0330
    assert 0.1600 <= credal.fn.low <= 0.1630
    assert 0.2400 <= credal.fn.high <= 0.2450


def test_insufficient_calibration_data_fallback():
    # If sample size is 0, falls back to vacuous [0, 1] x [0, 1]
    credal = calibrate_credal_set(0, 0, 0, 0)
    assert credal.fp.low == 0.0 and credal.fp.high == 1.0
    assert credal.fn.low == 0.0 and credal.fn.high == 1.0

    # Vacuous bounds produce upper risk = A = 0.9100 > 0.050 (mandatory failure)
    bounds = compute_credal_risk_bounds(credal, passed=True)
    assert bounds.upper_risk == DEFAULT_AVAILABILITY
    assert bounds.qualifies is False
    assert bounds.disqualified is True or bounds.inconclusive is True


def test_credal_risk_bounds_monotonic_corners():
    credal = CredalRates(fp=Interval(0.01, 0.03), fn=Interval(0.17, 0.25))

    # Passed check
    b_pass = compute_credal_risk_bounds(credal, passed=True)
    assert 0.0370 <= b_pass.lower_risk <= 0.0380
    assert 0.0545 <= b_pass.upper_risk <= 0.0555
    assert b_pass.inconclusive is True  # 0.03746 <= 0.050 < 0.05508

    # Failed check
    b_fail = compute_credal_risk_bounds(credal, passed=False)
    assert 0.7800 <= b_fail.lower_risk <= 0.7900
    assert 0.8650 <= b_fail.upper_risk <= 0.8750
    assert b_fail.disqualified is True  # 0.78448 > 0.050


def test_sample_size_sensitivity_monotonic_width():
    sample_sizes = [50, 100, 500, 2000]
    results = evaluate_sample_size_sensitivity(sample_sizes, n_reps=500, seed=EXPLORATORY_SEED_BASE)

    assert len(results) == 4
    # Bound widths must decrease monotonically as sample size increases
    widths = [r["mean_risk_width"] for r in results]
    assert widths[0] > widths[1] > widths[2] > widths[3]
    # Parameter coverage must remain close to nominal 95%
    for r in results:
        assert r["param_coverage"] >= 0.940


def test_five_arm_benchmark_reproduction():
    benchmark = run_five_arm_benchmark(n_reps=500, seed=EXPLORATORY_SEED_BASE + 10)

    # Arm A (Point Bayes): Falsely qualifies safe
    arm_a = benchmark["arm_a_point"]
    assert arm_a["qualifies"] is True
    assert arm_a["false_safety_qualification"] is True
    assert arm_a["utility"] == -100.0

    # Arm B (Oracle Credal): Abstains safely, zero false qualifications
    arm_b = benchmark["arm_b_oracle"]
    assert arm_b["inconclusive"] is True
    assert arm_b["false_safety_qualification"] is False

    # Arm C (Calibrated N=1000/500): High coverage, low failure rate
    arm_c = benchmark["arm_c_calibrated"]
    assert arm_c["parameter_coverage"] >= 0.940
    assert arm_c["false_safety_qualification_rate"] <= 0.020

    # Arm E (Frechet Copula): Inconclusive, encloses true dependent risk
    arm_e = benchmark["arm_e_frechet"]
    assert arm_e["inconclusive"] is True
    assert arm_e["risk_enclosed"] is True
    assert arm_e["false_safety_qualification"] is False


def test_clustered_sampling_coverage_degradation():
    violations = run_assumption_violation_scenarios(n_reps=500, seed=EXPLORATORY_SEED_BASE + 20)
    base = violations["scenario_1_independent_baseline"]
    clust = violations["scenario_2_clustered_calibration"]

    # Baseline i.i.d. coverage must be >= 95%
    assert base["empirical_coverage"] >= 0.950

    # Clustered sampling must statistically significantly degrade coverage
    assert clust["empirical_coverage"] < base["empirical_coverage"] - 0.20
    assert clust["coverage_degradation"] >= 0.20


def test_ast_clean_imports_and_seed_isolation():
    # Verify no hidden controller or production authorization imports
    tree = ast.parse(Path(experiment.__file__).read_text(encoding="utf-8"))
    imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    assert not any(
        x and ("domain_de" in x or "policy_v07_1" in x or "confirmatory" in x) for x in imports
    )

    # Verify seed isolation: EXPLORATORY_SEED_BASE is >= 50000000 and < 60000000
    assert 50000000 <= EXPLORATORY_SEED_BASE < 60000000
    assert EXPLORATORY_SEED_BASE not in range(70100001, 70100129)
    assert EXPLORATORY_SEED_BASE not in range(70200001, 70200129)
    assert EXPLORATORY_SEED_BASE not in range(60030001, 60030129)


def test_rate_confidence_interval_bounds():
    # Two-sided Wilson interval for 0 successes in 1000 trials (exact: z^2/n / (1 + z^2/n) ~= 0.003827)
    low_0, high_0 = rate_confidence_interval(0, 1000, method="wilson")
    assert low_0 == 0.0
    assert 0.00380 <= high_0 <= 0.00385

    # One-sided rule of three approximation for 0 successes in 1000 trials (3 / n = 0.003)
    low_rot, high_rot = rate_confidence_interval(0, 1000, method="rule_of_three")
    assert low_rot == 0.0
    assert high_rot == 0.003

    # Exact Clopper-Pearson two-sided interval for 0 successes in 1000 trials (1 - (0.025)^0.001 ~= 0.003682)
    low_cp, high_cp = rate_confidence_interval(0, 1000, method="clopper_pearson")
    assert low_cp == 0.0
    assert 0.00365 <= high_cp <= 0.00370

    # Wilson interval for 500 successes in 1000 trials (50%)
    low_500, high_500 = rate_confidence_interval(500, 1000, method="wilson")
    assert 0.468 <= low_500 <= 0.472
    assert 0.528 <= high_500 <= 0.532
