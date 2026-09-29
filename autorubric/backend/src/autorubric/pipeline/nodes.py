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
            
            print(json.dumps({
                "job_id": job_id,
                "stage": stage_name,
                "event": "started",
                "timestamp": started_at.isoformat()
            }))
            
            try:
                new_state = func(state)
                
                print(json.dumps({
                    "job_id": job_id,
                    "stage": stage_name,
                    "event": "finished",
                    "ok": True,
                    "timestamp": datetime.datetime.utcnow().isoformat()
                }))
                return new_state
            except Exception as e:
                print(json.dumps({
                    "job_id": job_id,
                    "stage": stage_name,
                    "event": "finished",
                    "ok": False,
                    "error": str(e),
                    "timestamp": datetime.datetime.utcnow().isoformat()
                }))
                raise
        return wrapper
    return decorator

@track_stage("extract", JobStatus.EXTRACTING)
def node_extract(state: PipelineState):
    state["tokens"] = extract(state["pdf_bytes"])
    return state

@track_stage("segment", JobStatus.SEGMENTING)
def node_segment(state: PipelineState):
    propositions = segment(state["tokens"])
    
    # Task 5 Glue: Set from_hidden_text on propositions
    token_dict = {t.id: t for t in state["tokens"]}
    for prop in propositions:
        if not prop.from_hidden_text:
            if any(token_dict.get(tid) and token_dict[tid].is_hidden for tid in prop.token_ids):
                prop.from_hidden_text = True
                
    state["propositions"] = propositions
    
    # Task 5 Glue: Store embed_propositions output in job_artifacts (mocked for now)
    embeddings = embed_propositions(propositions)
    # in real app: db.session.add(JobArtifact(stage="segment", payload=embeddings))
    
    return state

@track_stage("retrieve", JobStatus.RETRIEVING)
def node_retrieve(state: PipelineState):
    state["candidates"] = match(state["propositions"], state["rubric"])
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
    prop_dict = {p.id: p for p in state["propositions"]}
    crit_dict = {c.id: c for c in state["rubric"].criteria}
    
    eval_pairs = []
    for cand in state["candidates"]:
        p_text = prop_dict[cand.prop_id].text if cand.prop_id in prop_dict else ""
        c_text = crit_dict[cand.criterion_id].description if cand.criterion_id in crit_dict else ""
        eval_pairs.append(EvalPairAdapter(
            prop_id=cand.prop_id,
            criterion_id=cand.criterion_id,
            proposition_text=p_text,
            criterion_text=c_text,
            similarity=cand.similarity
        ))
        
    state["classifications"] = classify(eval_pairs)
    return state

@track_stage("audit", JobStatus.AUDITING)
def node_audit(state: PipelineState):
    state["verdicts"] = audit(state["classifications"], state["tokens"], state["propositions"])
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
    state["annotated_pdf"] = annotate(state["pdf_bytes"], state["score"])
    if state["status"] != JobStatus.NEEDS_REVIEW:
        state["status"] = JobStatus.DONE
    return state
