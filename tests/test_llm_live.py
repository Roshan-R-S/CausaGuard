"""Opt in explicitly; ordinary unit tests and CI never need a running llama.cpp."""

import os

import pytest

from causaguard.conservative import ConservativePolicy
from causaguard.guarded_agent import run_agent
from causaguard.llm import LlamaCppClient
from causaguard.llm_commands import environment_config
from causaguard.llm_trace import replay_trace
from causaguard.mock_tools import fixture


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
