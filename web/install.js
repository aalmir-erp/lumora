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
  const KEY_INSTALLED = "servia.install.completed";

  let deferred = null;

  // Phone-app benefits — what the user actually gains
  const BENEFITS = [
    { e: "📲", t: "One-tap booking",   d: "Skip the browser. Tap the Servia icon → book in 30s." },
    { e: "🔔", t: "Real-time updates", d: "Live arrival alerts: 'Crew in 10 min', 'Arriving now', 'Done'." },
    { e: "⚡",  t: "Faster everywhere", d: "Loads instantly even on weak signal. Saves your data." },
    { e: "🎁", t: "App-only deals",    d: "Push-only flash discounts. Ambassador tier perks unlocked instantly." },
    { e: "🛡", t: "100% safe + tiny",  d: "No app-store install. Adds a clean icon to your home screen." },
  ];

  function isIOS() { return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream; }
  function isStandalone() {
    return window.matchMedia("(display-mode: standalone)").matches ||
           window.navigator.standalone === true;
  }
  function track(event, extra) {
    try {
      navigator.sendBeacon
        ? navigator.sendBeacon("/api/app-install",
            new Blob([JSON.stringify({ event, ...(extra||{}),
              user_agent: navigator.userAgent, source: location.pathname,
              referrer: document.referrer })], { type: "application/json" }))
        : fetch("/api/app-install", { method:"POST",
            headers:{"content-type":"application/json"}, keepalive:true,
            body: JSON.stringify({ event, ...(extra||{}),
              user_agent: navigator.userAgent, source: location.pathname,
              referrer: document.referrer }) }).catch(()=>{});
    } catch {}
  }

  // ---------- Floating "Get the Servia app" CTA ----------
  function injectFAB() {
    if (isStandalone() || localStorage.getItem(KEY_INSTALLED)) return;
    if (document.getElementById("servia-install-fab")) return;
    const fab = document.createElement("button");
    fab.id = "servia-install-fab";
    fab.type = "button";
    fab.innerHTML = "📲 <span>Get the Servia app</span>";
    fab.style.cssText =
      "position:fixed;bottom:78px;left:14px;z-index:998;background:linear-gradient(135deg,#0F766E,#F59E0B);" +
      "color:#fff;border:0;padding:12px 18px;border-radius:999px;font-weight:700;font-size:14px;" +
      "cursor:pointer;box-shadow:0 8px 24px rgba(15,23,42,.22);display:flex;gap:8px;align-items:center;" +
      "transition:transform .15s";
    fab.addEventListener("mouseover", () => fab.style.transform = "translateY(-2px)");
    fab.addEventListener("mouseout", () => fab.style.transform = "");
    fab.onclick = openModal;
    document.body.appendChild(fab);
    // On mobile bottom-nav pages, raise it so it doesn't collide
    if (document.querySelector(".mobile-nav")) fab.style.bottom = "84px";
    track("fab_shown");
  }

  // ---------- Subtle banner (top of page) ----------
  function injectBanner() {
    if (isStandalone() || localStorage.getItem(KEY_INSTALLED)) return;
    if (localStorage.getItem(KEY_DISMISSED) === "banner") return;
    if (document.getElementById("servia-install-banner")) return;
    const b = document.createElement("div");
    b.id = "servia-install-banner";
    b.innerHTML =
      '<span style="font-size:18px">📲</span>' +
      '<span><b>Servia mobile app</b> · faster, arrival alerts, app-only deals.</span>' +
      '<button id="servia-install-banner-go" type="button">Install</button>' +
      '<button id="servia-install-banner-x" type="button" aria-label="Dismiss">✕</button>';
    b.style.cssText =
      "display:flex;gap:10px;align-items:center;justify-content:center;padding:8px 14px;" +
      "background:linear-gradient(90deg,#0F766E,#0D9488);color:#fff;font-size:13px;font-weight:600;" +
      "flex-wrap:wrap;line-height:1.4";
    b.querySelector("#servia-install-banner-go").style.cssText =
      "background:#FCD34D;color:#0F172A;border:0;padding:6px 14px;border-radius:999px;font-weight:800;cursor:pointer;font-size:13px";
    b.querySelector("#servia-install-banner-x").style.cssText =
      "background:transparent;color:#fff;border:0;cursor:pointer;font-size:16px;opacity:.7";
    // Insert at top of body, after the flag strip if present
    const flag = document.querySelector(".uae-flag-strip");
    if (flag && flag.nextSibling) flag.parentNode.insertBefore(b, flag.nextSibling);
    else document.body.insertBefore(b, document.body.firstChild);
    document.getElementById("servia-install-banner-go").onclick = openModal;
    document.getElementById("servia-install-banner-x").onclick = () => {
      localStorage.setItem(KEY_DISMISSED, "banner");
      b.remove(); track("banner_dismissed");
    };
    track("banner_shown");
  }

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
  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferred = e;
    track("eligible");
    // If they haven't dismissed, surface CTA
    if (localStorage.getItem(KEY_DISMISSED) !== "banner") injectBanner();
    injectFAB();
  });
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
  window.serviaShowInstall = openModal;
})();
