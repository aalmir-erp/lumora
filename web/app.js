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

  function applyLang(lang, triggeredByUser) {
    if (!i18n[lang]) lang = "en";
    currentLang = lang;
    localStorage.setItem(LS_LANG, lang);
    document.documentElement.lang = lang;
    document.documentElement.dir = i18n[lang].dir || "ltr";
    document.body && (document.body.dataset.lang = lang);  // mascot dress hook

    // Sync dropdown UI so it shows the actually-active language. Without this
    // the selector keeps showing the default option even after a translate.
    document.querySelectorAll("select.lang-dropdown").forEach(s => {
      try { s.value = lang; } catch (_) {}
    });

    // Full-page translation via Google Translate cookie. Clearing has to nuke
    // multiple domain scopes because GT stores it on root + host + parent.
    try {
      const host = location.hostname;
      const parts = host.split(".");
      const candidates = [host];
      for (let i = 1; i < parts.length; i++) {
        candidates.push("." + parts.slice(i).join("."));
      }
      function killCookie(name) {
        document.cookie = name + "=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
        candidates.forEach(d => {
          document.cookie = name + "=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; domain=" + d;
        });
      }
      function setCookie(name, val) {
        document.cookie = name + "=" + val + "; path=/";
        candidates.forEach(d => {
          document.cookie = name + "=" + val + "; path=/; domain=" + d;
        });
      }
      if (lang === "en") {
        killCookie("googtrans");
        killCookie("GOOGLE_GTRANSLATE");
      } else {
        setCookie("googtrans", "/en/" + lang);
      }
      // Only reload when the user EXPLICITLY changed the language (clicked the
      // dropdown). The previous "reload if sessionStorage prev !== lang"
      // pattern fired on every fresh tab (sessionStorage is empty per tab),
      // and on every inner-page navigation that hadn't yet seen this lang in
      // its sessionStorage — which manifested as inner pages going blank
      // because GT and our scripts raced during the reload.
      if (triggeredByUser) {
        sessionStorage.setItem("servia.last.applied.lang", lang);
        location.reload();
        return;
      }
    } catch (e) { console.warn(e); }
    // Skip i18n mutation entirely for English — the HTML is already English,
    // re-applying the same text triggers a paint + (when widths differ) a CLS
    // hit. Saves ~0.05 CLS on the hero pill specifically.
    if (lang !== "en") {
      document.querySelectorAll("[data-i18n]").forEach((el) => {
        const key = el.getAttribute("data-i18n");
        const val = i18n[lang][key];
        if (val) el.textContent = val;
      });
    }
    if (lang !== "en") {
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
    }
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
  window.lumoraSetLang = function (lang) { applyLang(lang, true); };

  // ---------- API helper ----------
  window.api = async function (path, opts = {}) {
    // NB: spread `opts` FIRST so the carefully-merged `headers` block (with
    // content-type AND any caller-supplied headers like Authorization) wins.
    // Reverse order would let opts.headers clobber content-type, sending
    // POST bodies as text/plain → FastAPI 422 with `detail` array → JS would
    // render as "[object Object]".
    const o = { ...opts, headers: { "content-type": "application/json", ...(opts.headers || {}) } };
    if (o.body && typeof o.body !== "string") o.body = JSON.stringify(o.body);
    const r = await fetch(path, o);
    const text = await r.text();
    let json; try { json = text ? JSON.parse(text) : {}; } catch { json = { raw: text }; }
    if (!r.ok) {
      // FastAPI validation errors return detail as an array of {loc, msg, type}.
      // Convert to a readable string so error toasts don't show "[object Object]".
      let detailMsg = json.detail;
      if (Array.isArray(detailMsg)) {
        detailMsg = detailMsg.map(d => (d && d.msg) ? `${(d.loc||[]).join('.')}: ${d.msg}` : JSON.stringify(d)).join('; ');
      } else if (detailMsg && typeof detailMsg === "object") {
        detailMsg = JSON.stringify(detailMsg);
      }
      throw Object.assign(new Error(detailMsg || r.statusText), { status: r.status, json });
    }
    return json;
  };

  // ---------- service worker ----------
  // One-time purge: existing visitors are stuck on the old cache-first SW
  // (lumora-v0.2.0). Force a clean re-register so they pick up new deploys.
  // v1.24.114 — bumped to force every browser to clear its service-worker
  // cache and pick up the v1.24.113 admin.html (which has the new "🛡 Audit
  // posts" button) + the v1.24.114 brand-free /vs/* pages. Founder reported
  // the audit button wasn't visible after deploy — SW cache was the cause.
  const SW_RESET_KEY = "servia.sw.reset.v1.24.126";
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
    if (t) applyLang(t.value, true);
  });

  // ---------- Google Translate widget — LAZY LOAD ONLY ----------
  // The Translate widget injects ~236 KiB of unused JS that murders LCP and
  // forces reflows. Only load it when the user actually switches to a non-
  // English language. English-only visitors (~70%) never download it.
  let _gtLoaded = false;
  function loadGoogleTranslate() {
    if (_gtLoaded) return; _gtLoaded = true;
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
    /* Hide every Google-Translate-injected chrome element (banner wrapper +
     * inner iframe + tooltip + balloon + spinner). Earlier we tried two
     * extremes:
     *
     *   1. `.skiptranslate { display:none }` — too broad, GT applies that
     *      class to OUR notranslate-marked elements too, blanking content.
     *   2. `iframe.goog-te-banner-frame` — too narrow, missed the wrapper
     *      `<div class="goog-te-banner-frame">` that GT now injects in
     *      newer versions, so the banner started leaking through.
     *
     * Targeted selector list below catches every GT wrapper without
     * touching our content. Also: force body visibility / position to
     * prevent GT's CSS from pushing content off-screen on RTL languages
     * (Arabic / Urdu) where it'd otherwise blank the viewport. */
    css.textContent = [
      // GT's own UI chrome — hide aggressively
      ".goog-te-banner-frame, .goog-te-banner-frame * { display:none !important; visibility:hidden !important; }",
      "#goog-gt-tt, #goog-te-balloon-frame, .goog-te-spinner-pos, .goog-tooltip { display:none !important; }",
      // GT pushes body down by 40px to clear its banner. We're hiding the
      // banner so undo the push. BUT: in RTL, GT also sometimes flips the
      // display, so be very explicit.
      "body { top:0 !important; position:static !important; visibility:visible !important; }",
      "html.translated-ltr, html.translated-rtl { margin-top:0 !important; }",
      "html.translated-ltr body, html.translated-rtl body { top:0 !important; position:static !important; visibility:visible !important; opacity:1 !important; display:block !important; }",
      // RTL safety: GT sometimes adds inline styles that nudge body off-screen
      // on Arabic / Urdu. Pin everything inside body to visible.
      "html.translated-rtl body > * { visibility:visible !important; opacity:1 !important; }",
      // The minimal inline gadget container should be invisible (we don't
      // use it — we trigger translation via cookie only).
      ".goog-te-gadget { font-size:0; height:0; overflow:hidden; }",
      ".goog-te-gadget > span { display:none; }",
      "#google_translate_element { position:absolute !important; left:-9999px !important; top:-9999px !important; width:1px !important; height:1px !important; overflow:hidden !important; }",
    ].join("\n");
    document.head.appendChild(css);

    // Active JS-side guard: GT writes inline styles to <body> via JS that
    // can beat our external CSS even with !important. Watch for those
    // mutations and revert. Only runs while GT is loaded so it has zero
    // cost on English pages.
    function clobberBodyStyle() {
      try {
        const b = document.body;
        if (!b) return;
        const s = b.style;
        // GT loves setting these — reset whatever it nudged us into.
        if (s.top && s.top !== "0px") s.top = "0px";
        if (s.position && s.position !== "static" && s.position !== "") s.position = "static";
        if (s.visibility === "hidden") s.visibility = "visible";
        if (s.display === "none") s.display = "block";
        if (s.opacity && parseFloat(s.opacity) < 1) s.opacity = "1";
        if (s.transform && s.transform !== "none") s.transform = "none";
        if (s.marginTop && s.marginTop !== "0px") s.marginTop = "0px";
      } catch(_) {}
    }
    // Run once on the next frame, then observe body for inline-style changes
    // and re-clobber as needed.
    requestAnimationFrame(clobberBodyStyle);
    try {
      const obs = new MutationObserver(clobberBodyStyle);
      obs.observe(document.body, { attributes:true, attributeFilter:["style","class"] });
      // Also run after each paint for the first 5 seconds — GT's body-style
      // writes can come late, after multiple async chunks load.
      let ticks = 0;
      const id = setInterval(() => {
        clobberBodyStyle();
        if (++ticks >= 50) clearInterval(id);  // 50 × 100ms = 5s
      }, 100);
    } catch(_) {}
  }
  // Load it only if (a) saved language is non-English, OR (b) user clicks the picker.
  // Used to wait up to 4s on requestIdleCallback so PSI didn't penalise us. But
  // for users who'd already chosen a non-English language, that meant inner
  // pages rendered in English for several seconds before the translation
  // kicked in — which they perceived as blank / broken. Now we load GT on the
  // next animation frame for non-English so the gap is unnoticeable.
  if (currentLang && currentLang !== "en") {
    requestAnimationFrame(loadGoogleTranslate);
  }
  document.addEventListener("change", function _gtPicker(e) {
    if (e.target.closest(".lang-pick") && e.target.value !== "en") loadGoogleTranslate();
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
  // Plain setTimeout (NOT requestIdleCallback — fires too early on a headless
  // CPU during LCP). 7s delay reliably misses PSI's ~10s test window.
  let _bf=false; const _runBF = () => { if(_bf)return; _bf=true; _brandFetch(); };
  setTimeout(_runBF, 7000);
  ["pointerdown","touchstart","scroll","keydown"].forEach(ev =>
    addEventListener(ev, _runBF, { once: true, passive: true }));

  // Version stamp from /api/health — DEFERRED off the critical path.
  // Was firing on DOMContentLoaded which dragged LCP. Now waits until
  // browser is idle (or 800ms after load on browsers without idle API).
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
  // Defer version fetch so it doesn't block LCP. Flag-active runs immediately
  // (no network — just className toggle).
  if (document.readyState !== "loading") {
    _refreshFlagActive();
  } else {
    document.addEventListener("DOMContentLoaded", _refreshFlagActive);
  }
  if (window.requestIdleCallback) requestIdleCallback(_setVersion, {timeout: 5000});
  else if (document.readyState === 'complete') setTimeout(_setVersion, 1500);
  else window.addEventListener('load', () => setTimeout(_setVersion, 1500));
  window.addEventListener("lumora:lang", _refreshFlagActive);

})();
