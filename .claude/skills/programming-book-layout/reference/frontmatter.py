#!/usr/bin/env python3
"""Inject standard book front/back matter into a pandoc-generated typst file.

Adds: half-title, title page, copyright page, dedication, Contents (roman
numerals), then the main matter in arabic numerals with running headers and
each Part/Chapter starting on a new page, then back matter (About the Author,
Colophon). Pandoc's own floating title block is suppressed; build the typst
WITHOUT --toc (this script renders its own outline).

Usage: frontmatter.py FILE.typ LANG METADATA.yaml
"""
import re
import sys

path, lang, meta_path = sys.argv[1], sys.argv[2], sys.argv[3]
isbn = sys.argv[4].strip() if len(sys.argv) > 4 else ""

# --- read metadata (simple key: value lines) ---
meta = {}
for line in open(meta_path, encoding="utf-8"):
    m = re.match(r"^([a-zA-Z_]+):\s*(.+?)\s*$", line)
    if m and m.group(2) not in (">", "|"):
        val = m.group(2)
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]          # strip YAML quoting (e.g. titles with a colon)
        meta.setdefault(m.group(1), val)

title = meta.get("title", "")
subtitle = meta.get("subtitle", "")
author = meta.get("author", "")
date = meta.get("date", "2026")
rights = meta.get("rights", f"(c) {date} {author}. All rights reserved.")
publisher = meta.get("publisher", author)
repo = "https://github.com/hidran/phpenterpriseblog"

