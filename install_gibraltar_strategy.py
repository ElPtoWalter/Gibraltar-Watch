#!/usr/bin/env python3
"""Instalador idempotente del giro editorial estratégico de Gibraltar Watch."""
from __future__ import annotations

from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
TODAY = "2026-08-03"
STYLE = '<link rel="stylesheet" href="gibraltar-strategy.css?v=strategy-20260803-1">'
SCRIPT = '<script defer src="gibraltar-strategy.js?v=strategy-20260803-1"></script>'

PAGES = [
    ("situacion-actual.html", "daily", "1.0"),
    ("en-current-situation.html", "daily", "0.9"),
    ("ceuta-melilla.html", "weekly", "0.95"),
    ("en-ceuta-melilla.html", "weekly", "0.85"),
    ("espana-marruecos.html", "weekly", "0.95"),
    ("en-spain-morocco.html", "weekly", "0.85"),
    ("quien-controla-estrecho.html", "monthly", "0.95"),
    ("en-who-controls-strait.html", "monthly", "0.85"),
    ("escenarios.html", "weekly", "0.9"),
    ("en-scenarios.html", "weekly", "0.8"),
]

ES_NAV = [
    ("index.html", "Inicio", "home"), ("situacion-actual.html", "Situación actual", "current"),
    ("trafico.html", "Tráfico y economía", "traffic"), ("ceuta-melilla.html", "Ceuta y Melilla", "ceuta"),
    ("espana-marruecos.html", "España–Marruecos", "relations"), ("quien-controla-estrecho.html", "Quién controla", "control"),
    ("escenarios.html", "Escenarios", "scenarios"), ("geologia.html", "Territorio y futuro", "territory"),
    ("fuentes.html", "Fuentes", "sources"),
]
EN_NAV = [
    ("en.html", "Home", "home"), ("en-current-situation.html", "Current situation", "current"),
    ("en-traffic.html", "Traffic and economy", "traffic"), ("en-ceuta-melilla.html", "Ceuta and Melilla", "ceuta"),
    ("en-spain-morocco.html", "Spain–Morocco", "relations"), ("en-who-controls-strait.html", "Who controls it", "control"),
    ("en-scenarios.html", "Scenarios", "scenarios"), ("en-geology.html", "Territory and future", "territory"),
    ("en-sources.html", "Sources", "sources"),
]

GROUPS = {
    "home": {"index.html", "en.html"},
    "current": {"situacion-actual.html", "en-current-situation.html", "parte-diario.html", "en-daily-brief.html"},
    "traffic": {"trafico.html", "en-traffic.html", "operacion-paso-estrecho-2026.html", "en-strait-crossing-operation-2026.html", "servicios-buques-estrecho-gibraltar.html", "en-ship-services-strait-gibraltar.html", "importancia.html", "en-importance.html"},
    "ceuta": {"ceuta-melilla.html", "en-ceuta-melilla.html"},
    "relations": {"espana-marruecos.html", "en-spain-morocco.html"},
    "control": {"quien-controla-estrecho.html", "en-who-controls-strait.html"},
    "scenarios": {"escenarios.html", "en-scenarios.html", "que-significaria-cierre-estrecho-gibraltar.html", "en-what-would-closure-strait-of-gibraltar-mean.html", "impacto-cierre-gibraltar-comercio-europa-africa.html", "en-impact-gibraltar-closure-trade-europe-africa.html"},
    "territory": {"geologia.html", "en-geology.html", "sismicidad.html", "en-seismicity.html", "futuro.html", "en-future.html", "tunel.html", "en-tunnel.html", "como-funciona-intercambio-agua-gibraltar.html", "en-how-water-exchange-works-strait-of-gibraltar.html", "por-que-45-mm-no-significa-cierre-gibraltar.html", "en-why-4-5-mm-does-not-mean-gibraltar-is-closing.html"},
    "sources": {"fuentes.html", "en-sources.html", "metodologia.html", "en-methodology.html", "politica-editorial.html", "en-editorial-policy.html", "contacto.html", "en-contact.html", "privacidad.html", "en-privacy.html"},
}

