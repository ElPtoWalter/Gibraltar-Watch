#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import sys
import textwrap
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
CONFIG_FILE = ROOT / "diario-config.json"
GEO_FILE = ROOT / "geopolitics.json"
OPE_FILE = ROOT / "ope-2026.json"
SITEMAP = ROOT / "sitemap.xml"
DIARY_DIR = ROOT / "diario"
INDEX_DATA = DIARY_DIR / "index.json"
LATEST = DIARY_DIR / "latest.json"
RSS = DIARY_DIR / "feed.xml"
ARCHIVE = DIARY_DIR / "index.html"
UA = "GibraltarWatch-Diario/1.0 (+https://estrechogibraltar.com/contacto.html)"

FALLBACK_QUERIES = [
    ("ceuta", "Ceuta Marruecos frontera", "es", "ES", "ES:es"),
    ("melilla", "Melilla Marruecos frontera", "es", "ES", "ES:es"),
    ("relations", "España Marruecos Ceuta Melilla", "es", "ES", "ES:es"),
    ("traffic", "Estrecho de Gibraltar tráfico marítimo", "es", "ES", "ES:es"),
    ("ports", "Algeciras Tanger Med puerto", "es", "ES", "ES:es"),
]

CATEGORY_LABELS = {
    "ceuta": "Ceuta",
    "melilla": "Melilla",
    "relations": "España–Marruecos",
    "traffic": "Tráfico marítimo",
    "ports": "Puertos y economía",
}

TRUST = {
    "Reuters": 5, "Associated Press": 5, "AP News": 5, "EFE": 4, "RTVE": 4,
    "La Moncloa": 5, "Ministerio del Interior": 5, "Ministerio de Asuntos Exteriores": 5,
    "European Commission": 5, "Council of the EU": 5, "NATO": 5, "IMO": 5,
    "Salvamento Marítimo": 5, "APBA": 5, "Tanger Med": 5, "Tánger Med": 5,
    "BBC": 4, "Financial Times": 4, "El País": 3, "Cadena SER": 3, "Euronews": 3,
}

HIGH_IMPACT = re.compile(
    r"\b(crisis|dead|death|muert|emergency|emergencia|mass|masiv|thousands|miles|closed|cerrad|"
    r"collision|colisi[oó]n|incident|incidente|agreement|acuerdo|border control|control fronterizo|"
    r"military|militar|evacuat|evacua|strike|huelga|suspend|suspensi[oó]n|dispute|disputa)\b", re.I
)

@dataclass
class Item:
    title: str
    source: str
    url: str
    published_at: str
    category: str
    language: str = "es"
    weight: int = 2


