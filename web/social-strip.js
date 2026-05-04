/* Servia social-follow strip — auto-injects above the footer when admin has
 * configured at least one social profile URL via /api/admin/launch/social.
 * Loads via /api/site/social, deferred to idle so it doesn't hurt PSI.
 */
(function () {
  if (window.__servia_social_strip) return; window.__servia_social_strip = true;
  function init() {
    fetch("/api/site/social").then(r => r.ok ? r.json() : null).then(j => {
      if (!j || !j.profiles || !j.profiles.length) return;
      // Find a footer to insert before, else append to body
      const footer = document.querySelector("footer");
      const wrap = document.createElement("section");
      wrap.id = "servia-social-strip";
      wrap.style.cssText =
        "background:linear-gradient(135deg,#0F766E,#0D9488);color:#fff;" +
        "padding:24px 16px;text-align:center;border-top:3px solid #FCD34D";
      const links = j.profiles.map(p =>
        '<a href="' + p.url + '" target="_blank" rel="noopener" style="' +
        'background:rgba(255,255,255,.18);color:#fff;padding:9px 16px;' +
        'border-radius:999px;font-weight:700;font-size:13.5px;text-decoration:none;' +
        'display:inline-flex;gap:6px;align-items:center;transition:.15s;' +
        'border:1px solid rgba(255,255,255,.22)" ' +
        'onmouseover="this.style.background=\'#FCD34D\';this.style.color=\'#7C2D12\'" ' +
        'onmouseout="this.style.background=\'rgba(255,255,255,.18)\';this.style.color=\'#fff\'">' +
        '<span style="font-size:16px">' + p.emoji + '</span>' + p.label + '</a>'
      ).join(" ");
      wrap.innerHTML =
        '<div style="max-width:760px;margin:0 auto">' +
          '<p style="margin:0 0 4px;font-size:11px;font-weight:800;letter-spacing:.1em;opacity:.85;text-transform:uppercase">Follow Servia</p>' +
          '<h3 style="margin:0 0 14px;font-size:22px;letter-spacing:-.02em">Stay in the loop on UAE service deals</h3>' +
          '<div style="display:flex;flex-wrap:wrap;gap:8px;justify-content:center">' + links + '</div>' +
        '</div>';
      if (footer && footer.parentNode) footer.parentNode.insertBefore(wrap, footer);
      else document.body.appendChild(wrap);
    }).catch(() => {});
  }
  if ("requestIdleCallback" in window) requestIdleCallback(init, {timeout: 4000});
  else setTimeout(init, 2000);
})();
