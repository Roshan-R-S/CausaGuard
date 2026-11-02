from dataclasses import replace

import numpy as np
import pytest

from causaguard.conservative import ConservativeConfig, ConservativePolicy
from causaguard.data import make_scenarios
from causaguard.domain import Intervention, Scenario
from causaguard.policy import LearnedPolicy


class ConstantTree:
    def __init__(self, value):
        self.value = value

    def predict(self, x):
        return np.full(len(x), self.value)


class Forest:
    def __init__(self, *values):
        self.estimators_ = [ConstantTree(v) for v in values]

    def predict(self, x):
        return np.mean([t.predict(x) for t in self.estimators_], axis=0)


@pytest.fixture
def evidence():
    base = LearnedPolicy()
    base.feature_min = np.zeros(7)
    base.feature_max = np.array([15, 1, 1, 100, 1, 1, 1])
    base.reward_models = {a.value: Forest(0.5, 0.5) for a in Intervention}
    base.risk_models = {a.value: Forest(0, 0) for a in Intervention}
    return base


@pytest.fixture
def clean():
    return Scenario(100, 1, 0, 0, 0, False, True, 1)


@pytest.mark.parametrize("arm", ["proceed", "retry"])
def test_candidate_needs_strict_advantage_over_verify(evidence, clean, arm):
    evidence.reward_models[arm] = Forest(0.75, 0.75)
    strict = ConservativePolicy(evidence, ConservativeConfig(reward_margin=0.25))
    assert strict.recommend(clean).action == "verify"
    accepted = ConservativePolicy(evidence, ConservativeConfig(reward_margin=0.24)).recommend(clean)
    assert accepted.action == arm
    assert not accepted.abstained


def test_threshold_checks_use_unrounded_scores(evidence, clean):
    evidence.reward_models["proceed"] = Forest(1, 1)
    evidence.risk_models["proceed"] = Forest(0.03000001, 0.03000001)
    assert ConservativePolicy(evidence).recommend(clean).action == "verify"
    evidence.risk_models["proceed"] = Forest(0.03, 0.03)
    assert ConservativePolicy(evidence).recommend(clean).action == "proceed"


@pytest.mark.parametrize("kind,values", [("reward", (0.2, 1.8)), ("risk", (0, 0.2))])
def test_disagreement_abstains_even_with_high_mean_advantage(evidence, clean, kind, values):
    evidence.reward_models["proceed"] = Forest(1, 1)
    getattr(evidence, f"{kind}_models")["proceed"] = Forest(*values)
    config = ConservativeConfig(risk_limit=1, uncertainty_multiplier=0)
    decision = ConservativePolicy(evidence, config).recommend(clean)
    assert decision.action == "verify"
    assert decision.diagnostics["candidates"]["proceed"]["uncertain"]


def test_spread_penalty_can_remove_apparent_advantage(evidence, clean):
    evidence.reward_models["proceed"] = Forest(0.5, 1.0)
    decision = ConservativePolicy(evidence).recommend(clean)
    assert decision.action == "verify"
    assert decision.diagnostics["candidates"]["proceed"]["spread_adjusted_advantage"] == 0


@pytest.mark.parametrize("failure", ["untrained", "legacy", "outside", "nan", "few_trees"])
def test_insufficient_evidence_verifies(evidence, clean, failure):
    evidence.reward_models["proceed"] = Forest(1, 1)
    if failure == "untrained":
        evidence.reward_models.clear()
    elif failure == "legacy":
        del evidence.feature_min
    elif failure == "outside":
        clean = replace(clean, data_age_hours=101)
    elif failure == "nan":
        evidence.risk_models["retry"] = Forest(float("nan"), 0)
    else:
        evidence.reward_models["proceed"] = Forest(1)
    assert ConservativePolicy(evidence).recommend(clean).action == "verify"


def test_known_risky_verification_escalates(evidence, clean):
    evidence.risk_models["verify"] = Forest(0.2, 0.2)
    assert ConservativePolicy(evidence).recommend(clean).action == "escalate"


@pytest.mark.parametrize("risk,margin", [(0, 0), (1, 0), (1, 10)])
def test_hard_authorization_survives_all_thresholds(evidence, clean, risk, margin):
    evidence.reward_models["proceed"] = Forest(100, 100)
    config = ConservativeConfig(risk_limit=risk, reward_margin=margin)
    assert ConservativePolicy(evidence, config).recommend(
        replace(clean, confirmation_present=False)).action == "escalate"
    assert ConservativePolicy(LearnedPolicy(), config).recommend(
        replace(clean, confirmation_present=False)).action == "escalate"


def test_original_compatibility_and_batch_equivalence(trained_policy):
    rows = make_scenarios(20, 808)
    expected = trained_policy.recommend_many(rows)
    conservative = ConservativePolicy(trained_policy)
    assert conservative.recommend_many(rows) == [conservative.recommend(s) for s in rows]
    assert trained_policy.recommend_many(rows) == expected
    assert conservative.recommend_many([]) == []
    assert conservative.recommend(rows[0]) == conservative.recommend(replace(rows[0], seed=987654))


@pytest.mark.parametrize("config", [
    {"risk_limit": -1}, {"risk_limit": float("nan")}, {"reward_margin": float("inf")},
    {"max_risk_std": -1}, {"uncertainty_multiplier": -1}, {"ignore_authorization": True},
])
def test_invalid_config_rejected(config):
    with pytest.raises(ValueError):
        ConservativeConfig(**config)
