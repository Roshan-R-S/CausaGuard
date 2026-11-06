import json

import numpy as np
import pytest

from causaguard.cli import main
from causaguard.factorial_policy import (
    FACTORIAL_POLICIES,
    FACTORIAL_VARIANTS,
    FactorialPolicySuite,
)
from causaguard.factorial_study import (
    FactorialStudyConfig,
    compute_factorial_contrasts,
    replay_report,
    run_study,
)
from causaguard.intervention_env import PROFILES, make_cases, potential_outcomes


@pytest.fixture(scope="module")
def small_reports():
    config = FactorialStudyConfig(
        train_n=32,
        calibration_n=32,
        trees=2,
        leaf_size=4,
        cases_per_seed=8,
        training_seeds=(79001, 79002, 79003),
        calibration_seeds=(79101, 79102, 79103),
        model_seeds=(79201, 79202, 79203),
        development_seeds=(79301, 79302, 79303),
        final_seeds=(79401, 79402, 79403),
        bootstrap_replicates=50,
        bootstrap_seed=79501,
    )
    dev = run_study(config=config)
    final = run_study(development=dev)
    return config, dev, final


def test_factorial_policy_suite():
    config = FactorialStudyConfig(
        train_n=32,
        calibration_n=32,
        trees=2,
        cases_per_seed=8,
        training_seeds=(79001, 79002, 79003),
        calibration_seeds=(79101, 79102, 79103),
        model_seeds=(79201, 79202, 79203),
        development_seeds=(79301, 79302, 79303),
        final_seeds=(79401, 79402, 79403),
        bootstrap_replicates=50,
    )
    cases = make_cases(32, 79001)
    cal = make_cases(32, 79101)
    suite = FactorialPolicySuite(config, 79201).fit(
        cases, potential_outcomes(cases), cal, potential_outcomes(cal)
    )
    ident = suite.identity()
    assert "contextual_16" in ident and "contextual_7" in ident and "original" in ident

    obs = [c.observation for c in cases[:10]]
    decisions, scores = suite.decisions(obs)
    for variant in FACTORIAL_VARIANTS:
        assert len(decisions[variant]) == 10
    assert "always_verify" in decisions
    assert "rules_repair" in decisions
    assert "cost_rule" in decisions
    assert "original" in decisions
    assert set(scores) == {"f16_raw", "f16_cal", "f7_raw", "f7_cal"}


def test_factorial_config_rejects_invalid_seeds():
    with pytest.raises(ValueError):
        FactorialStudyConfig(training_seeds=(70001, 70001, 70003))
    with pytest.raises(ValueError):
        FactorialStudyConfig(cases_per_seed=1)


def test_compute_factorial_contrasts():
    cells = {
        p: np.ones((3, 3, 2)) * (i + 1)
        for i, p in enumerate(FACTORIAL_VARIANTS)
    }
    contrasts = compute_factorial_contrasts(cells)
    assert "feature_main_effect" in contrasts
    assert "calibration_main_effect" in contrasts
    assert "risk_main_effect" in contrasts
    assert "interaction_feature_x_calibration" in contrasts
    assert "interaction_feature_x_risk" in contrasts
    assert "interaction_calibration_x_risk" in contrasts
    assert "interaction_feature_x_calibration_x_risk" in contrasts
    for name, arr in contrasts.items():
        assert arr.shape == (3, 3, 2)


def test_factorial_study_runs_and_replays(small_reports):
    _, dev, final = small_reports
    result = replay_report(json.loads(json.dumps(final)), json.loads(json.dumps(dev)))
    assert result["replay"] == "matched"
    assert dev["training"] == final["training"]
    for profile in PROFILES:
        res = final["results"][profile]
        assert len(res["policies"]) == len(FACTORIAL_POLICIES)
        for p in FACTORIAL_POLICIES:
            assert res["policies"][p]["metrics"]["authorization_violation"]["estimate"] == 0
    # Check primary test in IID profile
    primary = final["results"]["iid"]["primary"]
    assert primary is not None
    assert primary["conditions_count"] == 17
    assert "feature_main_effect_utility" in primary["checks"]
    for v in FACTORIAL_VARIANTS:
        assert f"absolute_risk_{v}" in primary["checks"]
        assert f"excess_risk_vs_always_verify_{v}" in primary["checks"]


def test_factorial_cli(tmp_path):
    out = tmp_path / "dev.json"
    with pytest.raises(SystemExit):
        main(["factorial-study", "--phase", "development", "--config", "nonexistent.json", "--output", str(out)])
