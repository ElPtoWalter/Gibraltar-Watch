(() => {
  'use strict';

  const cfg = window.GW_BUSINESS_CONFIG || {};
  const lang = document.documentElement.lang?.toLowerCase().startsWith('en') ? 'en' : 'es';
  const t = (es, en) => lang === 'es' ? es : en;

  function qs(selector, root = document) { return root.querySelector(selector); }
  function qsa(selector, root = document) { return [...root.querySelectorAll(selector)]; }

  function initReadingProgress() {
    if (document.body.dataset.page === 'home' || document.body.classList.contains('gw-commercial-page')) return;
    const main = qs('main');
    if (!main || !qs('h1', main)) return;
    const bar = document.createElement('div');
    bar.className = 'gw-reading-progress';
    bar.setAttribute('aria-hidden', 'true');
    bar.innerHTML = '<i></i>';
    document.body.prepend(bar);
    const fill = bar.firstElementChild;
    const update = () => {
      const max = Math.max(1, document.documentElement.scrollHeight - innerHeight);
      fill.style.width = `${Math.min(100, Math.max(0, scrollY / max * 100))}%`;
    };
    addEventListener('scroll', update, { passive: true });
    addEventListener('resize', update);
    update();
  }

  function getArticleTitle() {
    return qs('main h1')?.textContent.trim() || document.title;
  }

  function copyURL(button) {
    const url = location.href;
    const done = () => {
      const previous = button.textContent;
      button.textContent = t('Copiado', 'Copied');
      setTimeout(() => button.textContent = previous, 1400);
    };
    if (navigator.clipboard?.writeText) navigator.clipboard.writeText(url).then(done).catch(() => {});
    else {
      const input = document.createElement('textarea');
      input.value = url;
      document.body.append(input);
      input.select();
      document.execCommand('copy');
      input.remove();
      done();
    }
  }

  function buildShareTools() {
    const main = qs('main');
    const h1 = qs('h1', main || document);
    if (!main || !h1 || qs('.gw-article-tools', main)) return;
    if (document.body.dataset.page === 'home' || document.body.classList.contains('gw-commercial-page')) return;

    const words = (main.innerText || '').trim().split(/\s+/).filter(Boolean).length;
    const minutes = Math.max(2, Math.round(words / 220));
    const reviewed = qs('meta[name="gw:last-reviewed"]')?.content || document.lastModified;
    let dateText = reviewed;
    const date = new Date(reviewed);
    if (!Number.isNaN(date.getTime())) {
      dateText = new Intl.DateTimeFormat(lang === 'es' ? 'es-ES' : 'en-GB', { dateStyle: 'medium' }).format(date);
    }

    const tools = document.createElement('div');
    tools.className = 'gw-article-tools';
    tools.innerHTML = `
      <div class="gw-article-meta">
        <span>${minutes} ${t('min de lectura', 'min read')}</span>
        <span>${t('Revisado', 'Reviewed')}: ${dateText}</span>
      </div>
      <div class="gw-share-actions" aria-label="${t('Compartir', 'Share')}">
        <button type="button" data-gw-share-native>${t('Compartir', 'Share')}</button>
        <button type="button" data-gw-copy>${t('Copiar enlace', 'Copy link')}</button>
        <a data-gw-whatsapp target="_blank" rel="noopener">WhatsApp</a>
      </div>`;

    const hero = h1.closest('section, article, header') || h1.parentElement;
    hero.insertAdjacentElement('afterend', tools);

    qs('[data-gw-copy]', tools)?.addEventListener('click', event => copyURL(event.currentTarget));
    const title = getArticleTitle();
    const whatsapp = qs('[data-gw-whatsapp]', tools);
    if (whatsapp) whatsapp.href = `https://wa.me/?text=${encodeURIComponent(`${title} ${location.href}`)}`;
    const nativeButton = qs('[data-gw-share-native]', tools);
    if (!navigator.share) nativeButton?.remove();
    else nativeButton?.addEventListener('click', () => navigator.share({ title, url: location.href }).catch(() => {}));
  }

  function loadAdSense(client) {
    if (qs('script[data-gw-adsense]')) return;
    const script = document.createElement('script');
    script.async = true;
    script.crossOrigin = 'anonymous';
    script.dataset.gwAdsense = 'true';
    script.src = `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${encodeURIComponent(client)}`;
    document.head.append(script);
  }

  function initAds() {
    const adCfg = cfg.adsense || {};
    const slots = adCfg.slots || {};
    qsa('[data-gw-ad]').forEach(container => {
      const key = container.dataset.gwAd;
      const slot = slots[key];
      if (!adCfg.enabled || !adCfg.client || !slot) {
        container.hidden = true;
        return;
      }
      container.hidden = false;
      container.innerHTML = `
        <span class="gw-ad-label">${t('Publicidad', 'Advertisement')}</span>
        <ins class="adsbygoogle" style="display:block" data-ad-client="${adCfg.client}" data-ad-slot="${slot}" data-ad-format="auto" data-full-width-responsive="true"></ins>`;
      loadAdSense(adCfg.client);
      try { (window.adsbygoogle = window.adsbygoogle || []).push({}); } catch {}
    });
  }

  function initNewsletter() {
    qsa('[data-gw-newsletter]').forEach(block => {
      const form = qs('form', block);
      const fallback = qs('[data-gw-newsletter-fallback]', block);
      if (!form) return;
      const ncfg = cfg.newsletter || {};
      if (!ncfg.enabled || !ncfg.endpoint) {
        form.hidden = true;
        if (fallback) fallback.hidden = false;
        return;
      }
      form.hidden = false;
      if (fallback) fallback.hidden = true;
      form.action = ncfg.endpoint;
      form.method = ncfg.method || 'POST';
    });
  }

  function improveNavAccessibility() {
    qsa('.gwc-nav-group > summary').forEach(summary => {
      summary.setAttribute('role', 'button');
      summary.setAttribute('aria-haspopup', 'true');
      const group = summary.parentElement;
      const sync = () => summary.setAttribute('aria-expanded', group.open ? 'true' : 'false');
      group.addEventListener('toggle', sync);
      sync();
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    initReadingProgress();
    buildShareTools();
    initAds();
    initNewsletter();
    improveNavAccessibility();
  });
})();
