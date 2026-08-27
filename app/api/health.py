from fastapi import APIRouter

from app.config import DATABASE_URL, PLAYWRIGHT_ENABLED
from app.jobs.manager import manager

router = APIRouter(prefix="/api")


@router.get("/health")
async def health():
    """Liveness probe the launcher polls before opening the browser."""
    return {"status": "ok"}


@router.get("/status")
async def status():
    jobs = manager.list()
    active = [j for j in jobs if j.status in ("starting", "crawling")]
    return {
        "status": "ok",
        "version": "0.1.0",
        "playwright_enabled": PLAYWRIGHT_ENABLED,
        "database_url": DATABASE_URL,
        "active_jobs": len(active),
        "total_jobs": len(jobs),
    }
