#!/usr/bin/env python3
"""Consolidación final de Gibraltar Watch.

- Reemplaza la portada por una arquitectura editorial única.
- Simplifica navegación y pie en todas las páginas.
- Elimina duplicidades de la portada aunque instaladores anteriores vuelvan a ejecutarse.
- Mantiene geología, sismicidad y túnel como bloque secundario.
- Reconstruye sitemap.xml de forma válida.
"""
from __future__ import annotations

import html
import re
from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent
TODAY = date.today().isoformat()
CSS_FILE = "gibraltar-consolidated.css"
JS_FILE = "gibraltar-consolidated.js"

NAV_ES = r'''<nav aria-label="Navegación principal" class="site-nav gwc-site-nav">
  <a href="index.html">Inicio</a>
  <a href="situacion-actual.html">Situación actual</a>
  <a href="trafico.html">Tráfico y economía</a>
  <a href="ceuta-melilla.html">Ceuta y Melilla</a>
  <details class="gwc-nav-group">
    <summary>Geopolítica</summary>
    <div class="gwc-nav-menu">
      <a href="espana-marruecos.html">España–Marruecos</a>
      <a href="quien-controla-estrecho.html">Quién controla</a>
      <a href="escenarios.html">Escenarios</a>
    </div>
  </details>
  <details class="gwc-nav-group">
    <summary>Territorio y futuro</summary>
    <div class="gwc-nav-menu">
      <a href="geologia.html">Geología</a>
      <a href="sismicidad.html">Sismicidad</a>
      <a href="futuro.html">¿Podría cerrarse?</a>
      <a href="tunel.html">Túnel</a>
    </div>
  </details>
  <a href="fuentes.html">Fuentes</a>
  <a class="lang-switch" href="en.html">EN</a>
</nav>'''

NAV_EN = r'''<nav aria-label="Main navigation" class="site-nav gwc-site-nav">
  <a href="en.html">Home</a>
  <a href="en-current-situation.html">Current situation</a>
  <a href="en-traffic.html">Traffic and economy</a>
  <a href="en-ceuta-melilla.html">Ceuta and Melilla</a>
  <details class="gwc-nav-group">
    <summary>Geopolitics</summary>
    <div class="gwc-nav-menu">
      <a href="en-spain-morocco.html">Spain–Morocco</a>
      <a href="en-who-controls-strait.html">Who controls it</a>
      <a href="en-scenarios.html">Scenarios</a>
    </div>
  </details>
  <details class="gwc-nav-group">
    <summary>Territory and future</summary>
    <div class="gwc-nav-menu">
      <a href="en-geology.html">Geology</a>
      <a href="en-seismicity.html">Seismicity</a>
      <a href="en-future.html">Could it close?</a>
      <a href="en-tunnel.html">Tunnel</a>
    </div>
  </details>
  <a href="en-sources.html">Sources</a>
  <a class="lang-switch" href="index.html">ES</a>
</nav>'''

FOOTER_ES = r'''<footer class="site-footer gwc-footer">
  <div class="gwc-footer-grid">
    <section><a class="gwc-footer-brand" href="index.html">Gibraltar Watch</a><p>Observatorio independiente sobre tráfico, economía, fronteras y equilibrio estratégico en el Estrecho de Gibraltar.</p></section>
    <section><h2>Observatorio</h2><a href="situacion-actual.html">Situación actual</a><a href="trafico.html">Tráfico y economía</a><a href="ceuta-melilla.html">Ceuta y Melilla</a><a href="espana-marruecos.html">España–Marruecos</a></section>
    <section><h2>Contexto</h2><a href="quien-controla-estrecho.html">Quién controla el Estrecho</a><a href="escenarios.html">Escenarios</a><a href="geologia.html">Territorio y futuro</a><a href="metodologia.html">Metodología</a></section>
    <section><h2>Transparencia</h2><a href="fuentes.html">Fuentes</a><a href="privacidad.html">Privacidad</a><a href="contacto.html">Contacto</a><a href="feed.xml">RSS</a></section>
  </div>
  <div class="gwc-footer-bottom"><span>Gibraltar Watch · 2026</span><span>Hechos, interpretaciones y escenarios se presentan por separado.</span></div>
</footer>'''

