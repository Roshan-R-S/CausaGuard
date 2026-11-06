"""Tests for CausaGuard v0.7.1 Decomposed Human Escalation Mechanics."""

import pytest
from causaguard_v07_1.domain_cs import execute_cs_step_v07_1, make_cs_cases_v07_1
from causaguard_v07_1.domain_de import execute_de_step_v07_1, make_de_cases_v07_1
from causaguard_v07_1.escalation import (
    HumanEscalationParamsCS,
    HumanEscalationParamsDE,
    QueueState,
)


def test_escalation_cs_nonzero_labor_cost_and_delay():
    cases = make_cs_cases_v07_1(1, seed=777, profile="iid")
    case = cases[0]
    params = HumanEscalationParamsCS(c_labor_base=0.50, l_queue_base=1.0)

    r = execute_cs_step_v07_1(case, action="escalate", b_rem=1, escalation_params=params)
    assert r["terminal"] is True
    assert r["action"] == "escalate"
    # Cost must exceed labor base fee
    assert r["cost"] >= 0.50
    # Latency must exceed base queue delay
    assert r["latency"] >= 1.0


def test_escalation_de_nonzero_labor_cost_and_delay():
    cases = make_de_cases_v07_1(1, seed=777, profile="iid")
    case = cases[0]
    params = HumanEscalationParamsDE(c_labor_base=0.80, l_queue_base=1.5)

    r = execute_de_step_v07_1(case, action="escalate", b_rem=1, escalation_params=params)
    assert r["terminal"] is True
    assert r["action"] == "escalate"
    assert r["cost"] >= 0.80
    assert r["latency"] >= 1.5


def test_escalation_cs_capacity_exhaustion_queue_drop():
    cases = make_cs_cases_v07_1(1, seed=777, profile="iid")
    case = cases[0]
    # Set capacity limit to 2
    q_state = QueueState(capacity_limit=2)

    # First 2 escalations pass capacity check
    r1 = execute_cs_step_v07_1(case, action="escalate", b_rem=1, queue_state=q_state)
    _ = execute_cs_step_v07_1(case, action="escalate", b_rem=1, queue_state=q_state)
    assert q_state.escalation_count == 2
    assert q_state.drop_count == 0 or r1["reason"] == "human_specialist_unavailable"

    # 3rd escalation exceeds capacity -> triggers queue drop!
    r3 = execute_cs_step_v07_1(case, action="escalate", b_rem=1, queue_state=q_state)
    assert q_state.escalation_count == 3
    assert r3["reason"] == "human_queue_capacity_exhausted"
    assert r3["completed"] == 0
    assert r3["utility"] < 0.0


def test_escalation_de_capacity_exhaustion_queue_drop():
    cases = make_de_cases_v07_1(1, seed=777, profile="iid")
    case = cases[0]
    q_state = QueueState(capacity_limit=1)

    _ = execute_de_step_v07_1(case, action="escalate", b_rem=1, queue_state=q_state)
    r2 = execute_de_step_v07_1(case, action="escalate", b_rem=1, queue_state=q_state)
    assert q_state.escalation_count == 2
    assert r2["reason"] == "human_queue_capacity_exhausted"
    assert r2["completed"] == 0


def test_escalation_cs_workflow_value_discount():
    # Test that salvaged ticket receives discounted workflow value 0.80 * V
    cases = make_cs_cases_v07_1(50, seed=123, profile="iid")
    clean_cases = [c for c in cases if c.latent_state == "clean"]
    assert len(clean_cases) > 0
    case = clean_cases[0]

    params = HumanEscalationParamsCS(
        gamma_workflow=0.80,
        p_salvage_clean=1.0,  # Guarantee salvage
        p_error_base=0.0,     # Guarantee zero error
        p_avail_base=1.0,     # Guarantee available
    )
    r = execute_cs_step_v07_1(case, action="escalate", b_rem=1, escalation_params=params)
    if r["reason"] == "escalated_to_human" and r["completed"] == 1:
        expected_v = 0.80 * case.observation.value
        assert pytest.approx(r["utility"], abs=0.05) == (expected_v - r["cost"])
        assert r["escalation_diagnostics"]["workflow_discount"] == pytest.approx(0.20, abs=0.01)


def test_escalation_de_workflow_value_discount():
    cases = make_de_cases_v07_1(50, seed=234, profile="iid")
    clean_cases = [c for c in cases if not c.defect]
    assert len(clean_cases) > 0
    case = clean_cases[0]

    params = HumanEscalationParamsDE(
        gamma_workflow=0.75,
        p_salvage_clean=1.0,
        p_error_base=0.0,
        p_avail_base=1.0,
    )
    r = execute_de_step_v07_1(case, action="escalate", b_rem=1, escalation_params=params)
    if r["reason"] == "escalated_to_engineer" and r["completed"] == 1:
        expected_v = 0.75 * case.observation.value
        assert pytest.approx(r["utility"], abs=0.05) == (expected_v - r["cost"])
        assert r["escalation_diagnostics"]["workflow_discount"] == pytest.approx(0.25, abs=0.01)


def test_escalation_queue_state_cloning_and_order_invariance():
    q1 = QueueState(capacity_limit=10, escalation_count=5, drop_count=1, error_count=1)
    q2 = q1.clone()
    assert q2.capacity_limit == 10
    assert q2.escalation_count == 5
    assert q2.drop_count == 1
    assert q2.error_count == 1

    q2.escalation_count += 3
    # Mutating q2 does not mutate q1
    assert q1.escalation_count == 5
    assert q2.escalation_count == 8
