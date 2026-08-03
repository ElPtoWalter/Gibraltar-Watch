#!/usr/bin/env python3
"""Update Gibraltar Watch OPE 2026 data from official Civil Protection reports.

The updater is deliberately conservative: it preserves the last valid result when a
new official PDF cannot be discovered or parsed. It never invents daily figures.
"""
from __future__ import annotations
import io,json,re,sys,urllib.request,urllib.error,urllib.parse,html
from datetime import datetime,timezone,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'ope-2026.json';HISTORY=ROOT/'ope-history.json';SOURCES=ROOT/'ope-sources.json'
MONTHS={'enero':1,'febrero':2,'marzo':3,'abril':4,'mayo':5,'junio':6,'julio':7,'agosto':8,'septiembre':9,'octubre':10,'noviembre':11,'diciembre':12}
UA='GibraltarWatch/3.0 (+https://estrechogibraltar.com/contacto.html)'
CAMPAIGN='https://www.proteccioncivil.es/coordinacion/campanas/operaci%C3%B3n-paso-del-estrecho'
def load(p,d):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except Exception:return d
def iso(dt):return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def fetch_bytes(url,timeout=50):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/pdf,text/html;q=0.8,*/*;q=0.2'})
    with urllib.request.urlopen(req,timeout=timeout) as r:return r.read(),r.geturl(),r.headers.get_content_type()
def to_int(s):return int(re.sub(r'[^0-9]','',str(s)) or 0)
def parse_date(text):
    m=re.search(r'(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(2026)',text,re.I)
    if not m:return None
    return datetime(int(m.group(3)),MONTHS[m.group(2).lower()],int(m.group(1)),tzinfo=timezone.utc).date()
def rows(section):
    result=[]
    for line in section.splitlines():
        line=' '.join(line.split())
        m=re.match(r'(.+?)\s+(\d+)\s+([\d\.]+)\s+([\d\.]+)$',line)
        if not m:continue
        name=m.group(1).strip()
        if '/' not in name:continue
        result.append({'name':name,'rotations':to_int(m.group(2)),'passengers':to_int(m.group(3)),'vehicles':to_int(m.group(4))})
    return result
def totals(section,label):
    m=re.search(label+r'\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)',section,re.I)
    return {'rotations':to_int(m.group(1)),'passengers':to_int(m.group(2)),'vehicles':to_int(m.group(3))} if m else {'rotations':0,'passengers':0,'vehicles':0}
def parse_pdf(blob,url):
    from pypdf import PdfReader
    reader=PdfReader(io.BytesIO(blob));text='\n'.join((p.extract_text() or '') for p in reader.pages)
    date=parse_date(text)
    if not date:raise ValueError('report date not found')
    parts=re.split(r'Parte diario general\s*-\s*Operación Retorno',text,maxsplit=1,flags=re.I)
    dep=parts[0];ret=parts[1] if len(parts)>1 else ''
    dep_day=totals(dep,r'Total general d[ií]a');dep_cum=totals(dep,r'Total acumulado')
    ret_day=totals(ret,r'Total general (?:del )?d[ií]a');ret_cum=totals(ret,r'Total acumulado')
    dep_rows=rows(dep);ret_rows=rows(ret)
    if not dep_day['passengers'] or not dep_rows:raise ValueError('departure table not parsed')
    months_es=['','enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre']
    months_en=['','January','February','March','April','May','June','July','August','September','October','November','December']
    return {'season':2026,'status':'OK','checked_at':iso(datetime.now(timezone.utc)),'report_date':date.isoformat(),'report_label_es':f'{date.day} de {months_es[date.month]} de {date.year}','report_label_en':f'{date.day} {months_en[date.month]} {date.year}','source':'Secretaría General de Protección Civil y Emergencias','source_url':url,'campaign_url':'https://www.proteccioncivil.es/coordinacion/campanas/operaci%C3%B3n-paso-del-estrecho','season_start':'2026-06-15','season_end':'2026-09-15','departure':{'day':dep_day,'cumulative':dep_cum,'routes':sorted(dep_rows,key=lambda r:r['passengers'],reverse=True)[:8]},'return':{'day':ret_day,'cumulative':ret_cum,'routes':sorted(ret_rows,key=lambda r:r['passengers'],reverse=True)[:8]},'advice_es':'Protección Civil recomienda planificar el viaje y acudir al puerto con billete cerrado adquirido con antelación.','advice_en':'Spanish Civil Protection recommends planning the journey and arriving at the port with a pre-booked closed ticket.','data_note_es':'Último informe oficial localizado. No es un contador en tiempo real.','data_note_en':'Latest official report located. This is not a real-time counter.'}
def discover_official_links():
    """Find report links exposed by the official OPE campaign pages."""
    out=[]
    pages=[CAMPAIGN, CAMPAIGN+'/informes-diarios', CAMPAIGN+'/estadisticas']
    for page in pages:
        try:
            req=urllib.request.Request(page,headers={'User-Agent':UA,'Accept':'text/html,*/*;q=0.5'})
            with urllib.request.urlopen(req,timeout=35) as r:
                body=r.read().decode(r.headers.get_content_charset() or 'utf-8','replace')
            body=html.unescape(body)
            for href in re.findall(r'href=["\']([^"\']*InformeOPE\.pdf[^"\']*)',body,re.I):
                url=urllib.parse.urljoin(page,href)
                m=re.search(r'(20\d{6})_InformeOPE',url,re.I)
                if m:
                    d=datetime.strptime(m.group(1),'%Y%m%d').date().isoformat()
                    out.append({'date':d,'url':url})
        except Exception:
            continue
    return out

