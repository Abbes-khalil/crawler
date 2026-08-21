import time
from urllib.parse import urlparse

import httpx

from app.config import (
    CRAWLER_USER_AGENT,
    PLAYWRIGHT_ENABLED,
    RESPECT_ROBOTS_TXT,
    SITEMAP_MAX_URLS,
)
from app.crawler.browser_fetcher import BrowserFetcher, is_content_insufficient
from app.crawler.http_fetcher import build_http_client, fetch_page
from app.crawler.link_discovery import discover_internal_links
from app.crawler.page_ranker import select_best_urls
from app.crawler.robots import fetch_robots_policy
from app.crawler.sitemap import discover_sitemap_urls
from app.crawler.url_normalizer import normalize_url

from app.extraction.cleaner import compute_content_hash, extract_clean_text
from app.extraction.metadata import (
    extract_language,
    extract_meta_description,
    extract_title,
)
from app.extraction.observations import build_page_observations

from app.models.observation import Observation
from app.models.page import CrawledPage, PageError
from app.models.response import CrawlCompanyResponse, CrawlMetrics


def _empty_response(
    canonical_url: str,
    status: str,
    duration_ms: int,
) -> CrawlCompanyResponse:
    return CrawlCompanyResponse(
        status=status,
        canonical_url=canonical_url,
        pages_discovered=0,
        pages_selected=0,
        pages_crawled=0,
        pages_failed=0,
        pages=[],
        page_errors=[],
        observations=[],
        metrics=CrawlMetrics(
            duration_ms=duration_ms,
            http_pages=0,
            playwright_pages=0,
        ),
    )


def _dominant_status(page_errors: list[PageError]) -> str:
    if not page_errors:
        return "INSUFFICIENT_CONTENT"

    counts: dict[str, int] = {}

    for error in page_errors:
        counts[error.status] = counts.get(error.status, 0) + 1

    return max(counts, key=counts.get)


async def _try_render_with_browser(
    url: str,
    html: str,
    browser: BrowserFetcher | None,
) -> tuple[str, str, bool]:
    """Returns (html, crawl_method, used_playwright). Falls back
    silently to the original HTTP html on any browser failure - a
    Playwright problem should degrade the page, not the whole crawl."""
    if browser is None or not is_content_insufficient(html):
        return html, "http", False

    try:
        _status, rendered_html = await browser.fetch(url)
    except Exception:
        return html, "http", False

    if is_content_insufficient(rendered_html):
        return html, "http", False

    return rendered_html, "playwright", True


