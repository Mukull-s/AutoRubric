from autorubric.contracts import JobStatus
from autorubric.core.errors import PermanentError

VALID_TRANSITIONS = {
    JobStatus.QUEUED: [JobStatus.EXTRACTING, JobStatus.FAILED],
    JobStatus.EXTRACTING: [JobStatus.SEGMENTING, JobStatus.FAILED],
    JobStatus.SEGMENTING: [JobStatus.RETRIEVING, JobStatus.FAILED],
    JobStatus.RETRIEVING: [JobStatus.EVALUATING, JobStatus.FAILED],
    JobStatus.EVALUATING: [JobStatus.AUDITING, JobStatus.FAILED],
    JobStatus.AUDITING: [JobStatus.SCORING, JobStatus.NEEDS_REVIEW, JobStatus.FAILED],
    JobStatus.SCORING: [JobStatus.ANNOTATING, JobStatus.FAILED],
    JobStatus.ANNOTATING: [JobStatus.DONE, JobStatus.FAILED],
    JobStatus.FAILED: [JobStatus.QUEUED], # for retries
    JobStatus.DONE: [],
    JobStatus.NEEDS_REVIEW: [JobStatus.SCORING, JobStatus.FAILED] # could be adjusted
}

def transition(current_status: JobStatus, new_status: JobStatus) -> JobStatus:
    if new_status not in VALID_TRANSITIONS.get(current_status, []):
        raise PermanentError(f"Invalid transition from {current_status} to {new_status}")
    return new_status
