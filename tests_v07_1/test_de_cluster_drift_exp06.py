"""Unit and acceptance tests for Experiment 06 (Cluster-Robust Calibration & Sequential Drift Detection).

Verifies cluster estimators, profile likelihood, cluster bootstrap, sequential CUSUM monitors,
compensating drift counterexamples, and AST seed isolation.
"""

import ast
from pathlib import Path

import numpy as np
import pytest

from research.experiments.de_cluster_drift_exp06.experiment import (
    DEFAULT_AVAILABILITY,
    DEFAULT_PRIOR,
    EXPLORATORY_SEED_BASE,
    SAFETY_THRESHOLD,
    CredalRates,
    Interval,
    PageCUSUMMonitor,
    RiskBounds,
    StaticNoMonitor,
    estimate_icc_and_deff,
    exact_clopper_pearson,
    generate_clustered_batch,
    method_a_naive_clopper_pearson,
    method_b_design_effect_clopper_pearson,
    method_c_beta_binomial_profile,
    method_d_cluster_bootstrap,
    method_e_conservative_cluster_bound,
    simulate_drift_trajectory,
)


def test_interval_properties_and_dataclasses():
    """Verify Interval, CredalRates, and RiskBounds validation."""
    iv = Interval(0.10, 0.30)
    assert iv.low == 0.10
    assert iv.high == 0.30
    assert abs(iv.width - 0.20) < 1e-6
    assert iv.contains(0.20)
    assert not iv.contains(0.05)
    assert not iv.contains(0.35)

    with pytest.raises(ValueError):
        Interval(-0.1, 0.5)
    with pytest.raises(ValueError):
        Interval(0.6, 0.4)

    credal = CredalRates(fp=Interval(0.01, 0.05), fn=Interval(0.15, 0.30))
    assert credal.contains(0.02, 0.20)
    assert not credal.contains(0.06, 0.20)

    rb = RiskBounds(lower_risk=0.02, upper_risk=0.045, status="QUALIFY_SAFE")
    assert rb.qualifies
    assert not rb.disqualified
    assert not rb.inconclusive
    assert rb.encloses(0.03)

    rb_inconcl = RiskBounds(
        lower_risk=0.03, upper_risk=0.07, status="INCONCLUSIVE_ABSTAIN"
    )
    assert rb_inconcl.inconclusive
    assert not rb_inconcl.qualifies


def test_clopper_pearson_exact_calculation():
    """Verify Clopper-Pearson exact bounds for zero, interior, and total successes."""
    # Zero successes in 1000
    low0, high0 = exact_clopper_pearson(0, 1000, 0.05)
    assert low0 == 0.0
    expected_high0 = 1.0 - (0.025) ** (1.0 / 1000)
    assert abs(high0 - expected_high0) < 1e-6

    # All successes
    lown, highn = exact_clopper_pearson(1000, 1000, 0.05)
    assert highn == 1.0
    assert abs(lown - (0.025) ** (1.0 / 1000)) < 1e-6

    # Interior: 20 successes in 1000, alpha=0.05
    low20, high20 = exact_clopper_pearson(20, 1000, 0.05)
    assert 0.010 < low20 < 0.020
    assert 0.020 < high20 < 0.035
    assert low20 < 20 / 1000 < high20


def test_icc_and_deff_estimation():
    """Verify ANOVA moment estimator of ICC and design effect."""
    rng = np.random.default_rng(EXPLORATORY_SEED_BASE)
    # 50 clusters of size 20, true ICC = 0.25
    batch = generate_clustered_batch(50, 20, 0.20, 0.25, rng=rng)
    assert batch.c_count == 50
    assert batch.n_total == 1000

    icc_est, deff_est, n_eff, k_eff = estimate_icc_and_deff(batch.k_vec, batch.m_vec)
    # Estimated ICC should be positive and within reasonable sampling bounds of 0.25
    assert 0.10 <= icc_est <= 0.40
    # DEFF = 1 + (20 - 1) * 0.25 = 5.75 theoretical
    assert 2.5 <= deff_est <= 8.5
    # N_eff should be significantly smaller than 1000
    assert n_eff < 500
    assert n_eff >= 50


