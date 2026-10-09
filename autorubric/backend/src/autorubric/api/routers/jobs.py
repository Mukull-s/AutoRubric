from fastapi import APIRouter, Depends, HTTPException
from ..deps import get_current_user
from autorubric.contracts import JobStatus
from datetime import datetime

router = APIRouter()

@router.get("/{job_id}")
async def get_job_status(job_id: str, current_user: dict = Depends(get_current_user)):
    from autorubric.core.db import AsyncSessionLocal, Job, JobEvent
    from sqlalchemy import select

    try:
        async with AsyncSessionLocal() as session:
            job = await session.get(Job, job_id)
            if job:
                events_res = await session.execute(
                    select(JobEvent).where(JobEvent.job_id == job_id).order_by(JobEvent.started_at)
                )
                events = [
                    {
                        "stage": e.stage,
                        "started_at": e.started_at.isoformat() if e.started_at else None,
                        "finished_at": e.finished_at.isoformat() if e.finished_at else None,
                        "ok": e.ok,
                        "error": e.error,
                    }
                    for e in events_res.scalars().all()
                ]
                return {
                    "job_id": job.id,
                    "submission_id": job.submission_id,
                    "doc_id": job.submission_id,
                    "status": job.status,
                    "error": job.error,
                    "created_at": job.created_at.isoformat() if job.created_at else datetime.utcnow().isoformat(),
                    "updated_at": job.updated_at.isoformat() if job.updated_at else datetime.utcnow().isoformat(),
                    "events": events,
                }
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Job storage is unavailable: {exc}") from exc

    raise HTTPException(status_code=404, detail="Job not found")

@router.post("/{job_id}/retry")
async def retry_job(job_id: str, current_user: dict = Depends(get_current_user)):
    # Mocking retry logic
    return {"message": "Job requeued", "job_id": job_id}
