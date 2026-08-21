"""Worker entrypoint: `python -m app.jobs.worker`.

On Linux/Docker, `rq worker crawl` works directly (fork + SIGALRM based
timeouts are available). On Windows, RQ's default worker relies on
os.fork() and SIGALRM, neither of which exist there, so this uses
SimpleWorker (no fork - runs jobs in-process) with TimerDeathPenalty
(thread-based timeout, no SIGALRM) instead. Same task code either way.
"""
from rq import Queue, SimpleWorker
from rq.timeouts import TimerDeathPenalty

from app.config import RQ_QUEUE_NAME
from app.jobs.queue import get_redis_connection


class WindowsSafeWorker(SimpleWorker):
    death_penalty_class = TimerDeathPenalty


def main():
    connection = get_redis_connection()
    queue = Queue(RQ_QUEUE_NAME, connection=connection)

    worker = WindowsSafeWorker([queue], connection=connection)
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
