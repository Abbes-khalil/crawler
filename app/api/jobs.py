from fastapi import APIRouter, HTTPException

from app.jobs.manager import manager

router = APIRouter(prefix="/api")


@router.get("/jobs")
async def list_jobs():
    return [job.to_public() for job in manager.list()]


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    job = manager.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_public(include_result=True)


@router.post("/jobs/{job_id}/cancel", status_code=202)
async def cancel_job(job_id: str):
    job = manager.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if not manager.cancel(job_id):
        raise HTTPException(
            status_code=409,
            detail=f"Job is already {job.status} and cannot be cancelled",
        )
    return {"status": "cancelling"}
