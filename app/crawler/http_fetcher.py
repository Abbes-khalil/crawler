import asyncio

import httpx

from app.config import (
    CRAWLER_USER_AGENT,
    REQUEST_RETRY_COUNT,
    REQUEST_TIMEOUT,
)


def build_http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT,
        follow_redirects=True,
        headers={"User-Agent": CRAWLER_USER_AGENT},
    )


async def fetch_page(
    url: str,
    client: httpx.AsyncClient,
) -> tuple[int, str]:
    """Fetch a page. Raises httpx exceptions on network-level failures
    (timeout, connection error) so the caller can classify them.
    HTTP error status codes (4xx/5xx) are returned, not raised, so the
    caller can decide how to treat a failed page.

    Retries transient network failures (timeout/connect) up to
    REQUEST_RETRY_COUNT times with a short fixed delay before giving
    up - no exponential backoff yet, that is Sprint 3 scope."""
    attempts = REQUEST_RETRY_COUNT + 1
    last_error: Exception | None = None

    for attempt in range(attempts):
        try:
            response = await client.get(url)
            return response.status_code, response.text
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            last_error = exc

            if attempt < attempts - 1:
                await asyncio.sleep(0.5)

    raise last_error
