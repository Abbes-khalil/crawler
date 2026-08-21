import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.storage.db import Base
from app.storage.jobs import (
    create_batch_job,
    get_batch_job,
    mark_company_started,
    record_company_result,
)


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as s:
        yield s


def test_create_batch_job_creates_queued_companies(session):
    job = create_batch_job(
        session, "job-1", ["https://a.example", "https://b.example"]
    )

    assert job.status == "QUEUED"
    assert job.total_companies == 2
    assert len(job.companies) == 2
    assert all(c.status == "QUEUED" for c in job.companies)


def test_mark_company_started_transitions_job_to_running(session):
    create_batch_job(session, "job-2", ["https://a.example"])

    mark_company_started(session, "job-2", "https://a.example")

    job = get_batch_job(session, "job-2")
    assert job.status == "RUNNING"
    assert job.companies[0].status == "RUNNING"
    assert job.companies[0].started_at is not None


def test_record_company_result_marks_job_success_when_all_succeed(session):
    create_batch_job(session, "job-3", ["https://a.example"])

    record_company_result(
        session,
        "job-3",
        "https://a.example",
        status="SUCCESS",
        crawl_status="SUCCESS",
        canonical_url="https://a.example",
        pages_crawled=5,
        observations_count=3,
    )

    job = get_batch_job(session, "job-3")
    assert job.status == "SUCCESS"
    assert job.completed_companies == 1
    assert job.failed_companies == 0
    assert job.completed_at is not None


def test_record_company_result_marks_job_partial_success(session):
    create_batch_job(
        session, "job-4", ["https://a.example", "https://b.example"]
    )

    record_company_result(
        session, "job-4", "https://a.example", status="SUCCESS"
    )
    record_company_result(
        session, "job-4", "https://b.example", status="FAILED", error="timeout"
    )

    job = get_batch_job(session, "job-4")
    assert job.status == "PARTIAL_SUCCESS"
    assert job.completed_companies == 1
    assert job.failed_companies == 1


def test_record_company_result_marks_job_failed_when_all_fail(session):
    create_batch_job(session, "job-5", ["https://a.example"])

    record_company_result(
        session, "job-5", "https://a.example", status="FAILED", error="boom"
    )

    job = get_batch_job(session, "job-5")
    assert job.status == "FAILED"


def test_get_unknown_job_returns_none(session):
    assert get_batch_job(session, "does-not-exist") is None
