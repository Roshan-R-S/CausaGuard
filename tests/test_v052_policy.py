from dataclasses import replace

import numpy as np
import pytest
from pydantic import ValidationError

from causaguard.factorial_policy import FactorialContextualModel
from causaguard.intervention_env import ACTIONS, EnvironmentConfig, make_cases, outcome
from causaguard.v052.config import StudyConfig
from causaguard.v052.policy import BASELINES, CANDIDATES, PolicySuite, select_original


def small_config(**changes):
    values = {
        "training_seeds": (52900001, 52900002, 52900003),
        "calibration_seeds": (52900004, 52900005, 52900006),
        "model_seeds": (52900010, 52900020, 52900030),
        "development_seeds": (52900040, 52900041, 52900042),
        "final_seeds": (52900050, 52900051, 52900052),
        "bootstrap_seed": 52900060,
        "train_n": 32,
        "calibration_n": 32,
        "cases_per_seed": 8,
        "trees": 2,
        "bootstrap_replicates": 50,
    }
    return StudyConfig(**(values | changes))


@pytest.mark.parametrize("change", [
    {"risk_limit": .10}, {"utility_margin": .01}, {"absolute_risk_limit": .10},
    {"excess_risk_limit": .02}, {"family_alpha": .10}, {"trees": True},
    {"bootstrap_seed": True}, {"training_seeds": (True, 52900002, 52900003)},
    {"training_seeds": (52900001, 52900001, 52900003)},
    {"calibration_seeds": (52900001, 52900005, 52900006)},
    {"development_seeds": (52900013, 52900041, 52900042)},
    {"model_seeds": (52900010, 52900013, 52900030)},
    {"model_seeds": (2**32 - 3, 52900020, 52900030)},
    {"final_seeds": (52900050, 52900051)}, {"training_seeds": ()},
])
def test_locked_configuration_rejects_threshold_changes_and_seed_overlap(change):
    with pytest.raises(ValueError):
        small_config(**change)


def test_configuration_frozen_and_json_round_trip():
    config = small_config()
    assert StudyConfig.model_validate_json(config.model_dump_json()) == config
    with pytest.raises(ValidationError):
        config.risk_limit = .10
    with pytest.raises(ValidationError):
        StudyConfig()


def observation():
    return replace(make_cases(1, 52900070, EnvironmentConfig(denial_rate=0))[0].observation,
                   budget=2, escalation_cost=.3, value=1.5, harm=2)


@pytest.mark.parametrize("risk, expected", [(.05, "proceed"), (.050001, "escalate")])
def test_both_learned_selectors_use_unrounded_inclusive_five_percent_gate(risk, expected):
    obs = [observation()]
    predictions = {arm: np.array([[1., .6, 0.]]) for arm in ACTIONS}
    predictions["proceed"][0, 1] = risk
    model = FactorialContextualModel(52900010, 2)
    assert model.select(obs, predictions, .05) == [expected]
    rewards = {arm: np.array([1.]) for arm in ACTIONS}
    risks = {arm: np.array([.6]) for arm in ACTIONS}
    risks["proceed"][0] = risk
    assert select_original(obs, rewards, risks) == [expected]


@pytest.mark.parametrize("nonfinite", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_predictions_fail_closed(nonfinite):
    obs = [observation()]
    predictions = {arm: np.array([[1., 0., 0.]]) for arm in ACTIONS}
    predictions["proceed"][0, 0] = nonfinite
    assert FactorialContextualModel(52900010, 2).select(obs, predictions, .05) == ["escalate"]
    rewards = {arm: np.array([1.]) for arm in ACTIONS}
    risks = {arm: np.array([0.]) for arm in ACTIONS}
    rewards["proceed"][0] = nonfinite
    assert select_original(obs, rewards, risks) == ["escalate"]


def test_original_wrapper_enforces_budget_and_known_escalation_cost():
    obs = [replace(observation(), budget=1)]
    rewards = {arm: np.array([100.]) for arm in ACTIONS}
    rewards["proceed"][0] = -1.
    risks = {arm: np.array([0.]) for arm in ACTIONS}
    assert select_original(obs, rewards, risks) == ["escalate"]


@pytest.mark.parametrize("permission", ["authorized", "confirmation_present", "read_permitted"])
def test_favorable_model_predictions_cannot_override_permission_denial(permission):
    case = make_cases(1, 52900071, EnvironmentConfig(denial_rate=0))[0]
    case = replace(case, state=case.state.model_copy(update={permission: False}),
                   observation=observation())
    rewards = {arm: np.array([10. if arm == "proceed" else 1.]) for arm in ACTIONS}
    risks = {arm: np.array([0.]) for arm in ACTIONS}
    action = select_original([case.observation], rewards, risks)[0]
    assert action == "proceed"
    result = outcome(case, action)
    assert result["blocked"] == 1
    assert result["attempts"] == result["completed"] == result["authorization_violation"] == 0


def test_suite_shares_contextual_fit_and_final_evaluates_only_selected_candidate(monkeypatch):
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.isotonic import IsotonicRegression

    from causaguard.intervention_env import potential_outcomes

    fit_counts = {"forest": 0, "isotonic": 0}
    forest_fit, isotonic_fit = RandomForestRegressor.fit, IsotonicRegression.fit

    def fit_forest(self, *args, **kwargs):
        fit_counts["forest"] += 1
        return forest_fit(self, *args, **kwargs)

    def fit_isotonic(self, *args, **kwargs):
        fit_counts["isotonic"] += 1
        return isotonic_fit(self, *args, **kwargs)

    monkeypatch.setattr(RandomForestRegressor, "fit", fit_forest)
    monkeypatch.setattr(IsotonicRegression, "fit", fit_isotonic)
    config = small_config()
    train = make_cases(32, config.training_seeds[0])
    calibration = make_cases(32, config.calibration_seeds[0])
    suite = PolicySuite(config, config.model_seeds[0]).fit(
        train, potential_outcomes(train), calibration, potential_outcomes(calibration)
    )
    assert set(suite.identity()) == {"original_r05", "contextual_16"}
    assert fit_counts == {"forest": 12, "isotonic": 8}
    assert len(suite.contextual.models) == 4
    assert len(suite.base.reward_models) + len(suite.base.risk_models) == 8
    obs = [replace(observation(), alarm=.6, budget=1)]
    development = suite.decisions(obs)
    assert tuple(development) == CANDIDATES + BASELINES
    assert development["rules_repair"] == development["always_verify"] == ["verify"]
    for candidate in CANDIDATES:
        final = suite.decisions(obs, selected=candidate)
        assert tuple(final) == (candidate,) + BASELINES
        assert final[candidate] == development[candidate]
    with pytest.raises(ValueError):
        suite.decisions(obs, selected="f16_raw_r10")
