#!/usr/bin/env python3
"""Reshape a pandoc-built EPUB3 so Kindle / KDP detects its table of contents.

pandoc (--toc) writes a single nav.xhtml that is both the logical nav document
and the visible TOC page, and its landmarks entry points at a bare fragment:

    <a href="#toc" epub:type="toc">Table of Contents</a>

Amazon's converter expects the toc landmark / guide reference to name a content
document (see KDP "Navigation Guidelines" and "Create a Table of Contents with a
Navigation Document"); with pandoc's layout KDP reports the eBook as having no
table of contents. This script rewrites the EPUB in place:

  * adds toc.xhtml — an HTML TOC page copied from pandoc's <nav epub:type="toc">
  * puts toc.xhtml in the spine right after the cover / title page
  * drops nav.xhtml from the reading order (it stays the logical nav document)
  * points <guide><reference type="toc"> and the landmarks toc link at toc.xhtml
  * titles both TOCs "Contents" / "Sommario" / "Índice" … by language

Usage: fix-epub-toc.py <book.epub> [--lang xx] [--title "Contents"]
Idempotent: running it twice yields the same file.
"""
import argparse
import posixpath
import re
import sys
import zipfile
from xml.sax.saxutils import escape

from toc_title import toc_title  # noqa: E402
TOC_ID = "toc_page"
TOC_NAME = "toc.xhtml"
FRONT_PAGES = {"cover.xhtml", "title_page.xhtml"}  # spine items the TOC goes after


def die(msg):
    sys.exit(f"fix-epub-toc: {msg}")


