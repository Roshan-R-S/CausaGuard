import json
from copy import deepcopy
from dataclasses import replace

import pytest

from causaguard.conservative import ConservativePolicy
from causaguard.policy import Decision
from causaguard.sandbox import (
    CASES,
    INJECTION,
    SandboxExecutor,
    ToolProposal,
    fixture,
    replay_trace,
    run_agent,
)


class FixedPolicy:
    def __init__(self, action):
        self.action = action

    def recommend(self, scenario):
        return Decision(self.action, {}, {}, "test recommendation", 1.0)


def proposal(tool="read_record", **arguments):
    return ToolProposal(tool=tool, arguments=arguments or {"record_id": "demo-record"})


@pytest.mark.parametrize("case", CASES)
def test_complete_verify_runs_and_json_replay(case):
    policy = FixedPolicy("verify")
    trace = json.loads(json.dumps(run_agent(policy, case)))
    assert replay_trace(trace, policy) == trace
    assert trace["final"]["completed"] == (case not in ("authorization", "prompt_injection"))
    assert all("decision" in step and "proposal" in step for step in trace["steps"])
    if trace["final"]["completed"]:
        assert len(trace["steps"]) == 2
        assert trace["final"]["ledger"] == {"demo-record": "staged-in-memory"}


@pytest.mark.parametrize("action", ["proceed", "retry", "verify", "escalate", "unknown"])
def test_executor_cannot_bypass_missing_authorization(action):
    trace = run_agent(FixedPolicy(action), "authorization")
    assert not trace["final"]["completed"]
    assert trace["final"]["tool_attempts"] == 0
    assert "hard policy" in trace["steps"][0]["enforcement"]["reason"]


def test_authoritative_gate_is_independent_of_public_confidence():
    state = replace(fixture("clean"), authoritative_authorized=False)
    result = SandboxExecutor(state).execute(proposal(), FixedPolicy("proceed").recommend(None))
    assert not result["permitted"] and not result["events"]


@pytest.mark.parametrize("tool", ["shell", "send_email", "payment", "read_record; shell", "__import__"])
def test_arbitrary_tool_dispatch_is_impossible(tool):
    executor = SandboxExecutor(fixture("clean"))
    result = executor.execute(proposal(tool), FixedPolicy("proceed").recommend(None))
    assert not result["permitted"]
    assert executor.ledger == {} and executor.attempts == 0


@pytest.mark.parametrize("arguments", [
    {"record_id": "other-record"}, {"record_id": "demo-record", "confirmation": "true"},
    {"record_id": "../../private"},
])
def test_proposal_cannot_grant_its_own_permissions(arguments):
    result = SandboxExecutor(fixture("clean")).execute(
        proposal(**arguments), FixedPolicy("verify").recommend(None))
    assert not result["permitted"] and not result["events"]


def test_prompt_injection_text_is_logged_but_never_authorizes():
    trace = run_agent(FixedPolicy("proceed"), "prompt_injection")
    assert trace["fixture"]["untrusted_note"] == INJECTION
    assert trace["steps"][0]["enforcement"]["observation"]["note"] == INJECTION
    assert not trace["steps"][1]["enforcement"]["permitted"]
    assert not trace["final"]["completed"]


def test_retry_handles_timeout_without_sleep_or_unbounded_attempts():
    trace = run_agent(FixedPolicy("retry"), "timeout")
    assert trace["final"]["completed"]
    events = trace["steps"][0]["enforcement"]["events"]
    assert [e["status"] for e in events] == ["timeout", "ok"]
    assert trace["final"]["tool_attempts"] == 3


@pytest.mark.parametrize("case", ["schema_failure", "timeout", "stale_data"])
def test_proceed_does_not_silently_repair_faults(case):
    trace = run_agent(FixedPolicy("proceed"), case)
    assert not trace["final"]["completed"]
    assert trace["final"]["verified"] is False


def test_invalid_intervention_and_out_of_order_update_are_denied():
    executor = SandboxExecutor(fixture("clean"))
    assert not executor.execute(proposal(), FixedPolicy("bad").recommend(None))["permitted"]
    assert not executor.execute(proposal("stage_update"), FixedPolicy("proceed").recommend(None))[
        "permitted"]


def test_verification_can_repair_stale_state_after_a_read():
    executor = SandboxExecutor(fixture("stale_data"))
    executor.execute(proposal(), FixedPolicy("proceed").recommend(None))
    result = executor.execute(proposal("stage_update"), FixedPolicy("verify").recommend(None))
    assert result["permitted"] and executor.ledger


@pytest.mark.parametrize("target", ["decision", "enforcement", "fixture", "final"])
def test_tampered_trace_cannot_replay(target):
    policy = FixedPolicy("verify")
    trace = deepcopy(run_agent(policy))
    if target in ("decision", "enforcement"):
        trace["steps"][0][target] = {}
    else:
        trace[target] = {}
    with pytest.raises(ValueError, match="replay"):
        replay_trace(trace, policy)


def test_real_policies_replay_and_wrong_policy_is_rejected(trained_policy):
    conservative = ConservativePolicy(trained_policy)
    for policy in (trained_policy, conservative):
        for case in CASES:
            trace = json.loads(json.dumps(run_agent(policy, case)))
            assert replay_trace(trace, policy) == trace
    with pytest.raises(ValueError, match="same model"):
        replay_trace(run_agent(conservative), trained_policy)
    with pytest.raises(ValueError):
        run_agent(conservative, "unknown")
