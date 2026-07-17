#!/usr/bin/env python3
from __future__ import annotations
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOST = "estrechogibraltar.com"
KEY = "6a34c88f59d8939be9f2b8f504a2334c"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"
ENDPOINT = "https://api.indexnow.org/indexnow"

def urls() -> list[str]:
    sitemap = ROOT / "sitemap.xml"
    if not sitemap.exists():
        return [f"https://{HOST}/"]
    text = sitemap.read_text(encoding="utf-8")
    values = re.findall(r"<loc>\s*(https://estrechogibraltar\.com/[^<]*)\s*</loc>", text)
    return list(dict.fromkeys(values))[:10000]

def main() -> int:
    payload = json.dumps({
        "host": HOST,
        "key": KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": urls()
    }).encode("utf-8")
    request = urllib.request.Request(
        ENDPOINT, data=payload, method="POST",
        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": "GibraltarWatch/2.0"}
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                print(f"IndexNow HTTP {response.status} · URLs: {len(urls())}")
                return 0
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            if attempt == 2:
                print(f"IndexNow no disponible: {error}")
                return 0
            time.sleep(2 ** attempt)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
