(()=>{"use strict";
const locale=document.documentElement.lang==='en'?'en-GB':'es-ES';
const nf=new Intl.NumberFormat(locale);
const dateFmt=new Intl.DateTimeFormat(locale,{day:'numeric',month:'long',year:'numeric',timeZone:'UTC'});
function val(o,p){return p.split('.').reduce((a,k)=>a&&a[k],o)}
function set(key,value){document.querySelectorAll(`[data-ope="${key}"]`).forEach(el=>{el.textContent=value??'—'})}
function fmt(n){return Number.isFinite(Number(n))?nf.format(Number(n)):'—'}
function routeName(s){return locale==='en-GB'?String(s).replace('Tánger','Tangier').replace('Algeciras','Algeciras').replace('Ceuta','Ceuta'):s}
function renderRoutes(kind,routes){document.querySelectorAll(`[data-ope-routes="${kind}"]`).forEach(box=>{box.innerHTML='';(routes||[]).slice(0,6).forEach((r,i)=>{const row=document.createElement('article');row.className='gw-route-row';row.innerHTML=`<span>${String(i+1).padStart(2,'0')}</span><div><b>${routeName(r.name)}</b><small>${fmt(r.rotations)} ${locale==='en-GB'?'rotations':'rotaciones'}</small></div><strong>${fmt(r.passengers)}</strong><em>${fmt(r.vehicles)} ${locale==='en-GB'?'vehicles':'vehículos'}</em>`;box.appendChild(row)})})}
fetch('ope-2026.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(r.status);return r.json()}).then(d=>{
 let dt=d.report_date?new Date(d.report_date+'T12:00:00Z'):null;
 set('report_date',dt?new Intl.DateTimeFormat(locale,{day:'2-digit',month:'short',timeZone:'UTC'}).format(dt):'—');
 set('report_date_long',dt?dateFmt.format(dt):'—');
 ['departure.passengers.day'].forEach(()=>{});
 const map={
 'departure_passengers_day':'departure.day.passengers','departure_vehicles_day':'departure.day.vehicles','departure_rotations_day':'departure.day.rotations','departure_passengers_total':'departure.cumulative.passengers',
 'return_passengers_day':'return.day.passengers','return_vehicles_day':'return.day.vehicles','return_rotations_day':'return.day.rotations','return_passengers_total':'return.cumulative.passengers',
 'data_note_es':'data_note_es','data_note_en':'data_note_en','advice_es':'advice_es','advice_en':'advice_en'};
 Object.entries(map).forEach(([k,p])=>set(k,fmt(val(d,p))==='—'&&typeof val(d,p)==='string'?val(d,p):(typeof val(d,p)==='number'?fmt(val(d,p)):val(d,p))));
 const all=[...(d.departure?.routes||[]),...(d.return?.routes||[])];
 const top=all.sort((a,b)=>(b.passengers||0)-(a.passengers||0))[0]; set('top_route',top?routeName(top.name):'—'); set('top_route_passengers',top?fmt(top.passengers):'—');
 const dep=(d.departure?.routes||[]).find(r=>r.name.includes('Algeciras/Tánger'));
 const ret=(d.return?.routes||[]).find(r=>r.name.includes('Tánger-Med/Algeciras'));
 set('algeciras_tanger_total',fmt((dep?.passengers||0)+(ret?.passengers||0)));
 document.querySelectorAll('[data-ope-link]').forEach(a=>{a.href=d.source_url||'#'});
 renderRoutes('departure',d.departure?.routes);renderRoutes('return',d.return?.routes);
}).catch(()=>{document.querySelectorAll('[data-ope]').forEach(el=>{if(el.textContent.trim()==='—')el.textContent=locale==='en-GB'?'Data unavailable':'Datos no disponibles'})});
})();
