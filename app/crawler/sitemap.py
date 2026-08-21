from urllib.parse import urlparse
from xml.etree import ElementTree

import httpx

from app.crawler.link_discovery import clean_url


MAX_CHILD_SITEMAPS = 5


def _parse_locs(xml_text: str) -> tuple[list[str], list[str]]:
    """Returns (page_urls, child_sitemap_urls) from a sitemap or
    sitemap-index document. Malformed XML yields two empty lists rather
    than raising."""
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError:
        return [], []

    tag = root.tag.lower()

    locs = [
        (elem.text or "").strip()
        for elem in root.iter()
        if elem.tag.lower().endswith("loc") and elem.text
    ]
    locs = [loc for loc in locs if loc]

    if tag.endswith("sitemapindex"):
        return [], locs

    return locs, []


async def discover_sitemap_urls(
    homepage_url: str,
    client: httpx.AsyncClient,
    known_sitemap_urls: list[str],
    max_urls: int,
) -> list[str]:
    """Fetches /sitemap.xml plus any sitemaps referenced by robots.txt,
    follows at most MAX_CHILD_SITEMAPS nested sitemap-index entries, and
    returns same-domain page URLs (not blindly all of them - callers are
    expected to run these through the normal page ranker)."""
    parsed = urlparse(homepage_url)
    base_domain = parsed.netloc.lower()

    candidate_sitemaps = list(known_sitemap_urls)
    default_sitemap = f"{parsed.scheme}://{parsed.netloc}/sitemap.xml"

    if default_sitemap not in candidate_sitemaps:
        candidate_sitemaps.append(default_sitemap)

    discovered: set[str] = set()
    visited_sitemaps: set[str] = set()

    while candidate_sitemaps and len(visited_sitemaps) < MAX_CHILD_SITEMAPS:
        sitemap_url = candidate_sitemaps.pop(0)

        if sitemap_url in visited_sitemaps:
            continue

        visited_sitemaps.add(sitemap_url)

        try:
            response = await client.get(sitemap_url)
        except httpx.HTTPError:
            continue

        if response.status_code >= 400:
            continue

        page_urls, child_sitemaps = _parse_locs(response.text)

        for url in page_urls:
            if urlparse(url).netloc.lower() != base_domain:
                continue

            discovered.add(clean_url(url))

            if len(discovered) >= max_urls:
                break

        for child in child_sitemaps:
            if child not in visited_sitemaps:
                candidate_sitemaps.append(child)

        if len(discovered) >= max_urls:
            break

    return sorted(discovered)
