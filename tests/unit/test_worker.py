from rq.timeouts import TimerDeathPenalty

from app.jobs.worker import WindowsSafeWorker


def test_windows_safe_worker_uses_timer_death_penalty():
    assert WindowsSafeWorker.death_penalty_class is TimerDeathPenalty
