from pydantic import BaseModel, Field, model_validator
from typing import Self

class Criterion(BaseModel):
    """One line of the rubric, with a weight and dependencies."""
    id: str
    description: str
    weight: float = Field(gt=0)
    depends_on: list[str] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "id": "c1",
                "description": "Mentions chloroplasts",
                "weight": 2.0,
                "depends_on": []
            }]
        }
    }

class CreditMap(BaseModel):
    """Maps a Label to a credit multiplier."""
    FULL_CREDIT: float = 1.0
    PARTIAL_CREDIT: float = 0.5
    NO_CREDIT: float = 0.0
    MISCONCEPTION: float = 0.0

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "FULL_CREDIT": 1.0,
                "PARTIAL_CREDIT": 0.5,
                "NO_CREDIT": 0.0,
                "MISCONCEPTION": -0.5
            }]
        }
    }

class Rubric(BaseModel):
    """A multi-criteria rubric with dependencies."""
    id: str
    title: str
    criteria: list[Criterion]
    credit_map: CreditMap
    max_score: float

    @model_validator(mode="after")
    def validate_weights(self) -> Self:
        total_weight = sum(c.weight for c in self.criteria)
        if abs(total_weight - self.max_score) > 1e-5:
            raise ValueError(f"Sum of criteria weights ({total_weight}) must equal max_score ({self.max_score})")
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [{
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
            }]
        }
    }