HOME_ES = r'''<!-- GW_STRATEGY_HOME_START -->
<section class="gw-strategy-home">
  <div class="gw-strategy-home-copy">
    <div class="eyebrow"><span class="live-dot"></span> Observatorio marítimo, económico y geopolítico</div>
    <h1>El Estrecho de Gibraltar:<br><span>tráfico, economía y poder</span></h1>
    <p>Un corredor de apenas 14 km concentra navegación mundial, grandes puertos, fronteras europeas y la relación estratégica entre España y Marruecos. Gibraltar Watch distingue hechos, interpretación y escenarios.</p>
    <div class="gw-strategy-home-actions"><a class="button primary" href="situacion-actual.html">Ver situación actual</a><a class="button ghost" href="trafico.html">Abrir tráfico marítimo</a></div>
  </div>
  <aside class="gw-strategy-home-side"><div><small>IMPORTANCIA ESTRATÉGICA</small><strong>MUY<br>ALTA</strong><p>No porque el canal vaya a cerrarse geológicamente, sino porque conecta Atlántico y Mediterráneo, separa Europa y África y concentra rutas, puertos, seguridad e infraestructuras críticas.</p></div><div class="gw-strategy-axis"><span>ATLÁNTICO</span><i></i><span>MEDITERRÁNEO</span></div></aside>
</section>
<section class="gw-strategy-strip" aria-label="Estado estratégico"><article data-status-card="maritime"><small>TRÁFICO</small><strong data-strat="maritime_status">OPERATIVO</strong><span data-strat="maritime_note">El corredor permanece abierto.</span></article><article data-status-card="border"><small>CEUTA Y MELILLA</small><strong data-strat="border_pressure">ALTA</strong><span data-strat="border_note">Presión fronteriza y humanitaria.</span></article><article data-status-card="relations"><small>ESPAÑA–MARRUECOS</small><strong data-strat="bilateral_tension">ELEVADA</strong><span data-strat="bilateral_note">Cooperación y fricción simultáneas.</span></article><article data-status-card="security"><small>SEGURIDAD</small><strong data-strat="security_status">VIGILANCIA</strong><span data-strat="security_note">Seguimiento reforzado.</span></article></section>
<section class="gw-home-crisis"><div><div class="kicker">CEUTA · CONTEXTO ACTUAL</div><h2>La frontera vuelve a demostrar que el Estrecho es también un espacio político</h2><p>La crisis de julio y agosto de 2026 ha desbordado recursos, provocado víctimas y reabierto el debate sobre cooperación migratoria, soberanía e influencia de Marruecos. La web separa lo confirmado de las hipótesis.</p><a class="button primary" href="situacion-actual.html">Qué sabemos y qué no</a></div><aside><h3>Lectura prudente</h3><ul><li>Marruecos reivindica Ceuta y Melilla.</li><li>Las ciudades tienen gran valor estratégico.</li><li>No hay prueba pública concluyente de un plan inmediato para ocuparlas.</li><li>Controlarlas no equivaldría automáticamente a controlar la navegación.</li></ul></aside></section>
<section class="gw-home-economy"><div class="section-heading"><div><div class="kicker">ECONOMÍA DEL CORREDOR</div><h2>Dos orillas que compiten y se necesitan</h2></div><p>Puertos, ferris, comercio, industria y servicios marítimos convierten el entorno del Estrecho en una de las regiones logísticas más densas del Mediterráneo.</p></div><div class="gw-economic-ledger"><div><small>ALGECIRAS · 2025</small><strong>100,7 Mt</strong><p>Una década por encima de 100 millones de toneladas anuales.</p></div><div><small>TÁNGER MED · 2025</small><strong>11,1 M TEU</strong><p>Gran plataforma de transbordo, industria y conexión Europa–África.</p></div><div><small>UE–MARRUECOS · 2025</small><strong>€62,2 mil M</strong><p>Comercio de bienes en una relación profundamente interdependiente.</p></div></div></section>
<section class="gw-home-control"><div><div class="kicker">PODER DISTRIBUIDO</div><h2>Nadie controla solo el Estrecho</h2><p>España, Marruecos, Gibraltar, la OMI, los puertos y las alianzas de seguridad comparten competencias, capacidades y límites.</p><a class="button ghost" href="quien-controla-estrecho.html">Ver el mapa de control</a></div><div class="gw-home-control-grid"><article><span>ESPAÑA</span><h3>Tarifa, Algeciras y Ceuta</h3></article><article><span>MARRUECOS</span><h3>Tánger y Tánger Med</h3></article><article><span>REINO UNIDO</span><h3>Gibraltar y su puerto</h3></article><article><span>MARCO INTERNACIONAL</span><h3>GIBREP y libertad de navegación</h3></article></div></section>
<section class="gw-home-hub" aria-label="Secciones estratégicas"><a href="situacion-actual.html"><b>Situación actual</b><span>Noticias, indicadores y confianza</span></a><a href="trafico.html"><b>Tráfico y economía</b><span>AIS, puertos, ferris y logística</span></a><a href="ceuta-melilla.html"><b>Ceuta y Melilla</b><span>Soberanía, frontera y seguridad</span></a><a href="espana-marruecos.html"><b>España–Marruecos</b><span>Cooperación, competencia y presión</span></a><a href="escenarios.html"><b>Escenarios</b><span>Qué vigilar sin hacer predicciones</span></a></section>
<!-- GW_STRATEGY_HOME_END -->'''

