from fastapi import APIRouter, Depends, HTTPException
from ..deps import get_current_user
from autorubric.contracts import CollusionReport, JobStatus
from autorubric.core.db import AsyncSessionLocal, Submission, Job, Result
from sqlalchemy import select, func
import json
from pathlib import Path

router = APIRouter()

@router.get("/{cohort_id}")
async def get_cohort(cohort_id: str, current_user: dict = Depends(get_current_user)):
    async with AsyncSessionLocal() as session:
        # Get counts by status
        stmt = (
            select(Job.status, func.count(Job.id))
            .join(Submission, Job.submission_id == Submission.id)
            .where(Submission.cohort_id == cohort_id)
            .group_by(Job.status)
        )
        status_counts = dict(await session.execute(stmt))
        
        # Get list of docs with score and needs-review flag
        stmt = (
            select(Submission.id, Submission.filename, Job.status, Result.total_score, Result.needs_review)
            .join(Job, Submission.id == Job.submission_id)
            .outerjoin(Result, Submission.id == Result.doc_id)
            .where(Submission.cohort_id == cohort_id)
        )
        docs = []
        for row in await session.execute(stmt):
            docs.append({
                "doc_id": row.id,
                "filename": row.filename,
                "status": row.status.value,
                "score": row.total_score,
                "needs_review": row.needs_review
            })
            
        if not docs and not status_counts:
            raise HTTPException(status_code=404, detail="Cohort not found")
            
        return {
            "cohort_id": cohort_id,
            "status_counts": {status.value: count for status, count in status_counts.items()},
            "docs": docs
        }


@router.get("/{cohort_id}/collusion")
async def get_collusion(cohort_id: str, current_user: dict = Depends(get_current_user)):
    from autorubric.audit import detect
    from autorubric.core.db import JobArtifact, CollusionCache
    import hashlib
    
    async with AsyncSessionLocal() as session:
        # Get DONE or NEEDS_REVIEW docs
        stmt = (
            select(Submission.id)
            .join(Job, Submission.id == Job.submission_id)
            .where(Submission.cohort_id == cohort_id)
            .where(Job.status.in_([JobStatus.DONE, JobStatus.NEEDS_REVIEW]))
            .order_by(Submission.id)
        )
        doc_ids = [row[0] for row in await session.execute(stmt)]
        
        if len(doc_ids) < 2:
            return {"cohort_id": cohort_id, "pairs": [], "cluster_labels": {}}
            
        # Check cache
        docs_hash = hashlib.sha256(",".join(doc_ids).encode()).hexdigest()
        cache_stmt = select(CollusionCache).where(CollusionCache.cohort_id == cohort_id)
        cache_res = (await session.execute(cache_stmt)).scalar_one_or_none()
        
        if cache_res and cache_res.doc_ids_hash == docs_hash:
            return cache_res.report
            
        # Need to recompute. Fetch embeddings
        embeddings = []
        for doc_id in doc_ids:
            art_stmt = select(JobArtifact).where(
                JobArtifact.job_id == doc_id,
                JobArtifact.stage == "segment"
            )
            art = (await session.execute(art_stmt)).scalar_one_or_none()
            if art and "embeddings" in art.payload:
                embeddings.append({
                    "doc_id": doc_id,
                    "embeddings": art.payload["embeddings"]
                })
                
        report = detect(embeddings)
        report_dict = report.model_dump()
        
        # Save cache
        if cache_res:
            cache_res.doc_ids_hash = docs_hash
            cache_res.report = report_dict
        else:
            session.add(CollusionCache(
                cohort_id=cohort_id,
                doc_ids_hash=docs_hash,
                report=report_dict
            ))
        await session.commit()
        
        return report_dict
