from fastapi.testclient import TestClient

from causaguard import api

PAYLOAD = dict(amount=100, authorization_confidence=1, note_risk_score=0,
               data_age_hours=0, tool_error_rate=0,
               schema_warning=False, confirmation_present=True)


def test_health():
    response = TestClient(api.app).get("/health")
    assert response.status_code == 200
    assert response.json()["mode"] == "advisory-only"


def test_missing_model_gives_actionable_error(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "_model", None)
    monkeypatch.setattr(api, "MODEL_PATH", tmp_path / "not-found.joblib")
    payload = dict(amount=100, authorization_confidence=0.9, note_risk_score=0.1,
                   data_age_hours=2, tool_error_rate=0.1,
                   schema_warning=False, confirmation_present=True)
    resp = TestClient(api.app).post("/recommend", json=payload)
    assert resp.status_code == 503


def test_validation_rejects_extra_fields():
    payload = dict(amount=100, authorization_confidence=1.5, note_risk_score=0,
                   data_age_hours=1, tool_error_rate=0.1,
                   schema_warning=False, confirmation_present=True, secret="x")
    resp = TestClient(api.app).post("/recommend", json=payload)
    assert resp.status_code == 422


def test_original_response_is_backward_compatible(trained_policy, monkeypatch):
    from causaguard.domain import Scenario

    monkeypatch.setattr(api, "_model", trained_policy)
    response = TestClient(api.app).post("/recommend", json=PAYLOAD)
    assert response.status_code == 200
    assert response.json() == trained_policy.recommend(Scenario(**PAYLOAD, seed=0)).as_dict()


def test_conservative_selectable_with_explicit_configuration(trained_policy, monkeypatch):
    monkeypatch.setattr(api, "_model", trained_policy)
    payload = {**PAYLOAD, "policy": "conservative", "conservative_config": {"reward_margin": 0.2}}
    response = TestClient(api.app).post("/recommend", json=payload)
    assert response.status_code == 200
    assert response.json()["policy"] == "conservative"
    assert response.json()["diagnostics"]["config"]["reward_margin"] == 0.2
    payload["confirmation_present"] = False
    assert TestClient(api.app).post("/recommend", json=payload).json()["action"] == "escalate"


def test_policy_and_authorization_validation():
    client = TestClient(api.app)
    for updates in ({"policy": "unknown"}, {"confirmation_present": "true"},
                    {"confirmation_present": 1}, {"conservative_config": {"risk_limit": 1}},
                    {"policy": "conservative", "conservative_config": {"risk_limit": -1}}):
        assert client.post("/recommend", json={**PAYLOAD, **updates}).status_code == 422


def test_corrupt_model_returns_actionable_503(tmp_path, monkeypatch):
    path = tmp_path / "broken.joblib"
    path.write_bytes(b"not a model")
    monkeypatch.setattr(api, "_model", None)
    monkeypatch.setattr(api, "MODEL_PATH", path)
    response = TestClient(api.app).post("/recommend", json=PAYLOAD)
    assert response.status_code == 503
    assert "retrain" in response.json()["detail"]


def test_untrained_model_fails_closed_for_original_and_verifies_for_conservative(monkeypatch):
    from causaguard.policy import LearnedPolicy

    monkeypatch.setattr(api, "_model", LearnedPolicy())
    assert TestClient(api.app).post("/recommend", json=PAYLOAD).status_code == 503
    response = TestClient(api.app).post("/recommend", json={**PAYLOAD, "policy": "conservative"})
    assert response.status_code == 200 and response.json()["action"] == "verify"
