import httpx
import pytest

from app.crawler.sitemap import discover_sitemap_urls


SITEMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://company.com/products</loc></url>
  <url><loc>https://company.com/about</loc></url>
  <url><loc>https://external.example/ignored</loc></url>
</urlset>
"""

SITEMAP_INDEX_XML = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://company.com/sitemap-pages.xml</loc></sitemap>
</sitemapindex>
"""


@pytest.mark.asyncio
async def test_discovers_urls_and_filters_external_domain():
    def handler(request):
        return httpx.Response(200, text=SITEMAP_XML)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    ) as client:
        urls = await discover_sitemap_urls(
            "https://company.com", client, [], max_urls=50
        )

    assert "https://company.com/products" in urls
    assert "https://company.com/about" in urls
    assert not any("external.example" in u for u in urls)


@pytest.mark.asyncio
async def test_follows_sitemap_index_one_level():
    calls = {"count": 0}

    def handler(request):
        calls["count"] += 1

        if str(request.url).endswith("sitemap-pages.xml"):
            return httpx.Response(200, text=SITEMAP_XML)

        return httpx.Response(200, text=SITEMAP_INDEX_XML)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    ) as client:
        urls = await discover_sitemap_urls(
            "https://company.com", client, [], max_urls=50
        )

    assert "https://company.com/products" in urls


@pytest.mark.asyncio
async def test_missing_sitemap_returns_empty_list():
    def handler(request):
        return httpx.Response(404)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    ) as client:
        urls = await discover_sitemap_urls(
            "https://company.com", client, [], max_urls=50
        )

    assert urls == []
