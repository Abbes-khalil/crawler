import uuid

from fastapi import APIRouter, HTTPException

from app.config import MAX_BATCH_WEBSITES
from app.jobs.queue import enqueue_company_crawl, is_queue_enabled
from app.models.job import (
    BatchJobCompanyStatus,
    BatchJobStatus,
    CrawlBatchRequest,
    CrawlBatchResponse,
)
from app.storage.db import is_persistence_enabled
from app.storage.jobs import create_batch_job, get_batch_job


router = APIRouter()


def _require_batch_infrastructure() -> None:
    if not is_queue_enabled():
        raise HTTPException(
            status_code=503,
            detail=(
                "Batch crawling requires REDIS_URL to be configured - "
                "set it and run `rq worker` to process jobs."
            ),
        )

    if not is_persistence_enabled():
        raise HTTPException(
            status_code=503,
            detail=(
                "Batch crawling requires DATABASE_URL to be configured - "
                "job history is stored in Postgres/Supabase."
            ),
        )


@router.post(
    "/crawl-batch",
    response_model=CrawlBatchResponse,
    status_code=202,
)
async def crawl_batch_endpoint(request: CrawlBatchRequest):
    _require_batch_infrastructure()

    if len(request.websites) > MAX_BATCH_WEBSITES:
        raise HTTPException(
            status_code=422,
            detail=f"A batch may contain at most {MAX_BATCH_WEBSITES} websites.",
        )

    from app.storage.db import get_session

    job_id = str(uuid.uuid4())

    session = get_session()
    try:
        create_batch_job(session, job_id, request.websites)
    finally:
        session.close()

    for website in request.websites:
        enqueue_company_crawl(job_id, website, request.max_pages)

    return CrawlBatchResponse(
        job_id=job_id,
        status="QUEUED",
        total_companies=len(request.websites),
    )


@router.get(
    "/jobs/{job_id}",
    response_model=BatchJobStatus,
)
async def get_job_endpoint(job_id: str):
    if not is_persistence_enabled():
        raise HTTPException(
            status_code=503,
            detail="Job history requires DATABASE_URL to be configured.",
        )

    from app.storage.db import get_session

    session = get_session()
    try:
        job = get_batch_job(session, job_id)

        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")

        return BatchJobStatus(
            job_id=job.id,
            status=job.status,
            total_companies=job.total_companies,
            completed_companies=job.completed_companies,
            failed_companies=job.failed_companies,
            created_at=job.created_at,
            completed_at=job.completed_at,
            companies=[
                BatchJobCompanyStatus(
                    website=c.website,
                    status=c.status,
                    crawl_status=c.crawl_status,
                    canonical_url=c.canonical_url,
                    pages_crawled=c.pages_crawled,
                    observations_count=c.observations_count,
                    error=c.error,
                    started_at=c.started_at,
                    completed_at=c.completed_at,
                )
                for c in job.companies
            ],
        )
    finally:
        session.close()
