#!/usr/bin/env python3
"""Fail deployment if the public artifact exposes source or implementation details."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"

FORBIDDEN_EXT = {".json", ".py", ".pyc", ".yml", ".yaml", ".md", ".toml", ".ini", ".env", ".log", ".sql", ".zip", ".map"}
FORBIDDEN_TEXT = [
    (re.compile(r"\bGitHub Actions\b", re.I), "GitHub Actions"),
    (re.compile(r"Código y datos públicos", re.I), "Código y datos públicos"),
    (re.compile(r"Generado automáticamente", re.I), "Generado automáticamente"),
    (re.compile(r"asistida automáticamente", re.I), "asistida automáticamente"),
    (re.compile(r"Motor de esta edición", re.I), "Motor de esta edición"),
    (re.compile(r"Automatización e IA", re.I), "Automatización e IA"),
    (re.compile(r"El Diario puede apoyarse en un modelo de lenguaje", re.I), "atribución a modelo de lenguaje"),
    (re.compile(r"(?:generad[oa]|redactad[oa]|escrit[oa]|cread[oa]).{0,80}(?:OpenAI|inteligencia artificial|\bIA\b|modelo de lenguaje)", re.I | re.S), "atribución de autoría a IA"),
    (re.compile(r"GW_DIARY_OPENAI_MODEL", re.I), "variable interna de modelo"),
]


def fail(msg: str, errors: list[str]) -> None:
    errors.append(msg)


def main() -> int:
    errors: list[str] = []
    if not SITE.exists():
        fail("No existe _site", errors)
    else:
        for path in SITE.rglob("*"):
            if not path.is_file():
                continue
            rr = path.relative_to(SITE).as_posix()
            if path.suffix.lower() in FORBIDDEN_EXT:
                fail(f"Archivo no publicable: {rr}", errors)
            if path.suffix.lower() in {".html", ".htm", ".xml", ".js", ".css", ".txt"}:
                try:
                    text = path.read_text(encoding="utf-8")
                except Exception:
                    continue
                for pattern, label in FORBIDDEN_TEXT:
                    if pattern.search(text):
                        fail(f"{rr}: referencia pública no permitida ({label})", errors)
                if path.suffix.lower() in {".html", ".htm"}:
                    if re.search(r"(?:href|src)=[\"'][^\"']+\.json(?:[?\"'])", text, re.I):
                        fail(f"{rr}: enlace directo a JSON", errors)
                    if "gw-runtime-" not in text:
                        fail(f"{rr}: falta runtime de datos encapsulados", errors)

    if errors:
        print("AUDITORÍA PÚBLICA: ERROR")
        for e in errors:
            print(" -", e)
        return 2
    print("AUDITORÍA PÚBLICA: OK · sin JSON, backend, workflows, source maps ni referencias de implementación.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
