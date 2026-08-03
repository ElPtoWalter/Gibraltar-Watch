#!/usr/bin/env python3
"""Añade de forma idempotente la hoja de pulido visual a todas las páginas HTML."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LINK = '<link rel="stylesheet" href="gibraltar-layout-polish.css?v=20260803-1">'
PATTERN = re.compile(r'\s*<link[^>]+href=["\']gibraltar-layout-polish\.css(?:\?[^"\']*)?["\'][^>]*>\s*', re.I)


def update_html(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    cleaned = PATTERN.sub("", original)
    if "</head>" not in cleaned.lower():
        return False
    updated = re.sub(r"</head>", f"{LINK}\n</head>", cleaned, count=1, flags=re.I)
    if updated == original:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def main() -> None:
    changed = []
    for path in sorted(ROOT.glob("*.html")):
        if update_html(path):
            changed.append(path.name)
    print(f"Pulido visual aplicado a {len(changed)} páginas.")
    if changed:
        print("Actualizadas:", ", ".join(changed))


if __name__ == "__main__":
    main()
