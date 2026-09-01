#!/usr/bin/env python3
"""Build the live observatory layer for Gibraltar Watch.

This script does not fetch the news itself. It consolidates the validated outputs
already produced by update_gibraltar.py, update_ope.py, update_geopolitics.py and
Diario del Estrecho into a single, conservative operational view.
"""
from __future__ import annotations

import json
import os
import statistics
from datetime import datetime, timezone
from email.utils import format_datetime, parsedate_to_datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parent
NOW = datetime.now(timezone.utc)
MADRID = ZoneInfo("Europe/Madrid")
LOCAL_TODAY = NOW.astimezone(MADRID).date()

SEISMIC = ROOT / "seismicity.json"
GEO = ROOT / "geopolitics.json"
OPE = ROOT / "ope-2026.json"
DIARY = ROOT / "diario" / "latest.json"
HISTORY = ROOT / "observatory-history.json"
MEMORY = ROOT / "observatory-state-memory.json"
TIMELINE = ROOT / "timeline.json"
OBSERVATORY = ROOT / "observatory.json"
HEALTH = ROOT / "health.json"
FEED = ROOT / "observatory-feed.xml"

CRITICAL_PAGES = [
    "index.html",
    "situacion-actual.html",
    "trafico.html",
    "sismicidad.html",
    "fuentes.html",
    "diario/index.html",
    "datos.html",
    "mapa-estrategico.html",
    "transparencia.html",
    "correcciones.html",
]


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def atomic_json(path: Path, payload) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def iso(dt: datetime | None = None) -> str:
    dt = dt or NOW
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_dt(value) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass
    try:
        dt = parsedate_to_datetime(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def age_minutes(value) -> int | None:
    dt = parse_dt(value)
    if not dt:
        return None
    return max(0, int((NOW - dt).total_seconds() // 60))


def nested(status: dict, key: str, lang: str = "es", default: str = "—") -> str:
    value = status.get(key, default)
    if isinstance(value, dict):
        return str(value.get(lang, default) or default)
    return str(value or default)


def source_health(name: str, timestamp, source: str, good_minutes: int, warn_minutes: int, note: str = "", url: str = "") -> dict:
    age = age_minutes(timestamp)
    if age is None:
        state = "missing"
        label = "SIN DATOS"
    elif age <= good_minutes:
        state = "fresh"
        label = "ACTUALIZADO"
    elif age <= warn_minutes:
        state = "aging"
        label = "REVISAR FRESCURA"
    else:
        state = "stale"
        label = "DESACTUALIZADO"
    return {
        "name": name,
        "state": state,
        "label_es": label,
        "checked_at": timestamp,
        "age_minutes": age,
        "source": source,
        "url": url,
        "note_es": note,
    }


def severity_for(kind: str, value: str) -> int:
    t = (value or "").upper()
    if kind == "maritime":
        if any(x in t for x in ("CERRAD", "CLOSED", "INTERRUMP", "HALT", "SUSPEND")):
            return 4
        if any(x in t for x in ("RESTR", "CONGEST", "INCID", "DELAY", "LIMIT")):
            return 2
        if any(x in t for x in ("VIGIL", "WATCH")):
            return 1
        return 0
    if kind == "border":
        if any(x in t for x in ("CRÍT", "CRIT")):
            return 3
        if any(x in t for x in ("ALTA", "HIGH", "ELEVAD")):
            return 2
        if any(x in t for x in ("MEDIA", "MODER", "VIGIL", "WATCH")):
            return 1
        return 0
    if kind == "bilateral":
        if any(x in t for x in ("RUPT", "BREAKDOWN", "CRÍT", "CRIT")):
            return 3
        if any(x in t for x in ("ELEVAD", "TENSA", "TENSE", "HIGH")):
            return 2
        if any(x in t for x in ("VIGIL", "WATCH", "FRIC")):
            return 1
        return 0
    if kind == "security":
        if any(x in t for x in ("CRÍT", "CRIT", "ALERTA", "ALERT")) and "SIN ALERTA" not in t and "NO SPECIFIC ALERT" not in t:
            return 3
        if any(x in t for x in ("REFORZ", "HEIGHTENED", "ELEVAD")):
            return 2
        if any(x in t for x in ("VIGIL", "WATCH")):
            return 1
        return 0
    return 0


def overall_state(status: dict, health_state: str) -> dict:
    maritime = nested(status, "maritime_status")
    border = nested(status, "border_pressure")
    bilateral = nested(status, "bilateral_tension")
    security = nested(status, "security_status")
    scores = {
        "maritime": severity_for("maritime", maritime),
        "border": severity_for("border", border),
        "bilateral": severity_for("bilateral", bilateral),
        "security": severity_for("security", security),
    }
    mx = max(scores.values(), default=0)
    if scores["maritime"] >= 4:
        code, label, color = "operational_alert", "ALERTA OPERATIVA", "red"
        summary = "El monitor detecta una señal compatible con interrupción o cierre. Debe verificarse con avisos marítimos oficiales antes de afirmarlo como hecho."
    elif mx >= 3:
        code, label, color = "high_watch", "VIGILANCIA ALTA", "red"
        summary = "Hay señales relevantes en una o más capas del observatorio; el corredor marítimo se evalúa por separado de la tensión política o fronteriza."
    elif mx >= 2:
        code, label, color = "reinforced_watch", "VIGILANCIA REFORZADA", "orange"
        summary = "Existen incidencias o tensión apreciable, sin que ello implique por sí solo una interrupción del Estrecho."
    elif mx == 1:
        code, label, color = "watch", "VIGILANCIA", "yellow"
        summary = "La situación requiere seguimiento, pero no aparecen señales suficientes para elevar el nivel operativo."
    else:
        code, label, color = "normal", "NORMALIDAD OPERATIVA", "green"
        summary = "No aparecen señales suficientes para elevar el nivel general del observatorio."
    if health_state in {"degraded", "stale"}:
        summary += " Parte de las fuentes necesita actualización, por lo que la lectura debe interpretarse con cautela."
    return {
        "code": code,
        "label_es": label,
        "color": color,
        "severity": mx,
        "summary_es": summary,
        "layers": {
            "maritime": {"value": maritime, "severity": scores["maritime"]},
            "border": {"value": border, "severity": scores["border"]},
            "bilateral": {"value": bilateral, "severity": scores["bilateral"]},
            "security": {"value": security, "severity": scores["security"]},
        },
    }


def alert_level_for(state: dict) -> dict:
    severity = int(state.get("severity", 0) or 0)
    if severity >= 4:
        return {"code": "urgent", "label_es": "URGENTE", "meaning_es": "Señal operativa excepcional que exige verificación oficial inmediata."}
    if severity >= 3:
        return {"code": "important", "label_es": "IMPORTANTE", "meaning_es": "Cambio relevante que merece seguimiento prioritario."}
    if severity >= 2:
        return {"code": "relevant", "label_es": "RELEVANTE", "meaning_es": "Hay una alteración apreciable, sin implicar cierre del corredor."}
    return {"code": "informational", "label_es": "INFORMATIVO", "meaning_es": "Seguimiento ordinario o cambio menor."}


def confidence(status: dict, health_state: str) -> str:
    raw = nested(status, "confidence").upper()
    rank = 2 if "ALTA" in raw or "HIGH" in raw else 1 if "MEDIA" in raw or "MEDIUM" in raw else 0
    if health_state == "degraded":
        rank = max(0, rank - 1)
    elif health_state == "stale":
        rank = 0
    return ("BAJA", "MEDIA", "ALTA")[rank]


def metrics(seismic: dict, geopolitics: dict, ope: dict, diary: dict) -> dict:
    items = geopolitics.get("items", []) if isinstance(geopolitics, dict) else []
    recent_24 = 0
    sources = set()
    for item in items:
        dt = parse_dt(item.get("published_at"))
        if dt and (NOW - dt).total_seconds() <= 86400:
            recent_24 += 1
        if item.get("source"):
            sources.add(str(item["source"]))
    departure = (ope.get("departure") or {}).get("day") or {}
    returning = (ope.get("return") or {}).get("day") or {}
    return {
        "news_24h": recent_24,
        "news_sources": len(sources),
        "seismic_24h": (seismic.get("periods") or {}).get("24h"),
        "seismic_7d": (seismic.get("periods") or {}).get("7d"),
        "seismic_30d": (seismic.get("periods") or {}).get("30d"),
        "seismic_max_30d": seismic.get("max_magnitude_30d"),
        "ope_report_date": ope.get("report_date"),
        "ope_passengers_day": (departure.get("passengers") or 0) + (returning.get("passengers") or 0),
        "ope_vehicles_day": (departure.get("vehicles") or 0) + (returning.get("vehicles") or 0),
        "ope_rotations_day": (departure.get("rotations") or 0) + (returning.get("rotations") or 0),
        "diary_date": diary.get("date"),
        "diary_source_count": diary.get("source_count"),
    }


def numeric_history(history: list[dict], key: str, days: int = 14) -> list[float]:
    out = []
    for snap in history[:days]:
        value = (snap.get("metrics") or {}).get(key)
        if isinstance(value, (int, float)):
            out.append(float(value))
    return out


def detect_anomalies(current: dict, history: list[dict]) -> list[dict]:
    anomalies = []
    if len(history) >= 7:
        hist_news = numeric_history(history, "news_24h")
        if hist_news:
            med = statistics.median(hist_news)
            cur = current.get("news_24h") or 0
            if cur >= max(8, med * 1.8):
                anomalies.append({
                    "key": "news-volume",
                    "level": "info",
                    "title_es": "Volumen informativo superior al patrón reciente",
                    "detail_es": f"Se detectan {cur} referencias en 24 h frente a una mediana reciente de {med:.0f}. Es una señal de atención, no una prueba de crisis.",
                })
        hist_quakes = numeric_history(history, "seismic_7d")
        if hist_quakes:
            med = statistics.median(hist_quakes)
            cur = current.get("seismic_7d") or 0
            if cur >= max(5, med * 2 + 1):
                anomalies.append({
                    "key": "seismic-volume",
                    "level": "info",
                    "title_es": "Actividad sísmica regional por encima del patrón reciente",
                    "detail_es": "El cambio es estadístico y no implica por sí mismo un aumento de peligro ni permite predecir terremotos.",
                })
        hist_ope = [x for x in numeric_history(history, "ope_passengers_day") if x > 0]
        cur = current.get("ope_passengers_day") or 0
        if len(hist_ope) >= 5 and cur > 0:
            med = statistics.median(hist_ope)
            if cur >= med * 1.5:
                anomalies.append({
                    "key": "ope-mobility",
                    "level": "info",
                    "title_es": "Movilidad OPE por encima de la mediana reciente",
                    "detail_es": f"El último parte suma {cur:,} pasajeros en ambos sentidos frente a una mediana reciente de {med:,.0f}.".replace(",", "."),
                })
    return anomalies


def build_health(seismic: dict, geopolitics: dict, ope: dict, diary: dict) -> dict:
    components = [
        source_health("Sismicidad USGS", seismic.get("checked_at"), seismic.get("source", "USGS"), 180, 720, "Catálogo sísmico regional; no es una herramienta de predicción.", seismic.get("source_query", "")),
        source_health("Actualidad y geopolítica", geopolitics.get("generated_at"), "Monitor editorial de fuentes públicas", 180, 720, "Los titulares se usan como señales y requieren atribución.", "fuentes.html"),
        source_health("Operación Paso del Estrecho", ope.get("checked_at"), ope.get("source", "Protección Civil"), 360, 1440, "La frescura de consulta no convierte el parte oficial en un contador en tiempo real.", ope.get("source_url", "")),
    ]
    diary_stamp = diary.get("date")
    report_dt = parse_dt(ope.get("report_date"))
    if report_dt and (NOW - report_dt).total_seconds() > 7 * 86400:
        components[2].update(state="stale", label_es="PARTE ANTIGUO", report_date=ope.get("report_date"),
                             note_es=f'Último parte localizado: {ope.get("report_date")}. Una consulta reciente no actualiza la fecha de sus datos.')
    diary_dt = parse_dt(diary.get("updated_at") or diary.get("published_at") or diary.get("pub_rfc822"))
    if diary_dt is None and diary_stamp:
        try:
            diary_dt = datetime.fromisoformat(str(diary_stamp) + "T06:00:00").replace(tzinfo=MADRID).astimezone(timezone.utc)
        except Exception:
            diary_dt = None
    components.append(source_health("Diario del Estrecho", iso(diary_dt) if diary_dt else None, "Gibraltar Watch", 36 * 60, 60 * 60, "Última edición publicada", f"diario/{diary.get('slug', '')}" if diary.get("slug") else "diario/"))

    missing_pages = [x for x in CRITICAL_PAGES if not (ROOT / x).exists()]
    page_state = "fresh" if not missing_pages else "missing"
    components.append({
        "name": "Integridad del sitio",
        "state": page_state,
        "label_es": "CORRECTA" if not missing_pages else "FALTAN ARCHIVOS",
        "checked_at": iso(),
        "age_minutes": 0,
        "source": "Validador local",
        "note_es": "Todos los archivos críticos están presentes." if not missing_pages else "Faltan: " + ", ".join(missing_pages),
    })

    states = {x["state"] for x in components}
    if "missing" in states or "stale" in states:
        overall = "stale"
    elif "aging" in states:
        overall = "degraded"
    else:
        overall = "healthy"
    return {
        "schema_version": 1,
        "generated_at": iso(),
        "overall": overall,
        "components": components,
        "workflow": {
            "run_id": os.getenv("GITHUB_RUN_ID", "local"),
            "run_attempt": os.getenv("GITHUB_RUN_ATTEMPT", "1"),
            "sha": os.getenv("GITHUB_SHA", "local")[:12],
            "event": os.getenv("GITHUB_EVENT_NAME", "local"),
        },
    }


def make_snapshot(state: dict, metrics_data: dict, health: dict) -> dict:
    return {
        "date": LOCAL_TODAY.isoformat(),
        "generated_at": iso(),
        "state_code": state["code"],
        "state_label": state["label_es"],
        "health": health["overall"],
        "metrics": metrics_data,
    }


def update_history(snapshot: dict) -> list[dict]:
    history = load_json(HISTORY, [])
    if not isinstance(history, list):
        history = []
    if history and history[0].get("date") == snapshot["date"]:
        history[0] = snapshot
    else:
        history.insert(0, snapshot)
    history = history[:730]
    atomic_json(HISTORY, history)
    return history


def event(key: str, title: str, detail: str, level: str = "info", href: str = "") -> dict:
    return {"key": key, "at": iso(), "level": level, "title_es": title, "detail_es": detail, "href": href}


def build_timeline(state: dict, metrics_data: dict, seismic: dict, ope: dict, diary: dict, anomalies: list[dict]) -> tuple[list[dict], dict]:
    old = load_json(MEMORY, {})
    timeline = load_json(TIMELINE, [])
    if not isinstance(timeline, list):
        timeline = []
    events = []
    changes = {"state_changed": bool(old) and old.get("state_code") != state["code"], "previous_state_code": old.get("state_code") if old else None, "layer_changes": []}
    if not old:
        events.append(event("observatory-vnext", "Observatorio avanzado activado", "Se estrena el panel de estado, frescura, cronología, datos históricos y salud de fuentes.", "info", "datos.html"))
    elif old.get("state_code") != state["code"]:
        events.append(event(f"state-{state['code']}-{LOCAL_TODAY.isoformat()}", "Cambio de nivel del observatorio", f"El nivel general pasa a {state['label_es']}. {state['summary_es']}", "alert" if state["severity"] >= 2 else "info", "situacion-actual.html"))

    old_layers = old.get("layers", {})
    for key, title in (("maritime", "Tráfico marítimo"), ("border", "Ceuta y Melilla"), ("bilateral", "España–Marruecos"), ("security", "Seguridad")):
        value = state["layers"][key]["value"]
        if old and old_layers.get(key) != value:
            changes["layer_changes"].append({"key": key, "previous": old_layers.get(key), "current": value})
            events.append(event(f"layer-{key}-{value}-{LOCAL_TODAY.isoformat()}", f"Actualización: {title}", f"El indicador editorial pasa a «{value}».", "info", "situacion-actual.html"))

    if diary.get("date") and diary.get("date") != old.get("diary_date"):
        events.append(event(f"diary-{diary['date']}", "Nueva edición del Diario del Estrecho", diary.get("headline") or "Se ha publicado la edición diaria.", "info", f"diario/{diary.get('slug','')}"))
    if ope.get("report_date") and ope.get("report_date") != old.get("ope_report_date"):
        events.append(event(f"ope-{ope['report_date']}", "Nuevo parte oficial de la OPE", f"Se incorpora el informe correspondiente a {ope.get('report_label_es') or ope['report_date']}.", "data", "operacion-paso-estrecho-2026.html"))
    last_event = seismic.get("last_event") or {}
    if last_event.get("id") and last_event.get("id") != old.get("seismic_event_id"):
        events.append(event(f"seismic-{last_event['id']}", "Nuevo evento en el catálogo sísmico regional", f"M {last_event.get('magnitude','—')} · {last_event.get('place','Región consultada')}. No implica por sí solo un cambio de riesgo.", "data", "sismicidad.html"))
    old_anomaly_keys = set(old.get("anomaly_keys", []))
    for anomaly in anomalies:
        if anomaly["key"] not in old_anomaly_keys:
            events.append(event(f"anomaly-{anomaly['key']}-{LOCAL_TODAY.isoformat()}", anomaly["title_es"], anomaly["detail_es"], "data", "datos.html"))

    existing = {x.get("key") for x in timeline}
    for item in reversed(events):
        if item["key"] not in existing:
            timeline.insert(0, item)
    timeline = timeline[:180]
    atomic_json(TIMELINE, timeline)
    memory = {
        "updated_at": iso(),
        "state_code": state["code"],
        "layers": {k: v["value"] for k, v in state["layers"].items()},
        "diary_date": diary.get("date"),
        "ope_report_date": ope.get("report_date"),
        "seismic_event_id": last_event.get("id"),
        "anomaly_keys": [a["key"] for a in anomalies],
    }
    atomic_json(MEMORY, memory)
    return timeline, changes


def build_feed(timeline: list[dict]) -> str:
    items = []
    for x in timeline[:25]:
        link = "https://estrechogibraltar.com/" + (x.get("href") or "situacion-actual.html").lstrip("/")
        items.append(
            "<item>"
            f"<title>{xml_escape(x.get('title_es',''))}</title>"
            f"<link>{xml_escape(link)}</link>"
            f"<guid>{xml_escape('https://estrechogibraltar.com/#'+x.get('key',''))}</guid>"
            f"<pubDate>{xml_escape(format_datetime(parse_dt(x.get('at')) or NOW))}</pubDate>"
            f"<description>{xml_escape(x.get('detail_es',''))}</description>"
            "</item>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0"><channel>'
        '<title>Gibraltar Watch · Observatorio</title>'
        '<link>https://estrechogibraltar.com/</link>'
        '<description>Cambios de estado, nuevos partes y señales del observatorio del Estrecho de Gibraltar.</description>'
        '<language>es</language>' + "".join(items) + '</channel></rss>\n'
    )


def main() -> int:
    seismic = load_json(SEISMIC, {})
    geopolitics = load_json(GEO, {})
    ope = load_json(OPE, {})
    diary = load_json(DIARY, {})

    health = build_health(seismic, geopolitics, ope, diary)
    status = geopolitics.get("status", {}) if isinstance(geopolitics, dict) else {}
    state = overall_state(status, health["overall"])
    state["confidence"] = confidence(status, health["overall"])
    current_metrics = metrics(seismic, geopolitics, ope, diary)
    previous_history = load_json(HISTORY, [])
    anomalies = detect_anomalies(current_metrics, previous_history if isinstance(previous_history, list) else [])
    snapshot = make_snapshot(state, current_metrics, health)
    history = update_history(snapshot)
    timeline, changes = build_timeline(state, current_metrics, seismic, ope, diary, anomalies)
    state["alert_level"] = alert_level_for(state)

    observatory = {
        "schema_version": 2,
        "generated_at": iso(),
        "state": state,
        "metrics": current_metrics,
        "anomalies": anomalies,
        "changes": changes,
        "health": {"overall": health["overall"], "generated_at": health["generated_at"]},
        "latest_diary": diary,
        "latest_ope": {
            "report_date": ope.get("report_date"),
            "report_label_es": ope.get("report_label_es"),
            "source": ope.get("source"),
            "source_url": ope.get("source_url"),
        },
        "methodology": {
            "principle": "Hechos, interpretación y escenarios se muestran por separado.",
            "operational_note": "El estado editorial no sustituye avisos oficiales de navegación, seguridad o protección civil.",
            "seismic_note": "La sismicidad regional no se utiliza para predecir terremotos ni para inferir un cierre del Estrecho.",
        },
        "links": {
            "status": "situacion-actual.html",
            "data": "datos.html",
            "map": "mapa-estrategico.html",
            "sources": "fuentes.html",
            "transparency": "transparencia.html",
            "corrections": "correcciones.html",
            "diary": "diario/",
        },
    }
    atomic_json(HEALTH, health)
    atomic_json(OBSERVATORY, observatory)
    FEED.write_text(build_feed(timeline), encoding="utf-8")
    print(
        f"Observatorio actualizado: {state['label_es']} · confianza {state['confidence']} · "
        f"salud {health['overall']} · {len(timeline)} eventos · {len(history)} días de histórico"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
