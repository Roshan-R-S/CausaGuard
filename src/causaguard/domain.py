"""Public pre-decision signals and deterministic experiment records."""
from dataclasses import dataclass
from enum import Enum


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


@dataclass(frozen=True)
class Outcome:
    completed: bool
    unsafe: bool
    deferred: bool
    reward: float
    reason: str
