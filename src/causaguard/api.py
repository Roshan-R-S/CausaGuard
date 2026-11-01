"""Advisory-only API. Does not execute real agent tools or financial actions."""
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from causaguard.domain import Scenario
from causaguard.policy import LearnedPolicy

app = FastAPI(title="CausaGuard", version="0.1.0")
MODEL_PATH = Path(os.environ.get("CAUSAGUARD_MODEL", "artifacts/policy.joblib"))
_model: LearnedPolicy | None = None


class RecommendRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    amount: float = Field(ge=0, le=1_000_000)
    authorization_confidence: float = Field(ge=0, le=1)
    note_risk_score: float = Field(ge=0, le=1)
    data_age_hours: float = Field(ge=0, le=10_000)
    tool_error_rate: float = Field(ge=0, le=1)
    schema_warning: bool
    confirmation_present: bool


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "causaguard", "mode": "advisory-only"}


@app.post("/recommend")
def recommend(payload: RecommendRequest) -> dict:
    global _model
    if _model is None:
        if not MODEL_PATH.exists():
            raise HTTPException(503, "model missing: run 'causaguard train' first")
        _model = LearnedPolicy.load(MODEL_PATH)
    s = Scenario(**payload.model_dump(), seed=0)  # seed is never used by the predictor
    return _model.recommend(s).as_dict()
