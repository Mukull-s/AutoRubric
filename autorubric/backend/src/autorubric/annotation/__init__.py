import os
from autorubric.contracts import ScoreResult

def annotate(pdf_bytes: bytes, score: ScoreResult) -> bytes:
    mode = os.environ.get("STAGE_ANNOTATION_MODE", "real")
    if mode == "stub":
        from .stub import annotate as _annotate
    else:
        from .real import annotate as _annotate
    return _annotate(pdf_bytes, score)
