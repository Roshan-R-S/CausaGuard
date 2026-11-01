import pytest

from causaguard.data import make_scenarios
from causaguard.domain import Scenario
from causaguard.evaluation import evaluate
from causaguard.policy import LearnedPolicy


@pytest.fixture(scope="module")
def policy():
    return LearnedPolicy(seed=42).fit(make_scenarios(160, seed=42), n_estimators=8)


def test_hard_policy_cannot_be_overridden_by_model(policy):
    s = Scenario(100, 1, 0, 0, 0, False, False, 1)
    decision = policy.recommend(s)
    assert decision.action == "escalate"
    assert "missing explicit" in decision.rationale


def test_decision_contains_all_arms(policy):
    s = make_scenarios(1, 10)[0]
    d = policy.recommend(s)
    assert set(d.predicted_rewards) == {"proceed", "retry", "verify", "escalate"}
    assert all(0 <= risk <= 1 for risk in d.predicted_unsafe_risk.values())


def test_evaluation_produces_baselines(policy):
    report = evaluate(policy, make_scenarios(24, 99))
    assert "rules_baseline" in report
    assert "simulator_oracle_upper_bound" in report
    assert report["learned_policy"]["n"] == 24


def test_save_load_roundtrip(policy, tmp_path):
    path = tmp_path / "test.joblib"
    policy.save(path)
    s = make_scenarios(1, 500)[0]
    assert LearnedPolicy.load(path).recommend(s) == policy.recommend(s)
