#!/usr/bin/env python3
# Gibraltar Watch TOP · instalador idempotente.
# Se ejecuta después de update_gibraltar.py.

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TODAY = "2026-07-17"

NEW_URLS = [
    ("parte-diario.html", "daily", "0.95"),
    ("en-daily-brief.html", "daily", "0.95"),
    ("analisis.html", "weekly", "0.90"),
    ("en-analysis.html", "weekly", "0.90"),
    ("que-significaria-cierre-estrecho-gibraltar.html", "monthly", "0.90"),
    ("en-what-would-closure-strait-of-gibraltar-mean.html", "monthly", "0.90"),
    ("por-que-45-mm-no-significa-cierre-gibraltar.html", "monthly", "0.90"),
    ("en-why-4-5-mm-does-not-mean-gibraltar-is-closing.html", "monthly", "0.90"),
    ("impacto-cierre-gibraltar-comercio-europa-africa.html", "monthly", "0.90"),
    ("en-impact-gibraltar-closure-trade-europe-africa.html", "monthly", "0.90"),
    ("como-funciona-intercambio-agua-gibraltar.html", "monthly", "0.90"),
    ("en-how-water-exchange-works-strait-of-gibraltar.html", "monthly", "0.90"),
    ("politica-editorial.html", "yearly", "0.45"),
    ("en-editorial-policy.html", "yearly", "0.45"),
    ("media-kit.html", "monthly", "0.45"),
    ("en-media-kit.html", "monthly", "0.45"),
    ("contacto.html", "yearly", "0.45"),
    ("en-contact.html", "yearly", "0.45"),
]

CONTENT_PAGES_ES = [
    "sismicidad.html", "trafico.html", "importancia.html",
    "geologia.html", "futuro.html", "tunel.html"
]
CONTENT_PAGES_EN = [
    "en-seismicity.html", "en-traffic.html", "en-importance.html",
    "en-geology.html", "en-future.html", "en-tunnel.html"
]

HOME_BRIEF_ES = r'''<!-- GT_HOME_BRIEF_START -->
<section class="gt-brief-home gt-home-upgrade gt-shell" data-gibraltar-brief>
  <div>
    <span class="gt-eyebrow">Parte científico diario</span>
    <h2>La situación esencial, actualizada automáticamente</h2>
    <p>Un resumen prudente de la sismicidad regional, la salud de los datos y las conclusiones que sí pueden sostenerse. No convierte cada terremoto en una predicción ni confunde convergencia tectónica con cierre del canal.</p>
    <div class="gt-brief-metrics">
      <div><span>Eventos · 30 días</span><strong id="homeBriefSeismic">—</strong></div>
      <div><span>Calidad de datos</span><strong id="homeBriefFreshness">—</strong></div>
      <div><span>Conclusión</span><strong id="homeBriefConclusion">—</strong></div>
    </div>
  </div>
  <aside class="gt-brief-aside">
    <strong>Registro diario auditable</strong>
    <p>El parte se genera desde <code>seismicity.json</code>, conserva un archivo histórico y enlaza la metodología y las fuentes.</p>
    <a class="gt-button primary" href="parte-diario.html">Abrir parte diario</a>
  </aside>
</section>
<!-- GT_HOME_BRIEF_END -->'''

HOME_BRIEF_EN = r'''<!-- GT_HOME_BRIEF_START -->
<section class="gt-brief-home gt-home-upgrade gt-shell" data-gibraltar-brief>
  <div>
    <span class="gt-eyebrow">Daily scientific brief</span>
    <h2>The essential situation, updated automatically</h2>
    <p>A cautious summary of regional seismicity, data health and the conclusions that can actually be supported. It does not turn every earthquake into a prediction or confuse plate convergence with channel closure.</p>
    <div class="gt-brief-metrics">
      <div><span>Events · 30 days</span><strong id="homeBriefSeismic">—</strong></div>
      <div><span>Data quality</span><strong id="homeBriefFreshness">—</strong></div>
      <div><span>Conclusion</span><strong id="homeBriefConclusion">—</strong></div>
    </div>
  </div>
  <aside class="gt-brief-aside">
    <strong>Auditable daily record</strong>
    <p>The brief is generated from <code>seismicity.json</code>, keeps a historical archive and links to methodology and sources.</p>
    <a class="gt-button primary" href="en-daily-brief.html">Open daily brief</a>
  </aside>
</section>
<!-- GT_HOME_BRIEF_END -->'''