HOME_EN = r'''<!-- GW_STRATEGY_HOME_START -->
<section class="gw-strategy-home">
  <div class="gw-strategy-home-copy">
    <div class="eyebrow"><span class="live-dot"></span> Maritime, economic and geopolitical observatory</div>
    <h1>The Strait of Gibraltar:<br><span>traffic, economy and power</span></h1>
    <p>A corridor barely 14 km wide concentrates global shipping, major ports, European borders and the strategic relationship between Spain and Morocco. Gibraltar Watch separates facts, interpretation and scenarios.</p>
    <div class="gw-strategy-home-actions"><a class="button primary" href="en-current-situation.html">See current situation</a><a class="button ghost" href="en-traffic.html">Open maritime traffic</a></div>
  </div>
  <aside class="gw-strategy-home-side"><div><small>STRATEGIC IMPORTANCE</small><strong>VERY<br>HIGH</strong><p>Not because the channel is about to close geologically, but because it connects the Atlantic and Mediterranean, separates Europe and Africa and concentrates routes, ports, security and critical infrastructure.</p></div><div class="gw-strategy-axis"><span>ATLANTIC</span><i></i><span>MEDITERRANEAN</span></div></aside>
</section>
<section class="gw-strategy-strip" aria-label="Strategic status"><article data-status-card="maritime"><small>TRAFFIC</small><strong data-strat="maritime_status">OPERATIONAL</strong><span data-strat="maritime_note">The corridor remains open.</span></article><article data-status-card="border"><small>CEUTA AND MELILLA</small><strong data-strat="border_pressure">HIGH</strong><span data-strat="border_note">Border and humanitarian pressure.</span></article><article data-status-card="relations"><small>SPAIN–MOROCCO</small><strong data-strat="bilateral_tension">ELEVATED</strong><span data-strat="bilateral_note">Cooperation and friction coexist.</span></article><article data-status-card="security"><small>SECURITY</small><strong data-strat="security_status">MONITORING</strong><span data-strat="security_note">Reinforced scrutiny.</span></article></section>
<section class="gw-home-crisis"><div><div class="kicker">CEUTA · CURRENT CONTEXT</div><h2>The border again shows that the Strait is also a political space</h2><p>The July–August 2026 crisis overwhelmed services, caused deaths and reopened debate about migration cooperation, sovereignty and Moroccan influence. The site separates confirmed information from hypotheses.</p><a class="button primary" href="en-current-situation.html">What is known and unknown</a></div><aside><h3>Prudent reading</h3><ul><li>Morocco claims Ceuta and Melilla.</li><li>The cities have major strategic value.</li><li>There is no conclusive public evidence of an immediate plan to seize them.</li><li>Possession would not automatically equal control of navigation.</li></ul></aside></section>
<section class="gw-home-economy"><div class="section-heading"><div><div class="kicker">CORRIDOR ECONOMY</div><h2>Two shores that compete and need each other</h2></div><p>Ports, ferries, trade, industry and maritime services make the Strait one of the Mediterranean's densest logistics regions.</p></div><div class="gw-economic-ledger"><div><small>ALGECIRAS · 2025</small><strong>100.7 Mt</strong><p>A decade above 100 million tonnes annually.</p></div><div><small>TANGER MED · 2025</small><strong>11.1m TEU</strong><p>A major transshipment, industrial and Europe–Africa platform.</p></div><div><small>EU–MOROCCO · 2025</small><strong>€62.2bn</strong><p>Goods trade in a deeply interdependent relationship.</p></div></div></section>
<section class="gw-home-control"><div><div class="kicker">DISTRIBUTED POWER</div><h2>No one controls the Strait alone</h2><p>Spain, Morocco, Gibraltar, the IMO, ports and security alliances share capabilities, authority and limits.</p><a class="button ghost" href="en-who-controls-strait.html">See the control map</a></div><div class="gw-home-control-grid"><article><span>SPAIN</span><h3>Tarifa, Algeciras and Ceuta</h3></article><article><span>MOROCCO</span><h3>Tangier and Tanger Med</h3></article><article><span>UNITED KINGDOM</span><h3>Gibraltar and its port</h3></article><article><span>INTERNATIONAL FRAMEWORK</span><h3>GIBREP and freedom of navigation</h3></article></div></section>
<section class="gw-home-hub" aria-label="Strategic sections"><a href="en-current-situation.html"><b>Current situation</b><span>News, indicators and confidence</span></a><a href="en-traffic.html"><b>Traffic and economy</b><span>AIS, ports, ferries and logistics</span></a><a href="en-ceuta-melilla.html"><b>Ceuta and Melilla</b><span>Sovereignty, border and security</span></a><a href="en-spain-morocco.html"><b>Spain–Morocco</b><span>Cooperation, competition and leverage</span></a><a href="en-scenarios.html"><b>Scenarios</b><span>Signals to watch without predictions</span></a></section>
<!-- GW_STRATEGY_HOME_END -->'''

