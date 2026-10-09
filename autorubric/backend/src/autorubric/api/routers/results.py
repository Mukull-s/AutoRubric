from fastapi import APIRouter, Depends, HTTPException, Response
from ..deps import get_current_user
from autorubric.contracts import ScoreResult, Rubric, Classification, CriticVerdict
from autorubric.scorer import score, SCORER_VERSION
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
    from autorubric.core.db import AsyncSessionLocal, Result
    from sqlalchemy import select
    
    # Attempt verification using real stored audit bundle
    try:
        async with AsyncSessionLocal() as session:
            res = (await session.execute(select(Result).where(Result.doc_id == doc_id))).scalar_one_or_none()
            if res and res.audit_bundle:
                bundle = res.audit_bundle
                rubric = Rubric.model_validate(bundle["rubric"])
                classifications = [Classification.model_validate(c) for c in bundle.get("classifications", [])]
                verdicts = [CriticVerdict.model_validate(v) for v in bundle.get("verdicts", [])]
                new_score = score(classifications, rubric, verdicts)
                new_score.doc_id = doc_id
                
                diffs = []
                orig_score = res.data.get("total_score", 0.0)
                if abs(new_score.total_score - orig_score) > 1e-4:
                    diffs.append(f"Score recalculation mismatch: {new_score.total_score} vs {orig_score}")
                return {"match": len(diffs) == 0, "differences": diffs}
    except Exception:
        pass

    raise HTTPException(status_code=404, detail="No audit bundle is available for this result")

@router.get("/{doc_id}/propositions")
async def get_result_propositions(doc_id: str, current_user: dict = Depends(get_current_user)):
    from autorubric.core.db import AsyncSessionLocal, Result
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Result).where(Result.doc_id == doc_id))
        res = result.scalar_one_or_none()
        if not res:
            raise HTTPException(status_code=404, detail="Result not found")
            
        data = res.data
        return {"propositions": data.get("propositions", [])}