# --- localized boilerplate ---
STR = {
    "en": {
        "contents": "Contents",
        "no_repro": ("No part of this book may be reproduced or transmitted in "
            "any form or by any means, electronic or mechanical, including "
            "photocopying, recording, or by any information storage and "
            "retrieval system, without written permission from the author, "
            "except for the use of brief quotations in a review."),
        "disclaimer": ("The information in this book is provided on an \"as is\" "
            "basis, without warranty. While every precaution has been taken in "
            "its preparation, the author assumes no responsibility for errors "
            "or omissions, or for damages resulting from the use of the "
            "information contained herein."),
        "trademarks": ("All product names, logos, and brands are property of "
            "their respective owners. All company, product, and service names "
            "used in this book are for identification purposes only."),
        "code_license": ("The source code accompanying this book is released "
            f"under the MIT License and is available at: {repo}"),
        "first_edition": f"First edition: {date}",
        "publisher_line": f"Published by {publisher}",
        "isbn_line": "ISBN: [to be assigned by KDP]",
        "dedication": "For those who choose to understand the whole stack.",
        "about_title": "About the Author",
        "about_body": ("Hidran Arias is a professional software engineer and "
            "instructor who has spent years building and teaching modern PHP. "
            "He wrote this book to give developers the production-grade "
            "foundation that tutorials and framework manuals leave out."),
        "colophon_title": "Colophon",
        "colophon_body": ("This book was written in Markdown and typeset with "
            "Typst. The body is set in a serif face and code in a monospaced "
            "face. The manuscript, build pipeline, and all source code were "
            "version-controlled with Git. Every code listing is quoted from a "
            "tagged commit in the companion repository, so the code you read is "
            "the code that runs."),
    },
    "es": {
        "contents": "Índice",
        "no_repro": ("Ninguna parte de este libro puede ser reproducida ni "
            "transmitida de ninguna forma ni por ningún medio, electrónico o "
            "mecánico, incluyendo fotocopia, grabación o cualquier sistema de "
            "almacenamiento y recuperación de información, sin el permiso por "
            "escrito del autor, salvo el uso de citas breves en una reseña."),
        "disclaimer": ("La información de este libro se proporciona \"tal cual\", "
            "sin garantía. Aunque se ha tomado toda precaución en su "
            "preparación, el autor no asume ninguna responsabilidad por errores "
            "u omisiones, ni por los daños derivados del uso de la información "
            "aquí contenida."),
        "trademarks": ("Todos los nombres de productos, logotipos y marcas son "
            "propiedad de sus respectivos dueños. Todos los nombres de "
            "empresas, productos y servicios utilizados en este libro tienen "
            "únicamente fines de identificación."),
        "code_license": ("El código fuente que acompaña a este libro se publica "
            f"bajo la Licencia MIT y está disponible en: {repo}"),
        "first_edition": f"Primera edición: {date}",
        "publisher_line": f"Publicado por {publisher}",
        "isbn_line": "ISBN: [pendiente de asignación por KDP]",
        "dedication": "Para quienes eligen entender toda la pila.",
        "about_title": "Sobre el autor",
        "about_body": ("Hidran Arias es ingeniero de software profesional e "
            "instructor que ha dedicado años a construir y enseñar PHP moderno. "
            "Escribió este libro para dar a los desarrolladores la base de nivel "
            "producción que los tutoriales y los manuales de frameworks dejan "
            "fuera."),
        "colophon_title": "Colofón",
        "colophon_body": ("Este libro se escribió en Markdown y se compuso "
            "tipográficamente con Typst. El texto principal usa una fuente serif "
            "y el código una monoespaciada. El manuscrito, el proceso de "
            "compilación y todo el código fuente se gestionaron con Git. Cada "
            "listado de código está citado a partir de un commit etiquetado del "
            "repositorio complementario, de modo que el código que lees es el "
            "código que se ejecuta."),
    },
    "it": {
        "contents": "Indice",
        "no_repro": ("Nessuna parte di questo libro può essere riprodotta o "
            "trasmessa in alcuna forma o con alcun mezzo, elettronico o "
            "meccanico, inclusa la fotocopiatura, la registrazione o qualsiasi "
            "sistema di memorizzazione e recupero delle informazioni, senza il "
            "permesso scritto dell'autore, salvo l'uso di brevi citazioni in "
            "una recensione."),
        "disclaimer": ("Le informazioni contenute in questo libro sono fornite "
            "\"così come sono\", senza garanzia. Sebbene sia stata presa ogni "
            "precauzione nella loro preparazione, l'autore non si assume alcuna "
            "responsabilità per errori od omissioni, né per i danni derivanti "
            "dall'uso delle informazioni qui contenute."),
        "trademarks": ("Tutti i nomi di prodotti, loghi e marchi sono proprietà "
            "dei rispettivi titolari. Tutti i nomi di aziende, prodotti e "
            "servizi utilizzati in questo libro hanno il solo scopo di "
            "identificazione."),
        "code_license": ("Il codice sorgente che accompagna questo libro è "
            f"rilasciato sotto Licenza MIT ed è disponibile all'indirizzo: {repo}"),
        "first_edition": f"Prima edizione: {date}",
        "publisher_line": f"Pubblicato da {publisher}",
        "isbn_line": "ISBN: [da assegnare tramite KDP]",
        "dedication": "Per chi sceglie di capire l'intero stack.",
        "about_title": "Sull'autore",
        "about_body": ("Hidran Arias è un ingegnere del software professionista "
            "e formatore che ha dedicato anni a costruire e insegnare PHP "
            "moderno. Ha scritto questo libro per dare agli sviluppatori quelle "
            "fondamenta di livello produzione che i tutorial e i manuali dei "
            "framework tralasciano."),
        "colophon_title": "Colophon",
        "colophon_body": ("Questo libro è stato scritto in Markdown e composto "
            "tipograficamente con Typst. Il testo principale è in un carattere "
            "serif e il codice in un carattere monospaziato. Il manoscritto, la "
            "pipeline di compilazione e tutto il codice sorgente sono stati "
            "gestiti con Git. Ogni listato di codice è citato da un commit "
            "taggato del repository di accompagnamento, così il codice che leggi "
            "è il codice che viene eseguito."),
    },
}[lang]


# a real ISBN (passed in) overrides the placeholder line
if isbn:
    STR["isbn_line"] = f"ISBN: {isbn}"


def esc_content(s):
    """Escape typst markup special chars for use inside [ ... ]."""
    return re.sub(r'([#\[\]@\\*_`$])', r'\\\1', s)


