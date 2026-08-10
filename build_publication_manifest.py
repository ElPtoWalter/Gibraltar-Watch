#!/usr/bin/env python3
"""Create a checksum manifest for the build that is about to be committed."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "publication-manifest.json"
FILES = [
    "index.html", "situacion-actual.html", "trafico.html", "sismicidad.html", "fuentes.html",
    "datos.html", "mapa-estrategico.html", "transparencia.html", "correcciones.html", "boletin.html",
    "gw-observatory.css", "gw-observatory.js", "observatory.json", "health.json",
    "timeline.json", "observatory-history.json", "observatory-feed.xml", "sitemap.xml",
    "diario/index.html", "diario/latest.json", "newsletter/latest.html", "newsletter/latest.txt", "newsletter/latest.json",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    missing = [rel for rel in FILES if not (ROOT / rel).exists()]
    if missing:
        raise SystemExit("No se puede crear el manifiesto; faltan: " + ", ".join(missing))
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "git": {
            "sha_before_commit": os.getenv("GITHUB_SHA", "local"),
            "run_id": os.getenv("GITHUB_RUN_ID", "local"),
        },
        "recovery": {
            "method": "git-history",
            "note_es": "Cada publicación validada queda versionada en Git. Para recuperar una versión, restaura un commit anterior verificado.",
        },
        "files": {rel: {"sha256": sha256(ROOT / rel), "bytes": (ROOT / rel).stat().st_size} for rel in FILES},
    }
    tmp = OUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(OUT)
    print(f"Manifiesto de publicación creado: {len(FILES)} archivos verificados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
