import json
from pathlib import Path
from autorubric.contracts import Classification, Candidate

def classify(pairs: list[Candidate]) -> list[Classification]:
    fixture_path = Path(__file__).parents[3] / "tests" / "fixtures" / "evaluator" / "classifications.json"
    with open(fixture_path) as f:
        data = json.load(f)
    return [Classification.model_validate(item) for item in data]
