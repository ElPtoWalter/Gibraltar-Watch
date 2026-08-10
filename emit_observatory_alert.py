#!/usr/bin/env python3
"""Expose conservative Observatory state changes as GitHub Actions outputs.

This script never decides the underlying facts. It only reads observatory.json,
which is built from the project's existing validated data layers.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OBS = ROOT / "observatory.json"


def clean(value: object) -> str:
    return str(value or "").replace("\r", " ").replace("\n", " ").strip()


def main() -> int:
    if not OBS.exists():
        raise SystemExit("No existe observatory.json; ejecuta update_observatory.py primero.")
    data = json.loads(OBS.read_text(encoding="utf-8"))
    state = data.get("state") or {}
    changes = data.get("changes") or {}
    level = state.get("alert_level") or {}
    severity = int(state.get("severity", 0) or 0)
    state_changed = bool(changes.get("state_changed"))

    # Only open a GitHub alert for a material state transition to severity 3+.
    # Lower levels remain visible on-site without creating notification noise.
    notify = state_changed and severity >= 3
    resolve = state_changed and severity < 3

    outputs = {
        "state_code": clean(state.get("code")),
        "state_label": clean(state.get("label_es")),
        "alert_code": clean(level.get("code")),
        "alert_label": clean(level.get("label_es")),
        "severity": str(severity),
        "state_changed": str(state_changed).lower(),
        "notify": str(notify).lower(),
        "resolve": str(resolve).lower(),
        "summary": clean(state.get("summary_es")),
        "confidence": clean(state.get("confidence")),
    }
    output_path = os.getenv("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a", encoding="utf-8") as fh:
            for key, value in outputs.items():
                fh.write(f"{key}={value}\n")

    prefix = "::warning::" if notify else "::notice::"
    print(
        f"{prefix}Observatorio: {outputs['state_label']} · "
        f"alerta {outputs['alert_label']} · confianza {outputs['confidence']} · "
        f"cambio={outputs['state_changed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
