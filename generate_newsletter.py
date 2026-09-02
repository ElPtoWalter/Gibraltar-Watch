#!/usr/bin/env python3
"""Generate a provider-agnostic daily newsletter preview from verified outputs.

No email addresses are stored here. Sending/subscription remains disabled until
an external mailing endpoint is explicitly configured in gw-monetization-config.js.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "newsletter"


def load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def n(value) -> str:
    try:
        return f"{int(value):,}".replace(",", ".")
    except Exception:
        return "—"


def main() -> int:
    obs = load(ROOT / "observatory.json", {})
    diary = load(ROOT / "diario" / "latest.json", {})
    state = obs.get("state") or {}
    metrics = obs.get("metrics") or {}
    OUT.mkdir(exist_ok=True)

    date_label = diary.get("date_label") or diary.get("date") or "Última edición"
    headline = diary.get("headline") or "El Estrecho en 2 minutos"
    summary = diary.get("summary") or state.get("summary_es") or "Consulta la última lectura del observatorio."
    diary_slug = diary.get("slug") or "index.html"

    plain = "\n".join([
        f"GIBRALTAR WATCH · EL ESTRECHO EN 2 MINUTOS · {date_label}",
        "",
        headline,
        summary,
        "",
        f"Estado: {state.get('label_es','—')} · Aviso: {(state.get('alert_level') or {}).get('label_es','—')} · Confianza: {state.get('confidence','—')}",
        f"Noticias 24 h: {n(metrics.get('news_24h'))}",
        f"Sismos 7 d: {n(metrics.get('seismic_7d'))}",
        f"OPE, pasajeros último parte: {n(metrics.get('ope_passengers_day'))}",
        "",
        f"Diario: https://estrechogibraltar.com/diario/{diary_slug}",
        "Situación actual: https://estrechogibraltar.com/situacion-actual.html",
        "Datos: https://estrechogibraltar.com/datos.html",
        "",
        "Gibraltar Watch separa hechos, interpretación y escenarios. Los avisos oficiales prevalecen para navegación, seguridad y protección civil.",
    ]) + "\n"

    page = f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,follow"><title>{html.escape(headline)}</title></head><body style="margin:0;background:#f3efe5;color:#151a1f;font-family:Arial,sans-serif"><main style="max-width:680px;margin:auto;padding:32px 20px"><p style="font-size:12px;letter-spacing:.14em;font-weight:700">GIBRALTAR WATCH · EL ESTRECHO EN 2 MINUTOS</p><h1 style="font-family:Georgia,serif;font-size:36px;line-height:1.06">{html.escape(headline)}</h1><p style="font-size:18px;line-height:1.6">{html.escape(summary)}</p><div style="padding:18px;border:1px solid #ccd2d5;border-radius:16px;background:#fff"><b>{html.escape(state.get('label_es','—'))}</b><p style="margin:8px 0 0">Aviso: {html.escape((state.get('alert_level') or {}).get('label_es','—'))} · Confianza: {html.escape(state.get('confidence','—'))}</p></div><table role="presentation" style="width:100%;margin:22px 0;border-collapse:collapse"><tr><td style="padding:12px;border-bottom:1px solid #ccd2d5">Noticias · 24 h</td><td style="padding:12px;text-align:right;border-bottom:1px solid #ccd2d5"><b>{n(metrics.get('news_24h'))}</b></td></tr><tr><td style="padding:12px;border-bottom:1px solid #ccd2d5">Sismos · 7 d</td><td style="padding:12px;text-align:right;border-bottom:1px solid #ccd2d5"><b>{n(metrics.get('seismic_7d'))}</b></td></tr><tr><td style="padding:12px;border-bottom:1px solid #ccd2d5">OPE · pasajeros</td><td style="padding:12px;text-align:right;border-bottom:1px solid #ccd2d5"><b>{n(metrics.get('ope_passengers_day'))}</b></td></tr></table><p><a href="https://estrechogibraltar.com/diario/{html.escape(diary_slug)}">Leer el Diario del Estrecho →</a></p><p><a href="https://estrechogibraltar.com/situacion-actual.html">Abrir situación actual →</a></p><hr style="border:0;border-top:1px solid #ccd2d5;margin:30px 0"><small>Compuesto automáticamente a partir de los datos del monitor; no implica verificación humana individual. La fecha del informe OPE no equivale a la fecha de consulta.</small></main></body></html>'''

    latest = {
        "date": diary.get("date"),
        "date_label": date_label,
        "headline": headline,
        "summary": summary,
        "state": state.get("label_es"),
        "alert_level": (state.get("alert_level") or {}).get("label_es"),
        "confidence": state.get("confidence"),
        "diary_url": f"https://estrechogibraltar.com/diario/{diary_slug}",
    }
    (OUT / "latest.txt").write_text(plain, encoding="utf-8")
    (OUT / "latest.html").write_text(page, encoding="utf-8")
    (OUT / "latest.json").write_text(json.dumps(latest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Boletín diario generado en newsletter/latest.{html,txt,json}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
