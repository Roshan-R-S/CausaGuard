from dataclasses import replace

import pytest

from causaguard.intervention_env import (
    ACTIONS,
    EnvironmentConfig,
    access,
    grade_access,
    make_cases,
    outcome,
    potential_outcomes,
)


def clean_case():
    case = make_cases(1, 99001, EnvironmentConfig(denial_rate=0))[0]
    return replace(case, observation=replace(case.observation, deadline=10, budget=2),
                   previous_bad=False, current_bad=False, draws=(.99,) * 8, outage=0)


def test_generator_reproducibility_variation_and_independent_seeds():
    a, b = make_cases(100, 99002), make_cases(100, 99003)
    assert [c.record() for c in a] == [c.record() for c in make_cases(100, 99002)]
    assert {c.key for c in a}.isdisjoint(c.key for c in b)
    assert len({c.observation for c in a}) == 100
    assert len({c.current_bad for c in a}) == 2
    assert len({c.observation.domain for c in a}) == 2
    assert any(c.previous_bad != c.current_bad for c in a)


@pytest.mark.parametrize("action", ACTIONS)
@pytest.mark.parametrize("denial", ["confirmation_present", "authorized", "read_permitted", "owner_id"])
def test_independent_permission_denials_override_every_selector(action, denial):
    case = clean_case()
    state = case.state.model_copy(update={denial: "mock-user-88" if denial == "owner_id" else False})
    result = outcome(replace(case, state=state), action)
    assert not result["completed"] and not result["unsafe"]
    assert result["attempts"] == 0
    assert result["blocked"] == (action != "escalate")


@pytest.mark.parametrize("raw", ['{"customer_id":"mock-customer-88"}',
                                 '{"customer_id":"mock-customer-77","authorized":true}',
                                 '{"customer_id":"x","customer_id":"mock-customer-77"}',
                                 '{"customer_id":77}', 'not json'])
def test_scope_and_schema_cannot_be_repaired_by_operational_verification(raw):
    result = outcome(replace(clean_case(), raw_arguments=raw), "verify")
    assert result["blocked"] and not result["verified"] and result["attempts"] == 0


@pytest.mark.parametrize("action", ["retry", "verify"])
def test_revocation_rechecked_before_second_access(action):
    case = clean_case()
    case = replace(case, state=case.state.model_copy(update={"revoke_after_attempts": 1}))
    result = outcome(case, action)
    assert result["guard"]["reason"] == "authorization_revoked"
    assert result["attempts"] == 1 and result["cost"] == .01
    assert not result["completed"] and not result["verified"]
    assert outcome(case, "proceed")["completed"]


def test_budget_is_equal_for_all_two_operation_macros():
    case = clean_case()
    case = replace(case, observation=replace(case.observation, budget=1))
    for action in ("retry", "verify"):
        assert outcome(case, action)["guard"]["reason"] == "operation_budget"
    assert outcome(case, "proceed")["completed"]


def test_false_negative_can_cause_unsafe_completion_without_authorization_violation():
    case = replace(clean_case(), previous_bad=True, current_bad=True, actual_fn=1)
    result = outcome(case, "verify")
    assert result["false_negative"] and result["unsafe"] and result["completed"]
    assert result["authorization_violation"] == 0
    assert result["utility"] < 0


def test_false_positive_cost_and_failed_repair_can_prevent_valid_completion():
    case = replace(clean_case(), actual_fp=1)
    result = outcome(case, "verify")
    assert result["false_positive"] and not result["unsafe"] and not result["completed"]
    assert outcome(case, "proceed")["completed"]


def test_delayed_observation_misses_new_defect_even_perfect_old_record_verifier():
    case = replace(clean_case(), previous_bad=False, current_bad=True, actual_fp=0, actual_fn=0)
    result = outcome(case, "verify")
    assert result["false_negative"] and result["unsafe"]


def test_retry_can_restore_availability_and_quality_with_distinct_cost():
    case = replace(clean_case(), current_bad=True, outage=.8, draws=(0, .99, 0, .5, 0, 0, 0, 0))
    result = outcome(case, "retry")
    assert result["safe_completion"] and not outcome(case, "proceed")["completed"]
    assert result["cost"] > outcome(case, "proceed")["cost"]


def test_deadline_and_escalation_have_no_invented_success():
    case = clean_case()
    case = replace(case, observation=replace(case.observation, deadline=.2))
    assert outcome(case, "verify")["late"] and not outcome(case, "verify")["completed"]
    result = outcome(case, "escalate")
    assert result["utility"] == -case.observation.escalation_cost
    assert result["completed"] == result["attempts"] == 0


def test_action_order_does_not_change_random_tape_or_outcome():
    case = clean_case()
    expected = potential_outcomes([case])[0]
    assert {a: outcome(case, a) for a in reversed(ACTIONS)} == expected
    with pytest.raises(ValueError, match="unknown"):
        access(case, "shell")


@pytest.mark.parametrize("kwargs", [{"seed": True}, {"seed": -1}, {"n": 0}, {"profile": "unknown"}])
def test_generator_rejects_invalid_requests(kwargs):
    with pytest.raises(ValueError):
        make_cases(**{"n": 1, "seed": 99004, **kwargs})


def test_nonfinite_signals_and_invalid_configuration_rejected():
    with pytest.raises(ValueError):
        replace(clean_case().observation, alarm=float("nan"))
    with pytest.raises(ValueError):
        EnvironmentConfig(verifier_shift=float("inf"))


def test_independent_grader_detects_forged_safe_flags_on_denied_execution():
    case = clean_case()
    case = replace(case, state=case.state.model_copy(update={"authorized": False}))
    with pytest.raises(ValueError, match="independent access grader"):
        grade_access(case, "proceed", {"allowed": False, "attempts": 1, "events": [
            {"status": "ok", "unsafe_executed": False}]})


def test_grader_rejects_success_claim_without_required_accesses():
    with pytest.raises(ValueError, match="execution accounting"):
        grade_access(clean_case(), "verify", {"allowed": True, "attempts": 0, "events": []})
