import pathlib
import sys

import pytest
import yaml
from pptx.util import Emu

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools/slides"))

import deckgen  # noqa: E402
from deckgen import diagrams, shapes, theme  # noqa: E402

SPEC = ROOT / "books/neuron-course/slides/en/module-01.yaml"

SLIDE_W_IN = 13.333
SLIDE_H_IN = 7.5


@pytest.fixture(scope="module")
def spec():
    return yaml.safe_load(SPEC.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def deck(spec):
    return deckgen.build(spec)


# ----------------------------------------------------------------- theme
def test_body_area_fits_the_slide():
    assert diagrams.BX + diagrams.BW <= SLIDE_W_IN
    assert diagrams.BY + diagrams.BH <= Emu(theme.FOOTER_Y).inches


def test_body_constants_track_the_theme():
    """diagrams.py caches the body box; it must not drift from theme.py."""
    assert diagrams.BY == pytest.approx(Emu(theme.BODY_Y).inches)
    assert diagrams.BH == pytest.approx(Emu(theme.BODY_H).inches)
    assert diagrams.BW == pytest.approx(Emu(theme.CONTENT_W).inches)


def test_every_tone_resolves_to_three_colours():
    for name, value in theme.TONES.items():
        assert len(value) == 3, name


# ----------------------------------------------------------------- markup
@pytest.mark.parametrize("text,expected", [
    ("plain", [("plain", "plain")]),
    ("call `foo()` now", [("call ", "plain"), ("foo()", "mono"), (" now", "plain")]),
    ("**bold** tail", [("bold", "bold"), (" tail", "plain")]),
    ("", [("", "plain")]),
])
def test_rich_runs_splits_inline_markup(text, expected):
    assert shapes.rich_runs(text) == expected


# ----------------------------------------------------------------- build
def test_slide_count_matches_the_spec(spec, deck):
    expected = (
        len(spec.get("slides", []))
        + sum(1 + len(lesson.get("slides", [])) for lesson in spec["lessons"])
        + len(spec.get("closing", []))
    )
    assert deck.slide_count == expected


def test_every_lesson_is_covered(spec):
    """The deck must carry all seven theory lessons of Module 1."""
    ids = [lesson["id"] for lesson in spec["lessons"]]
    assert ids == ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7"]
    for lesson in spec["lessons"]:
        layouts = [s["layout"] for s in lesson["slides"]]
        assert layouts[0] == "objectives", lesson["id"]
        assert layouts[-1] == "takeaways", lesson["id"]


def test_all_layouts_used_are_known(spec):
    used = {s["layout"] for s in spec.get("slides", [])}
    used |= {s["layout"] for l in spec["lessons"] for s in l["slides"]}
    used |= {s["layout"] for s in spec.get("closing", [])}
    assert used <= set(deckgen.RENDERERS)


def test_unknown_layout_is_rejected():
    with pytest.raises(deckgen.SpecError):
        deckgen.build({"deck": {}, "slides": [{"layout": "nope"}]})


def test_shapes_stay_inside_the_slide(deck):
    """Nothing may hang off the canvas — it would be cropped on export."""
    tol = Emu(0.02).emu if hasattr(Emu(0.02), "emu") else 18288
    for i, slide in enumerate(deck.prs.slides):
        for shape in slide.shapes:
            if shape.left is None or shape.width is None:
                continue
            assert shape.left >= -tol, f"slide {i + 1}: {shape.shape_type} off left"
            assert shape.left + shape.width <= deck.prs.slide_width + tol, (
                f"slide {i + 1}: {shape.shape_type} overruns the right edge"
            )
            assert shape.top + shape.height <= deck.prs.slide_height + tol, (
                f"slide {i + 1}: {shape.shape_type} overruns the bottom edge"
            )


def test_diagram_and_chart_slides_get_a_heading(spec, deck):
    """Diagram layouts rely on the engine to draw their title."""
    visual = set(diagrams.RENDERERS) | {"chart", "big_number"}
    for lesson in spec["lessons"]:
        for slide_spec in lesson["slides"]:
            if slide_spec["layout"] in visual:
                assert slide_spec.get("title"), slide_spec["layout"]


def test_saves_a_readable_pptx(deck, tmp_path):
    from pptx import Presentation

    out = tmp_path / "deck.pptx"
    deck.save(out)
    assert out.stat().st_size > 20_000
    assert len(Presentation(str(out)).slides._sldIdLst) == deck.slide_count
