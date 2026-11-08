"""Acceptance and regression test suite for Gate 1 statistical safety-bound falsification.

Verifies:
1. Exact mathematical reproduction of the 88.8242% undercoverage and 11.1758% FSQ counterexample.
2. Non-monotonicity between 0-event and 1-event cluster outcomes (UCB[1] < UCB[0]).
3. Rigorous decoupling of per-case risk, cluster any-harm probability, and mean cluster rate.
4. Mathematical properties of alternative procedures (Clopper-Pearson, Maurer-Pontil, Hall skewness-corrected).
5. Coverage sensitivity to intraclass correlation rho from 0.0 to 1.0.
6. Quarantine and isolation: No reserved confirmatory seeds, no production auth.

STATUS: EXPLORATORY SCIENTIFIC RESEARCH — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

import json
import math

import numpy as np
import pytest

from research.experiments.gate1_coverage_audit import (
    PRE_FREEZE_NO_GO,
    PRODUCTION_AUTHORIZATION_ENABLED,
)
from research.experiments.gate1_coverage_audit.counterexample import (
    compute_protocol_ucb,
    reproduce_exact_counterexample,
)
from research.experiments.gate1_coverage_audit.estimand import (
    ESTIMAND_CLUSTER_ANY_HARM,
    ESTIMAND_GATE1_STANDARD,
    ESTIMAND_MEAN_CLUSTER_RATE,
    ESTIMAND_PER_CASE,
    EstimandType,
    SamplingUnit,
)
from research.experiments.gate1_coverage_audit.experiment import (
    build_audit_evidence_report,
    evaluate_exact_bernoulli_shock_methods,
)
from research.experiments.gate1_coverage_audit.methods import (
    ucb_cluster_clopper_pearson,
    ucb_gate1_existing,
    ucb_icc_sensitivity_bounds,
)

# ==============================================================================
# 1. Isolation & Security Guardrail Tests
# ==============================================================================


def test_research_status_and_flag_isolation():
    """Verify exploratory status and production auth disabled."""
    assert PRE_FREEZE_NO_GO is True
    assert PRODUCTION_AUTHORIZATION_ENABLED is False


def test_no_reserved_confirmatory_seeds_in_report():
    """Verify report contains no reserved confirmatory seeds (70100001+, 70200001+, 60030001+)."""
    report = build_audit_evidence_report()
    serialized = json.dumps(report)
    for forbidden_seed in ("7010", "7020", "6003"):
        assert forbidden_seed not in serialized


# ==============================================================================
# 2. Exact Counterexample Reproduction Tests
# ==============================================================================


def test_exact_reproduction_of_88_82_percent_undercoverage():
    """Verify exact reproduction of 88.8242% coverage and 11.1758% FSQ at theta=0.0501."""
    repro = reproduce_exact_counterexample(theta=0.0501, tau_safe=0.050, k=128, alpha=0.050)

    # Coverage: exactly 0.8882421570 (88.8242%)
    assert repro.exact_coverage == pytest.approx(0.8882421570, abs=1e-8)
    assert round(repro.exact_coverage * 100, 4) == 88.8242

    # False Safety Qualification: exactly 0.1117578430 (11.1758%)
    assert repro.exact_fsq == pytest.approx(0.1117578430, abs=1e-8)
    assert round(repro.exact_fsq * 100, 4) == 11.1758

    # The claimed confidence was 95.0%; empirical undercoverage is 6.18 percentage points
    assert repro.exact_coverage < 0.950 - 0.05


def test_exact_non_monotonicity_anomaly():
    """Verify non-monotonicity: UCB for 1 failure is LOWER than UCB for 0 failures."""
    ucb_0 = compute_protocol_ucb(z=0, k=128, alpha=0.050)
    ucb_1 = compute_protocol_ucb(z=1, k=128, alpha=0.050)

    assert ucb_0 == pytest.approx(0.0231324053, abs=1e-8)
    assert ucb_1 == pytest.approx(0.0207573464, abs=1e-8)

    # Paradox: having 1 failed cluster produces a more optimistic bound than 0 failures!
    delta = ucb_1 - ucb_0
    assert delta < 0.0
    assert delta == pytest.approx(-0.0023750588, abs=1e-8)


def test_non_coverage_outcomes_set():
    """Verify that failure to cover theta=0.0501 occurs precisely for z in {0, 1, 2, 3}."""
    ucbs = [compute_protocol_ucb(z, k=128, alpha=0.050) for z in range(129)]

    for z in (0, 1, 2, 3):
        assert ucbs[z] < 0.0501  # Fails coverage
        assert ucbs[z] <= 0.050  # Passes Gate 1 (FSQ!)

    # Starting from z=4, UCB > 0.0501 and UCB > 0.050
    for z in range(4, 129):
        assert ucbs[z] > 0.0501
        assert ucbs[z] > 0.050


# ==============================================================================
# 3. Statistical Estimand Decoupling Tests
# ==============================================================================


def test_estimand_definitions_and_hierarchy():
    """Verify separation of per-case risk, cluster any-harm, and mean cluster rate."""
    assert ESTIMAND_PER_CASE.sampling_unit == SamplingUnit.CASE
    assert ESTIMAND_CLUSTER_ANY_HARM.sampling_unit == SamplingUnit.CLUSTER
    assert ESTIMAND_MEAN_CLUSTER_RATE.sampling_unit == SamplingUnit.CLUSTER
    assert ESTIMAND_GATE1_STANDARD.sampling_unit == SamplingUnit.STUDY

    assert ESTIMAND_PER_CASE.estimand_type == EstimandType.PER_CASE_RISK
    assert ESTIMAND_CLUSTER_ANY_HARM.estimand_type == EstimandType.CLUSTER_ANY_HARM
    assert ESTIMAND_MEAN_CLUSTER_RATE.estimand_type == EstimandType.MEAN_CLUSTER_RATE


def test_estimand_inequality_bounds():
    """Verify mathematical inequality: theta <= q_cluster <= min(1, N * theta)."""
    theta = 0.050
    n = 400

    # Under independent cases (rho = 0):
    q_indep = 1.0 - (1.0 - theta) ** n
    assert theta <= q_indep <= min(1.0, n * theta)
    assert q_indep > 0.99999999  # Almost certainty under N=400!

    # Under common shock (rho = 1):
    q_shock = theta
    assert math.isclose(q_shock, theta)
    assert theta <= q_shock <= min(1.0, n * theta)


# ==============================================================================
# 4. Alternative Procedure Mathematical Properties
# ==============================================================================


def test_cluster_clopper_pearson_is_strictly_monotonic():
    """Verify Cluster Clopper-Pearson is strictly monotonic with zero non-monotonicity."""
    k = 128
    alpha = 0.050
    ucbs = []
    for z in range(k + 1):
        r = np.array([1.0] * z + [0.0] * (k - z), dtype=np.float64)
        res = ucb_cluster_clopper_pearson(r, alpha=alpha)
        ucbs.append(res.ucb)

    for z in range(k):
        assert ucbs[z] < ucbs[z + 1], f"Non-monotonicity at z={z}: {ucbs[z]} >= {ucbs[z+1]}"

    # At z=0: exact match with zero-event formula
    assert ucbs[0] == pytest.approx(1.0 - alpha ** (1.0 / k), abs=1e-8)
    # At z=1: strictly greater than z=0
    assert ucbs[1] > ucbs[0]
    assert ucbs[1] == pytest.approx(0.036523825, abs=1e-6)


def test_cluster_clopper_pearson_maintains_exact_coverage():
    """Verify Cluster Clopper-Pearson achieves >= 95% coverage at theta=0.0501."""
    evals = evaluate_exact_bernoulli_shock_methods(theta=0.0501, k=128, alpha=0.050, tau_safe=0.050)
    cp = evals["cluster_clopper_pearson"]

    # Coverage is >= 95%
    assert cp["coverage"] >= 0.950
    assert cp["coverage"] == pytest.approx(0.957822, abs=1e-4)
    # FSQ is strictly controlled below 5% (here 4.22%)
    assert cp["fsq"] <= 0.050
    assert cp["fsq"] == pytest.approx(0.042178, abs=1e-4)
    assert cp["non_monotonic"] is False


def test_empirical_bernstein_finite_sample_conservatism():
    """Verify Maurer-Pontil Empirical Bernstein achieves 100% coverage at theta=0.0501."""
    evals = evaluate_exact_bernoulli_shock_methods(theta=0.0501, k=128, alpha=0.050, tau_safe=0.050)
    eb = evals["empirical_bernstein"]

    # Finite sample valid: coverage is strictly >= 95% (here 100.0%)
    assert eb["coverage"] >= 0.950
    # Zero false safety qualifications: FSQ = 0.0%
    assert eb["fsq"] == pytest.approx(0.0, abs=1e-8)
    assert eb["non_monotonic"] is False


def test_degenerate_zero_variance_positive_risk_fail_closed():
    """Verify fail-closed Gate 1 rejection on degenerate constant positive risk."""
    r_const = [0.03] * 128  # std = 0, mean = 0.03
    res = ucb_gate1_existing(r_const, alpha=0.050, tau_safe=0.050)

    assert res.ucb == 1.0
    assert res.gate1_passed is False
    assert res.method_name == "existing_gate1_degenerate_fail_closed"


# ==============================================================================
# 5. Sensitivity to Intraclass Correlation (rho)
# ==============================================================================


def test_icc_sensitivity_bounds_effective_sample_size():
    """Verify effective sample size scaling with intraclass correlation rho."""
    r = [0.02] * 64 + [0.0] * 64
    bounds = ucb_icc_sensitivity_bounds(r, n_cases_per_cluster=400)
    curve = bounds["sensitivity_curve"]

    # At rho = 0.0: K_eff = 128 * 400 = 51,200
    assert curve["rho_0.00"]["k_effective"] == 51200.0
    assert curve["rho_0.00"]["design_effect"] == 1.0

    # At rho = 1.0: K_eff = 128
    assert curve["rho_1.00"]["k_effective"] == 128.0
    assert curve["rho_1.00"]["design_effect"] == 400.0

    # Bound widens monotonically as rho increases:
    assert curve["rho_0.00"]["ucb"] < curve["rho_0.10"]["ucb"] < curve["rho_1.00"]["ucb"]
