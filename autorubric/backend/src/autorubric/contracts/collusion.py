from pydantic import BaseModel

class DocPairMatch(BaseModel):
    a: str
    b: str
    similarity: float
    matching_props: list[str]

class CollusionReport(BaseModel):
    """Report of suspiciously similar submissions."""
    cohort_id: str
    doc_pairs: list[DocPairMatch]

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "cohort_id": "cohort_01",
                "doc_pairs": [{
                    "a": "doc123",
                    "b": "doc456",
                    "similarity": 0.92,
                    "matching_props": ["p1", "p5"]
                }]
            }]
        }
    }
