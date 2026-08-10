#!/usr/bin/env python3
"""Independent live-site smoke test for the daily audit workflow."""
from __future__ import annotations
import argparse,json,sys,urllib.request,urllib.error
from datetime import datetime,timezone
from xml.etree import ElementTree as ET

UA='GibraltarWatch-Audit/1.0'
def get(url,timeout=25):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'*/*'})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        if r.status!=200:raise RuntimeError(f'HTTP {r.status}: {url}')
        return r.read()
def main():
    p=argparse.ArgumentParser();p.add_argument('--base-url',default='https://estrechogibraltar.com/');p.add_argument('--max-age-hours',type=float,default=12);a=p.parse_args();base=a.base_url.rstrip('/')+'/'
    urls=['','situacion-actual.html','datos.html','mapa-estrategico.html','transparencia.html','diario/','observatory.json','health.json','sitemap.xml','observatory-feed.xml']
    errors=[]
    blobs={}
    for rel in urls:
        try:blobs[rel]=get(base+rel)
        except Exception as e:errors.append(f'{rel or "home"}: {e}')
    try:
        health=json.loads(blobs['health.json']);stamp=datetime.fromisoformat(health['generated_at'].replace('Z','+00:00')).astimezone(timezone.utc);age=(datetime.now(timezone.utc)-stamp).total_seconds()/3600
        if age>a.max_age_hours:errors.append(f'health.json tiene {age:.1f} h de antigüedad')
        if health.get('overall')=='stale':print('::warning::El sitio responde, pero health.json marca fuentes desactualizadas.')
    except Exception as e:errors.append(f'health.json no verificable: {e}')
    try:
        obs=json.loads(blobs['observatory.json']);
        if (obs.get('state') or {}).get('code') not in {'normal','watch','reinforced_watch','high_watch','operational_alert'}:errors.append('observatory.json contiene un estado inválido')
    except Exception as e:errors.append(f'observatory.json no verificable: {e}')
    for rel in ['sitemap.xml','observatory-feed.xml']:
        try:ET.fromstring(blobs[rel])
        except Exception as e:errors.append(f'{rel} XML inválido: {e}')
    try:
        home=blobs[''].decode('utf-8','replace')
        if 'gw-observatory.js' not in home:errors.append('La portada publicada no contiene la capa vNext')
    except Exception as e:errors.append(f'portada no verificable: {e}')
    if errors:
        for x in errors:print(f'::error::{x}')
        return 1
    print('SMOKE OK · Gibraltar Watch responde y el observatorio está fresco.')
    return 0
if __name__=='__main__':raise SystemExit(main())