def test_method_a_naive_undercoverage_under_clustering():
    """Confirm that naive Clopper-Pearson under-covers under intra-cluster correlation."""
    rng = np.random.default_rng(EXPLORATORY_SEED_BASE + 50)
    true_p = 0.050
    icc = 0.30
    n_reps = 150
    hits = 0

    for _ in range(n_reps):
        batch = generate_clustered_batch(15, 20, true_p, icc, rng=rng)
        iv = method_a_naive_clopper_pearson(batch, alpha=0.05)
        if iv.contains(true_p):
            hits += 1

    emp_cov = hits / n_reps
    # Under ICC=0.30 and m=20, DEFF = 6.7. Nominal 95% interval severely collapses (< 80%)
    assert emp_cov < 0.85, f"Expected coverage collapse under clustering, got {emp_cov}"


def test_method_b_deff_adjusted_interval_wider_than_naive():
    """Verify that Rao-Scott adjustment widens the confidence interval proportionally to DEFF."""
    rng = np.random.default_rng(EXPLORATORY_SEED_BASE + 60)
    batch = generate_clustered_batch(25, 20, 0.10, 0.25, rng=rng)

    iv_naive = method_a_naive_clopper_pearson(batch, alpha=0.05)
    iv_deff = method_b_design_effect_clopper_pearson(batch, alpha=0.05)

    assert iv_deff.width > iv_naive.width
    assert (
        iv_deff.width >= 1.3 * iv_naive.width
    )  # Should expand by approximately sqrt(DEFF)


def test_method_c_profile_likelihood_properties():
    """Verify Beta-Binomial profile likelihood interval computation."""
    rng = np.random.default_rng(EXPLORATORY_SEED_BASE + 70)
    batch = generate_clustered_batch(20, 15, 0.15, 0.20, rng=rng)

    iv_profile = method_c_beta_binomial_profile(batch, alpha=0.05)
    assert 0.0 <= iv_profile.low < iv_profile.high <= 1.0
    assert iv_profile.width > 0.02
    assert iv_profile.contains(0.15)


def test_method_d_cluster_bootstrap_resampling():
    """Verify whole-cluster bootstrap resampling interval."""
    rng = np.random.default_rng(EXPLORATORY_SEED_BASE + 80)
    batch = generate_clustered_batch(30, 15, 0.20, 0.15, rng=rng)

    iv_boot = method_d_cluster_bootstrap(batch, alpha=0.05, n_boot=500, rng=rng)
    assert 0.0 <= iv_boot.low < iv_boot.high <= 1.0
    assert iv_boot.contains(0.20)


def test_method_e_conservative_baseline_guarantee():
    """Verify Method E (worst-case cluster bound) maintains >= 95% coverage under strong clustering."""
    rng = np.random.default_rng(EXPLORATORY_SEED_BASE + 90)
    true_p = 0.050
    icc = 0.35
    n_reps = 100
    hits = 0

    for _ in range(n_reps):
        batch = generate_clustered_batch(20, 15, true_p, icc, rng=rng)
        iv_cons = method_e_conservative_cluster_bound(batch, alpha=0.05)
        if iv_cons.contains(true_p):
            hits += 1

    emp_cov = hits / n_reps
    # Method E treats each cluster as N_eff = C, guaranteeing conservative coverage
    assert emp_cov >= 0.94


def test_unidentifiable_compensating_drift_counterexample():
    """Test that compensating drift (surge in pi and FN, drop in FP) fools unlabelled CUSUM while risk surges."""
    # Under nominal: pi = 0.20, fp = 0.02, fn = 0.24 -> p0 = 0.83200, risk = 0.0525
    p0 = (1.0 - DEFAULT_PRIOR) * (1.0 - 0.020) + DEFAULT_PRIOR * 0.240
    assert abs(p0 - 0.83200) < 1e-6

    # Drifted: pi = 0.25, fn = 0.38, fp = 0.01733 -> p1 = 0.83200
    fp_drift = 1.0 - (p0 - 0.250 * 0.380) / 0.750
    p1 = (1.0 - 0.250) * (1.0 - fp_drift) + 0.250 * 0.380
    assert abs(p1 - p0) < 1e-6

    # True operational risk under drifted state
    denom = 0.250 * 0.380 + (1.0 - 0.250) * (1.0 - fp_drift)
    post_drift = (0.250 * 0.380) / denom
    risk_drift = DEFAULT_AVAILABILITY * post_drift

    # Risk surges to > 0.10, doubling safety threshold of 0.050
    assert risk_drift > 0.100
    assert risk_drift > 2 * SAFETY_THRESHOLD

    # Simulate trajectory under Page CUSUM: monitor fails to alarm because p1 == p0!
    rng = np.random.default_rng(EXPLORATORY_SEED_BASE + 200)
    mon = PageCUSUMMonitor(p0=0.832, h=6.0)
    traj = simulate_drift_trajectory(
        "scenario_5_compensating_unidentifiable", mon, horizon=600, drift_time=200, rng=rng
    )

    # Monitor fails to trigger alarm despite severe operational risk surge
    assert not traj.alarm_triggered
    assert traj.post_drift_hazardous_count > 0
    assert traj.post_drift_hazardous_count <= 400
    assert traj.pre_drift_hazardous_count <= 200
    assert traj.total_hazardous_count == traj.pre_drift_hazardous_count + traj.post_drift_hazardous_count


