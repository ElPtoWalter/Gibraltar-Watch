#!/usr/bin/env python3
"""Fail the update before commit if Gibraltar Watch would publish an invalid build."""
from __future__ import annotations

import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parent
ERRORS=[]; WARNINGS=[]
CRITICAL=[
 'index.html','situacion-actual.html','trafico.html','sismicidad.html','fuentes.html',
 'datos.html','mapa-estrategico.html','transparencia.html','correcciones.html','boletin.html',
 'gw-observatory.css','gw-observatory.js','observatory.json','health.json','timeline.json',
 'observatory-history.json','observatory-feed.xml','publication-manifest.json','sitemap.xml','diario/index.html','diario/latest.json','newsletter/latest.html','newsletter/latest.txt','newsletter/latest.json'
]
JSON_FILES=['observatory.json','health.json','timeline.json','observatory-history.json','publication-manifest.json','newsletter/latest.json','diario/latest.json','geopolitics.json','seismicity.json','ope-2026.json','corrections.json']
NEW_PAGES=['datos.html','mapa-estrategico.html','transparencia.html','correcciones.html','boletin.html']

def err(msg): ERRORS.append(msg)
def warn(msg): WARNINGS.append(msg)

def read(path):
    try:return (ROOT/path).read_text(encoding='utf-8')
    except Exception as e:err(f'{path}: no se puede leer ({e})');return ''

def load(path):
    try:return json.loads(read(path))
    except Exception as e:err(f'{path}: JSON inválido ({e})');return None

def validate_files():
    for rel in CRITICAL:
        p=ROOT/rel
        if not p.exists() or (p.is_file() and p.stat().st_size==0):err(f'Falta archivo crítico: {rel}')
    for rel in JSON_FILES:
        if (ROOT/rel).exists():load(rel)

def validate_observatory():
    obs=load('observatory.json') or {}; health=load('health.json') or {}
    allowed={'normal','watch','reinforced_watch','high_watch','operational_alert'}
    if (obs.get('state') or {}).get('code') not in allowed:err('observatory.json: state.code no permitido')
    if health.get('overall') not in {'healthy','degraded','stale'}:err('health.json: overall no permitido')
    for rel,obj in [('observatory.json',obs),('health.json',health)]:
        stamp=obj.get('generated_at')
        try:
            dt=datetime.fromisoformat(str(stamp).replace('Z','+00:00')).astimezone(timezone.utc)
            age=(datetime.now(timezone.utc)-dt).total_seconds()/3600
            if age>2:warn(f'{rel}: generado hace {age:.1f} h durante la validación')
        except Exception:err(f'{rel}: generated_at inválido')

def validate_xml():
    for rel in ['sitemap.xml','observatory-feed.xml']:
        try:ET.parse(ROOT/rel)
        except Exception as e:err(f'{rel}: XML inválido ({e})')
    sm=read('sitemap.xml')
    for p in NEW_PAGES:
        if f'https://estrechogibraltar.com/{p}' not in sm:err(f'sitemap.xml no contiene {p}')

def validate_html():
    for rel in NEW_PAGES:
        t=read(rel)
        if not re.search(r'<title>[^<]{8,}</title>',t,re.I):err(f'{rel}: title ausente')
        if 'rel="canonical"' not in t:err(f'{rel}: canonical ausente')
        if 'gw-observatory.css' not in t or 'gw-observatory.js' not in t:err(f'{rel}: assets vNext ausentes')
        if t.count('gw-observatory.css')!=1:err(f'{rel}: CSS vNext duplicado')
        ids=re.findall(r'\bid=["\']([^"\']+)["\']',t,re.I)
        dup=sorted({x for x in ids if ids.count(x)>1})
        if dup:err(f'{rel}: IDs HTML duplicados: {", ".join(dup)}')
        for raw in re.findall(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',t,re.I|re.S):
            try:json.loads(raw)
            except Exception as e:err(f'{rel}: JSON-LD inválido ({e})')
        # Validate only relative static refs introduced by these pages.
        refs=re.findall(r'(?:href|src)=["\']([^"\']+)["\']',t,re.I)
        for ref in refs:
            if ref.startswith(('http://','https://','mailto:','tel:','#','data:','javascript:')):continue
            clean=ref.split('?',1)[0].split('#',1)[0]
            if not clean or clean.endswith('/'):
                if clean=='diario/' and not (ROOT/'diario/index.html').exists():err(f'{rel}: referencia rota {ref}')
                continue
            target=(ROOT/clean).resolve()
            if ROOT.resolve() not in target.parents and target!=ROOT.resolve():err(f'{rel}: ruta fuera del sitio {ref}');continue
            if not target.exists():err(f'{rel}: referencia local ausente {ref}')
    core_markers={
        'index.html':['GWO_LIVE_START','GWO_TIMELINE_START'],
        'situacion-actual.html':['GWO_LIVE_START','GWO_DETAIL_START'],
        'fuentes.html':['GWO_HEALTH_START'],
        'trafico.html':['GWO_DETAIL_START'],
    }
    for rel,markers in core_markers.items():
        t=read(rel)
        for marker in markers:
            if marker not in t:err(f'{rel}: falta bloque {marker}')
        if t.count('gw-observatory.css')!=1:err(f'{rel}: assets Observatory ausentes o duplicados')
    latest=load('diario/latest.json') or {}
    slug=latest.get('slug')
    if slug and (ROOT/'diario'/slug).exists():
        t=(ROOT/'diario'/slug).read_text(encoding='utf-8')
        if 'GWO_DIARY_TRUST_START' not in t:err(f'diario/{slug}: falta capa de trazabilidad vNext')

def validate_manifest():
    manifest=load('publication-manifest.json') or {}
    files=manifest.get('files') or {}
    if not files:
        err('publication-manifest.json: sin archivos')
        return
    for rel,meta in files.items():
        path=ROOT/rel
        if not path.exists():
            err(f'publication-manifest.json: falta {rel}')
            continue
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != (meta or {}).get('sha256'):
            err(f'publication-manifest.json: checksum no coincide para {rel}')

def validate_workflow():
    wf=ROOT/'.github/workflows/update-gibraltar.yml'
    if not wf.exists():err('.github/workflows/update-gibraltar.yml no existe');return
    t=wf.read_text(encoding='utf-8')
    if re.search(r'^\s*run:\s*python\s+submit_gibraltar_inde\s*$',t,re.M):err('Workflow: ha reaparecido el nombre truncado submit_gibraltar_inde')
    if 'run: python submit_gibraltar_indexnow.py' not in t:err('Workflow: falta submit_gibraltar_indexnow.py')
    idx=t.find('- name: Avisar mediante IndexNow')
    if idx>=0 and 'continue-on-error: true' in t[idx:idx+260]:err('Workflow: IndexNow vuelve a ocultar errores con continue-on-error')
    required=['install_gibraltar_observatory.py','postprocess_diario.py','update_observatory.py','generate_newsletter.py','build_publication_manifest.py','validate_gibraltar.py']
    for x in required:
        if x not in t:err(f'Workflow: falta etapa {x}')

def main():
    validate_files();validate_observatory();validate_xml();validate_html();validate_manifest();validate_workflow()
    for w in WARNINGS:print(f'::warning::{w}')
    if ERRORS:
        for e in ERRORS:print(f'::error::{e}')
        print(f'VALIDACIÓN FALLIDA: {len(ERRORS)} error(es), {len(WARNINGS)} aviso(s).')
        return 1
    print(f'VALIDACIÓN OK · {len(WARNINGS)} aviso(s) · publicación segura para commit.')
    return 0
if __name__=='__main__':raise SystemExit(main())
