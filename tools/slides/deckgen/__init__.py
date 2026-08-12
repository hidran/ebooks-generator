"""Course slide generator for the ebooks pipeline.

A deck is described by a YAML spec holding text only; every visual decision
lives here in Python, so a translated deck reuses the same geometry.
"""
from . import charts, diagrams, layouts, shapes, theme
from .deck import Deck

__all__ = ["Deck", "build", "RENDERERS", "charts", "diagrams", "layouts",
           "shapes", "theme"]

# layout name → renderer(deck, slide, spec)
RENDERERS = dict(layouts.RENDERERS)
RENDERERS.update(
    {name: (lambda fn: lambda deck, slide, spec: fn(slide, spec))(fn)
     for name, fn in diagrams.RENDERERS.items()}
)
RENDERERS["chart"] = lambda deck, slide, spec: charts.chart(slide, spec)
RENDERERS["big_number"] = lambda deck, slide, spec: charts.big_number(slide, spec)

# Layouts that draw their own full-bleed chrome and need no title/footer.
FULL_BLEED = {"cover", "divider", "outro"}


class SpecError(ValueError):
    pass


def build(spec):
    """Turn a parsed YAML spec into a Deck."""
    meta = spec.get("deck", {})
    lessons = [lesson["id"] for lesson in spec.get("lessons", [])]
    deck = Deck(
        title=meta.get("title", ""),
        subtitle=meta.get("subtitle", ""),
        module=meta.get("module", ""),
        lessons=lessons,
    )

    for slide_spec in spec.get("slides", []):
        _render(deck, slide_spec)

    for lesson in spec.get("lessons", []):
        deck.current = (lesson["id"], lesson["title"])
        _render(deck, {
            "layout": "divider",
            "number": lesson["id"],
            "title": lesson["title"],
            "duration": lesson.get("duration"),
            "type": lesson.get("type"),
            "notes": lesson.get("notes"),
        })
        for slide_spec in lesson.get("slides", []):
            _render(deck, slide_spec)
    deck.current = None

    for slide_spec in spec.get("closing", []):
        _render(deck, slide_spec)

    return deck


def _render(deck, slide_spec):
    name = slide_spec.get("layout")
    renderer = RENDERERS.get(name)
    if renderer is None:
        raise SpecError(
            f"unknown layout {name!r}; known: {', '.join(sorted(RENDERERS))}"
        )
    slide = deck.blank(footer=name not in FULL_BLEED)
    if name in diagrams.RENDERERS or name in ("chart", "big_number"):
        deck.heading(slide, slide_spec["title"], slide_spec.get("kicker"))
    renderer(deck, slide, slide_spec)
    deck.speaker_notes(slide, slide_spec.get("notes"))
    return slide