FOOTER_EN = r'''<footer class="site-footer gwc-footer">
  <div class="gwc-footer-grid">
    <section><a class="gwc-footer-brand" href="en.html">Gibraltar Watch</a><p>Independent observatory covering traffic, economics, borders and strategic balance around the Strait of Gibraltar.</p></section>
    <section><h2>Observatory</h2><a href="en-current-situation.html">Current situation</a><a href="en-traffic.html">Traffic and economy</a><a href="en-ceuta-melilla.html">Ceuta and Melilla</a><a href="en-spain-morocco.html">Spain–Morocco</a></section>
    <section><h2>Context</h2><a href="en-who-controls-strait.html">Who controls the Strait</a><a href="en-scenarios.html">Scenarios</a><a href="en-geology.html">Territory and future</a><a href="en-methodology.html">Methodology</a></section>
    <section><h2>Transparency</h2><a href="en-sources.html">Sources</a><a href="en-privacy.html">Privacy</a><a href="en-contact.html">Contact</a><a href="feed.xml">RSS</a></section>
  </div>
  <div class="gwc-footer-bottom"><span>Gibraltar Watch · 2026</span><span>Facts, interpretations and scenarios are shown separately.</span></div>
</footer>'''

HOME_ES = r'''<main class="gwc-home" id="contenido">
  <!-- GWC_HOME_START -->
  <section class="gwc-hero" aria-labelledby="gwc-home-title">
    <div class="gwc-hero-copy">
      <p class="gwc-eyebrow"><span></span> Observatorio marítimo, económico y geopolítico</p>
      <h1 id="gwc-home-title">El Estrecho de Gibraltar:<br><em>tráfico, economía y poder</em></h1>
      <p class="gwc-lead">Un corredor de apenas 14 km concentra navegación mundial, grandes puertos, fronteras europeas y la relación estratégica entre España y Marruecos.</p>
      <div class="gwc-actions"><a class="gwc-button primary" href="situacion-actual.html">Ver situación actual</a><a class="gwc-button secondary" href="trafico.html">Abrir tráfico marítimo</a></div>
      <p class="gwc-hero-note">Gibraltar Watch diferencia <strong>hechos confirmados</strong>, <strong>interpretaciones</strong> y <strong>escenarios</strong>.</p>
    </div>
    <aside class="gwc-strategic-card" aria-label="Valoración estratégica">
      <small>IMPORTANCIA ESTRATÉGICA</small><strong>MUY<br>ALTA</strong>
      <p>Conecta Atlántico y Mediterráneo, separa Europa y África y concentra rutas, puertos, seguridad e infraestructuras críticas.</p>
      <div class="gwc-strait-line"><span>ATLÁNTICO</span><i></i><span>MEDITERRÁNEO</span></div>
    </aside>
  </section>

  <section class="gwc-status" aria-labelledby="gwc-status-title">
    <header class="gwc-section-head"><div><p class="gwc-kicker">PANEL OPERATIVO</p><h2 id="gwc-status-title">Una lectura rápida, con fecha y confianza</h2></div><p id="gwcStatusMeta">Cargando última comprobación…</p></header>
    <div class="gwc-status-grid">
      <article data-gwc-status="maritime"><small>TRÁFICO MARÍTIMO</small><strong id="gwcStatusMaritime">—</strong><p id="gwcNoteMaritime">Consultando el estado del corredor.</p></article>
      <article data-gwc-status="border"><small>CEUTA Y MELILLA</small><strong id="gwcStatusBorder">—</strong><p id="gwcNoteBorder">Consultando la presión fronteriza.</p></article>
      <article data-gwc-status="bilateral"><small>ESPAÑA–MARRUECOS</small><strong id="gwcStatusBilateral">—</strong><p id="gwcNoteBilateral">Consultando la relación bilateral.</p></article>
      <article data-gwc-status="security"><small>SEGURIDAD</small><strong id="gwcStatusSecurity">—</strong><p id="gwcNoteSecurity">Consultando alertas relevantes.</p></article>
    </div>
  </section>

  <section class="gwc-current" aria-labelledby="gwc-current-title">
    <div class="gwc-current-main">
      <header class="gwc-section-head"><div><p class="gwc-kicker">SITUACIÓN ACTUAL</p><h2 id="gwc-current-title">Lo importante, sin mezclar hechos y sospechas</h2></div><a href="situacion-actual.html">Seguimiento completo →</a></header>
      <div class="gwc-news-list" id="gwcNewsList"><p class="gwc-empty">Cargando novedades verificadas…</p></div>
    </div>
    <aside class="gwc-epistemic-card">
      <p class="gwc-kicker">LECTURA PRUDENTE</p><h2>Qué sabemos y qué no</h2>
      <div><strong>Confirmado</strong><ul><li>Marruecos reivindica Ceuta y Melilla.</li><li>Las dos ciudades tienen valor fronterizo, portuario y militar.</li><li>El corredor se gestiona mediante varios actores y normas internacionales.</li></ul></div>
      <div><strong>No demostrado</strong><ul><li>Que una crisis concreta forme parte de un plan inmediato de ocupación.</li><li>Que controlar una ciudad equivalga a controlar automáticamente la navegación.</li></ul></div>
      <a href="ceuta-melilla.html">Ver contexto y cronología →</a>
    </aside>
  </section>

  <section class="gwc-traffic-economy" aria-labelledby="gwc-economy-title">
    <div class="gwc-traffic-intro"><p class="gwc-kicker">TRÁFICO Y ECONOMÍA</p><h2 id="gwc-economy-title">El motor visible del Estrecho</h2><p>Puertos, ferris, logística, abastecimiento y servicios a buques convierten el corredor en una infraestructura económica de escala internacional.</p><div class="gwc-actions"><a class="gwc-button light" href="trafico.html">Radar AIS y tráfico</a><a class="gwc-button outline-light" href="operacion-paso-estrecho-2026.html">Operación Paso del Estrecho</a></div></div>
    <div class="gwc-economy-metrics">
      <article><small>ALGECIRAS · 2025</small><strong>100,7 Mt</strong><span>Tráfico portuario anual</span></article>
      <article><small>TÁNGER MED · 2025</small><strong>11,1 M TEU</strong><span>Contenedores gestionados</span></article>
      <article><small>UE–MARRUECOS · 2025</small><strong>€62,2 mil M</strong><span>Comercio de bienes</span></article>
      <article class="gwc-ope-metric"><small>OPE · ÚLTIMO PARTE</small><strong id="gwcOpePassengers">—</strong><span id="gwcOpeMeta">Pasajeros del día</span></article>
    </div>
    <div class="gwc-route-links"><a href="servicios-buques-estrecho-gibraltar.html">Servicios a buques →</a><a href="importancia.html">Importancia económica →</a><a href="quien-controla-estrecho.html">Mapa de control →</a></div>
  </section>

  <section class="gwc-two-columns" aria-label="Frontera y relación bilateral">
    <article class="gwc-feature-card warm"><p class="gwc-kicker">CEUTA Y MELILLA</p><h2>Frontera, soberanía y presión política</h2><p>Su importancia no nace solo de la geografía. Son fronteras exteriores de la Unión Europea, plazas portuarias y símbolos centrales de la relación hispano-marroquí.</p><ul><li>Presión migratoria y humanitaria</li><li>Economía transfronteriza</li><li>Seguridad y presencia estatal</li></ul><a href="ceuta-melilla.html">Abrir dossier →</a></article>
    <article class="gwc-feature-card blue"><p class="gwc-kicker">ESPAÑA–MARRUECOS</p><h2>Cooperación y competencia al mismo tiempo</h2><p>Comercio, migración, seguridad, Sáhara Occidental, puertos y el Mundial de 2030 obligan a cooperar, mientras persisten intereses y fricciones profundas.</p><ul><li>Interdependencia económica</li><li>Cooperación fronteriza</li><li>Competencia portuaria y diplomática</li></ul><a href="espana-marruecos.html">Ver cronología bilateral →</a></article>
  </section>

  <section class="gwc-control" aria-labelledby="gwc-control-title">
    <header><p class="gwc-kicker">PODER DISTRIBUIDO</p><h2 id="gwc-control-title">Nadie controla solo el Estrecho</h2><p>La capacidad real se reparte entre costas, puertos, centros de tráfico, alianzas y derecho marítimo.</p></header>
    <div class="gwc-control-grid">
      <article><small>ESPAÑA</small><strong>Tarifa, Algeciras y Ceuta</strong><p>Vigilancia, puertos, defensa y presencia en la orilla norte.</p></article>
      <article><small>MARRUECOS</small><strong>Tánger y Tánger Med</strong><p>Control de la orilla sur, puertos y cooperación migratoria.</p></article>
      <article><small>REINO UNIDO</small><strong>Gibraltar y su puerto</strong><p>Enclave, base naval y servicios marítimos.</p></article>
      <article><small>MARCO INTERNACIONAL</small><strong>GIBREP y libertad de navegación</strong><p>Reglas y coordinación que impiden reducir el corredor a un único actor.</p></article>
    </div><a class="gwc-text-link" href="quien-controla-estrecho.html">Entender quién controla realmente el Estrecho →</a>
  </section>

  <section class="gwc-analysis" aria-labelledby="gwc-analysis-title">
    <header class="gwc-section-head"><div><p class="gwc-kicker">ANÁLISIS Y ESCENARIOS</p><h2 id="gwc-analysis-title">Preguntas que exigen contexto</h2></div></header>
    <div class="gwc-analysis-grid">
      <a href="escenarios.html"><small>ESCENARIOS</small><h3>Qué señales indicarían una crisis estratégica real</h3><p>Indicadores, impacto y límites de cada hipótesis.</p><b>Leer →</b></a>
      <a href="quien-controla-estrecho.html"><small>CONTROL</small><h3>Por qué Ceuta y Melilla importan, pero no dan control automático</h3><p>Costas, puertos, navegación y alianzas.</p><b>Leer →</b></a>
      <a href="escenarios.html"><small>ECONOMÍA</small><h3>Qué supondría una interrupción para Europa y África</h3><p>Rutas, cadenas logísticas y costes.</p><b>Leer →</b></a>
    </div>
  </section>

  <section class="gwc-territory" aria-labelledby="gwc-territory-title">
    <header><p class="gwc-kicker">TERRITORIO Y FUTURO</p><h2 id="gwc-territory-title">La ciencia permanece, sin dominar la narrativa</h2><p>Geología, sismicidad, intercambio de aguas y túnel siguen siendo parte esencial del observatorio, pero no prueban un cierre a escala humana.</p></header>
    <div class="gwc-territory-grid">
      <a href="geologia.html"><span>01</span><h3>Geología del arco</h3><p>Convergencia regional y deformación compleja.</p></a>
      <a href="sismicidad.html"><span>02</span><h3>Monitor sísmico</h3><p><b id="gwcQuakes30">—</b> eventos en 30 días.</p></a>
      <a href="futuro.html"><span>03</span><h3>¿Podría cerrarse?</h3><p>Escalas geológicas, no una cuenta atrás.</p></a>
      <a href="tunel.html"><span>04</span><h3>Enlace fijo</h3><p>Estado real de los estudios España–Marruecos.</p></a>
    </div>
  </section>

  <section class="gwc-contact-cta"><div><p class="gwc-kicker">CORRECCIONES Y FUENTES</p><h2>Un observatorio útil debe poder corregirse</h2><p>Envía documentos, fuentes primarias o una corrección razonada. El correo profesional ya está operativo.</p></div><a class="gwc-button primary" href="contacto.html">contacto@estrechogibraltar.com</a></section>
  <!-- GWC_HOME_END -->
</main>'''

