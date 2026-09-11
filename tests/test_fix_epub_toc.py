"""fix-epub-toc.py reshapes a pandoc EPUB so Kindle/KDP detects its table of
contents: a dedicated toc.xhtml page in the spine, referenced by file path from
both the OPF <guide> and the nav landmarks (pandoc points the landmark at a bare
"#toc" fragment inside nav.xhtml, which Amazon's converter does not resolve)."""
import pathlib, re, shutil, subprocess, sys, zipfile

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tools/lib/fix-epub-toc.py"
PANDOC = pathlib.Path("/opt/homebrew/bin/pandoc")

SAMPLE_MD = """\
# Prefazione

## Una domanda

Testo.

# Capitolo 1 — Inizio

## 1.1 Primo passo

Testo.

### Dettaglio

Testo.

# Capitolo 2 — Fine

Testo.
"""


def build_epub(tmp_path, lang="it-IT"):
    md = tmp_path / "book.md"
    md.write_text(SAMPLE_MD, encoding="utf-8")
    epub = tmp_path / "book.epub"
    subprocess.run([str(PANDOC), "-M", "title=Libro di prova", "-M", f"lang={lang}",
                    "--toc", "--toc-depth=2", "--split-level=1",
                    "-o", str(epub), str(md)], check=True)
    return epub


def fix(epub, *args):
    return subprocess.run([sys.executable, str(SCRIPT), str(epub), *args],
                          capture_output=True, text=True, check=True, cwd=ROOT).stdout


def read(epub, name):
    with zipfile.ZipFile(epub) as z:
        return z.read(name).decode("utf-8")


pytestmark = pytest.mark.skipif(not PANDOC.exists(), reason="pandoc not installed")


def test_pandoc_baseline_points_landmark_at_fragment(tmp_path):
    # Guard: if pandoc ever fixes this itself, the post-processor may be obsolete.
    epub = build_epub(tmp_path)
    nav = read(epub, "EPUB/nav.xhtml")
    assert re.search(r'<a href="#toc" epub:type="toc">', nav)


def test_creates_toc_page_in_spine_after_title_page(tmp_path):
    epub = build_epub(tmp_path)
    fix(epub)
    opf = read(epub, "EPUB/content.opf")
    toc = read(epub, "EPUB/toc.xhtml")

    assert '<item id="toc_page" href="toc.xhtml" media-type="application/xhtml+xml"' in opf
    spine = re.search(r"<spine.*?</spine>", opf, re.S).group(0)
    idrefs = re.findall(r'idref="([^"]+)"', spine)
    assert idrefs[:2] == ["title_page_xhtml", "toc_page"], idrefs
    assert "nav" not in idrefs  # logical nav stays out of the reading order

    assert "<h1" in toc and "Sommario" in toc  # it-IT → Sommario
    assert 'href="text/ch002.xhtml#capitolo-1-inizio"' in toc
    assert 'href="text/ch002.xhtml#primo-passo"' in toc
    assert "Dettaglio" not in toc  # toc-depth=2 respected (copied from pandoc's nav)


def test_guide_and_landmarks_reference_toc_page_by_path(tmp_path):
    epub = build_epub(tmp_path)
    fix(epub)
    opf = read(epub, "EPUB/content.opf")
    nav = read(epub, "EPUB/nav.xhtml")
    assert re.search(r'<reference type="toc" title="Sommario" href="toc.xhtml"\s*/>', opf)
    assert re.search(r'<a href="toc.xhtml" epub:type="toc">Sommario</a>', nav)
    assert '"#toc"' not in nav
    assert '<h1 id="toc-title">Sommario</h1>' in nav


def test_title_by_language_and_override(tmp_path):
    (tmp_path / "en").mkdir()
    en = build_epub(tmp_path / "en", lang="en-US")
    fix(en)
    assert ">Contents<" in read(en, "EPUB/toc.xhtml")

    (tmp_path / "es").mkdir()
    es = build_epub(tmp_path / "es", lang="es-ES")
    fix(es, "--title", "Tabla de contenidos")
    assert ">Tabla de contenidos<" in read(es, "EPUB/toc.xhtml")


def test_idempotent(tmp_path):
    epub = build_epub(tmp_path)
    fix(epub)
    once = {n: read(epub, n) for n in ("EPUB/content.opf", "EPUB/nav.xhtml", "EPUB/toc.xhtml")}
    fix(epub)
    twice = {n: read(epub, n) for n in ("EPUB/content.opf", "EPUB/nav.xhtml", "EPUB/toc.xhtml")}
    assert once == twice


def test_zip_layout_and_epubcheck(tmp_path):
    epub = build_epub(tmp_path)
    fix(epub)
    with zipfile.ZipFile(epub) as z:
        infos = z.infolist()
        assert infos[0].filename == "mimetype"
        assert infos[0].compress_type == zipfile.ZIP_STORED
        assert z.testzip() is None
    if shutil.which("epubcheck") is None:
        pytest.skip("epubcheck not installed")
    res = subprocess.run(["epubcheck", str(epub)], capture_output=True, text=True)
    assert res.returncode == 0, res.stdout + res.stderr
