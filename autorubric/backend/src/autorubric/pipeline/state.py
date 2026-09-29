from typing import TypedDict, Optional
from autorubric.contracts import (
    JobStatus, Rubric, Token, Proposition, Candidate,
    Classification, CriticVerdict, ScoreResult
)

class PipelineState(TypedDict):
    doc_id: str
    rubric: Rubric
    pdf_bytes: bytes
    tokens: list[Token]
    propositions: list[Proposition]
    candidates: list[Candidate]
    classifications: list[Classification]
    verdicts: list[CriticVerdict]
    score: Optional[ScoreResult]
    annotated_pdf: Optional[bytes]
    status: JobStatus
    error: Optional[str]
