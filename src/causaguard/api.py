"""Advisory-only API. Does not execute real agent tools or financial actions."""
import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

from causaguard import __version__
from causaguard.conservative import ConservativeConfig, ConservativePolicy
from causaguard.domain import Scenario
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
