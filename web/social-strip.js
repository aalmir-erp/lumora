/* Servia social-follow strip — auto-injects above the footer when admin has
 * configured at least one social profile URL via /api/admin/launch/social.
 * Loads via /api/site/social, deferred to idle so it doesn't hurt PSI.
 */
(function () {
  if (window.__servia_social_strip) return; window.__servia_social_strip = true;
  function init() {
    fetch("/api/site/social").then(r => r.ok ? r.json() : null).then(j => {
      const slot = document.getElementById("servia-social-strip-slot");
      if (!j || !j.profiles || !j.profiles.length) {
        // v1.23.7 — DO NOT hide the slot when no admin profiles exist.
        // Earlier versions did slot.style.display='none' which nuked the
        // 8 hardcoded fallback buttons (WhatsApp / Instagram / FB / X /
        // TikTok / YouTube / LinkedIn / Refer 20%) baked into the HTML.
        // Now we just return — fallback content stays visible.
        return;
      }
      // Reuse pre-reserved #servia-social-strip-slot placeholder if present
      // (kills CLS by claiming layout space ahead of time). Else create new.
      const footer = document.querySelector("footer");
      const wrap = slot || document.createElement("section");
      wrap.id = "servia-social-strip";
      wrap.style.cssText =
        "background:linear-gradient(135deg,#0F766E,#0D9488);color:#fff;" +
        "padding:24px 16px;text-align:center;border-top:3px solid #FCD34D;" +
        "min-height:160px;contain:layout";
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
      // If we used the slot, it's already in the DOM — skip insert
      if (!slot) {
        if (footer && footer.parentNode) footer.parentNode.insertBefore(wrap, footer);
        else document.body.appendChild(wrap);
      }
    }).catch(() => {});
  }
  if ("requestIdleCallback" in window) requestIdleCallback(init, {timeout: 4000});
  else setTimeout(init, 2000);
})();
