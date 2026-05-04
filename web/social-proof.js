/* Servia social-proof toast — shows periodic 'X just booked Y in Z' alerts
 * to drive conversion + FOMO. Suppressed on admin/cart/pay; throttled hard
 * (1 every 35-50s, max 6 shows per session); never blocks UI.
 */
(function () {
  if (window.__servia_social_proof) return; window.__servia_social_proof = true;
  const path = location.pathname;
  if (/^\/(admin|vendor|portal-vendor|cart\.html|pay)/.test(path)) return;

  const KEY_DISMISSED = "servia.proof.dismissed_at";
  try {
    const last = parseInt(localStorage.getItem(KEY_DISMISSED) || "0", 10);
    if (Date.now() - last < 6 * 3600 * 1000) return;  // dismissed within 6h
  } catch (_) {}

  function init() {
    let shown = 0;
    const MAX_SHOWS = 6;
    const css = document.createElement("style");
    css.textContent = `
      #servia-proof {
        position:fixed;left:14px;bottom:200px;z-index:996;
        background:#fff;border-radius:14px;padding:10px 14px 10px 12px;
        box-shadow:0 10px 28px rgba(15,23,42,.18);
        border:1px solid #E2E8F0;font-size:12.5px;line-height:1.4;
        max-width:280px;display:flex;gap:10px;align-items:flex-start;
        opacity:0;transform:translateX(-12px);
        transition:opacity .35s, transform .35s;
        pointer-events:auto;
      }
      #servia-proof.show { opacity:1; transform:translateX(0) }
      #servia-proof .sp-emoji { font-size:22px; flex-shrink:0; line-height:1 }
      #servia-proof .sp-body { flex:1;min-width:0 }
      #servia-proof .sp-body b { color:#0F766E; font-weight:800 }
      #servia-proof .sp-body small { display:block; color:#94A3B8; margin-top:2px; font-size:11px }
      #servia-proof .sp-x {
        background:transparent;border:0;color:#94A3B8;cursor:pointer;
        font-size:14px;line-height:1;padding:0;margin-inline-start:4px
      }
      @media(max-width:540px){#servia-proof{max-width:240px;font-size:12px;left:8px;bottom:170px}}
    `;
    document.head.appendChild(css);

    const el = document.createElement("div");
    el.id = "servia-proof";
    el.setAttribute("aria-live", "polite");
    document.body.appendChild(el);

    function pickEvent() {
      // Try the live activity feed first; fallback to local synth
      return fetch("/api/activity/live", { cache: "no-store" })
        .then(r => r.ok ? r.json() : null)
        .then(j => {
          const all = (j && j.events) || [];
          const candidates = all.filter(e => e.type === "booking" || e.type === "real_booking" || e.type === "live");
          if (candidates.length) return candidates[Math.floor(Math.random() * candidates.length)];
          return null;
        }).catch(() => null);
    }
    function show(ev) {
      if (!ev) return;
      const ago = ev.ago_min ? (ev.ago_min < 60 ? ev.ago_min + " min ago" : Math.round(ev.ago_min/60) + "h ago") : "just now";
      el.innerHTML =
        '<span class="sp-emoji">' + (ev.icon || "📲") + '</span>' +
        '<div class="sp-body">' +
          '<div><b>' + (ev.area || "Someone in UAE") + '</b> ' + (ev.headline || "just booked a service") + '</div>' +
          '<small>' + ago + ' · verified</small>' +
        '</div>' +
        '<button class="sp-x" aria-label="Dismiss">✕</button>';
      el.classList.add("show");
      el.querySelector(".sp-x").onclick = () => {
        el.classList.remove("show");
        try { localStorage.setItem(KEY_DISMISSED, String(Date.now())); } catch (_) {}
        clearInterval(timer);
      };
      el.onclick = e => {
        if (e.target.classList.contains("sp-x")) return;
        location.href = "/services.html";
      };
      setTimeout(() => el.classList.remove("show"), 7000);
    }
    function tick() {
      if (shown >= MAX_SHOWS) { clearInterval(timer); return; }
      shown++;
      pickEvent().then(show);
    }
    // First show 14s after idle; then every 38s, jittered ±6s
    setTimeout(tick, 14000);
    const timer = setInterval(() => setTimeout(tick, Math.random() * 12000),
                              38000 + Math.random() * 6000);
  }
  if ("requestIdleCallback" in window) requestIdleCallback(init, {timeout: 6000});
  else setTimeout(init, 4000);
})();
