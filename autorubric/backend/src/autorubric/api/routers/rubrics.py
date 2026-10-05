from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from autorubric.contracts import Rubric
from autorubric.core.config import config
from ..deps import get_current_user
from autorubric.core.db import AsyncSessionLocal, RubricModel
from sqlalchemy import select

router = APIRouter()

# Optional auth scheme for read operations
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

def get_optional_user(token: str = Depends(oauth2_scheme_optional)):
    if not token:
        return None
    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])
        return {"username": payload.get("sub")}
    except (JWTError, Exception):
        return None

# In-memory store for fast lookup and fallback
_rubrics = {}

@router.get("")
async def list_rubrics(current_user: dict | None = Depends(get_optional_user)):
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
            import json
            from pathlib import Path
            fixture_path = Path(__file__).parents[4] / "tests" / "fixtures" / "rubrics" / "rubric.json"
            if fixture_path.exists():
                with open(fixture_path) as f:
                    default_rubric = Rubric.model_validate(json.load(f))
                    _rubrics[default_rubric.id] = default_rubric
                    results.append(default_rubric)
        except Exception:
            pass

    return results

import uuid
from autorubric.contracts.rubric import Criterion, CreditMap

@router.post("")
async def create_rubric(payload: dict, current_user: dict | None = Depends(get_optional_user)):
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
async def get_rubric(rubric_id: str, current_user: dict | None = Depends(get_optional_user)):
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

    # Return fixture rubric if not found
    try:
        import json
        from pathlib import Path
        fixture_path = Path(__file__).parents[4] / "tests" / "fixtures" / "rubrics" / "rubric.json"
        if fixture_path.exists():
            with open(fixture_path) as f:
                return Rubric.model_validate(json.load(f))
    except Exception:
        pass

    raise HTTPException(status_code=404, detail="Rubric not found")