def load_json(path: Path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def config() -> dict:
    defaults = {
        "timezone": "Europe/Madrid", "publish_after_local_hour": 6,
        "lookback_hours": 36, "extended_lookback_hours": 72, "max_sources": 7,
        "full_article_min_sources": 3, "full_article_min_score": 18,
        "ai_mode": "auto", "ai_model": "gpt-5.6-luna",
        "site_name": "Gibraltar Watch", "section_name": "Diario del Estrecho",
        "base_url": "https://estrechogibraltar.com",
    }
    defaults.update(load_json(CONFIG_FILE, {}))
    return defaults


def parse_date(value: str, now: datetime) -> datetime:
    if not value:
        return now
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        try:
            dt = parsedate_to_datetime(value)
        except Exception:
            return now
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def source_name(raw: str, title: str = "") -> str:
    raw = html.unescape((raw or "").strip())
    aliases = {"Reuters.com":"Reuters", "The Associated Press":"Associated Press", "Agencia EFE":"EFE", "EL PAÍS":"El País", "BBC News":"BBC"}
    if raw in aliases:
        return aliases[raw]
    if not raw and " - " in title:
        raw = title.rsplit(" - ", 1)[-1].strip()
    return aliases.get(raw, raw or "Fuente no identificada")


def fallback_fetch(now: datetime) -> list[Item]:
    out: list[Item] = []
    for category, query, hl, gl, ceid in FALLBACK_QUERIES:
        url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": query, "hl": hl, "gl": gl, "ceid": ceid})
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as r:
                root = ET.fromstring(r.read())
            for node in root.findall(".//item"):
                title = html.unescape((node.findtext("title") or "").strip())
                link = (node.findtext("link") or "").strip()
                sn = node.find("source")
                source = source_name(sn.text if sn is not None and sn.text else "", title)
                if " - " in title and title.rsplit(" - ",1)[-1].strip().lower() == source.lower():
                    title = title.rsplit(" - ",1)[0].strip()
                if title and link:
                    out.append(Item(title, source, link, parse_date(node.findtext("pubDate") or "", now).isoformat(), category, hl, TRUST.get(source, 2)))
        except Exception as exc:
            print(f"Aviso: no se pudo consultar {category}: {exc}", file=sys.stderr)
    return out


def items_from_geopolitics(now: datetime) -> tuple[list[Item], dict]:
    data = load_json(GEO_FILE, {})
    items: list[Item] = []
    for raw in data.get("items", []):
        source = raw.get("source") or "Fuente no identificada"
        items.append(Item(
            title=raw.get("title", "").strip(), source=source, url=raw.get("url", "").strip(),
            published_at=raw.get("published_at", now.isoformat()), category=raw.get("category", "relations"),
            language=raw.get("language", "es"), weight=int(raw.get("weight") or TRUST.get(source, 2)),
        ))
    if not items:
        items = fallback_fetch(now)
    return items, data.get("status", {})


def dedupe(items: list[Item]) -> list[Item]:
    seen_title, seen_url = set(), set()
    out = []
    for x in items:
        key = re.sub(r"\W+", " ", x.title.lower()).strip()
        key = " ".join(key.split()[:16])
        if not x.title or not x.url or key in seen_title or x.url in seen_url:
            continue
        seen_title.add(key); seen_url.add(x.url); out.append(x)
    return out


def select_items(items: list[Item], now: datetime, cfg: dict) -> list[Item]:
    def within(hours: int):
        threshold = now.astimezone(timezone.utc) - timedelta(hours=hours)
        return [x for x in items if parse_date(x.published_at, now) >= threshold]
    pool = within(int(cfg["lookback_hours"]))
    if len(pool) < 3:
        pool = within(int(cfg["extended_lookback_hours"]))

    def score(x: Item) -> float:
        age = max(0.0, (now.astimezone(timezone.utc)-parse_date(x.published_at,now)).total_seconds()/3600)
        recency = max(0, 4 - age/12)
        impact = 4 if HIGH_IMPACT.search(x.title) else 0
        cat = 1.5 if x.category in {"ceuta","melilla","traffic","ports","relations"} else 0
        return x.weight*2 + recency + impact + cat

    pool = sorted(dedupe(pool), key=score, reverse=True)
    chosen: list[Item] = []
    used_cats: set[str] = set()
    # First pass: diversity
    for x in pool:
        if x.category not in used_cats:
            chosen.append(x); used_cats.add(x.category)
        if len(chosen) >= int(cfg["max_sources"]): break
    # Second pass: highest remaining
    for x in pool:
        if x not in chosen:
            chosen.append(x)
        if len(chosen) >= int(cfg["max_sources"]): break
    return chosen


def signal_score(items: list[Item]) -> int:
    s = sum(min(5, max(1, x.weight)) for x in items)
    s += sum(3 for x in items if HIGH_IMPACT.search(x.title))
    s += len({x.source for x in items})
    return s


def txt(value) -> str:
    return html.escape(str(value or ""), quote=True)


def nested(status: dict, key: str, lang="es", default="—"):
    v = status.get(key, default)
    if isinstance(v, dict): return v.get(lang, default)
    return v or default


def ope_context() -> dict:
    data = load_json(OPE_FILE, {})
    if not data:
        return {}
    d = data.get("departure", {}).get("day", {})
    r = data.get("return", {}).get("day", {})
    routes = data.get("departure", {}).get("routes", [])
    top = max(routes, key=lambda x: x.get("passengers",0), default={})
    return {
        "report_date": data.get("report_label_es") or data.get("report_date"),
        "source": data.get("source"), "source_url": data.get("source_url"),
        "departure_passengers": d.get("passengers"), "departure_vehicles": d.get("vehicles"),
        "return_passengers": r.get("passengers"), "return_vehicles": r.get("vehicles"),
        "top_route": top.get("name"), "top_route_passengers": top.get("passengers"),
    }


def fallback_story(items: list[Item], status: dict, ope: dict, full: bool, local_now: datetime) -> dict:
    maritime = nested(status, "maritime_status")
    border = nested(status, "border_pressure")
    bilateral = nested(status, "bilateral_tension")
    security = nested(status, "security_status")
    has_border = any(x.category in {"ceuta","melilla"} for x in items)
    has_traffic = any(x.category in {"traffic","ports"} for x in items)

    if border in {"ALTA","HIGH"} or has_border:
        headline = f"Ceuta sigue marcando la agenda mientras el tráfico del Estrecho permanece {maritime.lower()}"
    elif maritime not in {"OPERATIVO","OPERATIONAL","—"}:
        headline = f"El tráfico marítimo concentra la atención en una jornada con el corredor {maritime.lower()}"
    elif items:
        headline = f"El Estrecho mantiene el pulso operativo con la actualidad repartida entre puertos y política"
    else:
        headline = "Jornada estable en el Estrecho, sin señales suficientes para elevar la alerta"

    dek = f"La lectura de esta mañana sitúa el tráfico marítimo en {maritime.lower()}, la presión fronteriza en {border.lower()} y la relación España–Marruecos en {bilateral.lower()}."
    if items:
        lead = f"Gibraltar Watch abre la edición del {local_now.strftime('%d/%m/%Y')} con {len(items)} referencias recientes seleccionadas por relevancia y trazabilidad. La prioridad editorial es separar lo que las fuentes han publicado de cualquier interpretación sobre sus causas o consecuencias."
    else:
        lead = "No se han localizado suficientes novedades recientes para justificar una crónica extensa. El observatorio conserva por ello un parte breve y remite a los indicadores operativos y a las fuentes oficiales."

    sections = []
    if items:
        top = items[:2]
        p = " ".join(f"{x.source} sitúa entre las novedades del periodo «{x.title}»." for x in top)
        sections.append({"heading":"La situación", "paragraphs":[p, f"La lectura conjunta no cambia por sí sola el estado del corredor: tráfico {maritime.lower()}, seguridad {security.lower()} y relación bilateral {bilateral.lower()} según el monitor editorial."]})
    if has_border:
        rel = [x for x in items if x.category in {"ceuta","melilla","relations"}][:3]
        p = " ".join(f"{x.source} ha publicado «{x.title}»." for x in rel)
        sections.append({"heading":"Ceuta, Melilla y la relación bilateral", "paragraphs":[p, "La existencia de presión fronteriza o fricción política no permite atribuir por sí misma intenciones estratégicas. El diario mantiene separadas las declaraciones, los hechos observables y los escenarios de análisis."]})
    if has_traffic or ope:
        ps = [f"El panel marítimo mantiene el estado {maritime.lower()}."]
        if ope.get("report_date"):
            sentence = f"El último parte OPE localizado corresponde a {ope['report_date']}"
            if ope.get("departure_passengers") is not None:
                sentence += f" y registra {ope['departure_passengers']:,} pasajeros en salida".replace(",", ".")
            if ope.get("top_route"):
                sentence += f"; la ruta con más pasajeros en ese parte es {ope['top_route']}"
            sentence += "."
            ps.append(sentence)
        sections.append({"heading":"Tráfico, ferris y puertos", "paragraphs":ps})

    meaning = "El valor de la jornada está en la superposición de capas: navegación, frontera, puertos y diplomacia. Ninguna de ellas equivale por sí sola al control del Estrecho, pero cambios sostenidos en varias capas a la vez sí pueden alterar su importancia económica y política."
    sections.append({"heading":"Qué significa", "paragraphs":[meaning]})
    watch = []
    if border not in {"BAJA / SIN SEÑALES RECIENTES","LOW / NO RECENT SIGNALS","—"}: watch.append("Evolución de la presión fronteriza y capacidad de acogida en Ceuta y Melilla.")
    if bilateral not in {"ESTABLE","STABLE","—"}: watch.append("Nuevas declaraciones o medidas que cambien la cooperación entre España y Marruecos.")
    watch.append("Avisos oficiales de navegación, incidencias y congestión en el corredor.")
    watch.append("Actividad de Algeciras, Tánger Med y las rutas de la OPE.")
    return {"headline":headline, "dek":dek, "lead":lead, "sections":sections, "watch":watch[:4], "summary":dek}


def ai_story(items: list[Item], status: dict, ope: dict, full: bool, local_now: datetime, cfg: dict) -> dict | None:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    mode = str(cfg.get("ai_mode", "auto")).lower()
    if mode == "off" or not key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        context = {
            "date_local": local_now.isoformat(), "article_type": "full" if full else "brief",
            "status": status, "ope": ope, "sources": [asdict(x) for x in items],
        }
        instructions = """
Eres la redacción de Gibraltar Watch, un observatorio independiente del Estrecho de Gibraltar. Redacta en español con tono periodístico sobrio, claro y humano, sin sonar a texto promocional ni a resumen de IA.
REGLAS OBLIGATORIAS:
- Usa exclusivamente los hechos presentes en el JSON de entrada. No añadas datos, cifras, causas, citas ni antecedentes no proporcionados.
- Los títulos de noticias son señales de lo publicado por cada fuente: atribuye la información a la fuente cuando proceda y no conviertas el titular en una certeza más amplia.
- Distingue hecho, declaración, interpretación y escenario. No atribuyas a Marruecos, España u otro actor intenciones no demostradas.
- No afirmes cierre del Estrecho salvo que los datos de entrada lo confirmen explícitamente.
- No copies frases largas de ninguna fuente; parafrasea.
- Si hay poca novedad, escribe un parte breve y dilo con naturalidad.
- Devuelve SOLO JSON válido, sin markdown.
Estructura JSON: {"headline":"...","dek":"...","lead":"...","sections":[{"heading":"...","paragraphs":["...","..."]}],"watch":["..."],"summary":"..."}.
Para artículo completo busca 650-900 palabras. Para parte breve 220-350 palabras. Incluye siempre una sección final "Qué significa" y una lista "watch" con 2-4 puntos concretos.
""".strip()
        response = client.responses.create(
            model=os.getenv("GW_DIARY_OPENAI_MODEL", str(cfg.get("ai_model","gpt-5.6-luna"))),
            reasoning={"effort":"low"},
            instructions=instructions,
            input=json.dumps(context, ensure_ascii=False),
        )
        raw = response.output_text.strip()
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.S)
        obj = json.loads(raw)
        if not all(k in obj for k in ("headline","dek","lead","sections","watch","summary")):
            raise ValueError("JSON incompleto")
        return obj
    except Exception as exc:
        print(f"Aviso: IA no disponible o respuesta inválida ({type(exc).__name__}: {exc}). Se usa redacción determinista.", file=sys.stderr)
        return None


