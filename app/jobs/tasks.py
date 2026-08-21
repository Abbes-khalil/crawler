import asyncio
import logging

from rq import get_current_job

from app.crawler.orchestrator import crawl_company
from app.jobs.queue import acquire_domain_slot, domain_from_website
from app.storage import persist_crawl_result
from app.storage.db import get_session
from app.storage.jobs import mark_company_started, record_company_result


logger = logging.getLogger(__name__)

FAILURE_CRAWL_STATUSES = {
    "DEAD_DOMAIN", "TIMEOUT", "BLOCKED", "HTTP_ERROR",
    "INVALID_URL", "ROBOTS_DENIED", "INSUFFICIENT_CONTENT",
}


def _retries_remaining() -> bool:
    """True if RQ will automatically re-run this job after the current
    attempt fails - i.e. we should NOT record a final result yet, to
    avoid double-counting the company across attempts. Returns False
    (record now) when not running inside an RQ worker at all, e.g. in
    tests calling this function directly."""
    job = get_current_job()

    if job is None:
        return False

    return bool(job.retries_left and job.retries_left > 0)


def run_company_crawl_job(
    job_id: str,
    website: str,
    max_pages: int,
) -> None:
    """Executed by an `rq worker` process - synchronous entry point
    that runs the async crawl pipeline to completion. One call = one
    company. Only records a terminal DB result once RQ has no retries
    left for this job, so a transient failure that succeeds on retry
    is never double-counted."""
    session = get_session()

    try:
        mark_company_started(session, job_id, website)

        acquire_domain_slot(domain_from_website(website))

        response = asyncio.run(crawl_company(website, max_pages))

        persist_crawl_result(response)

        status = (
            "FAILED"
            if response.status in FAILURE_CRAWL_STATUSES
            else "SUCCESS"
        )

        record_company_result(
            session,
            job_id,
            website,
            status=status,
            crawl_status=response.status,
            canonical_url=response.canonical_url,
            pages_crawled=response.pages_crawled,
            observations_count=len(response.observations),
        )
    except Exception as exc:
        logger.exception("Batch crawl failed for %s (job %s)", website, job_id)

        if not _retries_remaining():
            record_company_result(
                session,
                job_id,
                website,
                status="FAILED",
                error=str(exc),
            )

        raise
    finally:
        session.close()
