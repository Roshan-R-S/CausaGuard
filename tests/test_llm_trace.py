import json
from copy import deepcopy

import pytest

from causaguard.guarded_agent import run_agent
from causaguard.llm_benchmark import FixedPolicy, FixtureClient
from causaguard.llm_trace import RecordedClient, inspect_trace, redact, replay_trace, seal
from causaguard.mock_tools import fixture


def test_redaction_is_recursive_and_idempotent():
    raw = {"email": "person@example.com", "note": "Contact someone@example.com Bearer abc.def",
           "nested": [{"password": "secret-value"}],
           "arguments": '{"customer_id":"a","api_key":"private-key"}'}
    cleaned = redact(raw)
    assert "person@" not in json.dumps(cleaned)
    assert "someone@" not in json.dumps(cleaned)
    assert "abc.def" not in json.dumps(cleaned)
    assert "private-key" not in json.dumps(cleaned)
    assert "secret-value" not in json.dumps(cleaned)
    assert redact(cleaned) == cleaned


def test_redacted_task_replays_without_original_secret():
    policy, state = FixedPolicy("verify"), fixture()
    trace = run_agent(FixtureClient(state), policy, state,
                      task="Look up the mock record. email person@example.com password=not-for-logs")
    assert "person@" not in json.dumps(trace) and "not-for-logs" not in json.dumps(trace)
    assert replay_trace(trace, policy)["replay"] == "matched"


@pytest.mark.parametrize("mutation", ["outcome", "fixture", "tape", "request", "extra", "source"])
def test_replay_rejects_tampering_even_with_recomputed_checksum(mutation):
    policy, state = FixedPolicy("verify"), fixture()
    trace = run_agent(FixtureClient(state), policy, state)
    trace = deepcopy(trace)
    if mutation == "outcome":
        trace["final"]["task_completed"] = False
    elif mutation == "fixture":
        trace["fixture"]["authorized"] = False
    elif mutation == "tape":
        trace["llm_responses"].pop()
    elif mutation == "request":
        trace["llm_responses"][0]["request_sha256"] = "changed"
    elif mutation == "extra":
        trace["llm_responses"].append(trace["llm_responses"][-1])
    else:
        trace["source_fingerprint"] = "changed"
    seal(trace)
    with pytest.raises(ValueError):
        replay_trace(trace, policy)


def test_policy_changes_and_unguarded_replay_are_rejected():
    state = fixture()
    trace = run_agent(FixtureClient(state), FixedPolicy("verify"), state)
    with pytest.raises(ValueError, match="same policy"):
        replay_trace(trace, FixedPolicy("retry"))
    trace = run_agent(FixtureClient(state), FixedPolicy("proceed"), state, _benchmark_unguarded=True)
    with pytest.raises(ValueError, match="only guarded"):
        replay_trace(trace, FixedPolicy("proceed"))


def test_inspection_checks_integrity_and_version():
    state = fixture()
    trace = run_agent(FixtureClient(state), FixedPolicy("verify"), state)
    assert inspect_trace(trace)["steps"] == 4
    trace["final"]["status"] = "tampered"
    with pytest.raises(ValueError, match="integrity"):
        inspect_trace(trace)
    with pytest.raises(ValueError, match="version"):
        inspect_trace({})


def test_recording_exhaustion_is_explicit():
    with pytest.raises(ValueError, match="exhausted"):
        RecordedClient({}, []).complete([], [])