def iso_local_date(local_now: datetime) -> str:
    return local_now.date().isoformat()


def pretty_date_es(local_now: datetime) -> str:
    months = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
    return f"{local_now.day} de {months[local_now.month-1]} de {local_now.year}"


def article_html(story: dict, items: list[Item], status: dict, ope: dict, local_now: datetime, full: bool, generator: str, cfg: dict) -> str:
    date = iso_local_date(local_now)
    title = story["headline"]
    desc = story.get("summary") or story["dek"]
    robots = "index,follow,max-image-preview:large" if full else "noindex,follow"
    url = f"{cfg['base_url']}/diario/{date}.html"
    sources_html = "".join(
        f'<li><a href="{txt(x.url)}" target="_blank" rel="noopener noreferrer">{txt(x.source)} — {txt(x.title)}</a><small>{txt(parse_date(x.published_at, local_now).astimezone(ZoneInfo(cfg["timezone"])).strftime("%d/%m/%Y %H:%M"))}</small></li>'
        for x in items
    ) or '<li>No se localizaron novedades suficientes; se publica un parte operativo.</li>'
    sections_html = "".join(
        f'<section class="diary-section"><h2>{txt(sec.get("heading"))}</h2>' + "".join(f'<p>{txt(p)}</p>' for p in sec.get("paragraphs", [])) + '</section>'
        for sec in story.get("sections", [])
    )
    watch_html = "".join(f'<li>{txt(x)}</li>' for x in story.get("watch", []))
    status_html = "".join([
        f'<div><small>TRÁFICO</small><strong>{txt(nested(status,"maritime_status"))}</strong></div>',
        f'<div><small>CEUTA Y MELILLA</small><strong>{txt(nested(status,"border_pressure"))}</strong></div>',
        f'<div><small>ESPAÑA–MARRUECOS</small><strong>{txt(nested(status,"bilateral_tension"))}</strong></div>',
        f'<div><small>SEGURIDAD</small><strong>{txt(nested(status,"security_status"))}</strong></div>',
    ])
    article_type = "Crónica" if full else "Parte breve"
    schema = json.dumps({
        "@context":"https://schema.org","@type":"NewsArticle" if full else "Article","headline":title,
        "description":desc,"datePublished":local_now.isoformat(),"dateModified":local_now.isoformat(),
        "mainEntityOfPage":url,"inLanguage":"es","author":{"@type":"Organization","name":"Redacción de Gibraltar Watch"},
        "publisher":{"@type":"Organization","name":"Gibraltar Watch","url":cfg["base_url"]},
    }, ensure_ascii=False)
    return f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{txt(title)} | Diario del Estrecho</title><meta name="description" content="{txt(desc)}"><meta name="robots" content="{robots}"><link rel="canonical" href="{txt(url)}"><meta property="og:type" content="article"><meta property="og:title" content="{txt(title)}"><meta property="og:description" content="{txt(desc)}"><meta property="og:url" content="{txt(url)}"><meta property="og:image" content="{cfg['base_url']}/social-card.png"><link rel="stylesheet" href="../styles.css"><link rel="stylesheet" href="../gibraltar-consolidated.css?v=20260803-1"><link rel="stylesheet" href="../gibraltar-layout-polish.css?v=20260829-1"><link rel="stylesheet" href="../gw-business.css?v=20260829-1"><link rel="stylesheet" href="../diario.css?v=20260810-1"><script type="application/ld+json">{schema}</script></head>
