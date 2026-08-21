import time

import redis
from rq import Queue, Retry

from app.config import (
    JOB_RETRY_INTERVALS_SECONDS,
    JOB_RETRY_MAX,
    PER_DOMAIN_RATE_LIMIT_MAX_WAIT_SECONDS,
    PER_DOMAIN_RATE_LIMIT_SECONDS,
    REDIS_URL,
    RQ_QUEUE_NAME,
)


_redis_conn = None


def is_queue_enabled() -> bool:
    return bool(REDIS_URL)


def get_redis_connection():
    global _redis_conn

    if _redis_conn is None:
        _redis_conn = redis.Redis.from_url(REDIS_URL)

    return _redis_conn


def get_queue() -> Queue:
    return Queue(RQ_QUEUE_NAME, connection=get_redis_connection())


def enqueue_company_crawl(job_id: str, website: str, max_pages: int):
    from app.jobs.tasks import run_company_crawl_job

    queue = get_queue()

    return queue.enqueue(
        run_company_crawl_job,
        job_id,
        website,
        max_pages,
        retry=Retry(
            max=JOB_RETRY_MAX, interval=JOB_RETRY_INTERVALS_SECONDS
        ),
        job_timeout="10m",
    )


def acquire_domain_slot(domain: str) -> bool:
    """Best-effort per-domain rate limit shared across workers via
    Redis. Waits up to PER_DOMAIN_RATE_LIMIT_MAX_WAIT_SECONDS for a
    slot; if the domain stays busy the whole time, proceeds anyway
    rather than blocking a worker forever - polite by default, not a
    hard guarantee."""
    conn = get_redis_connection()
    key = f"ratelimit:domain:{domain}"

    deadline = time.monotonic() + PER_DOMAIN_RATE_LIMIT_MAX_WAIT_SECONDS

    while time.monotonic() < deadline:
        acquired = conn.set(
            key, "1", nx=True, ex=int(PER_DOMAIN_RATE_LIMIT_SECONDS) or 1
        )

        if acquired:
            return True

        time.sleep(0.5)

    return False


def domain_from_website(website: str) -> str:
    host = website.split("//")[-1].split("/")[0]

    return host.lower()
