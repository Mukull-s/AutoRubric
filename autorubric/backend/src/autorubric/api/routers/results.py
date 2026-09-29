from fastapi import APIRouter, Depends, HTTPException, Response
from ..deps import get_current_user
from autorubric.contracts import ScoreResult
import json
from pathlib import Path

router = APIRouter()

@router.get("/{doc_id}")
async def get_result(doc_id: str, current_user: dict = Depends(get_current_user)):
    fixture_path = Path(__file__).parents[4] / "tests" / "fixtures" / "scorer" / "score_result.json"
    with open(fixture_path) as f:
        data = json.load(f)
    return ScoreResult.model_validate(data)

@router.get("/{doc_id}/pdf")
async def get_result_pdf(doc_id: str, current_user: dict = Depends(get_current_user)):
    fixture_path = Path(__file__).parents[4] / "tests" / "fixtures" / "annotation" / "annotated.pdf"
    with open(fixture_path, "rb") as f:
        content = f.read()
    return Response(content=content, media_type="application/pdf")
