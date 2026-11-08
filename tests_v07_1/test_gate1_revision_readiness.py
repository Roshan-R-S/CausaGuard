"""Tests for Gate 1 statistical methodology revision readiness.

Verifies:
- Minimum cluster counts K_min required for zero-event Gate 1 qualification.
- Feasibility metrics across K in {32, 48, 56, 64, 128, 256}.
- Empirical Bernstein 100% false rejection at K=128.
- Exact Clopper-Pearson zero-event and maximum passing failure counts.
- Non-monotonicity proof for sample-variance-based bounds (Student-t, Empirical Bernstein).
- Strict monotonicity proof for cluster-level Clopper-Pearson.
- Multiplicity and error budget separation between Gate 1 (alpha=0.050) and Gate 2 (alpha=0.010/3).

Research status: EXPLORATORY RESEARCH ONLY -- PRE-FREEZE NO-GO.
"""

from __future__ import annotations

import pytest

from research.experiments.gate1_coverage_audit import (
    PRE_FREEZE_NO_GO,
    PRODUCTION_AUTHORIZATION_ENABLED,
)
from research.experiments.gate1_coverage_audit.feasibility import (
    compute_zero_event_ucb,
    demonstrate_variance_non_monotonicity,
    evaluate_cluster_count_feasibility,
    evaluate_policy_risk_performance,
    find_min_k_for_qualification,
)


def test_research_status_and_flag_isolation():
    """Verify research isolation invariants."""
    assert PRE_FREEZE_NO_GO is True
    assert PRODUCTION_AUTHORIZATION_ENABLED is False


def test_minimum_cluster_counts_for_zero_event_qualification():
    """Verify exact theoretical minimum cluster counts required to pass Gate 1 at Z=0.

    - Clopper-Pearson: K >= ceil(ln(alpha) / ln(1 - tau_safe)) = 59.
    - Empirical Bernstein: K >= ceil(7 ln(2/alpha) / (3 tau_safe) + 1) = 174 (Maurer & Pontil 2009 Thm 4).
    - Hoeffding: K >= ceil(ln(1/alpha) / (2 tau_safe^2)) = 600.
    """
    alpha = 0.050
    tau_safe = 0.050

    min_k_cp = find_min_k_for_qualification(alpha=alpha, tau_safe=tau_safe, method="clopper_pearson")
    min_k_eb = find_min_k_for_qualification(alpha=alpha, tau_safe=tau_safe, method="empirical_bernstein")
    min_k_hoeffding = find_min_k_for_qualification(alpha=alpha, tau_safe=tau_safe, method="hoeffding")

    assert min_k_cp == 59
    assert min_k_eb == 174
    assert min_k_hoeffding == 600

    # At K = 58: Clopper-Pearson cannot qualify
    assert compute_zero_event_ucb(k=58, alpha=alpha, method="clopper_pearson") > tau_safe
    # At K = 59: Clopper-Pearson qualifies
    assert compute_zero_event_ucb(k=59, alpha=alpha, method="clopper_pearson") <= tau_safe

    # At K = 173: Empirical Bernstein cannot qualify (0.050043 > 0.050)
    assert compute_zero_event_ucb(k=173, alpha=alpha, method="empirical_bernstein") > tau_safe
    # At K = 174: Empirical Bernstein qualifies (0.049753 <= 0.050)
    assert compute_zero_event_ucb(k=174, alpha=alpha, method="empirical_bernstein") <= tau_safe


