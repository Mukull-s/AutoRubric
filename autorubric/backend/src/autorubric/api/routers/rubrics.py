from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select

from autorubric.contracts import Rubric
from autorubric.contracts.rubric import Criterion, CreditMap
from autorubric.core.config import config
from autorubric.core.db import AsyncSessionLocal, RubricModel
from autorubric.core.security import decode_access_token

router = APIRouter()

# Optional auth scheme for read and creation operations
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)


def get_optional_user(token: Optional[str] = Depends(oauth2_scheme_optional)) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        return {"username": payload.get("sub")}
    except Exception:
        return None


# In-memory store for fast lookup and fallback
_rubrics: Dict[str, Rubric] = {}


@router.get("")
async def list_rubrics(current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)) -> List[Rubric]:
    results = list(_rubrics.values())
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(RubricModel)
            db_rubrics = (await session.execute(stmt)).scalars().all()
            for r in db_rubrics:
                if r.data and r.id not in [x.id for x in results]:
                    results.append(Rubric.model_validate(r.data))
    except Exception:
        pass

    # Ensure at least the default rubric is present
    if not results:
        try:
            fixture_path = Path(__file__).parents[4] / "tests" / "fixtures" / "rubrics" / "rubric.json"
            if fixture_path.exists():
                with open(fixture_path, encoding="utf-8") as f:
                    default_rubric = Rubric.model_validate(json.load(f))
                    _rubrics[default_rubric.id] = default_rubric
                    results.append(default_rubric)
        except Exception:
            pass

    return results


@router.post("")
async def create_rubric(payload: Dict[str, Any], current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)) -> Rubric:
    # Extract or generate ID
    rubric_id = payload.get("id") or f"r-{uuid.uuid4().hex[:6]}"
    title = payload.get("title", "Untitled Rubric")
    raw_criteria = payload.get("criteria", [])

    criteria = [Criterion.model_validate(c) for c in raw_criteria]

    # Calculate or get credit_map
    if "credit_map" in payload and isinstance(payload["credit_map"], dict):
        credit_map = CreditMap.model_validate(payload["credit_map"])
    else:
        credit_map = CreditMap()

    # Calculate max_score
    total_weight = sum(c.weight for c in criteria)
    max_score = float(payload.get("max_score") or total_weight)
    if abs(total_weight - max_score) > 1e-4:
        max_score = total_weight

    rubric = Rubric(
        id=rubric_id,
        title=title,
        criteria=criteria,
        credit_map=credit_map,
        max_score=max_score,
    )

    _rubrics[rubric.id] = rubric
    try:
        async with AsyncSessionLocal() as session:
            model = RubricModel(id=rubric.id, title=rubric.title, data=rubric.model_dump())
            await session.merge(model)
            await session.commit()
    except Exception:
        pass
    return rubric


@router.get("/{rubric_id}")
async def get_rubric(rubric_id: str, current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)) -> Rubric:
    if rubric_id in _rubrics:
        return _rubrics[rubric_id]

    try:
        async with AsyncSessionLocal() as session:
            model = await session.get(RubricModel, rubric_id)
            if model and model.data:
                rubric = Rubric.model_validate(model.data)
                _rubrics[rubric_id] = rubric
                return rubric
    except Exception:
        pass

    raise HTTPException(status_code=404, detail="Rubric not found")