<body class="diary-body"><div class="diary-shell"><header class="diary-header"><a class="diary-brand" href="../index.html">GIBRALTAR WATCH</a><nav class="diary-nav"><a href="./">Diario</a><a href="../situacion-actual.html">Situación actual</a><a href="../trafico.html">Tráfico</a><a href="../fuentes.html">Fuentes</a></nav></header>
<main><article class="diary-article"><div class="diary-main"><p class="diary-kicker">DIARIO DEL ESTRECHO · {txt(article_type.upper())}</p><h1>{txt(title)}</h1><p class="diary-dek">{txt(story['dek'])}</p><div class="diary-byline"><span>Redacción de Gibraltar Watch</span><time datetime="{date}">{txt(pretty_date_es(local_now))}</time><span>Confianza: {txt(nested(status,'confidence','es','—'))}</span></div><p class="diary-lead">{txt(story['lead'])}</p>{sections_html}<section class="diary-section diary-watch"><h2>Qué vigilamos ahora</h2><ul>{watch_html}</ul></section><section class="diary-sources"><h2>Fuentes de esta edición</h2><ol>{sources_html}</ol></section><div class="diary-disclosure"><strong>Cómo se elabora este diario.</strong> Gibraltar Watch selecciona referencias públicas recientes, elimina duplicados y cruza la actualidad con sus monitores de tráfico y contexto. La redacción puede ser asistida automáticamente, pero el sistema tiene instrucciones de no inventar hechos, no atribuir intenciones y enlazar las fuentes empleadas. Los partes de baja señal se publican con <code>noindex</code> para no crear páginas de escaso valor en buscadores. Motor de esta edición: {txt(generator)}.</div></div><aside class="diary-side"><div class="diary-side__sticky"><p class="diary-kicker">LECTURA DEL OBSERVATORIO</p><div class="diary-status">{status_html}</div></div></aside></article></main>
<footer class="diary-footer"><span>Gibraltar Watch · Diario del Estrecho</span><a href="../contacto.html">Correcciones y fuentes</a></footer></div></body></html>'''


def archive_html(entries: list[dict], cfg: dict) -> str:
    cards = []
    for e in entries:
        label = "CRÓNICA" if e.get("indexable") else "PARTE BREVE"
        cards.append(f'<a class="diary-entry" href="{txt(e["slug"])}"><time datetime="{txt(e["date"])}">{txt(e["date_label"])}</time><div><h2>{txt(e["headline"])}</h2><p>{txt(e["summary"])}</p></div><span>{label}</span></a>')
    body = "".join(cards) or '<p>Aún no hay ediciones publicadas.</p>'
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Diario del Estrecho | Gibraltar Watch</title><meta name="description" content="Archivo diario de Gibraltar Watch sobre tráfico marítimo, puertos, Ceuta y Melilla, España–Marruecos y economía del Estrecho."><link rel="canonical" href="{cfg['base_url']}/diario/"><link rel="alternate" type="application/rss+xml" title="Diario del Estrecho" href="{cfg['base_url']}/diario/feed.xml"><link rel="stylesheet" href="../styles.css"><link rel="stylesheet" href="../gibraltar-consolidated.css?v=20260803-1"><link rel="stylesheet" href="../gibraltar-layout-polish.css?v=20260829-1"><link rel="stylesheet" href="../gw-business.css?v=20260829-1"><link rel="stylesheet" href="../diario.css?v=20260810-1"></head><body class="diary-body"><div class="diary-shell"><header class="diary-header"><a class="diary-brand" href="../index.html">GIBRALTAR WATCH</a><nav class="diary-nav"><a href="../situacion-actual.html">Situación actual</a><a href="../trafico.html">Tráfico</a><a href="feed.xml">RSS</a></nav></header><main><section class="diary-masthead"><div class="diary-masthead__top"><div><p class="diary-kicker">HEMEROTECA · EDICIÓN DIARIA</p><h1>Diario<br>del Estrecho</h1></div><p class="diary-date">TRÁFICO · PUERTOS · FRONTERA · GEOPOLÍTICA</p></div><p>Una crónica diaria de lo que cambia —y de lo que no— en el corredor de Gibraltar. Las fuentes se enlazan y los días sin novedades suficientes se reducen a un parte breve.</p></section><section class="diary-archive"><div class="diary-archive-grid">{body}</div></section></main><footer class="diary-footer"><span>Gibraltar Watch · Archivo diario</span><a href="../contacto.html">Correcciones</a></footer></div></body></html>'''


