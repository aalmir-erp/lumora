/* Servia share toolbar — drop <div data-share="page-key"></div> anywhere.
 * Renders WhatsApp, Twitter/X, Facebook, Instagram, Telegram, Email, Copy
 * buttons + sponsorable referral hint. Native Web Share API on supported devices.
 */
(function () {
  function build(host) {
    const url = host.dataset.shareUrl || location.href;
    const title = host.dataset.shareTitle || document.title;
    const txt = host.dataset.shareText ||
      "Servia — UAE's smart home & business services in 60 seconds. Get AED 50 off your first booking with my link:";
    const utm = (host.dataset.shareUtm || "share") + "_" + (host.dataset.shareKey || "");
    const u = encodeURIComponent(url + (url.includes("?") ? "&" : "?") + "utm_source=" + utm);
    const t = encodeURIComponent(txt);
    const tt = encodeURIComponent(title);

    const targets = [
      { lbl: "WhatsApp", emoji: "💬", href: `https://wa.me/?text=${t}%20${u}`, color: "#25D366" },
      { lbl: "X",        emoji: "𝕏",  href: `https://twitter.com/intent/tweet?text=${t}&url=${u}`, color: "#000" },
      { lbl: "Facebook", emoji: "f",  href: `https://www.facebook.com/sharer/sharer.php?u=${u}`, color: "#1877F2" },
      { lbl: "Telegram", emoji: "✈", href: `https://t.me/share/url?url=${u}&text=${t}`, color: "#0088CC" },
      { lbl: "LinkedIn", emoji: "in", href: `https://www.linkedin.com/sharing/share-offsite/?url=${u}`, color: "#0A66C2" },
      { lbl: "Email",    emoji: "✉", href: `mailto:?subject=${tt}&body=${t}%20${u}`, color: "#475569" },
    ];

    host.innerHTML = `
      <div class="servia-share-bar" style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;font-size:13px;font-weight:600">
        <span style="color:var(--muted);margin-inline-end:4px">Share:</span>
        ${targets.map(o => `
          <a href="${o.href}" target="_blank" rel="noopener" aria-label="Share on ${o.lbl}"
             style="width:38px;height:38px;border-radius:50%;background:${o.color};color:#fff;
             display:inline-flex;align-items:center;justify-content:center;font-weight:800;
             text-decoration:none;font-size:16px;transition:transform .15s"
             onmouseover="this.style.transform='scale(1.12)'" onmouseout="this.style.transform='scale(1)'">${o.emoji}</a>
        `).join("")}
        <button type="button" class="servia-copy-btn" aria-label="Copy link"
          style="width:38px;height:38px;border-radius:50%;border:1px solid var(--border);background:var(--surface);
          color:var(--text);cursor:pointer;font-size:14px">🔗</button>
        ${navigator.share ? `<button type="button" class="servia-native-share" aria-label="More"
          style="width:38px;height:38px;border-radius:50%;border:1px solid var(--border);background:var(--surface);
          color:var(--text);cursor:pointer;font-size:14px">⋯</button>` : ''}
      </div>
      <div class="servia-share-hint" style="margin-top:8px;font-size:12px;color:var(--muted)">
        🎁 Share Servia + post a 5★ Google review to <b style="color:var(--primary-dark)">climb your Ambassador tier</b> (more % off every booking).
        <a href="/share-rewards.html" style="color:var(--primary-dark);text-decoration:underline">How →</a>
      </div>
    `;

    host.querySelector(".servia-copy-btn").onclick = async () => {
      try {
        await navigator.clipboard.writeText(decodeURIComponent(u));
        host.querySelector(".servia-copy-btn").textContent = "✓";
        setTimeout(() => host.querySelector(".servia-copy-btn").textContent = "🔗", 1800);
      } catch { alert("Copy failed — please long-press the URL bar."); }
    };
    const native = host.querySelector(".servia-native-share");
    if (native) native.onclick = async () => {
      try { await navigator.share({ title, text: txt, url }); } catch {}
    };
  }
  document.querySelectorAll("[data-share]").forEach(build);
  // Also expose for dynamic insertion
  window.serviaBuildShare = build;
})();
