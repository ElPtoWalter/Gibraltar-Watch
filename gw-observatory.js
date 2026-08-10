/* Gibraltar Watch · Observatory vNext */
(() => {
  'use strict';
  const script = document.currentScript;
  const BASE = script ? new URL('.', script.src) : new URL('./', location.href);
  const url = path => new URL(path, BASE).href;
  const cache = {};
  const fetchJSON = async path => {
    if (cache[path]) return cache[path];
    cache[path] = fetch(url(path), { cache: 'no-store' }).then(r => {
      if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
      return r.json();
    });
    return cache[path];
  };
  const qs = (sel, root = document) => root.querySelector(sel);
  const qsa = (sel, root = document) => [...root.querySelectorAll(sel)];
  const text = (el, value, fallback = '—') => { if (el) el.textContent = value ?? fallback; };
  const nfmt = value => Number.isFinite(Number(value)) ? new Intl.NumberFormat('es-ES').format(Number(value)) : '—';
  const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const ago = iso => {
    if (!iso) return 'sin fecha';
    const d = new Date(iso); if (Number.isNaN(d.getTime())) return 'sin fecha';
    const sec = Math.max(0, Math.floor((Date.now() - d.getTime()) / 1000));
    if (sec < 90) return 'hace menos de 1 min';
    const min = Math.floor(sec / 60); if (min < 60) return `hace ${min} min`;
    const h = Math.floor(min / 60); if (h < 48) return `hace ${h} h`;
    return d.toLocaleDateString('es-ES', { day:'numeric', month:'short' });
  };
  const dateTime = iso => {
    const d = new Date(iso); if (Number.isNaN(d.getTime())) return '—';
    return d.toLocaleString('es-ES', { day:'2-digit', month:'short', hour:'2-digit', minute:'2-digit' });
  };

  function setupBrowserAlerts(initial) {
    const buttons=qsa('[data-gwo-enable-alerts]'); if(!buttons.length) return;
    const statusEls=qsa('[data-gwo-alert-status]');
    const setStatus=msg=>statusEls.forEach(el=>text(el,msg));
    if(!('Notification' in window)){buttons.forEach(b=>b.disabled=true);setStatus('Este navegador no admite notificaciones web.');return;}
    const storageKey='gwo-browser-alerts'; const stateKey='gwo-alert-last-state';
    const currentKey=`${initial?.state?.code||''}|${initial?.state?.alert_level?.code||''}`;
    const enable=async()=>{
      const permission=await Notification.requestPermission();
      if(permission!=='granted'){setStatus('Permiso de notificaciones no concedido.');return;}
      localStorage.setItem(storageKey,'enabled'); localStorage.setItem(stateKey,currentKey);
      buttons.forEach(b=>{b.textContent='Alertas activadas';b.disabled=true;});setStatus('Activadas para cambios de nivel mientras mantengas el navegador disponible.');
    };
    buttons.forEach(b=>b.addEventListener('click',enable));
    if(localStorage.getItem(storageKey)==='enabled' && Notification.permission==='granted'){
      buttons.forEach(b=>{b.textContent='Alertas activadas';b.disabled=true;});setStatus('Alertas locales activadas.');
      if(!localStorage.getItem(stateKey)) localStorage.setItem(stateKey,currentKey);
      window.setInterval(async()=>{
        try{
          const r=await fetch(`${url('observatory.json')}?t=${Date.now()}`,{cache:'no-store'});if(!r.ok)return;const latest=await r.json();
          const key=`${latest?.state?.code||''}|${latest?.state?.alert_level?.code||''}`;const previous=localStorage.getItem(stateKey);
          if(previous && key!==previous){
            const level=Number(latest?.state?.severity||0);
            if(level>=2)new Notification(`Gibraltar Watch · ${latest.state.label_es||'Cambio de estado'}`,{body:latest.state.summary_es||'Se ha actualizado el nivel del observatorio.',tag:'gwo-state-alert'});
          }
          localStorage.setItem(stateKey,key);
        }catch(_){/* la auditoría independiente cubre fallos de red */}
      },300000);
    }
  }

  function populateMetric(key, value) {
    qsa(`[data-gwo-metric="${key}"]`).forEach(el => text(el, nfmt(value)));
  }

  function renderState(data, health) {
    const state = data.state || {};
    qsa('[data-gwo-state]').forEach(el => text(el, state.label_es));
    qsa('[data-gwo-summary]').forEach(el => text(el, state.summary_es));
    qsa('[data-gwo-confidence]').forEach(el => text(el, state.confidence));
    qsa('[data-gwo-alert-level]').forEach(el => text(el, state.alert_level?.label_es || 'INFORMATIVO'));
    qsa('[data-gwo-updated]').forEach(el => text(el, ago(data.generated_at)));
    qsa('[data-gwo-state-box]').forEach(el => el.dataset.level = state.code || 'unknown');
    qsa('[data-gwo-health-overall]').forEach(el => {
      const label = {healthy:'SALUD CORRECTA',degraded:'FRESCURA PARCIAL',stale:'REVISAR FUENTES'}[health?.overall] || 'SIN DATOS';
      text(el, label); el.dataset.health = health?.overall || 'unknown';
    });
    const layers = state.layers || {};
    qsa('[data-gwo-layer]').forEach(el => {
      const item = layers[el.dataset.gwoLayer] || {};
      el.dataset.severity = String(item.severity ?? 0);
      text(qs('[data-gwo-layer-value]', el), item.value);
    });
    const m = data.metrics || {};
    Object.entries(m).forEach(([k,v]) => {
      if (typeof v === 'number') populateMetric(k, v);
      else qsa(`[data-gwo-metric="${k}"]`).forEach(el => text(el, v));
    });
    qsa('[data-gwo-diario-generator]').forEach(el => text(el, m.diary_generator || '—'));
  }

  function renderTimeline(items) {
    qsa('[data-gwo-timeline]').forEach(root => {
      root.replaceChildren();
      if (!Array.isArray(items) || !items.length) {
        const e = document.createElement('div'); e.className='gwo-empty'; e.textContent='Aún no hay cambios registrados en la cronología.'; root.append(e); return;
      }
      items.slice(0, Number(root.dataset.limit || 12)).forEach(item => {
        const a = document.createElement('article'); a.className='gwo-event'; a.dataset.level=item.level || 'info';
        const tm=document.createElement('time'); tm.dateTime=item.at || ''; tm.textContent=dateTime(item.at);
        const h=document.createElement('h3'); h.textContent=item.title_es || 'Actualización';
        const p=document.createElement('p'); p.textContent=item.detail_es || '';
        a.append(tm,h,p);
        if(item.href){ const link=document.createElement('a'); link.href=url(item.href); link.textContent='Abrir contexto →'; a.append(link); }
        root.append(a);
      });
    });
  }

  function renderHealth(health) {
    qsa('[data-gwo-health-list]').forEach(root => {
      root.replaceChildren();
      const components = health?.components || [];
      if(!components.length){root.innerHTML='<div class="gwo-empty">No hay diagnóstico de fuentes disponible.</div>';return;}
      components.forEach(c => {
        const card=document.createElement('article'); card.className='gwo-health-card'; card.dataset.state=c.state || 'missing';
        const top=document.createElement('div'); top.className='gwo-health-top';
        const h=document.createElement('h3'); h.textContent=c.name || 'Fuente';
        const badge=document.createElement('span'); badge.className='gwo-health-badge'; badge.textContent=c.label_es || c.state || '—'; top.append(h,badge);
        const p=document.createElement('p'); p.textContent=c.note_es || '';
        const meta=document.createElement('div'); meta.className='gwo-health-meta';
        const source=document.createElement('span');
        if(c.url){const a=document.createElement('a');a.href=c.url.startsWith('http')?c.url:url(c.url);a.textContent=`Fuente: ${c.source || 'abrir'}`;if(c.url.startsWith('http')){a.target='_blank';a.rel='noopener noreferrer';}source.append(a);}else{source.textContent=`Fuente: ${c.source || '—'}`;}
        const seen=document.createElement('span'); seen.textContent=c.checked_at ? `Consulta: ${ago(c.checked_at)}` : 'Consulta: sin dato';
        meta.append(source,seen); card.append(top,p,meta); root.append(card);
      });
    });
  }

  function renderCorrections(items) {
    qsa('[data-gwo-corrections]').forEach(root => {
      root.replaceChildren();
      if(!Array.isArray(items) || !items.length){const e=document.createElement('div');e.className='gwo-empty';e.textContent='No hay correcciones materiales registradas en el archivo público.';root.append(e);return;}
      items.slice().reverse().forEach(item=>{
        const article=document.createElement('article');article.className='gwo-correction';
        const top=document.createElement('div');top.className='gwo-correction-top';
        const time=document.createElement('time');time.dateTime=item.date||'';time.textContent=item.date ? new Date(item.date+'T12:00:00').toLocaleDateString('es-ES',{day:'numeric',month:'long',year:'numeric'}) : 'Sin fecha';
        const badge=document.createElement('span');badge.className='gwo-chip';badge.textContent=item.type||'CORRECCIÓN';top.append(time,badge);
        const h=document.createElement('h3');h.textContent=item.title||item.page||'Corrección editorial';
        const p=document.createElement('p');p.textContent=item.detail||item.reason||'';
        article.append(top,h,p);
        if(item.url){const a=document.createElement('a');a.href=item.url.startsWith('http')?item.url:url(item.url);a.textContent='Abrir página corregida →';article.append(a);}
        root.append(article);
      });
    });
  }

  function renderAnomalies(items) {
    qsa('[data-gwo-anomalies]').forEach(root => {
      root.replaceChildren();
      if(!Array.isArray(items) || !items.length){
        const e=document.createElement('div');e.className='gwo-empty';e.textContent='No se detectan desviaciones estadísticas suficientes respecto al histórico disponible.';root.append(e);return;
      }
      items.forEach(x=>{const d=document.createElement('div');d.className='gwo-anomaly';const b=document.createElement('b');b.textContent=x.title_es;const p=document.createElement('p');p.textContent=x.detail_es;d.append(b,p);root.append(d);});
    });
  }

  function chart(root, history, key, formatter=nfmt) {
    const rows=(history || []).slice().reverse().filter(x => Number.isFinite(Number(x?.metrics?.[key])));
    root.replaceChildren();
    if(rows.length < 2){const e=document.createElement('div');e.className='gwo-empty';e.textContent='El histórico se irá formando automáticamente. Se necesitan al menos dos días.';root.append(e);return;}
    const values=rows.map(x=>Number(x.metrics[key])); const min=Math.min(...values,0); const max=Math.max(...values,1); const range=max-min || 1;
    const W=360,H=150,PX=28,PY=18; const x=i=>PX+(i*(W-PX*2)/(values.length-1)); const y=v=>H-PY-((v-min)/range)*(H-PY*2);
    const pts=values.map((v,i)=>`${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' ');
    const ns='http://www.w3.org/2000/svg'; const svg=document.createElementNS(ns,'svg'); svg.setAttribute('viewBox',`0 0 ${W} ${H}`);svg.setAttribute('role','img');
    [0,.5,1].forEach(t=>{const line=document.createElementNS(ns,'line');const yy=PY+t*(H-PY*2);line.setAttribute('x1',PX);line.setAttribute('x2',W-PX);line.setAttribute('y1',yy);line.setAttribute('y2',yy);line.setAttribute('class','gwo-chart-gridline');svg.append(line);});
    const area=document.createElementNS(ns,'polygon');area.setAttribute('points',`${PX},${H-PY} ${pts} ${W-PX},${H-PY}`);area.setAttribute('class','gwo-chart-area');svg.append(area);
    const poly=document.createElementNS(ns,'polyline');poly.setAttribute('points',pts);poly.setAttribute('class','gwo-chart-line');svg.append(poly);
    values.forEach((v,i)=>{if(i!==values.length-1 && values.length>12 && i%Math.ceil(values.length/8)!==0)return;const c=document.createElementNS(ns,'circle');c.setAttribute('cx',x(i));c.setAttribute('cy',y(v));c.setAttribute('r',i===values.length-1?'3.4':'2');c.setAttribute('class','gwo-chart-dot');const title=document.createElementNS(ns,'title');title.textContent=`${rows[i].date}: ${formatter(v)}`;c.append(title);svg.append(c);});
    const last=document.createElementNS(ns,'text');last.setAttribute('x',W-PX);last.setAttribute('y',13);last.setAttribute('text-anchor','end');last.setAttribute('class','gwo-chart-label');last.textContent=`Último: ${formatter(values.at(-1))}`;svg.append(last);
    root.append(svg);
  }

  function renderCharts(history) {
    qsa('[data-gwo-chart]').forEach(root => {
      const kind=root.dataset.gwoChart;
      const key={news:'news_24h',seismic:'seismic_7d',ope:'ope_passengers_day'}[kind];
      if(key) chart(root,history,key);
    });
  }

  function renderMap(seismic) {
    const el=qs('#gwoStrategicMap'); if(!el || !window.L) return;
    const map=L.map(el,{scrollWheelZoom:false}).setView([35.95,-5.55],9);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,attribution:'© OpenStreetMap'}).addTo(map);
    const nodes=[
      ['Algeciras',36.1408,-5.4562,'Puerto'],['Tarifa',36.0143,-5.6044,'Paso y ferris'],['Gibraltar',36.1408,-5.3536,'Puerto'],['Ceuta',35.8894,-5.3213,'Puerto y frontera'],['Tánger Med',35.8906,-5.5002,'Puerto'],['Tánger',35.7595,-5.8340,'Puerto y ciudad']
    ];
    const strategic=L.layerGroup(); nodes.forEach(([name,lat,lng,kind])=>L.circleMarker([lat,lng],{radius:7,weight:2,fillOpacity:.75}).bindPopup(`<b>${name}</b><br>${kind}`).addTo(strategic)); strategic.addTo(map);
    const quakes=L.layerGroup();
    const candidates=[];
    if(Array.isArray(seismic?.events)) candidates.push(...seismic.events);
    if(Array.isArray(seismic?.earthquakes)) candidates.push(...seismic.earthquakes);
    candidates.slice(0,120).forEach(q=>{
      const lat=Number(q.latitude ?? q.lat), lng=Number(q.longitude ?? q.lon ?? q.lng); if(!Number.isFinite(lat)||!Number.isFinite(lng))return;
      const mag=Number(q.magnitude ?? q.mag);L.circleMarker([lat,lng],{radius:Math.max(4,Number.isFinite(mag)?mag*2.2:4),weight:1,fillOpacity:.35}).bindPopup(`<b>Sismo M ${Number.isFinite(mag)?mag:'—'}</b><br>${escapeHTML(q.place||'Catálogo regional')}`).addTo(quakes);
    });
    if(candidates.length) quakes.addTo(map);
    const corridor=L.polyline([[36.05,-6.05],[35.92,-5.40],[35.95,-4.95]],{weight:3,dashArray:'7 7',opacity:.55}).bindTooltip('Corredor conceptual del Estrecho · no representa rutas AIS en tiempo real'); corridor.addTo(map);
    const overlays={'Nodos estratégicos':strategic,'Sismicidad reciente':quakes};L.control.layers(null,overlays,{collapsed:false}).addTo(map);
    setTimeout(()=>map.invalidateSize(),120);
  }

  async function main(){
    try{
      const [obs,health,timeline,history,seismic]=await Promise.all([
        fetchJSON('observatory.json'),fetchJSON('health.json').catch(()=>({})),fetchJSON('timeline.json').catch(()=>[]),fetchJSON('observatory-history.json').catch(()=>[]),fetchJSON('seismicity.json').catch(()=>({}))
      ]);
      renderState(obs,health);renderTimeline(timeline);renderHealth(health);renderAnomalies(obs.anomalies||[]);renderCharts(history);renderMap(seismic);setupBrowserAlerts(obs);
      if(qs('[data-gwo-corrections]')) fetchJSON('corrections.json').then(renderCorrections).catch(()=>renderCorrections([]));
      document.documentElement.dataset.gwoReady='true';
    }catch(err){
      console.warn('Gibraltar Watch Observatory:',err);
      qsa('[data-gwo-fallback]').forEach(el=>{el.hidden=false;});
    }
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',main,{once:true}); else main();
})();
