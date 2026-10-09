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
            select(Submission.id, Submission.filename, Job.id, Job.status, Result.total_score, Result.needs_review)
            .join(Job, Submission.id == Job.submission_id)
            .outerjoin(Result, Submission.id == Result.doc_id)
            .where(Submission.cohort_id == cohort_id)
        )
        docs = []
        jobs = []
        for row in await session.execute(stmt):
            sub_id, fname, j_id, j_status, score_val, needs_rev = row
            status_str = j_status.value if hasattr(j_status, "value") else str(j_status)
            docs.append({
                "doc_id": sub_id,
                "filename": fname,
                "job_id": j_id,
                "status": status_str,
                "score": score_val,
                "needs_review": needs_rev
            })
            jobs.append({
                "job_id": j_id,
                "doc_id": sub_id,
                "file_name": fname,
                "filename": fname,
                "status": status_str,
                "created_at": "",
                "updated_at": "",
                "events": [],
                "error": None
            })
            
        if not docs and not status_counts:
            raise HTTPException(status_code=404, detail="Cohort not found")
            
        return {
            "cohort_id": cohort_id,
            "id": cohort_id,
            "name": cohort_id,
            "status_counts": {status.value if hasattr(status, "value") else str(status): count for status, count in status_counts.items()},
            "docs": docs,
            "jobs": jobs
        }


@router.get("/{cohort_id}/collusion")
async def get_collusion(cohort_id: str, current_user: dict = Depends(get_current_user)):
    from autorubric.audit import detect
    from autorubric.core.db import JobArtifact, CollusionCache
    import hashlib
    
    async with AsyncSessionLocal() as session:
        # Get DONE or NEEDS_REVIEW docs
        stmt = (
            select(Submission.id, Job.id)
            .join(Job, Submission.id == Job.submission_id)
            .where(Submission.cohort_id == cohort_id)
            .where(Job.status.in_([JobStatus.DONE, JobStatus.NEEDS_REVIEW]))
            .order_by(Submission.id)
        )
        rows = (await session.execute(stmt)).all()
        doc_ids = [r[0] for r in rows]
        doc_to_job = {r[0]: r[1] for r in rows}
        
        if len(doc_ids) < 2:
            return {"cohort_id": cohort_id, "doc_pairs": [], "pairs": [], "cluster_labels": {}}
            
        # Check cache
        docs_hash = hashlib.sha256(",".join(doc_ids).encode()).hexdigest()
        cache_stmt = select(CollusionCache).where(CollusionCache.cohort_id == cohort_id)
        cache_res = (await session.execute(cache_stmt)).scalar_one_or_none()
        
        if cache_res and cache_res.doc_ids_hash == docs_hash:
            return cache_res.report
            
        # Need to recompute. Fetch embeddings
        embeddings = []
        for doc_id in doc_ids:
            possible_ids = [doc_id]
            if doc_id in doc_to_job:
                possible_ids.append(doc_to_job[doc_id])
            art_stmt = select(JobArtifact).where(
                JobArtifact.job_id.in_(possible_ids),
                JobArtifact.stage == "segment"
            )
            art = (await session.execute(art_stmt)).scalars().first()
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