def rss_xml(entries: list[dict], cfg: dict) -> str:
    items = []
    for e in entries[:20]:
        link = f"{cfg['base_url']}/diario/{e['slug']}"
        items.append(f"<item><title>{txt(e['headline'])}</title><link>{txt(link)}</link><guid>{txt(link)}</guid><pubDate>{txt(e['pub_rfc822'])}</pubDate><description>{txt(e['summary'])}</description></item>")
    return f'''<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>Diario del Estrecho · Gibraltar Watch</title><link>{cfg['base_url']}/diario/</link><description>Crónica diaria del Estrecho de Gibraltar.</description><language>es</language>{''.join(items)}</channel></rss>'''


def update_sitemap(entries: list[dict], cfg: dict):
    if not SITEMAP.exists():
        return
    text = SITEMAP.read_text(encoding="utf-8")
    # Remove old diary URLs managed by this generator.
    text = re.sub(r'\s*<url>\s*<loc>https://estrechogibraltar\.com/diario/[^<]*</loc>.*?</url>', '', text, flags=re.S)
    urls = [f'<url><loc>{cfg["base_url"]}/diario/</loc><lastmod>{entries[0]["date"] if entries else datetime.now().date().isoformat()}</lastmod><changefreq>daily</changefreq><priority>0.9</priority></url>']
    for e in entries:
        if e.get("indexable"):
            urls.append(f'<url><loc>{cfg["base_url"]}/diario/{e["slug"]}</loc><lastmod>{e["date"]}</lastmod><changefreq>never</changefreq><priority>0.7</priority></url>')
    text = text.replace('</urlset>', '\n' + '\n'.join(urls) + '\n</urlset>')
    SITEMAP.write_text(text, encoding="utf-8")


