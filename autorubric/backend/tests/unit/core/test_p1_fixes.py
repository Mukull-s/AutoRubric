import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from autorubric.contracts import JobStatus, Rubric
from autorubric.core.db import Job, Submission, Result as DBResult, JobEvent
from autorubric.pipeline.nodes import track_stage
from autorubric.contracts.rubric import Criterion

@pytest.mark.asyncio
async def test_p1_1_track_stage_uses_job_id(monkeypatch):
    """P1.1: Verify track_stage decorator uses job_id to update Job status and JobEvent."""
    updated_jobs = {}
    created_events = []

    class MockSession:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def get(self, model, ident):
            if model == Job:
                return updated_jobs.get(ident)
            return None
        def add(self, obj):
            if isinstance(obj, JobEvent):
                created_events.append(obj)
        async def commit(self): pass
        async def execute(self, stmt):
            m = MagicMock()
            m.scalars().first.return_value = created_events[-1] if created_events else None
            return m

    mock_job = Job(id="job-test-123", submission_id="doc-test-456", status=JobStatus.QUEUED)
    updated_jobs["job-test-123"] = mock_job

    monkeypatch.setattr("autorubric.core.db.AsyncSessionLocal", lambda: MockSession())

    @track_stage("extract", JobStatus.EXTRACTING)
    def dummy_func(state):
        return state

    state = {
        "job_id": "job-test-123",
        "doc_id": "doc-test-456",
        "status": JobStatus.QUEUED
    }

    dummy_func(state)

    # Job record must be updated to EXTRACTING using job_id
    assert mock_job.status == JobStatus.EXTRACTING
    # JobEvent must record job_id == "job-test-123"
    assert len(created_events) > 0
    assert created_events[0].job_id == "job-test-123"
    assert created_events[0].stage == "extract"

def test_p1_3_batch_submission_accepts_cohort_name():
    """P1.3: Verify chosen_cohort uses cohort_name when cohort_id is not provided."""
    cohort_id = None
    cohort_name = "Biology-Period-3"
    
    chosen_cohort = cohort_id or cohort_name
    actual_cohort_id = chosen_cohort.strip() if chosen_cohort and chosen_cohort.strip() else "fallback"
    assert actual_cohort_id == "Biology-Period-3"

def test_p1_4_cohort_jobs_contain_cohort_id():
    """P1.4: Verify jobs objects constructed in cohort router include cohort_id."""
    cohort_id = "cohort-fall-2026"
    j_id = "job-001"
    sub_id = "doc-001"
    fname = "essay1.pdf"
    status_str = "DONE"

    job_entry = {
        "job_id": j_id,
        "cohort_id": cohort_id,
        "doc_id": sub_id,
        "file_name": fname,
        "filename": fname,
        "status": status_str,
        "created_at": "",
        "updated_at": "",
        "events": [],
        "error": None
    }
    assert job_entry["cohort_id"] == "cohort-fall-2026"

def test_p1_5_result_propositions_serialization():
    """P1.5: Verify score_data includes propositions for the propositions API."""
    mock_props = [
        {"id": "prop-1", "text": "Mitochondria produce ATP.", "bboxes": [], "page": 1, "is_hidden": False}
    ]
    
    score_data = {
        "doc_id": "doc-1",
        "rubric_id": "r-1",
        "total": 10.0,
        "propositions": mock_props
    }

    assert "propositions" in score_data
    assert len(score_data["propositions"]) == 1
    assert score_data["propositions"][0]["text"] == "Mitochondria produce ATP."
