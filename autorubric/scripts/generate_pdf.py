import fitz # PyMuPDF

def generate_fixture_pdf():
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 50), "This is a valid dummy PDF for testing.", fontsize=12)
    
    # Optional: draw some bounding boxes to match fixture data
    page.draw_rect(fitz.Rect(10.0, 20.0, 150.0, 30.0), color=(0, 1, 0), fill_opacity=0.2)
    
    doc.save("backend/tests/fixtures/annotation/annotated.pdf")

if __name__ == "__main__":
    generate_fixture_pdf()