def update_home(latest: dict):
    path = ROOT / "index.html"
    if not path.exists(): return
    text = path.read_text(encoding="utf-8")
    start, end = '<!-- GW_DIARY_HOME_START -->', '<!-- GW_DIARY_HOME_END -->'
    block = f'''{start}\n<section class="gw-diary-home" aria-labelledby="gw-diary-home-title"><div class="gw-diary-home__mast"><small>EDICIÓN · {txt(latest['date_label']).upper()}</small><strong>DIARIO<br>DEL<br>ESTRECHO</strong><span>{'CRÓNICA DEL DÍA' if latest.get('indexable') else 'PARTE BREVE'}</span></div><div class="gw-diary-home__story"><div class="gw-diary-home__meta"><span>{txt(latest['source_count'])} fuentes seleccionadas</span><span>Confianza: {txt(latest['confidence'])}</span></div><h2 id="gw-diary-home-title">{txt(latest['headline'])}</h2><p>{txt(latest['summary'])}</p><a class="gw-diary-home__link" href="diario/{txt(latest['slug'])}">Leer la edición de hoy →</a></div></section>\n{end}'''
    if start in text and end in text:
        text = re.sub(re.escape(start)+r'.*?'+re.escape(end), block, text, flags=re.S)
    else:
        anchor = '<!-- GW_BUSINESS_HOME_START -->'
        text = text.replace(anchor, block+'\n'+anchor,1) if anchor in text else text.replace('</main>', block+'\n</main>',1)
    path.write_text(text, encoding="utf-8")


