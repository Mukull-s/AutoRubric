from langgraph.graph import StateGraph, END
from .state import PipelineState
from .nodes import (
    node_extract, node_segment, node_retrieve, node_evaluate, 
    node_audit, node_score, node_annotate
)

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
