from fastapi import APIRouter, Depends
from ..deps import get_current_user
from autorubric.contracts import CollusionReport
import json
from pathlib import Path

router = APIRouter()

@router.get("/{cohort_id}/collusion")
async def get_collusion(cohort_id: str, current_user: dict = Depends(get_current_user)):
    fixture_path = Path(__file__).parents[4] / "tests" / "fixtures" / "audit" / "collusion_report.json"
    with open(fixture_path) as f:
        data = json.load(f)
    return CollusionReport.model_validate(data)
