"""Redacted recording and deterministic response playback, never LLM regeneration."""

import hashlib
import json
import re
from copy import deepcopy
from pathlib import Path

from causaguard.llm import LLMError

TRACE_VERSION = "llm-sandbox-v1"
SENSITIVE = re.compile(r"^(password|secret|api_key|access_token|authorization|email|phone|ssn|card_number)$", re.I)


def redact(value):
    """Best-effort minimization for this synthetic demo, not a general DLP guarantee."""
    if isinstance(value, dict):
        return {key: "[REDACTED]" if SENSITIVE.fullmatch(key) else redact(item)
                for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str):
        # Function arguments arrive as JSON strings. Redact sensitive keys inside them too.
        if value.lstrip().startswith("{"):
            from causaguard.llm import strict_json
            try:
                parsed = strict_json(value)
                cleaned = redact(parsed)
                if cleaned != parsed:
                    return json.dumps(cleaned, sort_keys=True)
            except ValueError:
                pass
        value = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", value)
        value = re.sub(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]+", "Bearer [REDACTED]", value)
        value = re.sub(r"(?i)\b(password|secret|api_key|access_token)\s*[:=]\s*[^\s,;\"}]+",
                       r"\1=[REDACTED]", value)
        value = re.sub(r'(?i)("(?:password|secret|api_key|access_token)"\s*:\s*")[^"\r\n]*',
                       r'\1[REDACTED]', value)
        value = re.sub(r"\b\d{3}-\d{2}-\d{4}\b|\b\d{13,19}\b", "[REDACTED_NUMBER]", value)
    return value


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def source_fingerprint():
    names = ("llm.py", "mock_tools.py", "guarded_agent.py", "llm_trace.py", "policy.py",
             "conservative.py", "safety.py", "domain.py", "data.py", "provenance.py")
    return digest({name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                   for name in names})


def request_digest(messages, tools):
    return digest({"messages": messages, "tools": tools})


def deterministic(value):
    if isinstance(value, dict):
        return {k: deterministic(v) for k, v in value.items()
                if not k.endswith("_ms") and k != "content_sha256"}
    if isinstance(value, list):
        return [deterministic(v) for v in value]
    return value


def seal(trace):
    trace["content_sha256"] = digest({k: v for k, v in trace.items() if k != "content_sha256"})
    return trace


class RecordedClient:
    def __init__(self, identity, tape, identity_error=None):
        self._identity = deepcopy(identity)
        self.tape = deepcopy(tape)
        self.index = 0
        self.identity_error = identity_error

    def identity(self):
        if self.identity_error:
            raise LLMError(self.identity_error)
        return deepcopy(self._identity)

    def complete(self, messages, tools):
        if self.index >= len(self.tape):
            raise ValueError("recording exhausted")
        row = self.tape[self.index]
        self.index += 1
        if row["request_sha256"] != request_digest(messages, tools):
            raise ValueError("recording request differs from replay")
        if "error" in row:
            raise LLMError(row["error"])
        return deepcopy(row["response"])


def inspect_trace(trace):
    if not isinstance(trace, dict) or trace.get("trace_version") != TRACE_VERSION:
        raise ValueError("unsupported trace version")
    if trace.get("content_sha256") != digest({k: v for k, v in trace.items() if k != "content_sha256"}):
        raise ValueError("trace integrity check failed")
    return {"run_id": trace["run_id"], "case": trace["fixture"]["case"],
            "model": trace["model"], "final": trace["final"], "steps": len(trace["steps"]),
            "elapsed_ms": trace["elapsed_ms"], "errors": trace["errors"]}


def replay_trace(trace, policy):
    from causaguard.guarded_agent import run_agent
    from causaguard.mock_tools import MockState
    from causaguard.provenance import policy_fingerprint

    inspect_trace(trace)
    if trace["source_fingerprint"] != source_fingerprint():
        raise ValueError("replay requires the recorded source version")
    if trace["policy_fingerprint"] != policy_fingerprint(policy):
        raise ValueError("replay requires the same policy/model configuration")
    # Public replay never admits the deliberately unsafe benchmark-only mode.
    if trace["execution_mode"] != "guarded":
        raise ValueError("only guarded traces support public replay")
    client = RecordedClient(trace["model"], trace["llm_responses"], trace.get("identity_error"))
    result = run_agent(client, policy, MockState.model_validate(trace["fixture"]),
                       task=trace["task"], max_rounds=trace["max_rounds"], run_id=trace["run_id"])
    if client.index != len(client.tape) or deterministic(result) != deterministic(trace):
        raise ValueError("trace does not match deterministic replay")
    return {"replay": "matched", "run_id": trace["run_id"], "final": result["final"],
            "llm_calls": 0, "recorded_responses": client.index}