HOME_EN = r'''<main class="gwc-home" id="content">
  <!-- GWC_HOME_START -->
  <section class="gwc-hero" aria-labelledby="gwc-home-title">
    <div class="gwc-hero-copy"><p class="gwc-eyebrow"><span></span> Maritime, economic and geopolitical observatory</p><h1 id="gwc-home-title">The Strait of Gibraltar:<br><em>traffic, economics and power</em></h1><p class="gwc-lead">A 14 km corridor concentrates global navigation, major ports, European borders and the strategic relationship between Spain and Morocco.</p><div class="gwc-actions"><a class="gwc-button primary" href="en-current-situation.html">View current situation</a><a class="gwc-button secondary" href="en-traffic.html">Open maritime traffic</a></div><p class="gwc-hero-note">Gibraltar Watch separates <strong>confirmed facts</strong>, <strong>interpretations</strong> and <strong>scenarios</strong>.</p></div>
    <aside class="gwc-strategic-card" aria-label="Strategic assessment"><small>STRATEGIC IMPORTANCE</small><strong>VERY<br>HIGH</strong><p>It connects the Atlantic and Mediterranean, divides Europe and Africa and concentrates routes, ports, security and critical infrastructure.</p><div class="gwc-strait-line"><span>ATLANTIC</span><i></i><span>MEDITERRANEAN</span></div></aside>
  </section>

  <section class="gwc-status" aria-labelledby="gwc-status-title"><header class="gwc-section-head"><div><p class="gwc-kicker">OPERATIONAL PANEL</p><h2 id="gwc-status-title">A quick view with date and confidence</h2></div><p id="gwcStatusMeta">Loading latest check…</p></header><div class="gwc-status-grid"><article data-gwc-status="maritime"><small>MARITIME TRAFFIC</small><strong id="gwcStatusMaritime">—</strong><p id="gwcNoteMaritime">Checking corridor status.</p></article><article data-gwc-status="border"><small>CEUTA AND MELILLA</small><strong id="gwcStatusBorder">—</strong><p id="gwcNoteBorder">Checking border pressure.</p></article><article data-gwc-status="bilateral"><small>SPAIN–MOROCCO</small><strong id="gwcStatusBilateral">—</strong><p id="gwcNoteBilateral">Checking bilateral relations.</p></article><article data-gwc-status="security"><small>SECURITY</small><strong id="gwcStatusSecurity">—</strong><p id="gwcNoteSecurity">Checking relevant alerts.</p></article></div></section>

  <section class="gwc-current" aria-labelledby="gwc-current-title"><div class="gwc-current-main"><header class="gwc-section-head"><div><p class="gwc-kicker">CURRENT SITUATION</p><h2 id="gwc-current-title">What matters, without mixing facts and suspicions</h2></div><a href="en-current-situation.html">Full monitoring →</a></header><div class="gwc-news-list" id="gwcNewsList"><p class="gwc-empty">Loading verified developments…</p></div></div><aside class="gwc-epistemic-card"><p class="gwc-kicker">CAUTIOUS READING</p><h2>What we know and what we do not</h2><div><strong>Confirmed</strong><ul><li>Morocco claims Ceuta and Melilla.</li><li>Both cities have border, port and military value.</li><li>The corridor is managed through several actors and international rules.</li></ul></div><div><strong>Not established</strong><ul><li>That a specific crisis is part of an immediate occupation plan.</li><li>That controlling one city automatically means controlling navigation.</li></ul></div><a href="en-ceuta-melilla.html">Open context and chronology →</a></aside></section>

  <section class="gwc-traffic-economy" aria-labelledby="gwc-economy-title"><div class="gwc-traffic-intro"><p class="gwc-kicker">TRAFFIC AND ECONOMY</p><h2 id="gwc-economy-title">The visible engine of the Strait</h2><p>Ports, ferries, logistics, provisioning and ship services turn the corridor into economic infrastructure of international scale.</p><div class="gwc-actions"><a class="gwc-button light" href="en-traffic.html">AIS radar and traffic</a><a class="gwc-button outline-light" href="en-strait-crossing-operation-2026.html">Strait Crossing Operation</a></div></div><div class="gwc-economy-metrics"><article><small>ALGECIRAS · 2025</small><strong>100.7 Mt</strong><span>Annual port traffic</span></article><article><small>TANGER MED · 2025</small><strong>11.1 M TEU</strong><span>Containers handled</span></article><article><small>EU–MOROCCO · 2025</small><strong>€62.2 bn</strong><span>Trade in goods</span></article><article class="gwc-ope-metric"><small>OPE · LATEST REPORT</small><strong id="gwcOpePassengers">—</strong><span id="gwcOpeMeta">Passengers that day</span></article></div><div class="gwc-route-links"><a href="en-ship-services-strait-gibraltar.html">Ship services →</a><a href="en-importance.html">Economic importance →</a><a href="en-who-controls-strait.html">Control map →</a></div></section>

  <section class="gwc-two-columns" aria-label="Border and bilateral relations"><article class="gwc-feature-card warm"><p class="gwc-kicker">CEUTA AND MELILLA</p><h2>Border, sovereignty and political pressure</h2><p>Their importance is not only geographic. They are EU external borders, port cities and central symbols in Spanish–Moroccan relations.</p><ul><li>Migration and humanitarian pressure</li><li>Cross-border economy</li><li>Security and state presence</li></ul><a href="en-ceuta-melilla.html">Open dossier →</a></article><article class="gwc-feature-card blue"><p class="gwc-kicker">SPAIN–MOROCCO</p><h2>Cooperation and competition at the same time</h2><p>Trade, migration, security, Western Sahara, ports and the 2030 World Cup require cooperation while deep interests and frictions remain.</p><ul><li>Economic interdependence</li><li>Border cooperation</li><li>Port and diplomatic competition</li></ul><a href="en-spain-morocco.html">View bilateral timeline →</a></article></section>

  <section class="gwc-control" aria-labelledby="gwc-control-title"><header><p class="gwc-kicker">DISTRIBUTED POWER</p><h2 id="gwc-control-title">No one controls the Strait alone</h2><p>Real capacity is divided among coasts, ports, traffic centres, alliances and maritime law.</p></header><div class="gwc-control-grid"><article><small>SPAIN</small><strong>Tarifa, Algeciras and Ceuta</strong><p>Monitoring, ports, defence and presence on the northern shore.</p></article><article><small>MOROCCO</small><strong>Tangier and Tanger Med</strong><p>Southern shore, ports and migration cooperation.</p></article><article><small>UNITED KINGDOM</small><strong>Gibraltar and its port</strong><p>Enclave, naval base and maritime services.</p></article><article><small>INTERNATIONAL FRAMEWORK</small><strong>GIBREP and freedom of navigation</strong><p>Rules and coordination prevent the corridor being reduced to one actor.</p></article></div><a class="gwc-text-link" href="en-who-controls-strait.html">Understand who really controls the Strait →</a></section>

  <section class="gwc-analysis" aria-labelledby="gwc-analysis-title"><header class="gwc-section-head"><div><p class="gwc-kicker">ANALYSIS AND SCENARIOS</p><h2 id="gwc-analysis-title">Questions that need context</h2></div></header><div class="gwc-analysis-grid"><a href="en-scenarios.html"><small>SCENARIOS</small><h3>Which signs would indicate a genuine strategic crisis</h3><p>Indicators, impact and limits of each hypothesis.</p><b>Read →</b></a><a href="en-who-controls-strait.html"><small>CONTROL</small><h3>Why Ceuta and Melilla matter without granting automatic control</h3><p>Coasts, ports, navigation and alliances.</p><b>Read →</b></a><a href="en-scenarios.html"><small>ECONOMY</small><h3>What disruption would mean for Europe and Africa</h3><p>Routes, supply chains and costs.</p><b>Read →</b></a></div></section>

  <section class="gwc-territory" aria-labelledby="gwc-territory-title"><header><p class="gwc-kicker">TERRITORY AND FUTURE</p><h2 id="gwc-territory-title">Science remains without dominating the narrative</h2><p>Geology, seismicity, water exchange and the tunnel remain essential, but they do not prove closure on a human timescale.</p></header><div class="gwc-territory-grid"><a href="en-geology.html"><span>01</span><h3>Arc geology</h3><p>Regional convergence and complex deformation.</p></a><a href="en-seismicity.html"><span>02</span><h3>Seismic monitor</h3><p><b id="gwcQuakes30">—</b> events over 30 days.</p></a><a href="en-future.html"><span>03</span><h3>Could it close?</h3><p>Geological timescales, not a countdown.</p></a><a href="en-tunnel.html"><span>04</span><h3>Fixed link</h3><p>Real status of Spain–Morocco studies.</p></a></div></section>

  <section class="gwc-contact-cta"><div><p class="gwc-kicker">CORRECTIONS AND SOURCES</p><h2>A useful observatory must be open to correction</h2><p>Send documents, primary sources or a reasoned correction through the professional mailbox.</p></div><a class="gwc-button primary" href="en-contact.html">contacto@estrechogibraltar.com</a></section>
  <!-- GWC_HOME_END -->
</main>'''