TRAFFIC_ES = r'''<!-- GW_STRATEGIC_CONTEXT_START --><section class="gw-context-card"><div><small>POR QUÉ IMPORTA EL TRÁFICO</small><h2>El AIS muestra barcos; el contexto explica el poder</h2><p>El volumen marítimo sostiene puertos, energía, industria y servicios. Una alteración importante tendría efectos económicos y políticos en ambas orillas.</p></div><a class="button primary" href="quien-controla-estrecho.html">Quién controla el corredor</a></section><!-- GW_STRATEGIC_CONTEXT_END -->'''
TRAFFIC_EN = TRAFFIC_ES.replace('POR QUÉ IMPORTA EL TRÁFICO','WHY TRAFFIC MATTERS').replace('El AIS muestra barcos; el contexto explica el poder','AIS shows ships; context explains power').replace('El volumen marítimo sostiene puertos, energía, industria y servicios. Una alteración importante tendría efectos económicos y políticos en ambas orillas.','Maritime volume sustains ports, energy, industry and services. A major disruption would have economic and political effects on both shores.').replace('quien-controla-estrecho.html','en-who-controls-strait.html').replace('Quién controla el corredor','Who controls the corridor')

SOURCES_ES = r'''<!-- GW_GEOPOLITICS_SOURCES_START --><section class="gw-method-note"><div class="kicker">NUEVO EJE EDITORIAL</div><h2>Fuentes para geopolítica, Ceuta y relaciones bilaterales</h2><p>El seguimiento combina agencias internacionales, comunicados de España, instituciones europeas, OMI, OTAN, APBA y Tánger Med. Las noticias automáticas solo aportan titulares y enlaces; las conclusiones se redactan separando hecho, interpretación y escenario.</p><a href="geopolitics-sources.json">Abrir registro JSON de fuentes</a></section><!-- GW_GEOPOLITICS_SOURCES_END -->'''
SOURCES_EN = SOURCES_ES.replace('NUEVO EJE EDITORIAL','NEW EDITORIAL AXIS').replace('Fuentes para geopolítica, Ceuta y relaciones bilaterales','Sources for geopolitics, Ceuta and bilateral relations').replace('El seguimiento combina agencias internacionales, comunicados de España, instituciones europeas, OMI, OTAN, APBA y Tánger Med. Las noticias automáticas solo aportan titulares y enlaces; las conclusiones se redactan separando hecho, interpretación y escenario.','Monitoring combines international agencies, Spanish government statements, European institutions, IMO, NATO, APBA and Tanger Med. Automated news only provides headlines and links; conclusions separate facts, interpretation and scenarios.').replace('Abrir registro JSON de fuentes','Open JSON source register')


def is_english(text: str, name: str) -> bool:
    return 'lang="en"' in text[:500].lower() or name.startswith('en-') or name == 'en.html'


def active_group(name: str) -> str:
    for key, names in GROUPS.items():
        if name in names:
            return key
    return ""


def nav_html(english: bool, active: str) -> str:
    arr = EN_NAV if english else ES_NAV
    links = []
    for href, label, key in arr:
        cls = ' class="active"' if key == active else ''
        links.append(f'<a{cls} href="{href}">{label}</a>')
    links.append('<a class="lang-switch" href="index.html">ES</a>' if english else '<a class="lang-switch" href="en.html">EN</a>')
    aria = "Main navigation" if english else "Navegación principal"
    return f'<nav aria-label="{aria}" class="site-nav">' + ''.join(links) + '</nav>'


