/* Servia animated multi-slide announcement banner.
 *
 * Auto-injected on top of every page (above the nav). Cycles through
 * marketing/value messages with smooth slide+fade transitions. Single
 * dismissable for 24h via localStorage. Picks page-aware slides when a
 * meta tag <meta name="servia-page" content="..."> is present.
 *
 * Skips: /admin.html, /vendor.html, /portal-vendor.html (internal pages),
 *        /pay/* (payment flow — should stay clean).
 */
// Defer all banner work until the browser is idle so it never blocks LCP / TBT.
function __serviaBannerInit() {
  const KEY_DISMISSED = "servia.topbanner.dismissed_at";
  const path = location.pathname;
  if (/^\/(admin|vendor|portal-vendor|pay)/.test(path)) return;
  // Suppress for 24h after explicit dismiss
  try {
    const last = parseInt(localStorage.getItem(KEY_DISMISSED) || "0", 10);
    if (Date.now() - last < 24 * 3600 * 1000) return;
  } catch (_) {}

  // Page-context-aware slide deck
  const pageMeta = document.querySelector('meta[name="servia-page"]');
  const ctx = (pageMeta && pageMeta.content) || "default";

  // Each slide: {emoji, text:[head, body], cta:{label,href}, tone}
  const DECKS = {
    default: [
      { emoji: "⚡", head: "Book in 60 seconds", body: "Trusted UAE pros, vetted + insured. Same-day available across all 7 emirates.",
        cta: { label: "Book now →", href: "/book.html" }, tone: "teal" },
      { emoji: "🎁", head: "Become an Ambassador", body: "Refer friends to climb tiers — get up to 20% off every booking.",
        cta: { label: "Earn rewards →", href: "/share-rewards.html" }, tone: "amber" },
      { emoji: "📲", head: "Get the Servia mobile app", body: "Faster booking, real-time arrival alerts, app-only deals.",
        cta: { label: "Install app →", href: "javascript:window.serviaShowInstall&&serviaShowInstall()" }, tone: "purple" },
      { emoji: "🇦🇪", head: "All 7 emirates · live coverage", body: "200+ areas in Dubai, 80+ in Abu Dhabi, 60+ in Sharjah.",
        cta: { label: "See live map →", href: "/coverage.html" }, tone: "green" },
      { emoji: "🛡", head: "AED 25,000 damage cover", body: "Plus 7-day re-do guarantee on every Servia service. Pay only when satisfied.",
        cta: { label: "How it works →", href: "/services.html" }, tone: "indigo" },
      { emoji: "📝", head: "Daily UAE service tips", body: "Locally-informed articles updated every day — pre-summer prep, sandstorm cleaning, more.",
        cta: { label: "Read journal →", href: "/blog" }, tone: "rose" },
    ],
    book: [
      { emoji: "💎", head: "Pay securely in advance", body: "Apple Pay · Google Pay · Card · Tabby. Slot confirmed instantly.",
        cta: { label: "—", href: "" }, tone: "teal" },
      { emoji: "🛡", head: "Servia 7-day re-do guarantee", body: "If you're not happy, message us within 24h — we re-do free, no fine print.",
        cta: { label: "—", href: "" }, tone: "amber" },
      { emoji: "🌬", head: "AC service slots disappearing fast", body: "Pre-summer bookings up 240% this week — secure your morning slot.",
        cta: { label: "—", href: "" }, tone: "purple" },
    ],
    services: [
      { emoji: "🧹", head: "Cleaning crews available today", body: "Deep clean · maid hourly · move-in / move-out · sofa & carpet.",
        cta: { label: "See pricing →", href: "/services.html" }, tone: "teal" },
      { emoji: "🔧", head: "Handyman in 2 hours", body: "Plumbing · electrical · paint touch-ups · curtain rods · IKEA assembly.",
        cta: { label: "Book handyman →", href: "/book.html?service=handyman" }, tone: "amber" },
      { emoji: "🪲", head: "Pest control discreet visits", body: "Cockroach · bed bugs · ants · rodents — 90-day warranty included.",
        cta: { label: "Book pest control →", href: "/book.html?service=pest_control" }, tone: "green" },
    ],
    me: [
      { emoji: "🎁", head: "Climb the Ambassador tier ladder", body: "Refer 3 friends → Silver 10% off every booking · 6 → Gold 15% · 11+ → Platinum 20%.",
        cta: { label: "Get my link →", href: "/me.html?tab=referral" }, tone: "amber" },
      { emoji: "📲", head: "Add Servia to home screen", body: "One-tap booking + push alerts when crew is 10 min away.",
        cta: { label: "Install app →", href: "javascript:window.serviaShowInstall&&serviaShowInstall()" }, tone: "purple" },
    ],
    blog: [
      { emoji: "📝", head: "Fresh UAE-specific tips daily", body: "AC pre-summer, sandstorm reset, Ramadan kitchen deep clean — written for UAE residents.",
        cta: { label: "Read all →", href: "/blog" }, tone: "rose" },
    ],
    coverage: [
      { emoji: "📍", head: "Live coverage updating now", body: "Watch jobs starting and reviews landing in real time across UAE.",
        cta: { label: "View ambassadors →", href: "/share-rewards.html" }, tone: "green" },
    ],
  };
  const slides = DECKS[ctx] || DECKS.default;
  if (!slides || !slides.length) return;

  const TONES = {
    teal:   "linear-gradient(90deg,#0F766E 0%,#0D9488 50%,#14B8A6 100%)",
    amber:  "linear-gradient(90deg,#B45309 0%,#F59E0B 50%,#FCD34D 100%)",
    purple: "linear-gradient(90deg,#5B21B6 0%,#7C3AED 50%,#A78BFA 100%)",
    green:  "linear-gradient(90deg,#065F46 0%,#15803D 50%,#22C55E 100%)",
    indigo: "linear-gradient(90deg,#312E81 0%,#4F46E5 50%,#818CF8 100%)",
    rose:   "linear-gradient(90deg,#9F1239 0%,#E11D48 50%,#FB7185 100%)",
  };

  // Inject CSS once
  if (!document.getElementById("servia-banner-css")) {
    const css = document.createElement("style");
    css.id = "servia-banner-css";
    css.textContent = `
      #servia-topbanner {
        position: relative; width: 100%; min-height: 44px; overflow: hidden;
        font-size: 13.5px; font-weight: 600; line-height: 1.35;
        color: #fff; isolation: isolate;
        transition: background 0.7s ease;
      }
      #servia-topbanner::before {
        content: ""; position: absolute; inset: 0;
        background-image: radial-gradient(circle at 20% 50%, rgba(255,255,255,.15) 0%, transparent 30%),
                          radial-gradient(circle at 80% 50%, rgba(255,255,255,.10) 0%, transparent 30%);
        animation: servia-shimmer 8s linear infinite;
      }
      @keyframes servia-shimmer {
        0% { transform: translateX(0) }
        100% { transform: translateX(-30%) }
      }
      #servia-topbanner .b-track {
        position: relative; max-width: 1180px; margin: 0 auto;
        padding: 8px 40px 8px 14px;
        display: flex; align-items: center; gap: 10px;
        flex-wrap: nowrap; min-height: 44px;
      }
      #servia-topbanner .b-slide {
        display: flex; align-items: center; gap: 10px; width: 100%;
        opacity: 0; transform: translateY(8px);
        transition: opacity .55s ease, transform .55s ease;
        position: absolute; left: 14px; right: 40px; top: 50%;
        margin-top: -10px;
      }
      #servia-topbanner .b-slide.active { opacity: 1; transform: translateY(0); position: relative; left: 0; top: 0; margin-top: 0 }
      #servia-topbanner .b-slide.exit  { opacity: 0; transform: translateY(-10px) }
      #servia-topbanner .b-emoji { font-size: 20px; flex-shrink: 0; filter: drop-shadow(0 1px 2px rgba(0,0,0,.2)) }
      #servia-topbanner .b-text { display: flex; gap: 6px; align-items: baseline; flex-wrap: wrap; flex: 1; min-width: 0 }
      #servia-topbanner .b-text b { font-weight: 800; letter-spacing: -.01em }
      #servia-topbanner .b-text span { color: rgba(255,255,255,.92); font-weight: 500 }
      #servia-topbanner .b-cta {
        display: inline-flex; align-items: center; justify-content: center;
        padding: 12px 18px; min-height: 44px; min-width: 88px; border-radius: 999px;
        background: rgba(255,255,255,.95); color: #0F172A !important;
        font-weight: 800; font-size: 13px; text-decoration: none;
        white-space: nowrap; flex-shrink: 0; margin: 0 6px;
        transition: transform .12s ease, background .15s ease;
      }
      #servia-topbanner .b-cta:hover { transform: translateY(-1px); background: #fff }
      #servia-topbanner .b-dots {
        position: absolute; bottom: 3px; left: 50%; transform: translateX(-50%);
        display: flex; gap: 4px; z-index: 4;
      }
      #servia-topbanner .b-dots .d {
        width: 5px; height: 5px; border-radius: 50%;
        background: rgba(255,255,255,.4); transition: background .25s, width .25s
      }
      #servia-topbanner .b-dots .d.active { background: #fff; width: 14px; border-radius: 999px }
      #servia-topbanner .b-x {
        position: absolute; right: 8px; top: 50%; transform: translateY(-50%);
        background: rgba(0,0,0,.22); border: 0; color: #fff;
        width: 44px; height: 44px; border-radius: 50%;
        cursor: pointer; font-size: 18px; line-height: 1;
        display: flex; align-items: center; justify-content: center;
        opacity: .85; transition: opacity .12s, background .12s; z-index: 4;
      }
      #servia-topbanner .b-x:hover { opacity: 1; background: rgba(0,0,0,.32) }
      @media (max-width: 640px) {
        #servia-topbanner { font-size: 12.5px }
        #servia-topbanner .b-emoji { font-size: 17px }
        #servia-topbanner .b-cta { padding: 7px 12px; font-size: 11.5px; min-height: 32px }
        #servia-topbanner .b-text b { font-size: 13px }
        #servia-topbanner .b-text span { display: none }
        #servia-topbanner .b-dots { display: none }
      }
      @media (prefers-reduced-motion: reduce) {
        #servia-topbanner::before { animation: none }
        #servia-topbanner .b-slide { transition: none }
      }
    `;
    document.head.appendChild(css);
  }

  // Build banner DOM. If a stub was already inserted (see __serviaBannerReserveSlot
  // at the bottom of this file), reuse it so there's no layout shift between
  // "blank stub" → "real banner". Otherwise create a fresh element.
  const existing = document.getElementById("servia-topbanner");
  const wrap = existing || document.createElement("div");
  wrap.id = "servia-topbanner";
  wrap.innerHTML = "";  // clear stub content if reused
  wrap.style.background = TONES[slides[0].tone] || TONES.teal;
  const track = document.createElement("div");
  track.className = "b-track";
  wrap.appendChild(track);
  slides.forEach((s, i) => {
    const node = document.createElement("div");
    node.className = "b-slide" + (i === 0 ? " active" : "");
    const cta = (s.cta && s.cta.label && s.cta.label !== "—")
      ? `<a class="b-cta" href="${s.cta.href}">${s.cta.label}</a>`
      : "";
    node.innerHTML =
      `<span class="b-emoji" aria-hidden="true">${s.emoji}</span>` +
      `<span class="b-text"><b>${s.head}</b><span>${s.body}</span></span>` +
      cta;
    track.appendChild(node);
  });
  // Dots indicator
  const dots = document.createElement("div");
  dots.className = "b-dots";
  dots.setAttribute("aria-hidden", "true");
  slides.forEach((_, i) => {
    const d = document.createElement("div");
    d.className = "d" + (i === 0 ? " active" : "");
    dots.appendChild(d);
  });
  wrap.appendChild(dots);
  // Dismiss button
  const x = document.createElement("button");
  x.className = "b-x";
  x.type = "button";
  x.setAttribute("aria-label", "Dismiss banner");
  x.textContent = "✕";
  x.onclick = () => {
    try { localStorage.setItem(KEY_DISMISSED, String(Date.now())); } catch (_) {}
    wrap.style.transition = "max-height .35s ease, opacity .35s ease";
    wrap.style.maxHeight = wrap.offsetHeight + "px";
    requestAnimationFrame(() => {
      wrap.style.maxHeight = "0";
      wrap.style.opacity = "0";
      setTimeout(() => wrap.remove(), 360);
    });
  };
  wrap.appendChild(x);

  // Inject above the flag strip if present, else top of body — but ONLY if
  // we created a fresh node. If we reused an existing stub it's already in
  // the DOM at the right place.
  if (!existing) {
    const insertNow = () => {
      const flag = document.querySelector(".uae-flag-strip");
      const target = flag && flag.parentNode === document.body ? flag : document.body.firstChild;
      if (target) document.body.insertBefore(wrap, target);
      else document.body.appendChild(wrap);
    };
    if (document.body) insertNow();
    else document.addEventListener("DOMContentLoaded", insertNow, { once: true });
  }

  // Cycle slides every 4s
  let i = 0;
  const slideEls = wrap.querySelectorAll(".b-slide");
  const dotEls = wrap.querySelectorAll(".b-dots .d");
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const period = reduced ? 9000 : 4000;
  setInterval(() => {
    const cur = slideEls[i];
    const next = slideEls[(i + 1) % slideEls.length];
    cur.classList.remove("active");
    cur.classList.add("exit");
    next.classList.add("active");
    setTimeout(() => cur.classList.remove("exit"), 600);
    dotEls.forEach((d, di) => d.classList.toggle("active", di === (i + 1) % slideEls.length));
    i = (i + 1) % slideEls.length;
    // Background tone follows slide tone
    wrap.style.background = TONES[slides[i].tone] || TONES.teal;
  }, period);
}
// Reserve banner layout space EARLY so when init() injects content there's
// no layout jerk. The previous "wait 11s or first interaction" path made
// the banner feel broken — users would render the page, then much later
// (or on their first click) a teal bar would suddenly slide in above the
// nav. The 0.05 CLS we saved that way wasn't worth a UX that looks broken.
function __serviaBannerReserveSlot() {
  const path = location.pathname;
  if (/^\/(admin|vendor|portal-vendor|pay)/.test(path)) return null;
  try {
    const last = parseInt(localStorage.getItem("servia.topbanner.dismissed_at") || "0", 10);
    if (Date.now() - last < 24 * 3600 * 1000) return null;
  } catch (_) {}
  if (document.getElementById("servia-topbanner")) return null;
  const stub = document.createElement("div");
  stub.id = "servia-topbanner";
  stub.style.cssText = "min-height:44px;background:linear-gradient(90deg,#0F766E,#0D9488,#14B8A6)";
  const insert = () => {
    if (document.getElementById("servia-topbanner") && stub.parentNode) return;
    const flag = document.querySelector(".uae-flag-strip");
    const target = flag && flag.parentNode === document.body ? flag : document.body.firstChild;
    if (target) document.body.insertBefore(stub, target);
    else document.body.appendChild(stub);
  };
  if (document.body) insert();
  else document.addEventListener("DOMContentLoaded", insert, { once:true });
  return stub;
}
__serviaBannerReserveSlot();

// Init runs early — well before 11s — so the banner is interactive when
// the user shows up. We still defer past LCP via requestIdleCallback (or a
// tiny setTimeout fallback), and still fire on first interaction in case
// rIC takes its time.
let _bannerFired = false;
const _bannerGo = () => {
  if (_bannerFired) return; _bannerFired = true;
  __serviaBannerInit();
};
if ("requestIdleCallback" in window) {
  requestIdleCallback(_bannerGo, { timeout: 1500 });
} else {
  setTimeout(_bannerGo, 600);
}
["pointerdown","touchstart","scroll","keydown"].forEach(ev =>
  addEventListener(ev, _bannerGo, { once: true, passive: true }));
