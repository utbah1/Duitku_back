"""Health check tests."""
from app.main import app


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "service" in body


def test_docs_available(client):
    resp = client.get("/docs")
    assert resp.status_code == 200


def test_redoc_available(client):
    resp = client.get("/redoc")
    assert resp.status_code == 200
