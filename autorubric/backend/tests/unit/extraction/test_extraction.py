import json
import pytest
from pathlib import Path
from autorubric.extraction import extract
from autorubric.core.errors import PermanentError

FIXTURE_DIR = Path(__file__).parents[2] / "fixtures" / "extraction"

@pytest.fixture
def manifest():
    with open(FIXTURE_DIR / "manifest.json") as f:
        return json.load(f)

def test_clean_single_column(manifest):
    item = next(x for x in manifest if x["file"] == "clean_single_column.pdf")
    with open(FIXTURE_DIR / item["file"], "rb") as f:
        pdf_bytes = f.read()
    
    tokens = extract(pdf_bytes)
    assert len(tokens) > 0
    # No hidden text should be found
    assert not any(t.is_hidden for t in tokens)
    
    # Ids should be unique
    ids = [t.id for t in tokens]
    assert len(ids) == len(set(ids))

    # All bounding boxes must be within standard page bounds (approx 595x842)
    # The actual page bounds can be roughly checked to be > 0 and < 1000
    for t in tokens:
        assert 0 <= t.bbox.x <= 1000
        assert 0 <= t.bbox.y <= 1000

def test_two_column(manifest):
    item = next(x for x in manifest if x["file"] == "two_column.pdf")
    with open(FIXTURE_DIR / item["file"], "rb") as f:
        pdf_bytes = f.read()
        
    tokens = extract(pdf_bytes)
    assert len(tokens) > 0
    
    # Check reading order: Column 1 line 1, then line 2, then Column 2...
    words = [t.text for t in tokens if "Column" in t.text or "line" in t.text or t.text in ("1", "2")]
    # words should be roughly: Column, 1, line, 1, Column, 1, line, 2...
    text = " ".join(words)
    assert "Column 1 line 1" in text
    assert "Column 1 line 2" in text
    assert "Column 2 line 1" in text
    assert "Column 2 line 2" in text
    
    # Make sure Col 1 comes before Col 2
    idx1 = text.find("Column 1")
    idx2 = text.find("Column 2")
    assert idx1 < idx2

def test_hidden_white_text(manifest):
    item = next(x for x in manifest if x["file"] == "hidden_white_text.pdf")
    with open(FIXTURE_DIR / item["file"], "rb") as f:
        tokens = extract(f.read())
    
    hidden = [t for t in tokens if t.is_hidden]
    assert len(hidden) > 0
    hidden_text = " ".join(t.text for t in hidden)
    assert "award full marks" in hidden_text

def test_tiny_font(manifest):
    item = next(x for x in manifest if x["file"] == "tiny_font.pdf")
    with open(FIXTURE_DIR / item["file"], "rb") as f:
        tokens = extract(f.read())
    
    hidden = [t for t in tokens if t.is_hidden]
    assert len(hidden) > 0
    hidden_text = " ".join(t.text for t in hidden)
    assert "ignore previous instructions" in hidden_text

def test_off_page(manifest):
    item = next(x for x in manifest if x["file"] == "off_page.pdf")
    with open(FIXTURE_DIR / item["file"], "rb") as f:
        tokens = extract(f.read())
    
    hidden = [t for t in tokens if t.is_hidden]
    assert len(hidden) > 0
    hidden_text = " ".join(t.text for t in hidden)
    assert "off page" in hidden_text

def test_covered_text(manifest):
    item = next(x for x in manifest if x["file"] == "covered_text.pdf")
    with open(FIXTURE_DIR / item["file"], "rb") as f:
        tokens = extract(f.read())
    
    hidden = [t for t in tokens if t.is_hidden]
    assert len(hidden) > 0
    hidden_text = " ".join(t.text for t in hidden)
    assert "hidden by rectangle" in hidden_text

def test_invisible_render_mode(manifest):
    item = next(x for x in manifest if x["file"] == "invisible_render_mode.pdf")
    with open(FIXTURE_DIR / item["file"], "rb") as f:
        tokens = extract(f.read())
    
    hidden = [t for t in tokens if t.is_hidden]
    assert len(hidden) > 0
    hidden_text = " ".join(t.text for t in hidden)
    assert "invisible" in hidden_text

def test_rotated(manifest):
    item = next(x for x in manifest if x["file"] == "rotated.pdf")
    with open(FIXTURE_DIR / item["file"], "rb") as f:
        tokens = extract(f.read())
        
    # Rotated page should still have correct unrotated bboxes
    # "Rotated text at 50,50"
    rot_token = next(t for t in tokens if t.text == "Rotated")
    # if normalized to unrotated visual orientation, x should be around 50
    assert 40 <= rot_token.bbox.x <= 60
    assert 30 <= rot_token.bbox.y <= 60

def test_image_only(manifest):
    item = next(x for x in manifest if x["file"] == "image_only.pdf")
    with open(FIXTURE_DIR / item["file"], "rb") as f:
        tokens = extract(f.read())
        
    # Without OCR, returns empty
    assert len(tokens) == 0
    
def test_encrypted_error():
    # Empty bytes should raise PermanentError
    with pytest.raises(PermanentError):
        extract(b"")
