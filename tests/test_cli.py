import json

import pytest

from causaguard.cli import main
from causaguard.research import ExperimentConfig


def test_cli_complete_agent_run_and_replay(trained_policy, tmp_path, capsys):
    model = tmp_path / "model.joblib"
    output = tmp_path / "traces.json"
    trained_policy.save(model)
    main(["agent-demo", "--model", str(model), "--output", str(output)])
    assert len(json.loads(output.read_text())["traces"]) == 6
    main(["replay", str(output), "--model", str(model)])
    assert '"replay": "matched"' in capsys.readouterr().out


def test_cli_development_and_final_json_reports(tmp_path):
    config = ExperimentConfig(train_n=32, n_estimators=2, n_per_seed=4,
                              development_seeds=(71, 72), final_seeds=(81, 82),
                              bootstrap_replicates=4, profiles=("iid",),
                              sensitivity_risk_limits=(0.03,), sensitivity_reward_margins=(0.05,))
    config_path = tmp_path / "config.json"
    config_path.write_text(config.model_dump_json())
    development = tmp_path / "development.json"
    final = tmp_path / "final.json"
    main(["experiment", "--phase", "development", "--config", str(config_path),
          "--output", str(development)])
    main(["experiment", "--phase", "final", "--protocol", str(development),
          "--output", str(final)])
    report = json.loads(final.read_text())
    assert report["phase"] == "final"
    assert report["results"]["iid"]["policies"]["conservative"]["n"] == 8


@pytest.mark.parametrize("argv", [
    ["experiment", "--phase", "final", "--config", "anything.json"],
    ["experiment", "--phase", "development"],
    ["demo", "--model", "missing.joblib"],
])
def test_cli_actionable_errors(argv, capsys):
    with pytest.raises(SystemExit) as exc:
        main(argv)
    assert exc.value.code == 2
    assert "error:" in capsys.readouterr().err


def test_legacy_train_and_demo_commands(tmp_path, capsys):
    model = tmp_path / "policy.joblib"
    main(["train", "--n", "32", "--seed", "543", "--model", str(model)])
    assert model.exists()
    main(["demo", "--model", str(model)])
    assert "predicted_rewards" in capsys.readouterr().out
    with pytest.raises(SystemExit, match="2"):
        main(["evaluate", "--seed", "543", "--n", "2", "--model", str(model)])


def test_corrupt_model_has_no_traceback(tmp_path, capsys):
    path = tmp_path / "empty.joblib"
    path.write_bytes(b"")
    with pytest.raises(SystemExit) as exc:
        main(["demo", "--model", str(path)])
    assert exc.value.code == 2
    assert "cannot load local model" in capsys.readouterr().err
