#!/usr/bin/env python3
"""Update recent seismicity for Gibraltar Watch using the official USGS FDSN service."""
from __future__ import annotations
import json, os, sys, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parent
CFG=json.loads((ROOT/'config.json').read_text(encoding='utf-8'))
OUT=ROOT/'seismicity.json'; HISTORY=ROOT/'seismic-history.json'

def iso(dt): return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def fetch(url,timeout=45):
    req=urllib.request.Request(url,headers={'User-Agent':'GibraltarWatch/1.0 (educational; GitHub Pages)'})
    with urllib.request.urlopen(req,timeout=timeout) as r: return json.load(r)
def load(path,default):
    try:return json.loads(path.read_text(encoding='utf-8'))
    except Exception:return default

def main():
    now=datetime.now(timezone.utc); start=now-timedelta(days=30)
    r=CFG['region']
    params={'format':'geojson','starttime':iso(start),'endtime':iso(now),'minlatitude':r['min_lat'],'maxlatitude':r['max_lat'],'minlongitude':r['min_lon'],'maxlongitude':r['max_lon'],'minmagnitude':CFG.get('minimum_magnitude',1.0),'orderby':'time','limit':20000}
    url='https://earthquake.usgs.gov/fdsnws/event/1/query?'+urllib.parse.urlencode(params)
    previous=load(OUT,{})
    try:
        data=fetch(url)
        events=[]
        for f in data.get('features',[]):
            p=f.get('properties') or {}; g=(f.get('geometry') or {}).get('coordinates') or []
            if len(g)<3 or p.get('mag') is None: continue
            t=datetime.fromtimestamp((p.get('time') or 0)/1000,tz=timezone.utc)
            events.append({'id':f.get('id'),'time':iso(t),'magnitude':round(float(p['mag']),1),'place':p.get('place') or 'Región del Estrecho','longitude':round(float(g[0]),4),'latitude':round(float(g[1]),4),'depth_km':round(float(g[2]),1),'url':p.get('url') or '', 'reviewed':p.get('status')=='reviewed'})
        events.sort(key=lambda x:x['time'],reverse=True)
        def count(days):
            cutoff=now-timedelta(days=days)
            return sum(datetime.fromisoformat(e['time'].replace('Z','+00:00'))>=cutoff for e in events)
        p24,p7,p30=count(1),count(7),len(events)
        maxmag=max((e['magnitude'] for e in events),default=None)
        if maxmag is None: note_es='No se registran eventos M≥1 en el área consultada durante los últimos 30 días.'; note_en='No M≥1 events are present in the queried area during the last 30 days.'
        elif maxmag>=4.5: note_es=f'Actividad reciente con un evento máximo de magnitud {maxmag:.1f}. Consulta siempre la información oficial del IGN.'; note_en=f'Recent activity includes a maximum magnitude {maxmag:.1f} event. Always consult official seismic authorities.'
        elif maxmag>=3: note_es=f'Se han registrado {p30} eventos; magnitud máxima {maxmag:.1f} en 30 días.'; note_en=f'{p30} events recorded; maximum magnitude {maxmag:.1f} over 30 days.'
        else: note_es=f'Se han registrado {p30} eventos de baja magnitud en el catálogo consultado durante 30 días.'; note_en=f'{p30} low-magnitude events appear in the queried catalogue over 30 days.'
        result={'checked_at':iso(now),'source':'USGS Earthquake Catalog','source_query':url,'status':'OK','data_note_es':note_es,'data_note_en':note_en,'periods':{'24h':p24,'7d':p7,'30d':p30},'max_magnitude_30d':maxmag,'last_event':events[0] if events else None,'events':events[:200],'history_updated':False}
        hist=load(HISTORY,[]); today=now.date().isoformat()
        snapshot={'date':today,'checked_at':iso(now),'count_24h':p24,'count_7d':p7,'count_30d':p30,'max_magnitude_30d':maxmag}
        if not hist or hist[0].get('date')!=today:
            hist.insert(0,snapshot); hist=hist[:730]; result['history_updated']=True
            HISTORY.write_text(json.dumps(hist,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        else:
            hist[0]=snapshot; HISTORY.write_text(json.dumps(hist,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        update_feed(result)
        update_sitemap(now)
        print(f'Updated: {p30} events, max={maxmag}')
    except Exception as exc:
        print(f'WARNING: {type(exc).__name__}: {exc}',file=sys.stderr)
        if previous:
            previous['last_attempt_at']=iso(now); previous['last_error']=type(exc).__name__
            OUT.write_text(json.dumps(previous,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        else: raise

def update_feed(d):
    latest=d.get('last_event'); item=''
    if latest:
        item=f"""<entry><title>M {latest['magnitude']} — {xml(latest['place'])}</title><id>{xml(latest['url'] or latest['id'])}</id><link href="{xml(latest['url'])}"/><updated>{latest['time']}</updated><summary>Depth {latest['depth_km']} km.</summary></entry>"""
    feed=f"""<?xml version="1.0" encoding="utf-8"?><feed xmlns="http://www.w3.org/2005/Atom"><title>Gibraltar Watch — seismicity</title><id>{CFG['base_url']}feed.xml</id><link href="{CFG['base_url']}feed.xml" rel="self"/><link href="{CFG['base_url']}"/><updated>{d['checked_at']}</updated>{item}</feed>"""
    (ROOT/'feed.xml').write_text(feed,encoding='utf-8')
def xml(s):
    return str(s or '').replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')
def update_sitemap(now):
    # only update lastmod on data-heavy pages; full sitemap remains deterministic
    path=ROOT/'sitemap.xml'
    if not path.exists(): return
    text=path.read_text(encoding='utf-8')
    import re
    date=now.date().isoformat()
    text=re.sub(r'(<loc>[^<]*(?:sismicidad|seismicity)[^<]*</loc>\s*<lastmod>)[^<]+',r'\g<1>'+date,text)
    path.write_text(text,encoding='utf-8')
if __name__=='__main__': main()
