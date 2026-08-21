from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.storage.db import BatchJob, BatchJobCompany


def create_batch_job(
    session: Session,
    job_id: str,
    websites: list[str],
) -> BatchJob:
    job = BatchJob(
        id=job_id,
        status="QUEUED",
        total_companies=len(websites),
        completed_companies=0,
        failed_companies=0,
    )
    session.add(job)

    for website in websites:
        session.add(
            BatchJobCompany(
                batch_job_id=job_id,
                website=website,
                status="QUEUED",
            )
        )

    session.commit()

    return job


def get_batch_job(session: Session, job_id: str) -> BatchJob | None:
    return session.execute(
        select(BatchJob).where(BatchJob.id == job_id)
    ).scalar_one_or_none()


def mark_company_started(
    session: Session,
    job_id: str,
    website: str,
) -> None:
    company = session.execute(
        select(BatchJobCompany).where(
            BatchJobCompany.batch_job_id == job_id,
            BatchJobCompany.website == website,
        )
    ).scalar_one_or_none()

    if company is None:
        return

    company.status = "RUNNING"
    company.started_at = datetime.now(timezone.utc)

    job = get_batch_job(session, job_id)

    if job is not None and job.status == "QUEUED":
        job.status = "RUNNING"

    session.commit()


def record_company_result(
    session: Session,
    job_id: str,
    website: str,
    *,
    status: str,
    crawl_status: str | None = None,
    canonical_url: str | None = None,
    pages_crawled: int | None = None,
    observations_count: int | None = None,
    error: str | None = None,
) -> None:
    company = session.execute(
        select(BatchJobCompany).where(
            BatchJobCompany.batch_job_id == job_id,
            BatchJobCompany.website == website,
        )
    ).scalar_one_or_none()

    if company is None:
        return

    company.status = status
    company.crawl_status = crawl_status
    company.canonical_url = canonical_url
    company.pages_crawled = pages_crawled
    company.observations_count = observations_count
    company.error = error
    company.completed_at = datetime.now(timezone.utc)

    job = get_batch_job(session, job_id)

    if job is not None:
        if status == "FAILED":
            job.failed_companies += 1
        else:
            job.completed_companies += 1

        finished = job.completed_companies + job.failed_companies

        if finished >= job.total_companies:
            job.status = (
                "SUCCESS" if job.failed_companies == 0 else "PARTIAL_SUCCESS"
            )

            if job.failed_companies == job.total_companies:
                job.status = "FAILED"

            job.completed_at = datetime.now(timezone.utc)

    session.commit()
