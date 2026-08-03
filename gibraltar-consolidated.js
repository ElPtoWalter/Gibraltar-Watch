(() => {
  'use strict';

  const lang = document.documentElement.lang?.toLowerCase().startsWith('en') ? 'en' : 'es';
  const locale = lang === 'es' ? 'es-ES' : 'en-GB';
  const tz = lang === 'es' ? 'Europe/Madrid' : 'UTC';
  let BASE = './';
  try { BASE = new URL('.', document.currentScript?.src || window.location.href).href; } catch { BASE = './'; }

  const t = (es, en) => lang === 'es' ? es : en;
  const byId = id => document.getElementById(id);
  const safeText = value => String(value ?? '');

  async function getJSON(file) {
    const response = await fetch(`${BASE}${file}?v=${Date.now()}`, { cache: 'no-store' });
    if (!response.ok) throw new Error(`${file}: ${response.status}`);
    return response.json();
  }

  function formatDate(value) {
    if (!value) return '—';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '—';
    return new Intl.DateTimeFormat(locale, {
      dateStyle: 'medium',
      timeStyle: 'short',
      timeZone: tz,
    }).format(date) + (lang === 'en' ? ' UTC' : '');
  }

  function formatNumber(value) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return '—';
    return new Intl.NumberFormat(locale, { maximumFractionDigits: 0 }).format(Number(value));
  }

  function safeURL(value) {
    try {
      const url = new URL(value, window.location.href);
      return ['https:', 'http:'].includes(url.protocol) ? url.href : '#';
    } catch {
      return '#';
    }
  }

  function closeOtherNavGroups(active) {
    document.querySelectorAll('.gwc-nav-group[open]').forEach(group => {
      if (group !== active) group.removeAttribute('open');
    });
  }

  function initNavigation() {
    const toggle = document.querySelector('.nav-toggle');
    const nav = document.querySelector('.site-nav');
    if (toggle && nav && toggle.dataset.gwcBound !== 'true') {
      toggle.dataset.gwcBound = 'true';
      toggle.addEventListener('click', () => {
        const open = nav.classList.toggle('is-open');
        toggle.setAttribute('aria-expanded', String(open));
      });
    }
    document.querySelectorAll('.gwc-nav-group').forEach(group => {
      group.addEventListener('toggle', () => {
        if (group.open) closeOtherNavGroups(group);
      });
    });
    document.addEventListener('click', event => {
      if (!event.target.closest('.gwc-nav-group')) closeOtherNavGroups(null);
    });
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape') closeOtherNavGroups(null);
    });
  }

  function setStatus(articleKey, valueId, noteId, value, note) {
    const valueEl = byId(valueId);
    const noteEl = byId(noteId);
    if (valueEl) valueEl.textContent = value || '—';
    if (noteEl) noteEl.textContent = note || '';
    const article = document.querySelector(`[data-gwc-status="${articleKey}"]`);
    if (!article) return;
    const normalized = safeText(value).toLowerCase();
    let level = 'neutral';
    if (/operativo|operational|normal|abierto|open/.test(normalized)) level = 'operational';
    else if (/alta|high|crítica|critical/.test(normalized)) level = 'high';
    else if (/elevada|elevated|media|medium/.test(normalized)) level = 'elevated';
    else if (/vigilancia|monitoring|reforzada|reinforced/.test(normalized)) level = 'monitoring';
    article.dataset.level = level;
  }

  function categoryLabel(category) {
    const labels = {
      ceuta: t('Ceuta y frontera', 'Ceuta and border'),
      melilla: t('Melilla y frontera', 'Melilla and border'),
      relations: t('España–Marruecos', 'Spain–Morocco'),
      traffic: t('Tráfico marítimo', 'Maritime traffic'),
      economy: t('Economía y puertos', 'Economy and ports'),
      security: t('Seguridad', 'Security'),
    };
    return labels[category] || t('Actualidad', 'Current affairs');
  }

  function renderNews(items) {
    const container = byId('gwcNewsList');
    if (!container) return;
    container.replaceChildren();
    const sorted = [...(Array.isArray(items) ? items : [])]
      .sort((a, b) => new Date(b.published_at || 0) - new Date(a.published_at || 0))
      .slice(0, 5);
    if (!sorted.length) {
      container.innerHTML = `<p class="gwc-empty">${t('No hay novedades verificadas en el último ciclo.', 'No verified developments were found in the latest cycle.')}</p>`;
      return;
    }
    sorted.forEach(item => {
      const article = document.createElement('article');
      article.className = 'gwc-news-item';
      const time = document.createElement('time');
      time.dateTime = item.published_at || '';
      time.textContent = formatDate(item.published_at);
      const body = document.createElement('div');
      const title = document.createElement('h3');
      const link = document.createElement('a');
      link.href = safeURL(item.url);
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.textContent = item.title || t('Novedad sin título', 'Untitled update');
      title.append(link);
      const source = document.createElement('small');
      source.textContent = item.source || t('Fuente no indicada', 'Source not stated');
      body.append(title, source);
      const category = document.createElement('b');
      category.textContent = categoryLabel(item.category);
      article.append(time, body, category);
      container.append(article);
    });
  }

  async function loadGeopolitics() {
    try {
      const data = await getJSON('geopolitics.json');
      const status = data.status || {};
      const pick = entry => entry?.[lang] || entry?.es || entry?.en || '—';
      setStatus('maritime', 'gwcStatusMaritime', 'gwcNoteMaritime', pick(status.maritime_status), pick(status.maritime_note));
      setStatus('border', 'gwcStatusBorder', 'gwcNoteBorder', pick(status.border_pressure), pick(status.border_note));
      setStatus('bilateral', 'gwcStatusBilateral', 'gwcNoteBilateral', pick(status.bilateral_tension), pick(status.bilateral_note));
      setStatus('security', 'gwcStatusSecurity', 'gwcNoteSecurity', pick(status.security_status), pick(status.security_note));
      const confidence = pick(status.confidence);
      const meta = byId('gwcStatusMeta');
      if (meta) meta.textContent = `${t('Actualizado', 'Updated')}: ${formatDate(data.generated_at)} · ${t('Confianza', 'Confidence')}: ${confidence}`;
      renderNews(data.items);
    } catch (error) {
      console.warn('Gibraltar Watch geopolitics:', error);
      const meta = byId('gwcStatusMeta');
      if (meta) meta.textContent = t('No se pudo renovar el panel; consulta la página de situación actual.', 'The panel could not be refreshed; check the current situation page.');
      renderNews([]);
    }
  }

  async function loadOPE() {
    try {
      const data = await getJSON('ope-2026.json');
      const passengers = data.departure?.day?.passengers;
      const value = byId('gwcOpePassengers');
      const meta = byId('gwcOpeMeta');
      if (value) value.textContent = formatNumber(passengers);
      if (meta) {
        const label = lang === 'es' ? data.report_label_es : data.report_label_en;
        meta.textContent = `${t('Pasajeros del día', 'Passengers that day')} · ${label || '—'}`;
      }
    } catch (error) {
      console.warn('Gibraltar Watch OPE:', error);
    }
  }

  async function loadSeismicity() {
    try {
      const data = await getJSON('seismicity.json');
      const el = byId('gwcQuakes30');
      if (el) el.textContent = formatNumber(data.periods?.['30d']);
    } catch (error) {
      console.warn('Gibraltar Watch seismicity:', error);
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    if (document.querySelector('.gwc-home')) {
      Promise.allSettled([loadGeopolitics(), loadOPE(), loadSeismicity()]);
    }
  });
})();