def test_post_drift_hazardous_exposure_bounded_by_window():
    """Verify that post-drift hazardous qualified counts are strictly bounded by post-drift window (400)."""
    rng = np.random.default_rng(EXPLORATORY_SEED_BASE + 250)
    mon = StaticNoMonitor()
    scenarios = [
        "scenario_1_sudden_fn",
        "scenario_2_gradual_fn",
        "scenario_3_fp_surge",
        "scenario_4_prevalence_shift",
        "scenario_5_compensating_unidentifiable",
    ]
    for sc in scenarios:
        traj = simulate_drift_trajectory(sc, mon, horizon=600, drift_time=200, rng=rng)
        assert traj.post_drift_hazardous_count <= 400
        assert traj.pre_drift_hazardous_count <= 200
        assert traj.total_hazardous_count <= 600
        assert traj.post_drift_exposure_steps <= 400


def test_scenario_1_exact_pass_rate_and_kl_divergence():
    """Verify exact post-drift pass rate (0.860 vs 0.854) and exact Kullback-Leibler divergence."""
    pi = 0.20
    fp = 0.020
    fn_drift = 0.380
    fn_alt = 0.350

    # True pass rate under FN=0.38 is 0.860 (not 0.854!)
    p_true = (1.0 - pi) * (1.0 - fp) + pi * fn_drift
    assert abs(p_true - 0.86000) < 1e-6

    # 0.854 corresponds strictly to FN=0.350
    p_alt = (1.0 - pi) * (1.0 - fp) + pi * fn_alt
    assert abs(p_alt - 0.85400) < 1e-6

    # Exact Bernoulli KL divergences from nominal p0 = 0.83200
    p0 = 0.83200
    kl_0860 = p_true * np.log(p_true / p0) + (1.0 - p_true) * np.log((1.0 - p_true) / (1.0 - p0))
    assert abs(kl_0860 - 0.002941) < 1e-5

    kl_0854 = p_alt * np.log(p_alt / p0) + (1.0 - p_alt) * np.log((1.0 - p_alt) / (1.0 - p0))
    assert abs(kl_0854 - 0.001796) < 1e-5


def test_wilson_score_zero_events_reconciliation():
    """Verify that 0 events in 300 trials bounds failure probability to <= 1.26%, never zero."""
    n = 300
    z = 1.95996
    # Two-sided 95% Wilson score upper bound at k=0
    wilson_upper = (z**2 / n) / (1.0 + z**2 / n)
    assert 0.0125 < wilson_upper < 0.0130

    # One-sided rule-of-three upper bound at k=0
    rule_of_three = 3.0 / n
    assert abs(rule_of_three - 0.0100) < 1e-6
    # Confirms that 0 observed FSQs in 300 trials does NOT prove zero failure rate
    assert wilson_upper > 0.010


def test_ast_clean_imports_and_seed_isolation():
    """Enforce strict AST isolation: no prohibited controller imports and safe seeds."""
    exp_path = (
        Path(__file__).parents[1]
        / "research"
        / "experiments"
        / "de_cluster_drift_exp06"
        / "experiment.py"
    )
    with open(exp_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    prohibited_modules = {
        "domain_de",
        "policy_v07_1",
        "confirmatory_runner_v07_1",
        "seal_verifier_v07_1",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert (
                    alias.name not in prohibited_modules
                ), f"Prohibited module imported: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                assert (
                    node.module not in prohibited_modules
                ), f"Prohibited module imported: {node.module}"

    # Verify exploratory seed base is in safe exploratory range (50200001+)
    assert EXPLORATORY_SEED_BASE >= 50200000
    assert EXPLORATORY_SEED_BASE < 60000000  # Outside confirmatory range 60000000+