def is_english(text: str) -> bool:
    return bool(re.search(r'<html\b[^>]*\blang=["\']en(?:-[^"\']+)?["\']', text, re.I))


def stable_write(path: Path, text: str) -> None:
    previous = path.read_text(encoding="utf-8") if path.exists() else None
    if previous != text:
        path.write_text(text, encoding="utf-8")


def ensure_asset(text: str, filename: str, tag: str) -> str:
    if filename in text:
        return text
    return text.replace("</head>", tag + "\n</head>", 1)


def replace_block(text: str, tag: str, class_name: str, replacement: str) -> str:
    pattern = re.compile(
        rf'<{tag}\b(?=[^>]*class=["\'][^"\']*\b{re.escape(class_name)}\b[^"\']*["\'])[^>]*>.*?</{tag}>',
        re.I | re.S,
    )
    if pattern.search(text):
        return pattern.sub(replacement, text, count=1)
    return text


def update_head(text: str, english: bool) -> str:
    title = (
        "Strait of Gibraltar: traffic, economy and geopolitics"
        if english else
        "Estrecho de Gibraltar: tráfico, economía y geopolítica"
    )
    description = (
        "Independent Strait of Gibraltar observatory covering maritime traffic, ports, Ceuta and Melilla, Spain–Morocco relations, security and strategic scenarios."
        if english else
        "Observatorio independiente del Estrecho de Gibraltar sobre tráfico marítimo, puertos, Ceuta y Melilla, relaciones España–Marruecos, seguridad y escenarios estratégicos."
    )
    text = re.sub(r'<title>.*?</title>', f'<title>{html.escape(title)}</title>', text, count=1, flags=re.I | re.S)
    if re.search(r'<meta\b[^>]*name=["\']description["\'][^>]*>', text, re.I):
        text = re.sub(
            r'<meta\b[^>]*name=["\']description["\'][^>]*>',
            f'<meta name="description" content="{html.escape(description, quote=True)}"/>',
            text,
            count=1,
            flags=re.I,
        )
    else:
        text = text.replace("</title>", f'</title><meta name="description" content="{html.escape(description, quote=True)}"/>', 1)
    for prop in ("og:title", "twitter:title"):
        text = re.sub(
            rf'<meta\b[^>]*(?:property|name)=["\']{re.escape(prop)}["\'][^>]*>',
            f'<meta {"property" if prop.startswith("og:") else "name"}="{prop}" content="{html.escape(title, quote=True)}"/>',
            text,
            count=1,
            flags=re.I,
        )
    for prop in ("og:description", "twitter:description"):
        text = re.sub(
            rf'<meta\b[^>]*(?:property|name)=["\']{re.escape(prop)}["\'][^>]*>',
            f'<meta {"property" if prop.startswith("og:") else "name"}="{prop}" content="{html.escape(description, quote=True)}"/>',
            text,
            count=1,
            flags=re.I,
        )
    return text


