#!/usr/bin/env python3
"""Patch a pandoc-generated typst file to a custom KDP print trim size.

Typst has no built-in "8x10" paper name, so we rewrite the `set page(...)`
that pandoc's conf() emits, replacing the named paper + default margin with
explicit width/height and mirrored (inside/outside) KDP margins.

Usage: set-trim.py FILE.typ [WIDTH] [HEIGHT] [INSIDE] [OUTSIDE] [TOP] [BOTTOM]
Defaults: 8in 10in 0.875in 0.625in 0.75in 0.75in
"""
import re
import sys

args = sys.argv[1:]
path = args[0]
w, h, inside, outside, top, bottom = (args[1:] + [
    "8in", "10in", "0.875in", "0.625in", "0.75in", "0.75in",
][len(args) - 1:])

src = open(path, encoding="utf-8").read()
replacement = (
    "set page(\n"
    f"    width: {w},\n"
    f"    height: {h},\n"
    f"    margin: (inside: {inside}, outside: {outside}, "
    f"top: {top}, bottom: {bottom}),"
)
out, n = re.subn(
    r"set page\(\s*\n\s*paper: paper,\s*\n\s*margin: margin,",
    replacement, src)
if n != 1:
    sys.exit(f"set-trim: expected 1 page block, matched {n} in {path}")
open(path, "w", encoding="utf-8").write(out)
print(f"set-trim: {path} -> {w} x {h}")
