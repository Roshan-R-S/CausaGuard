"""Bounded, loopback-only llama.cpp chat client. No SDK, credentials, or tool execution."""

import json
import math
import re
from time import monotonic
from typing import Protocol
from urllib.parse import urlsplit

import httpx
from pydantic import BaseModel, ConfigDict, Field, field_validator


class LLMError(RuntimeError):
    """Stable error classes; never expose server bodies, prompts, or transport details."""

    def __init__(self, classification: str):
        self.classification = classification
        super().__init__(classification)


class LLMConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)
    base_url: str = "http://127.0.0.1:8080/v1"
    model: str | None = Field(default=None, min_length=1, max_length=512)
    timeout_seconds: float = Field(default=60, gt=0, le=300)
    max_tokens: int = Field(default=768, strict=True, ge=32, le=8192)
    temperature: float = Field(default=0, ge=0, le=2)
    seed: int = Field(default=42, strict=True, ge=0)

    @field_validator("base_url")
    @classmethod
    def local_url(cls, value):
        parsed = urlsplit(value)
        # Accessing port validates malformed/out-of-range ports before an HTTP request.
        parsed.port
        if (parsed.scheme != "http" or parsed.hostname not in ("127.0.0.1", "::1", "localhost")
                or parsed.username or parsed.password or parsed.query or parsed.fragment
                or parsed.path.rstrip("/") != "/v1"):
            raise ValueError("base_url must be a loopback http URL ending in /v1")
        return value.rstrip("/")


def strict_json(value: str, *, max_bytes=65536):
    def pairs(items):
        result = {}
        for key, item in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = item
        return result

    def constant(_):
        raise ValueError("nonfinite JSON number")

    if not isinstance(value, str) or len(value.encode("utf-8")) > max_bytes:
        raise ValueError("JSON exceeds size limit")
    try:
        result = json.loads(value, object_pairs_hook=pairs, parse_constant=constant)
        pending, nodes = [(result, 0)], 0
        while pending:
            item, depth = pending.pop()
            nodes += 1
            if depth > 32 or nodes > 8192:
                raise ValueError("JSON exceeds structural limit")
            if isinstance(item, float) and not math.isfinite(item):
                raise ValueError("nonfinite JSON number")
            if isinstance(item, dict):
                pending.extend((child, depth + 1) for child in item.values())
            elif isinstance(item, list):
                pending.extend((child, depth + 1) for child in item)
        return result
    except (RecursionError, OverflowError) as exc:
        raise ValueError("invalid JSON nesting") from exc


def normalize_message(message: dict) -> dict:
    """Validate the entire assistant envelope before allowing any member of a batch."""
    if not isinstance(message, dict) or message.get("role") != "assistant":
        raise LLMError("invalid_response")
    content = message.get("content")
    if content is not None and (not isinstance(content, str) or len(content) > 32768):
        raise LLMError("invalid_response")
    calls = message.get("tool_calls", [])
    if calls is None:
        calls = []
    if not isinstance(calls, list) or len(calls) > 8:
        raise LLMError("invalid_tool_calls")
    normalized, seen = [], set()
    for call in calls:
        if not isinstance(call, dict):
            raise LLMError("invalid_tool_calls")
        identity, function = call.get("id"), call.get("function")
        if (call.get("type") != "function" or not isinstance(identity, str)
                or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", identity) or identity in seen
                or not isinstance(function, dict)):
            raise LLMError("invalid_tool_calls")
        name, arguments = function.get("name"), function.get("arguments")
        if (not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_]{1,100}", name)
                or not isinstance(arguments, str) or len(arguments) > 8192):
            raise LLMError("invalid_tool_calls")
        seen.add(identity)
        normalized.append({"id": identity, "type": "function",
                           "function": {"name": name, "arguments": arguments}})
    if not calls and (not content or not content.strip()):
        raise LLMError("empty_response")
    result = {"role": "assistant", "content": content}
    if normalized:
        result["tool_calls"] = normalized
    return result


