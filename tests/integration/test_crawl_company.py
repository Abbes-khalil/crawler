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


def test_crawl_company_returns_structured_response():
    client = TestClient(app)

    response = client.post(
        "/crawl-company",
        json={"website": BASE_URL, "max_pages": 5},
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] in ("SUCCESS", "PARTIAL_SUCCESS")
    assert body["canonical_url"] == BASE_URL
    assert body["pages_crawled"] >= 1
    assert body["pages"], "expected at least one crawled page"

    for page in body["pages"]:
        assert page["content_hash"]
        assert page["crawl_method"] == "http"

    fields = {obs["field"] for obs in body["observations"]}
    assert "email" in fields

    email_obs = [o for o in body["observations"] if o["field"] == "email"]
    assert any(o["source_type"] == "mailto_link" for o in email_obs)
    assert any(o["confidence"] == 1.0 for o in email_obs)


def test_crawl_company_normalizes_bare_domain_without_scheme():
    client = TestClient(app)

    response = client.post(
        "/crawl-company",
        json={"website": "acme-industrial.example", "max_pages": 3},
    )

    assert response.status_code == 200
    assert response.json()["canonical_url"] == BASE_URL


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
