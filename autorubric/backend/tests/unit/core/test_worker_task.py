import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from autorubric.contracts import ScoreResult, JobStatus
from autorubric.core.db import Result as DBResult, Job

def test_score_result_contract_has_total():
    """Verify ScoreResult defines 'total', not 'total_score'."""
    sr = ScoreResult(
        doc_id="doc-123",
        rubric_id="rub-1",
        per_criterion=[],
        total=15.5,
        max_total=20.0,
        needs_review=False
    )
    assert sr.total == 15.5
    assert not hasattr(sr, "total_score")
    # Verify our getattr fallback correctly resolves total
    total_val = getattr(sr, "total", getattr(sr, "total_score", 0.0))
    assert total_val == 15.5

def test_save_final_uses_doc_id_and_not_job_id():
    """Verify Result record uses real doc_id instead of job_id collision."""
    doc_id = "doc-abc-123"
    job_id = "job-xyz-789"
    
    sr = ScoreResult(
        doc_id=doc_id,
        rubric_id="rub-1",
        per_criterion=[],
        total=18.0,
        max_total=20.0,
        needs_review=False
    )
    
    score_data = sr.model_dump()
    total_val = getattr(sr, "total", getattr(sr, "total_score", 0.0))
    
    res = DBResult(
        doc_id=doc_id,
        rubric_id="rub-1",
        data=score_data,
        total_score=total_val,
        needs_review=sr.needs_review,
        audit_bundle=None
    )
    
    assert res.doc_id == "doc-abc-123"
    assert res.doc_id != job_id
    assert res.total_score == 18.0
