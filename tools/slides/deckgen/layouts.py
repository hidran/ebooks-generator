"""Text-driven slide layouts."""
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

from . import shapes as S
from . import theme as T
from .diagrams import BH, BW, BX, BY, _I


# --------------------------------------------------------------- covers
def cover(deck, slide, spec):
    S.rect(slide, _I(0), _I(0), _I(0.14), T.SLIDE_H, fill=T.ACCENT, radius=0)
    S.textbox(slide, _I(1.35), _I(2.05), _I(10.2), _I(0.34),
              spec.get("kicker", deck.module), size=T.SZ_KICKER, color=T.ACCENT,
              bold=True, caps=True)
    S.textbox(slide, _I(1.35), _I(2.55), _I(10.2), _I(1.5), spec["title"],
              size=T.SZ_DECK_TITLE, color=T.TEXT, bold=True, spacing=1.05)
    S.rule(slide, _I(1.35), _I(4.22), _I(1.6))
    S.textbox(slide, _I(1.35), _I(4.55), _I(9.4), _I(0.8), spec.get("subtitle", ""),
              size=T.SZ_LEAD, color=T.MUTED, spacing=1.3)
    S.textbox(slide, _I(1.35), _I(5.85), _I(9.4), _I(0.4), spec.get("meta", ""),
              size=T.SZ_CAPTION, color=T.DIM, caps=True)


def divider(deck, slide, spec):
    """Lesson opener: number, title, duration."""
    S.rect(slide, _I(0), _I(0), _I(0.14), T.SLIDE_H, fill=T.ACCENT, radius=0)
    S.textbox(slide, _I(1.35), _I(1.95), _I(3.0), _I(1.4), spec["number"],
              size=T.SZ_DIVIDER_NUM, color=T.ACCENT, bold=True, spacing=0.9)
    S.textbox(slide, _I(1.35), _I(3.42), _I(10.0), _I(1.3), spec["title"],
              size=T.SZ_DIVIDER_TITLE, color=T.TEXT, bold=True, spacing=1.05)
    meta = " · ".join(x for x in (spec.get("duration"), spec.get("type")) if x)
    S.textbox(slide, _I(1.35), _I(4.92), _I(9.0), _I(0.34), meta,
              size=T.SZ_CAPTION, color=T.DIM, caps=True)


def agenda(deck, slide, spec):
    deck.heading(slide, spec.get("title", "In this module"), spec.get("kicker"))
    items = spec["items"]
    half = (len(items) + 1) // 2
    cols = [items[:half], items[half:]]
    cw = (BW - 0.5) / 2
    for c, column in enumerate(cols):
        for i, item in enumerate(column):
            y = BY + 0.1 + i * 0.78
            x = BX + c * (cw + 0.5)
            chip = S.rect(slide, _I(x), _I(y), _I(0.72), _I(0.5),
                          fill=T.SURFACE_2, radius=0.1)
            S.label(chip, item["id"], size=T.SZ_NODE_SM, color=T.ACCENT, bold=True)
            S.textbox(slide, _I(x + 0.9), _I(y + 0.03), _I(cw - 1.0), _I(0.3),
                      item["title"], size=T.SZ_CARD_TITLE, color=T.TEXT, bold=True)
            S.textbox(slide, _I(x + 0.9), _I(y + 0.3), _I(cw - 1.0), _I(0.26),
                      item.get("note", ""), size=T.SZ_CAPTION, color=T.MUTED)


# --------------------------------------------------------------- text
def objectives(deck, slide, spec):
    deck.heading(slide, spec.get("title", "What you will be able to do"),
                 spec.get("kicker", "Learning objectives"))
    points = spec.get("points", [])
    # With no sub-points the slide is mostly empty; sit the box on the optical
    # centre instead of leaving it stranded at the top.
    y0 = BY + 0.15 if points else BY + 1.1
    S.rect(slide, _I(BX), _I(y0), _I(BW), _I(1.9), fill=T.ACCENT_SOFT,
           line=T.ACCENT, radius=0.14)
    S.textbox(slide, _I(BX + 0.55), _I(y0 + 0.38), _I(BW - 1.1), _I(1.3),
              spec["text"], size=T.SZ_LEAD, color=T.TEXT, spacing=1.35)
    for i, item in enumerate(points):
        y = y0 + 2.28 + i * 0.62
        S.rect(slide, _I(BX + 0.06), _I(y + 0.16), _I(0.16), _I(0.16),
               fill=T.ACCENT, radius=0.08)
        S.textbox(slide, _I(BX + 0.46), _I(y), _I(BW - 0.46), _I(0.55), item,
                  size=T.SZ_BODY, color=T.MUTED, spacing=1.3)