HOME_ANALYSIS_ES = r'''<!-- GT_HOME_ANALYSIS_START -->
<section class="gt-home-analysis gt-shell">
  <div class="gt-section-head">
    <div><span class="gt-eyebrow">Análisis y contexto</span><h2>Entender antes de concluir</h2></div>
    <p>Guías editoriales para separar hechos, inferencias, escenarios y titulares engañosos.</p>
  </div>
  <div class="gt-grid-3">
    <a class="gt-card is-new" href="que-significaria-cierre-estrecho-gibraltar.html"><small>Navegación y riesgo</small><h3>Qué significaría realmente un cierre del Estrecho</h3><p>Cierre físico, interrupción operativa, restricciones y escenarios que no deben mezclarse.</p><b>Leer análisis →</b></a>
    <a class="gt-card is-new" href="por-que-45-mm-no-significa-cierre-gibraltar.html"><small>Tectónica</small><h3>Por qué 4,5 mm/año no significa que el canal se cierre</h3><p>Vectores de placa, deformación distribuida y el error de dividir anchura entre convergencia.</p><b>Leer análisis →</b></a>
    <a class="gt-card is-new" href="impacto-cierre-gibraltar-comercio-europa-africa.html"><small>Comercio y logística</small><h3>Qué ocurriría si el tránsito quedara interrumpido</h3><p>Puertos, cadenas logísticas, ferris, energía y conexión Atlántico–Mediterráneo.</p><b>Leer análisis →</b></a>
    <a class="gt-card" href="como-funciona-intercambio-agua-gibraltar.html"><small>Oceanografía</small><h3>Cómo funciona el intercambio de agua en dos capas</h3><p>Entrada atlántica superficial, salida mediterránea profunda y Umbral de Camarinal.</p><b>Leer análisis →</b></a>
    <a class="gt-card" href="futuro.html"><small>Escala geológica</small><h3>¿Podría cerrarse algún día?</h3><p>Qué sabe la ciencia, qué no puede predecir y por qué no existe un año de cierre.</p><b>Abrir guía →</b></a>
    <a class="gt-card" href="tunel.html"><small>Enlace fijo</small><h3>Estado real del túnel España–Marruecos</h3><p>Campañas geológicas, incertidumbres del fondo y diferencia entre estudio y obra.</p><b>Abrir guía →</b></a>
  </div>
  <div class="gt-actions"><a class="gt-button" href="analisis.html">Ver todos los análisis</a></div>
</section>
<!-- GT_HOME_ANALYSIS_END -->'''

HOME_ANALYSIS_EN = r'''<!-- GT_HOME_ANALYSIS_START -->
<section class="gt-home-analysis gt-shell">
  <div class="gt-section-head">
    <div><span class="gt-eyebrow">Analysis and context</span><h2>Understand before concluding</h2></div>
    <p>Editorial guides separating facts, inferences, scenarios and misleading headlines.</p>
  </div>
  <div class="gt-grid-3">
    <a class="gt-card is-new" href="en-what-would-closure-strait-of-gibraltar-mean.html"><small>Navigation and risk</small><h3>What would closure of the Strait really mean?</h3><p>Physical closure, operational interruption, restrictions and scenarios that should not be conflated.</p><b>Read analysis →</b></a>
    <a class="gt-card is-new" href="en-why-4-5-mm-does-not-mean-gibraltar-is-closing.html"><small>Tectonics</small><h3>Why 4.5 mm per year does not mean the channel is closing</h3><p>Plate vectors, distributed deformation and the error of dividing width by convergence.</p><b>Read analysis →</b></a>
    <a class="gt-card is-new" href="en-impact-gibraltar-closure-trade-europe-africa.html"><small>Trade and logistics</small><h3>What if transit were interrupted?</h3><p>Ports, supply chains, ferries, energy and the Atlantic–Mediterranean connection.</p><b>Read analysis →</b></a>
    <a class="gt-card" href="en-how-water-exchange-works-strait-of-gibraltar.html"><small>Oceanography</small><h3>How the two-layer water exchange works</h3><p>Surface Atlantic inflow, deep Mediterranean outflow and the Camarinal Sill.</p><b>Read analysis →</b></a>
    <a class="gt-card" href="en-future.html"><small>Geological timescale</small><h3>Could it ever close?</h3><p>What science knows, what it cannot forecast and why there is no closure year.</p><b>Open guide →</b></a>
    <a class="gt-card" href="en-tunnel.html"><small>Fixed link</small><h3>Real status of the Spain–Morocco tunnel</h3><p>Geological campaigns, seabed uncertainty and the difference between study and construction.</p><b>Open guide →</b></a>
  </div>
  <div class="gt-actions"><a class="gt-button" href="en-analysis.html">View all analysis</a></div>
</section>
<!-- GT_HOME_ANALYSIS_END -->'''

