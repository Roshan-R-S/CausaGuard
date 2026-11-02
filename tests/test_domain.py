from dataclasses import replace
from types import SimpleNamespace

import pytest

from causaguard.domain import Scenario
from causaguard.safety import authorization_block


@pytest.mark.parametrize("updates", [
    {"amount": -1}, {"data_age_hours": float("inf")}, {"tool_error_rate": float("nan")},
    {"authorization_confidence": 2}, {"note_risk_score": "0"}, {"amount": True},
    {"confirmation_present": "true"}, {"confirmation_present": 1},
    {"schema_warning": 0}, {"seed": -1}, {"seed": True},
])
def test_invalid_scenario_rejected(updates):
    with pytest.raises(ValueError):
        replace(Scenario(100, 1, 0, 0, 0, False, True, 1), **updates)


@pytest.mark.parametrize("value", [False, 1, "true", None])
def test_authorization_requires_explicit_boolean(value):
    assert authorization_block(SimpleNamespace(confirmation_present=value))


def test_authorized_scenario_passes_gate():
    assert authorization_block(Scenario(100, 1, 0, 0, 0, False, True, 1)) is None
