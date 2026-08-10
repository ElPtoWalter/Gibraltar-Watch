#!/usr/bin/env python3
"""Remove implementation-specific metadata from reader-facing generated files."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

DROP_KEYS = {
    "generator", "generator_name", "generator_version",
    "model", "model_name", "model_id",
    "provider", "engine", "prompt", "prompt_version",
    "openai", "openai_model", "ai_model", "diary_generator",
}

TARGETS = [
    ROOT / "diario" / "latest.json",
    ROOT / "newsletter" / "latest.json",
    ROOT / "observatory.json",
    ROOT / "health.json",
]


def clean(value):
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items() if k.lower() not in DROP_KEYS}
    if isinstance(value, list):
        return [clean(v) for v in value]
    return value


def main() -> int:
    changed = 0
    for path in TARGETS:
        if not path.exists():
            continue
        try:
            old_obj = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        new_obj = clean(old_obj)
        if new_obj != old_obj:
            path.write_text(json.dumps(new_obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            changed += 1
    print(f"Metadatos editoriales saneados en {changed} archivo(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
