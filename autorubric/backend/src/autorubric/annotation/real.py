import fitz
import os
from autorubric.contracts import ScoreResult, BBox, Label
from autorubric.core.errors import PermanentError

def merge_bboxes(bboxes: list[BBox]) -> list[BBox]:
    if not bboxes:
        return []
    
    # Sort by page, y, x
    sorted_bboxes = sorted(bboxes, key=lambda b: (b.page, round(b.y / 5) * 5, b.x))
    merged = []
    curr = sorted_bboxes[0]
    
    for b in sorted_bboxes[1:]:
        if b.page == curr.page and abs(b.y - curr.y) < 10 and (b.x - (curr.x + curr.w)) < 25:
            # Merge
            new_x = min(curr.x, b.x)
            new_y = min(curr.y, b.y)
            new_x1 = max(curr.x + curr.w, b.x + b.w)
            new_y1 = max(curr.y + curr.h, b.y + b.h)
            curr = BBox(x=new_x, y=new_y, w=new_x1 - new_x, h=new_y1 - new_y, page=curr.page)
        else:
            merged.append(curr)
            curr = b
    merged.append(curr)
    return merged

def get_color(label: Label):
    if label == Label.FULL_CREDIT:
        return (0.0, 1.0, 0.0) # Green
    elif label == Label.PARTIAL_CREDIT:
        return (1.0, 0.75, 0.0) # Amber
    elif label == Label.MISCONCEPTION:
        return (1.0, 0.0, 0.0) # Red
    return (0.8, 0.8, 0.8) # Grey

def annotate(pdf_bytes: bytes, score: ScoreResult) -> bytes:
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        raise PermanentError(f"Failed to open PDF: {e}")

    original_page_count = doc.page_count
    
    # To handle stacking of labels
    label_y_offsets = {} # (page) -> list of y_max

    for crit in score.per_criterion:
        if crit.label == Label.NO_CREDIT and not crit.evidence_bboxes:
            continue
            
        color = get_color(crit.label)
        border_color = (0.5, 0.5, 0.5) if not crit.trusted else color
        fill_color = (0.5, 0.5, 0.5) if not crit.trusted else color
        dashes = "[3] 0" if not crit.trusted else None

        merged = merge_bboxes(crit.evidence_bboxes)
        
        for bbox in merged:
            page_idx = bbox.page - 1
            if page_idx < 0 or page_idx >= original_page_count:
                print(f"Warning: bbox page {bbox.page} out of range")
                continue
                
            page = doc[page_idx]
            rect = fitz.Rect(bbox.x, bbox.y, bbox.x + bbox.w, bbox.y + bbox.h)
            
            # transform if rotated
            if page.rotation != 0:
                # We assume bboxes were extracted with rotation normalized to 0
                # But PyMuPDF drawing uses unrotated coordinates if we don't set rotation.
                # Actually, shape drawing is on unrotated coords.
                pass
                
            shape = page.new_shape()
            shape.draw_rect(rect)
            shape.finish(color=border_color, fill=fill_color, fill_opacity=0.3, dashes=dashes)
            shape.commit()
            
            # Add label in margin
            margin_x = page.rect.width - 100
            if margin_x < bbox.x + bbox.w + 10:
                margin_x = 10 # try left margin
                
            label_text = f"{crit.criterion_id}: {crit.label.value} ({crit.marks}m)"
            
            # handle overlap
            if page_idx not in label_y_offsets:
                label_y_offsets[page_idx] = []
            
            y_pos = rect.y0
            for existing_y in sorted(label_y_offsets[page_idx]):
                if abs(existing_y - y_pos) < 15:
                    y_pos = existing_y + 15
            
            label_y_offsets[page_idx].append(y_pos)
            
            page.insert_text((margin_x, y_pos + 10), label_text, color=border_color, fontsize=8)

    # Append summary page
    summary_page = doc.new_page()
    y = 50
    summary_page.insert_text((50, y), "Grading Summary", fontsize=18, fontname="hebo")
    y += 30
    summary_page.insert_text((50, y), f"Document ID: {score.doc_id}", fontsize=12)
    y += 20
    summary_page.insert_text((50, y), f"Rubric ID: {score.rubric_id}", fontsize=12)
    y += 20
    if score.needs_review:
        summary_page.insert_text((50, y), "NEEDS REVIEW", fontsize=12, color=(1.0, 0.0, 0.0), fontname="hebo")
        y += 20
    
    summary_page.insert_text((50, y), f"Total Score: {score.total} / {score.max_total}", fontsize=14, fontname="hebo")
    y += 30
    
    summary_page.insert_text((50, y), "Criterion", fontsize=10, fontname="hebo")
    summary_page.insert_text((200, y), "Label", fontsize=10, fontname="hebo")
    summary_page.insert_text((350, y), "Marks", fontsize=10, fontname="hebo")
    summary_page.insert_text((450, y), "Trusted", fontsize=10, fontname="hebo")
    y += 20
    
    for crit in score.per_criterion:
        summary_page.insert_text((50, y), str(crit.criterion_id), fontsize=10)
        summary_page.insert_text((200, y), crit.label.value, fontsize=10, color=get_color(crit.label))
        summary_page.insert_text((350, y), str(crit.marks), fontsize=10)
        summary_page.insert_text((450, y), str(crit.trusted), fontsize=10, color=(0,0,0) if crit.trusted else (1,0,0))
        y += 20

    y += 30
    summary_page.insert_text((50, y), "Legend:", fontsize=12, fontname="hebo")
    y += 20
    summary_page.insert_text((50, y), "Green = FULL_CREDIT, Amber = PARTIAL_CREDIT, Red = MISCONCEPTION, Grey Dashed = UNTRUSTED", fontsize=10)

    return doc.write()
