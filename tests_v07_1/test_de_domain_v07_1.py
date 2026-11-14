"""Tests for CausaGuard v0.7.1 Data Engineering pipeline mechanics."""

import pytest
from causaguard_v07_1.domain_de import (
    OP_COSTS_DE_V07_1,
    PROFILES_DE_V07_1,
    DEEvidenceV07_1,
    DEObservationV07_1,
    _check_independent_access,
    execute_de_step_v07_1,
    make_de_cases_v07_1,
)


def test_de_case_generation_deterministic():
    cases1 = make_de_cases_v07_1(10, seed=777, profile="iid")
    cases2 = make_de_cases_v07_1(10, seed=777, profile="iid")
    assert len(cases1) == 10
    for c1, c2 in zip(cases1, cases2):
        assert c1.key == c2.key
        assert c1.f_schema == c2.f_schema
        assert c1.f_content == c2.f_content
        assert c1.f_transient == c2.f_transient
        assert c1.observation == c2.observation
        assert c1.draws == c2.draws
        assert len(c1.draws) == 12


def test_de_observation_validation():
    with pytest.raises(ValueError, match="Invalid budget"):
        DEObservationV07_1(
            pipeline_load=0.5,
            schema_alarm=0.3,
            data_age_hours=12.0,
            source_quality=0.8,
            column_count_changed=0,
            quoted_fp_schema=0.05,
            quoted_fn_schema=0.05,
            observation_delay=0.2,
            deadline_hours=3.0,
            value=1.2,
            harm=4.0,
            apply_cost=0.03,
            verify_cost=0.15,
            restore_cost=0.20,
            escalation_cost=0.30,
            time_cost_per_hour=0.05,
            budget=0,  # Invalid
        )


def test_de_op_costs_and_budget_exhaustion():
    cases = make_de_cases_v07_1(1, seed=777, profile="iid")
    case = cases[0]

    assert OP_COSTS_DE_V07_1["verify"] == 1
    assert OP_COSTS_DE_V07_1["proceed"] == 1
    assert OP_COSTS_DE_V07_1["restore"] == 1
    assert OP_COSTS_DE_V07_1["escalate"] == 0

    r = execute_de_step_v07_1(case, action="restore", b_rem=0)
    assert r["terminal"] is True
    assert r["allowed"] is False
    assert r["reason"] == "operation_budget"
    assert r["blocked"] == 1


def test_de_restore_fallback_ratio_degradation():
    cases = make_de_cases_v07_1(50, seed=555, profile="iid")
    content_cases = [c for c in cases if c.f_content and not c.f_schema and c.draws[1] >= c.outage]
    assert len(content_cases) > 0
    case = content_cases[0]

    r = execute_de_step_v07_1(case, action="restore", b_rem=1, v_fallback_ratio=0.45)
    assert r["terminal"] is True
    assert r["completed"] == 1
    assert r["completed_fallback"] == 1
    # Check that utility reflects fallback discount 0.45 * V - costs
    expected_v = 0.45 * case.observation.value
    assert pytest.approx(r["utility"], abs=0.05) == (expected_v - r["cost"])


def test_de_schema_drift_persistent_failure_on_restore():
    cases = make_de_cases_v07_1(50, seed=666, profile="iid")
    schema_cases = [c for c in cases if c.f_schema and c.draws[1] >= c.outage]
    assert len(schema_cases) > 0
    case = schema_cases[0]

    # Force persistent failure p_schema_persistent_fail = 1.0
    r = execute_de_step_v07_1(
        case,
        action="restore",
        b_rem=1,
        v_fallback_ratio=0.45,
        p_schema_persistent_fail=1.0,
    )
    assert r["terminal"] is True
    assert r["completed"] == 1
    # Under persistent failure, fallback value collapses to 0.10 * V
    expected_v = 0.10 * case.observation.value
    assert pytest.approx(r["utility"], abs=0.05) == (expected_v - r["cost"])


def test_de_schema_proceed_causes_harm():
    cases = make_de_cases_v07_1(50, seed=777, profile="iid")
    schema_cases = [c for c in cases if c.f_schema and c.draws[1] >= c.outage and _check_independent_access(c, 0)]
    assert len(schema_cases) > 0
    case = schema_cases[0]

    r = execute_de_step_v07_1(case, action="proceed", b_rem=1)
    assert r["terminal"] is True
    assert r["unsafe"] == 1
    assert r["completed"] == 0
    assert r["utility"] <= -case.observation.harm


