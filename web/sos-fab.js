/* Servia floating SOS button. Injected on every public page via the
 * force-mobile middleware so the user can summon recovery from anywhere
 * on the site in one tap. v1.24.2.
 *
 * Skips: admin / vendor / portal-vendor / pay flows (would clutter the
 * staff UI), and /sos.html itself (already a panic page).
 */
(function(){
  try {
    var p = location.pathname;
    if (/^\/(admin|vendor|portal-vendor|pay|sos\.html)/.test(p)) return;
    if (document.getElementById('servia-sos-fab')) return;

    var css = "" +
      "#servia-sos-fab{position:fixed;right:14px;bottom:80px;z-index:9999;" +
        "background:#DC2626;color:#fff;border-radius:999px;padding:11px 16px 11px 13px;" +
        "font:700 13px/1 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;" +
        "text-decoration:none;display:flex;align-items:center;gap:7px;" +
        "box-shadow:0 8px 24px rgba(220,38,38,.45),0 2px 6px rgba(0,0,0,.3);" +
        "border:2px solid rgba(255,255,255,.25);transition:transform .15s ease}" +
      "#servia-sos-fab:hover{transform:translateY(-2px);background:#B91C1C}" +
      "#servia-sos-fab:active{transform:scale(.96)}" +
      "#servia-sos-fab .dot{width:9px;height:9px;border-radius:50%;background:#FCD34D;" +
        "box-shadow:0 0 0 0 #FCD34D;animation:servia-sos-pulse 1.4s ease-out infinite}" +
      "@keyframes servia-sos-pulse{0%{box-shadow:0 0 0 0 rgba(252,211,77,.7)}" +
        "100%{box-shadow:0 0 0 12px rgba(252,211,77,0)}}" +
      "@media(max-width:480px){#servia-sos-fab{right:12px;bottom:74px;padding:10px 14px;font-size:12px}}";

    var st = document.createElement('style');
    st.id = 'servia-sos-fab-style';
    st.textContent = css;
    document.head.appendChild(st);

    function mount(){
      if (document.getElementById('servia-sos-fab')) return;
      var a = document.createElement('a');
      a.id = 'servia-sos-fab';
      a.href = '/sos.html';
      a.setAttribute('aria-label','Any problem? Servia it — one-tap dispatch');
      // v1.24.8 — brand-building copy. "Servia it" is the new everyday verb
      // (like "Google it"). The 🆘 icon stays so people still associate it
      // with SOS / emergency, but the word changes the conversation.
      // v1.24.9 — show BOTH "SOS" and the new verb "Servia it" so customers
      // learn the brand verb while still recognising the universal SOS cue.
      a.innerHTML = '<span class="dot" aria-hidden="true"></span>🆘 SOS · Servia it';
      a.title = 'SOS / "Servia it" — any problem, one-tap dispatch · GPS auto-sent · vendor in seconds';
      document.body.appendChild(a);
    }
    if (document.body) mount();
    else document.addEventListener('DOMContentLoaded', mount);
  } catch(e) {}
})();
