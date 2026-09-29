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
        return {"status": result["status"]}
    except TransientError as e:
        raise
    except Exception as e:
        # Catch PermanentError or any other Exception
        error_msg = str(e)
        tb = traceback.format_exc()
        # Mocking writing to failed_jobs DB here
        print(f"FAILED JOB {job_id}: {error_msg}\n{tb}")
        # In a real app we would set job status to FAILED in DB and insert into failed_jobs
        return {"status": JobStatus.FAILED, "error": error_msg}