def footer_html(english: bool) -> str:
    if english:
        return '<footer class="site-footer gw-strategy-footer"><div><strong>Gibraltar Watch</strong><p>Independent observatory. Facts, interpretation and scenarios are separated. Not a replacement for official sources, professional navigation or security notices.</p></div><nav><a href="en-current-situation.html">Current situation</a><a href="en-traffic.html">Traffic</a><a href="en-ceuta-melilla.html">Ceuta and Melilla</a><a href="en-spain-morocco.html">Spain–Morocco</a><a href="en-who-controls-strait.html">Who controls it</a><a href="en-scenarios.html">Scenarios</a><a href="en-methodology.html">Methodology</a><a href="en-sources.html">Sources</a><a href="en-contact.html">Contact</a><a href="en-privacy.html">Privacy</a></nav><p class="footer-brand">Gibraltar Watch · 2026</p></footer>'
    return '<footer class="site-footer gw-strategy-footer"><div><strong>Gibraltar Watch</strong><p>Observatorio independiente. Separamos hechos, interpretación y escenarios. No sustituye fuentes oficiales, navegación profesional ni avisos de seguridad.</p></div><nav><a href="situacion-actual.html">Situación actual</a><a href="trafico.html">Tráfico</a><a href="ceuta-melilla.html">Ceuta y Melilla</a><a href="espana-marruecos.html">España–Marruecos</a><a href="quien-controla-estrecho.html">Quién controla</a><a href="escenarios.html">Escenarios</a><a href="metodologia.html">Metodología</a><a href="fuentes.html">Fuentes</a><a href="contacto.html">Contacto</a><a href="privacidad.html">Privacidad</a></nav><p class="footer-brand">Gibraltar Watch · 2026</p></footer>'


def add_assets(text: str) -> str:
    if "gibraltar-strategy.css" not in text:
        text = text.replace("</head>", STYLE + "</head>", 1)
    if "gibraltar-strategy.js" not in text:
        text = text.replace("</body>", SCRIPT + "</body>", 1)
    return text


def remove_marked(text: str, start: str, end: str) -> str:
    return re.sub(re.escape(start) + r".*?" + re.escape(end), "", text, flags=re.S | re.I)


