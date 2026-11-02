from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from causaguard import research
from causaguard.conservative import ConservativeConfig
from causaguard.data import make_scenarios
from causaguard.domain import Intervention
from causaguard.research import (
    METRICS,
    ExperimentConfig,
    assert_disjoint,
    compare_policies,
    outcome_values,
    paired_intervals,
    run_development,
    run_final,
    shifted_scenarios,
)
from causaguard.simulator import COST, simulate


@pytest.fixture(scope="module")
def config():
    return ExperimentConfig(train_n=64, n_estimators=4, n_per_seed=8,
                            development_seeds=(101, 102), final_seeds=(201, 202),
                            bootstrap_replicates=20, sensitivity_risk_limits=(0.01, 0.1),
                            sensitivity_reward_margins=(0.05,))


@pytest.fixture(scope="module")
def development(config):
    return run_development(config)


def test_development_never_opens_final_data(config, monkeypatch):
    original = research.make_split
    opened = []

    def monitored(cfg, split, profile="iid"):
        opened.append(split)
        assert split == "development"
        return original(cfg, split, profile)

    monkeypatch.setattr(research, "make_split", monitored)
    report = run_development(config)
    assert opened and len(report["sensitivity"]) == 2
    assert report["config"]["conservative"] == config.conservative.model_dump()


def test_final_is_reproducible_and_contains_no_tuning(development):
    first = run_final(development)
    assert first == run_final(development)
    assert "sensitivity" not in first
    assert first["model_fingerprint"] == development["model_fingerprint"]
    assert first["results"]["iid"]["datasets"] != development["results"]["iid"]["datasets"]
    assert set(first["results"]) == set(research.PROFILES)


@pytest.mark.parametrize("field", ["config_sha256", "source_sha256", "environment", "model_fingerprint"])
def test_final_rejects_changed_protocol_before_opening_final(development, monkeypatch, field):
    corrupted = deepcopy(development)
    corrupted[field] = "changed"
    original = research.make_split

    def monitored(cfg, split, profile="iid"):
        assert split != "final"
        return original(cfg, split, profile)

    monkeypatch.setattr(research, "make_split", monitored)
    with pytest.raises(ValueError):
        run_final(corrupted)


@pytest.mark.parametrize("updates", [
    {"development_seeds": (1,)}, {"final_seeds": (7101, 2)}, {"train_seed": 7101},
    {"final_seeds": (1, 1)}, {"final_seeds": (-1, 2)}, {"n_per_seed": 0},
    {"bootstrap_replicates": 0}, {"sensitivity_risk_limits": (float("nan"),)},
    {"sensitivity_reward_margins": ()}, {"profiles": ("unknown",)},
])
def test_bad_protocol_rejected(updates):
    with pytest.raises(ValueError):
        ExperimentConfig(**updates)


def test_disjointness_checks_latent_seeds_not_just_features():
    rows = make_scenarios(2, 888)
    with pytest.raises(ValueError, match="latent"):
        assert_disjoint(rows, [replace(rows[0], amount=150)])
    with pytest.raises(ValueError):
        assert_disjoint([rows[0], rows[0]])


def test_paired_intervals_have_correct_mean_and_exact_zero_gap():
    values = np.zeros((4, len(METRICS)))
    values[:, 0] = [1, 2, -1, 2]
    result = paired_intervals(values, [10, 10, 20, 20], 100, 42)
    assert result["mean_reward"]["difference"] == 1
    assert result["unsafe_rate"] == {"difference": 0, "ci95": [0, 0]}
    assert result == paired_intervals(values, [10, 10, 20, 20], 100, 42)
    # Identical paired measurements must produce zero uncertainty in their differences.
    assert all(v["ci95"] == [0, 0] for v in paired_intervals(
        values - values, [10, 10, 20, 20], 100, 42).values())


def test_metrics_match_manual_gated_baseline(trained_policy):
    rows = make_scenarios(20, 980)
    report = compare_policies(trained_policy, ConservativeConfig(), {980: rows}, 30, 1)
    actions = [Intervention.VERIFY if s.confirmation_present else Intervention.ESCALATE for s in rows]
    outcomes = [simulate(s, a) for s, a in zip(rows, actions, strict=True)]
    summary = report["policies"]["always_verify"]
    assert summary["mean_reward"] == pytest.approx(np.mean([o.reward for o in outcomes]))
    assert summary["defer_rate"] == pytest.approx(np.mean([o.deferred for o in outcomes]))
    assert summary["mean_intervention_cost"] == pytest.approx(np.mean([COST[a] for a in actions]))
    assert sum(summary["action_counts"].values()) == len(rows)
    gap = report["paired"]["conservative_minus_always_verify"]["mean_reward"]
    assert gap["difference"] == pytest.approx(
        report["policies"]["conservative"]["mean_reward"] - summary["mean_reward"])


def test_evaluator_rejects_policy_authorization_bypass(monkeypatch, trained_policy):
    rows = [replace(make_scenarios(1, 98)[0], confirmation_present=False)]
    monkeypatch.setattr(trained_policy, "recommend_many",
                        lambda rows: [SimpleNamespace(action="proceed") for _ in rows])
    with pytest.raises(ValueError, match="authorization"):
        compare_policies(trained_policy, ConservativeConfig(), {98: rows}, 10, 1)


def test_shift_profiles_are_deterministic_and_retain_latent_pairing():
    iid = shifted_scenarios(10, 61)
    stale = shifted_scenarios(10, 61, "stale_data")
    failures = shifted_scenarios(10, 61, "tool_failures")
    injection = shifted_scenarios(10, 61, "prompt_injection")
    assert stale == shifted_scenarios(10, 61, "stale_data")
    assert [s.seed for s in iid] == [s.seed for s in stale]
    assert all(s.data_age_hours >= 120 for s in stale)
    assert all(s.schema_warning and s.tool_error_rate >= 0.8 for s in failures)
    assert all(s.note_risk_score >= 0.8 for s in injection)
    with pytest.raises(ValueError):
        shifted_scenarios(10, 61, "bad")


def test_empty_and_misaligned_evaluations_fail(trained_policy):
    with pytest.raises(ValueError):
        compare_policies(trained_policy, ConservativeConfig(), {}, 10, 1)
    with pytest.raises(ValueError):
        outcome_values(make_scenarios(1), [])
    with pytest.raises(ValueError):
        paired_intervals(np.zeros((1, len(METRICS))), [], 10, 1)
