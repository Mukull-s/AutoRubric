import pytest
from autorubric.contracts import JobStatus
from autorubric.core.jobs import transition
from autorubric.core.errors import PermanentError

def test_valid_transition():
    assert transition(JobStatus.QUEUED, JobStatus.EXTRACTING) == JobStatus.EXTRACTING
    assert transition(JobStatus.AUDITING, JobStatus.SCORING) == JobStatus.SCORING

def test_invalid_transition():
    with pytest.raises(PermanentError):
        transition(JobStatus.DONE, JobStatus.EXTRACTING)
    
    with pytest.raises(PermanentError):
        transition(JobStatus.EXTRACTING, JobStatus.DONE)
