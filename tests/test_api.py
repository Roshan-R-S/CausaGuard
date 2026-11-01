from fastapi.testclient import TestClient

from causaguard import api


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
