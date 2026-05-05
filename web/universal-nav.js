/* Servia universal nav + footer.
 *
 * Replaces the per-page <nav class="nav"> and <footer> with a canonical
 * structure on every page so the header / footer is identical site-wide.
 *
 * Loaded EARLY in the lazy-load chain so it runs before search-widget.js
 * injects its FABs into .nav-cta — that keeps insertion order predictable
 * (GPT/Install icons end up next to Book, after the icons we drop here).
 *
 * The nav includes a search-icon button (🔍) that opens the same Cmd+K
 * palette the floating button opens — exposed by search-widget.js as
 * window.serviaOpenSearch(). If search-widget hasn't loaded yet, we fall
 * back to /search.html.
 */
(function () {
  if (window.__servia_universal_nav) return;
  window.__servia_universal_nav = true;

  const LANGS = [
    {v:"en",l:"🇬🇧 EN"},{v:"ar",l:"🇦🇪 AR"},{v:"ur",l:"🇵🇰 UR"},
    {v:"hi",l:"🇮🇳 HI"},{v:"bn",l:"🇧🇩 BN"},{v:"ta",l:"TA"},{v:"ml",l:"ML"},
    {v:"tl",l:"🇵🇭 TL"},{v:"ps",l:"🇦🇫 PS"},{v:"ne",l:"🇳🇵 NE"},
    {v:"ru",l:"🇷🇺 RU"},{v:"fa",l:"🇮🇷 FA"},{v:"fr",l:"🇫🇷 FR"},
    {v:"zh",l:"🇨🇳 ZH"},{v:"es",l:"🇪🇸 ES"},
  ];

  // Common CSS shared by every page so the universal nav doesn't depend on
  // each page's stylesheet defining .btn-icon / .lang-dropdown.
  const css = document.createElement("style");
  css.id = "unav-css";
  css.textContent = `
    .nav .nav-inner { max-width:1180px; margin:0 auto; padding:14px 20px;
      display:flex; align-items:center; gap:14px; }
    .nav .nav-links { display:flex; gap:18px; margin-inline-start:auto; }
    .nav .nav-links a { color:var(--text,#0F172A); font-weight:600; font-size:14px;
      text-decoration:none; }
    .nav .nav-links a.active { color:var(--primary-dark,#0F766E); }
    .nav .nav-cta { display:flex; gap:8px; align-items:center; }
    .nav .btn-icon { width:38px; height:38px; min-height:38px; padding:0;
      font-size:14px; border-radius:50%; border:1px solid var(--border,#E2E8F0);
      background:#fff; color:var(--text,#0F172A); cursor:pointer; display:inline-flex;
      align-items:center; justify-content:center; line-height:1; text-decoration:none;
      flex-shrink:0; }
    .nav .btn-icon:hover { background:#F0FDFA; border-color:#0F766E; color:#0F766E; }
    .nav .lang-dropdown { height:38px; padding:0 22px 0 10px; border-radius:999px;
      border:1px solid var(--border,#E2E8F0); background:#fff; font-size:12px;
      font-weight:700; cursor:pointer; color:var(--text,#0F172A); min-width:60px;
      text-align:center; appearance:none; -webkit-appearance:none;
      background-image:url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 10 10"><path d="M2 4l3 3 3-3" stroke="%2364748B" stroke-width="1.5" fill="none"/></svg>');
      background-repeat:no-repeat; background-position:right 8px center; }
    .nav .lang-dropdown:hover { border-color:#0F766E; color:#0F766E; }
    @media (max-width:720px) {
      .nav .nav-links { display:none; }
      .nav .btn-icon { width:34px; height:34px; font-size:13px; }
      .nav .lang-dropdown { min-width:48px; padding:0 22px 0 6px; font-size:11px; }
      .nav .nav-inner { gap:8px; padding:10px 12px; }
      .nav small#lumora-version { display:none; }
    }
    /* Footer: identical structure on every page. */
    footer { background:#0F172A; color:#fff; padding:48px 24px; min-height:240px; }
    footer .container { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
      gap:32px; max-width:1180px; margin:0 auto; }
    footer h3 { color:#fff; font-size:13px; margin:0 0 12px; font-weight:700; }
    footer a { color:#CBD5E1; font-size:13px; text-decoration:none; line-height:2; }
    footer a:hover { color:#fff; }
    footer .ftr-tag { margin:12px 0 0; font-size:13px; opacity:.85; }
    footer .ftr-pay { display:flex; gap:8px; margin-top:14px; flex-wrap:wrap; }
    footer .ftr-pay span { background:rgba(255,255,255,.12); border-radius:6px;
      padding:4px 8px; font-size:11px; font-weight:700; color:#CBD5E1; }
  `;
  document.head.appendChild(css);

  function activeIfMatch(href, path){
    if (path === "/" && href === "/") return " class=\"active\"";
    if (href !== "/" && path.indexOf(href.split("?")[0]) === 0) return " class=\"active\"";
    return "";
  }

  function buildNav() {
    const path = location.pathname;
    return `<div class="nav-inner">
      <a href="/" aria-label="Servia home"><img src="/logo.svg" width="124" height="40" alt="Servia" decoding="async"></a>
      <small id="lumora-version" style="font-size:10px;color:var(--muted,#64748B);margin-inline-start:6px;font-weight:600;background:var(--bg,#FAFAFA);padding:2px 6px;border-radius:6px">v?</small>
      <div class="nav-links">
        <a href="/services.html"${activeIfMatch("/services.html", path)} data-i18n="nav_services">Services</a>
        <a href="/coverage.html"${activeIfMatch("/coverage.html", path)} data-i18n="nav_coverage">Coverage</a>
        <a href="/blog">Blog</a>
        <a href="/me.html"${activeIfMatch("/me.html", path)} data-i18n="nav_my_account">My account</a>
      </div>
      <div class="nav-cta">
        <button type="button" class="btn btn-icon" id="unav-search" title="Search Servia (Ctrl/Cmd+K)" aria-label="Open search">🔍</button>
        <button type="button" class="btn btn-icon" onclick="window.lumoraOpenSettings&&lumoraOpenSettings()" title="Themes &amp; fonts" aria-label="Theme settings">🎨</button>
        <select class="lang-dropdown notranslate" translate="no" aria-label="Language" onchange="window.lumoraSetLang&&lumoraSetLang(this.value)">
          ${LANGS.map(o => `<option value="${o.v}">${o.l}</option>`).join("")}
        </select>
        <a class="btn btn-icon" href="/login.html" title="Sign in" aria-label="Sign in" data-i18n-title="nav_signin">👤</a>
        <a class="btn btn-primary" href="/book.html" data-i18n="nav_book_now">Book now</a>
      </div>
    </div>`;
  }

  function buildFooter() {
    return `<div class="container">
      <div>
        <img src="/logo.svg" height="36" alt="Servia" style="filter:brightness(0) invert(1)" decoding="async">
        <p class="ftr-tag" data-i18n="footer_tagline">Built for UAE homes &amp; businesses · 4.9★ from 2,400+ families.</p>
        <div class="ftr-pay" aria-label="Payment methods">
          <span>VISA</span><span>MC</span><span>Apple Pay</span><span>COD</span>
        </div>
      </div>
      <div><h3>Customers</h3>
        <a href="/services.html">All services</a><br>
        <a href="/book.html">Book online</a><br>
        <a href="/coverage.html">Coverage map</a><br>
        <a href="/me.html">My account</a><br>
        <a href="/faq.html">FAQ</a>
      </div>
      <div><h3>Service areas</h3>
        <a href="/area.html?city=dubai">Dubai</a><br>
        <a href="/area.html?city=sharjah">Sharjah</a><br>
        <a href="/area.html?city=abu-dhabi">Abu Dhabi</a><br>
        <a href="/area.html?city=ajman">Ajman</a><br>
        <a href="/area.html?city=ras-al-khaimah">RAK</a>
      </div>
      <div><h3>Apps &amp; AI</h3>
        <a href="/install.html">Install app</a><br>
        <a href="/smart-speakers.html">Voice booking</a><br>
        <a href="https://chatgpt.com/g/g-69f9f43427c88191bca61c0fe0977b53-servia-uae-helper" target="_blank" rel="noopener">ChatGPT GPT</a><br>
        <a href="/videos.html">Videos</a><br>
        <a href="/blog">Blog</a>
      </div>
      <div><h3>Legal</h3>
        <a href="/terms.html">Terms</a><br>
        <a href="/privacy.html">Privacy</a><br>
        <a href="/refund.html">Refund policy</a>
      </div>
      <div><h3>Contact</h3>
        <a href="/contact.html">Contact us</a><br>
        <a href="mailto:support@servia.ae">support@servia.ae</a><br>
        <span style="color:#94A3B8;font-size:12px;line-height:1.6">Replies in minutes,<br>7 days a week.</span>
      </div>
    </div>`;
  }

  function replaceNav() {
    const nav = document.querySelector("nav.nav");
    if (!nav) return;
    if (nav.dataset.universal === "1") return;
    nav.innerHTML = buildNav();
    nav.dataset.universal = "1";
    // Sync language dropdown to current value
    try {
      const cur = localStorage.getItem("lumora.lang") || "en";
      const sel = nav.querySelector("select.lang-dropdown");
      if (sel) sel.value = cur;
    } catch(_) {}
    // Wire the search-icon button to the modal palette.
    const btn = nav.querySelector("#unav-search");
    if (btn) {
      btn.addEventListener("click", () => {
        if (typeof window.serviaOpenSearch === "function") {
          window.serviaOpenSearch();
        } else {
          // Fallback if search-widget hasn't loaded yet — go to /search.html.
          location.href = "/search.html";
        }
      });
    }
  }

  function replaceFooter() {
    const ftr = document.querySelector("footer");
    if (!ftr) return;
    if (ftr.dataset.universal === "1") return;
    ftr.innerHTML = buildFooter();
    ftr.dataset.universal = "1";
  }

  function run() {
    replaceNav();
    replaceFooter();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", run);
  } else {
    run();
  }
  // In case other scripts swap the nav/footer after us (or if the page
  // initially has no nav and creates one later) — re-run once on load.
  window.addEventListener("load", run, { once:true });
})();
