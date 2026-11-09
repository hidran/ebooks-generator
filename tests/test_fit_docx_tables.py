"""Paperback tables must fit the page's configured printable area."""
import pathlib
import re
import subprocess
import sys
import zipfile

import pytest


ROOT = pathlib.Path(__file__).resolve().parent.parent
PANDOC = pathlib.Path("/opt/homebrew/bin/pandoc")
SCRIPT = ROOT / "tools/lib/fit-docx-tables.py"


@pytest.mark.skipif(not PANDOC.exists(), reason="pandoc required")
@pytest.mark.parametrize("reference", ["paperback.docx", "paperback-7.5x9.25.docx"])
def test_tables_fit_printable_width(reference, tmp_path):
    markdown = tmp_path / "table.md"
    markdown.write_text(
        "# Chapter\n\n| Found by | Priority |\n| :---- | :---- |\n"
        "| Every model | Critical, mandatory correction before deployment |\n",
        encoding="utf-8",
    )
    docx = tmp_path / "book.docx"
    subprocess.run([str(PANDOC), "--reference-doc", str(ROOT / "tools/lib" / reference),
                    "-o", str(docx), str(markdown)], check=True)

    def document_xml():
        with zipfile.ZipFile(docx) as archive:
            return archive.read("word/document.xml").decode("utf-8")

    def grid_width(xml):
        grid = re.search(r"<w:tblGrid>(.*?)</w:tblGrid>", xml, re.S).group(1)
        return sum(map(int, re.findall(r'<w:gridCol w:w="(\d+)"', grid)))

    before = document_xml()
    page = re.search(r'<w:pgSz w:h="\d+" w:w="(\d+)"', before)
    margins = re.search(r'<w:pgMar\b[^>]*w:left="(\d+)"[^>]*w:right="(\d+)"', before)
    printable = int(page.group(1)) - int(margins.group(1)) - int(margins.group(2))
    if reference == "paperback.docx":
        assert grid_width(before) > printable  # reproduces Pandoc's oversized grid
    else:
        assert grid_width(before) < printable  # larger trim needs no adjustment

    subprocess.run([sys.executable, str(SCRIPT), str(docx)], check=True)
    after = document_xml()
    assert grid_width(after) == min(grid_width(before), printable)
    assert "Critical, mandatory correction before deployment" in after
    subprocess.run([sys.executable, str(SCRIPT), str(docx)], check=True)
    assert document_xml() == after  # safe to run again
