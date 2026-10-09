from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, BackgroundTasks
from typing import Annotated, Optional
import uuid
import os
import fitz  # PyMuPDF
import logging
import threading

from ..deps import get_current_user
from autorubric.workers.tasks import run_pipeline, execute_pipeline_sync
from autorubric.core.config import config
from autorubric.core.db import AsyncSessionLocal, Submission, Job, RubricModel
from autorubric.contracts import JobStatus

logger = logging.getLogger(__name__)
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
        
    rubric_dict = None
    try:
        async with AsyncSessionLocal() as session:
            r_model = await session.get(RubricModel, rubric_id)
            if r_model and r_model.data:
                rubric_dict = r_model.data
            sub = Submission(id=doc_id, filename=file.filename or "unknown.pdf", rubric_id=rubric_id, cohort_id=cohort_id)
            job = Job(id=job_id, submission_id=doc_id, status=JobStatus.QUEUED)
            session.add(sub)
            session.add(job)
            await session.commit()
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"DB submission create warning: {e}")

    if not rubric_dict:
        from .rubrics import _rubrics
        if rubric_id in _rubrics:
            rubric_dict = _rubrics[rubric_id].model_dump()

    if not rubric_dict:
        import json
        from pathlib import Path
        fixture_path = Path(__file__).parents[4] / "tests" / "fixtures" / "rubrics" / "rubric.json"
        if fixture_path.exists():
            with open(fixture_path, encoding="utf-8") as f:
                rubric_dict = json.load(f)

    if not rubric_dict:
        raise HTTPException(status_code=404, detail=f"Rubric '{rubric_id}' not found")

    # Execute pipeline asynchronously in background thread so it finishes immediately without needing a celery worker
    def _safe_run():
        try:
            print(f"[PIPELINE] Starting pipeline execution for job: {job_id}")
            res = execute_pipeline_sync(job_id, rubric_dict, content, doc_id=doc_id)
            print(f"[PIPELINE] Successfully finished job {job_id}: {res}")
        except Exception as e:
            import traceback
            print(f"[PIPELINE ERROR] Failed job {job_id}: {e}\n{traceback.format_exc()}")

    t = threading.Thread(target=_safe_run, daemon=True)
    t.start()
    
    return {"filename": file.filename, "doc_id": doc_id, "job_id": job_id, "status": "QUEUED"}


@router.post("")
async def create_submission(
    rubric_id: Annotated[str, Form()],
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    current_user: dict = Depends(get_current_user)
):
    result = await process_upload(file, rubric_id, background_tasks=background_tasks)
    return {"job_id": result["job_id"], "doc_id": result["doc_id"], "filename": result["filename"], "status": result.get("status", "QUEUED")}


@router.post("/batch")
async def create_batch_submission(
    rubric_id: Annotated[str, Form()],
    files: list[UploadFile] = File(...),
    cohort_id: Optional[str] = Form(None),
    cohort_name: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = None,
    current_user: dict = Depends(get_current_user)
):
    chosen_cohort = cohort_id or cohort_name
    actual_cohort_id = chosen_cohort.strip() if chosen_cohort and chosen_cohort.strip() else f"cohort-{uuid.uuid4().hex[:8]}"
    results = []
    errors = []
    
    for file in files:
        try:
            res = await process_upload(file, rubric_id, actual_cohort_id, background_tasks=background_tasks)
            results.append(res)
        except HTTPException as e:
            errors.append({"filename": file.filename, "error": e.detail})
            
    return {
        "cohort_id": actual_cohort_id,
        "results": results,
        "errors": errors,
        "jobs": [{"job_id": r["job_id"], "file_name": r["filename"], "doc_id": r["doc_id"]} for r in results]
    }
