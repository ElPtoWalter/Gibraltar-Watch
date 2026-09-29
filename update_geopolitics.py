#!/usr/bin/env python3
"""Actualiza el monitor geopolítico de Gibraltar Watch.

- Consulta feeds RSS de Google News para temas públicos del Estrecho.
- Conserva solo titulares y enlaces; no copia artículos.
- Clasifica de forma conservadora estados editoriales.
- Mantiene el último resultado válido si falla la red.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Iterable
import html
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from straitwatch_core import (
    SourceRegistry, aggregate_events, canonical_url, normalize_title,
    title_similarity, write_json_if_changed,
)

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "geopolitics.json"
HISTORY = ROOT / "geopolitics-history.json"
SITEMAP = ROOT / "sitemap.xml"
EVENTS = ROOT / "events.json"
SOURCE_REGISTRY = SourceRegistry.from_path(ROOT / "source-registry.json")
UA = "GibraltarWatch/1.0 (+https://estrechogibraltar.com/contacto.html)"
NOW = datetime.now(timezone.utc)

QUERIES = [
    ("ceuta", "Ceuta Marruecos crisis frontera", "es", "ES", "ES:es"),
    ("melilla", "Melilla Marruecos frontera", "es", "ES", "ES:es"),
    ("relations", "España Marruecos relaciones Ceuta", "es", "ES", "ES:es"),
    ("traffic", "Estrecho de Gibraltar tráfico marítimo seguridad", "es", "ES", "ES:es"),
    ("ports", "Algeciras Tanger Med tráfico puerto", "es", "ES", "ES:es"),
    ("ceuta", "Ceuta Morocco border crisis", "en", "GB", "GB:en"),
    ("relations", "Spain Morocco relations Ceuta Melilla", "en", "GB", "GB:en"),
    ("traffic", "Strait of Gibraltar maritime traffic security", "en", "GB", "GB:en"),
]

TRUSTED = {
    "Reuters": 5, "Associated Press": 5, "AP News": 5, "EFE": 4,
    "RTVE": 4, "La Moncloa": 5, "Ministerio del Interior": 5,
    "Ministerio de Asuntos Exteriores": 5, "European Commission": 5,
    "Council of the EU": 5, "NATO": 5, "IMO": 5,
    "Salvamento Marítimo": 5, "APBA": 5, "Tanger Med": 5,
    "El País": 3, "Cadena SER": 3, "BBC": 4, "Financial Times": 4,
    "The Guardian": 3, "Politico": 3, "Euronews": 3,
}

SOURCE_ALIASES = {
    "Reuters.com": "Reuters", "Reuters": "Reuters", "AP": "Associated Press",
    "The Associated Press": "Associated Press", "Agencia EFE": "EFE",
    "EL PAÍS": "El País", "BBC News": "BBC",
    "Ministerio del Interior": "Ministerio del Interior",
    "La Moncloa": "La Moncloa", "NATO": "NATO",
}

BORDER_HIGH = re.compile(r"\b(mass|massive|thousands|50,?000|emergency|overwhelm|rush|dead|death|drown|crisis|entrada masiva|miles|emergencia|desbord|muert|ahog|avalancha)\b", re.I)
BORDER_MED = re.compile(r"\b(attempt|crossing|migrant|border|fence|swim|cruce|frontera|migrante|valla|nado|menores)\b", re.I)
BORDER_PREVENTIVE = re.compile(
    r"\b(reinforc\w*|deployment|heightened|preventive|alert|call(?:s|ing)? to cross|"
    r"refuerz\w*|despliegue|blindad\w*|preventiv\w*|alerta|llamamiento\w*|asalto)\b",
    re.I,
)
BORDER_WATCH_HOURS = 48
TENSION = re.compile(r"\b(tension|accus|critic|blame|sovereignty|claim|spat|pressure|instrumentali|tensión|acus|crític|culp|soberan|reivindic|presión|instrumentaliz)\b", re.I)
SECURITY = re.compile(r"\b(military|army|police|barrier|reinforce|security|patrol|naval|militar|ejército|polic|barrera|refuerzo|seguridad|patrulla|naval)\b", re.I)
MARITIME_DISRUPTION = re.compile(r"\b(strait.*closed|shipping.*halt|navigation.*suspend\w*|port.*clos\w*|estrecho.*cerrad\w*|tráfico.*deten\w*|navegación.*suspend\w*|puerto.*cerrad\w*)\b", re.I)
MARITIME_RESTRICT = re.compile(r"\b(restrict|delay|congestion|incident|collision|restric|retras|congest|incidente|colisión)\b", re.I)
MARITIME_POSITIVE = re.compile(
    r"\b(open to (?:shipping|navigation)|normal operations?|services? (?:remain |are )?operat\w*|"
    r"ferr(?:y|ies) (?:remain |are )?operat\w*|tr[aá]fico (?:mar[ií]timo )?normal|"
    r"servicios? (?:mar[ií]timos? )?operativos?|sin incidencias|navegaci[oó]n abierta)\b",
    re.I,
)

@dataclass(frozen=True)
class NewsItem:
    title: str
    source: str
    url: str
    published_at: str
    category: str
    language: str
    weight: int
    source_id: str = ""


def fetch(url: str, attempts: int = 3) -> bytes:
    last: Exception | None = None
    for n in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/rss+xml, application/xml, text/xml"})
            with urllib.request.urlopen(req, timeout=25) as response:
                return response.read()
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(1.2 * (n + 1))
    raise RuntimeError(f"No se pudo consultar {url}: {type(last).__name__}: {last}")


def normalise_source(source: str, title: str) -> str:
    raw = html.unescape((source or "").strip())
    if raw in SOURCE_ALIASES:
        return SOURCE_ALIASES[raw]
    if raw.casefold() in {"", "unknown source", "fuente no identificada"} and " - " in title:
        raw = title.rsplit(" - ", 1)[-1].strip()
    legacy = SOURCE_ALIASES.get(raw, raw or "Fuente no identificada")
    profile = SOURCE_REGISTRY.resolve(legacy)
    # Keep the publisher label supplied by the RSS feed when it is not yet in
    # the registry. Collapsing every unregistered outlet into "Unknown source"
    # destroys source independence and makes the factual packet unauditable.
    return profile.canonical_name if profile.source_id != "unknown" else legacy


def parse_date(value: str) -> datetime:
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return NOW


def parse_rss(payload: bytes, category: str, language: str) -> list[NewsItem]:
    root = ET.fromstring(payload)
    output: list[NewsItem] = []
    for node in root.findall(".//item"):
        title = html.unescape((node.findtext("title") or "").strip())
        link = (node.findtext("link") or "").strip()
        source_node = node.find("source")
        source = normalise_source(source_node.text if source_node is not None and source_node.text else "", title)
        if " - " in title and title.rsplit(" - ", 1)[-1].strip().lower() == source.lower():
            title = title.rsplit(" - ", 1)[0].strip()
        if not title or not link:
            continue
        dt = parse_date(node.findtext("pubDate") or "")
        profile = SOURCE_REGISTRY.resolve(source, link)
        weight = profile.tier if profile.source_id != "unknown" else TRUSTED.get(source, 2)
        publisher = profile.canonical_name if profile.source_id != "unknown" else source
        output.append(NewsItem(title, publisher, canonical_url(link), dt.isoformat(), category, language, weight, profile.source_id))
    return output


def feed_url(query: str, hl: str, gl: str, ceid: str) -> str:
    return "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": query, "hl": hl, "gl": gl, "ceid": ceid})


def dedupe(items: Iterable[NewsItem]) -> list[NewsItem]:
    out: list[NewsItem] = []
    for item in sorted(items, key=lambda x: (x.published_at, x.weight), reverse=True):
        url = canonical_url(item.url)
        key = normalize_title(item.title)
        if any(
            (url and url == canonical_url(old.url))
            or (
                item.source_id == old.source_id
                and abs((datetime.fromisoformat(item.published_at) - datetime.fromisoformat(old.published_at)).total_seconds()) <= 96 * 3600
                and title_similarity(key, old.title) >= 0.90
            )
            for old in out
        ):
            continue
        out.append(item)
    return out


def event_store_for(items: list[NewsItem], previous: dict | None = None) -> dict:
    rows = []
    for item in items:
        signal = ""
        if item.category in {"traffic", "ports"}:
            if MARITIME_DISRUPTION.search(item.title):
                signal = "CLOSURE_EFFECTIVE"
            elif MARITIME_RESTRICT.search(item.title):
                signal = "ACCESS_RESTRICTED"
            elif MARITIME_POSITIVE.search(item.title):
                signal = "OPEN_OPERATIONAL"
        row = asdict(item)
        row["signal"] = signal
        rows.append(row)
    previous_events = (previous or {}).get("events", []) if isinstance(previous, dict) else []
    return aggregate_events(rows, SOURCE_REGISTRY, previous_events, generated_at=NOW.isoformat())


def recent(items: list[NewsItem], hours: int = 96) -> list[NewsItem]:
    threshold = NOW - timedelta(hours=hours)
    out = []
    for item in items:
        try:
            dt = datetime.fromisoformat(item.published_at)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if dt >= threshold:
                out.append(item)
        except Exception:
            pass
    return out


def classify(items: list[NewsItem], previous: dict | None = None) -> dict:
    rec = recent(items)
    trusted = [i for i in rec if i.weight >= 3]
    border_high = sum(i.weight for i in trusted if i.category in {"ceuta", "melilla"} and BORDER_HIGH.search(i.title))
    border_med = sum(i.weight for i in trusted if i.category in {"ceuta", "melilla"} and BORDER_MED.search(i.title))
    tension_score = sum(i.weight for i in trusted if i.category in {"ceuta", "melilla", "relations"} and TENSION.search(i.title))
    security_score = sum(i.weight for i in trusted if SECURITY.search(i.title))
    disruption = [i for i in trusted if i.category in {"traffic", "ports"} and MARITIME_DISRUPTION.search(i.title)]
    restrictions = [i for i in trusted if i.category in {"traffic", "ports"} and MARITIME_RESTRICT.search(i.title)]
    positive = [i for i in trusted if i.category in {"traffic", "ports"} and MARITIME_POSITIVE.search(i.title)]
    positive_sources = {i.source_id or i.source for i in positive}
    disruption_sources = {i.source_id or i.source for i in disruption}
    official_positive = [i for i in positive if SOURCE_REGISTRY.resolve(i.source, i.url).official]
    official_disruption = [i for i in disruption if SOURCE_REGISTRY.resolve(i.source, i.url).official]
    preventive = [
        i for i in rec
        if i.category in {"ceuta", "melilla"}
        and i.weight >= 2
        and BORDER_PREVENTIVE.search(i.title)
    ]
    preventive_sources = {i.source for i in preventive}

    previous_payload = previous if isinstance(previous, dict) else {}
    previous_status = previous_payload.get("status") if isinstance(previous_payload.get("status"), dict) else previous_payload
    previous_watch = previous_status.get("border_watch") if isinstance(previous_status.get("border_watch"), dict) else {}
    previous_last_signal = previous_watch.get("last_signal_at") or previous_payload.get("generated_at")
    try:
        previous_last_signal_dt = datetime.fromisoformat(str(previous_last_signal).replace("Z", "+00:00"))
        if previous_last_signal_dt.tzinfo is None:
            previous_last_signal_dt = previous_last_signal_dt.replace(tzinfo=timezone.utc)
        previous_last_signal_dt = previous_last_signal_dt.astimezone(timezone.utc)
    except (TypeError, ValueError):
        previous_last_signal_dt = None
    previous_border = str((previous_status.get("border_pressure") or {}).get("es") or "").upper()
    prior_watch_active = (
        previous_last_signal_dt is not None
        and NOW - previous_last_signal_dt <= timedelta(hours=BORDER_WATCH_HOURS)
        and any(label in previous_border for label in ("ALTA", "MEDIA", "VIGILANCIA"))
    )
    current_last_signal = max(
        (datetime.fromisoformat(i.published_at).astimezone(timezone.utc) for i in preventive),
        default=None,
    )

    if official_disruption:
        maritime_es, maritime_en = "INTERRUPCIÓN CONFIRMADA", "CONFIRMED DISRUPTION"
        maritime_note_es = "Una fuente marítima oficial directa confirma una interrupción reciente."
        maritime_note_en = "A direct official maritime source confirms a recent disruption."
    elif len(disruption_sources) >= 2:
        maritime_es, maritime_en = "INTERRUPCIÓN POSIBLE", "POSSIBLE DISRUPTION"
        maritime_note_es = "Hay varias señales recientes; se requiere confirmación marítima oficial."
        maritime_note_en = "Multiple recent signals exist; official maritime confirmation is required."
    elif restrictions and (official_positive or len(positive_sources) >= 2):
        maritime_es, maritime_en = "OPERATIVO CON INCIDENCIAS", "OPERATIONAL WITH INCIDENTS"
        maritime_note_es = "La operatividad tiene respaldo positivo reciente, pero existen incidencias o congestión."
        maritime_note_en = "Recent positive evidence supports operation, but incidents or congestion are present."
    elif official_positive or len(positive_sources) >= 2:
        maritime_es, maritime_en = "OPERATIVO CONFIRMADO", "CONFIRMED OPERATIONAL"
        maritime_note_es = "Una fuente oficial directa o varias fuentes fiables independientes respaldan la operatividad reciente."
        maritime_note_en = "A direct official source or several reliable independent sources support recent operation."
    elif disruption or restrictions or positive:
        maritime_es, maritime_en = "VIGILANCIA", "WATCH"
        maritime_note_es = "Hay una señal marítima reciente, pero todavía no supera el umbral de confirmación."
        maritime_note_en = "There is a recent maritime signal, but it has not yet met the confirmation threshold."
    else:
        maritime_es, maritime_en = "SIN CONFIRMACIÓN RECIENTE", "NO RECENT CONFIRMATION"
        maritime_note_es = "No hay evidencia positiva reciente suficiente para afirmar operatividad; la ausencia de alertas no se trata como prueba."
        maritime_note_en = "There is not enough recent positive evidence to confirm operation; absence of alerts is not treated as proof."

    if border_high >= 8:
        border_es, border_en = "ALTA", "HIGH"
        border_note_es = "Varias fuentes describen una crisis fronteriza o humanitaria grave."
        border_note_en = "Several sources describe a serious border or humanitarian crisis."
    elif border_med >= 5:
        border_es, border_en = "MEDIA", "MEDIUM"
        border_note_es = "Existen intentos o presión fronteriza recientes."
        border_note_en = "Recent attempts or border pressure are being reported."
    elif len(preventive_sources) >= 2 or any(i.weight >= 4 for i in preventive):
        border_es, border_en = "VIGILANCIA PREVENTIVA", "PREVENTIVE WATCH"
        border_note_es = "Se mantienen medidas preventivas o alertas recientes; el nivel no baja todavía a normalidad."
        border_note_en = "Recent preventive measures or alerts remain in place; the level has not yet returned to normal."
    elif prior_watch_active:
        border_es, border_en = "VIGILANCIA PREVENTIVA", "PREVENTIVE WATCH"
        border_note_es = "Se conserva la vigilancia durante 48 horas desde la última señal preventiva antes de reducir el nivel."
        border_note_en = "Monitoring is retained for 48 hours after the latest preventive signal before lowering the level."
    else:
        border_es, border_en = "BAJA / SIN SEÑALES RECIENTES", "LOW / NO RECENT SIGNALS"
        border_note_es = "No aparecen señales recientes suficientes para elevar el nivel."
        border_note_en = "There are not enough recent signals to raise the level."

    watch_last_signal = current_last_signal or (previous_last_signal_dt if prior_watch_active else None)
    border_watch = {
        "last_signal_at": watch_last_signal.isoformat() if watch_last_signal else None,
        "hold_until": (watch_last_signal + timedelta(hours=BORDER_WATCH_HOURS)).isoformat() if watch_last_signal else None,
        "signal_sources": len(preventive_sources),
        "hold_hours": BORDER_WATCH_HOURS,
    }

    if tension_score >= 8:
        relation_es, relation_en = "ELEVADA", "ELEVATED"
        relation_note_es = "Las fuentes recientes muestran fricción política junto a cooperación operativa."
        relation_note_en = "Recent sources show political friction alongside operational cooperation."
    elif tension_score >= 3:
        relation_es, relation_en = "VIGILANCIA", "WATCH"
        relation_note_es = "Hay señales de fricción, sin ruptura de la cooperación."
        relation_note_en = "There are signs of friction without a breakdown in cooperation."
    else:
        relation_es, relation_en = "ESTABLE", "STABLE"
        relation_note_es = "No se detecta una escalada bilateral clara en las fuentes recientes."
        relation_note_en = "No clear bilateral escalation is detected in recent sources."

    if security_score >= 8 or border_high >= 8:
        sec_es, sec_en = "VIGILANCIA REFORZADA", "REINFORCED MONITORING"
        sec_note_es = "Las fuentes describen medidas adicionales de seguridad o control."
        sec_note_en = "Sources describe additional security or control measures."
    elif security_score >= 3:
        sec_es, sec_en = "VIGILANCIA", "MONITORING"
        sec_note_es = "Existen medidas o incidentes de seguridad recientes."
        sec_note_en = "Recent security measures or incidents are reported."
    else:
        sec_es, sec_en = "SIN ALERTA ESPECÍFICA", "NO SPECIFIC ALERT"
        sec_note_es = "No se detectan señales suficientes para una alerta editorial."
        sec_note_en = "There are not enough signals for an editorial alert."

    maritime_confirmed = maritime_es in {"OPERATIVO CONFIRMADO", "OPERATIVO CON INCIDENCIAS", "INTERRUPCIÓN CONFIRMADA"}
    confidence_es, confidence_en = (
        ("ALTA", "HIGH") if maritime_confirmed and len(trusted) >= 8
        else (("MEDIA", "MEDIUM") if maritime_confirmed or len(trusted) >= 3 else ("BAJA", "LOW"))
    )
    return {
        "maritime_status": {"es": maritime_es, "en": maritime_en},
        "maritime_note": {"es": maritime_note_es, "en": maritime_note_en},
        "border_pressure": {"es": border_es, "en": border_en},
        "border_note": {"es": border_note_es, "en": border_note_en},
        "border_watch": border_watch,
        "bilateral_tension": {"es": relation_es, "en": relation_en},
        "bilateral_note": {"es": relation_note_es, "en": relation_note_en},
        "security_status": {"es": sec_es, "en": sec_en},
        "security_note": {"es": sec_note_es, "en": sec_note_en},
        "confidence": {"es": confidence_es, "en": confidence_en},
    }


def load_json(path: Path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def update_sitemap() -> None:
    if not SITEMAP.exists():
        return
    text = SITEMAP.read_text(encoding="utf-8")
    date = NOW.date().isoformat()
    for slug in ("situacion-actual.html", "en-current-situation.html"):
        pattern = rf"(<loc>https://estrechogibraltar\.com/{re.escape(slug)}</loc>\s*<lastmod>)[^<]+"
        text = re.sub(pattern, rf"\g<1>{date}", text)
    SITEMAP.write_text(text, encoding="utf-8")


def main() -> int:
    previous = load_json(DATA, {})
    items: list[NewsItem] = []
    errors: list[str] = []
    for category, query, hl, gl, ceid in QUERIES:
        try:
            items.extend(parse_rss(fetch(feed_url(query, hl, gl, ceid)), category, hl))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{category}: {type(exc).__name__}: {exc}")
    items = dedupe(items)
    selected = [i for i in items if i.weight >= 2][:36]
    if selected:
        event_store = event_store_for(selected, load_json(EVENTS, {}))
        status = classify(selected, previous)
        payload = {
            "version": 1,
            "generated_at": NOW.isoformat(),
            "language_default": "es",
            "status": status,
            "items": [asdict(i) for i in selected],
            "errors": errors,
        }
        DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        write_json_if_changed(EVENTS, event_store)
        history = load_json(HISTORY, [])
        signature = json.dumps(status, sort_keys=True, ensure_ascii=False)
        old_signature = json.dumps(history[-1].get("status", {}), sort_keys=True, ensure_ascii=False) if history else ""
        if signature != old_signature:
            history.append({"at": NOW.isoformat(), "status": status})
            history = history[-180:]
            HISTORY.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
        update_sitemap()
        print(f"Monitor geopolítico actualizado con {len(selected)} titulares; {len(errors)} errores parciales.")
        return 0

    if previous:
        previous["errors"] = errors or ["No se obtuvieron titulares nuevos"]
        previous["last_failed_check"] = NOW.isoformat()
        DATA.write_text(json.dumps(previous, ensure_ascii=False, indent=2), encoding="utf-8")
        print("No hubo datos nuevos; se conserva el último resultado válido.")
        return 0
    raise RuntimeError("No se obtuvieron titulares y no existe un resultado previo")


if __name__ == "__main__":
    raise SystemExit(main())
