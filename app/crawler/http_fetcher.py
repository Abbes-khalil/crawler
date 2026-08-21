import httpx

from app.config import (
    CRAWLER_USER_AGENT,
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
    caller can decide how to treat a failed page."""
    response = await client.get(url)

    return response.status_code, response.text
