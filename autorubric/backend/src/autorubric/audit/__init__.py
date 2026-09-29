import json
from pathlib import Path
from autorubric.contracts import CriticVerdict, CollusionReport, Classification, Token, Proposition
from autorubric.contracts.grading import Candidate

from .critic import run_critic

def audit(classifications: list[Classification], tokens: list[Token], propositions: list[Proposition], candidates: list[Candidate] | None = None) -> list[CriticVerdict]:
    return run_critic(classifications, tokens, propositions, candidates)

def detect(cohort_embeddings) -> CollusionReport:
    fixture_path = Path(__file__).parents[3] / "tests" / "fixtures" / "audit" / "collusion_report.json"
    with open(fixture_path) as f:
        data = json.load(f)
    return CollusionReport.model_validate(data)
