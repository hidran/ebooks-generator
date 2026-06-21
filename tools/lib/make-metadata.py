#!/usr/bin/env python3
"""Emit a pandoc YAML metadata block for one edition.

Usage: make-metadata.py <book.yaml> <lang>
"""
import sys, yaml

# Minimal BCP-47 region map; extend as needed.
REGION = {"en": "en-US", "it": "it-IT", "es": "es-ES", "fr": "fr-FR",
          "de": "de-DE", "pt": "pt-BR"}

def main():
    path, lang = sys.argv[1], sys.argv[2]
    with open(path) as fh:
        cfg = yaml.safe_load(fh)
    edition = next((e for e in cfg.get("editions", []) if e["lang"] == lang), {})

    meta = {
        "title": edition.get("title", cfg["title"]),
        "subtitle": edition.get("subtitle", cfg.get("subtitle", "")),
        "author": cfg["author"],
        "language": REGION.get(lang, lang),
        "date": str(cfg.get("date", "")),
        "rights": cfg.get("rights", ""),
        "publisher": cfg.get("publisher", ""),
        "keywords": cfg.get("keywords", []),
        "toc": True,
        "toc-depth": 2,
    }
    desc = cfg.get("description", "")
    if desc:
        meta["description"] = desc
    print("---")
    print(yaml.safe_dump(meta, allow_unicode=True, sort_keys=False).strip())
    print("---")

if __name__ == "__main__":
    main()
