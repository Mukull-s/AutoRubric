import os
from autorubric.contracts import Token

def extract(pdf_bytes: bytes) -> list[Token]:
    mode = os.environ.get("STAGE_EXTRACTION_MODE", "real")
    if mode == "stub":
        from .stub import extract as _extract
    else:
        from .real import extract as _extract
    return _extract(pdf_bytes)
