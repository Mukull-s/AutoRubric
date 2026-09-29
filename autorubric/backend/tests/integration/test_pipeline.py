import json
import pytest
from pathlib import Path
from autorubric.pipeline.graph import build_graph
from autorubric.contracts import JobStatus, Rubric

def test_pipeline_end_to_end():
    graph = build_graph()
    
    fixture_path = Path(__file__).parents[1] / "fixtures" / "rubrics" / "rubric.json"
    with open(fixture_path) as f:
        rubric = Rubric.model_validate(json.load(f))
        
    initial_state = {
        "doc_id": "doc123",
        "rubric": rubric,
        "pdf_bytes": b"%PDF-1.4\n%dummy\n",
        "status": JobStatus.QUEUED
    }
    
    result = graph.invoke(initial_state)
    
    assert result["status"] == JobStatus.DONE
    assert result["score"] is not None
    assert result["score"].doc_id == "doc123"
    assert result["annotated_pdf"] is not None
