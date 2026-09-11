"""docx-update-toc.py fills pandoc's empty DOCX TOC field with page numbers via
LibreOffice and exports the PDF from the same layout."""
import pathlib, re, subprocess, sys, zipfile

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tools/lib/docx-update-toc.py"
PANDOC = pathlib.Path("/opt/homebrew/bin/pandoc")
SOFFICE = pathlib.Path("/opt/homebrew/bin/soffice")

pytestmark = pytest.mark.skipif(not (PANDOC.exists() and SOFFICE.exists()),
                                reason="pandoc + LibreOffice required")

MD = "# Prefazione\n\n## Una domanda\n\nTesto.\n\n" + "\n\n".join(
    f"# Capitolo {i}\n\n## {i}.1 Passo\n\n" + ("Testo. " * 400) for i in range(1, 4))


def build_docx(tmp_path):
    md = tmp_path / "b.md"; md.write_text(MD, encoding="utf-8")
    docx = tmp_path / "b.docx"
    subprocess.run([str(PANDOC), "-M", "title=Prova", "-M", "toc-title=Sommario",
                    "--toc", "--toc-depth=2", "--reference-doc", str(ROOT / "tools/lib/paperback.docx"),
                    "-o", str(docx), str(md)], check=True)
    return docx


def doc_xml(docx):
    with zipfile.ZipFile(docx) as z:
        return z.read("word/document.xml").decode("utf-8")


def test_pandoc_toc_field_starts_empty(tmp_path):
    x = doc_xml(build_docx(tmp_path))
    assert "TOC \\o" in x
    assert "Capitolo 3" in x and x.count("Capitolo 3") == 1  # heading only, no TOC entry yet


def test_fills_docx_toc_and_exports_pdf(tmp_path):
    docx = build_docx(tmp_path)
    before = doc_xml(docx)
    pdf = tmp_path / "b.pdf"
    out = subprocess.run([sys.executable, str(SCRIPT), str(docx), "--docx", str(docx), "--pdf", str(pdf)],
                         capture_output=True, text=True, check=True).stdout
    assert "TOC filled (8 entries)" in out
    x = doc_xml(docx)
    assert "TOC \\o &quot;1-2&quot;" in x                     # pandoc's field kept, so Word can refresh it
    assert x.count("Capitolo 3") == 2                          # heading + TOC entry
    assert len(re.findall(r'w:pStyle w:val="TOC1"', x)) == 4 and len(re.findall(r'w:pStyle w:val="TOC2"', x)) == 4
    anchors = re.findall(r'<w:hyperlink w:anchor="(_Toc\d+)"', x)
    assert anchors == [f"_Toc{i}" for i in range(1, 9)]
    assert all(f'w:name="{a}"' in x for a in anchors)          # every entry links to a heading bookmark
    with zipfile.ZipFile(docx) as z:
        sty = z.read("word/styles.xml").decode()
    assert 'w:styleId="TOC1"' in sty and 'w:leader="dot"' in sty
    # page setup is pandoc's, untouched (a LibreOffice re-export would drift to 12983)
    assert re.search(r'<w:pgSz w:h="12960" w:w="8640"', x) and re.search(r'<w:pgSz w:h="12960" w:w="8640"', before)
    text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True,
                          text=True, check=True).stdout
    assert re.search(r"Capitolo 3\.{3,}\s*\d+", text), text[:800]
    pages = [int(n) for n in re.findall(r"Capitolo \d\.{3,}\s*(\d+)", text)]
    assert pages == sorted(pages) and pages[-1] > pages[0]   # real, increasing page numbers


def test_no_toc_field_is_reported_not_fatal(tmp_path):
    md = tmp_path / "p.md"; md.write_text("# Solo\n\nTesto.\n")
    docx = tmp_path / "p.docx"
    subprocess.run([str(PANDOC), "-o", str(docx), str(md)], check=True)
    res = subprocess.run([sys.executable, str(SCRIPT), str(docx), "--pdf", str(tmp_path / "p.pdf")],
                         capture_output=True, text=True)
    assert res.returncode == 0
    assert "no TOC field" in res.stderr
    assert (tmp_path / "p.pdf").exists()