def esc_str(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


T = {k: esc_content(v) for k, v in {
    "title": title, "subtitle": subtitle, "author": author,
    "publisher": publisher, "rights": rights, **STR,
}.items()}

# publisher line on the title page only when it adds information (≠ author)
publisher_block = (f'#align(center, text(size: 11pt)[{T["publisher"]}])'
                   if publisher and publisher != author else "")

src = open(path, encoding="utf-8").read()

# 0) shade code blocks: light-gray, padded, page-breakable boxes (prints fine
# in KDP black & white). Only the fenced-code wrapper is touched; inline code
# is unaffected.
src, n = re.subn(
    r"block\(fill: bgcolor, blocks\)",
    "block(fill: luma(240), inset: (x: 7pt, y: 6pt), radius: 2pt, "
    "width: 100%, breakable: true, blocks)",
    src)
if n != 1:
    sys.exit(f"frontmatter: expected 1 code-block wrapper, found {n}")

# 1) suppress pandoc's floating title block (keep document metadata title)
src, n = re.subn(r'if title != none \{(\s*\n\s*place\(top)', r'if false {\1',
                 src, count=1)
if n != 1:
    sys.exit(f"frontmatter: could not disable conf title block ({n})")

# 2) build front matter (inserted before the 1st unnumbered level-1 heading)
front = f'''
#set document(title: "{esc_str(title)}", author: "{esc_str(author)}")
#show heading.where(level: 1): it => {{ pagebreak(weak: true); it }}

#set page(numbering: none)
#counter(page).update(1)

// half-title
#v(3fr)
#align(center, text(size: 20pt, weight: "bold")[{T["title"]}])
#v(5fr)

#pagebreak(to: "odd")
// title page
#v(2fr)
#align(center)[
  #text(size: 26pt, weight: "bold")[{T["title"]}]

  #v(1.2em)
  #text(size: 13pt, style: "italic")[{T["subtitle"]}]

  #v(3em)
  #text(size: 14pt)[{T["author"]}]
]
#v(3fr)
{publisher_block}
#pagebreak()
// copyright page
#v(1fr)
#block[
  #set par(justify: false, leading: 0.62em)
  #set text(size: 9.5pt)
  {T["rights"]}

  {T["no_repro"]}

  {T["disclaimer"]}

  {T["trademarks"]}

  {T["code_license"]}

  {T["first_edition"]} \\
  {T["publisher_line"]} \\
  {T["isbn_line"]}
]

#pagebreak(to: "odd")
// dedication
#v(1fr)
#align(center, text(size: 12pt, style: "italic")[{T["dedication"]}])
#v(2fr)

#pagebreak(to: "odd")
// contents (roman numerals from here)
#set page(numbering: "i")
#counter(page).update(1)
#text(size: 18pt, weight: "bold")[{T["contents"]}]
#v(0.8em)
#outline(title: none, depth: 2, indent: auto)

'''

# 3) arabic switch + running headers (before the 2nd unnumbered level-1 heading)
arabic = f'''
#pagebreak(to: "odd")
#set page(numbering: "1")
#counter(page).update(1)
#set page(header: context {{
  let cur = here().page()
  let prior = query(heading.where(level: 1)).filter(h => h.location().page() <= cur)
  if prior.len() == 0 {{ none }} else {{
    let it = prior.last()
    // suppress the running head on any page where a Part/Chapter opens
    if it.location().page() == cur {{ none }} else {{
      set text(size: 9pt, style: "italic")
      if calc.even(cur) {{ [{T["title"]} #h(1fr)] }}
      else {{ [#h(1fr) #it.body] }}
    }}
  }}
}})

'''

# 4) back matter (appended at end)
back = f'''

#heading(level: 1, numbering: none)[{T["about_title"]}]

{T["about_body"]}

#heading(level: 1, numbering: none)[{T["colophon_title"]}]

{T["colophon_body"]}
'''

anchor = "#heading(level: 1, numbering: none)["
positions = [m.start() for m in re.finditer(re.escape(anchor), src)]
if len(positions) < 2:
    sys.exit(f"frontmatter: expected >=2 unnumbered level-1 headings, "
             f"found {len(positions)}")

# insert back-to-front so earlier offsets stay valid
p_part = positions[1]   # Part I
p_pref = positions[0]   # Preface
src = src[:p_part] + arabic + src[p_part:]
src = src[:p_pref] + front + src[p_pref:]
src = src + back

open(path, "w", encoding="utf-8").write(src)
print(f"frontmatter: {path} ({lang}) front+back matter injected")
