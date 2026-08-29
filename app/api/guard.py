"""Lightweight access guards for the hosted single-page crawl endpoint.

The hosted deployment is public (no login screen). Two cheap defences keep
it from being used as an open proxy or from draining a free hosting tier:

* ``require_token`` - when ``ACCESS_TOKEN`` is set, the request must carry a
  matching ``?k=`` query param or ``x-access-key`` header. When the env var
  is unset (local dev, the desktop build) the check is a no-op.
* ``rate_limit`` - an in-memory sliding window per client IP, capped at
  ``RATE_LIMIT_PER_HOUR`` (default 15). In-memory is deliberate: serverless
  instances are short-lived, so this only needs to blunt bursts.

Both are plain callables usable as FastAPI dependencies.
"""

from __future__ import annotations

import hmac
import os
import time
from collections import defaultdict

from fastapi import HTTPException, Request

_WINDOW_SECONDS = 3600
_DEFAULT_LIMIT = 15

# ip -> list of request timestamps within the current window
_hits: dict[str, list[float]] = defaultdict(list)


def reset_rate_limit() -> None:
    """Clear all recorded hits (used by tests)."""
    _hits.clear()


def _limit() -> int:
    try:
        return max(1, int(os.getenv("RATE_LIMIT_PER_HOUR", str(_DEFAULT_LIMIT))))
    except ValueError:
        return _DEFAULT_LIMIT


def require_token(request: Request) -> None:
    expected = os.getenv("ACCESS_TOKEN") or ""
    if not expected:
        return
    provided = request.query_params.get("k") or request.headers.get("x-access-key") or ""
    if not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=403, detail="Invalid or missing access key.")


def rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    recent = [t for t in _hits[ip] if now - t < _WINDOW_SECONDS]
    if len(recent) >= _limit():
        _hits[ip] = recent
        raise HTTPException(
            status_code=429,
            detail="Rate limit reached. Try again later.",
        )
    recent.append(now)
    _hits[ip] = recent
