from fastapi import APIRouter, Depends, File, UploadFile, Form
from ..deps import get_current_user
from autorubric.workers.tasks import run_pipeline
import uuid
from typing import Annotated

router = APIRouter()

@router.post("")
async def create_submission(
    rubric_id: Annotated[str, Form()],
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    job_id = f"job-{uuid.uuid4()}"
    content = await file.read()
    
    # In a real app we'd fetch the rubric from DB
    import json
    from pathlib import Path
    fixture_path = Path(__file__).parents[4] / "tests" / "fixtures" / "rubrics" / "rubric.json"
    with open(fixture_path) as f:
        rubric_dict = json.load(f)
        
    run_pipeline.delay(job_id, rubric_dict, content.hex())
    return {"job_id": job_id}