def rel(target, from_dir):
    return posixpath.relpath(target, from_dir) if from_dir else target


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("epub")
    ap.add_argument("--lang", help="language code for the TOC title (default: from dc:language)")
    ap.add_argument("--title", help="explicit TOC title (overrides --lang)")
    args = ap.parse_args()

    with zipfile.ZipFile(args.epub) as z:
        entries = [(i, z.read(i.filename)) for i in z.infolist()]
    files = {i.filename: data for i, data in entries}

    # --- locate OPF / nav -------------------------------------------------
    m = re.search(r'full-path="([^"]+)"', files["META-INF/container.xml"].decode())
    opf_path = m.group(1) if m else die("no rootfile in container.xml")
    opf_dir = posixpath.dirname(opf_path)
    opf = files[opf_path].decode("utf-8")

    m = re.search(r'<item\b[^>]*\bproperties="[^"]*\bnav\b[^"]*"[^>]*/>', opf)
    nav_tag = m.group(0) if m else die("no nav item in manifest")
    nav_id = re.search(r'\bid="([^"]+)"', nav_tag).group(1)
    nav_href = re.search(r'\bhref="([^"]+)"', nav_tag).group(1)
    nav_path = posixpath.normpath(posixpath.join(opf_dir, nav_href))
    nav_dir = posixpath.dirname(nav_path)
    nav = files[nav_path].decode("utf-8")

    toc_path = posixpath.join(nav_dir, TOC_NAME) if nav_dir else TOC_NAME
    toc_href_opf = rel(toc_path, opf_dir)      # as seen from content.opf
    toc_href_nav = rel(toc_path, nav_dir)      # as seen from nav.xhtml

    # --- title ------------------------------------------------------------
    lang = args.lang
    if not lang:
        m = re.search(r"<dc:language>([^<]+)</dc:language>", opf)
        lang = m.group(1) if m else "en"
    title = args.title or toc_title(lang)
    xtitle = escape(title)

    # --- build toc.xhtml from pandoc's <nav epub:type="toc"> -----------------
    m = re.search(r'<nav\b[^>]*epub:type="toc"[^>]*>(.*?)</nav>', nav, re.S)
    inner = m.group(1) if m else die("no <nav epub:type=\"toc\"> in nav document")
    m = re.search(r"<ol\b.*</ol>", inner, re.S)
    toc_list = m.group(0) if m else die("nav toc has no <ol>")
    html_open = re.search(r"<html\b[^>]*>", nav).group(0)
    links = "".join(re.findall(r'\s*<link\b[^>]*rel="stylesheet"[^>]*/>', nav))
    toc_doc = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE html>\n'
        f"{html_open}\n<head>\n  <meta charset=\"utf-8\" />\n  <title>{xtitle}</title>"
        f"{links}\n</head>\n<body epub:type=\"frontmatter\">\n"
        f'<section class="toc-page">\n<h1 class="toc-title">{xtitle}</h1>\n{toc_list}\n'
        "</section>\n</body>\n</html>\n"
    )

    # --- nav.xhtml: retitle, point landmark at the page ------------------
    nav, n = re.subn(r'(<h1 id="toc-title">)[^<]*(</h1>)', rf"\g<1>{xtitle}\g<2>", nav, count=1)
    nav, n = re.subn(r'<a href="[^"]*" epub:type="toc">[^<]*</a>',
                     f'<a href="{toc_href_nav}" epub:type="toc">{xtitle}</a>', nav, count=1)
    if not n:
        die("no toc landmark in nav document")

    # --- content.opf ------------------------------------------------------
    item = f'<item id="{TOC_ID}" href="{toc_href_opf}" media-type="application/xhtml+xml" />'
    opf = re.sub(rf'\n[ \t]*<item id="{TOC_ID}"[^>]*/>', "", opf)          # idempotent
    indent = re.search(r"\n([ \t]*)" + re.escape(nav_tag), opf).group(1)
    opf = opf.replace(nav_tag, f"{nav_tag}\n{indent}{item}", 1)

    m = re.search(r"<spine\b[^>]*>(.*?)</spine>", opf, re.S)
    spine = m.group(1) if m else die("no <spine>")
    refs = re.findall(r"[ \t]*<itemref\b[^>]*/>\n?", spine)
    ind = re.match(r"[ \t]*", refs[0]).group(0) if refs else "    "
    hrefs = dict(re.findall(r'<item\b[^>]*\bid="([^"]+)"[^>]*\bhref="([^"]+)"', opf))
    keep = [r for r in refs
            if re.search(r'idref="([^"]+)"', r).group(1) not in (nav_id, TOC_ID)]
    pos = 0
    while pos < len(keep) and posixpath.basename(
            hrefs.get(re.search(r'idref="([^"]+)"', keep[pos]).group(1), "")) in FRONT_PAGES:
        pos += 1
    keep.insert(pos, f'{ind}<itemref idref="{TOC_ID}" />\n')
    opf = opf[:m.start(1)] + "\n" + "".join(keep) + opf[m.end(1):].lstrip(" \t")

    ref = f'<reference type="toc" title="{xtitle}" href="{toc_href_opf}" />'
    if re.search(r'<reference\b[^>]*type="toc"[^>]*/>', opf):
        opf = re.sub(r'<reference\b[^>]*type="toc"[^>]*/>', ref, opf, count=1)
    elif "<guide>" in opf:
        opf = opf.replace("<guide>", f"<guide>\n    {ref}", 1)
    else:
        opf = opf.replace("</package>", f"  <guide>\n    {ref}\n  </guide>\n</package>", 1)

    # --- write back: mimetype first & stored, everything else deflated -------
    files[opf_path] = opf.encode("utf-8")
    files[nav_path] = nav.encode("utf-8")
    order = [i.filename for i, _ in entries]
    if toc_path not in order:
        order.insert(order.index(nav_path) + 1, toc_path)
    files[toc_path] = toc_doc.encode("utf-8")
    if order[0] != "mimetype":
        die("mimetype is not the first zip entry")
    with zipfile.ZipFile(args.epub, "w") as z:
        z.writestr("mimetype", files["mimetype"], compress_type=zipfile.ZIP_STORED)
        for name in order[1:]:
            z.writestr(name, files[name], compress_type=zipfile.ZIP_DEFLATED)
    print(f"  ✓ {posixpath.basename(args.epub)}: TOC page {toc_href_opf} “{title}” "
          f"(guide + landmarks → {toc_href_opf}, nav out of spine)")


if __name__ == "__main__":
    main()