TRUST_ES = r'''<!-- GT_TRUST_START -->
<section class="gt-trust-strip gt-shell">
  <div><small>Fuentes</small><strong>Oficiales y científicas</strong></div>
  <div><small>Datos</small><strong>USGS + contraste IGN</strong></div>
  <div><small>Interpretación</small><strong>Sin predicciones sísmicas</strong></div>
  <div><small>Correcciones</small><strong>Canal editorial abierto</strong></div>
</section>
<!-- GT_TRUST_END -->'''

TRUST_EN = r'''<!-- GT_TRUST_START -->
<section class="gt-trust-strip gt-shell">
  <div><small>Sources</small><strong>Official and scientific</strong></div>
  <div><small>Data</small><strong>USGS + IGN cross-check</strong></div>
  <div><small>Interpretation</small><strong>No earthquake predictions</strong></div>
  <div><small>Corrections</small><strong>Open editorial channel</strong></div>
</section>
<!-- GT_TRUST_END -->'''


def stable_write(path: Path, text: str) -> None:
    previous = path.read_text(encoding="utf-8") if path.exists() else None
    if previous != text:
        path.write_text(text, encoding="utf-8")


def is_english(text: str) -> bool:
    return bool(re.search(r'<html\b[^>]*\blang=["\']en(?:-[^"\']+)?["\']', text, re.I))


def ensure_asset(text: str, token: str, tag: str) -> str:
    if token in text:
        return text
    return text.replace("</head>", f"{tag}\n</head>", 1)


def patch_nav(text: str, english: bool) -> str:
    brief_href = "en-daily-brief.html" if english else "parte-diario.html"
    brief_label = "Daily brief" if english else "Parte diario"
    analysis_href = "en-analysis.html" if english else "analisis.html"
    analysis_label = "Analysis" if english else "Análisis"
    seismic_href = "en-seismicity.html" if english else "sismicidad.html"
    method_href = "en-methodology.html" if english else "metodologia.html"

    nav_pattern = re.compile(
        r'(<nav\b[^>]*class=["\'][^"\']*site-nav[^"\']*["\'][^>]*>)(.*?)(</nav>)',
        re.I | re.S
    )

    def repl(match: re.Match[str]) -> str:
        inner = match.group(2)
        if brief_href not in inner:
            seismic = re.compile(
                rf'(<a\b[^>]*href=["\']{re.escape(seismic_href)}["\'][^>]*>.*?</a>)',
                re.I | re.S
            )
            if seismic.search(inner):
                inner = seismic.sub(rf'\1<a href="{brief_href}">{brief_label}</a>', inner, count=1)
            else:
                inner += f'<a href="{brief_href}">{brief_label}</a>'
        if analysis_href not in inner:
            method = re.compile(
                rf'(<a\b[^>]*href=["\']{re.escape(method_href)}["\'][^>]*>.*?</a>)',
                re.I | re.S
            )
            if method.search(inner):
                inner = method.sub(rf'<a href="{analysis_href}">{analysis_label}</a>\1', inner, count=1)
            else:
                inner += f'<a href="{analysis_href}">{analysis_label}</a>'
        return match.group(1) + inner + match.group(3)

    return nav_pattern.sub(repl, text, count=1)


