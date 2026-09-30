import os
import fitz
from pathlib import Path
from autorubric.extraction import extract
from autorubric.annotation import annotate
from autorubric.contracts import ScoreResult, CriterionResult, Label, BBox

def run_visual_check():
    fixture_dir = Path(__file__).parents[2] / "fixtures" / "extraction"
    out_dir = Path(__file__).parents[4] / "docs" / "screenshots" / "p2"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    with open(fixture_dir / "clean_single_column.pdf", "rb") as f:
        pdf_bytes = f.read()
        
    tokens = extract(pdf_bytes)
    
    # We want to highlight the answers
    # "The mitochondria."
    # "Photosynthesis."
    mito_tokens = [t for t in tokens if "mitochondria" in t.text.lower()]
    photo_tokens = [t for t in tokens if "photosynthesis" in t.text.lower()]
    
    score = ScoreResult(
        doc_id="doc1",
        rubric_id="rub1",
        per_criterion=[
            CriterionResult(
                criterion_id="c1",
                label=Label.FULL_CREDIT,
                credit=1.0,
                marks=2.0,
                evidence_bboxes=[t.bbox for t in mito_tokens],
                trusted=True
            ),
            CriterionResult(
                criterion_id="c2",
                label=Label.PARTIAL_CREDIT,
                credit=0.5,
                marks=1.0,
                evidence_bboxes=[t.bbox for t in photo_tokens],
                trusted=False
            )
        ],
        total=3.0,
        max_total=4.0,
        needs_review=True
    )
    
    annotated_bytes = annotate(pdf_bytes, score)
    
    doc = fitz.open(stream=annotated_bytes, filetype="pdf")
    for i in range(doc.page_count):
        pix = doc[i].get_pixmap(dpi=150)
        pix.save(out_dir / f"annotated_page_{i+1}.png")
        
    with open(out_dir / "README.md", "w") as f:
        f.write("# P2 Annotation Screenshots\n\nThese screenshots show the visual check of the annotation module.\nGreen highlights indicate FULL_CREDIT.\nAmber/Grey dashed highlights indicate untrusted/PARTIAL_CREDIT.\n")

if __name__ == "__main__":
    run_visual_check()
