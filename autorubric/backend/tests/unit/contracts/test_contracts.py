import pytest
from autorubric.contracts import (
    BBox, Token, Proposition, Criterion, CreditMap, Rubric,
    Candidate, Classification, CriticVerdict, CriterionResult,
    ScoreResult, CollusionReport
)

def test_bbox_roundtrip():
    data = {"x": 10.5, "y": 20.0, "w": 100.0, "h": 12.0, "page": 1}
    obj = BBox.model_validate(data)
    assert obj.model_dump() == data
    assert BBox.model_validate_json(obj.model_dump_json()) == obj

def test_token_roundtrip():
    data = {
        "id": "t1",
        "text": "photosynthesis",
        "page": 1,
        "bbox": {"x": 10.5, "y": 20.0, "w": 100.0, "h": 12.0, "page": 1},
        "block_id": "b1",
        "is_hidden": False
    }
    obj = Token.model_validate(data)
    assert obj.model_dump() == data
    assert Token.model_validate_json(obj.model_dump_json()) == obj

def test_proposition_roundtrip():
    data = {
        "id": "p1",
        "doc_id": "doc123",
        "text": "The plant cell has a chloroplast.",
        "token_ids": ["t1", "t2"],
        "page": 1,
        "bboxes": [{"x": 10.5, "y": 20.0, "w": 100.0, "h": 12.0, "page": 1}],
        "from_hidden_text": False
    }
    obj = Proposition.model_validate(data)
    assert obj.model_dump() == data
    assert Proposition.model_validate_json(obj.model_dump_json()) == obj

def test_criterion_roundtrip():
    data = {
        "id": "c1",
        "description": "Mentions chloroplasts",
        "weight": 2.0,
        "depends_on": []
    }
    obj = Criterion.model_validate(data)
    assert obj.model_dump() == data
    assert Criterion.model_validate_json(obj.model_dump_json()) == obj

def test_rubric_roundtrip():
    data = {
        "id": "r1",
        "title": "Photosynthesis",
        "criteria": [{
            "id": "c1",
            "description": "Mentions chloroplasts",
            "weight": 2.0,
            "depends_on": []
        }],
        "credit_map": {
            "FULL_CREDIT": 1.0,
            "PARTIAL_CREDIT": 0.5,
            "NO_CREDIT": 0.0,
            "MISCONCEPTION": 0.0
        },
        "max_score": 2.0
    }
    obj = Rubric.model_validate(data)
    assert obj.model_dump() == data
    assert Rubric.model_validate_json(obj.model_dump_json()) == obj

def test_candidate_roundtrip():
    data = {
        "prop_id": "p1",
        "criterion_id": "c1",
        "similarity": 0.85
    }
    obj = Candidate.model_validate(data)
    assert obj.model_dump() == data
    assert Candidate.model_validate_json(obj.model_dump_json()) == obj

def test_classification_roundtrip():
    data = {
        "id": "cl1",
        "prop_id": "p1",
        "criterion_id": "c1",
        "label": "FULL_CREDIT",
        "confidence": 0.95
    }
    obj = Classification.model_validate(data)
    assert obj.model_dump() == data
    assert Classification.model_validate_json(obj.model_dump_json()) == obj

def test_critic_verdict_roundtrip():
    data = {
        "classification_id": "cl1",
        "trusted": True,
        "reason": "Looks standard.",
        "flags": []
    }
    obj = CriticVerdict.model_validate(data)
    assert obj.model_dump() == data
    assert CriticVerdict.model_validate_json(obj.model_dump_json()) == obj

def test_score_result_roundtrip():
    data = {
        "doc_id": "doc123",
        "rubric_id": "r1",
        "per_criterion": [{
            "criterion_id": "c1",
            "label": "FULL_CREDIT",
            "credit": 1.0,
            "marks": 2.0,
            "evidence_bboxes": [{"x": 10.5, "y": 20.0, "w": 100.0, "h": 12.0, "page": 1}],
            "trusted": True
        }],
        "total": 2.0,
        "max_total": 2.0,
        "needs_review": False
    }
    obj = ScoreResult.model_validate(data)
    assert obj.model_dump() == data
    assert ScoreResult.model_validate_json(obj.model_dump_json()) == obj

def test_collusion_report_roundtrip():
    data = {
        "cohort_id": "cohort_01",
        "doc_pairs": [{
            "a": "doc123",
            "b": "doc456",
            "similarity": 0.92,
            "matching_props": ["p1", "p5"]
        }]
    }
    obj = CollusionReport.model_validate(data)
    assert obj.model_dump() == data
    assert CollusionReport.model_validate_json(obj.model_dump_json()) == obj
