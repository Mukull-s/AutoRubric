import pytest
import numpy as np
from autorubric.audit.collusion import detect, CollusionConfig

def create_embeddings(doc_id, num_props, offset=0.0):
    return {
        f"p{i}": [1.0 + offset, 0.0, 0.0] if i % 3 == 0 else
                 [0.0, 1.0 + offset, 0.0] if i % 3 == 1 else
                 [0.0, 0.0, 1.0 + offset]
        for i in range(num_props)
    }

def test_collusion_exact_copy():
    embeddings = {
        "d1": create_embeddings("d1", 5),
        "d2": create_embeddings("d2", 5),
    }
    config = CollusionConfig(prop_threshold=0.9, pair_absolute_threshold=0.5)
    report = detect(embeddings, config)
    
    assert len(report.doc_pairs) == 1
    assert report.doc_pairs[0].a == "d1"
    assert report.doc_pairs[0].b == "d2"
    assert len(report.doc_pairs[0].matching_props) == 5

def test_collusion_independent_answers():
    embeddings = {
        "d1": {"p0": [1.0, 0.0, 0.0], "p1": [1.0, 0.0, 0.0]},
        "d2": {"p0": [0.0, 1.0, 0.0], "p1": [0.0, 1.0, 0.0]},
    }
    config = CollusionConfig(prop_threshold=0.9, pair_absolute_threshold=0.5)
    report = detect(embeddings, config)
    assert len(report.doc_pairs) == 0

def test_collusion_tiny_cohorts():
    embeddings = {
        "d1": create_embeddings("d1", 5)
    }
    report = detect(embeddings)
    assert len(report.doc_pairs) == 0

def test_collusion_empty_documents():
    embeddings = {
        "d1": {},
        "d2": {}
    }
    report = detect(embeddings)
    assert len(report.doc_pairs) == 0

def test_collusion_mismatched_sizes():
    embeddings = {
        "d1": {"p1": [1.0, 0.0]},
        "d2": {"p1": [1.0, 0.0, 0.0]}
    }
    with pytest.raises(ValueError, match="Vector size mismatch"):
        detect(embeddings)

def test_collusion_subset():
    embeddings = {
        "d1": create_embeddings("d1", 10),
        "d2": create_embeddings("d2", 5) # subset
    }
    config = CollusionConfig(prop_threshold=0.9, pair_absolute_threshold=0.5)
    report = detect(embeddings, config)
    assert len(report.doc_pairs) == 1
    assert report.doc_pairs[0].similarity > 0.7 # 0.5 * 1.0 (frac matches) + 0.5 * 1.0 (mean sim) = 1.0
