from types import SimpleNamespace

import numpy as np
import pytest

from causaguard.calibration import audit_risk
from causaguard.domain import Scenario


class ConstantRiskModel:
    def __init__(self, probability):
        self.probability = probability

    def predict(self, x):
        return np.full(len(x), self.probability)


def make_policy(probability):
    model = ConstantRiskModel(probability)
    return SimpleNamespace(
        risk_models={
            "proceed": model,
            "retry": model,
        }
    )


def make_scenario(confirmed=True):
    return Scenario(
        amount=100,
        authorization_confidence=1.0,
        note_risk_score=0.0,
        data_age_hours=0.0,
        tool_error_rate=0.0,
        schema_warning=False,
        confirmation_present=confirmed,
        seed=1,
    )


def test_safe_outcomes_have_expected_brier_score():
    scenarios = [make_scenario()] * 20
    result = audit_risk(make_policy(0.2), scenarios)

    for action in ("proceed", "retry"):
        metrics = result["actions"][action]
        assert metrics["observed_unsafe_rate"] == 0.0
        assert metrics["brier_score"] == pytest.approx(0.04)
        assert metrics["expected_calibration_error"] == pytest.approx(0.2)


def test_unsafe_outcomes_are_detected():
    scenarios = [make_scenario(confirmed=False)] * 20
    result = audit_risk(make_policy(0.2), scenarios)

    for action in ("proceed", "retry"):
        metrics = result["actions"][action]
        assert metrics["observed_unsafe_rate"] == 1.0
        assert metrics["brier_score"] == pytest.approx(0.64)


def test_reproducibility_and_invalid_inputs():
    scenarios = [make_scenario()] * 10
    policy = make_policy(0.25)

    first = audit_risk(policy, scenarios)
    second = audit_risk(policy, scenarios)

    assert first == second

    with pytest.raises(ValueError):
        audit_risk(policy, [])

    with pytest.raises(ValueError):
        audit_risk(policy, scenarios, bins=1)
