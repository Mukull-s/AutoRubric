from .state import PipelineState
from autorubric.contracts import JobStatus
from autorubric.extraction import extract
from autorubric.nlp import segment
from autorubric.retrieval import match, embed_propositions
from autorubric.evaluator import classify
from autorubric.audit import audit
from autorubric.scorer import score, SCORER_VERSION
from autorubric.annotation import annotate
import datetime
import json
from functools import wraps

def track_stage(stage_name: str, new_status: JobStatus):
    def decorator(func):
        @wraps(func)
        def wrapper(state: PipelineState):
            job_id = state.get("doc_id", "unknown")
            started_at = datetime.datetime.utcnow()
            state["status"] = new_status
            
            from autorubric.core.db import AsyncSessionLocal, Job, JobEvent
            import asyncio
            
            async def log_start():
                async with AsyncSessionLocal() as session:
                    import uuid
                    job = await session.get(Job, job_id)
                    if job:
                        job.status = new_status
                    event = JobEvent(id=str(uuid.uuid4()), job_id=job_id, stage=stage_name, started_at=started_at)
                    session.add(event)
                    await session.commit()
            
            asyncio.run(log_start())
            
            try:
                new_state = func(state)
                
                async def log_success():
                    async with AsyncSessionLocal() as session:
                        from sqlalchemy import select
                        stmt = select(JobEvent).where(JobEvent.job_id == job_id, JobEvent.stage == stage_name).order_by(JobEvent.started_at.desc())
                        event = (await session.execute(stmt)).scalars().first()
                        if event:
                            event.finished_at = datetime.datetime.utcnow()
                            event.ok = True
                        await session.commit()
                
                asyncio.run(log_success())
                
                return new_state
            except Exception as e:
                async def log_failure():
                    async with AsyncSessionLocal() as session:
                        from sqlalchemy import select
                        stmt = select(JobEvent).where(JobEvent.job_id == job_id, JobEvent.stage == stage_name).order_by(JobEvent.started_at.desc())
                        event = (await session.execute(stmt)).scalars().first()
                        if event:
                            event.finished_at = datetime.datetime.utcnow()
                            event.ok = False
                            event.error = str(e)
                        await session.commit()
                        
                asyncio.run(log_failure())
                raise
        return wrapper
    return decorator

from autorubric.core.config import config

@track_stage("extract", JobStatus.EXTRACTING)
def node_extract(state: PipelineState):
    if config.STAGE_EXTRACTION_MODE == "mock":
        from autorubric.extraction import extract
        state["tokens"] = extract(state["pdf_bytes"])
    else:
        raise NotImplementedError("Real extraction module not yet merged")
    return state

@track_stage("segment", JobStatus.SEGMENTING)
def node_segment(state: PipelineState):
    if config.STAGE_SEGMENTATION_MODE == "mock":
        from autorubric.nlp import segment
        propositions = segment(state["tokens"])
    else:
        raise NotImplementedError("Real segmentation module not yet merged")
    
    # Task 5 Glue: Set from_hidden_text on propositions
    token_dict = {t.id: t for t in state["tokens"]}
    for prop in propositions:
        if not prop.from_hidden_text:
            if any(token_dict.get(tid) and token_dict[tid].is_hidden for tid in prop.token_ids):
                prop.from_hidden_text = True
                
    state["propositions"] = propositions
    
    # Store embed_propositions output in job_artifacts
    if config.STAGE_RETRIEVAL_MODE == "mock":
        from autorubric.retrieval import embed_propositions
        embeddings = embed_propositions(propositions)
    else:
        raise NotImplementedError("Real retrieval module not yet merged")
        
    from autorubric.core.db import AsyncSessionLocal, JobArtifact
    import asyncio
    
    async def save_artifact():
        async with AsyncSessionLocal() as session:
            art = JobArtifact(
                id=f"art-{state.get('doc_id')}-embed",
                job_id=state.get("doc_id", "unknown"),
                stage="segment",
                payload={"embeddings": embeddings}
            )
            session.add(art)
            await session.commit()
            
    # Since we are in sync land, run via asyncio
    asyncio.run(save_artifact())
    
    return state

