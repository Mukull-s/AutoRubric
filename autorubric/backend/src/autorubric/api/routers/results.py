from fastapi import APIRouter, Depends, HTTPException, Response
from ..deps import get_current_user
from autorubric.contracts import ScoreResult, Rubric, Classification, CriticVerdict
from autorubric.scorer import score, SCORER_VERSION
import json
from pathlib import Path
from pydantic import BaseModel

router = APIRouter()

@router.get("/{doc_id}")
async def get_result(doc_id: str, current_user: dict = Depends(get_current_user)):
    from autorubric.core.db import AsyncSessionLocal, Result
    from sqlalchemy import select
    from autorubric.core.config import config
    import os
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Result).where(Result.doc_id == doc_id))
        res = result.scalar_one_or_none()
        if not res:
            raise HTTPException(status_code=404, detail="Result not found")
            
        data = res.data
        pdf_path = os.path.join(config.UPLOADS_DIR, f"{doc_id}_annotated.pdf")
        data["annotated_pdf_available"] = os.path.exists(pdf_path)
        data["needs_review"] = res.needs_review
        
        return data

@router.get("/{doc_id}/pdf")
async def get_result_pdf(doc_id: str, current_user: dict = Depends(get_current_user)):
    from fastapi.responses import FileResponse
    from autorubric.core.config import config
    import os
    
    pdf_path = os.path.join(config.UPLOADS_DIR, f"{doc_id}_annotated.pdf")
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF not found")
        
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"{doc_id}_annotated.pdf")

class VerifyResponse(BaseModel):
    match: bool
    differences: list[str]

@router.post("/{doc_id}/verify", response_model=VerifyResponse)
async def verify_result(doc_id: str, current_user: dict = Depends(get_current_user)):
    # Mocking verify logic using fixture data
    fixture_path = Path(__file__).parents[4] / "tests" / "fixtures" / "scorer" / "score_result.json"
    with open(fixture_path) as f:
        data = json.load(f)
    original_score = ScoreResult.model_validate(data)
    
    rubric_fixture = Path(__file__).parents[4] / "tests" / "fixtures" / "rubrics" / "rubric.json"
    classifications_fixture = Path(__file__).parents[4] / "tests" / "fixtures" / "evaluator" / "classifications.json"
    verdicts_fixture = Path(__file__).parents[4] / "tests" / "fixtures" / "audit" / "critic_verdicts.json"
    
    with open(rubric_fixture) as f: rubric = Rubric.model_validate(json.load(f))
    with open(classifications_fixture) as f: classifications = [Classification.model_validate(i) for i in json.load(f)]
    with open(verdicts_fixture) as f: verdicts = [CriticVerdict.model_validate(i) for i in json.load(f)]
    
    new_score = score(classifications, rubric, verdicts)
    new_score.doc_id = doc_id
    
    if new_score.model_dump() == original_score.model_dump():
        return {"match": True, "differences": []}
    return {"match": False, "differences": ["Mismatched scores"]}
