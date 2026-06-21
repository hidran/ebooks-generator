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
    assert m["toc"] is True

def test_language_maps_es():
    m = gen("es")
    assert m["language"] == "es-ES"
