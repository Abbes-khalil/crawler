import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.crawler.orchestrator as orchestrator
from app.main import app


FIXTURES = Path(__file__).parent.parent / "fixtures"

HOMEPAGE_HTML = (FIXTURES / "homepage.html").read_text(encoding="utf-8")
CONTACT_HTML = (FIXTURES / "contact.html").read_text(encoding="utf-8")

GENERIC_PAGE_HTML = """
<html lang="en">
<head><title>Generic Page</title></head>
<body><main>
<h1>Content</h1>
<p>This page has enough readable text to pass content extraction checks
for the automated integration test suite used in this project.</p>
</main></body>
</html>
"""

BASE_URL = "https://acme-industrial.example"

PAGE_MAP = {
    BASE_URL: (200, HOMEPAGE_HTML),
    f"{BASE_URL}/contact": (200, CONTACT_HTML),
}


async def fake_fetch_page(url, client):
    if url in PAGE_MAP:
        return PAGE_MAP[url]

    return 200, GENERIC_PAGE_HTML


class _FakeRobotsPolicy:
    sitemap_urls: list[str] = []

    def is_allowed(self, url, user_agent):
        return True


async def fake_fetch_robots_policy(homepage_url, client):
    return _FakeRobotsPolicy()


async def fake_discover_sitemap_urls(
    homepage_url, client, known_sitemap_urls, max_urls
):
    return []


@pytest.fixture(autouse=True)
def patch_network_boundaries(monkeypatch):
    monkeypatch.setattr(orchestrator, "fetch_page", fake_fetch_page)
    monkeypatch.setattr(
        orchestrator, "fetch_robots_policy", fake_fetch_robots_policy
    )
    monkeypatch.setattr(
        orchestrator, "discover_sitemap_urls", fake_discover_sitemap_urls
    )


@pytest.fixture
def client():
    # Context-manager form keeps one event loop (and lifespan) alive for the
    # whole test, so background crawl tasks are not cancelled between requests.
    with TestClient(app) as c:
        yield c


def _run_crawl(client: TestClient, website: str, max_pages: int) -> dict:
    start = client.post(
        "/api/crawl", json={"website": website, "max_pages": max_pages}
    )
    assert start.status_code == 202
    job_id = start.json()["id"]

    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        poll = client.get(f"/api/jobs/{job_id}")
        assert poll.status_code == 200
        body = poll.json()
        if body["status"] in ("completed", "failed", "cancelled"):
            return body
        time.sleep(0.05)

    raise AssertionError("crawl job did not finish in time")


def test_crawl_job_returns_structured_result(client):

    job = _run_crawl(client, BASE_URL, 5)

    assert job["status"] == "completed"
    result = job["result"]

    assert result["status"] in ("SUCCESS", "PARTIAL_SUCCESS")
    assert result["canonical_url"] == BASE_URL
    assert result["pages_crawled"] >= 1
    assert result["pages"], "expected at least one crawled page"

    for page in result["pages"]:
        assert page["content_hash"]
        assert page["crawl_method"] == "http"

    fields = {obs["field"] for obs in result["observations"]}
    assert "email" in fields

    email_obs = [o for o in result["observations"] if o["field"] == "email"]
    assert any(o["source_type"] == "mailto_link" for o in email_obs)
    assert any(o["confidence"] == 1.0 for o in email_obs)


def test_crawl_job_normalizes_bare_domain_without_scheme(client):

    job = _run_crawl(client, "acme-industrial.example", 3)

    assert job["status"] == "completed"
    assert job["result"]["canonical_url"] == BASE_URL


def test_crawl_rejects_private_network_host(client):

    response = client.post(
        "/api/crawl", json={"website": "http://127.0.0.1:9999", "max_pages": 3}
    )

    assert response.status_code == 422


def test_health_endpoint(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
