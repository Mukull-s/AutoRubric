from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, BackgroundTasks
from typing import Annotated, Optional
import uuid
import os
import fitz  # PyMuPDF
from ..deps import get_current_user
from autorubric.workers.tasks import run_pipeline
from autorubric.core.config import config
from autorubric.core.db import AsyncSessionLocal, Submission, Job
from autorubric.contracts import JobStatus

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_PAGES = 50

def validate_pdf(content: bytes) -> None:
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")
        
    if not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="Invalid PDF magic bytes")
        
    try:
        doc = fitz.open(stream=content, filetype="pdf")
    except Exception:
        raise HTTPException(status_code=400, detail="Could not parse PDF")
        
    if doc.is_encrypted:
        doc.close()
        raise HTTPException(status_code=400, detail="PDF is encrypted")
        
    if doc.page_count > MAX_PAGES:
        doc.close()
        raise HTTPException(status_code=400, detail=f"PDF has too many pages (max {MAX_PAGES})")
        
    doc.close()

async def process_upload(file: UploadFile, rubric_id: str, cohort_id: Optional[str] = None) -> dict:
    content = await file.read()
    validate_pdf(content)
    
    doc_id = f"doc-{uuid.uuid4()}"
    job_id = f"job-{uuid.uuid4()}"
    
    os.makedirs(config.UPLOADS_DIR, exist_ok=True)
    file_path = os.path.join(config.UPLOADS_DIR, f"{doc_id}.pdf")
    with open(file_path, "wb") as f:
        f.write(content)
        
    async with AsyncSessionLocal() as session:
        sub = Submission(id=doc_id, filename=file.filename or "unknown.pdf", rubric_id=rubric_id, cohort_id=cohort_id)
        job = Job(id=job_id, submission_id=doc_id, status=JobStatus.QUEUED)
        session.add(sub)
        session.add(job)
        await session.commit()
    
    # In a real app we'd fetch the rubric from DB
    import json
    from pathlib import Path
    fixture_path = Path(__file__).parents[4] / "tests" / "fixtures" / "rubrics" / "rubric.json"
    with open(fixture_path) as f:
        rubric_dict = json.load(f)
        
    run_pipeline.delay(job_id, rubric_dict, content.hex())
    
    return {"filename": file.filename, "doc_id": doc_id, "job_id": job_id}

@router.post("")
async def create_submission(
    rubric_id: Annotated[str, Form()],
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    result = await process_upload(file, rubric_id)
    return {"job_id": result["job_id"]}

@router.post("/batch")
async def create_batch_submission(
    rubric_id: Annotated[str, Form()],
    files: list[UploadFile] = File(...),
    cohort_id: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    results = []
    errors = []
    
    for file in files:
        try:
            res = await process_upload(file, rubric_id, cohort_id)
            results.append(res)
        except HTTPException as e:
            errors.append({"filename": file.filename, "error": e.detail})
            
    return {"results": results, "errors": errors}
