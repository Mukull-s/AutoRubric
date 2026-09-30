import fitz
import io
import os
from pydantic import BaseModel
from autorubric.core.errors import PermanentError
from autorubric.contracts import Token, BBox

class ExtractionConfig(BaseModel):
    tiny_font_threshold: float = 2.0
    near_white_threshold: float = 2.9  # sum of RGB
    off_page_tolerance: float = 5.0
    ocr_backend: str = "auto"

def _is_color_near_white(color_tuple):
    # PyMuPDF colors are usually tuples of floats 0.0 to 1.0
    # or sometimes integers. Let's assume 0.0 to 1.0 for RGB
    if not color_tuple:
        return False
    if len(color_tuple) >= 3:
        return sum(color_tuple[:3]) >= 2.9
    elif len(color_tuple) == 1:
        return color_tuple[0] >= 0.95
    return False

def _rect_covered_by_drawings(word_rect, drawings):
    word_center = word_rect.tl + (word_rect.br - word_rect.tl) / 2
    for d in drawings:
        if d.get("fill_opacity", 1.0) > 0.9 and d.get("type", "f") != "s":
            # It's a filled drawing
            d_rect = d.get("rect")
            if d_rect and d_rect.contains(word_center):
                return True
    return False

def extract(pdf_bytes: bytes) -> list[Token]:
    config = ExtractionConfig()
    if os.environ.get("EXTRACTION_OCR"):
        config.ocr_backend = os.environ.get("EXTRACTION_OCR")

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        raise PermanentError(f"Failed to open PDF: {e}")

    if doc.is_encrypted or doc.page_count == 0:
        raise PermanentError("PDF is encrypted or empty")

    tokens = []
    
    for page_idx in range(doc.page_count):
        page = doc[page_idx]
        rotation = page.rotation
        
        # normalize to unrotated visual orientation
        if rotation != 0:
            page.set_rotation(0)

        page_rect = page.rect
        page_num = page_idx + 1

        words = page.get_text("words", clip=fitz.Rect(-2000, -2000, 5000, 5000))
        words.sort(key=lambda w: (w[5], w[6], w[7]))
        
        if not words:
            # Check for OCR if enabled
            if config.ocr_backend == "auto":
                try:
                    import paddleocr
                    # Not fully implemented yet, just skip with warning
                    print(f"Warning: Page {page_num} has no text layer, OCR not fully implemented.")
                except ImportError:
                    print(f"Warning: Page {page_num} has no text layer and paddleocr is not installed. Skipping.")
            continue

        traces = page.get_texttrace()
        drawings = page.get_drawings()

        for w in words:
            x0, y0, x1, y1, text, block_no, line_no, word_no = w
            w_rect = fitz.Rect(x0, y0, x1, y1)
            w_center = w_rect.tl + (w_rect.br - w_rect.tl) / 2
            
            # Find matching trace
            matched_trace = None
            for t in traces:
                t_rect = fitz.Rect(t.get("bbox"))
                if t_rect.contains(w_center):
                    matched_trace = t
                    break
            
            is_hidden = False
            
            # (c) bbox outside page
            if not page_rect.contains(w_rect):
                # allow some tolerance
                expanded_rect = page_rect + (config.off_page_tolerance, config.off_page_tolerance, config.off_page_tolerance, config.off_page_tolerance)
                if not expanded_rect.contains(w_rect):
                    is_hidden = True

            # (d) covered by opaque filled drawing
            if not is_hidden and _rect_covered_by_drawings(w_rect, drawings):
                is_hidden = True

            if matched_trace and not is_hidden:
                # (a) colour near-white
                if _is_color_near_white(matched_trace.get("color")):
                    is_hidden = True
                
                # (b) font size below threshold
                if matched_trace.get("size", 12.0) < config.tiny_font_threshold:
                    is_hidden = True
                
                # (e) invisible render mode or zero opacity
                if matched_trace.get("type", 0) == 3 or matched_trace.get("opacity", 1.0) == 0.0:
                    is_hidden = True

            token_id = f"t{page_num}_{block_no}_{word_no}_{int(x0)}_{int(y0)}"
            bbox = BBox(x=x0, y=y0, w=x1-x0, h=y1-y0, page=page_num)
            
            tokens.append(Token(
                id=token_id,
                text=text,
                page=page_num,
                bbox=bbox,
                block_id=f"b{page_num}_{block_no}",
                is_hidden=is_hidden
            ))

    return tokens
