#!/usr/bin/env python3
"""Flag the mechanical "AI prose" tells in Markdown manuscripts.

Usage: tools/slop-lint.py [--lang it|en|es] [--summary] FILE...

Code blocks and inline code are ignored. Exit status 1 when a hard rule is broken
(em/en dash, arrow or emoji in prose); soft findings (phrases, bold density) are
reported but do not fail the run.
"""
import argparse, re, sys

HARD = [
    ("em-dash", re.compile("—")),
    ("en-dash", re.compile("–")),
    ("arrow", re.compile("[→⇒←⟶]")),
    ("emoji", re.compile("[\U0001F300-\U0001FAFF☀-➿⭐✅❌]")),
]

PHRASES = {
    "it": [
        r"\bnon è (?:solo |soltanto )?[^.,;:]{1,40}[,:;] è\b", r"\bnon si tratta di\b",
        r"\bvediamo insieme\b", r"^ecco\b", r"\becco (?:cosa|come|i passi|perché)\b",
        r"\bin questo capitolo vedremo\b", r"\bcome vedremo\b", r"\bè importante notare\b",
        r"\bvale la pena (?:sottolineare|notare)\b", r"\bil punto chiave\b",
        r"\bma c'è di più\b", r"\bin sintesi\b", r"\bin altre parole\b",
        r"\bfondamental[ei]\b", r"\bcrucial[ei]\b", r"\bpotent[ei]\b",
        r"\brivoluzionari[oa]\b", r"\bincredibil[ei]\b", r"\bmagi[ac]\w*\b",
        r"\bgame.?changer\b", r"\balla radice\b", r"\ba colpo d.occhio\b",
        r"\bsenza soluzione di continuità\b", r"\bun vero e proprio\b", r"\bsinergi\w+\b",
        r"\bti sei mai chiesto\b", r"\bhands-on\b", r"\bdieci volte\b",
    ],
    "en": [
        r"\bit'?s not (?:just |only )?[^.,;]{1,40}[,;:] it'?s\b", r"\bnot about\b[^.]{1,40}\bit'?s about\b",
        r"\bdelve\b", r"\bleverag\w+\b", r"\brobust\b", r"\bseamless\w*\b", r"\bunlock\w*\b",
        r"\bempower\w*\b", r"\belevat\w+\b", r"\bcrucial\b", r"\bpowerful\b",
        r"\bgame.?changer\b", r"\blandscape\b", r"\bjourney\b", r"\bsupercharg\w+\b",
        r"\blet'?s dive\b", r"\bit'?s worth noting\b", r"\bhere'?s the thing\b",
        r"\bin a nutshell\b", r"\blet'?s break (?:it|this) down\b", r"\bmagic\w*\b",
        r"\bhave you ever wondered\b",
    ],
    "es": [
        r"\bno es (?:solo )?[^.,;]{1,40}[,;:] es\b", r"\bno se trata de\b", r"\bveamos\b",
        r"\bcabe destacar\b", r"\bes importante señalar\b", r"\ben resumen\b",
        r"\bcrucial(?:es)?\b", r"\bpotentes?\b", r"\brevolucionari[oa]s?\b",
        r"\bincreíbles?\b", r"\bmágic[oa]s?\b", r"\bsinergias?\b", r"\bpotenciar\b",
        r"\bsin fisuras\b", r"\bte has preguntado\b",
    ],
}

FENCE = re.compile(r"^\s*(```|~~~)")
INLINE = re.compile(r"`[^`]*`")
HTML_COMMENT = re.compile(r"<!--.*?-->")


def prose_lines(text):
    in_code = False
    for n, line in enumerate(text.split("\n"), 1):
        if FENCE.match(line):
            in_code = not in_code
            continue
        if in_code or line.startswith("    "):
            continue
        yield n, HTML_COMMENT.sub("", INLINE.sub("", line))


def lint(path, lang):
    text = open(path, encoding="utf-8").read()
    hard, soft = [], []
    bold = 0
    words = 0
    phrases = [re.compile(p, re.I | re.M) for p in PHRASES[lang]]
    for n, line in prose_lines(text):
        words += len(line.split())
        bold += len(re.findall(r"\*\*[^*]+\*\*", line))
        for name, rx in HARD:
            if rx.search(line):
                hard.append((n, name, line.strip()[:100]))
        for rx in phrases:
            m = rx.search(line)
            if m:
                soft.append((n, "phrase", m.group(0)))
        if re.match(r"^\s*[-*] \*\*", line):
            soft.append((n, "bold-bullet", line.strip()[:60]))
    per_k = bold * 1000 / max(words, 1)
    if per_k > 3:
        soft.append((0, "bold-density", f"{bold} bold spans, {per_k:.1f} per 1000 words (max 3)"))
    return hard, soft, words


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="it", choices=PHRASES)
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("files", nargs="+")
    a = ap.parse_args()
    failed = False
    for f in a.files:
        hard, soft, words = lint(f, a.lang)
        failed |= bool(hard)
        if a.summary:
            print(f"{f}: {words} words, {len(hard)} hard, {len(soft)} soft")
            continue
        for n, kind, s in hard:
            print(f"{f}:{n}: HARD {kind}: {s}")
        for n, kind, s in soft:
            print(f"{f}:{n}: soft {kind}: {s}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
