"""Tests for CausaGuard v0.7.1 Customer Support domain mechanics."""

import pytest
from causaguard_v07_1.domain_cs import (
    OP_COSTS_CS_V07_1,
    CSObservationV07_1,
    execute_cs_step_v07_1,
    make_cs_cases_v07_1,
)


def test_cs_case_generation_deterministic():
    cases1 = make_cs_cases_v07_1(10, seed=777, profile="iid")
    cases2 = make_cs_cases_v07_1(10, seed=777, profile="iid")
    assert len(cases1) == 10
    for c1, c2 in zip(cases1, cases2):
        assert c1.key == c2.key
        assert c1.latent_state == c2.latent_state
        assert c1.observation == c2.observation
        assert c1.draws == c2.draws
        assert len(c1.draws) == 12


def test_cs_observation_validation():
    with pytest.raises(ValueError, match="Invalid budget"):
        CSObservationV07_1(
            ticket_age_hours=10.0,
            conflict_alarm=0.5,
            source_reliability=0.8,
            queue_load=0.2,
            quoted_fp=0.05,
            quoted_fn=0.05,
            observation_delay=0.1,
            deadline_hours=2.0,
            value=1.0,
            harm=3.0,
            apply_cost=0.02,
            verify_cost=0.1,
            retry_cost=0.15,
            escalation_cost=0.25,
            time_cost_per_hour=0.05,
            budget=3,  # Invalid
        )


def test_cs_op_costs_and_budget_exhaustion():
    cases = make_cs_cases_v07_1(1, seed=777, profile="iid")
    case = cases[0]

    assert OP_COSTS_CS_V07_1["verify"] == 1
    assert OP_COSTS_CS_V07_1["proceed"] == 1
    assert OP_COSTS_CS_V07_1["retry"] == 1
    assert OP_COSTS_CS_V07_1["escalate"] == 0

    # Exhaust budget B=0 on action requiring 1 op
    r = execute_cs_step_v07_1(case, action="verify", b_rem=0)
    assert r["terminal"] is True
    assert r["allowed"] is False
    assert r["reason"] == "operation_budget"
    assert r["blocked"] == 1


def test_cs_customer_friction_and_abandonment_on_clean_retry():
    # Generate clean case
    cases = make_cs_cases_v07_1(50, seed=888, profile="iid")
    clean_cases = [c for c in cases if c.latent_state == "clean"]
    assert len(clean_cases) > 0
    case = clean_cases[0]

    # Test clean retry execution
    r = execute_cs_step_v07_1(case, action="retry", b_rem=1, p_friction_base=0.99, p_abandonment=0.99)
    assert r["terminal"] is True
    # Under high friction and high abandonment, customer abandons -> completed = False
    assert r["completed"] == 0
    assert r["safe_completion"] == 0
    assert r["utility"] < 0.0


def test_cs_fraud_proceed_causes_harm():
    cases = make_cs_cases_v07_1(50, seed=999, profile="iid")
    fraud_cases = [c for c in cases if c.latent_state == "fraud"]
    assert len(fraud_cases) > 0
    case = fraud_cases[0]

    r = execute_cs_step_v07_1(case, action="proceed", b_rem=1)
    assert r["terminal"] is True
    assert r["unsafe"] == 1
    assert r["completed"] == 0
    assert r["utility"] <= -case.observation.harm


def test_cs_verification_step_non_terminal_at_b2():
    cases = make_cs_cases_v07_1(1, seed=777, profile="iid")
    case = cases[0]

    r = execute_cs_step_v07_1(case, action="verify", b_rem=2)
    assert r["terminal"] is False
    assert r["b_rem"] == 1
    assert r["evidence"] is not None
    assert isinstance(r["evidence"].flagged, bool)
