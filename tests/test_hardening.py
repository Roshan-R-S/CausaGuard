import asyncio
import json
from copy import deepcopy

import httpx
import pytest
from fastapi.testclient import TestClient

from causaguard.adversarial import FAMILIES, AttackClient, make_case
from causaguard.api import app
from causaguard.guarded_agent import run_agent
from causaguard.llm import LlamaCppClient, LLMError, strict_json
from causaguard.llm_benchmark import FixedPolicy, FixtureClient
from causaguard.llm_trace import redact, replay_trace
from causaguard.mock_tools import MockSandbox, fixture, validate_arguments
from causaguard.request_limits import RequestLimits
from causaguard.validation import independent_grade


@pytest.mark.parametrize("raw", [None, {}, '{"n":1e999}', '[' * 34 + '0' + ']' * 34,
                                     '[0' + ',0' * 8192 + ']', '"' + '\u2603' * 22000 + '"'])
def test_json_limits_cover_bytes_structure_and_overflow(raw):
    with pytest.raises(ValueError):
        strict_json(raw)


@pytest.mark.parametrize("raw", ['{"customer_id":true}', '{"customer_id":"x","authorized":true}',
                                     '{"customer_id":"x","customer_id":"y"}', 'null', '{}',
                                     '{"customer_id":"' + 'a' * 101 + '"}', 'x' * 8193])
def test_argument_boundary_rejects_ambiguous_or_spoofed_inputs(raw):
    with pytest.raises(ValueError):
        validate_arguments("lookup_customer", raw)


@pytest.mark.parametrize("action", ["proceed", "retry", "verify"])
@pytest.mark.parametrize("family", FAMILIES)
def test_adversarial_corpus_cannot_override_hard_rules(family, action):
    case = make_case(family, 20001, 0)  # unit-only seed; never a final measurement
    trace = run_agent(AttackClient(case), FixedPolicy(action), case.state, task=case.task, max_rounds=16)
    assert independent_grade(trace)[0] == 0
    assert trace["final"]["sandbox"]["attempts"] <= 32
    if family in ("persistent_timeout", "retry_storm"):
        assert trace["final"]["sandbox"]["fetch_attempts"] == 2
        assert not trace["final"]["task_completed"]
    assert replay_trace(trace, FixedPolicy(action))["replay"] == "matched"


def test_trusted_state_revalidates_unsafe_pydantic_copy():
    with pytest.raises(ValueError):
        MockSandbox(fixture().model_copy(update={"authorized": "true"}))


def test_authorization_rechecked_after_policy_and_before_each_retry(monkeypatch):
    original = MockSandbox.execute

    def revoke(self, name, args, **kwargs):
        if name == "fetch_mock_transaction":
            self.state = self.state.model_copy(update={"read_permitted": False})
        return original(self, name, args, **kwargs)

    monkeypatch.setattr(MockSandbox, "execute", revoke)
    trace = run_agent(FixtureClient(fixture("timeout")), FixedPolicy("retry"), fixture("timeout"))
    assert trace["steps"][2]["authorization_outcome"]["allowed"]
    assert trace["steps"][2]["result"]["error"] == "authorization_denied"
    assert not trace["final"]["sandbox"]["fetched"]


def test_oracle_detects_disabled_executor_authorization(monkeypatch):
    # A broken enforcement helper must not silently make the evaluation look safe.
    monkeypatch.setattr(MockSandbox, "violations", lambda *_: [])
    state = fixture("authorization")
    trace = run_agent(FixtureClient(state), FixedPolicy("proceed"), state, _benchmark_unguarded=True)
    with pytest.raises(ValueError, match="oracle disagrees"):
        independent_grade(trace)


def test_redaction_covers_nested_arrays_headers_and_keys():
    raw = {"note": '[{"refresh_token":"top-secret"}]',
           "text": "Cookie: sid=private-cookie\nBasic cHJpdmF0ZQ==",
           "key": "-----BEGIN PRIVATE KEY-----\nprivate-material\n-----END PRIVATE KEY-----",
           "nested": {"API-Key": "private-api", "Set-Cookie": "private-session"}}
    cleaned = redact(raw)
    assert redact(cleaned) == cleaned
    assert all(secret not in json.dumps(cleaned) for secret in
               ("top-secret", "private-cookie", "cHJpdmF0ZQ", "private-material", "private-api", "private-session"))


def test_tool_output_redacted_before_recording_and_next_turn(monkeypatch):
    original = MockSandbox.execute

    def secret(self, name, args, **kwargs):
        result = original(self, name, args, **kwargs)
        if result["status"] == "ok":
            result["output"]["refresh_token"] = "secret-fixture-canary"
        return result

    monkeypatch.setattr(MockSandbox, "execute", secret)

    class InspectClient(FixtureClient):
        def complete(self, messages, tools):
            assert "secret-fixture-canary" not in json.dumps(messages)
            return super().complete(messages, tools)

    state = fixture()
    trace = run_agent(InspectClient(state), FixedPolicy("proceed"), state)
    assert "secret-fixture-canary" not in json.dumps(trace)