def patch_html(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    english = is_english(text)
    text = ensure_asset(text, CSS_FILE, f'<link href="{CSS_FILE}?v=20260803-1" rel="stylesheet"/>')
    text = ensure_asset(text, JS_FILE, f'<script defer src="{JS_FILE}?v=20260803-1"></script>')
    text = replace_block(text, "nav", "site-nav", NAV_EN if english else NAV_ES)
    text = replace_block(text, "footer", "site-footer", FOOTER_EN if english else FOOTER_ES)
    stable_write(path, text)


def patch_home(path: Path, english: bool) -> None:
    text = path.read_text(encoding="utf-8")
    # Home is rebuilt from scratch; legacy overlay assets would only add weight and
    # can reintroduce inherited layout rules. They remain available on inner pages.
    for legacy in ("gibraltar-growth.css", "gibraltar-growth.js", "gibraltar-strategy.css", "gibraltar-strategy.js", "gibraltar-top.css", "gibraltar-top.js", "app.js"):
        text = re.sub(rf'<(?:link|script)\b[^>]*(?:href|src)=["\'][^"\']*{re.escape(legacy)}[^"\']*["\'][^>]*>(?:</script>)?', '', text, flags=re.I)
    text = re.sub(r'<main\b[^>]*>.*?</main>', HOME_EN if english else HOME_ES, text, count=1, flags=re.I | re.S)
    text = update_head(text, english)
    text = re.sub(r'<body\b([^>]*)>', lambda m: '<body' + (m.group(1) or '') + ' class="gwc-page">' if 'class=' not in (m.group(1) or '') else m.group(0), text, count=1, flags=re.I)
    stable_write(path, text)


def mark_active_links(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    filename = path.name
    # Remove prior page markers without disturbing other classes.
    text = re.sub(r'\saria-current=["\']page["\']', '', text, flags=re.I)
    text = re.sub(
        rf'(<a\b[^>]*href=["\']{re.escape(filename)}["\'][^>]*)>',
        r'\1 aria-current="page">',
        text,
        count=1,
        flags=re.I,
    )
    stable_write(path, text)


def rebuild_sitemap() -> None:
    excluded = {"404.html"}
    pages = []
    for path in sorted(ROOT.glob("*.html")):
        if path.name in excluded or path.name.startswith("google"):
            continue
        pages.append(path.name)
    ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("", ns)
    urlset = ET.Element(f"{{{ns}}}urlset")
    daily = {"situacion-actual.html", "en-current-situation.html", "operacion-paso-estrecho-2026.html", "en-strait-crossing-operation-2026.html", "situacion-actual.html", "en-current-situation.html"}
    hourly = {"sismicidad.html", "en-seismicity.html"}
    priority_high = {"index.html", "en.html", "trafico.html", "en-traffic.html", "situacion-actual.html", "en-current-situation.html", "ceuta-melilla.html", "en-ceuta-melilla.html", "espana-marruecos.html", "en-spain-morocco.html"}
    for name in pages:
        url = ET.SubElement(urlset, f"{{{ns}}}url")
        loc = ET.SubElement(url, f"{{{ns}}}loc")
        loc.text = "https://estrechogibraltar.com/" if name == "index.html" else f"https://estrechogibraltar.com/{name}"
        ET.SubElement(url, f"{{{ns}}}lastmod").text = TODAY
        freq = "hourly" if name in hourly else "daily" if name in daily else "weekly"
        ET.SubElement(url, f"{{{ns}}}changefreq").text = freq
        priority = "1.0" if name == "index.html" else "0.9" if name in priority_high else "0.7"
        ET.SubElement(url, f"{{{ns}}}priority").text = priority
    tree = ET.ElementTree(urlset)
    ET.indent(tree, space="  ")
    tree.write(ROOT / "sitemap.xml", encoding="utf-8", xml_declaration=True)


def update_robots() -> None:
    stable_write(ROOT / "robots.txt", "User-agent: *\nAllow: /\n\nSitemap: https://estrechogibraltar.com/sitemap.xml\n")


def main() -> int:
    for path in ROOT.glob("*.html"):
        patch_html(path)
    for filename, english in (("index.html", False), ("en.html", True)):
        path = ROOT / filename
        if path.exists():
            patch_home(path, english)
            patch_html(path)
    for path in ROOT.glob("*.html"):
        mark_active_links(path)
    rebuild_sitemap()
    update_robots()
    print("Gibraltar Watch consolidado: portada, navegación, pie y sitemap.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
