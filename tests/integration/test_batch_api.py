import fakeredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.api.batch as batch_api
import app.storage.db as storage_db
from app.main import app


@pytest.fixture
def sqlite_session_factory(monkeypatch):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    storage_db.Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine)

    monkeypatch.setattr(storage_db, "get_session", session_local)
    monkeypatch.setattr(batch_api, "is_persistence_enabled", lambda: True)

    return session_local


@pytest.fixture
def fake_queue(monkeypatch):
    enqueued = []

    def fake_enqueue(job_id, website, max_pages):
        enqueued.append((job_id, website, max_pages))

    monkeypatch.setattr(batch_api, "is_queue_enabled", lambda: True)
    monkeypatch.setattr(batch_api, "enqueue_company_crawl", fake_enqueue)

    return enqueued


def test_crawl_batch_without_redis_returns_503(monkeypatch):
    monkeypatch.setattr(batch_api, "is_queue_enabled", lambda: False)

    client = TestClient(app)
    response = client.post(
        "/crawl-batch", json={"websites": ["https://a.example"]}
    )

    assert response.status_code == 503


def test_crawl_batch_without_database_returns_503(monkeypatch):
    monkeypatch.setattr(batch_api, "is_queue_enabled", lambda: True)
    monkeypatch.setattr(batch_api, "is_persistence_enabled", lambda: False)

    client = TestClient(app)
    response = client.post(
        "/crawl-batch", json={"websites": ["https://a.example"]}
    )

    assert response.status_code == 503


def test_crawl_batch_enqueues_and_creates_job(sqlite_session_factory, fake_queue):
    client = TestClient(app)

    response = client.post(
        "/crawl-batch",
        json={
            "websites": ["https://a.example", "https://b.example"],
            "max_pages": 3,
        },
    )

    assert response.status_code == 202

    body = response.json()
    assert body["status"] == "QUEUED"
    assert body["total_companies"] == 2
    assert len(fake_queue) == 2
    assert fake_queue[0][2] == 3


def test_get_job_returns_status_and_companies(sqlite_session_factory, fake_queue):
    client = TestClient(app)

    create_response = client.post(
        "/crawl-batch", json={"websites": ["https://a.example"]}
    )
    job_id = create_response.json()["job_id"]

    job_response = client.get(f"/jobs/{job_id}")

    assert job_response.status_code == 200
    body = job_response.json()
    assert body["job_id"] == job_id
    assert body["total_companies"] == 1
    assert body["companies"][0]["website"] == "https://a.example"
    assert body["companies"][0]["status"] == "QUEUED"


def test_get_unknown_job_returns_404(sqlite_session_factory):
    client = TestClient(app)
    response = client.get("/jobs/does-not-exist")

    assert response.status_code == 404


def test_crawl_batch_rejects_empty_website_list(sqlite_session_factory, fake_queue):
    client = TestClient(app)
    response = client.post("/crawl-batch", json={"websites": []})

    assert response.status_code == 422
