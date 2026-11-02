"""Public pre-decision signals and deterministic experiment records."""
from dataclasses import dataclass
from enum import Enum
from math import isfinite


class Intervention(str, Enum):
    PROCEED = "proceed"
    RETRY = "retry"
    VERIFY = "verify"
    ESCALATE = "escalate"


@dataclass(frozen=True)
class Scenario:
    # Signals visible before the simulated consequential action.
    amount: float
    authorization_confidence: float
    note_risk_score: float
    data_age_hours: float
    tool_error_rate: float
    schema_warning: bool
    confirmation_present: bool
    seed: int  # strictly for simulation; NEVER an ML input

    def __post_init__(self) -> None:
        limits = {
            "amount": 1_000_000,
            "authorization_confidence": 1,
            "note_risk_score": 1,
            "data_age_hours": 10_000,
            "tool_error_rate": 1,
        }
        for name, upper in limits.items():
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{name} must be numeric")
            if not isfinite(value) or not 0 <= value <= upper:
                raise ValueError(f"{name} must be finite and between 0 and {upper}")
        for name in ("schema_warning", "confirmation_present"):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"{name} must be a boolean")
        if type(self.seed) is not int or self.seed < 0:
            raise ValueError("seed must be a nonnegative integer")


@dataclass(frozen=True)
class Outcome:
    completed: bool
    unsafe: bool
    deferred: bool
    reward: float
    reason: str
