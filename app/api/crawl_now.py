"""Synchronous crawl endpoint for the hosted single-page tool.

Unlike ``POST /api/crawl`` (which queues an in-memory background job and is
polled via ``/api/jobs``), this runs the crawl inline and returns the result
in one response - a shape that fits a stateless serverless deployment with
no database. The response carries a ready-to-paste Markdown block plus the
structured data.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.api.guard import rate_limit, require_token
from app.crawler.orchestrator import crawl_company
from app.formatting import to_markdown
from app.models.request import CrawlCompanyRequest

router = APIRouter(prefix="/api")

# Hosted on a free tier with a ~60s function limit: keep crawls small.
HOSTED_MAX_PAGES = 8


@router.post("/crawl-now")
async def crawl_now(
    body: CrawlCompanyRequest,
    request: Request,
    _token: None = Depends(require_token),
    _rate: None = Depends(rate_limit),
) -> dict:
    max_pages = min(body.max_pages, HOSTED_MAX_PAGES)
    result = await crawl_company(body.website, max_pages)
    return {
        "text": to_markdown(result),
        "data": result.model_dump(mode="json"),
    }
