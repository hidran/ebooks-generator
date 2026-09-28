import subprocess, sys, pathlib, yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIX = ROOT / "tests/fixtures/sample-book/book.yaml"
SCRIPT = ROOT / "tools/lib/make-metadata.py"

def gen(lang):
    out = subprocess.run([sys.executable, str(SCRIPT), str(FIX), lang],
                         capture_output=True, text=True, check=True).stdout
    # strip the --- fences for parsing
    body = out.strip().strip("-")
    return yaml.safe_load(body)

def test_metadata_core():
    m = gen("en")
    assert m["title"] == "Sample Book"
    assert m["author"] == "Test Author"
    assert m["language"] == "en-US"
    assert "toc" not in m
    assert m["toc-title"] == "Contents"

def test_language_maps_es():
    m = gen("es")
    assert m["language"] == "es-ES"
    assert m["toc-title"] == "Índice"


def test_edition_inherits_book_level_rights_and_publisher():
    m = gen("en")
    assert m["rights"] == "© 2026 Test Author."
    assert m["publisher"] == "Selftest"


def test_edition_overrides_rights_and_publisher():
    m = gen("es")
    assert m["title"] == "Libro de muestra"
    assert m["rights"] == "© 2026 Test Author. Todos los derechos reservados."
    assert m["publisher"] == "Autoedición"


def test_edition_without_override_keeps_book_keywords():
    assert gen("es")["keywords"] == ["sample", "fixture"]
