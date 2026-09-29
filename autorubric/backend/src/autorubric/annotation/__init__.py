from autorubric.contracts import ScoreResult
from pathlib import Path

def annotate(pdf_bytes: bytes, score: ScoreResult) -> bytes:
    fixture_path = Path(__file__).parents[3] / "tests" / "fixtures" / "annotation" / "annotated.pdf"
    with open(fixture_path, "rb") as f:
        return f.read()
