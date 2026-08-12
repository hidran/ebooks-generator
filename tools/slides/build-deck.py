#!/usr/bin/env python3
"""Build a .pptx lesson deck from a YAML spec.

Usage:
  build-deck.py <spec.yaml> [-o <out.pptx>]
  build-deck.py --book <slug> [--lang en] [--module 01]
"""
import argparse
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deckgen  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def build_one(spec_path, out_path):
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    deck = deckgen.build(spec)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    deck.save(out_path)
    return deck


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec", nargs="?", type=Path)
    ap.add_argument("-o", "--out", type=Path)
    ap.add_argument("--book")
    ap.add_argument("--lang", default="en")
    ap.add_argument("--module", help="module number, e.g. 01; omit to build all")
    args = ap.parse_args()

    if args.spec:
        jobs = [(args.spec, args.out or args.spec.with_suffix(".pptx"))]
    elif args.book:
        book = ROOT / "books" / args.book
        src = book / "slides" / args.lang
        pattern = f"module-{args.module}.yaml" if args.module else "module-*.yaml"
        specs = sorted(src.glob(pattern))
        if not specs:
            ap.error(f"no specs matching {pattern} in {src}")
        out_dir = book / "build" / "slides" / args.lang
        jobs = [(s, out_dir / f"{s.stem}.pptx") for s in specs]
    else:
        ap.error("give a spec path, or --book <slug>")

    for spec_path, out_path in jobs:
        deck = build_one(spec_path, out_path)
        rel = out_path.relative_to(ROOT) if out_path.is_relative_to(ROOT) else out_path
        print(f"{deck.slide_count:>3} slides  →  {rel}")


if __name__ == "__main__":
    main()
