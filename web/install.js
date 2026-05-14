/* Servia mobile-app installer (PWA install — never call it 'PWA' to users).
 *
 * Captures Chrome/Edge/Brave/Samsung-Browser beforeinstallprompt; offers a
 * custom "Get the Servia app" CTA + benefits modal. iOS Safari shows
 * step-by-step instructions (Apple disallows programmatic install).
 *
 * Tracks events to /api/app-install: prompt_shown, accepted, dismissed, installed.
 */
(function () {
  const KEY_DISMISSED = "servia.install.dismissed";
  const KEY_DISMISSED_AT = "servia.install.dismissed_at";
  const KEY_INSTALLED = "servia.install.completed";
  // Banner dismissal now expires after 7 days. Was permanent before, which
  // is why users who tapped X once never saw it again — even after a fresh
  // install / browser change.
  const DISMISS_TTL_MS = 7 * 24 * 60 * 60 * 1000;
  // Debug: append ?show-install=1 to any page URL to force-show the CTAs
  // regardless of dismissed/installed state. Useful for testing.
  const FORCE_SHOW = /[?&]show-install=1\b/.test(location.search);

  let deferred = null;

  // Was the banner dismissed within the TTL?
  function isBannerDismissed() {
    if (FORCE_SHOW) return false;
    if (localStorage.getItem(KEY_DISMISSED) !== "banner") return false;
    const t = parseInt(localStorage.getItem(KEY_DISMISSED_AT) || "0", 10);
    if (!t) return true;  // dismissed before we tracked timestamps — keep dismissed
    if (Date.now() - t > DISMISS_TTL_MS) {
      // expired — reset
      localStorage.removeItem(KEY_DISMISSED);
      localStorage.removeItem(KEY_DISMISSED_AT);
      return false;
    }
    return true;
  }

  // Phone-app benefits — what the user actually gains
  const BENEFITS = [
    { e: "📲", t: "One-tap booking",   d: "Skip the browser. Tap the Servia icon → book in 30s." },
    { e: "🔔", t: "Real-time updates", d: "Live arrival alerts: 'Crew in 10 min', 'Arriving now', 'Done'." },
    { e: "⚡",  t: "Faster everywhere", d: "Loads instantly even on weak signal. Saves your data." },
    { e: "🎁", t: "App-only deals",    d: "Push-only flash discounts. Ambassador tier perks unlocked instantly." },
    { e: "🛡", t: "100% safe + tiny",  d: "No app-store install. Adds a clean icon to your home screen." },
  ];

  function isIOS() { return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream; }
  // v1.24.213 — Android-vs-other detection. Android users go straight to
  // /install (which links to Play Store) instead of seeing the PWA modal —
  // because on Android the real app gives them widgets / better notifications.
  function isAndroid() {
    return /Android/i.test(navigator.userAgent) && !/Windows|iPad|iPhone|iPod/i.test(navigator.userAgent);
  }
  // Currently running inside our installed TWA?
  function isInTWA() {
    return (document.referrer || "").indexOf("android-app://") === 0;
  }
  function isStandalone() {
    return window.matchMedia("(display-mode: standalone)").matches ||
           window.navigator.standalone === true;
  }
  // v1.24.213 — session-only dismissal (founder requirement: banner clears
  // on page refresh). sessionStorage clears when the tab closes OR a hard
  // reload happens, which is what we want.
  const SESSION_DISMISS_KEY = "servia.install.session_dismissed";
  function isSessionDismissed() {
    if (FORCE_SHOW) return false;
    try { return sessionStorage.getItem(SESSION_DISMISS_KEY) === "1"; }
    catch (_) { return false; }
  }
  function setSessionDismissed() {
    try { sessionStorage.setItem(SESSION_DISMISS_KEY, "1"); } catch (_) {}
  }
  // Stable device fingerprint — first/last installs from the same device
  // collapse to one record. localStorage is per-origin, so this works for
  // PWA + TWA + plain web on the same servia.ae origin.
  function deviceId() {
    try {
      let id = localStorage.getItem("servia.device.id");
      if (!id) {
        // Random 16 hex chars — not a privacy concern, just collapse-key.
        id = (crypto.randomUUID ? crypto.randomUUID().replace(/-/g,"") : Math.random().toString(36).slice(2)+Date.now().toString(36)).slice(0,32);
        localStorage.setItem("servia.device.id", id);
      }
      return id;
    } catch (_) { return ""; }
  }
  function detectPlatform() {
    if (window.matchMedia("(display-mode: standalone)").matches) return "twa-or-pwa";
    if (window.navigator.standalone === true) return "ios-pwa";
    return "browser";
  }
  function track(event, extra) {
    const body = {
      event, ...(extra||{}),
      user_agent: navigator.userAgent,
      source: location.pathname,
      referrer: document.referrer,
      // Rich device telemetry — populated on every install event so the
      // admin Mobile-App tab can show "X installs from Pixel 8 / Android 14"
      // without us needing to update the APK or any future migration.
      app_version: (document.querySelector("meta[name=app-version]")||{}).content
                || (window.__servia_app_version || "")
                || (location.search.match(/[?&]app=([\w.-]+)/)||[])[1] || "",
      device_model: navigator.userAgentData ? (navigator.userAgentData.platform || "") : "",
      os_version: navigator.platform || "",
      screen: (window.screen ? `${window.screen.width}x${window.screen.height}` : ""),
      language: navigator.language || "",
      device_id: deviceId(),
      platform: detectPlatform(),
    };
    // Forward an Authorization header if the user is logged in — backend
    // links the install event to the customer record.
    let headers = {"content-type":"application/json"};
    try {
      const tok = localStorage.getItem("lumora.user.tok");
      if (tok && localStorage.getItem("lumora.user.type") === "customer") {
        headers["Authorization"] = "Bearer " + tok;
      }
    } catch (_) {}
    try {
      // sendBeacon doesn't support Authorization headers in most browsers,
      // so fall back to fetch when we have an auth token.
      if (navigator.sendBeacon && !headers["Authorization"]) {
        navigator.sendBeacon("/api/app-install",
          new Blob([JSON.stringify(body)], { type: "application/json" }));
      } else {
        fetch("/api/app-install",
          { method:"POST", headers, keepalive:true, body: JSON.stringify(body) }).catch(()=>{});
      }
    } catch {}
  }

  // ---------- Floating "Get the Servia app" CTA ----------
  function injectFAB() {
    // v1.24.213 — Skip if already installed (TWA or PWA standalone), if
    // user dismissed this session, or if already on the install page.
    if (!FORCE_SHOW && (isStandalone() || isInTWA() ||
        localStorage.getItem(KEY_INSTALLED) || isSessionDismissed())) return;
    if (location.pathname === "/install" || location.pathname === "/install.html") return;
    if (document.getElementById("servia-install-fab")) return;
    // Never show on transactional flows (book / pay / cart / etc.)
    const TRANSACTIONAL = /^\/(book|q|p|i|pay|cart|quote|invoice|checkout)(\b|\/|\.)/;
    if (TRANSACTIONAL.test(location.pathname)) return;
    const fab = document.createElement("button");
    fab.id = "servia-install-fab";
    fab.type = "button";
    fab.title = isAndroid() ? "Get the Servia app on Play Store"
                            : "Install the Servia app";
    fab.setAttribute("aria-label", fab.title);
    fab.innerHTML = "📲";
    fab.style.cssText =
      "position:fixed;bottom:128px;left:14px;z-index:997;" +
      "background:linear-gradient(135deg,#0F766E,#F59E0B);color:#fff;" +
      "width:44px;height:44px;border:0;border-radius:50%;font-size:20px;" +
      "cursor:pointer;box-shadow:0 8px 22px rgba(15,23,42,.28);" +
      "display:inline-flex;align-items:center;justify-content:center;line-height:1;" +
      "transition:transform .12s, box-shadow .12s";
    fab.addEventListener("mouseover", () => fab.style.transform = "translateY(-2px)");
    fab.addEventListener("mouseout", () => fab.style.transform = "");
    // v1.24.213 — Android web users go to /install (which has Play Store
    // CTA + QR code + benefits). Non-Android users get the existing PWA
    // install modal flow.
    fab.onclick = () => {
      if (isAndroid()) {
        track("fab_android_to_install_page");
        location.href = "/install";
      } else {
        openModal();
      }
    };
    document.body.appendChild(fab);
    if (document.querySelector(".mobile-nav")) fab.style.bottom = "150px";
    track("fab_shown");

    // v1.24.213 — Pair the FAB with a soft slide-in banner on Android web
    // (only). The banner has a clear "Get app" CTA + dismissable ✕. Session-
    // only dismissal: refresh brings it back. Built once, lazily.
    if (isAndroid()) injectAndroidBanner();
  }

  // ---------- Android-only install banner (alongside FAB) ----------
  function injectAndroidBanner() {
    if (!isAndroid()) return;
    if (isSessionDismissed() || isStandalone() || isInTWA() ||
        localStorage.getItem(KEY_INSTALLED)) return;
    if (location.pathname === "/install" || location.pathname === "/install.html") return;
    if (document.getElementById("servia-install-banner")) return;
    const b = document.createElement("div");
    b.id = "servia-install-banner";
    b.setAttribute("role", "dialog");
    b.setAttribute("aria-label", "Get the Servia Android app");
    b.style.cssText =
      "position:fixed;left:12px;right:12px;bottom:84px;z-index:9989;" +
      "background:linear-gradient(135deg,#0F766E,#14B8A6);color:#fff;" +
      "border-radius:14px;padding:12px 14px;display:flex;gap:10px;align-items:center;" +
      "box-shadow:0 10px 28px rgba(15,118,110,.35);" +
      "font:600 13px/1.35 system-ui,-apple-system,sans-serif;" +
      "max-width:520px;margin:0 auto;animation:servia-fab-slide .35s";
    b.innerHTML =
      "<div style='font-size:26px;line-height:1;flex-shrink:0'>📲</div>" +
      "<div style='flex:1;min-width:0'>" +
        "<div style='font-weight:800;font-size:14px;margin-bottom:1px'>Get the Servia app</div>" +
        "<div style='opacity:.93;font-size:12px;font-weight:500'>Booking alerts, widgets, faster every day.</div>" +
      "</div>" +
      "<a href='/install' style='background:#FBBF24;color:#0F172A;padding:9px 14px;border-radius:10px;text-decoration:none;font-weight:800;font-size:12.5px;white-space:nowrap'>See more</a>" +
      "<button type='button' aria-label='Dismiss' style='background:transparent;border:0;color:rgba(255,255,255,.85);font-size:18px;cursor:pointer;padding:4px 6px;font-weight:700'>&times;</button>";
    b.querySelector("a").addEventListener("click", () => track("banner_android_to_install_page"));
    b.querySelector("button").addEventListener("click", () => {
      setSessionDismissed();
      b.remove();
      const fab = document.getElementById("servia-install-fab");
      if (fab) fab.remove();
      track("banner_session_dismissed");
    });
    document.body.appendChild(b);
    if (!document.getElementById("servia-fab-anim")) {
      const st = document.createElement("style");
      st.id = "servia-fab-anim";
      st.textContent = "@keyframes servia-fab-slide{from{transform:translateY(16px);opacity:0}to{transform:translateY(0);opacity:1}}";
      document.head.appendChild(st);
    }
  }

  // ---------- Subtle banner (top of page) ----------
  // v1.24.3 — DISABLED. banner.js already rotates a "📲 Get the Servia mobile
  // app" slide so a separate install banner just stacked another teal stripe
  // on top of the page. We keep the modal + FAB; banner.js's slide opens this
  // modal via window.serviaShowInstall.
  function injectBanner() { return; }

  // ---------- Detailed install modal ----------
  function openModal() {
    track("prompt_shown");
    if (document.getElementById("servia-install-modal")) return;
    const m = document.createElement("div");
    m.id = "servia-install-modal";
    m.style.cssText =
      "position:fixed;inset:0;background:rgba(15,23,42,.55);backdrop-filter:blur(4px);z-index:99999;" +
      "display:flex;align-items:flex-end;justify-content:center;animation:fadein .2s";
    const sheet = document.createElement("div");
    sheet.style.cssText =
      "background:#fff;border-radius:24px 24px 0 0;width:100%;max-width:520px;padding:28px 24px 32px;" +
      "max-height:88vh;overflow:auto;box-shadow:0 -16px 40px rgba(15,23,42,.18);animation:slideup .25s";
    sheet.innerHTML = `
      <div style="text-align:center;margin-bottom:14px">
        <img src="/icon-192.svg" width="64" height="64" alt="Servia" style="border-radius:18px;box-shadow:0 8px 18px rgba(15,23,42,.18);margin:0 auto 10px;display:block">
        <h2 style="margin:0 0 4px;font-size:22px;letter-spacing:-.02em">Install the Servia app</h2>
        <p style="margin:0;color:var(--muted);font-size:14px">Faster booking · push alerts · AED 50 off your first app-booking.</p>
      </div>
      <div id="servia-install-benefits" style="margin:18px 0">
        ${BENEFITS.map(b => `
          <div style="display:flex;gap:12px;padding:12px 0;border-top:1px solid var(--border)">
            <div style="font-size:24px;flex-shrink:0">${b.e}</div>
            <div>
              <div style="font-weight:700;font-size:14px">${b.t}</div>
              <div style="font-size:12px;color:var(--muted);line-height:1.5">${b.d}</div>
            </div>
          </div>`).join("")}
      </div>
      <div id="servia-install-actions"></div>
      <p style="text-align:center;font-size:11px;color:var(--muted);margin-top:14px">No app store. Just adds an icon to your home screen. 0.5 MB.</p>
    `;
    m.appendChild(sheet);
    m.onclick = (e) => { if (e.target === m) close(); };
    function close() { m.remove(); }
    document.body.appendChild(m);

    // Wire actions based on platform
    const acts = sheet.querySelector("#servia-install-actions");
    if (deferred && typeof deferred.prompt === "function") {
      // Chrome/Edge/Samsung — programmatic install
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "📲 Install Servia";
      btn.style.cssText =
        "width:100%;background:linear-gradient(135deg,#0F766E,#F59E0B);color:#fff;border:0;padding:14px 24px;" +
        "border-radius:999px;font-weight:700;font-size:16px;cursor:pointer;min-height:48px";
      btn.onclick = async () => {
        try {
          deferred.prompt();
          const choice = await deferred.userChoice;
          track(choice.outcome === "accepted" ? "accepted" : "dismissed",
                { platform: choice.platform });
          if (choice.outcome === "accepted") {
            localStorage.setItem(KEY_INSTALLED, "1");
          }
        } catch (e) { console.warn(e); }
        deferred = null;
        close();
      };
      acts.appendChild(btn);
    } else if (isIOS()) {
      // iOS Safari — show steps (Apple doesn't allow programmatic prompt)
      acts.innerHTML = `
        <div style="background:#FEF3C7;border:1px solid #FCD34D;border-radius:14px;padding:16px;font-size:14px;line-height:1.6">
          <b>Add to your iPhone home screen:</b>
          <ol style="margin:8px 0 0;padding-inline-start:22px">
            <li>Tap the <b>Share</b> button at the bottom of Safari (the square with up-arrow).</li>
            <li>Scroll and tap <b>"Add to Home Screen"</b>.</li>
            <li>Tap <b>Add</b> in the top right. Done — Servia icon appears on your home screen.</li>
          </ol>
        </div>
      `;
      track("ios_instructions_shown");
    } else {
      // No deferred prompt available — generic instructions
      acts.innerHTML = `
        <div style="background:#FEF3C7;border:1px solid #FCD34D;border-radius:14px;padding:16px;font-size:14px;line-height:1.6">
          <b>Tap your browser menu (⋮) → "Install Servia" or "Add to Home Screen".</b>
          <p style="margin:8px 0 0">If you don't see it, your browser doesn't support installs yet — try Chrome, Edge or Safari.</p>
        </div>`;
    }
    const skip = document.createElement("button");
    skip.type = "button";
    skip.textContent = "Maybe later";
    skip.style.cssText =
      "width:100%;background:transparent;color:var(--muted);border:0;padding:12px;cursor:pointer;font-size:13px;margin-top:8px";
    skip.onclick = () => { track("modal_dismissed"); close(); };
    acts.appendChild(skip);
  }

  // ---------- Hooks ----------
  // Show the FAB + top banner on every page load (subject to the same
  // dismissed/installed/standalone guards inside each function). Used to
  // gate this on `beforeinstallprompt`, but that event is browser-
  // engagement-heuristic-driven — after a service-worker wipe (like the
  // one v1.22.65 forced) Chrome can take a load or two to re-fire it,
  // making the install CTAs disappear for stretches. The modal that
  // opens from the FAB already handles "no deferred prompt" (iOS path
  // or generic instructions), so we don't need beforeinstallprompt to
  // surface the CTA — just to enable one-tap programmatic install.
  function surfaceInstallCTAs() {
    if (!FORCE_SHOW && (isStandalone() || localStorage.getItem(KEY_INSTALLED))) return;
    injectBanner();  // its own dismissal-TTL check inside
    injectFAB();
  }

  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferred = e;
    track("eligible");
    // Re-run surface in case we were called too early — the FAB now also
    // gets the deferred prompt wired up via openModal() when clicked.
    surfaceInstallCTAs();
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", surfaceInstallCTAs);
  } else {
    surfaceInstallCTAs();
  }
  window.addEventListener("appinstalled", () => {
    localStorage.setItem(KEY_INSTALLED, "1");
    track("installed");
    const fab = document.getElementById("servia-install-fab");
    if (fab) fab.remove();
    const banner = document.getElementById("servia-install-banner");
    if (banner) banner.remove();
    // Quick celebration toast
    const t = document.createElement("div");
    t.textContent = "✅ Servia installed! Open it from your home screen.";
    t.style.cssText = "position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:#065F46;color:#fff;padding:14px 22px;border-radius:999px;z-index:99999;font-weight:700;font-size:14px;box-shadow:0 10px 28px rgba(15,23,42,.22)";
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 4000);
  });

  // iOS doesn't fire beforeinstallprompt — show CTA after 4s of dwell time
  if (isIOS() && !isStandalone() && !localStorage.getItem(KEY_INSTALLED)) {
    setTimeout(() => {
      injectFAB();
      if (localStorage.getItem(KEY_DISMISSED) !== "banner") injectBanner();
    }, 4000);
  }

  // Public API for any "Install" button on the site
  // v1.24.213 — banner.js + other surfaces call window.serviaShowInstall().
  // On Android we redirect to /install instead of showing the PWA modal,
  // because the user benefits from the real app (widgets, OS-level
  // notifications, faster shell).
  window.serviaShowInstall = function () {
    if (isAndroid() && !isInTWA() && !isStandalone()) {
      track("serviaShowInstall_android_to_install_page");
      location.href = "/install";
      return;
    }
    openModal();
  };

  // Fire a `launched` event whenever the app loads in standalone (TWA / PWA)
  // mode — the admin Mobile-App tab uses these to count installs in the wild.
  // Once-per-day per device to avoid flooding.
  try {
    if (isStandalone()) {
      const today = new Date().toISOString().slice(0, 10);
      if (localStorage.getItem("servia.launched.today") !== today) {
        localStorage.setItem("servia.launched.today", today);
        track("launched");
      }
    }
  } catch (_) {}

  // ---------- Floating UI session-minimize ----------
  // The user complained that floating FABs (cart, install, search, chat)
  // crowd the screen. This adds a tiny ✕ master toggle at the corner —
  // tap once to hide ALL floating elements for the rest of the session.
  // SessionStorage so it resets on next visit.
  const KEY_FLOATS_HIDDEN = "servia.floats.hidden";
  const FLOAT_SELECTORS = [
    "#servia-cart-badge",
    "#servia-cart-pop",
    "#servia-install-fab",
    ".cmdk-fab",          // search palette FAB from search-widget.js
    ".us-launcher",       // chat FAB from widget.js
    ".servia-chat-online", // online presence badge if loaded
    "#servia-proof",      // social-proof toast if loaded
  ];
  function setFloatsHidden(hidden) {
    try { sessionStorage.setItem(KEY_FLOATS_HIDDEN, hidden ? "1" : "0"); } catch(_) {}
    FLOAT_SELECTORS.forEach(s => {
      document.querySelectorAll(s).forEach(el => {
        el.style.display = hidden ? "none" : "";
      });
    });
    document.getElementById("servia-floats-hide").style.display = hidden ? "none" : "";
    document.getElementById("servia-floats-show").style.display = hidden ? "inline-flex" : "none";
  }

  function injectFloatToggle() {
    if (document.getElementById("servia-floats-hide")) return;
    const css = document.createElement("style");
    css.textContent = `
      #servia-floats-hide, #servia-floats-show {
        position:fixed; right:6px; bottom:6px; z-index:1000;
        width:24px; height:24px; border-radius:50%; border:0;
        background:rgba(15,23,42,.55); color:#fff; font-size:12px;
        cursor:pointer; padding:0; line-height:1;
        display:inline-flex; align-items:center; justify-content:center;
        opacity:.45; transition:opacity .15s;
      }
      #servia-floats-hide:hover, #servia-floats-show:hover { opacity:1 }
      .mobile-nav ~ #servia-floats-hide,
      .mobile-nav ~ #servia-floats-show { bottom:74px }
    `;
    document.head.appendChild(css);
    const hide = document.createElement("button");
    hide.id = "servia-floats-hide"; hide.type = "button"; hide.title = "Hide floating buttons for this session";
    hide.setAttribute("aria-label", "Hide floating buttons");
    hide.textContent = "✕";
    hide.onclick = () => setFloatsHidden(true);
    const show = document.createElement("button");
    show.id = "servia-floats-show"; show.type = "button"; show.title = "Show floating buttons";
    show.setAttribute("aria-label", "Show floating buttons");
    show.textContent = "+"; show.style.display = "none";
    show.onclick = () => setFloatsHidden(false);
    document.body.appendChild(hide);
    document.body.appendChild(show);
    // Restore session state
    try {
      if (sessionStorage.getItem(KEY_FLOATS_HIDDEN) === "1") setFloatsHidden(true);
    } catch(_) {}
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", injectFloatToggle);
  } else {
    injectFloatToggle();
  }
  // Re-apply after a delay to catch lazily-loaded floats (chat widget,
  // social-proof toast — they appear after first interaction).
  setTimeout(() => {
    try {
      if (sessionStorage.getItem(KEY_FLOATS_HIDDEN) === "1") setFloatsHidden(true);
    } catch(_) {}
  }, 4000);
})();
