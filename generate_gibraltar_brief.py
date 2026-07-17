#!/usr/bin/env python3
"""Genera un parte científico diario desde seismicity.json.

El generador no predice terremotos ni infiere cierre tectónico a partir de
actividad sísmica. Solo resume el catálogo y la salud del observatorio.
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path(os.getenv("GIBRALTAR_ROOT", Path(__file__).resolve().parent))
MADRID = ZoneInfo("Europe/Madrid")
BASE = "https://estrechogibraltar.com"
MAX_ARCHIVE = 120

def load_json(name: str, default: Any) -> Any:
    path = ROOT / name
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default

def stable_write(path: Path, content: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    previous = path.read_text(encoding="utf-8") if path.exists() else None
    if previous == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True

def dump_json(path: Path, value: Any) -> bool:
    return stable_write(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")

def parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None

def event_value(event: dict[str, Any], *names: str) -> Any:
    for name in names:
        if event.get(name) is not None:
            return event.get(name)
    properties = event.get("properties") if isinstance(event.get("properties"), dict) else {}
    for name in names:
        if properties.get(name) is not None:
            return properties.get(name)
    return None

def event_description(event: dict[str, Any] | None, lang: str) -> str:
    if not event:
        return "No hay un último evento disponible." if lang == "es" else "No latest event is available."
    magnitude = event_value(event, "magnitude", "mag")
    place = event_value(event, "place", "location") or ("ubicación no indicada" if lang == "es" else "location not stated")
    raw_time = event_value(event, "time", "at", "datetime")
    if isinstance(raw_time, (int, float)):
        raw_time = datetime.fromtimestamp(raw_time / 1000 if raw_time > 10_000_000_000 else raw_time, tz=timezone.utc).isoformat()
    time = parse_time(raw_time)
    time_text = time.astimezone(MADRID).strftime("%d/%m/%Y %H:%M") if time else "—"
    mag_text = f"M {magnitude}" if magnitude is not None else "M —"
    if lang == "es":
        return f"{mag_text} · {place} · {time_text} (hora peninsular)"
    return f"{mag_text} · {place} · {time_text} (Europe/Madrid)"

def health_state(data: dict[str, Any], now: datetime) -> tuple[str, str, str]:
    checked = parse_time(data.get("checked_at"))
    if str(data.get("status", "")).upper() != "OK":
        return "DEGRADED", "Fuente sísmica degradada", "Seismic source degraded"
    if checked is None or (now - checked).total_seconds() > 8 * 3600:
        return "STALE", "Datos sísmicos desactualizados", "Seismic data out of date"
    return "OK", "Observatorio operativo", "Observatory operational"

def build_interpretation(data: dict[str, Any], health: str) -> tuple[list[str], list[str]]:
    periods = data.get("periods") if isinstance(data.get("periods"), dict) else {}
    count_24 = int(periods.get("24h") or 0)
    count_7 = int(periods.get("7d") or 0)
    count_30 = int(periods.get("30d") or 0)
    max_mag = data.get("max_magnitude_30d")

    es = [
        "La sismicidad confirma que la región tectónica está activa, pero no permite calcular una tasa de cierre del canal.",
        "Un aumento o descenso de eventos pequeños puede depender de la red observadora, revisiones del catálogo y secuencias locales.",
        "La actividad sísmica no equivale a una predicción de terremotos ni a una interrupción de la navegación."
    ]
    en = [
        "Seismicity confirms that the tectonic region is active, but it cannot be used to calculate a closure rate for the channel.",
        "A rise or fall in small events may reflect network coverage, catalogue revisions and local sequences.",
        "Seismic activity is not an earthquake prediction and does not imply disruption to navigation."
    ]

    if health != "OK":
        es.insert(0, "La fuente automática no está suficientemente fresca; consulta IGN y protección civil antes de interpretar el panel.")
        en.insert(0, "The automatic source is not sufficiently fresh; consult IGN and civil-protection authorities before interpreting the panel.")
    elif count_30 == 0:
        es.insert(0, "El catálogo consultado no contiene eventos M≥1 en el área durante los últimos 30 días.")
        en.insert(0, "The queried catalogue contains no M≥1 events in the area during the last 30 days.")
    elif max_mag is not None and float(max_mag) >= 4.5:
        es.insert(0, f"El catálogo incluye un evento de magnitud máxima M {max_mag} en 30 días; requiere contexto sismológico, no una conclusión sobre cierre.")
        en.insert(0, f"The catalogue includes a maximum M {max_mag} event in 30 days; it requires seismological context, not a conclusion about closure.")
    else:
        es.insert(0, f"El catálogo registra {count_24} eventos en 24 h, {count_7} en 7 días y {count_30} en 30 días dentro del filtro utilizado.")
        en.insert(0, f"The catalogue records {count_24} events in 24 h, {count_7} in 7 days and {count_30} in 30 days under the selected filter.")
    return es, en

def material_hash(value: dict[str, Any]) -> str:
    selected = {
        "date": value["date"],
        "health": value["health"],
        "periods": value["seismic"]["periods"],
        "max": value["seismic"]["max_magnitude_30d"],
        "last": value["seismic"]["last_event_es"],
        "summary": value["summary_es"]
    }
    return hashlib.sha256(json.dumps(selected, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]

def short_post(text: str, limit: int = 255) -> str:
    text = re.sub(r"[ \t]+", " ", text).strip()
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"

def build_feed(items: list[dict[str, Any]], updated: str) -> str:
    entries = []
    for item in items[:30]:
        entries.append(f"""  <entry>
    <title>{html.escape(item.get("headline_es", "Parte científico"))} · {item.get("date", "")}</title>
    <id>{BASE}/parte-diario.html#{item.get("date", "")}</id>
    <link href="{BASE}/parte-diario.html"/>
    <updated>{item.get("generated_at", updated)}</updated>
    <summary>{html.escape(item.get("summary_es", ""))}</summary>
  </entry>""")
    return f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Parte científico · Gibraltar Watch</title>
  <id>{BASE}/gibraltar-brief-feed.xml</id>
  <link href="{BASE}/gibraltar-brief-feed.xml" rel="self"/>
  <link href="{BASE}/parte-diario.html"/>
  <updated>{updated}</updated>
{chr(10).join(entries)}
</feed>
"""

