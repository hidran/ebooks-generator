"""Palette, type scale and geometry for the course decks.

One accent colour, used sparingly, is what makes nine hours of video read as one
system. Everything else is greyscale plus three semantic colours reserved for
meaning (cost, breakage, survival) rather than decoration.
"""
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt


def _rgb(h):
    return RGBColor.from_string(h)


# ---------------------------------------------------------------- palette
BG = _rgb("16181D")
SURFACE = _rgb("1F232B")
SURFACE_2 = _rgb("272C36")
TEXT = _rgb("ECEFF4")
MUTED = _rgb("8B93A3")
DIM = _rgb("5B6373")
ACCENT = _rgb("7C6BF0")
ACCENT_SOFT = _rgb("2A2748")
WARN = _rgb("E8A33D")
WARN_SOFT = _rgb("332A1B")
DANGER = _rgb("E4664F")
DANGER_SOFT = _rgb("32211D")
OK = _rgb("4FBF8B")
OK_SOFT = _rgb("1B2B25")
LINE = _rgb("343A45")

# Semantic aliases used by spec files via the `tone` field.
TONES = {
    "neutral": (SURFACE, LINE, TEXT),
    "accent": (ACCENT_SOFT, ACCENT, TEXT),
    "warn": (WARN_SOFT, WARN, TEXT),
    "danger": (DANGER_SOFT, DANGER, TEXT),
    "ok": (OK_SOFT, OK, TEXT),
    "ghost": (BG, LINE, MUTED),
}

# Chart series colours, in order.
SERIES = [ACCENT, WARN, OK, DANGER, MUTED]

# ---------------------------------------------------------------- type
FONT = "Inter"
MONO = "Menlo"

SZ_DECK_TITLE = Pt(42)
SZ_DIVIDER_NUM = Pt(80)
SZ_DIVIDER_TITLE = Pt(36)
SZ_TITLE = Pt(29)
SZ_KICKER = Pt(12)
SZ_LEAD = Pt(21)
SZ_BODY = Pt(17)
SZ_CARD_TITLE = Pt(15)
SZ_CARD_BODY = Pt(12)
SZ_NODE = Pt(13)
SZ_NODE_SM = Pt(11)
SZ_CAPTION = Pt(11)
SZ_CODE = Pt(13)
SZ_TABLE = Pt(12.5)
SZ_FOOTER = Pt(9.5)
SZ_BIGNUM = Pt(66)

# ---------------------------------------------------------------- geometry
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

MARGIN_X = Inches(0.85)
CONTENT_W = Inches(13.333 - 0.85 * 2)

TITLE_Y = Inches(0.58)
RULE_W = Inches(1.35)
BODY_Y = Inches(1.55)
BODY_H = Inches(5.02)
BODY_BOTTOM = Inches(6.57)

FOOTER_Y = Inches(6.92)
PROGRESS_Y = Inches(7.22)

GAP = Inches(0.22)