def test_unexpected_client_error_is_sanitized_and_replayable():
    class Broken(FixtureClient):
        def complete(self, messages, tools):
            raise RuntimeError("private-client-canary")

    trace = run_agent(Broken(fixture()), FixedPolicy("proceed"), fixture())
    assert trace["errors"][-1]["classification"] == "client_error"
    assert "private-client-canary" not in json.dumps(trace)
    assert replay_trace(trace, FixedPolicy("proceed"))["replay"] == "matched"


def test_http_body_stops_reading_at_size_limit_and_closes_stream():
    class Endless(httpx.SyncByteStream):
        consumed, closed = 0, False

        def __iter__(self):
            for _ in range(100):
                self.consumed += 1
                yield b"x" * 4096

        def close(self):
            self.closed = True

    stream = Endless()
    with LlamaCppClient(transport=httpx.MockTransport(
            lambda _: httpx.Response(200, stream=stream))) as client:
        with pytest.raises(LLMError, match="invalid_response"):
            client.health()
    assert stream.consumed == 17 and stream.closed


def test_compressed_response_is_rejected_before_decompression():
    with LlamaCppClient(transport=httpx.MockTransport(lambda _: httpx.Response(
            200, headers={"Content-Encoding": "gzip"}, stream=httpx.ByteStream(b"not-gzip")))) as client:
        with pytest.raises(LLMError, match="invalid_response"):
            client.health()


def test_api_limits_body_before_json_parsing():
    response = TestClient(app).post("/llm/trace/inspect", content=b"x" * 1_048_577)
    assert response.status_code == 413


@pytest.mark.parametrize("body", [b"[" * 2000, b'{"case":"clean","case":"authorization"}',
                                      b'{"seed":1e999}', b"\xff"])
def test_api_rejects_excessive_or_ambiguous_json_without_echo(body):
    response = TestClient(app).post("/llm/demo", content=body)
    assert response.status_code == 422
    assert response.json() == {"detail": "invalid or excessive JSON structure"}


def test_nonfinite_policy_result_is_blocked_without_invalid_trace():
    from causaguard.policy import Decision

    class CorruptPolicy:
        def recommend(self, scenario):
            return Decision("proceed", {"proceed": float("nan")}, {}, "bad", 0)

    trace = run_agent(FixtureClient(fixture()), CorruptPolicy(), fixture())
    assert trace["final"]["sandbox"]["attempts"] == 0
    assert trace["steps"][0]["result"]["error"] == "policy_error"
    assert all(s["result"]["status"] == "blocked" for s in trace["steps"])
    json.dumps(trace, allow_nan=False)


def test_chunked_body_limit_and_capacity_are_released():
    async def check():
        reached, sent = [], []

        async def application(scope, receive, send):
            reached.append(True)

        boundary = RequestLimits(application, max_body=5, max_active=1)
        scope = {"type": "http", "method": "POST", "path": "/llm/demo"}
        queue = iter([{"type": "http.request", "body": b"1234", "more_body": True},
                      {"type": "http.request", "body": b"56", "more_body": False}])

        async def receive():
            return next(queue)

        async def send(message):
            sent.append(message)

        await boundary(scope, receive, send)
        assert not reached and sent[0]["status"] == 413 and boundary.active == 0
        boundary.active = 1
        sent.clear()
        await boundary(scope, receive, send)
        assert sent[0]["status"] == 429 and boundary.active == 1
    asyncio.run(check())


def test_conversation_budget_is_fail_closed():
    class Verbose(FixtureClient):
        def complete(self, messages, tools):
            response = super().complete(messages, tools)
            response["content"] = "a" * 32768
            return response

    trace = run_agent(Verbose(fixture()), FixedPolicy("proceed"), fixture())
    assert trace["errors"][-1]["classification"] == "conversation_limit"
    assert replay_trace(trace, FixedPolicy("proceed"))["replay"] == "matched"


def test_execution_budget_applies_even_to_unchecked_benchmark():
    sandbox = MockSandbox(fixture())
    for _ in range(32):
        assert sandbox.execute("lookup_customer", {"customer_id": "mock-customer-77"}, guarded=False)["status"] == "ok"
    assert sandbox.execute("lookup_customer", {"customer_id": "mock-customer-77"}, guarded=False)["error"] == "execution_limit"


def test_repeated_resource_retry_budget_cannot_reset_with_new_ids():
    case = make_case("retry_storm", 20001, 0)
    trace = run_agent(AttackClient(case), FixedPolicy("retry"), case.state, max_rounds=16)
    assert trace["final"]["sandbox"]["fetch_attempts"] == 2
    assert any(e["classification"] == "retry_budget_exhausted" for e in trace["errors"])
    changed = deepcopy(trace)
    changed["steps"][0]["unsafe_executed"] = True
    with pytest.raises(ValueError, match="oracle"):
        independent_grade(changed)
