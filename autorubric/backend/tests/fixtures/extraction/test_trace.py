import fitz
from pathlib import Path
import pprint

def inspect():
    out_dir = Path(__file__).parent
    doc = fitz.open(out_dir / "clean_single_column.pdf")
    page = doc[0]
    print("clean:")
    pprint.pprint(page.get_texttrace()[0])
    
    doc2 = fitz.open(out_dir / "invisible_render_mode.pdf")
    print("invisible:")
    pprint.pprint(doc2[0].get_texttrace()[1])

if __name__ == "__main__":
    inspect()
