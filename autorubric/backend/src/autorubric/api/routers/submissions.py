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

async def process_upload(
    file: UploadFile,
    rubric_id: str,
    cohort_id: Optional[str] = None,
    background_tasks: Optional[BackgroundTasks] = None
) -> dict:
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
    
    # Retrieve the actual selected rubric from DB or in-memory store
    rubric_dict = None
    try:
        from autorubric.core.db import RubricModel
        from sqlalchemy import select
        async with AsyncSessionLocal() as session:
            res = await session.execute(select(RubricModel).where(RubricModel.id == rubric_id))
            row = res.scalar_one_or_none()
            if row:
                rubric_dict = row.data
    except Exception:
        pass

    if not rubric_dict:
        from .rubrics import _rubrics
        if rubric_id in _rubrics:
            rubric_dict = _rubrics[rubric_id].model_dump()

    if not rubric_dict:
        import json
        from pathlib import Path
        fixture_path = Path(__file__).parents[4] / "tests" / "fixtures" / "rubrics" / "rubric.json"
        if fixture_path.exists():
            with open(fixture_path) as f:
                rubric_dict = json.load(f)

    # Execute pipeline asynchronously in background thread so it finishes immediately without needing celery worker
    def _safe_run():
        try:
            print(f"[PIPELINE] Starting pipeline execution for job: {job_id}")
            from autorubric.workers.tasks import execute_pipeline_sync
            res = execute_pipeline_sync(job_id, rubric_dict, content, doc_id)
            print(f"[PIPELINE] Successfully finished job {job_id}: {res}")
        except Exception as e:
            import traceback
            print(f"[PIPELINE ERROR] Failed job {job_id}: {e}\n{traceback.format_exc()}")

    import threading
    t = threading.Thread(target=_safe_run, daemon=True)
    t.start()
    
    return {"filename": file.filename, "doc_id": doc_id, "job_id": job_id}

@router.post("")
async def create_submission(
    rubric_id: Annotated[str, Form()],
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    current_user: dict = Depends(get_current_user)
):
    result = await process_upload(file, rubric_id, background_tasks=background_tasks)
    return {"job_id": result["job_id"]}

@router.post("/batch")
async def create_batch_submission(
    rubric_id: Annotated[str, Form()],
    files: list[UploadFile] = File(...),
    cohort_id: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = None,
    current_user: dict = Depends(get_current_user)
):
    results = []
    errors = []
    
    for file in files:
        try:
            res = await process_upload(file, rubric_id, cohort_id, background_tasks=background_tasks)
            results.append(res)
        except HTTPException as e:
            errors.append({"filename": file.filename, "error": e.detail})
            
    return {"results": results, "errors": errors}
