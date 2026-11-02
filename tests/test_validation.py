from copy import deepcopy

import pytest

from causaguard.adversarial import CONTROLS, HELD_OUT, KNOWN, make_dataset
from causaguard.cli import main
from causaguard.llm_trace import deterministic, digest
from causaguard.validation import (
    METRICS,
    POLICIES,
    ValidationConfig,
    behavior_digest,
    paired_bootstrap,
    replay_validation,
    run_validation,
)


@pytest.fixture(scope="module")
def validation_reports():
    config = ValidationConfig(training_seeds=(20101, 20102), model_seeds=(1, 2),
                              development_seeds=(20201, 20202), final_seeds=(20301, 20302),
                              train_n=64, n_estimators=3, variants_per_family=1,
                              bootstrap_replicates=20)
    dev = run_validation(config=config)
    final = run_validation(development=dev)
    return config, dev, final


def test_complete_protocol_and_replay(validation_reports):
    config, dev, final = validation_reports
    assert set(dev["by_family"]) == set(CONTROLS + KNOWN)
    assert set(final["by_family"]) == set(CONTROLS + KNOWN + HELD_OUT)
    assert len(final["rows"]) == 2 * 2 * 21 * len(POLICIES)
    assert dev["dataset_sha256"] != final["dataset_sha256"]
    assert final["development_report_sha256"] == dev["report_sha256"]
    for name in POLICIES:
        metrics = final["summary"]["all"]["policies"][name]
        assert (metrics["unsafe_actions"] > 0) == (name == "unguarded")
    assert replay_validation(final)["runs"] == len(final["rows"])
    repeated = run_validation(config=config)
    # Timings/report checksums are intentionally observational; all behavior reproduces.
    for first, second in zip(dev["rows"], repeated["rows"], strict=True):
        assert deterministic(first) == deterministic(second)


def test_development_never_opens_final_cases(monkeypatch):
    from causaguard import validation
    actual = validation.make_dataset

    def spy(*args, **kwargs):
        assert kwargs.get("final", False) is False
        return actual(*args, **kwargs)

    monkeypatch.setattr(validation, "make_dataset", spy)
    run_validation(config=ValidationConfig(training_seeds=(1, 2), model_seeds=(3, 4),
                   development_seeds=(5, 6), final_seeds=(7, 8), train_n=32,
                   n_estimators=2, variants_per_family=1, bootstrap_replicates=20))


@pytest.mark.parametrize("options", [
    {"training_seeds": (1,)}, {"model_seeds": (1, 1, 2)}, {"development_seeds": (1, 1)},
    {"training_seeds": (1, 2, 3), "final_seeds": (3, 4)}, {"final_seeds": (True, 2)},
    {"train_n": 0}, {"n_estimators": 1}, {"variants_per_family": 0}, {"bootstrap_seed": -1},
])
def test_invalid_protocols(options):
    with pytest.raises(ValueError):
        ValidationConfig(**options)


def test_final_rejects_tuning_drift_before_opening_final(validation_reports, monkeypatch):
    config, dev, _ = validation_reports
    with pytest.raises(ValueError, match="overrides"):
        run_validation(config=config, development=dev)
    changed = deepcopy(dev)
    changed["source_manifest"]["guarded_agent.py"] = "tampered"
    changed["behavior_sha256"] = behavior_digest(changed)
    changed["report_sha256"] = digest({k: v for k, v in changed.items() if k != "report_sha256"})

    def forbidden(*args, **kwargs):
        pytest.fail("opened data before checking protocol")

    monkeypatch.setattr("causaguard.validation.make_dataset", forbidden)
    with pytest.raises(ValueError, match="source_manifest"):
        run_validation(development=changed)


@pytest.mark.parametrize("mutation", ["drop", "duplicate", "metric", "trace", "summary"])
def test_replay_rejects_resealed_tampering(validation_reports, mutation):
    _, dev, _ = validation_reports
    changed = deepcopy(dev)
    if mutation == "drop":
        changed["rows"].pop()
    elif mutation == "duplicate":
        changed["rows"][1] = changed["rows"][0]
    elif mutation == "metric":
        changed["rows"][0]["metrics"]["safe_completion_rate"] = 999
    elif mutation == "trace":
        changed["rows"][0]["trace"]["task"] = "tampered"
    else:
        changed["summary"]["all"]["policies"]["rules_only"]["runs"] = 999
    changed["behavior_sha256"] = behavior_digest(changed)
    changed["report_sha256"] = digest({k: v for k, v in changed.items() if k != "report_sha256"})
    with pytest.raises(ValueError):
        replay_validation(changed)


def test_bootstrap_pairing_cluster_uncertainty_and_determinism():
    left, right = [], []
    for train in (1, 2, 3):
        for seed in (10, 20, 30):
            row = {"training_seed": train, "evaluation_seed": seed, "case_key": str(seed),
                   "metrics": {m: float(train + seed) for m in METRICS}}
            left.append(row)
            right.append({**row, "metrics": dict.fromkeys(METRICS, 0)})
    result = paired_bootstrap(left, right, 200, 5)
    assert result == paired_bootstrap(left, list(reversed(right)), 200, 5)
    assert result[METRICS[0]]["difference"] == 22
    low, high = result[METRICS[0]]["ci95"]
    assert low < 22 < high
    zeros = paired_bootstrap(left, left, 100, 5)
    assert zeros[METRICS[0]] == {"difference": 0, "ci95": [0, 0]}
    with pytest.raises(ValueError, match="paired"):
        paired_bootstrap(left, right[:-1], 100, 5)


def test_disjoint_datasets_and_seed_dependent_variation():
    dev = make_dataset((30101, 30102), 2)
    final = make_dataset((30201, 30202), 2, final=True)
    assert len({c.key for c in dev + final}) == len(dev + final)
    assert not set(HELD_OUT) & {c.family for c in dev}
    assert len({c.state.customer_id for c in dev + final}) == len(dev + final)


def test_final_cli_disallows_configuration_override(tmp_path, capsys):
    with pytest.raises(SystemExit):
        main(["validate-research", "--phase", "final", "--config", "experiments/v040.json",
              "--output", str(tmp_path / "never.json")])
    assert "tuning is forbidden" in capsys.readouterr().err
    assert not (tmp_path / "never.json").exists()


def test_cli_never_overwrites_existing_reports(tmp_path, capsys):
    output = tmp_path / "historical.json"
    output.write_text("preserve")
    with pytest.raises(SystemExit):
        main(["validate-research", "--phase", "development", "--config", "experiments/v040.json",
              "--output", str(output)])
    assert "refusing to overwrite" in capsys.readouterr().err
    assert output.read_text() == "preserve"
