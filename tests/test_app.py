from fastapi.testclient import TestClient

from src.app import app

client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert "status" in r.json()


def test_ask_validation():
    r = client.post("/ask", json={"user_id": "u", "question": "ok"})
    # question min_length=3, so exactly 'ok' should fail; expect 422
    assert r.status_code in (422, 400)
