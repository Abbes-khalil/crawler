import pytest
from fastapi import HTTPException

from app.api import guard


class _FakeClient:
    def __init__(self, host: str) -> None:
        self.host = host


class _FakeRequest:
    def __init__(self, *, query=None, headers=None, host="1.2.3.4") -> None:
        self.query_params = query or {}
        self.headers = headers or {}
        self.client = _FakeClient(host)


# --- token ---------------------------------------------------------------

def test_token_check_is_skipped_when_unset(monkeypatch):
    monkeypatch.delenv("ACCESS_TOKEN", raising=False)
    guard.require_token(_FakeRequest())  # no raise


def test_token_accepts_matching_query_param(monkeypatch):
    monkeypatch.setenv("ACCESS_TOKEN", "s3cret")
    guard.require_token(_FakeRequest(query={"k": "s3cret"}))


def test_token_accepts_matching_header(monkeypatch):
    monkeypatch.setenv("ACCESS_TOKEN", "s3cret")
    guard.require_token(_FakeRequest(headers={"x-access-key": "s3cret"}))


def test_token_rejects_missing_or_wrong(monkeypatch):
    monkeypatch.setenv("ACCESS_TOKEN", "s3cret")
    with pytest.raises(HTTPException) as exc:
        guard.require_token(_FakeRequest(query={"k": "nope"}))
    assert exc.value.status_code == 403
    with pytest.raises(HTTPException):
        guard.require_token(_FakeRequest())


# --- rate limit --------------------------------------------------------

def test_rate_limit_allows_up_to_limit_then_blocks(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_PER_HOUR", "3")
    guard.reset_rate_limit()
    req = _FakeRequest(host="9.9.9.9")

    for _ in range(3):
        guard.rate_limit(req)

    with pytest.raises(HTTPException) as exc:
        guard.rate_limit(req)
    assert exc.value.status_code == 429


def test_rate_limit_is_per_ip(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_PER_HOUR", "1")
    guard.reset_rate_limit()

    guard.rate_limit(_FakeRequest(host="10.0.0.1"))
    guard.rate_limit(_FakeRequest(host="10.0.0.2"))  # different IP, still ok
    with pytest.raises(HTTPException):
        guard.rate_limit(_FakeRequest(host="10.0.0.1"))


def test_rate_limit_window_expires(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_PER_HOUR", "1")
    guard.reset_rate_limit()
    now = [1000.0]
    monkeypatch.setattr(guard.time, "time", lambda: now[0])
    req = _FakeRequest(host="8.8.8.8")

    guard.rate_limit(req)
    now[0] += 3601  # more than an hour later
    guard.rate_limit(req)  # window cleared, allowed again