def bullets(deck, slide, spec):
    deck.heading(slide, spec["title"], spec.get("kicker"))
    items = spec["items"]
    y = BY + 0.1
    if spec.get("lead"):
        S.textbox(slide, _I(BX), _I(y), _I(BW), _I(0.75), spec["lead"],
                  size=T.SZ_LEAD, color=T.TEXT, spacing=1.3)
        y += 0.95
    step = min(0.92, (BY + BH - 0.25 - y) / max(1, len(items)))
    for i, item in enumerate(items):
        if isinstance(item, str):
            item = {"text": item}
        iy = y + i * step
        marker = item.get("marker")
        if marker:
            chip = S.rect(slide, _I(BX), _I(iy + 0.02), _I(0.46), _I(0.4),
                          fill=T.SURFACE_2, radius=0.09)
            S.label(chip, marker, size=T.SZ_NODE_SM, color=T.ACCENT, bold=True)
        else:
            S.rect(slide, _I(BX + 0.06), _I(iy + 0.16), _I(0.15), _I(0.15),
                   fill=T.ACCENT, radius=0.075)
        tx = BX + (0.66 if marker else 0.46)
        S.textbox(slide, _I(tx), _I(iy), _I(BW - (tx - BX)), _I(step),
                  item["text"], size=T.SZ_BODY, color=T.TEXT, spacing=1.25)
        if item.get("note"):
            S.textbox(slide, _I(tx), _I(iy + 0.34), _I(BW - (tx - BX)), _I(step - 0.3),
                      item["note"], size=T.SZ_CARD_BODY, color=T.MUTED, spacing=1.25)


def lead(deck, slide, spec):
    """One sentence that deserves the whole slide."""
    if spec.get("title"):
        deck.heading(slide, spec["title"], spec.get("kicker"))
        y, h = BY + 0.4, BH - 1.0
    else:
        y, h = _I(2.0).inches, 3.0
    S.rule(slide, _I(BX), _I(y), _I(1.35))
    S.textbox(slide, _I(BX), _I(y + 0.42), _I(BW - 1.2), _I(h - 0.8), spec["text"],
              size=Pt(spec.get("size", 34)), color=T.TEXT, bold=True, spacing=1.2)
    if spec.get("note"):
        S.textbox(slide, _I(BX), _I(BY + BH - 0.75), _I(BW - 1.2), _I(0.7),
                  spec["note"], size=T.SZ_BODY, color=T.MUTED, spacing=1.3)


