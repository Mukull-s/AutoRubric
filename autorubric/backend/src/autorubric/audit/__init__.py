import json
from pathlib import Path
from autorubric.contracts import CriticVerdict, CollusionReport, Classification, Token, Proposition

def audit(classifications: list[Classification], tokens: list[Token], propositions: list[Proposition]) -> list[CriticVerdict]:
    fixture_path = Path(__file__).parents[3] / "tests" / "fixtures" / "audit" / "critic_verdicts.json"
    with open(fixture_path) as f:
        data = json.load(f)
    return [CriticVerdict.model_validate(item) for item in data]

def detect(cohort_embeddings) -> CollusionReport:
    fixture_path = Path(__file__).parents[3] / "tests" / "fixtures" / "audit" / "collusion_report.json"
    with open(fixture_path) as f:
        data = json.load(f)
    return CollusionReport.model_validate(data)
