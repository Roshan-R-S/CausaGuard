from dataclasses import replace

import numpy as np
import pytest

from causaguard.intervention_env import ACTIONS, FEATURES, make_cases, potential_outcomes
from causaguard.intervention_policy import ContextualPolicy, PolicySuite, design
from causaguard.intervention_study import StudyConfig


@pytest.fixture(scope="module")
def suite():
    config = StudyConfig(train_n=64, calibration_n=48, trees=3)
    cases, cal = make_cases(64, 99011), make_cases(48, 99012)
    return PolicySuite(config, 99013).fit(cases, potential_outcomes(cases), cal, potential_outcomes(cal))


def test_public_features_exclude_hidden_information_and_outcomes(suite):
    case = make_cases(1, 99014)[0]
    changed = replace(case, key="different", current_bad=not case.current_bad,
                      actual_fn=.99, draws=(0,) * 8)
    assert suite.decisions([case.observation])[0] == suite.decisions([changed.observation])[0]
    assert not {"seed", "key", "current_bad", "previous_bad", "actual_fn", "draws"} & set(FEATURES)
    assert design([case.observation]).shape[1] > design([case.observation], False).shape[1]


def test_batch_singleton_decisions_predictions_and_fingerprints_are_stable(suite):
    observations = [c.observation for c in make_cases(20, 99015)]
    batch, scores = suite.decisions(observations)
    for i, o in enumerate(observations):
        single, one_score = suite.decisions([o])
        assert all(single[p][0] == batch[p][i] for p in single)
        for kind in scores:
            for arm in ACTIONS:
                np.testing.assert_array_equal(one_score[kind][arm][0], scores[kind][arm][i])
    assert suite.identity() == suite.identity()


def test_cost_ablation_changes_utility_selection_and_risk_still_applies():
    o = make_cases(1, 99016)[0].observation
    o = replace(o, value=1, harm=3, escalation_cost=.2, budget=2)
    predictions = {"proceed": np.array([[.75, .01, .01]]),
                   "retry": np.array([[.95, .01, .5]]),
                   "verify": np.array([[1, .8, 0]]),
                   "escalate": np.array([[0, 0, .2]])}
    policy = ContextualPolicy(1, 2, .05)
    assert policy.select([o], predictions) == ["proceed"]
    assert policy.select([o], predictions, costs=False) == ["retry"]
    predictions["retry"][0, 1] = .06
    assert policy.select([o], predictions, costs=False) == ["proceed"]


def test_nonfinite_evidence_fails_closed_and_budget_limits_candidates():
    o = replace(make_cases(1, 99017)[0].observation, budget=1)
    predictions = {a: np.array([[1., 0, 0]]) for a in ACTIONS}
    predictions["proceed"][0, 0] = 0
    policy = ContextualPolicy(1, 2, .05)
    assert policy.select([o], predictions)[0] in ("proceed", "escalate")
    predictions["verify"][0, 1] = np.nan
    assert policy.select([o], predictions) == ["escalate"]


def test_calibration_is_bounded_and_models_are_separate(suite):
    obs = [c.observation for c in make_cases(20, 99018)]
    predictions = suite.contextual.predict(obs)
    for arm in ACTIONS:
        assert np.isfinite(predictions[arm]).all()
        assert ((predictions[arm][:, :2] >= 0) & (predictions[arm][:, :2] <= 1)).all()
    assert suite.contextual.fingerprint() != suite.reduced.fingerprint()
