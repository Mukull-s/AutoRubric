from .celery_app import celery_app
from autorubric.pipeline.graph import build_graph
from autorubric.contracts import JobStatus, Rubric
from autorubric.core.errors import TransientError, PermanentError
from autorubric.core.db import AsyncSessionLocal, Result as DBResult, Job, FailedJob
import traceback
import os
import uuid
import logging
import asyncio
import concurrent.futures

logger = logging.getLogger(__name__)


def _run_sync(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


def execute_pipeline_sync(job_id: str, rubric_dict: dict, pdf_bytes: bytes, doc_id: str = None):
    """Executes the pipeline synchronously and updates database job/result."""
    real_doc_id = doc_id
    if not real_doc_id:
        async def get_doc_id():
            async with AsyncSessionLocal() as session:
                j = await session.get(Job, job_id)
                return j.submission_id if j else None
        try:
            real_doc_id = _run_sync(get_doc_id())
        except Exception as e:
            logger.warning(f"Could not fetch doc_id for job {job_id}: {e}")
    if not real_doc_id:
        real_doc_id = job_id

    graph = build_graph()
    rubric = Rubric.model_validate(rubric_dict)

    initial_state = {
        "job_id": job_id,
        "doc_id": real_doc_id,
        "rubric": rubric,
        "pdf_bytes": pdf_bytes,
        "status": JobStatus.QUEUED
    }

    try:
        result = graph.invoke(initial_state)
    except TransientError:
        raise
    except Exception as e:
        error_msg = str(e)
        tb = traceback.format_exc()
        logger.error(f"FAILED JOB {job_id}: {error_msg}\n{tb}")

        async def save_failure():
            try:
                async with AsyncSessionLocal() as session:
                    job = await session.get(Job, job_id)
                    if job:
                        job.status = JobStatus.FAILED
                        job.error = error_msg
                    failed = FailedJob(id=str(uuid.uuid4()), job_id=job_id, error=error_msg, traceback=tb)
                    session.add(failed)
                    await session.commit()
            except Exception as se:
                logger.warning(f"Error saving job failure to DB: {se}")

        try:
            _run_sync(save_failure())
        except Exception:
            pass
        return {"status": JobStatus.FAILED, "error": error_msg}

    async def save_final():
        try:
            async with AsyncSessionLocal() as session:
                score_res = result.get("score")
                if score_res:
                    stage_modes = {
                        "extraction": os.environ.get("STAGE_EXTRACTION_MODE", "real"),
                        "segmentation": os.environ.get("STAGE_SEGMENTATION_MODE", "real"),
                        "retrieval": os.environ.get("STAGE_RETRIEVAL_MODE", "real"),
                        "evaluation": os.environ.get("STAGE_EVALUATION_MODE", "real"),
                        "audit": os.environ.get("STAGE_AUDIT_MODE", "real"),
                        "annotation": os.environ.get("STAGE_ANNOTATION_MODE", "real"),
                    }
                    score_data = score_res.model_dump()
                    if "propositions" in result and result["propositions"] is not None:
                        score_data["propositions"] = [
                            p.model_dump() if hasattr(p, "model_dump") else p
                            for p in result["propositions"]
                        ]
                    from autorubric.evaluator import model_info
                    score_data["provenance"] = {
                        "evaluator": model_info(),
                        "stage_modes": stage_modes,
                        "fixture_data_used": any(mode == "stub" for mode in stage_modes.values()),
                    }
                    total_val = getattr(score_res, "total", getattr(score_res, "total_score", 0.0))
                    res = DBResult(
                        doc_id=real_doc_id,
                        rubric_id=rubric.id if hasattr(rubric, "id") else "unknown",
                        data=score_data,
                        total_score=float(total_val),
                        needs_review=score_res.needs_review,
                        audit_bundle=result.get("audit_bundle")
                    )
                    existing_res = await session.get(DBResult, real_doc_id)
                    if existing_res:
                        existing_res.data = score_data
                        existing_res.total_score = float(total_val)
                        existing_res.needs_review = score_res.needs_review
                        existing_res.audit_bundle = result.get("audit_bundle")
                    else:
                        session.add(res)
                job = await session.get(Job, job_id)
                if job:
                    job.status = result["status"]
                await session.commit()
        except Exception as e:
            logger.error(f"Error saving pipeline final result to DB: {e}", exc_info=True)
            raise

    try:
        _run_sync(save_final())
    except Exception as e:
        logger.error(f"Error executing save_final for job {job_id}: {e}", exc_info=True)

    return {"status": result["status"]}


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
def run_pipeline(self, job_id: str, rubric_dict: dict, pdf_bytes_hex: str, doc_id: str = None):
    try:
        pdf_bytes = bytes.fromhex(pdf_bytes_hex)
        return execute_pipeline_sync(job_id, rubric_dict, pdf_bytes, doc_id=doc_id)
    except TransientError:
        raise
    except Exception as e:
        error_msg = str(e)
        tb = traceback.format_exc()
        logger.error(f"FAILED JOB {job_id}: {error_msg}\n{tb}")

        async def save_failure():
            try:
                async with AsyncSessionLocal() as session:
                    job = await session.get(Job, job_id)
                    if job:
                        job.status = JobStatus.FAILED
                        job.error = error_msg
                    failed = FailedJob(id=str(uuid.uuid4()), job_id=job_id, error=error_msg, traceback=tb)
                    session.add(failed)
                    await session.commit()
            except Exception:
                pass

        try:
            _run_sync(save_failure())
        except Exception:
            pass
        return {"status": JobStatus.FAILED, "error": error_msg}


@celery_app.task(bind=True, queue="gpu_queue")
def evaluate_task(self, candidates_json: list[dict]):
    from autorubric.evaluator import classify
    from autorubric.contracts import EvalPair
    pairs = [EvalPair.model_validate(c) for c in candidates_json]
    classifications = classify(pairs)
    return [c.model_dump() for c in classifications]
