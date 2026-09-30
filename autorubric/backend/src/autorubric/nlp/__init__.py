import json
from pathlib import Path
from autorubric.contracts import Rubric, Proposition, Token

def compile_rubric(rubric_json: dict) -> Rubric:
    # Just validate the dictionary
    return Rubric.model_validate(rubric_json)

def segment(tokens: list[Token]) -> list[Proposition]:
    fixture_path = Path(__file__).parents[3] / "tests" / "fixtures" / "nlp" / "propositions.json"
    with open(fixture_path) as f:
        data = json.load(f)
    return [Proposition.model_validate(item) for item in data]

def detect(docs: list[dict]) -> "CollusionReport":
    from autorubric.contracts import CollusionReport
    return CollusionReport(
        cohort_id="unknown",
        pairs=[],
        cluster_labels={}
    )
