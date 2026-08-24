from fastapi.testclient import TestClient

from app.main import app


def test_cors_allows_configured_frontend_origin():
    client = TestClient(app)

    response = client.get("/health", headers={"Origin": "http://localhost:3000"})

    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_cors_rejects_other_origin():
    client = TestClient(app)

    response = client.get("/health", headers={"Origin": "http://evil.example"})

    assert "access-control-allow-origin" not in response.headers
