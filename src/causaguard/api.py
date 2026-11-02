"""Advisory-only API. Does not execute real agent tools or financial actions."""
import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

from causaguard import __version__
from causaguard.conservative import ConservativeConfig, ConservativePolicy
from causaguard.domain import Scenario
from causaguard.guarded_agent import run_agent
from causaguard.llm import LlamaCppClient, LLMError
from causaguard.llm_commands import environment_config
from causaguard.llm_trace import inspect_trace, replay_trace
from causaguard.mock_tools import CASES, fixture
from causaguard.policy import LearnedPolicy

app = FastAPI(title="CausaGuard", version=__version__)
MODEL_PATH = Path(os.environ.get("CAUSAGUARD_MODEL", "artifacts/policy.joblib"))
_model: LearnedPolicy | None = None


class RecommendRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    amount: float = Field(ge=0, le=1_000_000)
    authorization_confidence: float = Field(ge=0, le=1)
    note_risk_score: float = Field(ge=0, le=1)
    data_age_hours: float = Field(ge=0, le=10_000)
    tool_error_rate: float = Field(ge=0, le=1)
    schema_warning: StrictBool
    confirmation_present: StrictBool
    policy: Literal["original", "conservative"] = "original"
    conservative_config: ConservativeConfig | None = None

    @model_validator(mode="after")
    def validate_policy_config(self):
        if self.conservative_config is not None and self.policy != "conservative":
            raise ValueError("conservative_config requires policy='conservative'")
        return self


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "causaguard", "mode": "advisory-only"}


@app.post("/recommend")
def recommend(payload: RecommendRequest) -> dict:
    global _model
    if _model is None:
        if not MODEL_PATH.exists():
            raise HTTPException(503, "model missing: run 'causaguard train' first")
        try:
            _model = LearnedPolicy.load(MODEL_PATH)
        except Exception as exc:
            # Only administrator-configured local artifacts are loaded. Do not leak paths/errors.
            raise HTTPException(503, "model unavailable: retrain the local model") from exc
    s = Scenario(**payload.model_dump(exclude={"policy", "conservative_config"}), seed=0)
    policy = (_model if payload.policy == "original" else
              ConservativePolicy(_model, payload.conservative_config))
    try:
        return policy.recommend(s).as_dict()
    except (RuntimeError, ValueError, KeyError, AttributeError) as exc:
        raise HTTPException(503, "model cannot produce a decision: retrain the local model") from exc


class LLMDemoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    case: Literal[*CASES] = "clean"
    seed: int = Field(default=77, ge=0, le=9999999999)
    task: str | None = Field(default=None, min_length=1, max_length=4000)
    max_rounds: int = Field(default=8, ge=1, le=16)


def _sandbox_policy():
    # Only the administrator's model path is accepted. HTTP bodies cannot supply models or ACLs.
    global _model
    if _model is None:
        try:
            _model = LearnedPolicy.load(MODEL_PATH)
        except Exception as exc:
            raise HTTPException(503, "model unavailable: train the configured local model") from exc
    return ConservativePolicy(_model)


@app.get("/llm/health")
def llm_health():
    try:
        with LlamaCppClient(environment_config()) as client:
            return client.health()
    except (LLMError, ValueError) as exc:
        raise HTTPException(503, "local llama.cpp unavailable or misconfigured") from exc


@app.post("/llm/demo")
def llm_demo(payload: LLMDemoRequest):
    policy = _sandbox_policy()
    try:
        with LlamaCppClient(environment_config()) as client:
            return run_agent(client, policy, fixture(payload.case, payload.seed),
                             task=payload.task, max_rounds=payload.max_rounds)
    except ValueError as exc:
        raise HTTPException(400, "invalid local demo configuration") from exc


@app.post("/llm/trace/inspect")
def llm_inspect(trace: dict):
    try:
        return inspect_trace(trace)
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(422, "invalid sandbox trace") from exc


@app.post("/llm/replay")
def llm_replay(trace: dict):
    policy = _sandbox_policy()
    try:
        return replay_trace(trace, policy)
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(422, "sandbox trace does not match replay") from exc