def cards(deck, slide, spec):
    deck.heading(slide, spec["title"], spec.get("kicker"))
    items = spec["items"]
    n = len(items)
    per_row = spec.get("columns", min(n, 4 if n % 4 == 0 or n > 3 else n))
    rows = (n + per_row - 1) // per_row
    gap = 0.28
    cw = (BW - gap * (per_row - 1)) / per_row
    avail = BH - 0.55
    ch = min(spec.get("height", 2.7), (avail - gap * (rows - 1)) / rows)
    # A single row stranded at the top reads as an unfinished slide; centre it.
    y0 = BY + ((avail - ch) / 2 if rows == 1 else 0.12)

    for i, item in enumerate(items):
        x = BX + (i % per_row) * (cw + gap)
        y = y0 + (i // per_row) * (ch + gap)
        fill, line, txt = T.TONES.get(item.get("tone", "neutral"), T.TONES["neutral"])
        box = S.rect(slide, _I(x), _I(y), _I(cw), _I(ch), fill=fill, line=line,
                     radius=0.12)
        tf = box.text_frame
        tf.margin_left = tf.margin_right = Emu(150000)
        tf.margin_top = Emu(120000)
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        if item.get("marker"):
            S.write(p, item["marker"], T.SZ_CAPTION, T.ACCENT, bold=True)
            p = tf.add_paragraph()
            p.space_before = Pt(4)
            p.alignment = PP_ALIGN.LEFT
        S.write(p, item["title"], T.SZ_CARD_TITLE, txt, bold=True)
        if item.get("text"):
            p2 = tf.add_paragraph()
            p2.alignment = PP_ALIGN.LEFT
            p2.line_spacing = 1.3
            p2.space_before = Pt(7)
            S.write(p2, item["text"], T.SZ_CARD_BODY, T.MUTED)


def table(deck, slide, spec):
    deck.heading(slide, spec["title"], spec.get("kicker"))
    cols = spec["columns"]
    rows = spec["rows"]
    widths = spec.get("widths") or [1] * len(cols)
    scale = BW / sum(widths)
    rh = min(0.5, (BH - 0.9) / (len(rows) + 1))
    y0 = BY + 0.12

    x = BX
    for j, col in enumerate(cols):
        w = widths[j] * scale
        S.textbox(slide, _I(x + 0.14), _I(y0 + 0.08), _I(w - 0.2), _I(0.3), col,
                  size=T.SZ_CAPTION, color=T.MUTED, bold=True, caps=True)
        x += w
    S.rect(slide, _I(BX), _I(y0 + rh - 0.03), _I(BW), Pt(1.2), fill=T.LINE, radius=0)

    for i, row in enumerate(rows):
        y = y0 + rh + i * rh
        emphasis = isinstance(row, dict) and row.get("tone")
        cells = row["cells"] if isinstance(row, dict) else row
        if emphasis:
            fill, line, _ = T.TONES[emphasis]
            S.rect(slide, _I(BX), _I(y), _I(BW), _I(rh - 0.04), fill=fill,
                   line=line, radius=0.07)
        x = BX
        for j, cell in enumerate(cells):
            w = widths[j] * scale
            colour = T.TEXT if (j == 0 or emphasis) else T.MUTED
            S.textbox(slide, _I(x + 0.14), _I(y + (rh - 0.3) / 2), _I(w - 0.2),
                      _I(0.3), str(cell), size=T.SZ_TABLE, color=colour,
                      bold=bool(emphasis) or j == 0)
            x += w
        if not emphasis and i < len(rows) - 1:
            S.rect(slide, _I(BX), _I(y + rh - 0.04), _I(BW), Pt(0.6),
                   fill=T.LINE, radius=0)

    if spec.get("caption"):
        S.textbox(slide, _I(BX), _I(BY + BH - 0.4), _I(BW), _I(0.4), spec["caption"],
                  size=T.SZ_CAPTION, color=T.WARN, bold=True)


def code(deck, slide, spec):
    deck.heading(slide, spec["title"], spec.get("kicker"))
    lines = spec["code"].rstrip("\n").split("\n")
    h = min(BH - 0.6, 0.34 + len(lines) * 0.245)
    w = spec.get("width", BW * 0.72)
    S.rect(slide, _I(BX), _I(BY + 0.1), _I(w), _I(h), fill=T.SURFACE, line=T.LINE,
           radius=0.12)
    box = S.textbox(slide, _I(BX + 0.34), _I(BY + 0.28), _I(w - 0.6), _I(h - 0.4),
                    "", size=T.SZ_CODE, color=T.TEXT)
    tf = box.text_frame
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = 1.28
        run = p.add_run()
        run.text = line or " "
        run.font.name = T.MONO
        run.font.size = T.SZ_CODE
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("//"):
            run.font.color.rgb = T.DIM
        elif spec.get("highlight") and any(k in line for k in spec["highlight"]):
            run.font.color.rgb = T.ACCENT
        else:
            run.font.color.rgb = T.TEXT

    # `notes` is reserved for speaker notes; on-slide annotations are side_notes.
    for i, note in enumerate(spec.get("side_notes", [])):
        ny = BY + 0.22 + i * 1.0
        S.textbox(slide, _I(BX + w + 0.45), _I(ny), _I(BW - w - 0.45), _I(0.9),
                  note, size=T.SZ_CARD_BODY, color=T.MUTED, spacing=1.35)


def takeaways(deck, slide, spec):
    deck.heading(slide, spec.get("title", "Key takeaways"),
                 spec.get("kicker", "Remember this"))
    items = spec["items"]
    h = min(0.95, (BH - 0.6) / len(items) - 0.16)
    for i, item in enumerate(items):
        y = BY + 0.15 + i * (h + 0.16)
        box = S.rect(slide, _I(BX), _I(y), _I(BW), _I(h), fill=T.SURFACE,
                     line=T.LINE, radius=0.1)
        tf = box.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.margin_left = Emu(700000)
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        p.line_spacing = 1.2
        S.write(p, item, T.SZ_BODY, T.TEXT)
        chip = S.rect(slide, _I(BX + 0.24), _I(y + (h - 0.34) / 2), _I(0.34),
                      _I(0.34), fill=T.ACCENT, radius=0.08)
        S.label(chip, str(i + 1), size=T.SZ_NODE_SM, color=T.BG, bold=True)


def outro(deck, slide, spec):
    S.rect(slide, _I(0), _I(0), _I(0.14), T.SLIDE_H, fill=T.ACCENT, radius=0)
    S.textbox(slide, _I(1.35), _I(2.6), _I(10.2), _I(0.34), spec.get("kicker", ""),
              size=T.SZ_KICKER, color=T.ACCENT, bold=True, caps=True)
    S.textbox(slide, _I(1.35), _I(3.05), _I(10.2), _I(1.6), spec["title"],
              size=T.SZ_DIVIDER_TITLE, color=T.TEXT, bold=True, spacing=1.1)
    if spec.get("note"):
        S.textbox(slide, _I(1.35), _I(4.85), _I(9.6), _I(0.8), spec["note"],
                  size=T.SZ_BODY, color=T.MUTED, spacing=1.3)


RENDERERS = {
    "cover": cover,
    "divider": divider,
    "agenda": agenda,
    "objectives": objectives,
    "bullets": bullets,
    "lead": lead,
    "cards": cards,
    "table": table,
    "code": code,
    "takeaways": takeaways,
    "outro": outro,
}
