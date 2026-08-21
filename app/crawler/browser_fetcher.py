from playwright.async_api import Browser, async_playwright

from app.config import (
    CRAWLER_USER_AGENT,
    PLAYWRIGHT_MIN_CONTENT_CHARS,
    PLAYWRIGHT_TIMEOUT_MS,
)
from app.extraction.cleaner import extract_clean_text


def is_content_insufficient(html: str) -> bool:
    """Heuristic for 'this HTML is a JS shell, not real content'. Avoid
    reaching for Playwright just because a site uses React/Next.js if
    server-rendered content is already present - only trigger when the
    readable text extracted from the raw HTML is clearly too thin."""
    text = extract_clean_text(html)

    return len(text.strip()) < PLAYWRIGHT_MIN_CONTENT_CHARS


class BrowserFetcher:
    """Lazily launches a single Chromium instance on first use and
    reuses it for the rest of the crawl, so we never launch a browser
    per page - only when HTTP content already proved insufficient."""

    def __init__(self):
        self._playwright = None
        self._browser: Browser | None = None

    async def _ensure_browser(self) -> Browser:
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True
            )

        return self._browser

    async def fetch(self, url: str) -> tuple[int, str]:
        browser = await self._ensure_browser()

        page = await browser.new_page(user_agent=CRAWLER_USER_AGENT)

        try:
            response = await page.goto(
                url,
                timeout=PLAYWRIGHT_TIMEOUT_MS,
                wait_until="networkidle",
            )
            html = await page.content()
            status_code = response.status if response else 200

            return status_code, html
        finally:
            await page.close()

    async def close(self):
        if self._browser is not None:
            await self._browser.close()

        if self._playwright is not None:
            await self._playwright.stop()
