#!/usr/bin/env python3
"""Independent live-site smoke test for the hardened public deployment."""
from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from xml.etree import ElementTree as ET

UA = "GibraltarWatch-Audit/2.0"


def request(url: str, timeout: int = 25) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def get200(url: str) -> bytes:
    status, body = request(url)
    if status != 200:
        raise RuntimeError(f"HTTP {status}: {url}")
    return body


def extract_runtime(home: str, base: str) -> dict:
    m = re.search(r'<script\b[^>]*src=["\']([^"\']*gw-runtime-[^"\']+\.js)["\']', home, re.I)
    if not m:
        raise RuntimeError("la portada no referencia el runtime público endurecido")
    src = m.group(1)
    if src.startswith("http"):
        url = src
    elif src.startswith("/"):
        from urllib.parse import urlsplit
        parts = urlsplit(base)
        url = f"{parts.scheme}://{parts.netloc}{src}"
    else:
        url = base + src
    js = get200(url).decode("utf-8", "replace")
    m2 = re.search(r"const D=(\{.*?\});const F=", js, re.S)
    if not m2:
        raise RuntimeError("runtime sin paquete de datos verificable")
    return json.loads(m2.group(1))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", default="https://estrechogibraltar.com/")
    p.add_argument("--max-age-hours", type=float, default=12)
    a = p.parse_args()
    base = a.base_url.rstrip("/") + "/"

    urls = ["", "situacion-actual.html", "datos.html", "mapa-estrategico.html", "transparencia.html", "diario/", "sitemap.xml", "observatory-feed.xml"]
    errors: list[str] = []
    blobs: dict[str, bytes] = {}
    for rel in urls:
        try:
            blobs[rel] = get200(base + rel)
        except Exception as e:
            errors.append(f'{rel or "home"}: {e}')

    data = {}
    try:
        home = blobs[""].decode("utf-8", "replace")
        data = extract_runtime(home, base)
        forbidden = [r"\bOpenAI\b", r"\binteligencia artificial\b", r"\bGitHub Actions\b", r"Generado automáticamente"]
        for pat in forbidden:
            if re.search(pat, home, re.I):
                errors.append(f"La portada contiene texto técnico no permitido: {pat}")
    except Exception as e:
        errors.append(f"runtime público no verificable: {e}")

    try:
        health = data["health.json"]
        stamp = datetime.fromisoformat(health["generated_at"].replace("Z", "+00:00")).astimezone(timezone.utc)
        age = (datetime.now(timezone.utc) - stamp).total_seconds() / 3600
        if age > a.max_age_hours:
            errors.append(f"estado de salud tiene {age:.1f} h de antigüedad")
        if health.get("overall") == "stale":
            print("::warning::El sitio responde, pero el diagnóstico marca fuentes desactualizadas.")
    except Exception as e:
        errors.append(f"estado de salud no verificable: {e}")

    try:
        obs = data["observatory.json"]
        if (obs.get("state") or {}).get("code") not in {"normal", "watch", "reinforced_watch", "high_watch", "operational_alert"}:
            errors.append("estado editorial inválido")
    except Exception as e:
        errors.append(f"estado editorial no verificable: {e}")

    for rel in ["sitemap.xml", "observatory-feed.xml"]:
        try:
            ET.fromstring(blobs[rel])
        except Exception as e:
            errors.append(f"{rel} XML inválido: {e}")

    # Raw implementation/data endpoints must no longer be public.
    for rel in ["observatory.json", "health.json", "timeline.json", ".github/workflows/update-gibraltar.yml", "update_observatory.py"]:
        status, _ = request(base + rel)
        if status == 200:
            errors.append(f"Ruta técnica expuesta públicamente: /{rel}")

    if errors:
        for x in errors:
            print(f"::error::{x}")
        return 1
    print("SMOKE OK · web operativa, datos encapsulados y rutas técnicas no publicadas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
