#!/usr/bin/env python3
"""Normalize every page box of a PDF to an exact trim size.

LibreOffice's DOCX->PDF export nudges the page height by ~1.16 pt, which can
trip KDP's print interior size check. The source DOCX is exactly 6x9, so we
snap the PDF MediaBox/CropBox to the exact trim (default 432 x 648 pt = 6x9").
The 1.16 pt removed is blank top margin; no content is affected.

Usage: fix-pdf-trim.py <pdf> [width_pt] [height_pt]
"""
import sys
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject

path = sys.argv[1]
W = float(sys.argv[2]) if len(sys.argv) > 2 else 432.0   # 6 in
H = float(sys.argv[3]) if len(sys.argv) > 3 else 648.0   # 9 in

reader = PdfReader(path)
writer = PdfWriter()
for page in reader.pages:
    box = RectangleObject((0, 0, W, H))
    page.mediabox = box
    page.cropbox = box
    writer.add_page(page)

with open(path, "wb") as fh:
    writer.write(fh)

print(f"  normalized {len(reader.pages)} pages to {W:.0f} x {H:.0f} pt")
