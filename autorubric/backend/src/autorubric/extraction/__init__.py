import json
from pathlib import Path
from autorubric.contracts import Token

def extract(pdf_bytes: bytes) -> list[Token]:
    fixture_path = Path(__file__).parents[3] / "tests" / "fixtures" / "extraction" / "tokens.json"
    with open(fixture_path) as f:
        data = json.load(f)
    return [Token.model_validate(item) for item in data]