def validate_sequence(messages: list[dict]) -> None:
    pending, used = set(), set()
    if not messages or messages[0].get("role") != "system":
        raise LLMError("invalid_message_sequence")
    for message in messages:
        role = message.get("role")
        if role == "tool":
            identity = message.get("tool_call_id")
            if identity not in pending:
                raise LLMError("invalid_message_sequence")
            pending.remove(identity)
        elif pending:
            raise LLMError("invalid_message_sequence")
        elif role == "assistant":
            for call in normalize_message(message).get("tool_calls", []):
                if call["id"] in used:
                    raise LLMError("invalid_message_sequence")
                pending.add(call["id"])
                used.add(call["id"])
        elif role not in ("system", "user"):
            raise LLMError("invalid_message_sequence")
    if pending:
        raise LLMError("invalid_message_sequence")


class ChatClient(Protocol):
    def identity(self) -> dict: ...
    def complete(self, messages: list[dict], tools: list[dict]) -> dict: ...


class LlamaCppClient:
    def __init__(self, config: LLMConfig | None = None, *, transport=None):
        self.config = config or LLMConfig()
        self._model = self.config.model
        self._http = httpx.Client(timeout=self.config.timeout_seconds, transport=transport,
                                  trust_env=False, follow_redirects=False,
                                  headers={"Accept-Encoding": "identity"})

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def close(self):
        self._http.close()

    def _request(self, method, path, *, at_root=False, **kwargs):
        try:
            base = self.config.base_url[:-3] if at_root else self.config.base_url
            started, chunks, size = monotonic(), [], 0
            # Bound decoded bytes while streaming, including compressed responses.
            # The deadline is cooperative between reads; each read also has an httpx timeout.
            with self._http.stream(method, base + path, **kwargs) as response:
                response.raise_for_status()
                if response.headers.get("content-encoding", "identity").lower() != "identity":
                    raise LLMError("invalid_response")
                for chunk in response.iter_bytes(chunk_size=4096):
                    size += len(chunk)
                    if size > 65536:
                        raise LLMError("invalid_response")
                    if monotonic() - started > self.config.timeout_seconds:
                        raise LLMError("llm_timeout")
                    chunks.append(chunk)
        except httpx.TimeoutException as exc:
            raise LLMError("llm_timeout") from exc
        except httpx.HTTPStatusError as exc:
            raise LLMError("llm_http_error") from exc
        except httpx.RequestError as exc:
            raise LLMError("llm_connection_error") from exc
        try:
            value = strict_json(b"".join(chunks).decode("utf-8"))
        except (ValueError, UnicodeError) as exc:
            raise LLMError("invalid_response") from exc
        if not isinstance(value, dict):
            raise LLMError("invalid_response")
        return value

    def models(self) -> list[str]:
        data = self._request("GET", "/models").get("data")
        if (not isinstance(data, list) or not data or any(
                not isinstance(row, dict) or not isinstance(row.get("id"), str)
                or not row["id"] or len(row["id"]) > 512 for row in data)):
            raise LLMError("invalid_models")
        return [row["id"] for row in data]

    def identity(self):
        if self._model is None:
            models = self.models()
            if len(models) != 1:
                raise LLMError("ambiguous_model")
            self._model = models[0]
        return {"runtime": "llama.cpp", "model": self._model,
                "config": self.config.model_dump()}

    def health(self):
        if self._request("GET", "/health", at_root=True).get("status") != "ok":
            raise LLMError("invalid_health")
        models = self.models()
        if self.config.model and self.config.model not in models:
            raise LLMError("model_not_found")
        return {"status": "ok", "models": models, **self.identity()}

    def complete(self, messages, tools):
        validate_sequence(messages)
        body = {"model": self.identity()["model"], "messages": messages, "tools": tools,
                "tool_choice": "auto", "parallel_tool_calls": False,
                "max_tokens": self.config.max_tokens, "temperature": self.config.temperature,
                "seed": self.config.seed, "stream": False}
        response = self._request("POST", "/chat/completions", json=body)
        choices = response.get("choices")
        if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
            raise LLMError("invalid_response")
        finish = choices[0].get("finish_reason")
        if finish == "length":
            raise LLMError("truncated_response")
        if finish not in ("stop", "tool_calls"):
            raise LLMError("invalid_finish_reason")
        message = normalize_message(choices[0].get("message"))
        if finish == "tool_calls" and not message.get("tool_calls"):
            raise LLMError("missing_tool_calls")
        return message
