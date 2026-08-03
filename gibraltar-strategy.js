(() => {
  'use strict';
  const lang = document.documentElement.lang === 'en' ? 'en' : 'es';
  const fmtDate = (iso) => {
    if (!iso) return '—';
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return new Intl.DateTimeFormat(lang === 'es' ? 'es-ES' : 'en-GB', {
      dateStyle: 'medium', timeStyle: 'short'
    }).format(d);
  };
  const levelFor = (key, value) => {
    const v = String(value || '').toLowerCase();
    if (key === 'maritime') return /operativo|operational|abierto|open/.test(v) ? 'low' : /reduc|restrict/.test(v) ? 'medium' : 'high';
    if (/alta|high|elevad|reinforced|reforzada|critical|crítica/.test(v)) return 'high';
    if (/media|medium|moderad|vigilancia|watch/.test(v)) return 'medium';
    return 'low';
  };
  const localized = (obj) => obj && typeof obj === 'object' ? (obj[lang] || obj.es || obj.en || '—') : (obj || '—');
  const setText = (key, value) => document.querySelectorAll(`[data-strat="${key}"]`).forEach(el => { el.textContent = value; });
  const esc = (s) => String(s ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  const renderNews = (items) => {
    document.querySelectorAll('[data-news-feed]').forEach(container => {
      const list = (items || []).slice(0, 9);
      if (!list.length) {
        container.innerHTML = `<article class="gw-news-placeholder">${lang === 'es' ? 'No hay titulares recientes disponibles.' : 'No recent headlines are available.'}</article>`;
        return;
      }
      container.innerHTML = list.map(item => {
        const title = esc(item.title);
        const source = esc(item.source || 'Fuente');
        const cat = esc(item.category || 'actualidad');
        const date = fmtDate(item.published_at);
        const url = esc(item.url || '#');
        return `<a class="gw-news-card" href="${url}" target="_blank" rel="noopener noreferrer"><small>${cat}</small><h3>${title}</h3><footer><span>${source}</span><time>${date}</time></footer></a>`;
      }).join('');
    });
  };
  const apply = (data) => {
    const s = data.status || {};
    const pairs = [
      ['maritime_status', localized(s.maritime_status)], ['maritime_note', localized(s.maritime_note)],
      ['border_pressure', localized(s.border_pressure)], ['border_note', localized(s.border_note)],
      ['bilateral_tension', localized(s.bilateral_tension)], ['bilateral_note', localized(s.bilateral_note)],
      ['security_status', localized(s.security_status)], ['security_note', localized(s.security_note)],
      ['confidence', localized(s.confidence)], ['generated_at', fmtDate(data.generated_at)]
    ];
    pairs.forEach(([k,v]) => setText(k,v));
    const cards = {
      maritime: localized(s.maritime_status), border: localized(s.border_pressure),
      relations: localized(s.bilateral_tension), security: localized(s.security_status)
    };
    Object.entries(cards).forEach(([key,value]) => {
      document.querySelectorAll(`[data-status-card="${key}"]`).forEach(card => card.dataset.level = levelFor(key,value));
    });
    renderNews(data.items);
  };
  fetch(`geopolitics.json?v=${Date.now()}`, {cache:'no-store'})
    .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
    .then(apply)
    .catch(() => renderNews([]));
})();
