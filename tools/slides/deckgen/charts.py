"""Native PowerPoint charts, themed dark.

Real charts (not images) so the author can retype a number without regenerating
the deck, and so they stay sharp at 4K recording resolution.
"""
import copy

from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

from . import shapes as S
from . import theme as T
from .diagrams import BH, BW, BX, BY, _I, _note

_KIND = {
    "column": XL_CHART_TYPE.COLUMN_CLUSTERED,
    "stacked_column": XL_CHART_TYPE.COLUMN_STACKED,
    "bar": XL_CHART_TYPE.BAR_CLUSTERED,
    "line": XL_CHART_TYPE.LINE_MARKERS,
}


def _no_fill(element):
    """Drop the white background so the dark slide shows through."""
    sp_pr = element.find(qn("c:spPr"))
    if sp_pr is None:
        sp_pr = element.makeelement(qn("c:spPr"), {})
        element.append(sp_pr)
    for child in list(sp_pr):
        sp_pr.remove(child)
    sp_pr.append(sp_pr.makeelement(qn("a:noFill"), {}))
    ln = sp_pr.makeelement(qn("a:ln"), {})
    ln.append(ln.makeelement(qn("a:noFill"), {}))
    sp_pr.append(ln)


def _style_axis(axis, show_line=True, gridlines=False):
    axis.has_major_gridlines = gridlines
    if gridlines:
        gl = axis.major_gridlines.format.line
        gl.color.rgb = T.LINE
        gl.width = Pt(0.75)
    fmt = axis.format.line
    if show_line:
        fmt.color.rgb = T.LINE
        fmt.width = Pt(1.0)
    else:
        fmt.fill.background()
    labels = axis.tick_labels
    labels.font.size = Pt(13)      # read at video distance, not print distance
    labels.font.color.rgb = T.MUTED
    labels.font.name = T.FONT


def chart(slide, spec):
    """Render a themed native chart into the slide body."""
    kind = _KIND[spec.get("kind", "column")]
    data = CategoryChartData()
    data.categories = spec["categories"]
    for series in spec["series"]:
        data.add_series(series["name"], series["values"])

    w = spec.get("width", BW)
    h = spec.get("height", BH - 1.0)
    x = BX + (BW - w) / 2
    y = spec.get("y", BY + 0.15)

    frame = slide.shapes.add_chart(kind, _I(x), _I(y), _I(w), _I(h), data)
    ch = frame.chart

    _no_fill(ch._chartSpace)
    plot_area = ch._chartSpace.find(qn("c:chart")).find(qn("c:plotArea"))
    _no_fill(plot_area)

    ch.font.size = T.SZ_CAPTION
    ch.font.name = T.FONT
    ch.font.color.rgb = T.MUTED
    ch.has_title = False

    multi = len(spec["series"]) > 1
    ch.has_legend = spec.get("legend", multi)
    if ch.has_legend:
        ch.legend.position = XL_LEGEND_POSITION.TOP
        ch.legend.include_in_layout = False
        ch.legend.font.size = Pt(13)
        ch.legend.font.color.rgb = T.MUTED
        ch.legend.font.name = T.FONT

    horizontal = spec.get("kind") == "bar"
    _style_axis(ch.category_axis, show_line=True, gridlines=False)
    _style_axis(ch.value_axis, show_line=False,
                gridlines=spec.get("gridlines", not horizontal))

    if spec.get("hide_value_axis", horizontal):
        ch.value_axis.visible = False

    plot = ch.plots[0]
    plot.gap_width = spec.get("gap_width", 60 if horizontal else 45)
    if spec.get("kind") == "stacked_column":
        plot.overlap = 100

    palette = [T.SERIES[i % len(T.SERIES)] for i in range(len(spec["series"]))]
    for i, series in enumerate(ch.series):
        colour = palette[i]
        declared = spec["series"][i].get("color")
        if declared:
            colour = getattr(T, declared.upper(), colour)
        if spec.get("kind") == "line":
            series.format.line.color.rgb = colour
            series.format.line.width = Pt(2.5)
            series.smooth = False
        else:
            series.format.fill.solid()
            series.format.fill.fore_color.rgb = colour
            series.format.line.fill.background()

    if spec.get("labels"):
        plot.has_data_labels = True
        dl = plot.data_labels
        dl.font.size = Pt(11.5)
        dl.font.color.rgb = T.TEXT
        dl.font.name = T.FONT
        dl.number_format = spec.get("number_format", "General")
        dl.number_format_is_linked = False
        if spec.get("kind") in ("column", "bar"):
            dl.position = XL_LABEL_POSITION.OUTSIDE_END
        elif spec.get("kind") == "stacked_column":
            dl.position = XL_LABEL_POSITION.CENTER

    if spec.get("caption"):
        _note(slide, spec["caption"], y=y + h + 0.12)
    return ch


def big_number(slide, spec):
    """Two headline figures set against each other — the cost punchline."""
    items = spec["items"]
    n = len(items)
    gap = 0.5
    cw = (BW - gap * (n - 1)) / n
    h = spec.get("height", 2.55)
    y = BY + (BH - h) / 2 - 0.4

    for i, item in enumerate(items):
        x = BX + i * (cw + gap)
        fill, line, _ = T.TONES.get(item.get("tone", "neutral"), T.TONES["neutral"])
        S.rect(slide, _I(x), _I(y), _I(cw), _I(h), fill=fill, line=line, radius=0.14)
        S.textbox(slide, _I(x), _I(y + 0.34), _I(cw), _I(0.32), item.get("kicker", ""),
                  size=T.SZ_CAPTION, color=T.MUTED, align=PP_ALIGN.CENTER,
                  caps=True, bold=True)
        colour = getattr(T, item.get("color", "TEXT").upper(), T.TEXT)
        S.textbox(slide, _I(x), _I(y + 0.78), _I(cw), _I(1.1), item["value"],
                  size=T.SZ_BIGNUM, color=colour, bold=True,
                  align=PP_ALIGN.CENTER, spacing=0.95)
        S.textbox(slide, _I(x), _I(y + h - 0.72), _I(cw), _I(0.55),
                  item.get("note", ""), size=T.SZ_CARD_BODY, color=T.MUTED,
                  align=PP_ALIGN.CENTER, spacing=1.25)

        if i < n - 1:
            S.textbox(slide, _I(x + cw), _I(y + h / 2 - 0.22), _I(gap), _I(0.4),
                      spec.get("joiner", "→"), size=T.SZ_LEAD, color=T.DIM,
                      align=PP_ALIGN.CENTER)

    if spec.get("caption"):
        _note(slide, spec["caption"], y=y + h + 0.3, color=T.WARN,
              size=T.SZ_CARD_TITLE)
