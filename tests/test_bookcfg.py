import subprocess, sys, pathlib, textwrap

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIX = ROOT / "tests/fixtures/sample-book/book.yaml"
SCRIPT = ROOT / "tools/lib/bookcfg.py"


def run(*args, yaml_path=None):
    path = yaml_path if yaml_path is not None else FIX
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(path), *args],
        capture_output=True, text=True, check=True, cwd=ROOT
    ).stdout


def test_shellvars_has_core_fields():
    out = run("shellvars")
    assert "SLUG=sample-book" in out
    assert "PRIMARY_LANG=en" in out
    assert "TRIM=6x9" in out
    assert "FORMATS='epub paperback'" in out
    assert "EDITIONS='en es'" in out
    assert "TRANSLATE_FROM_es=en" in out
    assert "TRANS_MODEL=large-v3" in out
    assert "TRANS_LANG=en" in out


def test_hyphenated_lang_sanitized(tmp_path):
    yaml_content = textwrap.dedent("""\
        slug: test-book
        title: "Test"
        primary_language: en
        editions:
          - lang: es-MX
            translate_from: en
        transcription:
          model: large-v3
          language: en
    """)
    yaml_file = tmp_path / "book.yaml"
    yaml_file.write_text(yaml_content)
    out = run("shellvars", yaml_path=yaml_file)
    assert "TRANSLATE_FROM_es_MX=en" in out
    assert "TRANSLATE_FROM_es-MX" not in out
