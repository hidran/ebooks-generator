"""The paperback PDF should have exact trim boxes and no print annotations."""
import pathlib
import subprocess
import sys

from pypdf import PdfReader, PdfWriter
from pypdf.annotations import Link


SCRIPT = pathlib.Path(__file__).resolve().parent.parent / "tools/fix-pdf-trim.py"


def test_trim_removes_link_annotations(tmp_path):
    pdf = tmp_path / "paperback.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=432, height=649.162)
    writer.add_annotation(0, Link(rect=(50, 50, 100, 65), url="https://example.com"))
    with pdf.open("wb") as output:
        writer.write(output)

    result = subprocess.run([sys.executable, str(SCRIPT), str(pdf), "432", "648"],
                            text=True, capture_output=True, check=True)
    page = PdfReader(pdf).pages[0]
    assert tuple(float(value) for value in page.mediabox) == (0, 0, 432, 648)
    assert "/Annots" not in page
    assert "removed 1 non-printing annotations" in result.stdout
