#!/usr/bin/env python3
"""Create/close GitHub Issues used as low-noise observatory notifications.

Uses only the GitHub Actions token and Python's standard library. Notification
failure is reported as a workflow warning but does not invalidate site data.
"""
from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
API = "https://api.github.com"


def request(method: str, path: str, payload=None):
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")
    if not token or not repo:
        raise RuntimeError("Faltan GH_TOKEN/GITHUB_REPOSITORY")
    url = f"{API}/repos/{repo}{path}"
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "GibraltarWatch-Automation/1.0",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=25) as response:
        raw = response.read()
        return json.loads(raw.decode("utf-8")) if raw else {}


def find_open_issue(title: str):
    issues = request("GET", "/issues?state=open&per_page=100")
    for issue in issues:
        if "pull_request" in issue:
            continue
        if issue.get("title") == title:
            return issue
    return None


def upsert(title: str, body: str) -> None:
    issue = find_open_issue(title)
    if issue:
        request("POST", f"/issues/{issue['number']}/comments", {"body": body})
        print(f"Aviso actualizado en issue #{issue['number']}.")
    else:
        created = request("POST", "/issues", {"title": title, "body": body})
        print(f"Aviso creado en issue #{created.get('number','?')}.")


def close(title: str, body: str) -> None:
    issue = find_open_issue(title)
    if not issue:
        print("No hay issue abierto que cerrar.")
        return
    request("POST", f"/issues/{issue['number']}/comments", {"body": body})
    request("PATCH", f"/issues/{issue['number']}", {"state": "closed"})
    print(f"Issue #{issue['number']} cerrado.")


def observatory() -> None:
    payload = json.loads((ROOT / "observatory.json").read_text(encoding="utf-8"))
    state = payload.get("state") or {}
    changes = payload.get("changes") or {}
    severity = int(state.get("severity", 0) or 0)
    changed = bool(changes.get("state_changed"))
    title = "🚨 Gibraltar Watch · alerta del observatorio"
    if changed and severity >= 3:
        alert = state.get("alert_level") or {}
        body = "\n".join([
            f"## {state.get('label_es','Cambio de estado')}",
            "",
            f"**Nivel de aviso:** {alert.get('label_es','—')}",
            f"**Confianza:** {state.get('confidence','—')}",
            f"**Generado:** {payload.get('generated_at','—')}",
            "",
            state.get("summary_es", ""),
            "",
            "Este aviso es una **señal editorial automatizada**, no un aviso oficial de navegación o seguridad. Debe verificarse con fuentes oficiales antes de publicar una afirmación extraordinaria.",
            "",
            "https://estrechogibraltar.com/situacion-actual.html",
        ])
        upsert(title, body)
    elif changed and severity < 3:
        close(title, f"El observatorio ha bajado a **{state.get('label_es','un nivel inferior')}**. Se cierra este aviso automático.\n\nhttps://estrechogibraltar.com/situacion-actual.html")
    else:
        print("Sin transición que requiera issue de alerta.")


def audit(status: str, detail: str) -> None:
    title = "🛠️ Gibraltar Watch · auditoría automática fallida"
    if status == "fail":
        body = "\n".join([
            "## La auditoría externa ha detectado un problema",
            "",
            detail or "La comprobación de disponibilidad/frescura no terminó correctamente.",
            "",
            f"Run: https://github.com/{os.getenv('GITHUB_REPOSITORY','')}/actions/runs/{os.getenv('GITHUB_RUN_ID','')}",
            "",
            "Este issue se cerrará automáticamente cuando una auditoría posterior vuelva a superar las comprobaciones.",
        ])
        upsert(title, body)
    else:
        close(title, "La auditoría externa vuelve a superar todas las comprobaciones. Cierre automático.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=["observatory", "audit"])
    parser.add_argument("--status", choices=["ok", "fail"], default="ok")
    parser.add_argument("--detail", default="")
    args = parser.parse_args()
    try:
        if args.kind == "observatory":
            observatory()
        else:
            audit(args.status, args.detail)
    except (RuntimeError, urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError, KeyError) as exc:
        print(f"::warning::No se pudo gestionar el issue automático: {exc}")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
