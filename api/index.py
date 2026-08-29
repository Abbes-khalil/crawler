"""Vercel serverless entrypoint.

Vercel's Python runtime detects the module-level ``app`` ASGI callable and
serves it. Only ``/api/*`` requests reach this function (see ``vercel.json``
rewrites); the static frontend in ``web/out`` is served directly by Vercel.
"""

from app.main import app

__all__ = ["app"]