def test_de_verification_step_and_asymmetric_errors():
    """WP2 test: verifies fallible verification step, asymmetric errors, and delay accounting."""
    cases = make_de_cases_v07_1(20, seed=777, profile="iid")
    accessible_cases = [c for c in cases if _check_independent_access(c, 0)]
    assert len(accessible_cases) > 0
    case = accessible_cases[0]

    # Verification consumes 1 op and is non-terminal when b_rem=2
    res = execute_de_step_v07_1(case, action="verify", b_rem=2, current_latency=0.1, prior_cost=0.05)
    assert res["allowed"] is True
    assert res["terminal"] is False
    assert res["b_rem"] == 1
    assert res["blocked"] == 0

    # Verification evidence
    ev = res["evidence"]
    assert isinstance(ev, DEEvidenceV07_1)
    assert isinstance(ev.schema_valid, bool)
    assert 0.0 <= ev.sample_pass_rate <= 1.0

    # Latency accumulation: current_latency + obs_delay + verif_lag
    expected_latency = 0.1 + case.observation.observation_delay + case.verification_lag
    assert pytest.approx(res["latency"]) == expected_latency
    assert pytest.approx(ev.evidence_age_hours) == expected_latency

    # Cost accumulation: prior_cost + verify_cost + time_cost * latency
    expected_cost = 0.05 + case.observation.verify_cost + case.observation.time_cost_per_hour * expected_latency
    assert pytest.approx(res["cost"]) == expected_cost
    assert pytest.approx(res["utility"]) == -expected_cost

    # Asymmetric error invariant check:
    # If f_schema: schema_valid == (draws[0] < actual_fn_schema)
    # If not f_schema: schema_valid == (draws[0] >= actual_fp_schema)
    if case.f_schema:
        assert ev.schema_valid == (case.draws[0] < case.actual_fn_schema)
    else:
        assert ev.schema_valid == (case.draws[0] >= case.actual_fp_schema)


def test_de_transient_hazard_unobservability():
    """WP2 test: verifies hidden transient hazard is unobservable by static pipeline verification."""
    cases = make_de_cases_v07_1(100, seed=888, profile="iid")
    transient_cases = [
        c
        for c in cases
        if c.f_transient and not c.f_schema and not c.f_content and _check_independent_access(c, 0)
    ]
    assert len(transient_cases) > 0, "Expected at least one pure transient hazard case"
    case = transient_cases[0]

    # Verify action on transient hazard case
    res_v = execute_de_step_v07_1(case, action="verify", b_rem=2)
    assert res_v["allowed"] is True
    ev = res_v["evidence"]
    assert isinstance(ev, DEEvidenceV07_1)

    # Static verification only checks schema and content sampling:
    # Since f_schema is False and f_content is False, sample_pass_rate is clean (>= 0.80)
    assert ev.sample_pass_rate >= 0.80

    # Policy proceeding after clean verification faces the hidden transient hazard:
    # Transient hazard causes execution failure (completed=False, unsafe=False)
    res_p = execute_de_step_v07_1(
        case,
        action="proceed",
        b_rem=res_v["b_rem"],
        current_latency=res_v["latency"],
        prior_cost=res_v["cost"],
        evidence=ev,
    )
    assert res_p["terminal"] is True
    assert res_p["completed"] == 0
    assert res_p["unsafe"] == 0


def test_de_profile_distribution_validation():
    """WP2 distribution-validation test: exercises and verifies all 4 profile distribution shifts."""
    # 1. Invalid profile raises ValueError
    with pytest.raises(ValueError, match="Unknown profile"):
        make_de_cases_v07_1(5, seed=123, profile="invalid_profile")

    # 2. Iterate across all authorized profiles
    assert PROFILES_DE_V07_1 == ("iid", "verifier_shift", "outage_shift", "cost_shift")
    for prof in PROFILES_DE_V07_1:
        cases = make_de_cases_v07_1(10, seed=42, profile=prof)
        assert len(cases) == 10
        for c in cases:
            assert c.profile == prof
            assert isinstance(c.f_schema, bool)
            assert isinstance(c.f_content, bool)
            assert isinstance(c.f_transient, bool)
            assert isinstance(c.defect, bool)

            # Profile-specific distribution assertions:
            if prof == "cost_shift":
                # Cost multiplier 2.5x applied to action costs
                assert c.observation.apply_cost >= 0.025
                assert c.observation.verify_cost >= 0.20
                assert c.observation.restore_cost >= 0.25
                assert c.observation.escalation_cost >= 0.50
            elif prof == "verifier_shift":
                # Shift of +0.20 on actual_fn_schema and +0.10 on actual_fp_schema
                assert c.actual_fn_schema >= c.observation.quoted_fn_schema + 0.15
                assert c.actual_fp_schema >= c.observation.quoted_fp_schema + 0.08
            elif prof == "outage_shift":
                # Outage shift of +0.25 applied to staging outage probability
                assert c.outage >= 0.25
