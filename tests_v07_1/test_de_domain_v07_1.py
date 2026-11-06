"""Tests for CausaGuard v0.7.1 Data Engineering pipeline mechanics."""

import pytest
from causaguard_v07_1.domain_de import (
    OP_COSTS_DE_V07_1,
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
