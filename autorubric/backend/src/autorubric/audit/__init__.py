import json
from pathlib import Path
from autorubric.contracts import CriticVerdict, CollusionReport, Classification, Token, Proposition
from autorubric.contracts.grading import Candidate

from .critic import run_critic

def audit(classifications: list[Classification], tokens: list[Token], propositions: list[Proposition], candidates: list[Candidate] | None = None) -> list[CriticVerdict]:
    return run_critic(classifications, tokens, propositions, candidates)

from .collusion import detect as _detect

def detect(cohort_embeddings) -> CollusionReport:
    return _detect(cohort_embeddings)
