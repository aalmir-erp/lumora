/* Servia "About this app" floating button + sheet.
 *
 * Shows version, reset/logout, check-for-update, banner-permission reset,
 * and a quick reset-all-cache option. Loaded on every public page so
 * users can find it whether they're in the TWA or browser.
 *
 * Trigger: small ⓘ icon in the bottom-right corner (under the floats-hide
 * toggle from install.js). Tap → bottom sheet with all the settings.
 */
(function () {
  if (window.__servia_about_app) return;
  window.__servia_about_app = true;

  // Skip on admin / vendor / payment pages
  if (/^\/(admin|vendor|portal|pay|invoice)/.test(location.pathname)) return;

  const css = document.createElement("style");
  css.textContent = `
    #servia-about-fab {
      /* v1.24.107 (Bug 32): re-positioned to top of FAB stack.
         Stack order bottom-to-top:
           us-launcher (chat) 24px → wa-fab 104px → cmdk-fab 184px
           → about-fab 252px. 6px right-inset cascade. */
      position:fixed; right:36px; bottom:252px; z-index:1001;
      width:32px; height:32px; border-radius:50%;
      background:#0F172A; color:#fff; font-size:14px;
      border:2px solid rgba(255,255,255,.85);
      box-shadow:0 4px 12px rgba(15,23,42,.35);
      cursor:pointer; padding:0; line-height:1;
      display:inline-flex; align-items:center; justify-content:center;
      opacity:.92; transition:opacity .15s, transform .15s;
    }
    /* When mobile-nav (~56px) is on screen, push the entire FAB stack
       up by 64px so all 4 FABs stay above the nav. */
    .mobile-nav ~ #servia-about-fab { bottom:316px }
    #servia-about-fab:hover, #servia-about-fab:active {
      opacity:1; transform:scale(1.08);
    }

    #servia-about-modal {
      position:fixed; inset:0; background:rgba(15,23,42,.55);
      backdrop-filter:blur(4px); z-index:99998;
      display:flex; align-items:flex-end; justify-content:center;
      animation:abfade .2s;
    }
    @keyframes abfade { from { opacity:0 } to { opacity:1 } }
    #servia-about-modal .sheet {
      background:#fff; width:100%; max-width:520px;
      border-radius:24px 24px 0 0; padding:22px 22px 30px;
      max-height:88vh; overflow:auto;
      box-shadow:0 -16px 40px rgba(15,23,42,.18);
      animation:abup .25s ease;
    }
    @keyframes abup { from { transform:translateY(40px) } to { transform:translateY(0) } }
    .ab-head {
      display:flex; gap:14px; align-items:center; padding-bottom:14px;
      border-bottom:1px solid #E2E8F0; margin-bottom:14px;
    }
    .ab-head img { width:54px; height:54px; border-radius:14px; }
    .ab-head h3 { margin:0; font-size:18px; }
    .ab-head .v {
      font-size:11.5px; font-weight:700; color:#0F766E;
      background:#F0FDFA; padding:2px 10px; border-radius:999px;
      display:inline-block; margin-top:4px; font-family:ui-monospace,monospace;
    }
    .ab-row {
      display:flex; align-items:center; gap:14px; padding:12px 6px;
      border-bottom:1px solid #F1F5F9; cursor:pointer;
      transition:background .12s; user-select:none;
    }
    .ab-row:hover { background:#F8FAFC }
    .ab-row .ic {
      width:38px; height:38px; border-radius:10px; background:#F0FDFA;
      display:flex; align-items:center; justify-content:center;
      font-size:18px; flex-shrink:0;
    }
    .ab-row .body { flex:1; min-width:0 }
    .ab-row .body b { font-size:14px; color:#0F172A; display:block }
    .ab-row .body small { font-size:12px; color:#64748B; line-height:1.4 }
    .ab-row .arrow { color:#94A3B8 }
    .ab-row.danger .ic { background:#FEF2F2 }
    .ab-row.danger b { color:#B91C1C }
    .ab-foot {
      text-align:center; font-size:11px; color:#94A3B8; margin-top:14px; line-height:1.6;
    }
  `;
  document.head.appendChild(css);

  const fab = document.createElement("button");
  fab.id = "servia-about-fab";
  fab.type = "button";
  fab.title = "About this app & settings";
  fab.setAttribute("aria-label", "About this app");
  fab.textContent = "ⓘ";
  fab.onclick = (e) => {
    // v1.22.90: prevent the chat launcher (positioned bottom-right, large
    // hit-area) from receiving the same tap. Also auto-minimize the chat
    // panel if it's open, so the about-modal isn't covered by chat UI.
    e.stopPropagation();
    e.preventDefault();
    try {
      // Close chat panel if open (servia-chat-widget)
      const chatPanel = document.querySelector(".us-panel, .servia-chat-panel, [data-chat-panel]");
      if (chatPanel && (chatPanel.classList.contains("open") ||
                         getComputedStyle(chatPanel).display !== "none")) {
        chatPanel.classList.remove("open");
        chatPanel.style.display = "none";
      }
      // Hide chat launcher temporarily so it can't be tapped behind the modal
      const launcher = document.querySelector(".us-launcher");
      if (launcher) launcher.dataset.preAboutDisplay = launcher.style.display || "";
    } catch (_) {}
    openSheet();
  };

  function attachFab() {
    if (document.getElementById("servia-about-fab")) return;
    if (document.body) document.body.appendChild(fab);
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", attachFab);
  } else {
    attachFab();
  }

  async function fetchVersion() {
    try {
      const r = await fetch("/api/health");
      const j = await r.json();
      return j.version || "?";
    } catch (_) {
      return "?";
    }
  }

  async function openSheet() {
    if (document.getElementById("servia-about-modal")) return;
    const ver = await fetchVersion();
    const isStandalone = window.matchMedia("(display-mode: standalone)").matches
                      || window.navigator.standalone === true;
    const loggedIn = !!localStorage.getItem("lumora.user.tok");
    const userPhone = (function () {
      try {
        const loc = JSON.parse(localStorage.getItem("servia.user.location.v1") || "null");
        return loc?.contact_phone || "";
      } catch (_) { return ""; }
    })();
    const m = document.createElement("div");
    m.id = "servia-about-modal";
    m.innerHTML = `
      <div class="sheet">
        <div class="ab-head">
          <img src="/brand/servia-icon-512x512.png" alt="" onerror="this.style.display='none'">
          <div>
            <h3>About this app</h3>
            <div class="v">v${escapeHtml(ver)} ${isStandalone ? "· installed" : "· browser"}</div>
          </div>
        </div>

        <div class="ab-row" data-action="check-update">
          <div class="ic">🔄</div>
          <div class="body"><b>Check for updates</b><small>Pull the latest version from servia.ae</small></div>
          <div class="arrow">›</div>
        </div>

        <div class="ab-row" data-action="install-app" ${isStandalone ? 'style="display:none"' : ''}>
          <div class="ic">📲</div>
          <div class="body"><b>Install Servia app</b><small>Add to home screen for one-tap access</small></div>
          <div class="arrow">›</div>
        </div>

        <div class="ab-row" data-action="reset-banners">
          <div class="ic">🔔</div>
          <div class="body"><b>Reset banner preferences</b><small>Show all dismissed top banners and install prompts again</small></div>
          <div class="arrow">›</div>
        </div>

        <div class="ab-row" data-action="reset-floats">
          <div class="ic">👁</div>
          <div class="body"><b>Show floating buttons</b><small>Restore minimized cart / install / chat / search</small></div>
          <div class="arrow">›</div>
        </div>

        <div class="ab-row" data-action="reset-location">
          <div class="ic">📍</div>
          <div class="body"><b>Reset saved location</b><small>Re-detect or re-enter your address</small></div>
          <div class="arrow">›</div>
        </div>

        <div class="ab-row" data-action="reset-language">
          <div class="ic">🌐</div>
          <div class="body"><b>Language: <span id="ab-lang">EN</span></b><small>Tap to change UI language</small></div>
          <div class="arrow">›</div>
        </div>

        <div class="ab-row" data-action="logout" ${loggedIn ? '' : 'style="display:none"'}>
          <div class="ic">👤</div>
          <div class="body"><b>Log out</b><small>${escapeHtml(userPhone || "Sign back in next time")}</small></div>
          <div class="arrow">›</div>
        </div>

        <div class="ab-row danger" data-action="reset-all">
          <div class="ic">🗑</div>
          <div class="body"><b>Reset everything</b><small>Clears all preferences, addresses, sessions. The app reloads.</small></div>
          <div class="arrow">›</div>
        </div>

        <div class="ab-foot">
          Servia FZ-LLC · Dubai, UAE<br>
          <a href="/privacy.html" style="color:#0F766E">Privacy</a> ·
          <a href="/terms.html" style="color:#0F766E">Terms</a> ·
          <a href="/contact.html" style="color:#0F766E">Contact</a>
        </div>
      </div>
    `;
    document.body.appendChild(m);
    m.addEventListener("click", e => {
      if (e.target === m) m.remove();
    });
    m.querySelectorAll(".ab-row").forEach(row => {
      row.addEventListener("click", () => handleAction(row.dataset.action, m));
    });
    // Show current language
    try {
      const cur = localStorage.getItem("lumora.lang") || "en";
      const lng = m.querySelector("#ab-lang");
      if (lng) lng.textContent = cur.toUpperCase();
    } catch (_) {}
  }

  function escapeHtml(s) {
    return String(s || "").replace(/[<>&"']/g, c => ({"<":"&lt;",">":"&gt;","&":"&amp;","\"":"&quot;","'":"&#39;"}[c]));
  }

  async function handleAction(action, modal) {
    switch (action) {
      case "check-update":
        // Two-stage update check:
        //   1. Web (service worker): refresh cached HTML/CSS/JS — picks up
        //      banner / nav / scraper-style / page-content changes that
        //      live on the server. Always done.
        //   2. APK (native shell): if running standalone (TWA) and the
        //      bundled APK version is older than the latest GitHub
        //      Release, offer to download the new .apk. Sideloaded APKs
        //      do NOT auto-update — user has to install the new one over
        //      the old one (Android keeps user data).
        toast("⏳ Checking…", 1500);
        try {
          if (navigator.serviceWorker) {
            const regs = await navigator.serviceWorker.getRegistrations();
            await Promise.all(regs.map(r => r.update()));
          }
        } catch (_) {}
        try {
          const r = await fetch("/api/app/latest", {cache:"no-store"});
          if (r.ok) {
            const j = await r.json();
            // Running APK version = either the version baked into the
            // page meta (set by app/main.py via settings.APP_VERSION)
            // or, in the absence of that, the SW-cache version.
            const installedApk = (window.SERVIA_INSTALLED_APK_VER ||
                                   localStorage.getItem("servia.apk.installed_ver") ||
                                   j.web_version || "0.0.0");
            const isStandalone = window.matchMedia("(display-mode: standalone)").matches ||
                                  document.referrer.startsWith("android-app://");
            if (j.apk_url && j.apk_version && cmpSemver(j.apk_version, installedApk) > 0) {
              // Newer APK available
              const proceed = confirm(
                "📲 New Servia version available — v" + j.apk_version +
                " (" + (j.apk_size_mb || "?") + " MB)\n\n" +
                "Your installed app: v" + installedApk + "\n\n" +
                "Sideloaded apps don't auto-update. Tap OK to download the " +
                "new APK; install it over the existing app (your data stays)."
              );
              if (proceed) {
                location.href = j.apk_url;
                // Mark as installed AFTER they tap install on the OS prompt
                // — they'll hit Check-for-updates again later and we'll see
                // the same version and not nag.
                localStorage.setItem("servia.apk.pending_ver", j.apk_version);
              }
              return;  // don't reload
            }
            if (isStandalone && j.apk_version) {
              toast("✓ You're on the latest v" + j.apk_version, 2200);
            } else {
              toast("✓ Web content refreshed — reloading…", 1500);
            }
          }
        } catch (_) {
          toast("⚠ Couldn't check for updates — refreshing web only", 2000);
        }
        setTimeout(() => location.reload(), 1200);
        break;
      case "install-app":
        if (window.serviaShowInstall) window.serviaShowInstall();
        else location.href = "/install.html";
        break;
      case "reset-banners":
        try {
          localStorage.removeItem("servia.topbanner.dismissed_at");
          localStorage.removeItem("servia.install.dismissed");
          localStorage.removeItem("servia.install.dismissed_at");
          document.documentElement.classList.remove("hide-topbanner", "hide-install-banner");
        } catch (_) {}
        toast("✓ Banner preferences reset");
        location.reload();
        break;
      case "reset-floats":
        try { sessionStorage.removeItem("servia.floats.hidden"); } catch (_) {}
        toast("✓ Floating buttons restored");
        location.reload();
        break;
      case "reset-location":
        try { localStorage.removeItem("servia.user.location.v1"); } catch (_) {}
        toast("✓ Saved location cleared");
        location.reload();
        break;
      case "reset-language":
        if (window.lumoraSetLang) {
          // Cycle through common langs as a quick demo
          const next = prompt("Language code (en, ar, ur, hi, fr, ru, es, …)", localStorage.getItem("lumora.lang") || "en");
          if (next) window.lumoraSetLang(next.trim().toLowerCase());
        }
        break;
      case "logout":
        if (!confirm("Log out of Servia on this device?")) return;
        try {
          localStorage.removeItem("lumora.user.tok");
          localStorage.removeItem("lumora.user.type");
        } catch (_) {}
        toast("✓ Logged out");
        location.href = "/login.html";
        break;
      case "reset-all":
        if (!confirm("This clears EVERYTHING — saved addresses, sessions, preferences. Continue?")) return;
        try {
          localStorage.clear();
          sessionStorage.clear();
          if (navigator.serviceWorker) {
            const regs = await navigator.serviceWorker.getRegistrations();
            await Promise.all(regs.map(r => r.unregister()));
          }
          if (window.caches) {
            const keys = await caches.keys();
            await Promise.all(keys.map(k => caches.delete(k)));
          }
        } catch (_) {}
        location.replace("/");
        break;
    }
    if (modal && action !== "reset-language") modal.remove();
  }

  function toast(t, ms) {
    const el = document.createElement("div");
    el.textContent = t;
    el.style.cssText = "position:fixed;bottom:50%;left:50%;transform:translate(-50%,50%);background:#0F172A;color:#fff;padding:14px 22px;border-radius:999px;z-index:99999;font-weight:700;font-size:14px;box-shadow:0 12px 28px rgba(15,23,42,.32);animation:abfade .2s";
    document.body.appendChild(el);
    setTimeout(() => el.remove(), ms || 2200);
  }

  function cmpSemver(a, b) {
    // Returns -1 / 0 / 1 like Array.sort. Tolerates "1.22.84" or "v1.22.84".
    const pa = String(a || "0").replace(/^v/, "").split(".").map(n => parseInt(n) || 0);
    const pb = String(b || "0").replace(/^v/, "").split(".").map(n => parseInt(n) || 0);
    for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
      const x = pa[i] || 0, y = pb[i] || 0;
      if (x > y) return 1;
      if (x < y) return -1;
    }
    return 0;
  }

  // First-launch detection: when the user first opens the TWA, we don't
  // know which APK version they have. We mark the current web version as
  // the "installed APK version" so subsequent update checks can compare.
  // (Best-effort heuristic — accurate as long as APK + web ship together.)
  try {
    const isStandalone = window.matchMedia("(display-mode: standalone)").matches ||
                          document.referrer.startsWith("android-app://");
    if (isStandalone && !localStorage.getItem("servia.apk.installed_ver")) {
      // Pull web version from /api/health (avoids needing it inlined in HTML)
      fetch("/api/health").then(r => r.ok && r.json()).then(j => {
        if (j && j.version) {
          localStorage.setItem("servia.apk.installed_ver", j.version);
        }
      }).catch(()=>{});
    }
    // If a pending APK version was confirmed installed (the user came back
    // to a higher web version after re-installing the APK), update marker.
    const pending = localStorage.getItem("servia.apk.pending_ver");
    if (pending && isStandalone) {
      const cur = localStorage.getItem("servia.apk.installed_ver") || "0";
      if (cmpSemver(pending, cur) > 0) {
        // User likely installed it — but don't overwrite until they
        // open after install. We confirm on next /api/app/latest call.
      }
    }
  } catch (_) {}
})();
