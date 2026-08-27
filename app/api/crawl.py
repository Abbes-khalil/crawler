from fastapi import APIRouter

from app.jobs.manager import manager
from app.models.request import CrawlCompanyRequest

router = APIRouter(prefix="/api")


@router.post("/crawl", status_code=202)
async def start_crawl(request: CrawlCompanyRequest):
    """Start a crawl in the background. Returns immediately with a job id;
    poll ``GET /api/jobs/{id}`` for status, progress, and the result."""
    job = manager.create(request.website, request.max_pages)
    return job.to_public()
