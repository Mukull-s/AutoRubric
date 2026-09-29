from langgraph.graph import StateGraph, END
from .state import PipelineState
from autorubric.contracts import JobStatus
from autorubric.extraction import extract
from autorubric.nlp import segment
from autorubric.retrieval import match
from autorubric.evaluator import classify
from autorubric.audit import audit
from autorubric.scorer import score
from autorubric.annotation import annotate

def node_extract(state: PipelineState):
    state["status"] = JobStatus.EXTRACTING
    state["tokens"] = extract(state["pdf_bytes"])
    return state

def node_segment(state: PipelineState):
    state["status"] = JobStatus.SEGMENTING
    state["propositions"] = segment(state["tokens"])
    return state

def node_retrieve(state: PipelineState):
    state["status"] = JobStatus.RETRIEVING
    state["candidates"] = match(state["propositions"], state["rubric"])
    return state

def node_evaluate(state: PipelineState):
    state["status"] = JobStatus.EVALUATING
    state["classifications"] = classify(state["candidates"])
    return state

def node_audit(state: PipelineState):
    state["status"] = JobStatus.AUDITING
    state["verdicts"] = audit(state["classifications"], state["tokens"], state["propositions"])
    return state

def node_score(state: PipelineState):
    state["status"] = JobStatus.SCORING
    state["score"] = score(state["classifications"], state["rubric"], state["verdicts"])
    return state

def node_annotate(state: PipelineState):
    state["status"] = JobStatus.ANNOTATING
    state["annotated_pdf"] = annotate(state["pdf_bytes"], state["score"])
    state["status"] = JobStatus.DONE
    return state

def build_graph():
    workflow = StateGraph(PipelineState)
    
    workflow.add_node("extract", node_extract)
    workflow.add_node("segment", node_segment)
    workflow.add_node("retrieve", node_retrieve)
    workflow.add_node("evaluate", node_evaluate)
    workflow.add_node("audit", node_audit)
    workflow.add_node("score", node_score)
    workflow.add_node("annotate", node_annotate)
    
    workflow.set_entry_point("extract")
    workflow.add_edge("extract", "segment")
    workflow.add_edge("segment", "retrieve")
    workflow.add_edge("retrieve", "evaluate")
    workflow.add_edge("evaluate", "audit")
    workflow.add_edge("audit", "score")
    workflow.add_edge("score", "annotate")
    workflow.add_edge("annotate", END)
    
    return workflow.compile()