def patch_common(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    english = is_english(text, path.name)
    text = add_assets(text)
    text = re.sub(r'<nav\b[^>]*class=["\'][^"\']*site-nav[^"\']*["\'][^>]*>.*?</nav>', nav_html(english, active_group(path.name)), text, count=1, flags=re.S | re.I)
    text = re.sub(r'<footer\b[^>]*class=["\'][^"\']*site-footer[^"\']*["\'][^>]*>.*?</footer>', footer_html(english), text, count=1, flags=re.S | re.I)
    path.write_text(text, encoding="utf-8")


def patch_home(path: Path, english: bool) -> None:
    text = path.read_text(encoding="utf-8")
    text = remove_marked(text, "<!-- GW_STRATEGY_HOME_START -->", "<!-- GW_STRATEGY_HOME_END -->")
    # Remove the old question-led hero, scientific answer banner and four-card dashboard.
    text = re.sub(r'<section\b[^>]*class=["\'][^"\']*home-hero[^"\']*["\'][^>]*>.*?</section>', '', text, count=1, flags=re.S | re.I)
    text = re.sub(r'<section\b[^>]*class=["\'][^"\']*truth-banner[^"\']*["\'][^>]*>.*?</section>', '', text, count=1, flags=re.S | re.I)
    text = re.sub(r'<section\b(?=[^>]*(?:class=["\'][^"\']*dashboard[^"\']*["\']|id=["\']panel["\']))[^>]*>.*?</section>', '', text, count=1, flags=re.S | re.I)
    block = HOME_EN if english else HOME_ES
    main = re.search(r'<main\b[^>]*>', text, flags=re.I)
    if main:
        text = text[:main.end()] + block + text[main.end():]
    if english:
        seo_title = "Strait of Gibraltar: traffic, economy and geopolitics"
        seo_desc = "Strategic observatory of the Strait of Gibraltar: maritime traffic, ports, Ceuta, Melilla and Spain–Morocco relations."
    else:
        seo_title = "Estrecho de Gibraltar: tráfico, economía y geopolítica"
        seo_desc = "Observatorio estratégico del Estrecho de Gibraltar: tráfico marítimo, puertos, Ceuta, Melilla y relaciones entre España y Marruecos."
    text = re.sub(r'<title>.*?</title>', f'<title>{seo_title}</title>', text, count=1, flags=re.S | re.I)
    text = re.sub(r'<meta\b(?=[^>]*name=["\']description["\'])[^>]*>', f'<meta name="description" content="{seo_desc}">', text, count=1, flags=re.I)
    text = re.sub(r'<meta\b(?=[^>]*property=["\']og:title["\'])[^>]*>', f'<meta property="og:title" content="{seo_title}">', text, count=1, flags=re.I)
    text = re.sub(r'<meta\b(?=[^>]*property=["\']og:description["\'])[^>]*>', f'<meta property="og:description" content="{seo_desc}">', text, count=1, flags=re.I)
    text = re.sub(r'<meta\b(?=[^>]*name=["\']twitter:title["\'])[^>]*>', f'<meta name="twitter:title" content="{seo_title}">', text, count=1, flags=re.I)
    text = re.sub(r'<meta\b(?=[^>]*name=["\']twitter:description["\'])[^>]*>', f'<meta name="twitter:description" content="{seo_desc}">', text, count=1, flags=re.I)
    path.write_text(text, encoding="utf-8")


def insert_before_editorial(path: Path, block: str) -> None:
    text = path.read_text(encoding="utf-8")
    text = remove_marked(text, "<!-- GW_STRATEGIC_CONTEXT_START -->", "<!-- GW_STRATEGIC_CONTEXT_END -->")
    marker = '<section class="gt-editorial-record' if '<section class="gt-editorial-record' in text else '</main>'
    text = text.replace(marker, block + marker, 1)
    path.write_text(text, encoding="utf-8")


def patch_sources(path: Path, block: str) -> None:
    text = path.read_text(encoding="utf-8")
    text = remove_marked(text, "<!-- GW_GEOPOLITICS_SOURCES_START -->", "<!-- GW_GEOPOLITICS_SOURCES_END -->")
    text = text.replace('</main>', block + '</main>', 1)
    path.write_text(text, encoding="utf-8")


def update_sitemap() -> None:
    path = ROOT / "sitemap.xml"
    if not path.exists():
        return
    ET.register_namespace('', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    tree = ET.parse(path)
    root = tree.getroot()
    ns = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
    existing = {u.findtext(ns + 'loc') for u in root.findall(ns + 'url')}
    for slug, freq, priority in PAGES:
        url = f'https://estrechogibraltar.com/{slug}'
        if url in existing:
            continue
        node = ET.SubElement(root, ns + 'url')
        ET.SubElement(node, ns + 'loc').text = url
        ET.SubElement(node, ns + 'lastmod').text = TODAY
        ET.SubElement(node, ns + 'changefreq').text = freq
        ET.SubElement(node, ns + 'priority').text = priority
    tree.write(path, encoding='utf-8', xml_declaration=True)


def update_llms() -> None:
    path = ROOT / 'llms.txt'
    text = path.read_text(encoding='utf-8') if path.exists() else '# Gibraltar Watch\n'
    marker = '## Strategic Observatory 2026'
    if marker not in text:
        text = text.rstrip() + '\n\n' + marker + '\n' + '\n'.join([
            '- Current situation: https://estrechogibraltar.com/situacion-actual.html',
            '- Ceuta and Melilla: https://estrechogibraltar.com/ceuta-melilla.html',
            '- Spain–Morocco: https://estrechogibraltar.com/espana-marruecos.html',
            '- Who controls the Strait: https://estrechogibraltar.com/quien-controla-estrecho.html',
            '- Strategic scenarios: https://estrechogibraltar.com/escenarios.html',
            '- Current geopolitical data: https://estrechogibraltar.com/geopolitics.json',
        ]) + '\n'
    path.write_text(text, encoding='utf-8')


def main() -> int:
    for path in ROOT.glob('*.html'):
        patch_common(path)
    for name, english in [('index.html', False), ('en.html', True)]:
        path = ROOT / name
        if path.exists():
            patch_home(path, english)
            patch_common(path)
    for name, block in [('trafico.html', TRAFFIC_ES), ('en-traffic.html', TRAFFIC_EN), ('importancia.html', TRAFFIC_ES), ('en-importance.html', TRAFFIC_EN)]:
        path = ROOT / name
        if path.exists():
            insert_before_editorial(path, block)
    for name, block in [('fuentes.html', SOURCES_ES), ('en-sources.html', SOURCES_EN)]:
        path = ROOT / name
        if path.exists():
            patch_sources(path, block)
    update_sitemap()
    update_llms()
    print('Gibraltar Watch remodelado como observatorio estratégico.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
