#!/usr/bin/env python3
"""Read a book.yaml and emit shell-evalable variables.

Usage: bookcfg.py <book.yaml> shellvars
"""
import sys, shlex, re
import yaml

def main():
    if len(sys.argv) < 3:
        print("Usage: bookcfg.py <book.yaml> shellvars", file=sys.stderr)
        sys.exit(1)
    path, mode = sys.argv[1], sys.argv[2]
    with open(path) as fh:
        cfg = yaml.safe_load(fh)
    if mode != "shellvars":
        sys.exit(f"unknown mode: {mode}")

    eds = cfg.get("editions", [])
    langs = [e["lang"] for e in eds]
    out = []
    out.append(f"SLUG={shlex.quote(str(cfg['slug']))}")
    out.append(f"PRIMARY_LANG={shlex.quote(str(cfg['primary_language']))}")
    out.append(f"TRIM={shlex.quote(str(cfg.get('trim', '6x9')))}")
    out.append(f"FORMATS={shlex.quote(' '.join(cfg.get('formats', ['epub'])))}")
    out.append(f"EDITIONS={shlex.quote(' '.join(langs))}")
    for e in eds:
        if e.get("translate_from"):
            lang_var = re.sub(r'[^A-Za-z0-9_]', '_', e['lang'])
            out.append(f"TRANSLATE_FROM_{lang_var}={shlex.quote(str(e['translate_from']))}")
    tr = cfg.get("transcription", {})
    out.append(f"TRANS_MODEL={shlex.quote(str(tr.get('model', 'large-v3')))}")
    out.append(f"TRANS_LANG={shlex.quote(str(tr.get('language', 'auto')))}")
    print("\n".join(out))

if __name__ == "__main__":
    main()