def patch_footer(text: str, english: bool) -> str:
    if "GT_FOOTER_LINKS" in text:
        return text
    block = (
        '<span class="gt-footer-extra" data-upgrade="GT_FOOTER_LINKS">'
        '<a href="en-daily-brief.html">Daily brief</a>'
        '<a href="en-analysis.html">Analysis</a>'
        '<a href="en-editorial-policy.html">Editorial policy</a>'
        '<a href="en-media-kit.html">Media kit</a>'
        '</span>'
        if english else
        '<span class="gt-footer-extra" data-upgrade="GT_FOOTER_LINKS">'
        '<a href="parte-diario.html">Parte diario</a>'
        '<a href="analisis.html">Análisis</a>'
        '<a href="politica-editorial.html">Política editorial</a>'
        '<a href="media-kit.html">Media kit</a>'
        '</span>'
    )
    footer = re.search(r'<footer\b.*?</footer>', text, re.I | re.S)
    if footer:
        fragment = footer.group(0).replace("</footer>", block + "</footer>", 1)
        return text[:footer.start()] + fragment + text[footer.end():]
    return text


def remove_marked(text: str, start: str, end: str) -> str:
    return re.sub(re.escape(start) + r'.*?' + re.escape(end), "", text, flags=re.I | re.S)


def insert_after_dashboard(text: str, block: str) -> str:
    dashboard = re.search(
        r'<section\b(?=[^>]*(?:class=["\'][^"\']*dashboard[^"\']*["\']|id=["\']panel["\']))[^>]*>.*?</section>',
        text, re.I | re.S
    )
    if dashboard:
        return text[:dashboard.end()] + "\n" + block + text[dashboard.end():]
    hero = re.search(
        r'<section\b[^>]*class=["\'][^"\']*home-hero[^"\']*["\'][^>]*>.*?</section>',
        text, re.I | re.S
    )
    if hero:
        return text[:hero.end()] + "\n" + block + text[hero.end():]
    return text.replace("</main>", block + "\n</main>", 1)


def insert_before_faq(text: str, block: str) -> str:
    faq = re.search(
        r'<section\b[^>]*class=["\'][^"\']*faq-section[^"\']*["\'][^>]*>',
        text, re.I
    )
    if faq:
        return text[:faq.start()] + block + "\n" + text[faq.start():]
    return text.replace("</main>", block + "\n</main>", 1)


def patch_home(path: Path, english: bool) -> None:
    text = path.read_text(encoding="utf-8")
    text = remove_marked(text, "<!-- GT_HOME_BRIEF_START -->", "<!-- GT_HOME_BRIEF_END -->")
    text = remove_marked(text, "<!-- GT_HOME_ANALYSIS_START -->", "<!-- GT_HOME_ANALYSIS_END -->")
    text = remove_marked(text, "<!-- GT_TRUST_START -->", "<!-- GT_TRUST_END -->")
    text = insert_after_dashboard(text, HOME_BRIEF_EN if english else HOME_BRIEF_ES)
    text = insert_before_faq(
        text,
        (HOME_ANALYSIS_EN if english else HOME_ANALYSIS_ES)
        + "\n"
        + (TRUST_EN if english else TRUST_ES)
    )
    stable_write(path, text)


