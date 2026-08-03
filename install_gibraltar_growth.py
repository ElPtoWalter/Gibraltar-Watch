#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
STYLE='<link rel="stylesheet" href="gibraltar-growth.css?v=growth-20260803-1">'
SCRIPT='<script defer src="gibraltar-growth.js?v=growth-20260803-1"></script>'
ES_BLOCK='<section class="gw-growth-links" data-growth="strategic-search"><div><small>TRÁFICO Y LOGÍSTICA</small><h2>La demanda de búsqueda señala tres temas</h2></div><nav><a href="trafico.html"><b>Tráfico marítimo</b><span>Radar AIS y GIBREP</span></a><a href="operacion-paso-estrecho-2026.html"><b>OPE 2026</b><span>Ferris, pasajeros y vehículos</span></a><a href="servicios-buques-estrecho-gibraltar.html"><b>Servicios a buques</b><span>Bunkering, reparaciones y agentes</span></a><a href="impacto-cierre-gibraltar-comercio-europa-africa.html"><b>Comercio y seguridad</b><span>Impacto de una alteración</span></a></nav></section>'
EN_BLOCK='<section class="gw-growth-links" data-growth="strategic-search"><div><small>TRAFFIC AND LOGISTICS</small><h2>Search demand points to three themes</h2></div><nav><a href="en-traffic.html"><b>Maritime traffic</b><span>AIS radar and GIBREP</span></a><a href="en-strait-crossing-operation-2026.html"><b>OPE 2026</b><span>Ferries, passengers and vehicles</span></a><a href="en-ship-services-strait-gibraltar.html"><b>Vessel services</b><span>Bunkering, repairs and agents</span></a><a href="en-impact-gibraltar-closure-trade-europe-africa.html"><b>Trade and security</b><span>Impact of disruption</span></a></nav></section>'
HOME_ES='<section class="gw-home-growth" data-growth="traffic-demand"><div><small>LO QUE MÁS BUSCAN LOS LECTORES</small><h2>Tráfico marítimo, ferris y servicios del Estrecho</h2><p>Accede al radar AIS, al panel oficial de la OPE 2026 y a la guía de servicios a buques.</p></div><nav><a href="trafico.html"><b>Radar AIS</b><span>Tráfico marítimo en directo</span></a><a href="operacion-paso-estrecho-2026.html"><b>OPE 2026</b><span>Pasajeros y vehículos</span></a><a href="servicios-buques-estrecho-gibraltar.html"><b>Servicios</b><span>Actividad portuaria</span></a></nav></section>'
HOME_EN='<section class="gw-home-growth" data-growth="traffic-demand"><div><small>WHAT READERS SEARCH FOR</small><h2>Maritime traffic, ferries and Strait services</h2><p>Open the AIS radar, the official OPE 2026 panel and the vessel-services guide.</p></div><nav><a href="en-traffic.html"><b>AIS radar</b><span>Live maritime traffic</span></a><a href="en-strait-crossing-operation-2026.html"><b>OPE 2026</b><span>Passengers and vehicles</span></a><a href="en-ship-services-strait-gibraltar.html"><b>Services</b><span>Port activity</span></a></nav></section>'

def add_assets(text):
    if 'gibraltar-growth.css' not in text:
        text=text.replace('</head>',STYLE+'</head>')
    if 'gibraltar-growth.js' not in text:
        text=text.replace('</body>',SCRIPT+'</body>')
    return text

def patch(path,lang,kind):
    p=ROOT/path
    if not p.exists(): return
    t=p.read_text(encoding='utf-8')
    t=add_assets(t)
    if kind=='importance':
        if lang=='es':
            t=re.sub(r'<title>.*?</title>','<title>Importancia del Estrecho de Gibraltar: comercio y seguridad</title>',t,count=1,flags=re.S)
            t=re.sub(r'<meta content="[^"]*" name="description"\s*/?>','<meta content="Por qué el Estrecho de Gibraltar es estratégico para el comercio, los puertos, la energía, la seguridad marítima y la conexión entre Europa y África." name="description"/>',t,count=1)
            block=ES_BLOCK
        else:
            t=re.sub(r'<title>.*?</title>','<title>Why the Strait of Gibraltar matters: trade and security</title>',t,count=1,flags=re.S)
            t=re.sub(r'<meta content="[^"]*" name="description"\s*/?>','<meta content="Why the Strait of Gibraltar matters for trade, ports, energy, maritime security and the link between Europe and Africa." name="description"/>',t,count=1)
            block=EN_BLOCK
    else:
        block=HOME_ES if lang=='es' else HOME_EN
    if 'data-growth="'+('strategic-search' if kind=='importance' else 'traffic-demand')+'"' not in t:
        marker='<!-- GT_EDITORIAL_RECORD -->' if '<!-- GT_EDITORIAL_RECORD -->' in t else '</main>'
        t=t.replace(marker,block+marker,1)
    p.write_text(t,encoding='utf-8')

