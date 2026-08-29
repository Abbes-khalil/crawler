"""Integration tests for the synchronous hosted endpoint POST /api/crawl-now.

Network boundaries are faked exactly as in test_crawl_company.py so the
crawl runs fully offline against in-repo fixtures.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.crawler.orchestrator as orchestrator
from app.api import guard
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
    return PAGE_MAP.get(url, (200, GENERIC_PAGE_HTML))


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
    monkeypatch.setattr(orchestrator, "fetch_robots_policy", fake_fetch_robots_policy)
    monkeypatch.setattr(
        orchestrator, "discover_sitemap_urls", fake_discover_sitemap_urls
    )
    guard.reset_rate_limit()


@pytest.fixture(autouse=True)
def _clear_access_env(monkeypatch):
    monkeypatch.delenv("ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("RATE_LIMIT_PER_HOUR", raising=False)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_crawl_now_returns_text_and_data(client):
    r = client.post("/api/crawl-now", json={"website": BASE_URL, "max_pages": 5})
    assert r.status_code == 200
    body = r.json()

    assert body["data"]["status"] in ("SUCCESS", "PARTIAL_SUCCESS")
    assert body["data"]["canonical_url"] == BASE_URL

    text = body["text"]
    assert text.startswith("# Web crawl: " + BASE_URL)
    assert "## Contact details" in text
    assert "info@" in text or "Emails" in text


def test_crawl_now_clamps_pages_to_hosted_max(client):
    r = client.post(
        "/api/crawl-now", json={"website": BASE_URL, "max_pages": 20}
    )
    assert r.status_code == 200
    assert r.json()["data"]["pages_crawled"] <= 8


def test_crawl_now_rejects_private_host(client):
    r = client.post(
        "/api/crawl-now", json={"website": "http://127.0.0.1:9999", "max_pages": 3}
    )
    assert r.status_code == 422


def test_crawl_now_requires_token_when_configured(client, monkeypatch):
    monkeypatch.setenv("ACCESS_TOKEN", "s3cret")

    denied = client.post(
        "/api/crawl-now", json={"website": BASE_URL, "max_pages": 3}
    )
    assert denied.status_code == 403

    ok = client.post(
        "/api/crawl-now?k=s3cret",
        json={"website": BASE_URL, "max_pages": 3},
    )
    assert ok.status_code == 200


def test_crawl_now_rate_limited(client, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_PER_HOUR", "2")
    guard.reset_rate_limit()

    for _ in range(2):
        assert (
            client.post(
                "/api/crawl-now", json={"website": BASE_URL, "max_pages": 3}
            ).status_code
            == 200
        )

    blocked = client.post(
        "/api/crawl-now", json={"website": BASE_URL, "max_pages": 3}
    )
    assert blocked.status_code == 429
