import pytest
from autorubric.scorer import score
from autorubric.contracts import Rubric, Classification, CriticVerdict, Label, ScoreResult
from decimal import Decimal
import hypothesis.strategies as st
from hypothesis import given

def test_trust_filter():
    rubric = Rubric.model_validate({
        "id": "r1", "title": "Test", "max_score": 1.0,
        "credit_map": {"FULL_CREDIT": 1.0, "PARTIAL_CREDIT": 0.5, "NO_CREDIT": 0.0, "MISCONCEPTION": 0.0},
        "criteria": [{"id": "c1", "description": "d", "weight": 1.0, "depends_on": []}]
    })
    
    # Classification with no verdict
    c1 = Classification(id="cl1", prop_id="p1", criterion_id="c1", label=Label.FULL_CREDIT, confidence=0.9)
    res = score([c1], rubric, [])
    
    assert res.per_criterion[0].credit == 0.0
    assert res.needs_review == True

def test_dag_dependency_cap():
    rubric = Rubric.model_validate({
        "id": "r1", "title": "Test", "max_score": 2.0,
        "credit_map": {"FULL_CREDIT": 1.0, "PARTIAL_CREDIT": 0.5, "NO_CREDIT": 0.0, "MISCONCEPTION": 0.0},
        "criteria": [
            {"id": "c1", "description": "d1", "weight": 1.0, "depends_on": []},
            {"id": "c2", "description": "d2", "weight": 1.0, "depends_on": ["c1"]}
        ]
    })
    
    c1 = Classification(id="cl1", prop_id="p1", criterion_id="c1", label=Label.NO_CREDIT, confidence=0.9)
    c2 = Classification(id="cl2", prop_id="p2", criterion_id="c2", label=Label.FULL_CREDIT, confidence=0.9)
    
    v1 = CriticVerdict(classification_id="cl1", trusted=True, reason="", flags=[])
    v2 = CriticVerdict(classification_id="cl2", trusted=True, reason="", flags=[])
    
    res = score([c1, c2], rubric, [v1, v2])
    
    # c2 is capped at PARTIAL_CREDIT (0.5) because c1 is NO_CREDIT
    assert res.per_criterion[1].credit == 0.5
    assert res.total == 0.5

@given(st.permutations([0, 1, 2]))
def test_property_order_invariance(order):
    rubric = Rubric.model_validate({
        "id": "r1", "title": "Test", "max_score": 2.0,
        "credit_map": {"FULL_CREDIT": 1.0, "PARTIAL_CREDIT": 0.5, "NO_CREDIT": 0.0, "MISCONCEPTION": 0.0},
        "criteria": [
            {"id": "c1", "description": "d1", "weight": 1.0, "depends_on": []},
            {"id": "c2", "description": "d2", "weight": 1.0, "depends_on": ["c1"]}
        ]
    })
    c1 = Classification(id="cl1", prop_id="p1", criterion_id="c1", label=Label.NO_CREDIT, confidence=0.9)
    c2 = Classification(id="cl2", prop_id="p2", criterion_id="c2", label=Label.FULL_CREDIT, confidence=0.9)
    c3 = Classification(id="cl3", prop_id="p3", criterion_id="c2", label=Label.PARTIAL_CREDIT, confidence=0.95)
    
    v1 = CriticVerdict(classification_id="cl1", trusted=True, reason="", flags=[])
    v2 = CriticVerdict(classification_id="cl2", trusted=True, reason="", flags=[])
    v3 = CriticVerdict(classification_id="cl3", trusted=True, reason="", flags=[])
    
    classifications = [c1, c2, c3]
    shuffled_classifications = [classifications[i] for i in order]
    
    res = score(shuffled_classifications, rubric, [v1, v2, v3])
    
    assert res.per_criterion[1].credit == 0.5
    assert res.total == 0.5
