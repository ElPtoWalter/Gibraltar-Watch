#!/usr/bin/env python3
"""Install the additive Observatory vNext UI without replacing the existing site.

Run this AFTER all previous Gibraltar Watch installers and after install_diario.py.
The script is idempotent: marker blocks are replaced instead of duplicated.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
VERSION = "20260810-1"
CSS = f'<link rel="stylesheet" href="gw-observatory.css?v={VERSION}">' 
JS = f'<script defer src="gw-observatory.js?v={VERSION}"></script>'
RSS = '<link rel="alternate" type="application/rss+xml" title="Gibraltar Watch · Observatorio" href="observatory-feed.xml">'
START_LIVE = '<!-- GWO_LIVE_START -->'
END_LIVE = '<!-- GWO_LIVE_END -->'
START_TIMELINE = '<!-- GWO_TIMELINE_START -->'
END_TIMELINE = '<!-- GWO_TIMELINE_END -->'
START_DETAIL = '<!-- GWO_DETAIL_START -->'
END_DETAIL = '<!-- GWO_DETAIL_END -->'
START_HEALTH = '<!-- GWO_HEALTH_START -->'
END_HEALTH = '<!-- GWO_HEALTH_END -->'
START_FOOT = '<!-- GWO_FOOTER_LINKS_START -->'
END_FOOT = '<!-- GWO_FOOTER_LINKS_END -->'

LIVE = f'''{START_LIVE}
<section class="gwo-livebar gwo-shell" aria-label="Estado resumido del observatorio">
  <div class="gwo-livebar-inner">
    <div class="gwo-state" data-gwo-state-box><span class="gwo-state-dot" aria-hidden="true"></span><div class="gwo-state-copy"><small>ESTADO DEL ESTRECHO</small><b data-gwo-state>Cargando…</b><small data-gwo-updated>Consultando última actualización</small></div></div>
    <div class="gwo-live-metric"><span>Confianza</span><strong data-gwo-confidence>—</strong><em>lectura editorial</em></div>
    <div class="gwo-live-metric"><span>Noticias · 24 h</span><strong data-gwo-metric="news_24h">—</strong><em>referencias</em></div>
    <div class="gwo-live-metric"><span>Sismos · 7 d</span><strong data-gwo-metric="seismic_7d">—</strong><em>catálogo regional</em></div>
    <div class="gwo-live-metric"><span>Fuentes</span><strong class="gwo-chip" data-gwo-health-overall>—</strong><em>frescura e integridad</em></div>
  </div>
</section>
{END_LIVE}'''

HOME_TIMELINE = f'''{START_TIMELINE}
<section class="gwo-panel gwo-shell" aria-labelledby="gwo-home-timeline-title">
  <div class="gwo-panel-head"><div><div class="gwo-kicker">CRONOLOGÍA AUTOMÁTICA</div><h2 id="gwo-home-timeline-title">Qué ha cambiado</h2></div><div><p>Solo registra cambios materiales, nuevos partes, nuevas ediciones y señales estadísticas. No convierte cada titular en una alerta.</p><a href="datos.html">Abrir datos e histórico →</a></div></div>
  <div class="gwo-timeline" data-gwo-timeline data-limit="5"></div>
</section>
{END_TIMELINE}'''

DETAIL = f'''{START_DETAIL}
<section class="gwo-panel gwo-shell" aria-labelledby="gwo-current-title">
  <div class="gwo-panel-head"><div><div class="gwo-kicker">LECTURA CONSOLIDADA</div><h2 id="gwo-current-title">Estado del Estrecho</h2></div><p>El nivel combina las capas editoriales ya verificadas por Gibraltar Watch y reduce confianza si las fuentes pierden frescura.</p></div>
  <div class="gwo-state-hero">
    <article class="gwo-state-main" data-gwo-state-box><div class="gwo-kicker">NIVEL GENERAL</div><strong data-gwo-state>—</strong><p data-gwo-summary>Cargando lectura consolidada…</p><div class="gwo-meta-row"><span class="gwo-chip">Aviso: <b data-gwo-alert-level>—</b></span><span class="gwo-chip">Confianza: <b data-gwo-confidence>—</b></span><span class="gwo-chip" data-gwo-health-overall>—</span><span class="gwo-chip">Actualizado <b data-gwo-updated>—</b></span></div><div class="gwo-alert-actions"><button class="button" type="button" data-gwo-enable-alerts>Activar alertas en este navegador</button><small data-gwo-alert-status>Solo avisaremos de cambios de nivel mientras este navegador esté abierto.</small></div></article>
    <aside class="gwo-state-side"><div class="gwo-kicker">CAPAS</div><div class="gwo-layer-list"><div class="gwo-layer" data-gwo-layer="maritime"><i></i><b>Tráfico marítimo</b><span data-gwo-layer-value>—</span></div><div class="gwo-layer" data-gwo-layer="border"><i></i><b>Ceuta y Melilla</b><span data-gwo-layer-value>—</span></div><div class="gwo-layer" data-gwo-layer="bilateral"><i></i><b>España–Marruecos</b><span data-gwo-layer-value>—</span></div><div class="gwo-layer" data-gwo-layer="security"><i></i><b>Seguridad</b><span data-gwo-layer-value>—</span></div></div></aside>
  </div>
  <p class="gwo-source-note" style="margin-top:16px">Este indicador es editorial y explicable: una tensión fronteriza o política no implica por sí sola un cierre del corredor. Los avisos oficiales prevalecen para decisiones de navegación o seguridad.</p>
</section>
<section class="gwo-panel gwo-shell"><div class="gwo-panel-head"><div><div class="gwo-kicker">CRONOLOGÍA</div><h2>Últimos cambios materiales</h2></div><a href="datos.html">Ver histórico completo →</a></div><div class="gwo-timeline" data-gwo-timeline data-limit="12"></div></section>
{END_DETAIL}'''

HEALTH = f'''{START_HEALTH}
<section class="gwo-panel gwo-shell" aria-labelledby="gwo-source-health-title"><div class="gwo-panel-head"><div><div class="gwo-kicker">FRESCURA Y TRAZABILIDAD</div><h2 id="gwo-source-health-title">Salud de las fuentes</h2></div><p>La hora de consulta se muestra por separado de la fecha a la que se refiere cada dato. Una fuente antigua no se presenta como información en tiempo real.</p></div><div class="gwo-health-grid" data-gwo-health-list></div><p style="margin-top:18px"><a href="transparencia.html">Cómo funciona el sistema de confianza →</a></p></section>
{END_HEALTH}'''

TRAFFIC = f'''{START_DETAIL}
<section class="gwo-livebar gwo-shell" aria-label="Frescura del observatorio"><div class="gwo-livebar-inner"><div class="gwo-state" data-gwo-state-box><span class="gwo-state-dot"></span><div class="gwo-state-copy"><small>LECTURA CONSOLIDADA</small><b data-gwo-state>—</b><small data-gwo-updated>Actualizando…</small></div></div><div class="gwo-live-metric"><span>OPE · pasajeros</span><strong data-gwo-metric="ope_passengers_day">—</strong><em>último parte</em></div><div class="gwo-live-metric"><span>OPE · vehículos</span><strong data-gwo-metric="ope_vehicles_day">—</strong><em>último parte</em></div><div class="gwo-live-metric"><span>Fuentes</span><strong class="gwo-chip" data-gwo-health-overall>—</strong><em>estado de frescura</em></div><div class="gwo-live-metric"><span>Contexto</span><strong><a href="mapa-estrategico.html">Mapa</a></strong><em>nodos estratégicos</em></div></div></section>
{END_DETAIL}'''

FOOT = f'''{START_FOOT}<div class="gwo-footer-links"><a href="datos.html">Datos</a><a href="mapa-estrategico.html">Mapa estratégico</a><a href="transparencia.html">Transparencia</a><a href="correcciones.html">Correcciones</a><a href="boletin.html">Boletín</a><a href="observatory-feed.xml">RSS del observatorio</a></div>{END_FOOT}'''

NEW_URLS = [
    ("datos.html", "daily", "0.8"),
    ("mapa-estrategico.html", "weekly", "0.7"),
    ("transparencia.html", "monthly", "0.6"),
    ("correcciones.html", "monthly", "0.5"),
    ("boletin.html", "daily", "0.7"),
]


def replace_marked(text: str, start: str, end: str, block: str) -> str:
    if start in text and end in text:
        return re.sub(re.escape(start) + r".*?" + re.escape(end), lambda _: block, text, count=1, flags=re.S)
    return text


def add_head(text: str) -> str:
    for tag, needle in ((CSS, 'gw-observatory.css'), (JS, 'gw-observatory.js'), (RSS, 'observatory-feed.xml')):
        if needle not in text and '</head>' in text:
            text = text.replace('</head>', tag + '\n</head>', 1)
    return text


def insert_after_first_section(text: str, section_class: str, block: str) -> str:
    match = re.search(rf'<section\b[^>]*class=["\'][^"\']*\b{re.escape(section_class)}\b[^"\']*["\'][^>]*>', text, re.I)
    if not match:
        return text
    end = text.find('</section>', match.end())
    if end < 0:
        return text
    end += len('</section>')
    return text[:end] + '\n' + block + text[end:]


def patch_home(text: str) -> str:
    text = add_head(text)
    text = replace_marked(text, START_LIVE, END_LIVE, LIVE)
    if START_LIVE not in text:
        changed = insert_after_first_section(text, 'gwc-hero', LIVE)
        if changed == text:
            changed = insert_after_first_section(text, 'home-hero', LIVE)
        text = changed if changed != text else insert_after_main(text, LIVE)
    text = replace_marked(text, START_TIMELINE, END_TIMELINE, HOME_TIMELINE)
    if START_TIMELINE not in text:
        if '<!-- GW_DIARY_HOME_START -->' in text:
            text = text.replace('<!-- GW_DIARY_HOME_START -->', HOME_TIMELINE + '\n<!-- GW_DIARY_HOME_START -->', 1)
        elif '<!-- GW_BUSINESS_HOME_START -->' in text:
            text = text.replace('<!-- GW_BUSINESS_HOME_START -->', HOME_TIMELINE + '\n<!-- GW_BUSINESS_HOME_START -->', 1)
        else:
            text = text.replace('</main>', HOME_TIMELINE + '\n</main>', 1)
    return patch_footer(text)


def insert_after_main(text: str, block: str) -> str:
    m = re.search(r'<main\b[^>]*>', text, re.I)
    if not m:
        return text
    return text[:m.end()] + '\n' + block + text[m.end():]


def patch_current(text: str) -> str:
    text = add_head(text)
    text = replace_marked(text, START_LIVE, END_LIVE, LIVE)
    if START_LIVE not in text:
        text = insert_after_main(text, LIVE)
    text = replace_marked(text, START_DETAIL, END_DETAIL, DETAIL)
    if START_DETAIL not in text:
        text = text.replace('</main>', DETAIL + '\n</main>', 1)
    return patch_footer(text)


def patch_sources(text: str) -> str:
    text = add_head(text)
    text = replace_marked(text, START_HEALTH, END_HEALTH, HEALTH)
    if START_HEALTH not in text:
        text = text.replace('</main>', HEALTH + '\n</main>', 1)
    return patch_footer(text)


def patch_traffic(text: str) -> str:
    text = add_head(text)
    text = replace_marked(text, START_DETAIL, END_DETAIL, TRAFFIC)
    if START_DETAIL not in text:
        text = insert_after_main(text, TRAFFIC)
    return patch_footer(text)


def patch_footer(text: str) -> str:
    text = replace_marked(text, START_FOOT, END_FOOT, FOOT)
    if START_FOOT in text:
        return text
    marker = '<div class="gwc-footer-bottom">'
    if marker in text:
        return text.replace(marker, FOOT + '\n' + marker, 1)
    if '</footer>' in text:
        return text.replace('</footer>', FOOT + '\n</footer>', 1)
    return text


def patch_generic(path: Path) -> None:
    if not path.exists():
        return
    old = path.read_text(encoding='utf-8')
    new = patch_footer(add_head(old))
    if new != old:
        path.write_text(new, encoding='utf-8')


def update_sitemap() -> None:
    path = ROOT / 'sitemap.xml'
    if not path.exists():
        return
    text = path.read_text(encoding='utf-8')
    today = datetime.now(ZoneInfo('Europe/Madrid')).date().isoformat()
    additions=[]
    for rel,freq,priority in NEW_URLS:
        absolute='https://estrechogibraltar.com/'+rel
        if absolute in text:
            continue
        additions.append(f'  <url>\n    <loc>{absolute}</loc>\n    <lastmod>{today}</lastmod>\n    <changefreq>{freq}</changefreq>\n    <priority>{priority}</priority>\n  </url>\n')
    if additions and '</urlset>' in text:
        path.write_text(text.replace('</urlset>',''.join(additions)+'</urlset>',1),encoding='utf-8')


def main() -> int:
    required = ['gw-observatory.css','gw-observatory.js','datos.html','mapa-estrategico.html','transparencia.html','correcciones.html','boletin.html','update_observatory.py']
    missing=[x for x in required if not (ROOT/x).exists()]
    if missing:
        raise SystemExit('Faltan archivos del paquete vNext: '+', '.join(missing))

    targets = {
        'index.html': patch_home,
        'situacion-actual.html': patch_current,
        'fuentes.html': patch_sources,
        'trafico.html': patch_traffic,
    }
    changed=0
    for name,fn in targets.items():
        p=ROOT/name
        if not p.exists():
            continue
        old=p.read_text(encoding='utf-8'); new=fn(old)
        if new!=old:
            p.write_text(new,encoding='utf-8'); changed+=1

    # Make new transparency/data routes discoverable from Spanish pages without widening the primary nav.
    for p in ROOT.glob('*.html'):
        if p.name in targets or p.name in {x[0] for x in NEW_URLS} or p.name.startswith('en-') or p.name=='en.html':
            continue
        old=p.read_text(encoding='utf-8'); new=patch_footer(add_head(old))
        if new!=old:
            p.write_text(new,encoding='utf-8'); changed+=1

    update_sitemap()
    print(f'Observatory vNext instalado/validado en {changed} página(s).')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