def generate(root: Path = ROOT, now: datetime | None = None, force=False, allow_early=False, disable_ai=False) -> dict | None:
    global ROOT, CONFIG_FILE, GEO_FILE, OPE_FILE, SITEMAP, DIARY_DIR, INDEX_DATA, LATEST, RSS, ARCHIVE
    # Allow tests/alternate roots.
    if root != ROOT:
        ROOT = root; CONFIG_FILE=root/'diario-config.json'; GEO_FILE=root/'geopolitics.json'; OPE_FILE=root/'ope-2026.json'; SITEMAP=root/'sitemap.xml'; DIARY_DIR=root/'diario'; INDEX_DATA=DIARY_DIR/'index.json'; LATEST=DIARY_DIR/'latest.json'; RSS=DIARY_DIR/'feed.xml'; ARCHIVE=DIARY_DIR/'index.html'
    cfg = config()
    tz = ZoneInfo(cfg["timezone"])
    now = now or datetime.now(timezone.utc)
    local_now = now.astimezone(tz)
    if local_now.hour < int(cfg["publish_after_local_hour"]) and not allow_early:
        print(f"Diario: todavía no son las {cfg['publish_after_local_hour']}:00 en {cfg['timezone']}; no se publica.")
        return None
    DIARY_DIR.mkdir(parents=True, exist_ok=True)
    date = iso_local_date(local_now); article_path = DIARY_DIR / f"{date}.html"
    entries = load_json(INDEX_DATA, [])
    if article_path.exists() and not force:
        print(f"Diario: la edición {date} ya existe; no se vuelve a generar.")
        if entries:
            update_home(entries[0]); ARCHIVE.write_text(archive_html(entries,cfg),encoding='utf-8'); RSS.write_text(rss_xml(entries,cfg),encoding='utf-8'); update_sitemap(entries,cfg)
        return entries[0] if entries else None
    items, status = items_from_geopolitics(now)
    selected = select_items(items, now, cfg)
    score = signal_score(selected)
    source_count = len({x.source for x in selected})
    full = source_count >= int(cfg["full_article_min_sources"]) and score >= int(cfg["full_article_min_score"])
    ope = ope_context()
    story = None if disable_ai else ai_story(selected, status, ope, full, local_now, cfg)
    generator = "OpenAI + reglas editoriales" if story else "reglas editoriales deterministas"
    story = story or fallback_story(selected, status, ope, full, local_now)
    article_path.write_text(article_html(story, selected, status, ope, local_now, full, generator, cfg), encoding="utf-8")
    source_hash = hashlib.sha256(json.dumps([asdict(x) for x in selected],ensure_ascii=False,sort_keys=True).encode()).hexdigest()[:16]
    entry = {
        "date":date,"date_label":pretty_date_es(local_now),"slug":f"{date}.html","headline":story["headline"],"summary":story.get("summary") or story["dek"],
        "indexable":full,"source_count":source_count,"confidence":nested(status,"confidence","es","—"),"generator":generator,"source_hash":source_hash,
        "pub_rfc822":local_now.astimezone(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    }
    entries = [e for e in entries if e.get("date") != date]
    entries.insert(0, entry); entries = sorted(entries,key=lambda e:e.get("date",""),reverse=True)[:730]
    INDEX_DATA.write_text(json.dumps(entries,ensure_ascii=False,indent=2),encoding='utf-8')
    LATEST.write_text(json.dumps(entry,ensure_ascii=False,indent=2),encoding='utf-8')
    ARCHIVE.write_text(archive_html(entries,cfg),encoding='utf-8')
    RSS.write_text(rss_xml(entries,cfg),encoding='utf-8')
    update_home(entry); update_sitemap(entries,cfg)
    print(f"Diario publicado: {date} · {'crónica' if full else 'parte breve'} · {source_count} fuentes · motor: {generator}.")
    return entry


def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument('--force',action='store_true'); p.add_argument('--allow-early',action='store_true'); p.add_argument('--no-ai',action='store_true'); args=p.parse_args()
    generate(force=args.force,allow_early=args.allow_early,disable_ai=args.no_ai)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
