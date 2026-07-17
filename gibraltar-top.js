(() => {
  "use strict";
  const lang = document.documentElement.lang === "en" ? "en" : "es";
  const labels = {
    es: {
      error: "No se pudo cargar la actualización.",
      unavailable: "No disponible",
      updated: "Actualizado",
      dataFresh: "Datos recientes",
      dataStale: "Datos desactualizados"
    },
    en: {
      error: "The update could not be loaded.",
      unavailable: "Unavailable",
      updated: "Updated",
      dataFresh: "Fresh data",
      dataStale: "Stale data"
    }
  }[lang];

  const getJSON = async (path) => {
    const response = await fetch(`${path}?v=${Date.now()}`, {cache: "no-store"});
    if (!response.ok) throw new Error(`${path}: ${response.status}`);
    return response.json();
  };

  const text = (id, value) => {
    const node = document.getElementById(id);
    if (node) node.textContent = value ?? "—";
  };

  const formatDate = (value) => {
    if (!value) return labels.unavailable;
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return labels.unavailable;
    return new Intl.DateTimeFormat(lang === "es" ? "es-ES" : "en-GB", {
      dateStyle: "long",
      timeStyle: "short",
      timeZone: lang === "es" ? "Europe/Madrid" : "UTC"
    }).format(date) + (lang === "en" ? " UTC" : "");
  };

  const renderList = (id, values) => {
    const root = document.getElementById(id);
    if (!root) return;
    root.replaceChildren();
    (values || []).forEach(value => {
      const li = document.createElement("li");
      li.textContent = value;
      root.append(li);
    });
  };

  const renderArchive = (values) => {
    const root = document.getElementById("gtBriefArchive");
    if (!root) return;
    root.replaceChildren();
    (values || []).slice(0, 6).forEach(item => {
      const article = document.createElement("article");
      const time = document.createElement("time");
      time.textContent = item.date || "—";
      const heading = document.createElement("h3");
      heading.textContent = lang === "es" ? item.headline_es : item.headline_en;
      const summary = document.createElement("p");
      summary.textContent = lang === "es" ? item.summary_es : item.summary_en;
      article.append(time, heading, summary);
      root.append(article);
    });
  };

  const renderBrief = (brief, archive) => {
    text("gtBriefDate", brief.date);
    text("gtBriefHeadline", lang === "es" ? brief.headline_es : brief.headline_en);
    text("gtBriefSummary", lang === "es" ? brief.summary_es : brief.summary_en);
    text("gtBriefGenerated", formatDate(brief.generated_at));
    text("gtBriefSourceChecked", formatDate(brief.source_checked_at));
    text("gtBriefChange", lang === "es" ? brief.change_es : brief.change_en);
    text("gtBrief24h", brief.seismic?.periods?.["24h"] ?? "—");
    text("gtBrief7d", brief.seismic?.periods?.["7d"] ?? "—");
    text("gtBrief30d", brief.seismic?.periods?.["30d"] ?? "—");
    text("gtBriefMax", brief.seismic?.max_magnitude_30d == null ? "—" : `M ${brief.seismic.max_magnitude_30d}`);
    text("gtBriefLastEvent", lang === "es" ? brief.seismic?.last_event_es : brief.seismic?.last_event_en);
    renderList("gtBriefInterpretation", lang === "es" ? brief.interpretation_es : brief.interpretation_en);
    renderList("gtBriefWatch", lang === "es" ? brief.watchlist_es : brief.watchlist_en);
    renderArchive(Array.isArray(archive) ? archive : archive.items);

    const pill = document.getElementById("gtBriefHealth");
    if (pill) {
      pill.textContent = lang === "es" ? brief.health_label_es : brief.health_label_en;
      pill.className = "gt-status-pill";
      if (brief.health === "STALE") pill.classList.add("is-warning");
      if (brief.health === "DEGRADED") pill.classList.add("is-error");
    }

    text("homeBriefSeismic", brief.seismic?.periods?.["30d"] ?? "—");
    text("homeBriefFreshness", brief.health === "OK" ? labels.dataFresh : labels.dataStale);
    text("homeBriefConclusion", lang === "es" ? brief.short_conclusion_es : brief.short_conclusion_en);
  };

  async function loadBrief() {
    if (!document.querySelector("[data-gibraltar-brief]")) return;
    try {
      const [brief, archive] = await Promise.all([
        getJSON("/gibraltar-brief.json"),
        getJSON("/gibraltar-brief-archive.json")
      ]);
      renderBrief(brief, archive);
      const loading = document.getElementById("gtBriefLoading");
      if (loading) loading.hidden = true;
    } catch (error) {
      console.error(error);
      const loading = document.getElementById("gtBriefLoading");
      if (loading) loading.textContent = labels.error;
    }
  }

  function setupNav() {
    const toggle = document.querySelector(".nav-toggle");
    const nav = document.querySelector(".site-nav");
    if (!toggle || !nav) return;
    toggle.addEventListener("click", () => {
      const open = nav.classList.toggle("open");
      nav.classList.toggle("is-open", open);
      toggle.setAttribute("aria-expanded", String(open));
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    setupNav();
    loadBrief();
  });
})();
