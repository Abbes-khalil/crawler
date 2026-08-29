"""Guard the Vercel entrypoint: api/index.py must import cleanly and expose
the synchronous crawl route."""

from fastapi.testclient import TestClient


def test_entrypoint_exposes_app_and_route():
    from api.index import app

    with TestClient(app) as client:
        assert client.get("/api/health").status_code == 200
        assert "/api/crawl-now" in client.get("/openapi.json").json()["paths"]
