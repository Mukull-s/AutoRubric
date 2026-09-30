from fastapi import APIRouter, Depends, HTTPException
from ..deps import get_current_user
from autorubric.contracts import JobStatus
from datetime import datetime

router = APIRouter()

@router.get("/{job_id}")
async def get_job_status(job_id: str, current_user: dict = Depends(get_current_user)):
    # Mocking status
    return {
        "job_id": job_id,
        "status": JobStatus.DONE,
        "error": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "events": []
    }

@router.post("/{job_id}/retry")
async def retry_job(job_id: str, current_user: dict = Depends(get_current_user)):
    # Mocking retry logic
    return {"message": "Job requeued", "job_id": job_id}
