import fitz
from pathlib import Path
doc = fitz.open(Path(__file__).parents[2] / "fixtures" / "extraction" / "off_page.pdf")
print("page rect:", doc[0].rect)
print("words:", doc[0].get_text("words", clip=fitz.Rect(-2000, -2000, 2000, 2000)))
