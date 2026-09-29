from fastapi import APIRouter, Depends, HTTPException
from autorubric.contracts import Rubric
from ..deps import get_current_user

router = APIRouter()

# In-memory store for stubs
_rubrics = {}

@router.post("")
async def create_rubric(rubric: Rubric, current_user: dict = Depends(get_current_user)):
    _rubrics[rubric.id] = rubric
    return rubric

@router.get("/{rubric_id}")
async def get_rubric(rubric_id: str, current_user: dict = Depends(get_current_user)):
    if rubric_id not in _rubrics:
        # Return a mock rubric if not found for testing
        import json
        from pathlib import Path
        fixture_path = Path(__file__).parents[4] / "tests" / "fixtures" / "rubrics" / "rubric.json"
        with open(fixture_path) as f:
            return Rubric.model_validate(json.load(f))
    return _rubrics[rubric_id]
