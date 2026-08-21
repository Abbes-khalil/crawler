import fakeredis
import pytest

from app.jobs import queue


@pytest.fixture(autouse=True)
def fake_redis_connection(monkeypatch):
    fake = fakeredis.FakeRedis()
    monkeypatch.setattr(queue, "_redis_conn", fake)
    monkeypatch.setattr(queue, "get_redis_connection", lambda: fake)
    return fake


def test_domain_from_website_strips_scheme_and_path():
    assert queue.domain_from_website("https://Company.com/about") == "company.com"
    assert queue.domain_from_website("company.com") == "company.com"


def test_acquire_domain_slot_first_call_succeeds():
    assert queue.acquire_domain_slot("company.com") is True


def test_acquire_domain_slot_second_call_waits_then_times_out(monkeypatch):
    monkeypatch.setattr(queue, "PER_DOMAIN_RATE_LIMIT_SECONDS", 30)
    monkeypatch.setattr(queue, "PER_DOMAIN_RATE_LIMIT_MAX_WAIT_SECONDS", 0.1)
    monkeypatch.setattr(queue.time, "sleep", lambda _: None)

    assert queue.acquire_domain_slot("busy.example") is True
    assert queue.acquire_domain_slot("busy.example") is False


def test_is_queue_enabled_reflects_redis_url(monkeypatch):
    monkeypatch.setattr(queue, "REDIS_URL", "")
    assert queue.is_queue_enabled() is False

    monkeypatch.setattr(queue, "REDIS_URL", "redis://localhost:6379/0")
    assert queue.is_queue_enabled() is True
