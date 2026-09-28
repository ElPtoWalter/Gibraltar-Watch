#!/usr/bin/env python3
"""Run LOCAL and Gemini on the same real Gibraltar packet without publishing."""
from __future__ import annotations

import argparse
import json
import os
from contextlib import contextmanager
from pathlib import Path

import generate_diario_estrecho as journal


@contextmanager
def temporary_environment(values):
    previous = {key: os.environ.get(key) for key in values}
    try:
        for key, value in values.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def run_pilot(root: Path) -> dict:
    data = journal.load_json(root / "geopolitics.json", {})
    events = journal.load_json(root / "events.json", {})
    diary_state = journal.load_json(root / ".github" / "diario-state.json", {})
    status = data.get("status", {}) if isinstance(data, dict) else {}
    # The isolated pilot may use the latest four days of stored real references
    # so a quiet 36-hour news cycle does not prevent comparing both engines.
    # Production selection remains unchanged at 36 hours.
    selected = journal.select_items(data.get("items", []) if isinstance(data, dict) else [], hours=96)
    previous = diary_state.get("latest_entry", {}) if isinstance(diary_state, dict) else {}
    if not status or not selected:
        raise RuntimeError("Missing current real monitor data or newsroom references")
    if not isinstance(events, dict) or not events.get("events"):
        raise RuntimeError("Missing real event store; run build_events.py first")
    mode = journal.edition_mode(status, selected, events)

    local_trace = {}
    with temporary_environment({"GEMINI_API_KEY": None, "OPENROUTER_API_KEY": None}):
        local_draft, local_engine, local_status = journal.build_draft(
            status, selected, mode, events, previous, local_trace
        )
    if not os.environ.get("GEMINI_API_KEY", "").strip():
        raise RuntimeError("GEMINI_API_KEY is not configured for the isolated pilot")
    gemini_trace = {}
    with temporary_environment({"OPENROUTER_API_KEY": None}):
        gemini_draft, gemini_engine, gemini_status = journal.build_draft(
            status, selected, mode, events, previous, gemini_trace
        )

    local_hash = local_trace.get("factual_packet_hash")
    gemini_hash = gemini_trace.get("factual_packet_hash")
    checks = {
        "same_factual_packet": bool(local_hash and local_hash == gemini_hash),
        "local_rules_ok": local_engine == "rules",
        "gemini_selected": gemini_engine == "gemini" and gemini_status == "ok",
        "validator_same_version": local_trace.get("validator_version") == gemini_trace.get("validator_version"),
        "event_ids_same": local_trace.get("event_ids") == gemini_trace.get("event_ids"),
        "source_ids_same": local_trace.get("source_ids") == gemini_trace.get("source_ids"),
        "canonical_state_preserved": journal.status_text(status, "maritime_status") == journal.status_text(data.get("status", {}), "maritime_status"),
        "spanish_output_complete": all(key in gemini_draft for key in ("headline", "deck", "situation", "sections", "meaning", "watch")),
    }
    return {
        "schema_version": 1,
        "site": "Gibraltar Watch",
        "timestamp": journal.NOW_UTC.isoformat(),
        "published": False,
        "canonical_state": journal.status_text(status, "maritime_status"),
        "factual_packet_hash": local_hash,
        "checks": checks,
        "passed": all(checks.values()),
        "local": {"engine": local_engine, "assistant_status": local_status, "draft": local_draft},
        "gemini": {"engine": gemini_engine, "assistant_status": gemini_status, "attempts": gemini_trace.get("attempts", []), "draft": gemini_draft},
        "trace": {
            "validator_version": gemini_trace.get("validator_version"),
            "event_ids": gemini_trace.get("event_ids", []),
            "source_ids": gemini_trace.get("source_ids", []),
            "verification_summary": gemini_trace.get("verification_summary", {}),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = run_pilot(args.root.resolve())
    except RuntimeError as exc:
        print(f"Piloto Gemini: ERROR · {exc}")
        return 1
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    print(f"Piloto Gemini: {'OK' if report['passed'] else 'FALLO'} · packet={report['factual_packet_hash']} · publicación=no")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
