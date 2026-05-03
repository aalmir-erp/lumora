/* Lumora shared frontend utils.
 *
 * - i18n loader + helpers (window.t, window.setLang)
 * - PWA service-worker registration
 * - install-app button
 * - global fetch wrapper with JSON
 */
(function () {
  // ---------- i18n ----------
  const LS_LANG = "lumora.lang";
  let i18n = null;
  let currentLang = localStorage.getItem(LS_LANG) || "en";

  async function loadI18n() {
    if (i18n) return i18n;
    try {
      const r = await fetch("/api/i18n");
      i18n = await r.json();
    } catch (e) {
      console.warn("i18n fetch failed:", e);
      i18n = { en: {} };
    }
    return i18n;
  }

  function applyLang(lang) {
    if (!i18n[lang]) lang = "en";
    currentLang = lang;
    localStorage.setItem(LS_LANG, lang);
    document.documentElement.lang = lang;
    document.documentElement.dir = i18n[lang].dir || "ltr";
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      const val = i18n[lang][key];
      if (val) el.textContent = val;
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      const key = el.getAttribute("data-i18n-placeholder");
      const val = i18n[lang][key];
      if (val) el.placeholder = val;
    });
    window.dispatchEvent(new CustomEvent("lumora:lang", { detail: { lang } }));
  }

  window.lumoraT = function (key, fallback) {
    return (i18n && i18n[currentLang] && i18n[currentLang][key]) || fallback || key;
  };
  window.lumoraLang = function () { return currentLang; };
  window.lumoraSetLang = function (lang) { applyLang(lang); };

  // ---------- API helper ----------
  window.api = async function (path, opts = {}) {
    const o = { headers: { "content-type": "application/json", ...(opts.headers || {}) }, ...opts };
    if (o.body && typeof o.body !== "string") o.body = JSON.stringify(o.body);
    const r = await fetch(path, o);
    const text = await r.text();
    let json; try { json = text ? JSON.parse(text) : {}; } catch { json = { raw: text }; }
    if (!r.ok) throw Object.assign(new Error(json.detail || r.statusText), { status: r.status, json });
    return json;
  };

  // ---------- service worker ----------
  // One-time purge: existing visitors are stuck on the old cache-first SW
  // (lumora-v0.2.0). Force a clean re-register so they pick up new deploys.
  const SW_RESET_KEY = "lumora.sw.reset.v0.8.0";
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", async () => {
      try {
        if (!localStorage.getItem(SW_RESET_KEY)) {
          const regs = await navigator.serviceWorker.getRegistrations();
          await Promise.all(regs.map(r => r.unregister()));
          if (window.caches) {
            const keys = await caches.keys();
            await Promise.all(keys.map(k => caches.delete(k)));
          }
          localStorage.setItem(SW_RESET_KEY, "1");
        }
        await navigator.serviceWorker.register("/sw.js", { updateViaCache: "none" });
      } catch (e) { console.warn(e); }
    });
  }

  // ---------- install prompt (PWA) ----------
  let deferredPrompt = null;
  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredPrompt = e;
    document.querySelectorAll("[data-install]").forEach((b) => (b.style.display = ""));
  });
  document.addEventListener("click", (e) => {
    const t = e.target.closest("[data-install]");
    if (!t || !deferredPrompt) return;
    deferredPrompt.prompt();
    deferredPrompt = null;
  });

  // ---------- language picker ----------
  document.addEventListener("change", (e) => {
    const t = e.target.closest(".lang-pick");
    if (t) applyLang(t.value);
  });

  // ---------- bootstrap ----------
  loadI18n().then(() => {
    applyLang(currentLang);
    // populate any <select.lang-pick>
    document.querySelectorAll(".lang-pick").forEach((sel) => {
      sel.innerHTML = Object.entries(i18n).map(
        ([k, v]) => `<option value="${k}" ${k === currentLang ? "selected" : ""}>${v.label || k}</option>`
      ).join("");
    });
  });

  // ---------- live brand binding ----------
  // Fetch /api/brand once, then sync any element with class .lumora-phone / .lumora-whatsapp / .lumora-email
  // and rewrite any wa.me / tel: anchor href to use the live number.
  fetch("/api/brand").then(r => r.json()).then((b) => {
    window.LUMORA_BRAND = b;
    document.querySelectorAll(".lumora-phone").forEach(el => el.textContent = b.phone || el.textContent);
    document.querySelectorAll(".lumora-whatsapp").forEach(el => el.textContent = b.phone || el.textContent);
    document.querySelectorAll(".lumora-email").forEach(el => el.textContent = b.email || el.textContent);
    // Rewrite all wa.me + tel: links to use the live number
    const wa = (b.whatsapp || "").replace(/[^0-9]/g, "");
    const tel = (b.phone || "").replace(/[^+0-9]/g, "");
    document.querySelectorAll("a[href*='wa.me/'], a[data-wa]").forEach(a => {
      try {
        const u = new URL(a.href, location.href);
        const text = u.searchParams.get("text") || a.dataset.waText || "";
        a.href = `https://wa.me/${wa}` + (text ? `?text=${encodeURIComponent(text)}` : "");
      } catch {}
    });
    document.querySelectorAll("a[href^='tel:']").forEach(a => { a.href = "tel:" + tel; });
    window.dispatchEvent(new CustomEvent("lumora:brand", { detail: b }));
  }).catch(() => {});

  // Version stamp from /api/health
  function _setVersion() {
    fetch("/api/health").then(r => r.json()).then(j => {
      window.LUMORA_VERSION = j.version;
      document.querySelectorAll("#lumora-version").forEach(el => el.textContent = "v" + j.version);
    }).catch(e => console.warn("[lumora] /api/health failed", e));
  }
  function _refreshFlagActive() {
    const cur = (window.lumoraLang ? lumoraLang() : (localStorage.getItem("lumora.lang") || "en"));
    document.querySelectorAll(".lang-flags [data-lang]").forEach(b =>
      b.classList.toggle("active", b.dataset.lang === cur));
  }
  if (document.readyState !== "loading") {
    _setVersion(); _refreshFlagActive();
  } else {
    document.addEventListener("DOMContentLoaded", () => { _setVersion(); _refreshFlagActive(); });
  }
  window.addEventListener("lumora:lang", _refreshFlagActive);

})();
