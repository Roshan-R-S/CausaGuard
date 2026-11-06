import json
from copy import deepcopy

import numpy as np
import pytest

from causaguard.cli import main
from causaguard.intervention_env import PROFILES
from causaguard.intervention_study import (
    METRICS,
    StudyConfig,
    calibration_metrics,
    crossed_interval,
    paired_cells,
    replay_report,
    run_study,
    seal,
    write_new,
)


@pytest.fixture(scope="module")
def reports():
    config = StudyConfig(train_n=32, calibration_n=32, trees=2, cases_per_seed=8,
                         development_seeds=(99301, 99302, 99303),
                         final_seeds=(99401, 99402, 99403), bootstrap_replicates=50)
    dev = run_study(config=config)
    final = run_study(development=dev)
    return config, dev, final


@pytest.mark.parametrize("change", [{"final_seeds": (50001, 50402, 50403)},
                                    {"calibration_seeds": (50001, 50102, 50103)},
                                    {"model_seeds": (50201, 50201, 50203)},
                                    {"training_seeds": (50001, 50002)},
                                    {"training_seeds": (True, 50002, 50003)},
                                    {"cases_per_seed": 1}, {"risk_limit": float("nan")}])
def test_protocol_rejects_leakage_and_invalid_budgets(change):
    with pytest.raises(ValueError):
        StudyConfig(**change)


def test_final_replay_retrains_models_recomputes_every_outcome_and_aggregate(reports):
    _, dev, final = reports
    # Exercise the actual on-disk JSON shape, not only in-memory Python objects.
    result = replay_report(json.loads(json.dumps(final)), json.loads(json.dumps(dev)))
    assert result["replay"] == "matched" and result["policy_case_runs"] == 3168
    assert dev["training"] == final["training"]
    for profile in PROFILES:
        dev_keys = {c["key"] for c in dev["results"][profile]["cases"]}
        assert dev_keys.isdisjoint(c["key"] for c in final["results"][profile]["cases"])
        for p in final["results"][profile]["policies"].values():
            assert p["metrics"]["authorization_violation"]["estimate"] == 0
            assert p["metrics"]["regret"]["estimate"] >= -1e-12


def test_source_or_protocol_drift_rejected_before_data_access(reports, monkeypatch):
    _, dev, _ = reports
    changed = deepcopy(dev)
    changed["identity"]["source"]["intervention_env.py"] = "changed"
    def forbidden(*args, **kwargs):
        pytest.fail("opened data before validating freeze")
    monkeypatch.setattr("causaguard.intervention_study.make_cases", forbidden)
    with pytest.raises(ValueError, match="source/environment"):
        run_study(development=seal(changed))


def test_training_drift_rejected_before_generating_final_cases(reports, monkeypatch):
    config, dev, _ = reports
    changed = deepcopy(dev)
    changed["training"][0]["models"]["contextual"] = "wrong"
    from causaguard.intervention_env import make_cases
    def track(n, seed, *args):
        assert seed not in config.final_seeds
        return make_cases(n, seed, *args)
    monkeypatch.setattr("causaguard.intervention_study.make_cases", track)
    with pytest.raises(ValueError, match="model identity"):
        run_study(development=seal(changed))


@pytest.mark.parametrize("target", ["decision", "outcome", "summary", "latent"])
def test_resealed_tampering_cannot_pass_recomputation(reports, target):
    _, dev, _ = reports
    changed = deepcopy(dev)
    result = changed["results"]["iid"]
    if target == "decision":
        result["decisions"][0]["contextual"][0] = "forged"
    elif target == "outcome":
        result["potential_outcomes"][0]["verify"]["utility"] += 100
    elif target == "latent":
        result["cases"][0]["current_bad"] = not result["cases"][0]["current_bad"]
    else:
        result["policies"]["contextual"]["metrics"]["utility"]["estimate"] += 100
    with pytest.raises(ValueError, match="differs"):
        replay_report(seal(changed))


def test_crossed_bootstrap_preserves_cluster_variation_and_pairing():
    cells = np.array([[[t + e] for e in (0, 10, 20)] for t in (0, 1, 2)])
    ci = crossed_interval(cells, 500, 5)[0]
    assert ci["estimate"] == 11 and ci["interval"][0] < 11 < ci["interval"][1]
    assert crossed_interval(cells, 500, 5)[0] == ci
    zero = crossed_interval(cells - cells, 500, 5)[0]
    assert zero["interval"] == [0, 0] and zero["zero_width"]
    # Duplicating fixed baseline training rows must not manufacture independent evidence.
    fixed = np.array([[[0], [1], [2]]])
    np.testing.assert_allclose(crossed_interval(np.repeat(fixed, 3, axis=0), 4000, 7)[0]["interval"],
                               crossed_interval(np.repeat(fixed, 6, axis=0), 4000, 7)[0]["interval"])
    with pytest.raises(ValueError, match="paired"):
        paired_cells(cells, cells, ["a", "b", "c"], ["b", "a", "c"])
    with pytest.raises(ValueError, match="paired"):
        paired_cells(cells, cells, ["a", "a", "c"], ["a", "a", "c"])
    assert len(METRICS) == 13


def test_calibration_metrics_known_values_include_probability_one():
    good = calibration_metrics([0, 1], [0, 1])
    assert good["brier"] == good["ece10"] == 0
    bad = calibration_metrics([1, 0], [0, 1])
    assert bad["brier"] == bad["ece10"] == 1


def test_final_cli_disallows_tuning_and_existing_files_are_immutable(tmp_path, capsys):
    path = tmp_path / "report.json"
    with pytest.raises(SystemExit):
        main(["intervention-study", "--phase", "final", "--config", "experiments/v050.json",
              "--output", str(path)])
    assert "forbids configuration overrides" in capsys.readouterr().err
    write_new({"preserve": True}, path)
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        write_new({"destroy": True}, path)
    with pytest.raises(SystemExit):
        main(["intervention-study", "--phase", "development", "--config", "experiments/v050.json",
              "--output", str(path)])
    assert path.read_bytes() == before


def test_final_requires_exact_parent_and_rejects_phase_confusion(reports):
    _, dev, final = reports
    with pytest.raises(ValueError, match="exact development"):
        replay_report(final)
    with pytest.raises(ValueError, match="development report"):
        run_study(development=final)
    with pytest.raises(ValueError, match="exactly one"):
        run_study(config=StudyConfig(), development=dev)


def test_development_never_opens_final_data_or_fits_on_evaluation(reports, monkeypatch):
    config, _, _ = reports
    from causaguard.intervention_env import make_cases
    from causaguard.intervention_policy import PolicySuite
    original_fit = PolicySuite.fit
    seen = []
    def generation(n, seed, *args):
        assert seed not in config.final_seeds
        seen.append(seed)
        return make_cases(n, seed, *args)
    def fit(self, cases, outcomes, calibration, calibration_outcomes):
        assert {c.evaluation_seed for c in cases} <= set(config.training_seeds)
        assert {c.evaluation_seed for c in calibration} <= set(config.calibration_seeds)
        return original_fit(self, cases, outcomes, calibration, calibration_outcomes)
    monkeypatch.setattr("causaguard.intervention_study.make_cases", generation)
    monkeypatch.setattr(PolicySuite, "fit", fit)
    run_study(config=config)
    assert set(config.development_seeds) <= set(seen)