async def crawl_company(
    website: str,
    max_pages: int,
) -> CrawlCompanyResponse:
    start = time.monotonic()

    canonical_url = normalize_url(website)

    if not urlparse(canonical_url).netloc or "." not in urlparse(canonical_url).netloc:
        duration_ms = int((time.monotonic() - start) * 1000)
        return _empty_response(canonical_url, "INVALID_URL", duration_ms)

    browser = BrowserFetcher() if PLAYWRIGHT_ENABLED else None

    try:
        async with build_http_client() as client:
            robots_policy = await fetch_robots_policy(canonical_url, client)

            if RESPECT_ROBOTS_TXT and not robots_policy.is_allowed(
                canonical_url, CRAWLER_USER_AGENT
            ):
                duration_ms = int((time.monotonic() - start) * 1000)
                return _empty_response(canonical_url, "ROBOTS_DENIED", duration_ms)

            try:
                homepage_status, homepage_html = await fetch_page(
                    canonical_url, client
                )
            except httpx.TimeoutException:
                duration_ms = int((time.monotonic() - start) * 1000)
                return _empty_response(canonical_url, "TIMEOUT", duration_ms)
            except httpx.ConnectError:
                duration_ms = int((time.monotonic() - start) * 1000)
                return _empty_response(canonical_url, "DEAD_DOMAIN", duration_ms)
            except httpx.HTTPError:
                duration_ms = int((time.monotonic() - start) * 1000)
                return _empty_response(canonical_url, "HTTP_ERROR", duration_ms)

            if homepage_status == 403:
                duration_ms = int((time.monotonic() - start) * 1000)
                return _empty_response(canonical_url, "BLOCKED", duration_ms)

            if homepage_status >= 400:
                duration_ms = int((time.monotonic() - start) * 1000)
                return _empty_response(canonical_url, "HTTP_ERROR", duration_ms)

            link_source_html = homepage_html

            if is_content_insufficient(homepage_html) and browser is not None:
                try:
                    _pw_status, rendered = await browser.fetch(canonical_url)

                    if not is_content_insufficient(rendered):
                        link_source_html = rendered
                except Exception:
                    pass

            discovered = set(
                discover_internal_links(link_source_html, canonical_url)
            )

            sitemap_urls = await discover_sitemap_urls(
                canonical_url,
                client,
                robots_policy.sitemap_urls,
                SITEMAP_MAX_URLS,
            )
            discovered.update(sitemap_urls)

            discovered = sorted(discovered)

            selected_urls = select_best_urls(
                discovered,
                homepage=canonical_url,
                max_pages=max_pages,
            )

            pages: list[CrawledPage] = []
            page_errors: list[PageError] = []
            observations: list[Observation] = []
            seen_observation_keys: set[tuple[str, str]] = set()
            http_pages_count = 0
            playwright_pages_count = 0

            for url in selected_urls:
                if RESPECT_ROBOTS_TXT and not robots_policy.is_allowed(
                    url, CRAWLER_USER_AGENT
                ):
                    page_errors.append(
                        PageError(
                            url=url,
                            status="ROBOTS_DENIED",
                            error="disallowed by robots.txt",
                        )
                    )
                    continue

                try:
                    status_code, html = await fetch_page(url, client)
                except httpx.TimeoutException as exc:
                    page_errors.append(
                        PageError(url=url, status="TIMEOUT", error=str(exc))
                    )
                    continue
                except httpx.ConnectError as exc:
                    page_errors.append(
                        PageError(url=url, status="DEAD_DOMAIN", error=str(exc))
                    )
                    continue
                except httpx.HTTPError as exc:
                    page_errors.append(
                        PageError(url=url, status="HTTP_ERROR", error=str(exc))
                    )
                    continue

                if status_code == 403:
                    page_errors.append(
                        PageError(url=url, status="BLOCKED", error="HTTP 403")
                    )
                    continue

                if status_code >= 400:
                    page_errors.append(
                        PageError(
                            url=url,
                            status="HTTP_ERROR",
                            error=f"HTTP {status_code}",
                        )
                    )
                    continue

                html, crawl_method, used_playwright = (
                    await _try_render_with_browser(url, html, browser)
                )

                clean_text = extract_clean_text(html)

                if not clean_text.strip():
                    page_errors.append(
                        PageError(
                            url=url,
                            status="INSUFFICIENT_CONTENT",
                            error="no readable text extracted",
                        )
                    )
                    continue

                for observation in build_page_observations(html, url):
                    key = (
                        observation.field,
                        observation.normalized_value or observation.raw_value,
                    )

                    if key in seen_observation_keys:
                        continue

                    seen_observation_keys.add(key)
                    observations.append(observation)

                pages.append(
                    CrawledPage(
                        url=url,
                        title=extract_title(html),
                        meta_description=extract_meta_description(html),
                        language=extract_language(html),
                        text=clean_text,
                        status_code=status_code,
                        crawl_method=crawl_method,
                        content_hash=compute_content_hash(clean_text),
                    )
                )

                if used_playwright:
                    playwright_pages_count += 1
                else:
                    http_pages_count += 1
    finally:
        if browser is not None:
            await browser.close()

    duration_ms = int((time.monotonic() - start) * 1000)

    pages_crawled = len(pages)
    pages_failed = len(page_errors)

    if pages_crawled == 0:
        status = _dominant_status(page_errors)
    elif pages_failed > 0:
        status = "PARTIAL_SUCCESS"
    else:
        status = "SUCCESS"

    return CrawlCompanyResponse(
        status=status,
        canonical_url=canonical_url,
        pages_discovered=len(discovered),
        pages_selected=len(selected_urls),
        pages_crawled=pages_crawled,
        pages_failed=pages_failed,
        pages=pages,
        page_errors=page_errors,
        observations=observations,
        metrics=CrawlMetrics(
            duration_ms=duration_ms,
            http_pages=http_pages_count,
            playwright_pages=playwright_pages_count,
        ),
    )
