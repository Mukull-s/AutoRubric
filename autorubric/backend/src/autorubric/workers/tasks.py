from .celery_app import celery_app
from autorubric.pipeline.graph import build_graph
from autorubric.contracts import JobStatus, Rubric
from autorubric.core.errors import TransientError, PermanentError
import traceback

@celery_app.task(
    bind=True,
    autoretry_for=(TransientError,),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    max_retries=3,
    soft_time_limit=300,
    time_limit=330,
    acks_late=True,
    reject_on_worker_lost=True
)
def run_pipeline(self, job_id: str, rubric_dict: dict, pdf_bytes_hex: str):
    try:
        graph = build_graph()
        rubric = Rubric.model_validate(rubric_dict)
        pdf_bytes = bytes.fromhex(pdf_bytes_hex)
        
        initial_state = {
            "doc_id": job_id,
            "rubric": rubric,
            "pdf_bytes": pdf_bytes,
            "status": JobStatus.QUEUED
        }
        
        result = graph.invoke(initial_state)
        
        import asyncio
        from autorubric.core.db import AsyncSessionLocal, Result as DBResult, Job
        
        async def save_final():
            async with AsyncSessionLocal() as session:
                score_res = result.get("score")
                if score_res:
                    res = DBResult(
                        doc_id=job_id,
                        rubric_id=rubric.id if hasattr(rubric, "id") else "unknown",
                        data=score_res.model_dump(),
                        total_score=score_res.total_score,
                        needs_review=score_res.needs_review,
                        audit_bundle=result.get("audit_bundle")
                    )
                    session.add(res)
                job = await session.get(Job, job_id)
                if job:
                    job.status = result["status"]
                await session.commit()
                
        asyncio.run(save_final())
        
        return {"status": result["status"]}
    except TransientError as e:
        raise
    except Exception as e:
        error_msg = str(e)
        tb = traceback.format_exc()
        print(f"FAILED JOB {job_id}: {error_msg}\n{tb}")
        
        import asyncio
        from autorubric.core.db import AsyncSessionLocal, Job, FailedJob
        import uuid
        
        async def save_failure():
            async with AsyncSessionLocal() as session:
                job = await session.get(Job, job_id)
                if job:
                    job.status = JobStatus.FAILED
                    job.error = error_msg
                failed = FailedJob(id=str(uuid.uuid4()), job_id=job_id, error=error_msg, traceback=tb)
                session.add(failed)
                await session.commit()
                
        asyncio.run(save_failure())
        return {"status": JobStatus.FAILED, "error": error_msg}

@celery_app.task(bind=True, queue="gpu_queue")
def evaluate_task(self, candidates_json: list[dict]):
    from autorubric.evaluator import classify
    from autorubric.contracts import Candidate
    candidates = [Candidate.model_validate(c) for c in candidates_json]
    classifications = classify(candidates)
    return [c.model_dump() for c in classifications]

