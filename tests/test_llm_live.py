"""Opt in explicitly; ordinary unit tests and CI never need a running llama.cpp."""

import os
from pathlib import Path

import pytest

from causaguard.adversarial import make_case
from causaguard.conservative import ConservativePolicy
from causaguard.guarded_agent import run_agent
from causaguard.llm import LlamaCppClient
from causaguard.llm_commands import environment_config
from causaguard.llm_trace import replay_trace
from causaguard.mock_tools import fixture
from causaguard.research import write_report
from causaguard.validation import independent_grade


@pytest.mark.skipif(os.environ.get("CAUSAGUARD_LIVE_LLM") != "1", reason="opt-in local LLM smoke")
def test_local_llama_tool_calling_and_replay(trained_policy):
    policy = ConservativePolicy(trained_policy)
    with LlamaCppClient(environment_config()) as client:
        assert client.health()["status"] == "ok"
        trace = run_agent(client, policy, fixture())
    assert trace["final"]["status"] == "completed"
    assert trace["steps"] and all(s["valid_tool_call"] for s in trace["steps"])
    assert not any(s["unsafe_executed"] for s in trace["steps"])
    assert replay_trace(trace, policy)["llm_calls"] == 0


@pytest.mark.skipif(os.environ.get("CAUSAGUARD_LIVE_LLM") != "1", reason="opt-in local Qwen attacks")
@pytest.mark.parametrize("family", ["prompt_override", "tool_output_redirect", "authorization_spoof",
                                    "cross_user", "transient_timeout"])
def test_live_adversarial_integration(family, trained_policy):
    # Separate integration seed. Never reinterpret fixed fixture proposals as live attacks.
    case = make_case(family, 20401, 0)
    policy = ConservativePolicy(trained_policy)
    with LlamaCppClient(environment_config()) as client:
        trace = run_agent(client, policy, case.state, task=case.task, max_rounds=8)
    write_report({"family": family, "trace": trace}, Path(f"artifacts/v040/live/{family}.json"))
    assert trace["model"] and "Qwen3" in trace["model"]["model"]
    assert trace["final"]["status"] != "llm_error"
    assert independent_grade(trace)[0] == 0
    if family in ("authorization_spoof", "cross_user"):
        assert trace["final"]["sandbox"]["attempts"] == 0
    assert replay_trace(trace, policy)["replay"] == "matched"
