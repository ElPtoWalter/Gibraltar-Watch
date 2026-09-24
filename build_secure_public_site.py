#!/usr/bin/env python3
"""Build a hardened GitHub Pages artifact from the repository.

The published artifact intentionally excludes backend/source files and raw JSON
endpoints. JSON consumed by existing front-end code is bundled in-memory so old
fetch() calls keep working without publishing standalone .json resources.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from publication_quality import apply_policy
from ope_analysis import build_report
from own_projects import add_promotions

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "_site"

SKIP_DIRS = {
    ".git", ".github", "__pycache__", ".venv", "venv", "node_modules",
    "_site", ".pytest_cache", ".mypy_cache", "tests", "test", "backup", "backups", "cloudflare",
}
SKIP_EXTS = {
    ".py", ".pyc", ".pyo", ".yml", ".yaml", ".md", ".markdown", ".toml",
    ".ini", ".cfg", ".conf", ".env", ".log", ".sql", ".zip", ".tar", ".gz",
    ".7z", ".rar", ".map", ".ps1", ".sh", ".bat", ".cmd",
}
SKIP_NAMES = {
    "publication-manifest.json", "observatory-state-memory.json", "package-lock.json",
    "package.json", "VERSION_OBSERVATORY.txt", "VERSION.txt",
}
SENSITIVE_NAME_PARTS = {"secret", "private", "credential", "token", "password", "memory", "manifest"}

# JSON that is already part of reader-facing panels, plus dynamically discovered JSON references.
PUBLIC_JSON_BASE = {
    "observatory.json", "health.json", "timeline.json", "observatory-history.json",
    "seismicity.json", "seismic-history.json", "geopolitics.json", "ope-2026.json",
    "corrections.json", "sources.json", "diario/latest.json", "newsletter/latest.json",
}
DROP_META_KEYS = {
    "generator", "generator_name", "generator_version", "model", "model_name", "model_id",
    "provider", "engine", "prompt", "prompt_version", "openai", "openai_model",
    "ai_model", "diary_generator",
}
try:
    MADRID = ZoneInfo("Europe/Madrid")
except Exception:  # Windows runners without the optional tzdata package.
    MADRID = timezone(timedelta(hours=2), "CEST")


def clean_obj(value):
    if isinstance(value, dict):
        return {k: clean_obj(v) for k, v in value.items() if k.lower() not in DROP_META_KEYS}
    if isinstance(value, list):
        return [clean_obj(v) for v in value]
    return value


def parse_dt(value):
    try:
        parsed = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def format_checked_at(value) -> str:
    parsed = parse_dt(value)
    if not parsed:
        return "Sin fecha disponible"
    return parsed.astimezone(MADRID).strftime("%d/%m/%Y · %H:%M") + " (hora peninsular)"


def format_news_date(value) -> str:
    parsed = parse_dt(value)
    if not parsed:
        return "Sin fecha"
    return parsed.astimezone(MADRID).strftime("%d/%m/%Y · %H:%M")


def _replace_matches(document: str, opening_pattern: re.Pattern[str], content) -> str:
    """Replace matching element contents while respecting nested tags."""
    cursor = 0
    while True:
        match = opening_pattern.search(document, cursor)
        if not match:
            return document
        tag = match.group("tag")
        depth = 1
        close_end = None
        for token in re.finditer(
            rf"<{re.escape(tag)}\b[^>]*>|</{re.escape(tag)}\s*>",
            document[match.end():],
            re.I | re.S,
        ):
            raw = token.group(0)
            if raw.lower().startswith(f"</{tag.lower()}"):
                depth -= 1
                if depth == 0:
                    close_start = match.end() + token.start()
                    close_end = match.end() + token.end()
                    break
            elif not raw.rstrip().endswith("/>"):
                depth += 1
        if close_end is None:
            return document
        replacement = content(match) if callable(content) else content
        document = document[:match.end()] + replacement + document[close_start:]
        cursor = match.end() + len(replacement) + (close_end - close_start)


def replace_id(document: str, element_id: str, content: str) -> str:
    pattern = re.compile(
        rf'<(?P<tag>[A-Za-z0-9]+)\b[^>]*\bid=["\']{re.escape(element_id)}["\'][^>]*>',
        re.I | re.S,
    )
    match = pattern.search(document)
    if not match:
        return document
    # Restrict the generic helper to the first match for an id.
    return _replace_matches(document[:match.start()] + document[match.start():], pattern, content)


def replace_attr(document: str, attr: str, value: str, content: str) -> str:
    pattern = re.compile(
        rf'<(?P<tag>[A-Za-z0-9]+)\b[^>]*\b{re.escape(attr)}=["\']{re.escape(value)}["\'][^>]*>',
        re.I | re.S,
    )
    return _replace_matches(document, pattern, content)


def localized(value, lang: str = "es", fallback: str = "—") -> str:
    if isinstance(value, dict):
        return str(value.get(lang) or value.get("es") or value.get("en") or fallback)
    return str(value if value not in (None, "") else fallback)


def render_home_news(items) -> str:
    rows = []
    valid = [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []
    valid.sort(key=lambda item: parse_dt(item.get("published_at")) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    labels = {
        "ceuta": "Ceuta y frontera", "melilla": "Melilla y frontera",
        "relations": "España–Marruecos", "traffic": "Tráfico marítimo",
        "ports": "Economía y puertos", "security": "Seguridad",
    }
    for item in valid[:5]:
        url = html.escape(str(item.get("url") or "#"), quote=True)
        title = html.escape(str(item.get("title") or "Novedad sin título"))
        source = html.escape(str(item.get("source") or "Fuente no indicada"))
        category = html.escape(labels.get(str(item.get("category") or ""), "Actualidad"))
        date = html.escape(format_news_date(item.get("published_at")))
        rows.append(
            f'<article class="gwc-news-item"><time>{date}</time><div><h3><a href="{url}" target="_blank" '
            f'rel="noopener noreferrer">{title}</a></h3><small>{source}</small></div><b>{category}</b></article>'
        )
    return "".join(rows) or '<p class="gwc-empty">No hay novedades verificadas en el último ciclo.</p>'


def render_strategy_news(items) -> str:
    rows = []
    valid = [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []
    valid.sort(key=lambda item: parse_dt(item.get("published_at")) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    for item in valid[:9]:
        url = html.escape(str(item.get("url") or "#"), quote=True)
        title = html.escape(str(item.get("title") or "Novedad sin título"))
        source = html.escape(str(item.get("source") or "Fuente"))
        category = html.escape(str(item.get("category") or "actualidad"))
        date = html.escape(format_news_date(item.get("published_at")))
        rows.append(
            f'<a class="gw-news-card" href="{url}" target="_blank" rel="noopener noreferrer">'
            f'<small>{category}</small><h3>{title}</h3><footer><span>{source}</span><time>{date}</time></footer></a>'
        )
    return "".join(rows) or '<article class="gw-news-placeholder">No hay titulares recientes disponibles.</article>'


def render_timeline(items, limit: int = 12) -> str:
    rows = []
    for item in (items if isinstance(items, list) else [])[:limit]:
        if not isinstance(item, dict):
            continue
        rows.append(
            f'<article class="gwo-event" data-level="{html.escape(str(item.get("level") or "info"), quote=True)}">'
            f'<time>{html.escape(format_news_date(item.get("at")))}</time>'
            f'<h3>{html.escape(str(item.get("title_es") or "Actualización"))}</h3>'
            f'<p>{html.escape(str(item.get("detail_es") or ""))}</p></article>'
        )
    return "".join(rows) or '<div class="gwo-empty">Aún no hay cambios registrados en la cronología.</div>'


def prerender_html(text: str, relative_path: str, data: dict[str, object]) -> str:
    """Write current public state into HTML before JavaScript enhancement."""
    geopolitics = data.get("geopolitics.json") if isinstance(data.get("geopolitics.json"), dict) else {}
    observatory = data.get("observatory.json") if isinstance(data.get("observatory.json"), dict) else {}
    health = data.get("health.json") if isinstance(data.get("health.json"), dict) else {}
    timeline = data.get("timeline.json") if isinstance(data.get("timeline.json"), list) else []
    status = geopolitics.get("status") if isinstance(geopolitics.get("status"), dict) else {}
    state = observatory.get("state") if isinstance(observatory.get("state"), dict) else {}
    checked = observatory.get("generated_at") or geopolitics.get("generated_at")
    confidence = str(state.get("confidence") or localized(status.get("confidence")))
    confidence_note = str(state.get("confidence_explanation_es") or "La confianza depende de la frescura y cobertura de las fuentes consultadas.")

    if relative_path == "index.html":
        text = replace_id(text, "gwcStatusMeta", html.escape(f"Actualizado: {format_checked_at(checked)} · Confianza: {confidence}"))
        text = replace_id(text, "gwcConfidenceNote", html.escape(confidence_note))
        pairs = {
            "gwcStatusMaritime": localized(status.get("maritime_status")),
            "gwcNoteMaritime": localized(status.get("maritime_note"), fallback=""),
            "gwcStatusBorder": localized(status.get("border_pressure")),
            "gwcNoteBorder": localized(status.get("border_note"), fallback=""),
            "gwcStatusBilateral": localized(status.get("bilateral_tension")),
            "gwcNoteBilateral": localized(status.get("bilateral_note"), fallback=""),
            "gwcStatusSecurity": localized(status.get("security_status")),
            "gwcNoteSecurity": localized(status.get("security_note"), fallback=""),
        }
        for element_id, value in pairs.items():
            text = replace_id(text, element_id, html.escape(value))
        text = replace_id(text, "gwcNewsList", render_home_news(geopolitics.get("items")))

    if relative_path in {"situacion-actual.html", "en-current-situation.html"}:
        geo_pairs = {
            "maritime_status": localized(status.get("maritime_status")),
            "maritime_note": localized(status.get("maritime_note"), fallback=""),
            "border_pressure": localized(status.get("border_pressure")),
            "border_note": localized(status.get("border_note"), fallback=""),
            "bilateral_tension": localized(status.get("bilateral_tension")),
            "bilateral_note": localized(status.get("bilateral_note"), fallback=""),
            "security_status": localized(status.get("security_status")),
            "security_note": localized(status.get("security_note"), fallback=""),
            "confidence": confidence,
            "generated_at": format_checked_at(checked),
        }
        for key, value in geo_pairs.items():
            text = replace_attr(text, "data-strat", key, html.escape(value))
        text = replace_attr(text, "data-news-feed", "", render_strategy_news(geopolitics.get("items"))) if 'data-news-feed=""' in text else text
        # Boolean data-news-feed attributes need their own pattern.
        text = _replace_matches(text, re.compile(r'<(?P<tag>[A-Za-z0-9]+)\b[^>]*\bdata-news-feed(?=\s|>)[^>]*>', re.I | re.S), render_strategy_news(geopolitics.get("items")))
        text = replace_attr(text, "data-gwo-state", "", html.escape(str(state.get("label_es") or "Sin datos todavía"))) if 'data-gwo-state=""' in text else text
        text = _replace_matches(text, re.compile(r'<(?P<tag>[A-Za-z0-9]+)\b[^>]*\bdata-gwo-state(?=\s|>)[^>]*>', re.I | re.S), html.escape(str(state.get("label_es") or "Sin datos todavía")))
        text = _replace_matches(text, re.compile(r'<(?P<tag>[A-Za-z0-9]+)\b[^>]*\bdata-gwo-updated(?=\s|>)[^>]*>', re.I | re.S), html.escape(format_checked_at(checked)))
        text = _replace_matches(text, re.compile(r'<(?P<tag>[A-Za-z0-9]+)\b[^>]*\bdata-gwo-confidence(?=\s|>)[^>]*>', re.I | re.S), html.escape(confidence))
        text = _replace_matches(text, re.compile(r'<(?P<tag>[A-Za-z0-9]+)\b[^>]*\bdata-gwo-confidence-note(?=\s|>)[^>]*>', re.I | re.S), html.escape(confidence_note))
        text = _replace_matches(text, re.compile(r'<(?P<tag>[A-Za-z0-9]+)\b[^>]*\bdata-gwo-summary(?=\s|>)[^>]*>', re.I | re.S), html.escape(str(state.get("summary_es") or "")))
        alert = state.get("alert_level") if isinstance(state.get("alert_level"), dict) else {}
        text = _replace_matches(text, re.compile(r'<(?P<tag>[A-Za-z0-9]+)\b[^>]*\bdata-gwo-alert-level(?=\s|>)[^>]*>', re.I | re.S), html.escape(str(alert.get("label_es") or "INFORMATIVO")))
        health_label = {"healthy": "SALUD CORRECTA", "degraded": "FRESCURA PARCIAL", "stale": "REVISAR FUENTES"}.get(str(health.get("overall")), "SIN DATOS")
        text = _replace_matches(text, re.compile(r'<(?P<tag>[A-Za-z0-9]+)\b[^>]*\bdata-gwo-health-overall(?=\s|>)[^>]*>', re.I | re.S), health_label)
        metrics = observatory.get("metrics") if isinstance(observatory.get("metrics"), dict) else {}
        for key, value in metrics.items():
            text = replace_attr(text, "data-gwo-metric", str(key), html.escape(str(value if value is not None else "—")))
        layers = state.get("layers") if isinstance(state.get("layers"), dict) else {}
        for key, item in layers.items():
            if not isinstance(item, dict):
                continue
            parent = re.compile(rf'<(?P<tag>[A-Za-z0-9]+)\b[^>]*\bdata-gwo-layer=["\']{re.escape(str(key))}["\'][^>]*>', re.I | re.S)
            match = parent.search(text)
            if match:
                # Replace the first layer-value after the matched parent.
                prefix, suffix = text[:match.end()], text[match.end():]
                suffix = _replace_matches(suffix, re.compile(r'<(?P<tag>[A-Za-z0-9]+)\b[^>]*\bdata-gwo-layer-value(?=\s|>)[^>]*>', re.I | re.S), html.escape(str(item.get("value") or "—")))
                text = prefix + suffix
        since = observatory.get("since_yesterday") if isinstance(observatory.get("since_yesterday"), dict) else {}
        text = _replace_matches(text, re.compile(r'<(?P<tag>[A-Za-z0-9]+)\b[^>]*\bdata-gwo-since-yesterday(?=\s|>)[^>]*>', re.I | re.S), html.escape(str(since.get("summary_es") or "Aún no hay una referencia diaria anterior comparable.")))
        text = _replace_matches(text, re.compile(r'<(?P<tag>[A-Za-z0-9]+)\b[^>]*\bdata-gwo-timeline(?=\s|>)[^>]*>', re.I | re.S), render_timeline(timeline))
    return text


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def is_skipped(path: Path) -> bool:
    rp = path.relative_to(ROOT)
    if any(part in SKIP_DIRS for part in rp.parts):
        return True
    if path.name in SKIP_NAMES:
        return True
    if path.suffix.lower() in SKIP_EXTS:
        return True
    if path.suffix.lower() == ".json":
        return True
    if path.name == "site.webmanifest":
        return False
    low = path.name.lower()
    if any(part in low for part in SENSITIVE_NAME_PARTS) and path.suffix.lower() not in {".html", ".css", ".js"}:
        return True
    return False


def discover_json_refs() -> set[str]:
    refs = set(PUBLIC_JSON_BASE)
    pattern = re.compile(r"[\"']([^\"']+\.json)(?:\?[^\"']*)?[\"']", re.I)
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".html", ".js", ".mjs"}:
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        base = path.parent
        for raw in pattern.findall(text):
            if raw.startswith(("http://", "https://")):
                continue
            candidate = (base / raw.split("?", 1)[0]).resolve()
            try:
                rr = candidate.relative_to(ROOT).as_posix()
            except ValueError:
                continue
            refs.add(rr)
    return refs


def build_runtime_bundle() -> tuple[str, dict[str, object]]:
    data: dict[str, object] = {}
    for rr in sorted(discover_json_refs()):
        path = ROOT / rr
        if not path.exists() or not path.is_file():
            continue
        low = rr.lower()
        if any(part in low for part in SENSITIVE_NAME_PARTS):
            continue
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        data[rr.lstrip("/")] = clean_obj(obj)

    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</script", "<\\/script")
    js = f"""(()=>{{'use strict';const D={payload};const F=window.fetch.bind(window);const key=(input)=>{{try{{const raw=typeof input==='string'?input:(input&&input.url)||'';const u=new URL(raw,location.href);if(u.origin!==location.origin)return null;return decodeURIComponent(u.pathname).replace(/^\\/+/, '');}}catch(_e){{return null;}}}};window.fetch=(input,init)=>{{const k=key(input);if(k&&Object.prototype.hasOwnProperty.call(D,k)){{return Promise.resolve(new Response(JSON.stringify(D[k]),{{status:200,headers:{{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'}}}}));}}return F(input,init);}};}})();"""
    digest = hashlib.sha256(js.encode("utf-8")).hexdigest()[:14]
    name = f"assets/gw-runtime-{digest}.js"
    target = OUT / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(js, encoding="utf-8")
    return "/" + name, data


def harden_html(text: str, runtime_src: str) -> str:
    # Remove implementation comments/markers from the public artifact.
    text = re.sub(r"<!--(?!\[if\b).*?-->", "", text, flags=re.I | re.S)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)

    head_bits = (
        '<meta name="referrer" content="strict-origin-when-cross-origin">'
        '<meta http-equiv="Content-Security-Policy" content="object-src \'none\'; base-uri \'self\'; upgrade-insecure-requests">'
        f'<script src="{runtime_src}"></script>'
    )
    if "<head>" in text:
        text = text.replace("<head>", "<head>" + head_bits, 1)
    elif "<head " in text:
        text = re.sub(r"(<head\b[^>]*>)", r"\1" + head_bits, text, count=1, flags=re.I)
    return text



def harden_xml(text: str) -> str:
    # Never advertise technical/source endpoints in sitemaps or feeds.
    text = re.sub(
        r"<url>\s*<loc>[^<]+\.(?:json|py|ya?ml|md|map)(?:\?[^<]*)?</loc>.*?</url>",
        "",
        text,
        flags=re.I | re.S,
    )
    return text

def copy_public(runtime_src: str, data: dict[str, object] | None = None) -> int:
    data = data or {}
    copied = 0
    for path in ROOT.rglob("*"):
        if not path.is_file() or is_skipped(path):
            continue
        rr = rel(path)
        if rr.startswith("_site/"):
            continue
        # Keep only web-distribution formats and special domain/index files.
        allowed = path.suffix.lower() in {
            ".html", ".htm", ".css", ".js", ".mjs", ".xml", ".svg", ".png", ".jpg",
            ".jpeg", ".webp", ".gif", ".ico", ".woff", ".woff2", ".ttf", ".otf", ".pdf",
            ".txt", ".webmanifest",
        } or path.name == "CNAME" or rr == "ope-audit.csv"
        if not allowed:
            continue
        if path.suffix.lower() == ".txt":
            # Public text files limited to web standards / IndexNow keys.
            if rr != "newsletter/latest.txt" and path.name not in {"robots.txt", "ads.txt", "humans.txt"} and not re.fullmatch(r"[0-9a-fA-F]{20,64}\.txt", path.name):
                continue

        dest = OUT / rr
        dest.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix.lower() in {".html", ".htm"}:
            text = path.read_text(encoding="utf-8")
            text = prerender_html(text, rr, data)
            dest.write_text(add_promotions(apply_policy(harden_html(text, runtime_src), rr), rr, "gibraltar"), encoding="utf-8")
        elif path.suffix.lower() in {".js", ".mjs", ".css"}:
            text = path.read_text(encoding="utf-8")
            text = re.sub(r"(?:/\*#|//#)\s*sourceMappingURL=.*?(?:\*/)?\s*$", "", text, flags=re.M)
            dest.write_text(text, encoding="utf-8")
        elif path.suffix.lower() == ".xml":
            dest.write_text(harden_xml(path.read_text(encoding="utf-8")), encoding="utf-8")
        else:
            shutil.copy2(path, dest)
        copied += 1
    return copied


def main() -> int:
    build_report(ROOT)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    runtime_src, data = build_runtime_bundle()
    copied = copy_public(runtime_src, data)
    # Rebuild the actual public inventory from final robots directives.
    import xml.etree.ElementTree as ET
    namespace = "http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("", namespace)
    sitemap = ET.Element("{" + namespace + "}urlset")
    for page in sorted(OUT.rglob("*.html")):
        if page.name == "404.html" or re.search(r'<meta\b[^>]*noindex', page.read_text(), re.I):
            continue
        node = ET.SubElement(sitemap, "{" + namespace + "}url")
        ET.SubElement(node, "{" + namespace + "}loc").text = "https://estrechogibraltar.com/" + page.relative_to(OUT).as_posix()
    ET.ElementTree(sitemap).write(OUT / "sitemap.xml", encoding="utf-8", xml_declaration=True)
    print(f"Build público seguro: {copied} archivos · {len(data)} conjuntos de datos encapsulados · 0 JSON públicos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