for args in [('importancia.html','es','importance'),('en-importance.html','en','importance'),('index.html','es','home'),('en.html','en','home'),('parte-diario.html','es','home'),('en-daily-brief.html','en','home')]: patch(*args)

# Add stylesheet for home teaser to growth CSS only once
css=ROOT/'gibraltar-growth.css'
if css.exists():
    s=css.read_text(encoding='utf-8')
    marker='/* GW_HOME_GROWTH */'
    if marker not in s:
        s += '\n/* GW_HOME_GROWTH */\n.gw-home-growth{display:grid;grid-template-columns:minmax(250px,.7fr) minmax(0,1.3fr);gap:30px;padding:38px 0;border-top:3px solid var(--ink);border-bottom:1px solid var(--line);margin:64px 0}.gw-home-growth small{font:600 9px "IBM Plex Mono";letter-spacing:.15em;color:var(--accent)}.gw-home-growth h2{font-family:"Newsreader";font-size:clamp(34px,4vw,56px);line-height:1;margin:10px 0}.gw-home-growth p{color:var(--muted)}.gw-home-growth nav{display:grid;grid-template-columns:repeat(3,1fr)}.gw-home-growth a{padding:24px 20px;border-left:1px solid var(--line);text-decoration:none}.gw-home-growth b,.gw-home-growth span{display:block}.gw-home-growth b{font-family:"Newsreader";font-size:25px}.gw-home-growth span{font-size:11px;color:var(--muted);margin-top:5px}.gw-home-growth a:hover{background:var(--accent-soft)}@media(max-width:800px){.gw-home-growth{grid-template-columns:1fr}.gw-home-growth nav{grid-template-columns:1fr}.gw-home-growth a{border-left:0;border-top:1px solid var(--line);padding-left:0}}\n'
        css.write_text(s,encoding='utf-8')

# Preserve current sitemap and add new URLs only
smap=ROOT/'sitemap.xml'
if smap.exists():
    ET.register_namespace('', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    tree=ET.parse(smap); root=tree.getroot(); ns='{http://www.sitemaps.org/schemas/sitemap/0.9}'
    existing={u.findtext(ns+'loc') for u in root.findall(ns+'url')}
    pages=[
      ('https://estrechogibraltar.com/operacion-paso-estrecho-2026.html','daily','0.9'),
      ('https://estrechogibraltar.com/en-strait-crossing-operation-2026.html','daily','0.8'),
      ('https://estrechogibraltar.com/servicios-buques-estrecho-gibraltar.html','monthly','0.8'),
      ('https://estrechogibraltar.com/en-ship-services-strait-gibraltar.html','monthly','0.7')]
    for url,freq,prio in pages:
        if url in existing: continue
        e=ET.SubElement(root,ns+'url');ET.SubElement(e,ns+'loc').text=url;ET.SubElement(e,ns+'lastmod').text='2026-08-03';ET.SubElement(e,ns+'changefreq').text=freq;ET.SubElement(e,ns+'priority').text=prio
    tree.write(smap,encoding='utf-8',xml_declaration=True)

llms=ROOT/'llms.txt'
if llms.exists():
    t=llms.read_text(encoding='utf-8')
    for line in ['- OPE 2026 dashboard: https://estrechogibraltar.com/operacion-paso-estrecho-2026.html','- Vessel services guide: https://estrechogibraltar.com/servicios-buques-estrecho-gibraltar.html']:
        if line not in t:t+='\n'+line
    llms.write_text(t.rstrip()+'\n',encoding='utf-8')
print('Gibraltar Growth instalado y sitemap preservado.')
