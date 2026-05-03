/* Servia shared frontend utils.
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
    document.body && (document.body.dataset.lang = lang);  // mascot dress hook

    // Full-page translation via Google Translate cookie.
    try {
      const host = location.hostname;
      const dom = host.includes(".") ? "." + host.split(".").slice(-2).join(".") : host;
      if (lang === "en") {
        document.cookie = "googtrans=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
        document.cookie = "googtrans=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; domain=" + dom;
      } else {
        const v = "/en/" + lang;
        document.cookie = "googtrans=" + v + "; path=/";
        document.cookie = "googtrans=" + v + "; path=/; domain=" + dom;
      }
      const prev = sessionStorage.getItem("servia.last.applied.lang");
      if (prev && prev !== lang) {
        sessionStorage.setItem("servia.last.applied.lang", lang);
        location.reload();
        return;
      }
      sessionStorage.setItem("servia.last.applied.lang", lang);
    } catch (e) { console.warn(e); }
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      const val = i18n[lang][key];
      if (val) el.textContent = val;
    });
    document.querySelectorAll("[data-i18n-html]").forEach((el) => {
      const key = el.getAttribute("data-i18n-html");
      const val = i18n[lang][key];
      if (val) el.innerHTML = val;
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      const key = el.getAttribute("data-i18n-placeholder");
      const val = i18n[lang][key];
      if (val) el.placeholder = val;
    });
    document.querySelectorAll("[data-i18n-aria]").forEach((el) => {
      const key = el.getAttribute("data-i18n-aria");
      const val = i18n[lang][key];
      if (val) el.setAttribute("aria-label", val);
    });
    // Highlight the active language button in the picker
    document.querySelectorAll(".lang-list button").forEach(b => {
      b.classList.toggle("active", b.dataset.lang === lang);
    });
    // Mascot dress: swap a small accessory pin per language so users feel
    // represented (UAE, Pakistan, India, Philippines flag accents).
    const dressMap = { ar:"🇦🇪", ur:"🇵🇰", hi:"🇮🇳", tl:"🇵🇭", en:"🇬🇧" };
    document.querySelectorAll(".mascot-frame, .mascot-wrap").forEach(f => {
      let pin = f.querySelector(".mascot-flag-pin");
      if (!pin) {
        pin = document.createElement("div");
        pin.className = "mascot-flag-pin";
        pin.style.cssText = "position:absolute;top:8%;inset-inline-end:8%;width:34px;height:34px;border-radius:50%;background:#fff;display:flex;align-items:center;justify-content:center;font-size:18px;box-shadow:0 4px 12px rgba(15,23,42,.18);z-index:5;border:2px solid #FCD34D";
        f.appendChild(pin);
      }
      pin.textContent = dressMap[lang] || "🇦🇪";
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
  const SW_RESET_KEY = "servia.sw.reset.v1.7.0";
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

  // ---------- Google Translate widget (full-page translation) ----------
  (function injectGT() {
    if (document.getElementById("google_translate_element")) return;
    const el = document.createElement("div");
    el.id = "google_translate_element";
    el.style.cssText = "position:absolute;left:-9999px;top:-9999px;width:1px;height:1px;overflow:hidden";
    document.body && document.body.appendChild(el);
    window.googleTranslateElementInit = function () {
      try {
        new google.translate.TranslateElement({
          pageLanguage: "en",
          includedLanguages: "en,ar,ur,hi,bn,ta,ml,tl,ps,ne,ru,fa,fr,zh,es",
          layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
          autoDisplay: false
        }, "google_translate_element");
      } catch (e) { console.warn("[gt]", e); }
    };
    const s = document.createElement("script");
    s.src = "https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit";
    s.async = true; document.head.appendChild(s);
    const css = document.createElement("style");
    css.textContent = ".goog-te-banner-frame, .skiptranslate { display:none !important } body { top:0 !important } .goog-te-gadget { font-size:0 } .goog-te-gadget > span { display:none }";
    document.head.appendChild(css);
  })();

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

  // ---------- live brand binding (deferred to idle so it doesn't compete with LCP) ----------
  const _brandFetch = () => fetch("/api/brand").then(r => r.json()).then((b) => {
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
  if ("requestIdleCallback" in window) requestIdleCallback(_brandFetch, { timeout: 2000 });
  else setTimeout(_brandFetch, 600);

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