@track_stage("retrieve", JobStatus.RETRIEVING)
def node_retrieve(state: PipelineState):
    if config.STAGE_RETRIEVAL_MODE == "mock":
        from autorubric.retrieval import match
        state["candidates"] = match(state["propositions"], state["rubric"])
    else:
        raise NotImplementedError("Real retrieval module not yet merged")
    return state

# Task 5 Glue: Build EvalPairs (or marked adapter)
class EvalPairAdapter:
    def __init__(self, prop_id, criterion_id, proposition_text, criterion_text, similarity):
        self.prop_id = prop_id
        self.criterion_id = criterion_id
        self.proposition_text = proposition_text
        self.criterion_text = criterion_text
        self.similarity = similarity
        
    def __getattr__(self, name):
        # Allow classification stub to still use it like a Candidate
        if name in ["prop_id", "criterion_id", "similarity"]:
            return self.__dict__[name]
        raise AttributeError(name)

@track_stage("evaluate", JobStatus.EVALUATING)
def node_evaluate(state: PipelineState):
    if config.STAGE_EVALUATION_MODE == "mock":
        prop_dict = {p.id: p for p in state["propositions"]}
        crit_dict = {c.id: c for c in state["rubric"].criteria}
        
        eval_pairs_dict = []
        for cand in state["candidates"]:
            p_text = prop_dict[cand.prop_id].text if cand.prop_id in prop_dict else ""
            c_text = crit_dict[cand.criterion_id].description if cand.criterion_id in crit_dict else ""
            eval_pairs_dict.append({
                "prop_id": cand.prop_id,
                "criterion_id": cand.criterion_id,
                "similarity": cand.similarity
            })
            
        from autorubric.workers.tasks import evaluate_task
        from celery.result import allow_join_result
        from autorubric.contracts import Classification
        
        with allow_join_result():
            result_json = evaluate_task.delay(eval_pairs_dict).get()
            classifications = [Classification.model_validate(c) for c in result_json]
            
        state["classifications"] = classifications
    else:
        raise NotImplementedError("Real evaluation module not yet merged")
    return state

@track_stage("audit", JobStatus.AUDITING)
def node_audit(state: PipelineState):
    if config.STAGE_AUDIT_MODE == "mock":
        from autorubric.audit import audit
        state["verdicts"] = audit(state["classifications"], state["tokens"], state["propositions"])
    else:
        raise NotImplementedError("Real audit module not yet merged")
    return state

@track_stage("score", JobStatus.SCORING)
def node_score(state: PipelineState):
    state["audit_bundle"] = {
        "rubric": state["rubric"].model_dump(),
        "classifications": [c.model_dump() for c in state.get("classifications", [])],
        "verdicts": [v.model_dump() for v in state.get("verdicts", [])],
        "scorer_version": SCORER_VERSION
    }
    
    score_res = score(state.get("classifications", []), state["rubric"], state.get("verdicts", []))
    score_res.doc_id = state.get("doc_id", "unknown")
    state["score"] = score_res
    
    if score_res.needs_review:
        state["status"] = JobStatus.NEEDS_REVIEW
    return state

@track_stage("annotate", JobStatus.ANNOTATING)
def node_annotate(state: PipelineState):
    if config.STAGE_ANNOTATION_MODE == "mock":
        from autorubric.annotation import annotate
        pdf_bytes = annotate(state["pdf_bytes"], state["score"])
    else:
        raise NotImplementedError("Real annotation module not yet merged")
        
    # Save the annotated pdf to the volume
    import os
    
    doc_id = state.get("doc_id", "unknown")
    os.makedirs(config.UPLOADS_DIR, exist_ok=True)
    pdf_path = os.path.join(config.UPLOADS_DIR, f"{doc_id}_annotated.pdf")
    
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)
        
    state["annotated_pdf"] = pdf_path
    if state["status"] != JobStatus.NEEDS_REVIEW:
        state["status"] = JobStatus.DONE
    return state