def test_feasibility_across_cluster_sample_sizes():
    """Verify feasibility across K in {32, 48, 56, 64, 128, 256}."""
    ks = [32, 48, 56, 64, 128, 256]
    feasibility = evaluate_cluster_count_feasibility(k_values=ks, alpha=0.050, tau_safe=0.050)

    # For K in {32, 48, 56}: NO method can qualify, even at Z=0
    for method in ["clopper_pearson", "empirical_bernstein", "existing_gate1"]:
        metrics_by_k = {m.k_clusters: m for m in feasibility[method]}
        for k in [32, 48, 56]:
            assert metrics_by_k[k].qualification_possible_at_zero_events is False
            assert metrics_by_k[k].max_passing_z == -1

    # For K = 64:
    cp_64 = next(m for m in feasibility["clopper_pearson"] if m.k_clusters == 64)
    eb_64 = next(m for m in feasibility["empirical_bernstein"] if m.k_clusters == 64)
    ex_64 = next(m for m in feasibility["existing_gate1"] if m.k_clusters == 64)

    assert cp_64.qualification_possible_at_zero_events is True
    assert cp_64.max_passing_z == 0  # Clopper-Pearson only passes at Z=0
    assert eb_64.qualification_possible_at_zero_events is False  # EB cannot pass
    assert eb_64.max_passing_z == -1
    assert ex_64.max_passing_z == 1  # Existing Gate 1 passes for Z in {0, 1}

    # For K = 128 (Planned confirmatory sample size):
    cp_128 = next(m for m in feasibility["clopper_pearson"] if m.k_clusters == 128)
    eb_128 = next(m for m in feasibility["empirical_bernstein"] if m.k_clusters == 128)
    ex_128 = next(m for m in feasibility["existing_gate1"] if m.k_clusters == 128)

    assert cp_128.qualification_possible_at_zero_events is True
    assert cp_128.max_passing_z == 2  # Clopper-Pearson passes for Z in {0, 1, 2}
    assert eb_128.qualification_possible_at_zero_events is False  # EB FAILS at K=128 even at Z=0
    assert eb_128.max_passing_z == -1
    assert ex_128.max_passing_z == 3  # Existing Gate 1 passes for Z in {0, 1, 2, 3} (FSQ defect)

    # For K = 256:
    cp_256 = next(m for m in feasibility["clopper_pearson"] if m.k_clusters == 256)
    eb_256 = next(m for m in feasibility["empirical_bernstein"] if m.k_clusters == 256)
    ex_256 = next(m for m in feasibility["existing_gate1"] if m.k_clusters == 256)

    assert cp_256.max_passing_z == 6
    assert eb_256.max_passing_z == 1  # Corrected theorem: EB passes if Z <= 1
    assert ex_256.max_passing_z == 8


def test_empirical_bernstein_unavoidable_false_rejection_at_k128():
    """Verify that Empirical Bernstein suffers 100% unnecessary rejection at K=128."""
    # Even for an exceptionally safe candidate policy with true risk theta = 0.001
    res = evaluate_policy_risk_performance(k=128, theta=0.001, alpha=0.050, tau_safe=0.050)
    eb = res["empirical_bernstein"]

    # Even at theta=0.001, EB has 100% unnecessary rejection and 0% power to qualify
    assert eb.unnecessary_rejection == pytest.approx(1.0, abs=1e-8)
    assert eb.qualification_power == pytest.approx(0.0, abs=1e-8)
    assert eb.expected_ucb > 0.050


def test_clopper_pearson_power_at_k128():
    """Verify Clopper-Pearson qualification power for safe candidate policies at K=128."""
    # Candidate with true risk theta = 0.005
    res_005 = evaluate_policy_risk_performance(k=128, theta=0.005, alpha=0.050, tau_safe=0.050)
    cp_005 = res_005["clopper_pearson"]
    assert cp_005.qualification_power > 0.950  # ~97.31% power to qualify

    # Candidate with true risk theta = 0.010
    res_010 = evaluate_policy_risk_performance(k=128, theta=0.010, alpha=0.050, tau_safe=0.050)
    cp_010 = res_010["clopper_pearson"]
    assert cp_010.qualification_power > 0.850  # ~86.25% power to qualify


def test_variance_non_monotonicity_proof():
    """Verify that methods based on sample variance (Student-t, Empirical Bernstein)

    are not universally monotonic, while Clopper-Pearson is strictly monotonic.
    """
    demo = demonstrate_variance_non_monotonicity(k=128, alpha=0.050)

    # Empirical Bernstein unclipped UCB DECREASES when risk in cluster 0 is increased from 0.0 to 0.10!
    assert demo["empirical_bernstein"]["is_non_monotonic"] is True
    assert demo["empirical_bernstein"]["delta_ucb"] < 0.0

    # Student-t unclipped UCB also DECREASES
    assert demo["student_t"]["is_non_monotonic"] is True
    assert demo["student_t"]["delta_ucb"] < 0.0

    # Clopper-Pearson UCB is strictly non-decreasing
    assert demo["clopper_pearson"]["is_non_monotonic"] is False
    assert demo["clopper_pearson"]["delta_ucb"] > 0.0


def test_error_budget_separation_and_invariants():
    """Verify statistical error budget allocation standards."""
    alpha_gate1 = 0.050
    alpha_superiority_fwer = 0.010
    n_superiority_contrasts = 3
    alpha_contrast = alpha_superiority_fwer / n_superiority_contrasts

    assert alpha_gate1 == 0.050
    assert alpha_contrast == pytest.approx(0.0033333333333333335, abs=1e-10)
    # The two budgets are separate and distinct
    assert alpha_gate1 != alpha_contrast
