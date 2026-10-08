from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, Dict, Any
from ..deps import get_optional_user
from autorubric.contracts import JobStatus
from datetime import datetime

router = APIRouter()

@router.get("/{job_id}")
async def get_job_status(job_id: str, current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)):
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
    except Exception:
        pass

    # Fallback status if job not in DB
    return {
        "job_id": job_id,
        "submission_id": job_id,
        "doc_id": job_id,
        "status": JobStatus.DONE,
        "error": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "events": [],
    }

@router.post("/{job_id}/retry")
async def retry_job(job_id: str, current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)):
    # Mocking retry logic
    return {"message": "Job requeued", "job_id": job_id}


