from causaguard.domain import Intervention, Scenario
from causaguard.simulator import simulate


def scenario(**kwargs):
    data = dict(
        amount=100, authorization_confidence=1, note_risk_score=0,
        data_age_hours=0, tool_error_rate=0, schema_warning=False,
        confirmation_present=True, seed=1,
    )
    data.update(kwargs)
    return Scenario(**data)


def test_clean_run():
    assert simulate(scenario(), Intervention.PROCEED).completed


def test_explicitly_unconfirmed_cannot_proceed_safely():
    assert simulate(scenario(confirmation_present=False), Intervention.PROCEED).unsafe
    o = simulate(scenario(confirmation_present=False), Intervention.ESCALATE)
    assert o.deferred and not o.unsafe


def test_verify_holds_risky_action():
    s = scenario(note_risk_score=1, seed=3)
    assert simulate(s, Intervention.PROCEED).unsafe
    assert not simulate(s, Intervention.VERIFY).unsafe


def test_replay_is_deterministic():
    s = scenario(data_age_hours=60, tool_error_rate=0.4)
    assert simulate(s, Intervention.VERIFY) == simulate(s, Intervention.VERIFY)
