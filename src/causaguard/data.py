"""Synthetic, reproducible scenarios. No real-world safety claims."""
import random

import numpy as np

from causaguard.domain import Intervention, Scenario
from causaguard.simulator import simulate

FEATURE_NAMES = (
    "log_amount", "authorization_confidence", "note_risk_score", "data_age_hours",
    "tool_error_rate", "schema_warning", "confirmation_present",
)


def make_scenarios(count: int, seed: int = 42) -> list[Scenario]:
    if count < 1:
        raise ValueError("count must be positive")
    rng = random.Random(seed)
    scenarios = []
    # Vary regimes to avoid a one-variable, trivially separable toy.
    for _ in range(count):
        regime = rng.randrange(4)
        amount = round(10 ** rng.uniform(1, 3.25), 2)
        authorization = min(1.0, max(0.0, rng.betavariate(16 if regime == 0 else (2 if regime == 2 else 6), 1.2 if regime == 0 else 2)))
        note_risk = min(1.0, max(0.0, rng.betavariate(0.6 if regime == 0 else (4 if regime == 1 else 1.4), 20 if regime == 0 else 5)))
        age = rng.uniform(0, 6 if regime == 0 else 100)
        tool_error = rng.uniform(0.005, 0.08 if regime == 0 else 0.85)
        schema_warning = rng.random() < (0.01 if regime == 0 else 0.32)
        confirmation = rng.random() > (0.01 if regime == 0 else 0.14)
        scenarios.append(Scenario(
            amount, authorization, note_risk, age, tool_error,
            schema_warning, confirmation, rng.randrange(1, 2**62),
        ))
    return scenarios


def features(s: Scenario) -> np.ndarray:
    # Excludes simulator seed, hidden ground truth, and any outcome data.
    return np.asarray([
        np.log1p(s.amount), s.authorization_confidence, s.note_risk_score,
        s.data_age_hours, s.tool_error_rate, float(s.schema_warning),
        float(s.confirmation_present),
    ], dtype=float)


def matrices(scenarios: list[Scenario]) -> tuple[np.ndarray, dict[str, np.ndarray], dict[str, np.ndarray]]:
    x = np.stack([features(s) for s in scenarios])
    rewards = {}
    risks = {}
    for action in Intervention:
        outcomes = [simulate(s, action) for s in scenarios]
        rewards[action.value] = np.asarray([o.reward for o in outcomes], dtype=float)
        risks[action.value] = np.asarray([float(o.unsafe) for o in outcomes], dtype=float)
    return x, rewards, risks
