#!/usr/bin/env python3
"""Diario del Estrecho · cuaderno editorial de Gibraltar Watch.

Principios:
- Nunca publica sin una base factual local (geopolitics.json).
- Distingue artículo completo de parte breve según la relevancia real de la jornada.
- La edición ordinaria se redacta con un motor editorial local y reproducible.
- La publicación no depende de APIs, cuotas ni servicios de pago.
- Evita páginas SEO vacías: los partes sin fuentes recientes se publican para la
  hemeroteca, pero se marcan noindex y no entran en el sitemap.
- La portada se actualiza de forma estática; no necesita JSON público ni JavaScript.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from html import escape
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
import hashlib
import json
import os
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
TZ = ZoneInfo("Europe/Madrid")
NOW_UTC = datetime.now(timezone.utc)
NOW = NOW_UTC.astimezone(TZ)

GEOPOLITICS = ROOT / "geopolitics.json"
OPE = ROOT / "ope-2026.json"
STATE_DATA = ROOT / ".github" / "diario-state.json"
LEGACY_STATE_DATA = ROOT / "diario-index.json"
LEGACY_LATEST_DATA = ROOT / "diario-latest.json"
LEGACY_DIARIO_JS = ROOT / "diario.js"
ARCHIVE_DIR = ROOT / "diario"
ARCHIVE_PAGE = ARCHIVE_DIR / "index.html"
LEGACY_ARCHIVE_PAGE = ROOT / "diario.html"
RSS = ROOT / "diario-feed.xml"
SITEMAP = ROOT / "sitemap.xml"
HOME = ROOT / "index.html"

MIN_HOUR_LOCAL = 7
MAX_ITEMS = 9
MAX_PER_CATEGORY = 3
MAX_PER_DOMAIN = 2
AI_MODEL = os.getenv("DIARIO_AI_MODEL", "gpt-5.6-terra").strip() or "gpt-5.6-terra"
# El modelo remoto queda como compatibilidad manual, nunca como dependencia del diario.
AI_ENABLED = os.getenv("DIARIO_AI_OPT_IN", "0") == "1" and bool(os.getenv("OPENAI_API_KEY", "").strip())
EDITORIAL_VERSION = "cuaderno-1"

HOME_START = "<!-- GW_DIARIO_HOME_START -->"
HOME_END = "<!-- GW_DIARIO_HOME_END -->"
NAV_START = "<!-- GD_DAY_NAV_START -->"
NAV_END = "<!-- GD_DAY_NAV_END -->"

CATEGORY_LABELS = {
    "traffic": "Tráfico marítimo",
    "ports": "Puertos y logística",
    "ceuta": "Ceuta y Melilla",
    "melilla": "Ceuta y Melilla",
    "relations": "España–Marruecos",
    "security": "Seguridad y defensa",
    "defence": "Seguridad y defensa",
    "defense": "Seguridad y defensa",
    "economy": "Economía y comercio",
    "energy": "Energía y logística",
    "tunnel": "Infraestructuras",
    "ope": "Operación Paso del Estrecho",
}

CATEGORY_BONUS = {
    "traffic": 5,
    "ports": 5,
    "ceuta": 5,
    "melilla": 5,
    "relations": 5,
    "security": 6,
    "defence": 6,
    "defense": 6,
    "tunnel": 4,
    "ope": 4,
    "economy": 3,
    "energy": 4,
}

HIGH_ALERT_WORDS = (
    "INTERRUMP", "CIERRE", "CERRAD", "INCIDEN", "EMERGEN", "ALTA", "ELEVAD",
    "CRITIC", "CRÍTIC", "TENSIÓN", "TENSION", "VIGILANCIA", "RESTRING",
)
NORMAL_WORDS = ("OPERATIVO", "NORMAL", "ESTABLE", "BAJA", "SIN INCIDEN")

EDITION_IDENTITIES = {
    "traffic": ("Cuaderno de navegación", "navigation"),
    "ports": ("Cuaderno portuario", "ports"),
    "ceuta": ("Cuaderno de las dos orillas", "shores"),
    "melilla": ("Cuaderno de las dos orillas", "shores"),
    "relations": ("Cuaderno diplomático", "relations"),
    "security": ("Cuaderno estratégico", "security"),
    "defence": ("Cuaderno estratégico", "security"),
    "defense": ("Cuaderno estratégico", "security"),
    "economy": ("Cuaderno económico", "economy"),
    "energy": ("Cuaderno económico", "economy"),
    "tunnel": ("Cuaderno de infraestructuras", "infrastructure"),
    "ope": ("Cuaderno de movilidad", "mobility"),
    "other": ("Cuaderno del Estrecho", "general"),
}


def load_json(path: Path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def parse_dt(value: str, fallback: datetime | None = None) -> datetime:
    try:
        text = str(value or "").strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return fallback or NOW_UTC


def status_text(status: dict, key: str, lang: str = "es", fallback: str = "SIN DATOS") -> str:
    value = status.get(key, fallback)
    if isinstance(value, dict):
        return str(value.get(lang, value.get("es", fallback)))
    return str(value)


def normalized_title(value: str) -> str:
    return re.sub(r"[^a-z0-9áéíóúüñ]+", " ", str(value).lower(), flags=re.I).strip()


def valid_http_url(value: str) -> bool:
    try:
        p = urlparse(str(value))
        return p.scheme in {"http", "https"} and bool(p.netloc)
    except Exception:
        return False


def item_domain(item: dict) -> str:
    try:
        return urlparse(str(item.get("url", ""))).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def item_score(item: dict) -> float:
    published = parse_dt(str(item.get("published_at", "")))
    hours = max(0.0, (NOW_UTC - published).total_seconds() / 3600)
    recency = max(0.0, 7.0 - hours / 5.0)
    try:
        weight = float(item.get("weight", 2))
    except Exception:
        weight = 2.0
    category = str(item.get("category", "other")).lower()
    return weight * 2.3 + CATEGORY_BONUS.get(category, 1) + recency


def select_items(items: list[dict], hours: int = 36) -> list[dict]:
    """Selecciona señales recientes, diversas y con URL trazable."""
    threshold = NOW_UTC - timedelta(hours=hours)
    candidates: list[dict] = []
    for raw in items or []:
        if not isinstance(raw, dict):
            continue
        title = str(raw.get("title", "")).strip()
        url = str(raw.get("url", "")).strip()
        if len(title) < 8 or not valid_http_url(url):
            continue
        if parse_dt(str(raw.get("published_at", ""))) < threshold:
            continue
        candidates.append(raw)

    candidates.sort(key=item_score, reverse=True)
    picked: list[dict] = []
    per_cat: Counter[str] = Counter()
    per_domain: Counter[str] = Counter()
    seen_titles: set[str] = set()

    for item in candidates:
        cat = str(item.get("category", "other")).lower()
        domain = item_domain(item) or str(item.get("source", "desconocida")).lower()
        key = normalized_title(str(item.get("title", "")))
        if not key or key in seen_titles:
            continue
        # Dedupe blando: evita titulares prácticamente idénticos.
        if any(key in old or old in key for old in seen_titles if min(len(key), len(old)) >= 28):
            continue
        if per_cat[cat] >= MAX_PER_CATEGORY or per_domain[domain] >= MAX_PER_DOMAIN:
            continue
        seen_titles.add(key)
        per_cat[cat] += 1
        per_domain[domain] += 1
        picked.append(item)
        if len(picked) >= MAX_ITEMS:
            break
    return picked


def stable_pick(options: tuple[str, ...], seed: str) -> str:
    """Elige una variante estable para que una misma edición no cambie en cada ejecución."""
    if not options:
        return ""
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    return options[int.from_bytes(digest[:2], "big") % len(options)]


def dominant_category(selected: list[dict]) -> str:
    if not selected:
        return "other"
    weighted: Counter[str] = Counter()
    for item in selected:
        category = str(item.get("category", "other")).lower()
        weighted[category] += max(1, round(item_score(item)))
    return weighted.most_common(1)[0][0]


def source_geography(item: dict) -> str:
    haystack = " ".join(
        (str(item.get("title", "")), str(item.get("source", "")), item_domain(item))
    ).lower()
    if any(word in haystack for word in ("gibraltar", "gibchronicle", "the rock")):
        return "Gibraltar"
    if any(word in haystack for word in ("marruecos", "morocco", "maroc", "tánger", "tanger", "tangier", "tetuán", "tetouan")):
        return "orilla sur"
    if any(word in haystack for word in ("españa", "spain", "algeciras", "tarifa", "cádiz", "cadiz", "ceuta", "melilla")):
        return "orilla norte"
    return "ámbito regional"


def editorial_profile(date: str, selected: list[dict], entries: list[dict]) -> dict:
    """Construye la identidad visual y el pulso propio de la edición sin inferir hechos."""
    category = dominant_category(selected)
    label, slug = EDITION_IDENTITIES.get(category, EDITION_IDENTITIES["other"])
    recent = [e for e in entries if e.get("date") != date and isinstance(e.get("source_count"), int)][:7]
    average = sum(e["source_count"] for e in recent) / len(recent) if recent else 0.0
    current = len(selected)
    if not recent:
        pulse = "Primera referencia comparable"
    elif current >= average + 1.5:
        pulse = "Agenda más cargada que la última semana"
    elif current <= max(0, average - 1.5):
        pulse = "Agenda más ligera que la última semana"
    else:
        pulse = "Agenda en línea con la última semana"

    geographies = list(dict.fromkeys(source_geography(item) for item in selected))
    domains = {item_domain(item) or str(item.get("source", "")).lower() for item in selected}
    topic = CATEGORY_LABELS.get(category, "Actualidad regional")
    signal = selected[0] if selected else None
    if not selected:
        limitation = "No hay señales recientes suficientes para afirmar un cambio de tendencia. La edición conserva únicamente la lectura operativa disponible."
    elif len(domains) < 2:
        limitation = "La señal principal no cuenta todavía con contraste entre dominios independientes; se mantiene como pista informativa, no como cambio confirmado."
    elif not any(str(item.get("category", "")).lower() in {"traffic", "ports"} for item in selected):
        limitation = "Esta edición no incorpora una señal marítima nueva suficiente para modificar por sí sola la lectura del tráfico."
    else:
        limitation = "Los titulares describen la agenda informativa; por sí solos no prueban variaciones de tráfico, capacidad portuaria o riesgo operativo."

    return {
        "label": label,
        "slug": slug,
        "topic": topic,
        "source_count": current,
        "recent_average": average,
        "pulse": pulse,
        "geographies": geographies,
        "domain_count": len(domains),
        "signal": signal,
        "limitation": limitation,
    }


def editorial_dashboard_html(profile: dict) -> str:
    signal = profile.get("signal")
    if signal:
        signal_html = (
            f'<a href="{escape(safe_external_url(str(signal.get("url", "#"))), quote=True)}" target="_blank" '
            f'rel="noopener noreferrer nofollow"><strong>{escape(clean_text(signal.get("title", ""), 300))}</strong>'
            f'<span>{escape(clean_text(signal.get("source", "Fuente"), 100))} · abrir fuente ↗</span></a>'
        )
    else:
        signal_html = '<strong>Sin una señal nueva dominante</strong><span>La continuidad también forma parte del registro.</span>'
    average = profile.get("recent_average", 0.0)
    average_text = f"{average:.1f}" if average else "—"
    geography = ", ".join(profile.get("geographies") or []) or "sin mapa informativo nuevo"
    return f'''<section class="gd-dashboard" aria-label="Mesa de edición">
<article class="gd-signal"><p class="gd-kicker">LA SEÑAL DEL DÍA</p>{signal_html}</article>
<article><p class="gd-kicker">PULSO DEL ARCHIVO</p><strong>{profile.get('source_count', 0)} señales</strong><span>Media de 7 ediciones: {average_text} · {escape(str(profile.get('pulse', '')))}</span></article>
<article><p class="gd-kicker">MAPA DE LA AGENDA</p><strong>{escape(str(profile.get('topic', 'Actualidad regional')))}</strong><span>{escape(geography)} · {profile.get('domain_count', 0)} dominios</span></article>
</section>'''


def alert_score(status: dict) -> int:
    fields = (
        "maritime_status", "security_status", "border_pressure", "bilateral_tension",
        "maritime_note", "security_note", "border_note", "bilateral_note",
    )
    text = " ".join(status_text(status, k, fallback="") for k in fields).upper()
    score = sum(4 for word in HIGH_ALERT_WORDS if word in text)
    return min(score, 12)


def edition_significance(status: dict, selected: list[dict]) -> tuple[int, list[str]]:
    """Devuelve puntuación 0-100 y razones auditables para decidir FULL vs BRIEF."""
    reasons: list[str] = []
    if not selected:
        base = 0
    else:
        scores = sorted((item_score(i) for i in selected), reverse=True)
        base = min(45, int(sum(scores[:4]) * 0.75))
        categories = {str(i.get("category", "other")).lower() for i in selected}
        if len(categories) >= 3:
            base += 10
            reasons.append("actualidad repartida en tres o más ámbitos")
        if len(selected) >= 5:
            base += 8
            reasons.append("volumen informativo relevante")
        high_weight = []
        for i in selected:
            try:
                if float(i.get("weight", 0)) >= 5:
                    high_weight.append(i)
            except Exception:
                pass
        if high_weight:
            base += min(20, 7 * len(high_weight))
            reasons.append("al menos una señal de prioridad alta")

    a = alert_score(status)
    if a:
        base += a * 2
        reasons.append("indicadores operativos o geopolíticos fuera de la normalidad")

    score = max(0, min(100, base))
    if not reasons and selected:
        reasons.append("novedades recientes sin cambio estructural")
    if not selected:
        reasons.append("sin señales recientes suficientes")
    return score, reasons


def edition_mode(status: dict, selected: list[dict]) -> str:
    score, _ = edition_significance(status, selected)
    return "full" if score >= 46 else "brief"


def seo_indexable(mode: str, status: dict, selected: list[dict]) -> bool:
    # Un artículo completo siempre aporta suficiente entidad. Un parte sin fuentes
    # nuevas se conserva para lectores recurrentes, pero no se empuja a Google.
    return mode == "full" or bool(selected) or alert_score(status) > 0


def fallback_headline(status: dict, selected: list[dict], mode: str) -> str:
    maritime = status_text(status, "maritime_status", fallback="OPERATIVO").upper()
    border = status_text(status, "border_pressure", fallback="SIN DATOS").upper()
    bilateral = status_text(status, "bilateral_tension", fallback="ESTABLE").upper()
    cats = Counter(CATEGORY_LABELS.get(str(i.get("category", "")).lower(), "Otros") for i in selected)
    dominant = cats.most_common(1)[0][0] if cats else ""

    if any(w in maritime for w in ("INTERRUMP", "CIERRE", "INCIDEN", "RESTRING")):
        return "El tráfico marítimo centra una jornada de vigilancia en el Estrecho"
    if any(w in border for w in ("ALTA", "ELEVAD", "CRÍTIC", "CRITIC")):
        return "Ceuta y la presión fronteriza concentran la atención de la jornada"
    if any(w in bilateral for w in ("ELEVAD", "TENS", "VIGILANCIA")):
        return "España y Marruecos marcan el pulso político del Estrecho"
    if dominant == "Tráfico marítimo" or dominant == "Puertos y logística":
        return stable_pick((
            "Tráfico, puertos y logística marcan la jornada del Estrecho",
            "El pulso portuario coloca la navegación en el centro de la jornada",
            "La agenda del Estrecho se mueve hoy entre tráfico y actividad portuaria",
        ), NOW.date().isoformat() + dominant)
    if dominant == "Ceuta y Melilla":
        return "Ceuta y Melilla concentran la actualidad del Estrecho"
    if mode == "brief":
        return stable_pick((
            "Parte del Estrecho: continuidad y vigilancia de las señales clave",
            "Una jornada de continuidad, contada sin forzar novedades",
            "El Estrecho mantiene el rumbo mientras la agenda informativa se modera",
        ), NOW.date().isoformat() + maritime + border)
    return stable_pick((
        "El Estrecho cruza tráfico, economía y geopolítica en una jornada activa",
        "Una jornada de varias capas en el corredor entre el Atlántico y el Mediterráneo",
        "Puertos, fronteras y diplomacia componen el mapa del día en el Estrecho",
    ), NOW.date().isoformat() + dominant)


def fallback_deck(status: dict, selected: list[dict], mode: str) -> str:
    maritime = status_text(status, "maritime_status", fallback="sin lectura").lower()
    border = status_text(status, "border_pressure", fallback="sin lectura").lower()
    bilateral = status_text(status, "bilateral_tension", fallback="sin lectura").lower()
    if selected:
        return (
            f"El corredor figura como {maritime}; la presión fronteriza, {border}; y la relación España–Marruecos, "
            f"{bilateral}. La edición contrasta {len(selected)} señales recientes antes de extraer conclusiones."
        )
    return (
        f"El corredor figura como {maritime}, con presión fronteriza {border} y relación bilateral {bilateral}. "
        "No aparecen suficientes novedades recientes como para convertir la jornada en un artículo largo."
    )


def fallback_situation(status: dict, selected: list[dict], mode: str) -> list[str]:
    maritime = status_text(status, "maritime_status", fallback="SIN DATOS").lower()
    security = status_text(status, "security_status", fallback="SIN DATOS").lower()
    confidence = status_text(status, "confidence", fallback="BAJA").lower()
    counts = Counter(CATEGORY_LABELS.get(str(i.get("category", "")).lower(), "Otros") for i in selected)
    focus = ", ".join(label.lower() for label, _ in counts.most_common(3)) or "la situación general del corredor"

    p1 = (
        f"La fotografía operativa de esta edición sitúa el tráfico marítimo en {maritime} y el indicador de seguridad en "
        f"{security}. La selección de las últimas horas se concentra en {focus}."
    )
    p2 = (
        f"La confianza de la síntesis es {confidence}. Gibraltar Watch separa el estado operativo de los titulares: una "
        "noticia aislada se trata como señal informativa hasta que avisos oficiales, datos portuarios o varias fuentes "
        "permiten elevar su importancia."
    )
    if mode == "brief":
        return [p1, p2]
    p3 = (
        "El valor de la jornada está en la combinación de capas. El Estrecho no es solo navegación: Algeciras, Tánger Med "
        "y Gibraltar compiten y cooperan en logística; Ceuta y Melilla añaden la dimensión fronteriza; y la relación entre "
        "España y Marruecos condiciona el contexto político sin determinar por sí sola el funcionamiento del corredor."
    )
    return [p1, p2, p3]


def fallback_section_text(section: str, status: dict, items: list[dict]) -> str:
    if section in {"Tráfico marítimo", "Puertos y logística", "Economía y comercio", "Energía y logística"}:
        maritime = status_text(status, "maritime_status", fallback="SIN DATOS")
        note = status_text(status, "maritime_note", fallback="Los avisos oficiales prevalecen sobre cualquier lectura editorial.")
        return f"El indicador marítimo permanece en {maritime}. {note} Esta sección reúne {len(items)} señales con impacto potencial sobre los flujos del corredor."
    if section == "Ceuta y Melilla":
        level = status_text(status, "border_pressure", fallback="SIN DATOS")
        note = status_text(status, "border_note", fallback="Sin lectura suficiente para elevar el nivel.")
        return f"La presión fronteriza se sitúa en {level}. {note} La edición se limita a hechos publicados y evita atribuir intenciones no demostradas."
    if section == "España–Marruecos":
        level = status_text(status, "bilateral_tension", fallback="SIN DATOS")
        note = status_text(status, "bilateral_note", fallback="Sin cambio bilateral confirmado.")
        return f"La relación bilateral figura en {level}. {note} Cooperación y fricción pueden coexistir, por lo que cada episodio se interpreta dentro de una serie y no como ruptura automática."
    if section == "Seguridad y defensa":
        level = status_text(status, "security_status", fallback="SIN DATOS")
        return f"El indicador de seguridad se sitúa en {level}. Las novedades se presentan con prudencia y sin convertir actividad militar o policial rutinaria en una crisis por defecto."
    return "Las señales de esta sección se incorporan por su relación directa con la capacidad, la economía o el equilibrio estratégico del Estrecho."


def fallback_meaning(status: dict, selected: list[dict], mode: str) -> list[str]:
    maritime = status_text(status, "maritime_status", fallback="SIN DATOS").lower()
    border = status_text(status, "border_pressure", fallback="SIN DATOS").lower()
    bilateral = status_text(status, "bilateral_tension", fallback="SIN DATOS").lower()
    p1 = (
        f"La combinación de tráfico {maritime}, presión fronteriza {border} y relación bilateral {bilateral} obliga a leer "
        "el Estrecho como un sistema. Un cambio en una capa puede aumentar el riesgo o el coste en otra, pero no equivale "
        "automáticamente a un cambio del estado general del corredor."
    )
    if mode == "brief":
        return [p1]
    p2 = (
        "Para el seguimiento diario, lo decisivo es distinguir ruido de tendencia: incidencias repetidas, decisiones oficiales, "
        "cambios de capacidad portuaria y movimientos diplomáticos sostenidos pesan más que un único titular llamativo. Esa es "
        "la referencia que se utiliza para decidir qué merece seguimiento al día siguiente."
    )
    return [p1, p2]


def fallback_watch(status: dict, selected: list[dict]) -> list[str]:
    bullets = [
        "Avisos oficiales que alteren el tráfico, la navegación o los servicios portuarios.",
        "Medidas operativas nuevas en Ceuta, Melilla o los pasos fronterizos.",
        "Comunicados de España o Marruecos que modifiquen de forma verificable el tono bilateral.",
    ]
    if any(str(i.get("category", "")).lower() in {"ports", "traffic", "energy", "economy"} for i in selected):
        bullets.append("Cambios de capacidad, rutas o incidencias en Algeciras, Tánger Med y Gibraltar.")
    return bullets[:4]


def groups_for_items(selected: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for item in selected:
        label = CATEGORY_LABELS.get(str(item.get("category", "")).lower(), "Otras señales")
        groups[label].append(item)
    return groups


def source_payload(selected: list[dict]) -> list[dict]:
    out = []
    for i, item in enumerate(selected, 1):
        out.append({
            "id": i,
            "title": str(item.get("title", ""))[:240],
            "source": str(item.get("source", "Fuente"))[:120],
            "category": CATEGORY_LABELS.get(str(item.get("category", "")).lower(), "Otras señales"),
            "published_at": str(item.get("published_at", "")),
            "weight": item.get("weight", 2),
            "url": str(item.get("url", "")),
        })
    return out


def ai_editorial_draft(status: dict, selected: list[dict], mode: str) -> dict | None:
    """Una sola llamada opcional. Devuelve None ante cualquier problema."""
    if not AI_ENABLED:
        return None
    try:
        from openai import OpenAI
        from pydantic import BaseModel, Field

        class SectionDraft(BaseModel):
            title: str
            paragraph: str

        class DiaryDraft(BaseModel):
            headline: str = Field(min_length=20, max_length=150)
            deck: str = Field(min_length=50, max_length=420)
            situation: list[str]
            sections: list[SectionDraft]
            meaning: list[str]
            watch: list[str]

        score, reasons = edition_significance(status, selected)
        facts = {
            "edition_mode": mode,
            "significance_score": score,
            "significance_reasons": reasons,
            "status": status,
            "sources": source_payload(selected),
        }
        length_rule = (
            "Escribe una pieza periodística de aproximadamente 650-950 palabras en total. Usa 3-5 párrafos en situation, "
            "1 párrafo contextual por cada sección con fuentes, 2-3 párrafos en meaning y 2-4 puntos en watch."
            if mode == "full" else
            "Escribe un parte breve de aproximadamente 170-300 palabras en total. Usa 2 párrafos en situation, como máximo "
            "1 párrafo por sección imprescindible, 1 párrafo en meaning y 2-3 puntos en watch."
        )
        instructions = (
            "Eres el equipo editorial de Gibraltar Watch. Redacta en español de España con tono de periodista especializado: "
            "sobrio, claro, narrativo y preciso. NO navegues, NO uses conocimiento externo y NO añadas hechos, cifras, nombres, "
            "causas, fechas o consecuencias que no estén en el JSON suministrado. Los titulares de las fuentes son pistas, no hechos "
            "confirmados por sí solos: atribuye cuando corresponda y evita convertir una noticia en un cambio operativo sin respaldo del status. "
            "Parafrasea; no copies frases largas de las fuentes. Separa hechos de interpretación. No menciones IA, modelos, prompts ni automatización. "
            "No uses lenguaje sensacionalista. Si faltan datos, dilo de forma natural. 'Qué significa' debe aportar contexto causal prudente, no repetir titulares. "
            "En sections usa únicamente títulos de categoría presentes en sources y omite categorías sin material. " + length_rule
        )
        client = OpenAI()
        response = client.responses.parse(
            model=AI_MODEL,
            instructions=instructions,
            input=json.dumps(facts, ensure_ascii=False),
            text_format=DiaryDraft,
        )
        parsed = response.output_parsed
        if not parsed:
            return None
        data = parsed.model_dump()
        if len(data.get("situation", [])) < 1 or len(data.get("meaning", [])) < 1:
            return None
        return data
    except Exception as exc:
        print(f"Diario: redacción IA no disponible ({type(exc).__name__}: {exc}). Se usa fallback local.")
        return None


def build_draft(status: dict, selected: list[dict], mode: str) -> tuple[dict, str]:
    ai = ai_editorial_draft(status, selected, mode)
    if ai:
        # Limita las secciones a categorías realmente presentes.
        allowed = set(groups_for_items(selected))
        ai["sections"] = [s for s in ai.get("sections", []) if str(s.get("title", "")) in allowed]
        ai["watch"] = ai.get("watch", [])[:4]
        return ai, "model"

    groups = groups_for_items(selected)
    return {
        "headline": fallback_headline(status, selected, mode),
        "deck": fallback_deck(status, selected, mode),
        "situation": fallback_situation(status, selected, mode),
        "sections": [
            {"title": section, "paragraph": fallback_section_text(section, status, items)}
            for section, items in groups.items()
        ],
        "meaning": fallback_meaning(status, selected, mode),
        "watch": fallback_watch(status, selected),
    }, "rules"


def clean_text(value: object, max_chars: int = 2400) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text[:max_chars]


def safe_external_url(value: str) -> str:
    return value if valid_http_url(value) else "#"


def source_items_html(selected: list[dict]) -> str:
    if not selected:
        return '<p class="gd-empty">No hubo suficientes novedades recientes para una lista de fuentes de la jornada.</p>'
    lis = []
    for item in selected:
        title = escape(clean_text(item.get("title", "Sin título"), 320))
        source = escape(clean_text(item.get("source", "Fuente"), 120))
        url = escape(safe_external_url(str(item.get("url", "#"))), quote=True)
        published = parse_dt(str(item.get("published_at", ""))).astimezone(TZ).strftime("%d %b · %H:%M")
        lis.append(
            f'<li><a href="{url}" target="_blank" rel="noopener noreferrer nofollow">{title}</a>'
            f'<span>{source} · {escape(published)}</span></li>'
        )
    return '<ol class="gd-sources">' + "".join(lis) + "</ol>"


def sections_html(draft: dict, selected: list[dict]) -> str:
    groups = groups_for_items(selected)
    prose_by_title = {clean_text(s.get("title")): clean_text(s.get("paragraph"), 1800) for s in draft.get("sections", []) if isinstance(s, dict)}
    chunks: list[str] = []
    for section, items in groups.items():
        paragraph = prose_by_title.get(section, "")
        cards = []
        for item in items:
            cards.append(
                '<article class="gd-news-card">'
                f'<small>{escape(clean_text(item.get("source", "Fuente"), 100))}</small>'
                f'<h3>{escape(clean_text(item.get("title", ""), 300))}</h3>'
                f'<a href="{escape(safe_external_url(str(item.get("url", "#"))), quote=True)}" target="_blank" rel="noopener noreferrer nofollow">Abrir fuente original ↗</a>'
                '</article>'
            )
        chunks.append(
            f'<section class="gd-section"><p class="gd-kicker">{escape(section.upper())}</p><h2>{escape(section)}</h2>'
            f'<p>{escape(paragraph)}</p><div class="gd-news-grid">{"".join(cards)}</div></section>'
        )
    return "".join(chunks)


def words_in_draft(draft: dict) -> int:
    parts = [draft.get("headline", ""), draft.get("deck", "")]
    parts.extend(draft.get("situation", []))
    parts.extend(draft.get("meaning", []))
    parts.extend(draft.get("watch", []))
    parts.extend(s.get("paragraph", "") for s in draft.get("sections", []) if isinstance(s, dict))
    return len(re.findall(r"\b\w+[\wáéíóúüñ-]*\b", " ".join(map(str, parts)), flags=re.I))


def day_nav_html(date: str, entries: list[dict]) -> str:
    entries_sorted = sorted(entries, key=lambda e: e.get("date", ""))
    idx = next((i for i, e in enumerate(entries_sorted) if e.get("date") == date), None)
    prev_entry = entries_sorted[idx - 1] if idx is not None and idx > 0 else None
    next_entry = entries_sorted[idx + 1] if idx is not None and idx + 1 < len(entries_sorted) else None
    prev_html = f'<a rel="prev" href="/{escape(prev_entry["url"], quote=True)}">← {escape(prev_entry["date"])}</a>' if prev_entry else '<span></span>'
    next_html = f'<a rel="next" href="/{escape(next_entry["url"], quote=True)}">{escape(next_entry["date"])} →</a>' if next_entry else '<span></span>'
    return f'{NAV_START}<nav class="gd-day-nav" aria-label="Navegación entre ediciones">{prev_html}<a href="/diario/">Archivo completo</a>{next_html}</nav>{NAV_END}'


def article_html(date: str, published_at: str, updated_at: str, status: dict, selected: list[dict], fingerprint: str,
                 draft: dict, mode: str, indexable: bool, entries: list[dict], editor_engine: str) -> str:
    h = clean_text(draft.get("headline"), 180) or fallback_headline(status, selected, mode)
    deck = clean_text(draft.get("deck"), 500) or fallback_deck(status, selected, mode)
    situation = "".join(f"<p>{escape(clean_text(p, 2600))}</p>" for p in draft.get("situation", []) if clean_text(p))
    meaning = "".join(f"<p>{escape(clean_text(p, 2600))}</p>" for p in draft.get("meaning", []) if clean_text(p))
    watch = "".join(f"<li>{escape(clean_text(x, 420))}</li>" for x in draft.get("watch", []) if clean_text(x))
    pretty_date = datetime.fromisoformat(date).strftime("%d · %m · %Y")
    canonical = f"https://estrechogibraltar.com/diario/{date}.html"
    robots = "index,follow,max-image-preview:large" if indexable else "noindex,follow"
    type_label = "ARTÍCULO DE JORNADA" if mode == "full" else "PARTE BREVE"
    schema_type = "NewsArticle" if mode == "full" else "Article"
    section = "Estrecho de Gibraltar"
    keywords = "Estrecho de Gibraltar, Algeciras, Tánger Med, Gibraltar, Ceuta, Melilla, España Marruecos, tráfico marítimo"
    desc = deck[:160]
    nav = day_nav_html(date, entries)
    word_count = words_in_draft(draft)
    source_count = len(selected)
    profile = editorial_profile(date, selected, entries)
    dashboard = editorial_dashboard_html(profile)

    return f'''<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(h)} | Diario del Estrecho</title>
<meta name="description" content="{escape(desc, quote=True)}"><meta name="robots" content="{robots}">
<link rel="canonical" href="{canonical}"><link rel="alternate" type="application/rss+xml" title="Diario del Estrecho" href="https://estrechogibraltar.com/diario-feed.xml">
<meta property="og:type" content="article"><meta property="og:site_name" content="Gibraltar Watch"><meta property="og:title" content="{escape(h, quote=True)}"><meta property="og:description" content="{escape(desc, quote=True)}"><meta property="og:url" content="{canonical}"><meta property="og:image" content="https://estrechogibraltar.com/social-card.png">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{escape(h, quote=True)}"><meta name="twitter:description" content="{escape(desc, quote=True)}"><meta name="twitter:image" content="https://estrechogibraltar.com/social-card.png">
<meta name="theme-color" content="#f3efe5">
<link rel="stylesheet" href="/styles.css?v=editorial-20260714-contact-1"><link rel="stylesheet" href="/gibraltar-consolidated.css?v=20260803-1"><link rel="stylesheet" href="/gibraltar-layout-polish.css?v=20260829-1"><link rel="stylesheet" href="/diario.css?v=20260831-4">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1713078636060241" crossorigin="anonymous"></script>
<script type="application/ld+json">{json.dumps({"@context":"https://schema.org","@type":schema_type,"headline":h,"description":desc,"datePublished":published_at,"dateModified":updated_at,"inLanguage":"es","articleSection":section,"keywords":keywords,"isAccessibleForFree":True,"wordCount":word_count,"author":{"@type":"Organization","name":"Equipo editorial de Gibraltar Watch"},"publisher":{"@type":"Organization","name":"Gibraltar Watch"},"mainEntityOfPage":canonical}, ensure_ascii=False)}</script>
</head><body class="gd-page gd-page--{escape(str(profile['slug']))}"><div class="site-shell"><header class="gd-top"><a href="/" class="gd-brand"><b>GIBRALTAR</b><span>WATCH</span></a><nav><a href="/">Inicio</a><a href="/situacion-actual.html">Situación actual</a><a href="/trafico.html">Tráfico</a><a href="/diario/" aria-current="page">Diario</a><a href="/fuentes.html">Fuentes</a></nav></header>
<main class="gd-shell"><article>
<header class="gd-hero"><p class="gd-kicker">{escape(str(profile['label']).upper())} · {pretty_date}</p><div class="gd-edition-row"><span class="gd-edition-type">{type_label}</span><span>{source_count} fuentes recientes · {word_count} palabras</span></div><h1>{escape(h)}</h1><p class="gd-deck">{escape(deck)}</p><div class="gd-meta"><span>Publicado {escape(published_at[11:16])}</span><span>Actualizado {escape(updated_at[11:16])}</span><span>Equipo editorial de Gibraltar Watch</span></div></header>
{dashboard}
<section class="gd-summary"><p class="gd-kicker">LA JORNADA EN UNA FRASE</p><strong>{escape(deck)}</strong></section>
<section class="gd-prose"><p class="gd-kicker">LA SITUACIÓN</p><h2>{'Qué deja la jornada' if mode == 'full' else 'Parte de situación'}</h2>{situation}</section>
{sections_html(draft, selected)}
<section class="gd-prose gd-meaning"><p class="gd-kicker">QUÉ SIGNIFICA</p><h2>La lectura del Estrecho</h2>{meaning}</section>
<aside class="gd-limit"><p class="gd-kicker">EL LÍMITE DE LA LECTURA</p><h2>Lo que hoy no puede afirmarse</h2><p>{escape(str(profile['limitation']))}</p></aside>
<section class="gd-watch"><p class="gd-kicker">QUÉ VIGILAMOS</p><h2>Las próximas horas</h2><ul>{watch}</ul></section>
<section class="gd-source-section"><p class="gd-kicker">FUENTES DE ESTA EDICIÓN</p><h2>Trazabilidad</h2><p>La edición se construye a partir de fuentes públicas seleccionadas por Gibraltar Watch. Los enlaces originales permiten comprobar cada señal; un titular aislado no se convierte por sí solo en un cambio del estado operativo.</p>{source_items_html(selected)}</section>
<section class="gd-transparency"><p class="gd-kicker">SOBRE ESTE DIARIO</p><p>El Equipo editorial de Gibraltar Watch aplica un protocolo estable para seleccionar, ordenar y contrastar fuentes públicas. Cada edición distingue hechos, interpretación y límites de la evidencia, y puede corregirse si aparece una fuente primaria mejor o cambia la lectura operativa.</p></section>
{nav}
<footer class="gd-article-footer"><p><strong>Gibraltar Watch</strong> · Hechos, interpretación y escenarios se presentan por separado.</p><a href="/diario/">Volver a la hemeroteca</a><a href="/contacto.html">Enviar corrección</a></footer>
</article></main><footer class="gd-site-footer"><a href="/privacidad.html">Privacidad</a><a href="/cookies.html">Cookies</a><a href="/publicidad-y-patrocinios.html">Publicidad</a></footer></div>
<!-- fingerprint:{fingerprint};edition:{EDITORIAL_VERSION};mode:{mode};indexable:{str(indexable).lower()} --></body></html>'''


def archive_html(entries: list[dict]) -> str:
    entries = sorted(entries, key=lambda e: e.get("date", ""), reverse=True)
    cards = []
    for e in entries[:500]:
        badge = "ARTÍCULO" if e.get("mode") == "full" else "PARTE BREVE"
        identity = e.get("edition_label") or "Cuaderno del Estrecho"
        cards.append(
            f'<a class="gd-archive-card" href="/{escape(e["url"], quote=True)}"><div><time>{escape(e["date"])}</time><span class="gd-mini-badge">{badge}</span></div>'
            f'<small>{escape(str(identity))}</small><h2>{escape(e["headline"])}</h2><p>{escape(e["summary"])}</p><span>Leer edición →</span></a>'
        )
    latest = entries[0] if entries else None
    lead = (
        f'<a class="gd-latest" href="/{escape(latest["url"], quote=True)}"><span>ÚLTIMA EDICIÓN · {escape(latest["date"])}</span><strong>{escape(latest["headline"])}</strong><p>{escape(latest["summary"])}</p><b>Leer el diario de hoy →</b></a>'
        if latest else '<div class="gd-latest"><span>PRÓXIMA EDICIÓN</span><strong>El Diario del Estrecho publicará su primera jornada desde las 07:00.</strong></div>'
    )
    return f'''<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Diario del Estrecho | Gibraltar Watch</title><meta name="description" content="Hemeroteca del Estrecho de Gibraltar: tráfico, puertos, Ceuta y Melilla, España–Marruecos, economía y seguridad."><link rel="canonical" href="https://estrechogibraltar.com/diario/"><link rel="alternate" type="application/rss+xml" title="Diario del Estrecho" href="https://estrechogibraltar.com/diario-feed.xml"><link rel="stylesheet" href="/styles.css?v=editorial-20260714-contact-1"><link rel="stylesheet" href="/gibraltar-consolidated.css?v=20260803-1"><link rel="stylesheet" href="/gibraltar-layout-polish.css?v=20260829-1"><link rel="stylesheet" href="/diario.css?v=20260831-4"><script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1713078636060241" crossorigin="anonymous"></script></head><body class="gd-page"><div class="site-shell"><header class="gd-top"><a href="/" class="gd-brand"><b>GIBRALTAR</b><span>WATCH</span></a><nav><a href="/">Inicio</a><a href="/situacion-actual.html">Situación actual</a><a href="/trafico.html">Tráfico</a><a href="/diario/" aria-current="page">Diario</a><a href="/fuentes.html">Fuentes</a></nav></header><main class="gd-shell"><header class="gd-archive-hero"><p class="gd-kicker">HEMEROTECA · CUADERNOS DEL ESTRECHO</p><h1>Diario del Estrecho</h1><p>Cada jornada adopta el formato que pide la información: navegación, puertos, fronteras, diplomacia, economía o seguridad. Los días tranquilos también quedan registrados, sin fabricar una noticia que no existe.</p><a href="/diario-feed.xml">RSS del diario</a></header>{lead}<section class="gd-archive"><header><p class="gd-kicker">ARCHIVO</p><h2>Ediciones anteriores</h2></header><div class="gd-archive-grid">{''.join(cards)}</div></section></main><footer class="gd-site-footer"><a href="/contacto.html">Contacto</a><a href="/fuentes.html">Fuentes</a><a href="/publicidad-y-patrocinios.html">Publicidad</a></footer></div></body></html>'''


def legacy_archive_redirect_html() -> str:
    return '''<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Diario del Estrecho | Gibraltar Watch</title><link rel="canonical" href="https://estrechogibraltar.com/diario/"><meta http-equiv="refresh" content="0;url=/diario/"><script>location.replace('/diario/')</script></head><body><p><a href="/diario/">Abrir Diario del Estrecho</a></p></body></html>'''


def home_block(entry: dict | None) -> str:
    if not entry:
        return f'''{HOME_START}
<section class="gw-diary-home" aria-labelledby="gw-diary-title"><div><p class="gw-business-kicker">EL DIARIO · HOY</p><span class="gd-date">PRÓXIMA EDICIÓN</span><h2 id="gw-diary-title">Diario del Estrecho</h2><p>Una pieza diaria con contexto, fuentes y una lectura de qué importa realmente.</p><a href="/diario/">Abrir hemeroteca →</a></div><div class="gw-diary-side"><p class="gw-business-kicker">EN PREPARACIÓN</p><h3>La primera edición se publicará desde las 07:00</h3><p>Los días tranquilos se publica un parte breve; cuando la jornada lo merece, un artículo completo.</p><a href="/diario/">Ver el diario →</a></div></section>
{HOME_END}'''
    badge = entry.get("edition_label") or ("ARTÍCULO DE JORNADA" if entry.get("mode") == "full" else "PARTE BREVE")
    return f'''{HOME_START}
<section class="gw-diary-home" aria-labelledby="gw-diary-title"><div><p class="gw-business-kicker">EL DIARIO · HOY</p><span class="gd-date">{escape(entry["date"])}</span><h2 id="gw-diary-title">Diario del Estrecho</h2><p>Una lectura diaria del tráfico, los puertos, Ceuta y Melilla y la relación España–Marruecos.</p><a href="/diario/">Archivo completo →</a></div><div class="gw-diary-side"><p class="gw-business-kicker">{badge}</p><h3>{escape(entry["headline"])}</h3><p>{escape(entry["summary"])}</p><a href="/{escape(entry["url"], quote=True)}">Leer el diario de hoy →</a></div></section>
{HOME_END}'''


def replace_marked(text: str, start: str, end: str, block: str) -> str:
    if start in text and end in text:
        return re.sub(re.escape(start) + r".*?" + re.escape(end), lambda _: block, text, count=1, flags=re.S)
    return text


def update_home(entry: dict | None) -> None:
    if not HOME.exists():
        return
    text = HOME.read_text(encoding="utf-8")
    new = replace_marked(text, HOME_START, HOME_END, home_block(entry))
    if new != text:
        HOME.write_text(new, encoding="utf-8")


def update_rss(entries: list[dict]) -> None:
    items = []
    for e in sorted(entries, key=lambda x: x.get("date", ""), reverse=True)[:60]:
        items.append(
            f'<item><title>{escape(e["headline"])}</title><link>https://estrechogibraltar.com/{escape(e["url"])}</link>'
            f'<guid isPermaLink="true">https://estrechogibraltar.com/{escape(e["url"])}</guid><pubDate>{escape(e["published_rfc822"])}</pubDate>'
            f'<description>{escape(e["summary"])}</description></item>'
        )
    updated = format_datetime(NOW)
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
        '<title>Diario del Estrecho · Gibraltar Watch</title><link>https://estrechogibraltar.com/diario/</link>'
        '<description>La jornada del Estrecho de Gibraltar explicada cada día.</description><language>es-es</language>'
        f'<lastBuildDate>{escape(updated)}</lastBuildDate>' + ''.join(items) + '</channel></rss>'
    )
    RSS.write_text(xml, encoding="utf-8")


def update_sitemap(entries: list[dict]) -> None:
    if not SITEMAP.exists():
        return
    try:
        tree = ET.parse(SITEMAP)
        root = tree.getroot()
        ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        nodes = {u.findtext(ns + "loc", ""): u for u in root.findall(ns + "url")}
        wanted = [("https://estrechogibraltar.com/diario/", NOW.date().isoformat(), "0.9", "daily")]
        wanted += [
            (f'https://estrechogibraltar.com/{e["url"]}', e["date"], "0.7" if e.get("mode") == "full" else "0.5", "never")
            for e in entries if e.get("indexable", True)
        ]
        for loc, mod, priority, freq in wanted:
            node = nodes.get(loc)
            if node is None:
                node = ET.SubElement(root, ns + "url")
                ET.SubElement(node, ns + "loc").text = loc
                nodes[loc] = node
            lm = node.find(ns + "lastmod")
            if lm is None:
                lm = ET.SubElement(node, ns + "lastmod")
            lm.text = mod
            cf = node.find(ns + "changefreq")
            if cf is None:
                cf = ET.SubElement(node, ns + "changefreq")
            cf.text = freq
            pr = node.find(ns + "priority")
            if pr is None:
                pr = ET.SubElement(node, ns + "priority")
            pr.text = priority

        # Si un parte noindex estaba en un sitemap anterior, se retira.
        noindex_urls = {
            f'https://estrechogibraltar.com/{e["url"]}' for e in entries if not e.get("indexable", True)
        }
        for node in list(root.findall(ns + "url")):
            if node.findtext(ns + "loc", "") in noindex_urls:
                root.remove(node)

        ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
        tree.write(SITEMAP, encoding="utf-8", xml_declaration=True)
    except Exception as exc:
        print(f"Aviso: no se pudo actualizar sitemap: {exc}")


def refresh_day_navigation(entries: list[dict]) -> None:
    for entry in entries:
        path = ROOT / str(entry.get("url", ""))
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if NAV_START not in text or NAV_END not in text:
            continue
        block = day_nav_html(str(entry.get("date", "")), entries)
        new = replace_marked(text, NAV_START, NAV_END, block)
        if new != text:
            path.write_text(new, encoding="utf-8")


def fingerprint_payload(status: dict, selected: list[dict], mode: str) -> str:
    data = {
        "editorial_version": EDITORIAL_VERSION,
        "mode": mode,
        "status": status,
        "items": [
            (i.get("title"), i.get("source"), i.get("published_at"), i.get("weight"), i.get("url"))
            for i in selected
        ],
    }
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()[:20]


def published_rfc822(iso_value: str) -> str:
    return format_datetime(parse_dt(iso_value).astimezone(TZ))


def load_state_entries() -> list[dict]:
    """Carga el estado interno y migra la hemeroteca pública de la v1 si existe."""
    state = load_json(STATE_DATA, None)
    if isinstance(state, dict) and isinstance(state.get("entries"), list):
        return state["entries"]

    legacy = load_json(LEGACY_STATE_DATA, None)
    if isinstance(legacy, list):
        legacy_entries = legacy
    elif isinstance(legacy, dict) and isinstance(legacy.get("entries"), list):
        legacy_entries = legacy["entries"]
    else:
        legacy_entries = []

    migrated = []
    for raw in legacy_entries:
        if not isinstance(raw, dict) or not raw.get("date") or not raw.get("url"):
            continue
        e = dict(raw)
        e.setdefault("mode", "full")
        e.setdefault("significance", 50)
        e.setdefault("significance_reasons", ["Edición migrada desde la primera versión del diario."])
        e.setdefault("indexable", True)
        e.setdefault("editor_engine", "legacy")
        e.setdefault("source_count", 0)
        if not e.get("published_at"):
            e["published_at"] = f'{e["date"]}T07:00+02:00'
        e.setdefault("updated_at", e["published_at"] )
        if not e.get("published_rfc822"):
            try:
                e["published_rfc822"] = published_rfc822(e["published_at"])
            except Exception:
                e["published_rfc822"] = format_datetime(NOW)
        migrated.append(e)
    return migrated


def cleanup_legacy_public_assets() -> None:
    # La web ya no necesita JSON/JS públicos para pintar el Diario en portada.
    for path in (LEGACY_STATE_DATA, LEGACY_LATEST_DATA, LEGACY_DIARIO_JS):
        try:
            if path.exists():
                path.unlink()
        except OSError as exc:
            print(f"Aviso: no se pudo retirar {path.name}: {exc}")


def main() -> int:
    if NOW.hour < MIN_HOUR_LOCAL:
        print(f"Diario: son las {NOW:%H:%M} en Madrid; se espera hasta las 07:00.")
        return 0

    data = load_json(GEOPOLITICS, {})
    if not data:
        print("Diario: geopolitics.json no disponible; no se publica una edición sin base factual.")
        return 0

    status = data.get("status", {}) if isinstance(data.get("status", {}), dict) else {}
    selected = select_items(data.get("items", []) if isinstance(data.get("items", []), list) else [])
    mode = edition_mode(status, selected)
    score, reasons = edition_significance(status, selected)
    indexable = seo_indexable(mode, status, selected)
    date = NOW.date().isoformat()
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    page = ARCHIVE_DIR / f"{date}.html"
    fp = fingerprint_payload(status, selected, mode)

    old = page.read_text(encoding="utf-8") if page.exists() else ""
    if f"fingerprint:{fp}" in old:
        print(f"Diario: la edición de hoy ya está al día ({mode}, relevancia {score}/100).")
        return 0

    entries = load_state_entries()
    old_entry = next((e for e in entries if e.get("date") == date), None)
    published = old_entry.get("published_at") if old_entry else NOW.isoformat(timespec="minutes")
    updated = NOW.isoformat(timespec="minutes")

    draft, engine = build_draft(status, selected, mode)
    headline = clean_text(draft.get("headline"), 180) or fallback_headline(status, selected, mode)
    summary = clean_text(draft.get("deck"), 500) or fallback_deck(status, selected, mode)
    profile = editorial_profile(date, selected, entries)

    entry = {
        "date": date,
        "headline": headline,
        "summary": summary,
        "url": f"diario/{date}.html",
        "published_at": published,
        "updated_at": updated,
        "published_rfc822": published_rfc822(published),
        "source_count": len(selected),
        "fingerprint": fp,
        "mode": mode,
        "significance": score,
        "significance_reasons": reasons,
        "indexable": indexable,
        "editor_engine": engine,
        "edition_label": profile["label"],
        "edition_slug": profile["slug"],
    }
    entries = [e for e in entries if e.get("date") != date]
    entries.append(entry)
    entries.sort(key=lambda e: e.get("date", ""), reverse=True)

    # La página recibe la lista ya actualizada para que su navegación sepa cuál es la anterior.
    page.write_text(
        article_html(date, published, updated, status, selected, fp, draft, mode, indexable, entries, engine),
        encoding="utf-8",
    )

    STATE_DATA.parent.mkdir(parents=True, exist_ok=True)
    STATE_DATA.write_text(json.dumps({"version": 3, "entries": entries}, ensure_ascii=False, indent=2), encoding="utf-8")
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_PAGE.write_text(archive_html(entries), encoding="utf-8")
    LEGACY_ARCHIVE_PAGE.write_text(legacy_archive_redirect_html(), encoding="utf-8")
    update_home(entry)
    update_rss(entries)
    update_sitemap(entries)
    refresh_day_navigation(entries)
    cleanup_legacy_public_assets()

    print(
        f"Diario: edición {date} publicada como {mode} · relevancia {score}/100 · "
        f"{len(selected)} fuentes · redacción={engine} · indexable={indexable}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
