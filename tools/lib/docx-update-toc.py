#!/usr/bin/env python3
"""Fill the table-of-contents field of a pandoc DOCX with real page numbers and
export the matching PDF.

pandoc --toc writes a Word TOC field with an *empty* result: Word fills it only
when a user updates fields, and KDP / LibreOffice conversions never do. This
driver runs a small script *inside* soffice (its embedded Python script
provider, in a throwaway user profile) that loads the document hidden, updates
the index until the page numbers stop shifting, exports the PDF, and hands back
the computed "title<TAB>page" lines. The driver then injects those entries into
pandoc's own DOCX — hyperlinked to new _TocN bookmarks on the headings, styled
TOC1/TOC2 — so the upload file keeps pandoc's exact page setup and styles
instead of a LibreOffice re-export.

    docx-update-toc.py <in.docx> [--docx <out.docx>] [--pdf <out.pdf>]

--docx may equal the input path. Set SOFFICE to override the binary.
"""
import argparse
import html
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from xml.sax.saxutils import escape

SOFFICE = os.environ.get("SOFFICE", "/opt/homebrew/bin/soffice")

# Runs inside soffice; XSCRIPTCONTEXT is injected by the script provider.
INNER = r'''
import os, traceback, uno
from com.sun.star.beans import PropertyValue

def _props(**kw):
    out = []
    for k, v in kw.items():
        p = PropertyValue(); p.Name, p.Value = k, v; out.append(p)
    return tuple(out)

def run(*_):
    env = os.environ
    log = open(env["EBOOKS_TOC_LOG"], "w")
    desktop = XSCRIPTCONTEXT.getDesktop()
    try:
        doc = desktop.loadComponentFromURL(
            uno.systemPathToFileUrl(env["EBOOKS_TOC_IN"]), "_blank", 0, _props(Hidden=True))
        if doc is None:
            raise RuntimeError("loadComponentFromURL returned None")
        idx = doc.getDocumentIndexes()
        n = idx.getCount()
        prev = None
        for _ in range(6):  # a longer TOC shifts later page numbers: repeat until stable
            for i in range(n):
                idx.getByIndex(i).update()
            doc.refresh()
            cur = tuple(idx.getByIndex(i).getAnchor().getString() for i in range(n))
            if cur == prev:
                break
            prev = cur
        with open(env["EBOOKS_TOC_TXT"], "w", encoding="utf-8") as fh:
            fh.write("\n".join(prev or ()))
        if env.get("EBOOKS_TOC_PDF"):
            doc.storeToURL(uno.systemPathToFileUrl(env["EBOOKS_TOC_PDF"]),
                           _props(FilterName="writer_pdf_Export"))
        log.write(f"OK {n}\n")
        doc.close(True)
    except Exception:
        log.write("ERR " + traceback.format_exc())
    finally:
        log.close()
        try:
            desktop.terminate()
        except Exception:
            pass
'''

PARA = re.compile(r"<w:p\b[^>]*>(?:(?!</w:p>).)*?</w:p>", re.S)
FIELD_PARA = re.compile(
    r'<w:p\b[^>]*>\s*(?:<w:pPr>.*?</w:pPr>\s*)?<w:r>\s*<w:fldChar w:fldCharType="begin"[^>]*/>\s*'
    r'<w:instrText[^>]*>\s*(TOC [^<]*)</w:instrText>\s*<w:fldChar w:fldCharType="separate"\s*/>\s*'
    r'<w:fldChar w:fldCharType="end"\s*/>\s*</w:r>\s*</w:p>', re.S)


def para_text(p):
    return re.sub(r"\s+", " ", html.unescape("".join(re.findall(r"<w:t\b[^>]*>([^<]*)</w:t>", p)))).strip()


def toc_styles(sty, width):
    """Add TOC1/TOC2 paragraph styles (dot-leader right tab at the text width)."""
    based = '<w:basedOn w:val="Normal"/>' if 'w:styleId="Normal"' in sty else ""
    out = ""
    for lv, ind, before in ((1, 0, 120), (2, 260, 0)):
        if f'w:styleId="TOC{lv}"' in sty:
            continue
        out += (f'<w:style w:type="paragraph" w:styleId="TOC{lv}"><w:name w:val="toc {lv}"/>{based}'
                f'<w:next w:val="Normal"/><w:uiPriority w:val="39"/><w:pPr>'
                f'<w:tabs><w:tab w:val="right" w:leader="dot" w:pos="{width}"/></w:tabs>'
                f'<w:spacing w:before="{before}" w:after="0"/><w:ind w:left="{ind}"/>'
                f'<w:jc w:val="left"/></w:pPr></w:style>')
    return sty.replace("</w:styles>", out + "</w:styles>", 1) if out else sty


