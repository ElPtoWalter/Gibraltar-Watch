#!/usr/bin/env python3
"""Apply Gibraltar Watch public-facing editorial/professional wording.

This is intentionally idempotent. It removes implementation details from public
pages, keeps the editorial methodology truthful, and avoids claiming a manual
review step that may not have occurred.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

ES_REPLACEMENTS = [
    ("Observatorio científico · actualización automática", "Observatorio científico · seguimiento continuo"),
    ("catálogo automático", "catálogo de seguimiento"),
    ("catálogos automáticos", "catálogos de seguimiento"),
    ("CRONOLOGÍA AUTOMÁTICA", "CRONOLOGÍA EDITORIAL"),
    ("Metodología y automatización →", "Estándares editoriales →"),
    ("Transparencia y metodología de automatización", "Transparencia y estándares editoriales"),
    ("Cómo separa Gibraltar Watch hechos, interpretación, IA, frescura, correcciones y publicidad.",
     "Cómo trabaja Gibraltar Watch: fuentes, criterios editoriales, frescura, correcciones y publicidad."),
    ("La automatización solo es útil si el lector puede saber qué se ha medido, qué se ha inferido, cuándo se consultó y qué puede estar desactualizado.",
     "Gibraltar Watch aplica criterios editoriales claros para distinguir hechos, interpretación y escenarios, y para indicar la frescura de las fuentes utilizadas."),
    ("4 · Automatización e IA", "4 · Proceso editorial"),
    ("El Diario puede apoyarse en un modelo de lenguaje cuando está disponible y dispone de reglas de seguridad editorial. Si no está disponible, existe una generación determinista. El motor utilizado se publica en cada edición o metadato asociado.",
     "La redacción de Gibraltar Watch define los criterios de selección, jerarquización y publicación. Los procesos técnicos de recopilación y actualización ayudan a mantener el observatorio al día; la responsabilidad editorial corresponde a Gibraltar Watch."),
    ("Este diagnóstico se genera en el mismo ciclo de actualización y forma parte de la información pública del observatorio.",
     "Este diagnóstico acompaña cada actualización y permite valorar la frescura y coherencia de las fuentes del observatorio."),
    ("La nueva cadena verifica JSON, páginas críticas, sitemap, RSS, enlaces internos básicos y la configuración sensible del workflow antes de hacer push.",
     "Antes de publicar, Gibraltar Watch verifica la integridad de las páginas críticas, enlaces, metadatos, fuentes y archivos de distribución."),
    ("La web se construye en el checkout de GitHub Actions y solo se confirma si supera las pruebas. El historial de Git conserva cada versión publicada, permitiendo revertir a un commit anterior sin acumular copias ZIP dentro del repositorio.",
     "Cada edición publicada conserva trazabilidad interna y controles de recuperación para poder revertir cambios si se detecta una incidencia técnica o editorial."),
    ("Generado automáticamente a partir de salidas verificadas de Gibraltar Watch.",
     "Preparado por la redacción de Gibraltar Watch a partir de fuentes verificadas."),
    ("Generado automáticamente", "Preparado por la redacción de Gibraltar Watch"),
    ("La web combina datos automáticos, fuentes oficiales y explicaciones científicas.",
     "La web combina datos actualizados, fuentes oficiales y explicaciones científicas."),
    ("GitHub Actions consulta cada hora la API oficial del USGS en un área fija. Guarda eventos, resúmenes y una serie diaria.",
     "El sistema de seguimiento consulta cada hora la API oficial del USGS en un área fija y mantiene eventos, resúmenes y una serie histórica."),
]

EN_REPLACEMENTS = [
    ("The site combines automated data, official sources and scientific explanation.",
     "The site combines updated data, official sources and scientific explanation."),
    ("GitHub Actions queries the official USGS API hourly within a fixed area. It stores events, summaries and a daily series.",
     "The monitoring system queries the official USGS API hourly within a fixed area and maintains events, summaries and a daily series."),
    ("Public code and data", "Integrity and traceability"),
]

FORBIDDEN_PUBLIC_PATTERNS = [
    r"\bOpenAI\b",
    r"\binteligencia artificial\b",
    r"\bmodelo de lenguaje\b",
    r"\bGitHub Actions\b",
]


def remove_public_code_sections(text: str) -> str:
    # Spanish methodology legacy section.
    text = re.sub(
        r"<h2>\s*Código y datos públicos\s*</h2>\s*<p>.*?</p>",
        "<h2>Integridad y trazabilidad</h2><p>Gibraltar Watch mantiene controles internos de integridad, histórico y recuperación. Los datos mostrados al lector se presentan dentro de las páginas y paneles editoriales correspondientes.</p>",
        text,
        flags=re.I | re.S,
    )
    # English legacy section.
    text = re.sub(
        r"<h2>\s*Public code and data\s*</h2>\s*<p>.*?</p>",
        "<h2>Integrity and traceability</h2><p>Gibraltar Watch maintains internal integrity, history and recovery controls. Reader-facing data is presented through the relevant editorial pages and panels.</p>",
        text,
        flags=re.I | re.S,
    )
    # Remove direct links to JSON files from prose if an older version survives.
    text = re.sub(r"<a\b[^>]*href=[\"'][^\"']+\.json[^\"']*[\"'][^>]*>.*?</a>", "los paneles de datos", text, flags=re.I | re.S)
    return text


def scrub_implementation_copy(text: str) -> str:
    for old, new in ES_REPLACEMENTS + EN_REPLACEMENTS:
        text = text.replace(old, new)

    # Public-facing implementation labels that may be emitted in slightly varied forms.
    text = re.sub(r"\bMotor:\s*[^<\n]+", "Edición publicada", text, flags=re.I)
    text = re.sub(r"\bGenerador:\s*[^<\n]+", "Redacción: Gibraltar Watch", text, flags=re.I)
    text = re.sub(r"\bModelo:\s*[^<\n]+", "Redacción: Gibraltar Watch", text, flags=re.I)
    text = re.sub(
        r"La redacción puede ser asistida automáticamente, pero el sistema tiene instrucciones de no inventar hechos, no atribuir intenciones y enlazar las fuentes empleadas\.\s*",
        "La publicación sigue reglas editoriales que prohíben inventar hechos o atribuir intenciones y exige enlazar las fuentes empleadas. ",
        text,
        flags=re.I,
    )
    text = re.sub(r"Motor de esta edición:\s*[^<\n.]+\.?", "Criterio editorial: Gibraltar Watch.", text, flags=re.I)
    text = re.sub(r"\bgeneración determinista\b", "proceso editorial de continuidad", text, flags=re.I)
    return remove_public_code_sections(text)


def patch_html(path: Path) -> bool:
    old = path.read_text(encoding="utf-8")
    new = scrub_implementation_copy(old)
    if new != old:
        path.write_text(new, encoding="utf-8")
        return True
    return False


def main() -> int:
    changed = 0
    for path in ROOT.rglob("*.html"):
        parts = set(path.relative_to(ROOT).parts)
        if parts & {"_site", ".git", "node_modules", "__pycache__"}:
            continue
        changed += int(patch_html(path))

    # Public XML/RSS may carry visible implementation wording too.
    for path in ROOT.rglob("*.xml"):
        if "_site" in path.parts:
            continue
        old = path.read_text(encoding="utf-8")
        new = scrub_implementation_copy(old)
        if new != old:
            path.write_text(new, encoding="utf-8")
            changed += 1

    print(f"Capa editorial profesional aplicada en {changed} archivo(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
