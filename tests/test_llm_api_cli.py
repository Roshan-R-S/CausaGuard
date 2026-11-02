import json

import pytest
from fastapi.testclient import TestClient

from causaguard import api, llm_commands
from causaguard.cli import main
from causaguard.llm import LLMError
from causaguard.llm_benchmark import BenchmarkConfig, FixtureClient
from causaguard.mock_tools import fixture


class MockClient(FixtureClient):
    def __init__(self, config):
        super().__init__(fixture())

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def health(self):
        return {"status": "ok", **self.identity()}


def test_api_health_demo_inspection_replay(trained_policy, monkeypatch):
    monkeypatch.setattr(api, "_model", trained_policy)
    monkeypatch.setattr(api, "LlamaCppClient", MockClient)
    client = TestClient(api.app)
    assert client.get("/llm/health").json()["status"] == "ok"
    response = client.post("/llm/demo", json={})
    assert response.status_code == 200
    trace = response.json()
    assert trace["final"]["status"] == "completed"
    assert client.post("/llm/trace/inspect", json=trace).status_code == 200
    assert client.post("/llm/replay", json=trace).json()["llm_calls"] == 0
    trace["final"]["task_completed"] = False
    assert client.post("/llm/replay", json=trace).status_code == 422
    assert client.post("/llm/trace/inspect", json=trace).status_code == 422


@pytest.mark.parametrize("payload", [{"authorized": True}, {"confirmation_present": True},
                                         {"llm_url": "http://example.com"}, {"case": "unknown"},
                                         {"max_rounds": True}, {"_benchmark_unguarded": True}])
def test_api_cannot_set_permissions_or_remote_endpoints(payload):
    assert TestClient(api.app).post("/llm/demo", json=payload).status_code == 422


def test_api_missing_model_and_llm_errors(trained_policy, monkeypatch, tmp_path):
    monkeypatch.setattr(api, "_model", None)
    monkeypatch.setattr(api, "MODEL_PATH", tmp_path / "missing.joblib")
    assert TestClient(api.app).post("/llm/demo", json={}).status_code == 503
    class Offline(MockClient):
        def health(self):
            raise LLMError("llm_connection_error")
    monkeypatch.setattr(api, "LlamaCppClient", Offline)
    assert TestClient(api.app).get("/llm/health").status_code == 503


def test_cli_health_demo_smoke_inspect_replay(trained_policy, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(llm_commands, "LlamaCppClient", MockClient)
    model = tmp_path / "model.joblib"
    trained_policy.save(model)
    trace = tmp_path / "trace.json"
    main(["llm-health"])
    for command in ("llm-demo", "llm-smoke"):
        main([command, "--model", str(model), "--output", str(trace)])
        assert json.loads(trace.read_text())["traces"][0]["final"]["status"] == "completed"
    main(["llm-inspect", str(trace)])
    main(["llm-replay", str(trace), "--model", str(model)])
    assert '"replay": "matched"' in capsys.readouterr().out


def test_cli_benchmark_phases_and_replay(trained_policy, tmp_path, capsys):
    model, config = tmp_path / "model.joblib", tmp_path / "config.json"
    trained_policy.save(model)
    config.write_text(BenchmarkConfig(development_seeds=(71,), final_seeds=(81,),
                                     cases=("clean",)).model_dump_json())
    development, final = tmp_path / "development.json", tmp_path / "final.json"
    main(["llm-benchmark", "--phase", "development", "--config", str(config),
          "--model", str(model), "--output", str(development)])
    main(["llm-benchmark", "--phase", "final", "--protocol", str(development),
          "--model", str(model), "--output", str(final)])
    main(["llm-replay", str(final), "--benchmark", "--model", str(model)])
    assert '"replay": "matched"' in capsys.readouterr().out


def test_cli_unavailable_llm_smoke_fails_with_saved_trace(trained_policy, monkeypatch, tmp_path):
    class Offline(MockClient):
        def identity(self):
            raise LLMError("llm_connection_error")
    monkeypatch.setattr(llm_commands, "LlamaCppClient", Offline)
    model, output = tmp_path / "policy.joblib", tmp_path / "trace.json"
    trained_policy.save(model)
    with pytest.raises(SystemExit, match="2"):
        main(["llm-smoke", "--model", str(model), "--output", str(output)])
    assert json.loads(output.read_text())["traces"][0]["final"]["status"] == "llm_error"


def test_environment_configuration(monkeypatch):
    monkeypatch.setenv("CAUSAGUARD_LLM_MODEL", "qwen-local")
    monkeypatch.setenv("CAUSAGUARD_LLM_MAX_TOKENS", "128")
    config = llm_commands.environment_config()
    assert config.model == "qwen-local" and config.max_tokens == 128
