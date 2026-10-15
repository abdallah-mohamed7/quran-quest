"""Convert your mushaf PDF into public/quran/pages/001.webp ... 604.webp"""
import io
import pathlib
import fitz  # PyMuPDF
from PIL import Image

PDF_PATH = "mushaf.pdf"                       # ← change me
OUT_DIR  = pathlib.Path("public/quran/pages")
DPI      = 150
QUALITY  = 82

OUT_DIR.mkdir(parents=True, exist_ok=True)
doc = fitz.open(PDF_PATH)
print(f"Opened {PDF_PATH}: {doc.page_count} pages")

for i, page in enumerate(doc, start=1):
    pix = page.get_pixmap(dpi=DPI)
    img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    out = OUT_DIR / f"{i:03d}.webp"
    img.save(out, "WEBP", quality=QUALITY, method=6)
    if i % 20 == 0 or i == doc.page_count:
        print(f"  page {i}/{doc.page_count}")

print("Done.")