def candidate_urls():
    known=load(SOURCES,[])
    out=discover_official_links()
    # Try stable document paths for recent dates; Liferay may redirect them to the current UUID.
    now=datetime.now(timezone.utc).date()
    for i in range(14):
        d=now-timedelta(days=i);name=d.strftime('%Y%m%d')+'_InformeOPE.pdf'
        out.append({'date':d.isoformat(),'url':'https://www.proteccioncivil.es/documents/20121/0/'+name})
    out.extend(known)
    seen=set();return [x for x in sorted(out,key=lambda x:x.get('date',''),reverse=True) if not (x['url'] in seen or seen.add(x['url']))]
def update_sitemap(date):
    p=ROOT/'sitemap.xml'
    if not p.exists():return
    t=p.read_text(encoding='utf-8')
    for slug in ('operacion-paso-estrecho-2026','en-strait-crossing-operation-2026','trafico','en-traffic'):
        t=re.sub(r'(<loc>[^<]*'+re.escape(slug)+r'[^<]*</loc>\s*<lastmod>)[^<]+',r'\g<1>'+date,t)
    p.write_text(t,encoding='utf-8')
def main():
    previous=load(OUT,{})
    errors=[]
    for item in candidate_urls():
        try:
            blob,final,ctype=fetch_bytes(item['url'])
            if not blob.startswith(b'%PDF'):continue
            data=parse_pdf(blob,final)
            if previous.get('report_date') and data['report_date']<previous['report_date']:continue
            OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            hist=load(HISTORY,[])
            snap={'report_date':data['report_date'],'departure':data['departure']['day'],'return':data['return']['day'],'source_url':data['source_url']}
            hist=[x for x in hist if x.get('report_date')!=data['report_date']];hist.insert(0,snap)
            HISTORY.write_text(json.dumps(hist[:100],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            known=load(SOURCES,[])
            if not any(x.get('url')==final for x in known):
                known.insert(0,{'date':data['report_date'],'url':final});SOURCES.write_text(json.dumps(known[:40],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            update_sitemap(data['report_date'])
            print('OPE updated:',data['report_date'],data['departure']['day']['passengers'])
            return 0
        except Exception as exc:errors.append(type(exc).__name__+': '+str(exc))
    if previous:
        previous['last_attempt_at']=iso(datetime.now(timezone.utc));previous['last_error']=' | '.join(errors[-3:]) or 'No official report located'
        OUT.write_text(json.dumps(previous,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print('OPE preserved:',previous.get('report_date'))
        return 0
    print('No valid OPE data and no previous file',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
