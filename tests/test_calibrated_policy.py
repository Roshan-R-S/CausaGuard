import numpy as np
import pytest

from causaguard.data import make_scenarios
from causaguard.domain import Intervention, Scenario
from causaguard.policy import LearnedPolicy
from experiments.compare_calibrated_policy import (
    calibrated_actions,
    run_experiment,
)


class IdentityCalibrator:
    def predict(self, values):
        return np.asarray(values)


@pytest.fixture(scope="module")
def policy():
    return LearnedPolicy(seed=42).fit(
        make_scenarios(160, seed=42),
        n_estimators=8,
    )


def test_missing_confirmation_always_escalates(policy):
    scenario = Scenario(
        amount=100,
        authorization_confidence=1,
        note_risk_score=0,
        data_age_hours=0,
        tool_error_rate=0,
        schema_warning=False,
        confirmation_present=False,
        seed=999,
    )

    calibrators = {
        "proceed": IdentityCalibrator(),
        "retry": IdentityCalibrator(),
    }

    result = calibrated_actions(policy, calibrators, [scenario])
    assert result == [Intervention.ESCALATE]


def test_identity_calibration_preserves_decisions(policy):
    scenarios = make_scenarios(30, seed=9090)
    calibrators = {
        "proceed": IdentityCalibrator(),
        "retry": IdentityCalibrator(),
    }

    expected = [
        Intervention(d.action)
        for d in policy.recommend_many(scenarios)
    ]
    actual = calibrated_actions(policy, calibrators, scenarios)

    assert actual == expected


def test_empty_evaluation_is_rejected(policy):
    with pytest.raises(ValueError):
        run_experiment(policy, {}, [])