def patch_editorial_record(path: Path, english: bool) -> None:
    text = path.read_text(encoding="utf-8")
    if "GT_EDITORIAL_RECORD" in text or "</main>" not in text:
        return
    block = (
        r'''<!-- GT_EDITORIAL_RECORD -->
<section class="gt-editorial-record gt-shell">
  <span class="gt-eyebrow">Editorial record</span><h2>Traceability and corrections</h2>
  <dl><dt>Author</dt><dd>Gibraltar Watch Editorial Team</dd><dt>Review</dt><dd>Updated when source data or official project information changes materially.</dd><dt>Standard</dt><dd>Facts, interpretations and scenarios are separated. Seismic activity is never presented as a prediction.</dd><dt>Corrections</dt><dd><a href="en-contact.html">Submit a documented correction</a>.</dd></dl>
</section>'''
        if english else
        r'''<!-- GT_EDITORIAL_RECORD -->
<section class="gt-editorial-record gt-shell">
  <span class="gt-eyebrow">Ficha editorial</span><h2>Trazabilidad y correcciones</h2>
  <dl><dt>Autoría</dt><dd>Equipo editorial de Gibraltar Watch</dd><dt>Revisión</dt><dd>Se actualiza cuando cambian materialmente los datos fuente o la información oficial del proyecto.</dd><dt>Criterio</dt><dd>Se separan hechos, interpretación y escenarios. La sismicidad nunca se presenta como predicción.</dd><dt>Correcciones</dt><dd><a href="contacto.html">Enviar una corrección documentada</a>.</dd></dl>
</section>'''
    )
    stable_write(path, text.replace("</main>", block + "\n</main>", 1))


def update_sitemap() -> None:
    path = ROOT / "sitemap.xml"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    blocks: list[str] = []
    for rel, freq, priority in NEW_URLS:
        absolute = f"https://estrechogibraltar.com/{rel}"
        if absolute in text:
            continue
        blocks.append(
            "  <url>\n"
            f"    <loc>{absolute}</loc>\n"
            f"    <lastmod>{TODAY}</lastmod>\n"
            f"    <changefreq>{freq}</changefreq>\n"
            f"    <priority>{priority}</priority>\n"
            "  </url>\n"
        )
    if blocks and "</urlset>" in text:
        stable_write(path, text.replace("</urlset>", "".join(blocks) + "</urlset>", 1))


def update_robots() -> None:
    path = ROOT / "robots.txt"
    text = path.read_text(encoding="utf-8") if path.exists() else "User-agent: *\nAllow: /\n"
    sitemap_line = "Sitemap: https://estrechogibraltar.com/sitemap.xml"
    if sitemap_line not in text:
        text = text.rstrip() + "\n" + sitemap_line + "\n"
    stable_write(path, text)


def update_llms() -> None:
    path = ROOT / "llms.txt"
    marker = "## Gibraltar Watch TOP"
    text = path.read_text(encoding="utf-8") if path.exists() else "# Gibraltar Watch\n"
    if marker not in text:
        text = (
            text.rstrip()
            + "\n\n## Gibraltar Watch TOP\n"
            + "- Parte científico: https://estrechogibraltar.com/parte-diario.html\n"
            + "- Daily scientific brief: https://estrechogibraltar.com/en-daily-brief.html\n"
            + "- Análisis: https://estrechogibraltar.com/analisis.html\n"
            + "- Analysis: https://estrechogibraltar.com/en-analysis.html\n"
            + "- Metodología: https://estrechogibraltar.com/metodologia.html\n"
            + "- Fuentes: https://estrechogibraltar.com/fuentes.html\n"
            + "- Datos sísmicos: https://estrechogibraltar.com/seismicity.json\n"
        )
    stable_write(path, text)


def main() -> int:
    stable_write(ROOT / ".nojekyll", "#\n")

    for path in ROOT.glob("*.html"):
        text = path.read_text(encoding="utf-8")
        english = is_english(text)
        text = ensure_asset(
            text, "gibraltar-top.css",
            '<link href="gibraltar-top.css" rel="stylesheet"/>'
        )
        text = ensure_asset(
            text, "gibraltar-top.js",
            '<script defer src="gibraltar-top.js"></script>'
        )
        text = patch_nav(text, english)
        text = patch_footer(text, english)
        stable_write(path, text)

    for name in ("index.html", "en.html"):
        path = ROOT / name
        if path.exists():
            patch_home(path, name == "en.html")

    for name in CONTENT_PAGES_ES:
        path = ROOT / name
        if path.exists():
            patch_editorial_record(path, False)
    for name in CONTENT_PAGES_EN:
        path = ROOT / name
        if path.exists():
            patch_editorial_record(path, True)

    update_sitemap()
    update_robots()
    update_llms()
    print("Gibraltar Watch TOP instalado de forma idempotente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