def inject(src, dst, entries):
    """Write `src` DOCX to `dst` with its TOC field filled from entries [(text, page)]."""
    with zipfile.ZipFile(src) as z:
        infos = z.infolist()
        files = {i.filename: z.read(i.filename) for i in infos}
    doc = files["word/document.xml"].decode("utf-8")
    sty = files["word/styles.xml"].decode("utf-8")

    heads = [(m, int(re.search(r'w:pStyle w:val="Heading([12])"', m.group(0)).group(1)))
             for m in PARA.finditer(doc) if re.search(r'w:pStyle w:val="Heading[12]"', m.group(0))]
    if len(heads) != len(entries):
        sys.exit(f"docx-update-toc: LibreOffice returned {len(entries)} TOC entries but the DOCX "
                 f"has {len(heads)} Heading 1/2 paragraphs — refusing to guess")
    off = [i for i, ((m, _), (t, _)) in enumerate(zip(heads, entries)) if para_text(m.group(0)) != t]
    if off:
        print(f"  ! {len(off)} TOC titles differ from the headings (e.g. entry {off[0] + 1}: "
              f"{entries[off[0]][0]!r} vs {para_text(heads[off[0]][0].group(0))!r}); using heading order",
              file=sys.stderr)

    fm = FIELD_PARA.search(doc)
    if not fm:
        sys.exit("docx-update-toc: no empty TOC field paragraph found in the DOCX")
    instr = fm.group(1)

    sect = re.findall(r"<w:sectPr\b.*?</w:sectPr>", doc, re.S)[-1]
    g = lambda tag, attr: int(re.search(rf'<w:{tag}\b[^>]*\bw:{attr}="(\d+)"', sect).group(1))
    width = g("pgSz", "w") - g("pgMar", "left") - g("pgMar", "right") - g("pgMar", "gutter")

    ids = [int(x) for x in re.findall(r'<w:bookmarkStart\b[^>]*\bw:id="(\d+)"', doc)]
    next_id = max(ids, default=0) + 1

    # Rebuild the document: bookmark each heading, replace the field paragraph.
    edits = []  # (start, end, replacement)
    for n, (m, _) in enumerate(heads, 1):
        p = m.group(0)
        bid = next_id + n
        start = f'<w:bookmarkStart w:id="{bid}" w:name="_Toc{n}"/>'
        end = f'<w:bookmarkEnd w:id="{bid}"/>'
        if "</w:pPr>" in p:
            p2 = p.replace("</w:pPr>", "</w:pPr>" + start, 1)
        else:
            p2 = re.sub(r"(<w:p\b[^>]*>)", r"\1" + start, p, count=1)
        p2 = p2[: p2.rfind("</w:p>")] + end + "</w:p>"
        edits.append((m.start(), m.end(), p2))
    paras = []
    for n, ((_, lv), (text, page)) in enumerate(zip(heads, entries), 1):
        runs = ""
        if n == 1:
            runs += ('<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
                     f'<w:r><w:instrText xml:space="preserve">{instr}</w:instrText></w:r>'
                     '<w:r><w:fldChar w:fldCharType="separate"/></w:r>')
        runs += (f'<w:hyperlink w:anchor="_Toc{n}" w:history="1">'
                 f'<w:r><w:t xml:space="preserve">{escape(text)}</w:t></w:r>'
                 f'<w:r><w:tab/></w:r><w:r><w:t>{escape(page)}</w:t></w:r></w:hyperlink>')
        if n == len(heads):
            runs += '<w:r><w:fldChar w:fldCharType="end"/></w:r>'
        paras.append(f'<w:p><w:pPr><w:pStyle w:val="TOC{lv}"/></w:pPr>{runs}</w:p>')
    edits.append((fm.start(), fm.end(), "".join(paras)))
    for s, e, rep in sorted(edits, reverse=True):
        doc = doc[:s] + rep + doc[e:]

    files["word/document.xml"] = doc.encode("utf-8")
    files["word/styles.xml"] = toc_styles(sty, width).encode("utf-8")
    tmp = str(dst) + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for i in infos:
            z.writestr(i, files[i.filename])
    os.replace(tmp, dst)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("docx")
    ap.add_argument("--docx", dest="out_docx", help="write the DOCX with a filled TOC here (may equal input)")
    ap.add_argument("--pdf", dest="out_pdf", help="export a PDF here")
    args = ap.parse_args()
    if not (args.out_docx or args.out_pdf):
        sys.exit("docx-update-toc: nothing to do (give --docx and/or --pdf)")
    src = pathlib.Path(args.docx).resolve()
    if not src.is_file():
        sys.exit(f"docx-update-toc: {src} not found")

    work = pathlib.Path(tempfile.mkdtemp(prefix="docx-update-toc-"))
    try:
        profile = work / "profile"
        scripts = profile / "user" / "Scripts" / "python"
        scripts.mkdir(parents=True)
        (scripts / "update_toc.py").write_text(INNER)
        tmp_pdf, log, txt = work / "out.pdf", work / "result.log", work / "toc.txt"
        env = {**os.environ, "EBOOKS_TOC_IN": str(src), "EBOOKS_TOC_LOG": str(log),
               "EBOOKS_TOC_TXT": str(txt), "EBOOKS_TOC_PDF": str(tmp_pdf) if args.out_pdf else ""}
        cmd = [SOFFICE, "--headless", "--invisible", "--nologo", "--norestore", "--nodefault",
               f"-env:UserInstallation={profile.as_uri()}",
               "vnd.sun.star.script:update_toc.py$run?language=Python&location=user"]
        res = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=900)
        result = log.read_text() if log.exists() else ""
        if not result.startswith("OK"):
            sys.exit(f"docx-update-toc: LibreOffice script failed\n{result}\n"
                     f"soffice rc={res.returncode}\n{res.stdout}\n{res.stderr}")
        n_index = int(result.split()[1])
        entries = [tuple(line.rsplit("\t", 1)) for line in txt.read_text(encoding="utf-8").split("\n")
                   if "\t" in line]
        entries = [(re.sub(r"\s+", " ", t).strip(), p.strip()) for t, p in entries]

        if args.out_pdf:
            shutil.move(tmp_pdf, pathlib.Path(args.out_pdf).resolve())
        if args.out_docx:
            dst = pathlib.Path(args.out_docx).resolve()
            if n_index == 0:
                if dst != src:
                    shutil.copy(src, dst)
            else:
                inject(src, dst, entries)
        what = " + ".join(w for w, on in (("docx", args.out_docx), ("pdf", args.out_pdf)) if on)
        if n_index == 0:
            print(f"  ! {src.name}: no TOC field found; wrote {what} unchanged", file=sys.stderr)
        else:
            print(f"  ✓ {src.name}: TOC filled ({len(entries)} entries) → {what}")
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
