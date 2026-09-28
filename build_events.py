#!/usr/bin/env python3
"""Rebuild the StraitWatch event store from the normalized Gibraltar news data."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from update_geopolitics import EVENTS, DATA, SOURCE_REGISTRY, NewsItem, classify, event_store_for
from straitwatch_core import canonical_url, write_json_if_changed


def load(path: Path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def normalise_item(raw: dict) -> NewsItem:
    values = {
        key: raw[key]
        for key in NewsItem.__dataclass_fields__
        if key in raw
    }
    original_source = str(values.get("source") or "").strip()
    profile = SOURCE_REGISTRY.resolve(original_source, values.get("url"))
    values.update(
        source=profile.canonical_name if profile.source_id != "unknown" else (original_source or profile.canonical_name),
        source_id=profile.source_id,
        url=canonical_url(values.get("url")),
        weight=profile.tier if profile.source_id != "unknown" else values.get("weight", 1),
    )
    return NewsItem(**values)


def main() -> int:
    data = load(DATA, {})
    items = []
    for raw in data.get("items", []) if isinstance(data, dict) else []:
        if not isinstance(raw, dict):
            continue
        try:
            items.append(normalise_item(raw))
        except TypeError:
            continue
    store = event_store_for(items, load(EVENTS, {}))
    if isinstance(data, dict):
        data["version"] = 2
        data["status"] = classify(items, data)
        data["items"] = [asdict(item) for item in items]
        write_json_if_changed(DATA, data)
    write_json_if_changed(EVENTS, store)
    print(f"Eventos Gibraltar: {store['article_count']} articulos -> {store['event_count']} acontecimientos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
