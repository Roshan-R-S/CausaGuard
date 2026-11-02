import json

import httpx
import pytest

from causaguard.llm import (
    LlamaCppClient,
    LLMConfig,
    LLMError,
    normalize_message,
    strict_json,
    validate_sequence,
)

MESSAGES = [{"role": "system", "content": "Mock only"}, {"role": "user", "content": "Look up"}]


def call(identity="call_1", name="lookup_customer", arguments='{"customer_id":"mock-customer-77"}'):
    return {"id": identity, "type": "function", "function": {"name": name, "arguments": arguments}}


def assistant(*calls, content=None):
    return {"role": "assistant", "content": content, "tool_calls": list(calls)}


def test_model_resolution_and_roundtrip_ids():
    requests = []

    def handler(request):
        requests.append(request)
        if request.method == "GET":
            return httpx.Response(200, json={"data": [{"id": "qwen-local"}]})
        body = json.loads(request.content)
        assert body["model"] == "qwen-local" and body["max_tokens"] == 99
        assert body["stream"] is False and body["parallel_tool_calls"] is False
        if len(body["messages"]) == 2:
            message, finish = assistant(call()), "tool_calls"
        else:
            assert body["messages"][-1]["tool_call_id"] == "call_1"
            message, finish = assistant(content="Done"), "stop"
        return httpx.Response(200, json={"choices": [{"message": message, "finish_reason": finish}]})

    with LlamaCppClient(LLMConfig(max_tokens=99), transport=httpx.MockTransport(handler)) as client:
        message = client.complete(MESSAGES, [])
        messages = MESSAGES + [message, {"role": "tool", "tool_call_id": "call_1", "content": "{}"}]
        assert client.complete(messages, [])["content"] == "Done"
        assert len(requests) == 3  # model discovery is cached


@pytest.mark.parametrize("url", ["https://api.openai.com/v1", "http://example.com/v1",
                                     "http://127.0.0.1:8080/else", "http://user:pass@localhost/v1",
                                     "http://localhost/v1?key=secret", "http://localhost:bad/v1",
                                     "http://localhost:99999/v1"])
def test_local_only_configuration(url):
    with pytest.raises(ValueError):
        LLMConfig(base_url=url)


@pytest.mark.parametrize("options", [{"max_tokens": 0}, {"max_tokens": True},
                                         {"timeout_seconds": 0}, {"temperature": float("nan")}])
def test_config_limits(options):
    with pytest.raises(ValueError):
        LLMConfig(**options)


@pytest.mark.parametrize("data,classification", [
    ({"data": []}, "invalid_models"), ({"data": [{}]}, "invalid_models"),
    ({"data": [{"id": "a"}, {"id": "b"}]}, "ambiguous_model"),
])
def test_bad_model_discovery(data, classification):
    with LlamaCppClient(transport=httpx.MockTransport(lambda _: httpx.Response(200, json=data))) as c:
        with pytest.raises(LLMError, match=classification):
            c.identity()


def test_configured_model_health_mismatch():
    with LlamaCppClient(LLMConfig(model="missing"), transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={"status": "ok"} if request.url.path == "/health"
                                           else {"data": [{"id": "present"}]}))) as c:
        with pytest.raises(LLMError, match="model_not_found"):
            c.health()


def test_health_checks_server_and_models():
    paths = []
    def handler(request):
        paths.append(request.url.path)
        return httpx.Response(200, json={"status": "ok"} if request.url.path == "/health" else
                              {"data": [{"id": "qwen"}]})
    with LlamaCppClient(transport=httpx.MockTransport(handler)) as c:
        assert c.health()["model"] == "qwen"
        assert paths[:2] == ["/health", "/v1/models"]


@pytest.mark.parametrize("error,classification", [(httpx.ConnectError, "llm_connection_error"),
                                                     (httpx.ReadTimeout, "llm_timeout")])
def test_transport_errors_are_sanitized(error, classification):
    def handler(request):
        raise error("secret transport details", request=request)
    with LlamaCppClient(transport=httpx.MockTransport(handler)) as c:
        with pytest.raises(LLMError) as exc:
            c.health()
        assert str(exc.value) == classification


@pytest.mark.parametrize("status,body,classification", [
    (500, "secret", "llm_http_error"), (302, "redirect", "llm_http_error"),
    (200, "not json", "invalid_response"), (200, "[]", "invalid_response"),
    (200, "x" * 65537, "invalid_response"),
])
def test_http_failures(status, body, classification):
    with LlamaCppClient(transport=httpx.MockTransport(lambda _: httpx.Response(status, text=body))) as c:
        with pytest.raises(LLMError, match=classification):
            c.health()


@pytest.mark.parametrize("message", [
    {}, {"role": "user", "content": "a"}, assistant(), assistant(call(), call()),
    assistant({"id": "a", "type": "function", "function": {"name": "x", "arguments": {}}}),
    assistant(call(identity="bad id")), assistant(call(name="shell.exe")),
    {"role": "assistant", "content": [], "tool_calls": []},
    {"role": "assistant", "content": None, "tool_calls": [None]},
])
def test_invalid_envelopes_fail_atomically(message):
    with pytest.raises(LLMError):
        normalize_message(message)


@pytest.mark.parametrize("finish,message,classification", [
    ("length", assistant(call()), "truncated_response"),
    ("tool_calls", assistant(content="No tool"), "missing_tool_calls"),
    ("content_filter", assistant(content="no"), "invalid_finish_reason"),
])
def test_finish_reason(finish, message, classification):
    payload = {"choices": [{"message": message, "finish_reason": finish}]}
    with LlamaCppClient(LLMConfig(model="qwen"), transport=httpx.MockTransport(
            lambda _: httpx.Response(200, json=payload))) as c:
        with pytest.raises(LLMError, match=classification):
            c.complete(MESSAGES, [])


@pytest.mark.parametrize("suffix", [
    [assistant(call())],
    [{"role": "tool", "tool_call_id": "orphan", "content": "{}"}],
    [assistant(call()), {"role": "user", "content": "interrupt"}],
    [assistant(call()), {"role": "tool", "tool_call_id": "wrong", "content": "{}"}],
    [assistant(call()), {"role": "tool", "tool_call_id": "call_1", "content": "{}"}, assistant(call())],
])
def test_sequencing_rejects_orphans_pending_and_reused_ids(suffix):
    with pytest.raises(LLMError):
        validate_sequence(MESSAGES + suffix)


@pytest.mark.parametrize("raw", ['{"a":1,"a":2}', '{"a":NaN}', '{"x":Infinity}', "{", "[" * 2000])
def test_strict_json_rejects_ambiguous_input(raw):
    with pytest.raises(ValueError):
        strict_json(raw)
