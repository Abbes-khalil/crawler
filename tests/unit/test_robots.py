import httpx
import pytest

from app.crawler.robots import fetch_robots_policy


ROBOTS_TXT = """User-agent: *
Disallow: /private/
Sitemap: https://company.com/sitemap.xml
"""


@pytest.mark.asyncio
async def test_parses_disallow_rules_and_sitemap():
    def handler(request):
        return httpx.Response(200, text=ROBOTS_TXT)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    ) as client:
        policy = await fetch_robots_policy("https://company.com", client)

    assert policy.is_allowed("https://company.com/about", "TestBot") is True
    assert (
        policy.is_allowed("https://company.com/private/secret", "TestBot")
        is False
    )
    assert "https://company.com/sitemap.xml" in policy.sitemap_urls


@pytest.mark.asyncio
async def test_missing_robots_txt_fails_open():
    def handler(request):
        return httpx.Response(404)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    ) as client:
        policy = await fetch_robots_policy("https://company.com", client)

    assert policy.is_allowed("https://company.com/anything", "TestBot") is True
    assert policy.sitemap_urls == []


@pytest.mark.asyncio
async def test_network_error_fails_open():
    def handler(request):
        raise httpx.ConnectError("boom", request=request)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    ) as client:
        policy = await fetch_robots_policy("https://company.com", client)

    assert policy.is_allowed("https://company.com/anything", "TestBot") is True