def main() -> int:
    data = load_json("seismicity.json", {})
    if not isinstance(data, dict):
        raise SystemExit("seismicity.json no es un objeto JSON válido.")

    now = datetime.now(timezone.utc)
    date = now.astimezone(MADRID).date().isoformat()
    generated_at = now.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    health, health_es, health_en = health_state(data, now)
    periods = data.get("periods") if isinstance(data.get("periods"), dict) else {}
    periods = {
        "24h": int(periods.get("24h") or 0),
        "7d": int(periods.get("7d") or 0),
        "30d": int(periods.get("30d") or 0)
    }
    max_mag = data.get("max_magnitude_30d")
    last_event = data.get("last_event") if isinstance(data.get("last_event"), dict) else None
    interpretation_es, interpretation_en = build_interpretation(data, health)

    archive = load_json("gibraltar-brief-archive.json", [])
    if isinstance(archive, dict):
        archive = archive.get("items", [])
    if not isinstance(archive, list):
        archive = []
    previous = next((item for item in archive if item.get("date") != date), None)

    current_key = (health, periods["24h"], periods["7d"], periods["30d"], max_mag, event_description(last_event, "es"))
    previous_key = None
    if previous:
        p_seismic = previous.get("seismic") if isinstance(previous.get("seismic"), dict) else {}
        p_periods = p_seismic.get("periods") if isinstance(p_seismic.get("periods"), dict) else {}
        previous_key = (
            previous.get("health"), p_periods.get("24h"), p_periods.get("7d"), p_periods.get("30d"),
            p_seismic.get("max_magnitude_30d"), p_seismic.get("last_event_es")
        )

    if previous is None:
        change_es = "Primera línea base del parte científico; no representa por sí sola una novedad."
        change_en = "First scientific-brief baseline; this does not by itself represent a new development."
        publish = False
    elif current_key == previous_key:
        change_es = "Sin cambio material frente al parte diario anterior."
        change_en = "No material change from the previous daily brief."
        publish = False
    else:
        change_es = "Han cambiado los datos sísmicos o la salud de la fuente respecto al parte anterior."
        change_en = "Seismic data or source health has changed since the previous brief."
        publish = bool(
            health != previous.get("health")
            or (max_mag is not None and float(max_mag) >= 4.5)
        )

    if health == "OK":
        headline_es = "Sin indicios científicos de cierre a escala humana"
        headline_en = "No scientific indication of closure on a human timescale"
    else:
        headline_es = "Observatorio sísmico pendiente de datos fiables"
        headline_en = "Seismic observatory awaiting reliable data"

    summary_es = (
        f"El paso oceánico continúa siendo una conexión natural abierta. El catálogo automático registra "
        f"{periods['30d']} eventos M≥1 en 30 días"
        + (f", con una magnitud máxima de M {max_mag}" if max_mag is not None else "")
        + ". Estos datos describen sismicidad regional y no permiten inferir una tasa de cierre."
    )
    summary_en = (
        f"The ocean passage remains a naturally open connection. The automatic catalogue records "
        f"{periods['30d']} M≥1 events in 30 days"
        + (f", with a maximum magnitude of M {max_mag}" if max_mag is not None else "")
        + ". These data describe regional seismicity and cannot be used to infer a closure rate."
    )

    brief = {
        "schema_version": 1,
        "date": date,
        "generated_at": generated_at,
        "source_checked_at": data.get("checked_at"),
        "health": health,
        "health_label_es": health_es,
        "health_label_en": health_en,
        "headline_es": headline_es,
        "headline_en": headline_en,
        "short_conclusion_es": "No existe una predicción científica de cierre del Estrecho en décadas o siglos.",
        "short_conclusion_en": "There is no scientific forecast of the Strait closing within decades or centuries.",
        "summary_es": summary_es,
        "summary_en": summary_en,
        "change_es": change_es,
        "change_en": change_en,
        "seismic": {
            "source": data.get("source", "USGS Earthquake Catalog"),
            "source_query": data.get("source_query"),
            "periods": periods,
            "max_magnitude_30d": max_mag,
            "last_event_es": event_description(last_event, "es"),
            "last_event_en": event_description(last_event, "en"),
            "data_note_es": data.get("data_note_es"),
            "data_note_en": data.get("data_note_en")
        },
        "interpretation_es": interpretation_es,
        "interpretation_en": interpretation_en,
        "watchlist_es": [
            "Catálogos del IGN y USGS, teniendo en cuenta revisiones y diferencias de completitud.",
            "Avisos oficiales de protección civil ante eventos relevantes.",
            "Continuidad del tráfico mediante trayectorias AIS completas y avisos marítimos, no puntos aislados.",
            "Resultados oficiales de las campañas geológicas del enlace fijo España–Marruecos."
        ],
        "watchlist_en": [
            "IGN and USGS catalogues, accounting for revisions and completeness differences.",
            "Official civil-protection notices following relevant events.",
            "Traffic continuity through completed AIS tracks and maritime notices, not isolated points.",
            "Official results from Spain–Morocco fixed-link geological campaigns."
        ],
        "publish_recommended": publish
    }
    brief["material_hash"] = material_hash(brief)

    existing = load_json("gibraltar-brief.json", {})
    if isinstance(existing, dict) and existing.get("material_hash") == brief["material_hash"]:
        brief["generated_at"] = existing.get("generated_at", generated_at)

    archive = [item for item in archive if item.get("date") != date]
    archive.insert(0, brief)
    archive = archive[:MAX_ARCHIVE]

    url_es = f"{BASE}/parte-diario.html?utm_source=x&utm_medium=social&utm_campaign=parte_cientifico&utm_content=es"
    url_en = f"{BASE}/en-daily-brief.html?utm_source=x&utm_medium=social&utm_campaign=scientific_brief&utm_content=en"
    post_es = short_post(f"PARTE CIENTÍFICO — ESTRECHO DE GIBRALTAR\n\n{headline_es}.\n\n{summary_es}")
    post_en = short_post(f"SCIENTIFIC BRIEF — STRAIT OF GIBRALTAR\n\n{headline_en}.\n\n{summary_en}")
    social = {
        "generated_at": brief["generated_at"],
        "publish_recommended": publish,
        "status_es": f"{post_es}\n\n{url_es}",
        "status_en": f"{post_en}\n\n{url_en}"
    }

    dump_json(ROOT / "gibraltar-brief.json", brief)
    dump_json(ROOT / "gibraltar-brief-archive.json", archive)
    dump_json(ROOT / "gibraltar-social-drafts.json", social)
    dump_json(ROOT / "briefs" / f"{date}.json", brief)
    stable_write(ROOT / "gibraltar-brief-feed.xml", build_feed(archive, brief["generated_at"]))
    print(f"Parte científico generado: {date} · publicar={publish}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
