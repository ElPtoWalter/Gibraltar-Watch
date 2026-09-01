#!/usr/bin/env python3
"""Build a hardened GitHub Pages artifact from the repository.

The published artifact intentionally excludes backend/source files and raw JSON
endpoints. JSON consumed by existing front-end code is bundled in-memory so old
fetch() calls keep working without publishing standalone .json resources.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path

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


def clean_obj(value):
    if isinstance(value, dict):
        return {k: clean_obj(v) for k, v in value.items() if k.lower() not in DROP_META_KEYS}
    if isinstance(value, list):
        return [clean_obj(v) for v in value]
    return value


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

def copy_public(runtime_src: str) -> int:
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
        } or path.name == "CNAME"
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
            dest.write_text(harden_html(text, runtime_src), encoding="utf-8")
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
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    runtime_src, data = build_runtime_bundle()
    copied = copy_public(runtime_src)
    print(f"Build público seguro: {copied} archivos · {len(data)} conjuntos de datos encapsulados · 0 JSON públicos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
