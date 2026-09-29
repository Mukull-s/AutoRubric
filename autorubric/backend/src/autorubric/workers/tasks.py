from .celery_app import celery_app
from autorubric.pipeline.graph import build_graph
from autorubric.contracts import JobStatus, Rubric
import asyncio
# In a real app we'd fetch the job from the DB here
# For the stub, we just run the pipeline.

@celery_app.task(bind=True, max_retries=3)
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
        
        # In a real app we'd stream the state changes to the DB
        # graph.stream() could be used here
        result = graph.invoke(initial_state)
        
        # update DB with result["score"]
        return {"status": result["status"], "score_total": result["score"].total}
    except Exception as e:
        # set FAILED in DB
        raise self.retry(exc=e, countdown=10)
