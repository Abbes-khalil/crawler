from typing import Literal

from pydantic import BaseModel

from app.models.observation import Observation
from app.models.page import CrawledPage, PageError


CrawlStatus = Literal[
    "SUCCESS",
    "PARTIAL_SUCCESS",
    "INVALID_URL",
    "DEAD_DOMAIN",
    "TIMEOUT",
    "BLOCKED",
    "ROBOTS_DENIED",
    "CAPTCHA",
    "INSUFFICIENT_CONTENT",
    "HTTP_ERROR",
]


class CrawlMetrics(BaseModel):
    duration_ms: int
    http_pages: int
    playwright_pages: int = 0


class CrawlCompanyResponse(BaseModel):
    status: CrawlStatus
    canonical_url: str

    pages_discovered: int
    pages_selected: int
    pages_crawled: int
    pages_failed: int

    pages: list[CrawledPage]
    page_errors: list[PageError]
    observations: list[Observation]

    metrics: CrawlMetrics
