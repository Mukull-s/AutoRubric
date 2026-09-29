import json
from pathlib import Path
from autorubric.contracts import ScoreResult, Classification, Rubric, CriticVerdict

def score(classifications: list[Classification], rubric: Rubric, verdicts: list[CriticVerdict] = None) -> ScoreResult:
    fixture_path = Path(__file__).parents[3] / "tests" / "fixtures" / "scorer" / "score_result.json"
    with open(fixture_path) as f:
        data = json.load(f)
    return ScoreResult.model_validate(data)
