import pytest
import json
from autorubric.scorer import score
from autorubric.contracts import Rubric, Classification, CriticVerdict, Label, ScoreResult
from pathlib import Path

def test_audit_consistency(tmp_path):
    rubric = Rubric.model_validate({
        "id": "r1", "title": "Test", "max_score": 1.0,
        "credit_map": {"FULL_CREDIT": 1.0, "PARTIAL_CREDIT": 0.5, "NO_CREDIT": 0.0, "MISCONCEPTION": 0.0},
        "criteria": [{"id": "c1", "description": "d", "weight": 1.0, "depends_on": []}]
    })
    
    c1 = Classification(id="cl1", prop_id="p1", criterion_id="c1", label=Label.FULL_CREDIT, confidence=0.9)
    v1 = CriticVerdict(classification_id="cl1", trusted=True, reason="", flags=[])
    
    res1 = score([c1], rubric, [v1])
    bundle = {
        "rubric": rubric.model_dump(),
        "classifications": [c1.model_dump()],
        "verdicts": [v1.model_dump()],
        "score_result": res1.model_dump()
    }
    
    # Store
    storage_path = tmp_path / "bundle.json"
    storage_path.write_text(json.dumps(bundle))
    
    # Load
    loaded_data = json.loads(storage_path.read_text())
    loaded_rubric = Rubric.model_validate(loaded_data["rubric"])
    loaded_classifications = [Classification.model_validate(c) for c in loaded_data["classifications"]]
    loaded_verdicts = [CriticVerdict.model_validate(v) for v in loaded_data["verdicts"]]
    
    res2 = score(loaded_classifications, loaded_rubric, loaded_verdicts)
    
    assert json.dumps(res1.model_dump(), sort_keys=True) == json.dumps(res2.model_dump(), sort_keys=True)
