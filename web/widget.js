/* Servia chat widget — floating concierge bot.
 *
 * Single-instance via `window.__servia_widget_loaded` guard so accidental
 * double-include never produces two launchers / two send buttons.
 *
 * Capabilities:
 *  - Text chat (Claude-powered) with quick replies + tool actions
 *  - Voice input (Web Speech API) with 15-language map → live transcript
 *  - Photo attachment with client-side compression (max 1280px, JPEG q=0.65)
 *  - Live agent handoff polling
 */
(function () {
  if (window.__servia_widget_loaded) return;
  window.__servia_widget_loaded = true;

  const script = document.currentScript || document.querySelector("script[data-api-base]");
  const API_BASE = (script && script.dataset.apiBase) ||
                   (window.LUMORA_API_BASE || window.location.origin);
  const SESSION_KEY = "lumora.chat.sid";
  const SINCE_KEY = "lumora.chat.since";
  const STARTED_KEY = "lumora.chat.started";
  const QR_FALLBACK = [
    "How much for deep cleaning a 2-bedroom?",
    "Do you cover Sharjah?",
    "What's available tomorrow?",
    "Talk to a human",
  ];

  // Web Speech API language code map — covers all supported i18n languages.
  const SR_LANG_MAP = {
    en: "en-US", ar: "ar-AE", ur: "ur-PK", hi: "hi-IN", bn: "bn-BD",
    ta: "ta-IN", ml: "ml-IN", tl: "fil-PH", ps: "ps-AF", ne: "ne-NP",
    ru: "ru-RU", fa: "fa-IR", fr: "fr-FR", zh: "zh-CN", es: "es-ES",
  };

  // Persistent action chips that stay above messages forever (not hidden after first reply)
  const QUICK_ACTIONS = [
    { icon: "🛠", label: "Book service", send: "I want to book a service" },
    { icon: "💰", label: "Get quote", send: "Get me a quick price quote" },
    { icon: "📋", label: "My bookings", send: "Show me my bookings" },
    { icon: "🚐", label: "Track pro", send: "Where is my pro right now?" },
    { icon: "📍", label: "Areas covered", send: "Which areas do you cover?" },
    { icon: "💎", label: "Rewards", send: "How do I earn ambassador rewards?" },
    { icon: "🔁", label: "Repeat last", send: "Repeat my last booking" },
    { icon: "🎬", label: "Submit video", send: "I want to submit a video for creator points" },
    { icon: "👤", label: "Talk to human", send: "Talk to a human" },
  ];

  // Eye-catching launcher: brand mascot avatar inside a pulsing ring with a
  // periodic "Need help?" tooltip that nudges the user.
  const launcher = el("button", { class: "us-launcher", "aria-label": "Open chat with Servia concierge" });
  launcher.innerHTML =
    '<img src="/avatar.svg" width="38" height="38" alt="" ' +
    'style="display:block;margin:auto;border-radius:50%;background:rgba(255,255,255,.16)">' +
    '<span class="us-launcher-pulse" aria-hidden="true"></span>' +
    '<span class="us-launcher-bubble" aria-hidden="true">💬</span>';
  // Floating tooltip — rotates messages, gently re-appears every ~25s
  const tip = el("div", { class: "us-launcher-tip", "aria-hidden": "true" }, "");
  document.body.appendChild(tip);
  const panel = el("div", { class: "us-panel", role: "dialog" },
    el("div", { class: "us-header" },
      el("img", { src: "/avatar.svg", width: "36", height: "36",
        style: "border-radius:50%;background:rgba(255,255,255,.18)" }),
      el("div", { style: "flex:1" },
        el("h3", {}, "Servia"),
        el("p", { class: "us-mode-line" }, "Concierge · 24×7 · 15 languages"),
        el("p", { class: "us-version", style: "font-size:10px;opacity:.55;margin-top:1px;letter-spacing:.05em" }, "v—")),
      // v1.24.56 — header controls: download / new chat / minimize / maximize / close
      el("button", { class: "us-newchat", "aria-label": "Start new chat", title: "Start new chat" }, "✨"),
      el("button", { class: "us-download", "aria-label": "Download transcript", title: "Download transcript" }, "⤓"),
      el("button", { class: "us-resize", "aria-label": "Maximize / restore", title: "Maximize / restore" }, "⛶"),
      el("button", { class: "us-min", "aria-label": "Minimize", title: "Minimize" }, "—"),
      el("button", { class: "us-close", "aria-label": "Close", title: "Close" }, "×")),
    // v1.24.55 — Chat / History tabs
    el("div", { class: "us-tabs" },
      el("button", { class: "us-tab active", "data-tab": "chat" }, "💬 Chat"),
      el("button", { class: "us-tab", "data-tab": "history" }, "📜 History")),
    el("div", { class: "us-actions-bar" }),
    el("div", { class: "us-body" }),
    // v1.24.55 — History panel (hidden until tab tapped)
    el("div", { class: "us-history", style: "display:none;flex:1;overflow-y:auto;padding:14px;background:#FAFBFD" },
      el("div", { class: "us-hist-form", style: "background:#fff;border:1px solid #E2E8F0;border-radius:10px;padding:12px;margin-bottom:10px" },
        el("p", { style: "font-size:12.5px;color:#64748B;margin-bottom:10px;line-height:1.45" },
          "Enter the phone you've used with us before. We'll show your previous bookings, invoices, payments, and chats."),
        el("input", { type: "tel", class: "us-hist-phone", placeholder: "Mobile (e.g. 0559396459)",
          autocomplete: "tel",
          style: "width:100%;padding:9px 11px;border:1px solid #CBD5E1;border-radius:8px;font:inherit;margin-bottom:6px" }),
        el("input", { type: "email", class: "us-hist-email", placeholder: "Email (optional)",
          autocomplete: "email",
          style: "width:100%;padding:9px 11px;border:1px solid #CBD5E1;border-radius:8px;font:inherit;margin-bottom:8px" }),
        el("button", { class: "us-hist-go",
          style: "width:100%;padding:10px;background:#0D9488;color:#fff;border:none;border-radius:8px;font-weight:600;cursor:pointer" },
          "🔍 Find my history")),
      el("div", { class: "us-hist-results" })),
    el("div", { class: "us-quickreplies" }),
    el("div", { class: "us-attach-preview", style: "display:none" }),
    el("form", { class: "us-input", autocomplete: "off" },
      el("button", { type: "button", class: "us-attach", "aria-label": "Attach photo", title: "Attach photo" }, "📎"),
      el("button", { type: "button", class: "us-mic", "aria-label": "Voice input", title: "Voice input" }, "🎤"),
      // v1.24.9 — location share. Tap → popup with GPS / map pin / address
      // fields. If the chat context implies a service that needs FROM and TO
      // (chauffeur, furniture move, recovery tow), the popup shows BOTH
      // location pickers stacked.
      el("button", { type: "button", class: "us-loc", "aria-label": "Share location", title: "Share live location or pin on map" }, "📍"),
      el("input", { type: "text", placeholder: "Type, 🎤 voice, 📎 photo, 📍 location…", maxlength: "1000" }),
      el("button", { type: "submit", class: "us-send", "aria-label": "Send", title: "Send" }, "↑")),
    el("div", { class: "us-mode" }, ""));
  // Hidden file input for image attachment
  const fileInput = el("input", { type: "file", accept: "image/*",
    style: "display:none", capture: "environment" });
  panel.appendChild(fileInput);

  document.body.appendChild(launcher);
  document.body.appendChild(panel);

  // Lift launcher above sticky bottom bars (replaces heavy CSS :has() rule).
  if (document.querySelector(".sticky-cta, .mobile-nav")) {
    document.body.classList.add("us-lift-bar");
  }

  // Periodic tooltip — gentle "Need a hand?" prompts. Only shows when chat
  // is closed and the user hasn't dismissed via interaction.
  const TIPS = [
    "👋 Need a hand? Ask me anything",
    "💰 Want a quick price?",
    "📲 Book a service in 60s",
    "🚐 Track your pro live",
    "🎬 Earn creator points",
  ];
  let tipIdx = 0, tipTimer = null;
  function showTip() {
    if (panel.classList.contains("open")) return;
    tip.textContent = TIPS[tipIdx % TIPS.length];
    tip.classList.add("show");
    tipIdx++;
    setTimeout(() => tip.classList.remove("show"), 4500);
  }
  // First tip after the browser has been idle (PSI-friendly: never blocks
  // first paint or interaction). Falls back to a longer setTimeout if
  // requestIdleCallback is unavailable.
  function _scheduleTips() {
    showTip();
    tipTimer = setInterval(showTip, 35000);
  }
  if ("requestIdleCallback" in window) {
    requestIdleCallback(() => setTimeout(_scheduleTips, 8000), { timeout: 12000 });
  } else {
    setTimeout(_scheduleTips, 12000);
  }
  // Hide tooltip permanently if user clicks/dismisses
  tip.addEventListener("click", () => { tip.classList.remove("show"); if (tipTimer) clearInterval(tipTimer); launcher.click(); });
  launcher.addEventListener("click", () => { tip.classList.remove("show"); if (tipTimer) clearInterval(tipTimer); });

  const body = panel.querySelector(".us-body");
  const actionsBar = panel.querySelector(".us-actions-bar");
  const quickWrap = panel.querySelector(".us-quickreplies");
  const form = panel.querySelector(".us-input");
  const input = form.querySelector('input[type="text"]');
  const sendBtn = form.querySelector(".us-send");
  const attachBtn = form.querySelector(".us-attach");
  const micBtn = form.querySelector(".us-mic");
  const locBtn = form.querySelector(".us-loc");
  const previewWrap = panel.querySelector(".us-attach-preview");
  const modeBadge = panel.querySelector(".us-mode");
  const subtitle = panel.querySelector(".us-mode-line");
  // v1.24.58 — populate version label in chat header from /api/health.
  // Fires once on widget mount (idle-deferred so it doesn't block paint).
  (function _showVersion() {
    function paint(v) {
      const el = panel.querySelector(".us-version");
      if (el) el.textContent = "v" + v;
    }
    if (window.LUMORA_VERSION) { paint(window.LUMORA_VERSION); return; }
    function go() {
      fetch(API_BASE + "/api/health").then(r => r.ok && r.json()).then(j => {
        if (j && j.version) { window.LUMORA_VERSION = j.version; paint(j.version); }
      }).catch(()=>{});
    }
    if (window.requestIdleCallback) requestIdleCallback(go, {timeout: 4000});
    else setTimeout(go, 1500);
  })();

  // Build persistent action toolbar
  QUICK_ACTIONS.forEach(a => {
    const b = el("button", { type: "button", title: a.label },
      el("span", { style: "font-size:14px" }, a.icon),
      el("span", {}, a.label));
    b.onclick = () => {
      input.value = a.send;
      form.requestSubmit();
    };
    actionsBar.appendChild(b);
  });

  let sessionId = localStorage.getItem(SESSION_KEY);
  let since = +localStorage.getItem(SINCE_KEY) || 0;
  let busy = false;
  let pollT = null;
  let agentMode = false;
  let chatStarted = !!localStorage.getItem(STARTED_KEY) || !!sessionId;
  let userMsgCount = chatStarted ? 1 : 0;
  let pendingAttachment = null; // { url, name, w, h, sizeKb }

  function applyI18n() {
    const t = (k, d) => (window.lumoraT ? window.lumoraT(k, d) : d);
    input.placeholder = t("bot_placeholder", "Type message, send a voice note 🎤 or photo 📎…");
    // Send is an icon now — never set to text
    if (chatStarted || userMsgCount > 0) {
      quickWrap.innerHTML = "";
      quickWrap.style.display = "none";
      return;
    }
    quickWrap.innerHTML = "";
    quickWrap.style.display = "";
    QR_FALLBACK.forEach((q) => {
      const b = el("button", { type: "button" }, q);
      b.onclick = () => { input.value = q; form.requestSubmit(); };
      quickWrap.appendChild(b);
    });
  }
  window.addEventListener("lumora:lang", applyI18n);
  applyI18n();

  launcher.onclick = () => {
    panel.classList.add("open");
    // First-time? Show greeting. Returning user with a saved session?
    // Restore the full conversation history so the chat doesn't feel
    // like it's "restarting" every time they reopen the panel or change
    // pages. We fetch /api/chat/poll with since_id=0 to grab everything
    // for this session_id.
    if (!body.children.length) {
      if (sessionId) {
        restoreHistory().then(restored => {
          if (!restored) greet();
        });
      } else {
        greet();
      }
    }
    setTimeout(() => input.focus(), 150);
    startPolling();
    try { localStorage.setItem("servia.chat.open.v2", "1"); } catch(_) {}
  };
  panel.querySelector(".us-close").onclick = () => {
    panel.classList.remove("open");
    panel.classList.remove("us-min-state","us-max-state");
    try { localStorage.setItem("servia.chat.open.v2", "0"); } catch(_) {}
    try { localStorage.removeItem("servia.chat.size"); } catch(_) {}
  };

  // v1.24.82 — Minimize now CLOSES the panel (back to launcher icon).
  // Previous behaviour kept a 54px header bar across the bottom which
  // hid page content on every page (user reported it as a "horizontal
  // long useless bar"). Conversation persists; clicking the launcher
  // brings it back exactly as it was.
  panel.querySelector(".us-min").onclick = () => {
    panel.style.display = "none";
    panel.classList.remove("us-max-state");
    if (typeof launcher !== "undefined" && launcher) launcher.style.display = "";
    try { localStorage.setItem("servia.chat.size", "min"); } catch(_) {}
  };
  panel.querySelector(".us-resize").onclick = () => {
    panel.classList.toggle("us-max-state");
    panel.classList.remove("us-min-state");
    try { localStorage.setItem("servia.chat.size",
      panel.classList.contains("us-max-state") ? "max" : "normal"); } catch(_) {}
  };
  panel.querySelector(".us-newchat").onclick = () => {
    if (!confirm("Start a new chat? Current conversation stays in our records but the widget resets.")) return;
    sessionId = null; since = 0; chatStarted = false;
    localStorage.removeItem(SESSION_KEY);
    localStorage.removeItem(SINCE_KEY);
    localStorage.removeItem(STARTED_KEY);
    body.innerHTML = "";
    greet();
  };
  panel.querySelector(".us-download").onclick = async () => {
    if (!sessionId) { alert("Nothing to download yet — say hi first."); return; }
    try {
      const r = await fetch(API_BASE + "/api/chat/poll?session_id=" + encodeURIComponent(sessionId) + "&since_id=0");
      const j = await r.json();
      const lines = (j.messages || []).map(m => {
        const ts = (m.created_at || "").slice(0,19).replace("T"," ");
        const who = m.role === "user" ? "You" : (m.agent_handled ? "Agent" : "Servia");
        return `[${ts}] ${who}:\n${(m.content || "").trim()}\n`;
      }).join("\n");
      const header = `Servia chat transcript\nSession: ${sessionId}\nDownloaded: ${new Date().toISOString()}\n\n${"=".repeat(48)}\n\n`;
      const blob = new Blob([header + lines], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = `servia-chat-${sessionId}.txt`;
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 5000);
    } catch (e) { alert("Download failed: " + e.message); }
  };

  // v1.24.55 — Tab switching + History tab handlers
  function _switchTab(name) {
    panel.querySelectorAll(".us-tab").forEach(t =>
      t.classList.toggle("active", t.dataset.tab === name));
    body.style.display = name === "chat" ? "" : "none";
    actionsBar.style.display = name === "chat" ? "" : "none";
    quickWrap.style.display = name === "chat" ? "" : "none";
    form.style.display = name === "chat" ? "" : "none";
    panel.querySelector(".us-history").style.display = name === "history" ? "flex" : "none";
  }
  panel.querySelectorAll(".us-tab").forEach(b => b.onclick = () => _switchTab(b.dataset.tab));

  panel.querySelector(".us-hist-go").onclick = async () => {
    const phone = panel.querySelector(".us-hist-phone").value.trim();
    const email = panel.querySelector(".us-hist-email").value.trim();
    if (!phone && !email) { alert("Enter your mobile or email"); return; }
    const out = panel.querySelector(".us-hist-results");
    out.innerHTML = '<p style="text-align:center;color:#64748B;padding:18px">Looking up…</p>';
    try {
      const r = await fetch(API_BASE + "/api/me/history", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone, email }),
      });
      const j = await r.json();
      if (!j.ok) { out.innerHTML = '<p style="text-align:center;color:#DC2626">Lookup failed</p>'; return; }
      try { localStorage.setItem("servia.history.phone", phone); } catch(_) {}
      _renderHistory(out, j);
    } catch (e) {
      out.innerHTML = '<p style="text-align:center;color:#DC2626">Network error</p>';
    }
  };

  function _renderHistory(container, data) {
    const esc = s => String(s||"").replace(/[&<>"']/g,
      c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
    if ((data.total || 0) === 0) {
      container.innerHTML = '<p style="text-align:center;color:#64748B;padding:24px">No matches found for this phone / email.</p>';
      return;
    }
    const counts = data.counts || {};
    let html = `<p style="font-size:11.5px;color:#64748B;margin-bottom:10px;text-align:center">
      <b>${data.total}</b> records · ${counts.bookings||0} bookings · ${counts.quotes||0} quotes ·
      ${counts.invoices||0} invoices · ${counts.chats||0} chats</p>`;
    const statusColor = s => ({signed:"#0D9488", paid:"#10B981", dispatched:"#F59E0B",
      arrived:"#3B82F6", in_progress:"#8B5CF6", done:"#10B981",
      cancelled:"#94A3B8", pending:"#64748B"})[s] || "#64748B";
    if (data.quotes && data.quotes.length) {
      html += '<h4 style="margin:14px 0 6px;font-size:13px;color:#0D9488">📋 Quotes & orders</h4>';
      html += data.quotes.map(q => `
        <div style="background:#fff;border:1px solid #E2E8F0;border-radius:10px;padding:12px;margin:6px 0">
          <div style="display:flex;justify-content:space-between;align-items:start">
            <div><b>${esc(q.quote_id)}</b>
              <span style="display:inline-block;font-size:10px;padding:2px 6px;border-radius:3px;margin-left:6px;background:${statusColor(q.status)};color:#fff">${esc((q.status||'pending').toUpperCase())}</span>
              <div style="font-size:12px;color:#64748B;margin-top:2px">${q.target_date||''} ${q.time_slot||''} · ${(q.items||[]).length} services</div></div>
            <div style="text-align:right"><b style="color:#0D9488">AED ${q.total_aed||'—'}</b>
              ${q.paid_at ? '<div style="font-size:10px;color:#10B981">✓ PAID</div>' : ''}</div>
          </div>
          <div style="font-size:12px;color:#64748B;margin:6px 0">
            ${(q.items||[]).slice(0,4).map(i => '• ' + esc(i.label)).join('<br>')}</div>
          <div style="display:flex;gap:6px;margin-top:8px;flex-wrap:wrap">
            <a href="${q.view_url}" target="_blank" style="flex:1;padding:7px;background:#0D9488;color:#fff;text-align:center;border-radius:6px;font-size:12px;text-decoration:none">View</a>
            <a href="${q.invoice_url}" target="_blank" style="flex:1;padding:7px;background:#1E293B;color:#fff;text-align:center;border-radius:6px;font-size:12px;text-decoration:none">Invoice</a>
            <a href="${q.pdf_url}" target="_blank" style="flex:1;padding:7px;background:#F59E0B;color:#fff;text-align:center;border-radius:6px;font-size:12px;text-decoration:none">📄 PDF</a>
            ${!q.paid_at ? `<a href="${q.pay_url}" target="_blank" style="flex:1;padding:7px;background:#DC2626;color:#fff;text-align:center;border-radius:6px;font-size:12px;text-decoration:none">Pay</a>` : ''}
          </div></div>`).join("");
    }
    if (data.bookings && data.bookings.length) {
      html += '<h4 style="margin:14px 0 6px;font-size:13px;color:#0D9488">📅 Bookings</h4>';
      html += data.bookings.map(b => `<div style="background:#fff;border:1px solid #E2E8F0;border-radius:10px;padding:10px;margin:6px 0;font-size:12.5px">
        <b>${esc(b.service_id||'service')}</b> · ${b.target_date||''} ${b.time_slot||''}<br>
        <span style="font-size:11px;color:#64748B">${esc(b.address||'')}</span>
        <span style="float:right;background:#F1F5F9;padding:1px 6px;border-radius:3px;font-size:10px">${esc(b.status||'?')}</span></div>`).join("");
    }
    if (data.invoices && data.invoices.length) {
      html += '<h4 style="margin:14px 0 6px;font-size:13px;color:#0D9488">🧾 Invoices</h4>';
      html += data.invoices.map(i => `<div style="background:#fff;border:1px solid #E2E8F0;border-radius:10px;padding:10px;margin:6px 0;font-size:12.5px">
        <b>${esc(i.id)}</b>: AED ${i.amount_aed||'—'}
        <span style="float:right;background:${i.paid_at?'#D1FAE5':'#FEE2E2'};padding:1px 6px;border-radius:3px;font-size:10px;color:${i.paid_at?'#065F46':'#991B1B'}">${i.paid_at?'PAID':'PENDING'}</span></div>`).join("");
    }
    if (data.chats && data.chats.length) {
      html += '<h4 style="margin:14px 0 6px;font-size:13px;color:#0D9488">💬 Past chats</h4>';
      html += data.chats.map(c => `<div style="background:#fff;border:1px solid #E2E8F0;border-radius:10px;padding:10px;margin:6px 0;font-size:12px">
        <div style="color:#64748B;font-size:10px">${(c.first_at||'').slice(0,16)} · ${c.msg_count} msgs</div>
        <div style="margin-top:3px">${esc(c.preview||'(no preview)')}</div></div>`).join("");
    }
    container.innerHTML = html;
  }

  // v1.24.82 — restore widget size, but treat "min" as closed (panel
   // hidden, launcher shown). The 54px header strip was bad UX.
  setTimeout(() => {
    try {
      const sz = localStorage.getItem("servia.chat.size");
      if (sz === "min") {
        panel.style.display = "none";
        if (launcher) launcher.style.display = "";
      } else if (sz === "max") panel.classList.add("us-max-state");
    } catch (_) {}
  }, 200);

  // Reopen panel automatically on the next page if user had it open.
  // Stored in sessionStorage so it resets on tab close.
  setTimeout(() => {
    try {
      if (localStorage.getItem("servia.chat.open.v2") === "1" && !panel.classList.contains("open")) {
        launcher.click();
      }
    } catch(_) {}
  }, 800);

  // Pull conversation history for the current session from the server and
  // render every message in order. Returns true if any messages were
  // restored, false if nothing exists (caller should show greet).
  async function restoreHistory() {
    if (!sessionId) return false;
    try {
      const r = await fetch(API_BASE + "/api/chat/poll?session_id=" +
                            encodeURIComponent(sessionId) + "&since_id=0");
      if (!r.ok) return false;
      const d = await r.json();
      const msgs = d.messages || [];
      if (!msgs.length) return false;
      for (const m of msgs) {
        if (m.role === "user" || m.role === "assistant") {
          addMsg(m.role === "user" ? "user" : "bot", m.content || "",
                 null, !!m.agent_handled);
        }
        if (typeof m.id === "number" && m.id > since) {
          since = m.id;
          try { localStorage.setItem(SINCE_KEY, String(since)); } catch(_) {}
        }
      }
      // Mark chat as started so the quick-action chips stay collapsed
      chatStarted = true;
      userMsgCount = Math.max(userMsgCount, 1);
      try { localStorage.setItem(STARTED_KEY, "1"); } catch(_) {}
      // Hide first-time greeting card if it had been shown
      quickWrap.style.display = "none";
      return true;
    } catch (e) {
      console.warn("[chat] restoreHistory failed", e);
      return false;
    }
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (busy) return;
    const text = input.value.trim();
    if (!text && !pendingAttachment) return;
    input.value = "";
    if (pendingAttachment) {
      addMsgWithImage("user", text || "(photo attached)", pendingAttachment.url);
    } else {
      addMsg("user", text);
    }
    userMsgCount++;
    chatStarted = true;
    localStorage.setItem(STARTED_KEY, "1");
    hideQuickReplies();
    const att = pendingAttachment;
    pendingAttachment = null;
    previewWrap.style.display = "none";
    previewWrap.innerHTML = "";
    await send(text, att);
  });

  if (new URLSearchParams(location.search).get("chat") === "1") {
    setTimeout(() => launcher.click(), 400);
  }

  function hideQuickReplies() { quickWrap.style.display = "none"; }

  function greet() {
    const t = window.lumoraT ? window.lumoraT("bot_greeting") : null;
    addMsg("bot", t ||
      "Hi! I'm your Servia concierge. I can quote, book, track your pro, " +
      "show your bookings, handle reschedules, find areas, set up rewards, and " +
      "switch you to a human anytime. Type, voice note 🎤, or send a photo 📎 — " +
      "I speak 15 languages.");
    // intentionally do NOT set the mode badge — kept .us-mode hidden via CSS
  }

  async function send(text, attachment) {
    busy = true; sendBtn.disabled = true;
    const typing = showTyping();
    try {
      // Resolve current UI language. Order: lumoraLang() (set by app.js
      // when user picks from the dropdown) → localStorage 'lumora.lang'
      // (in case app.js hasn't initialized yet) → 'en' as last resort.
      let lang = "en";
      try {
        if (window.lumoraLang) lang = window.lumoraLang();
        else lang = localStorage.getItem("lumora.lang") || "en";
      } catch(_) {}
      const resp = await fetch(API_BASE + "/api/chat", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text || (attachment ? "(photo)" : ""),
          session_id: sessionId,
          language: lang,
          attachment_url: attachment ? attachment.url : null,
        }),
      });
      const data = await resp.json();
      typing.remove();
      if (!resp.ok) throw new Error(data.detail || "Request failed");
      sessionId = data.session_id;
      localStorage.setItem(SESSION_KEY, sessionId);
      if (data.agent_handled) {
        agentMode = true;
        subtitle.textContent = "🟢 connected to a live agent";
      }
      if (data.text) addMsg("bot", data.text, data.tool_calls);
    } catch (err) {
      typing.remove();
      addMsg("bot", "Sorry, I'm having trouble. Please try again, or contact us via /contact.html.");
      console.error(err);
    } finally {
      busy = false; sendBtn.disabled = false;
      input.focus();
    }
  }

  function startPolling() {
    if (pollT || !sessionId) return;
    pollT = setInterval(async () => {
      try {
        const r = await fetch(API_BASE + "/api/chat/poll?session_id=" +
                              encodeURIComponent(sessionId) + "&since_id=" + since);
        const d = await r.json();
        if (d.agent_handling) {
          agentMode = true;
          subtitle.textContent = "🟢 connected to a live agent";
        }
        for (const m of (d.messages || [])) {
          since = Math.max(since, m.id);
          localStorage.setItem(SINCE_KEY, String(since));
          if (m.role === "assistant" && m.agent_handled) {
            addMsg("bot", m.content, null, true);
          }
        }
      } catch {}
    }, 3500);
  }

  function extractActions(text, toolCalls) {
    const out = [];
    let cleanText = text || "";
    let pickerKind = null;   // v1.24.64 — 'date' | 'time' | null
    let quoteCardId = null;  // v1.24.78 — Q-XXXXXX to render as in-chat card
    cleanText = cleanText.replace(/\[\[\s*picker\s*:\s*(datetime|date|time|address)\s*\]\]/gi, (_, kind) => {
      pickerKind = kind.toLowerCase();
      return "";
    }).replace(/\[\[\s*quote_card\s*:\s*(Q-[A-Z0-9]+)\s*\]\]/gi, (_, qid) => {
      quoteCardId = qid;
      return "";
    }).replace(/\[\[\s*choices?\s*:\s*([^\]]+)\]\]/gi, (_, b) => {
      b.split(/\s*;\s*/).forEach(pair => {
        const m = pair.match(/^\s*(.+?)\s*=\s*(.+?)\s*$/);
        if (m) out.push({ label: m[1], send: m[2] });
        else if (pair.trim()) out.push({ label: pair.trim(), send: pair.trim() });
      });
      return "";
    }).replace(/\n{3,}/g, "\n\n").trim();
    if (pickerKind) out.__picker = pickerKind;
    if (quoteCardId) out.__quoteCard = quoteCardId;
    for (const tc of toolCalls || []) {
      const r = tc.result || {};
      if (tc.name === "list_slots" && r.ok && Array.isArray(r.slots) && !out.length) {
        for (const s of r.slots) out.push({ label: "🕒 " + s, send: `Book at ${s} on ${r.date}` });
      }
      if (tc.name === "create_booking" && r.ok && r.booking && !out.length) {
        out.push({ label: "📋 Track this booking", send: `Track ${r.booking.id}` });
        out.push({ label: "💳 View invoice", send: `Show me the invoice for ${r.booking.id}` });
      }
    }
    if (out.length === 0 && cleanText) {
      const seen = new Set();
      const reTime = /(?:^|\n)\s*(?:[•\-\*]\s+)?(?:🕒\s*)?(\d{1,2}:\d{2})(?:\s*(?:AM|PM|am|pm))?\b/g;
      let m;
      while ((m = reTime.exec(cleanText))) {
        if (seen.has(m[1])) continue; seen.add(m[1]);
        out.push({ label: "🕒 " + m[1], send: `Book at ${m[1]}` });
      }
      if (!out.length && /how\s+many\s+(bed)?room/i.test(cleanText)) {
        for (const n of [1, 2, 3, 4, 5]) out.push({ label: `${n} BR`, send: String(n) });
        out.push({ label: "Studio", send: "1" });
      }
      if (!out.length && /(which area|where|emirate)/i.test(cleanText)) {
        for (const a of ["Dubai", "Sharjah", "Ajman", "Abu Dhabi"]) out.push({ label: a, send: a });
      }
      if (!out.length && /\?\s*$/.test(cleanText) &&
          /\b(confirm|proceed|continue|right|correct|sound good)\b/i.test(cleanText)) {
        out.push({ label: "✅ Yes", send: "Yes" });
        out.push({ label: "❌ No", send: "No" });
      }
    }
    return { cleanText, actions: out, picker: pickerKind, quoteCard: quoteCardId };
  }

  function addMsg(who, text, toolCalls, isAgent) {
    let cleanText = text;
    let actions = [];
    let picker = null;
    let quoteCard = null;
    if (who === "bot") {
      const ex = extractActions(text, toolCalls);
      cleanText = ex.cleanText;
      actions = ex.actions;
      picker = ex.picker;
      quoteCard = ex.quoteCard;
    }
    const div = el("div", { class: "us-msg " + (who === "user" ? "user" : "bot") });
    div.innerHTML = formatMd(cleanText);
    if (isAgent) div.prepend(el("div", { class: "us-tool-tag" }, "👤 Live agent"));
    else if (toolCalls && toolCalls.length) {
      const names = [...new Set(toolCalls.map(t => t.name))].join(", ");
      div.appendChild(el("div", { class: "us-tool-tag" }, "Used: " + names));
    }
    body.appendChild(div);
    if (who === "bot" && actions.length) {
      const wrap = el("div", { class: "us-actions" });
      actions.forEach(a => {
        const b = el("button", { type: "button" }, a.label);
        b.onclick = () => {
          [...wrap.querySelectorAll("button")].forEach(x => x.disabled = true);
          b.classList.add("us-action-picked");
          input.value = a.send; form.requestSubmit();
        };
        wrap.appendChild(b);
      });
      body.appendChild(wrap);
    }
    // v1.24.78 — render in-chat quote card if [[quote_card:Q-XXX]] was emitted
    if (who === "bot" && quoteCard) {
      const card = _buildQuoteCard(quoteCard);
      body.appendChild(card);
    }
    // v1.24.64 — render rich date/time picker if [[picker:date]] / [[picker:time]] was emitted
    if (who === "bot" && picker) {
      body.appendChild(_buildPicker(picker));
    }
    body.scrollTop = body.scrollHeight;
  }

  // v1.24.64 — date/time picker DOM
  function _buildPicker(kind) {
    const wrap = el("div", { class: "us-picker" });
    if (kind === "date") {
      // 14-day horizontal scroll cards: Today, Tomorrow, then weekday + date
      const days = [];
      const today = new Date();
      today.setHours(0,0,0,0);
      const monthShort = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
      const dayShort = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
      for (let i = 0; i < 14; i++) {
        const d = new Date(today.getTime() + i * 86400000);
        const label = i === 0 ? "Today" : (i === 1 ? "Tomorrow" : dayShort[d.getDay()]);
        const sub = `${d.getDate()} ${monthShort[d.getMonth()]}`;
        const iso = d.toISOString().slice(0,10);
        const sendStr = `${label} (${dayShort[d.getDay()]} ${d.getDate()} ${monthShort[d.getMonth()]} ${d.getFullYear()})`;
        days.push({ label, sub, iso, sendStr, isWeekend: d.getDay() === 0 || d.getDay() === 6 });
      }
      const strip = el("div", { class: "us-picker-strip" });
      days.forEach(d => {
        const card = el("button", { type: "button", class: "us-picker-day" + (d.isWeekend ? " us-picker-day-weekend" : "") });
        card.innerHTML = `<div class="us-picker-day-label">${d.label}</div>
          <div class="us-picker-day-sub">${d.sub}</div>`;
        card.onclick = () => {
          [...wrap.querySelectorAll("button")].forEach(x => x.disabled = true);
          card.classList.add("us-picker-picked");
          input.value = d.sendStr; form.requestSubmit();
        };
        strip.appendChild(card);
      });
      // v1.24.74 — append a "Custom date" card at the end that opens a
      // native <input type="date"> picker for any future date.
      const customCard = el("button", { type: "button", class: "us-picker-day us-picker-day-custom" });
      customCard.innerHTML = `<div class="us-picker-day-label">📅 Custom</div>
        <div class="us-picker-day-sub">pick any</div>`;
      // Hidden native date input — full Android/iOS native picker
      const hiddenDate = el("input", {
        type: "date",
        style: "position:absolute;opacity:0;pointer-events:none;width:1px;height:1px;left:0;top:0",
      });
      // Min = tomorrow, max = +180 days
      const tomorrow = new Date(today.getTime() + 86400000);
      const maxDate  = new Date(today.getTime() + 180 * 86400000);
      hiddenDate.min = tomorrow.toISOString().slice(0,10);
      hiddenDate.max = maxDate.toISOString().slice(0,10);
      hiddenDate.onchange = () => {
        if (!hiddenDate.value) return;
        const d = new Date(hiddenDate.value + "T00:00:00");
        const sendStr = `${dayShort[d.getDay()]} ${d.getDate()} ${monthShort[d.getMonth()]} ${d.getFullYear()}`;
        [...wrap.querySelectorAll("button")].forEach(x => x.disabled = true);
        customCard.classList.add("us-picker-picked");
        customCard.innerHTML = `<div class="us-picker-day-label">${dayShort[d.getDay()]}</div>
          <div class="us-picker-day-sub">${d.getDate()} ${monthShort[d.getMonth()]}</div>`;
        input.value = sendStr; form.requestSubmit();
      };
      customCard.onclick = () => {
        // showPicker() opens the native date dialog on Chrome/Android/iOS.
        // Fallback to .focus() + .click() for older browsers.
        try {
          if (typeof hiddenDate.showPicker === "function") hiddenDate.showPicker();
          else { hiddenDate.focus(); hiddenDate.click(); }
        } catch (_) { hiddenDate.focus(); hiddenDate.click(); }
      };
      strip.appendChild(customCard);
      wrap.appendChild(strip);
      wrap.appendChild(hiddenDate);
      const hint = el("div", { class: "us-picker-hint" }, "← swipe for more days · or tap 📅 Custom for any date");
      wrap.appendChild(hint);
    } else if (kind === "time") {
      // 6-col grid of half-hour slots from 7am to 9pm
      const slots = [];
      for (let h = 7; h <= 21; h++) {
        for (const m of [0, 30]) {
          if (h === 21 && m === 30) continue;
          const t24 = `${String(h).padStart(2,"0")}:${String(m).padStart(2,"0")}`;
          const ampm = h < 12 ? "AM" : "PM";
          const h12 = h % 12 || 12;
          const t12 = `${h12}:${String(m).padStart(2,"0")} ${ampm}`;
          slots.push({ t24, t12 });
        }
      }
      const grid = el("div", { class: "us-picker-grid" });
      slots.forEach(s => {
        const b = el("button", { type: "button", class: "us-picker-time" }, s.t12);
        b.onclick = () => {
          [...wrap.querySelectorAll("button")].forEach(x => x.disabled = true);
          b.classList.add("us-picker-picked");
          input.value = s.t24; form.requestSubmit();
        };
        grid.appendChild(b);
      });
      wrap.appendChild(grid);
      const hint = el("div", { class: "us-picker-hint" }, "or type a custom time (e.g. 11pm)");
      wrap.appendChild(hint);
    } else if (kind === "datetime") {
      // v1.24.75 — combined month-grid calendar + time slots in one picker.
      // Customer picks a day on the calendar, time grid reveals below,
      // then a single tap on a time slot submits "Day DD Mon YYYY at HH:MM".
      const monthShort = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
      const monthLong  = ["January","February","March","April","May","June","July","August","September","October","November","December"];
      const dayShort   = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
      const dayHead    = ["S","M","T","W","T","F","S"];
      const today = new Date(); today.setHours(0,0,0,0);
      const max = new Date(today.getTime() + 180 * 86400000);

      // State
      let viewYear  = today.getFullYear();
      let viewMonth = today.getMonth();   // 0-11
      let pickedISO = null;
      let pickedSendDate = null;          // "Sat 11 May 2026"

      // --- Month header with prev/next ---
      const header = el("div", { class: "us-cal-head" });
      const btnPrev = el("button", { type: "button", class: "us-cal-nav", "aria-label": "Previous month" }, "‹");
      const lblMonth = el("div", { class: "us-cal-title" });
      const btnNext = el("button", { type: "button", class: "us-cal-nav", "aria-label": "Next month" }, "›");
      header.appendChild(btnPrev); header.appendChild(lblMonth); header.appendChild(btnNext);
      wrap.appendChild(header);

      // --- Day-of-week heading row ---
      const dowRow = el("div", { class: "us-cal-dow" });
      dayHead.forEach(d => { dowRow.appendChild(el("div", { class: "us-cal-dow-cell" }, d)); });
      wrap.appendChild(dowRow);

      // --- Calendar grid ---
      const calGrid = el("div", { class: "us-cal-grid" });
      wrap.appendChild(calGrid);

      // --- Time block (hidden until date picked) ---
      const timeBlock = el("div", { class: "us-cal-time", style: "display:none" });
      const timeLabel = el("div", { class: "us-cal-time-label" }, "Pick a time");
      const timeGrid  = el("div", { class: "us-picker-grid us-cal-time-grid" });
      timeBlock.appendChild(timeLabel);
      timeBlock.appendChild(timeGrid);
      wrap.appendChild(timeBlock);

      const hint = el("div", { class: "us-picker-hint" }, "Tap a date, then a time");
      wrap.appendChild(hint);

      // --- Renderers ---
      function _isPast(y, m, d) {
        const cell = new Date(y, m, d); cell.setHours(0,0,0,0);
        return cell.getTime() < today.getTime();
      }
      function _isAfterMax(y, m, d) {
        const cell = new Date(y, m, d); cell.setHours(0,0,0,0);
        return cell.getTime() > max.getTime();
      }
      function _renderCalendar() {
        lblMonth.textContent = `${monthLong[viewMonth]} ${viewYear}`;
        // Disable nav past today/max
        btnPrev.disabled = (viewYear < today.getFullYear() ||
          (viewYear === today.getFullYear() && viewMonth <= today.getMonth()));
        btnNext.disabled = (viewYear > max.getFullYear() ||
          (viewYear === max.getFullYear() && viewMonth >= max.getMonth()));
        // Build cells
        calGrid.innerHTML = "";
        const firstDow = new Date(viewYear, viewMonth, 1).getDay();
        const dim = new Date(viewYear, viewMonth + 1, 0).getDate();
        for (let i = 0; i < firstDow; i++) {
          calGrid.appendChild(el("div", { class: "us-cal-cell us-cal-empty" }));
        }
        for (let d = 1; d <= dim; d++) {
          const past = _isPast(viewYear, viewMonth, d);
          const beyond = _isAfterMax(viewYear, viewMonth, d);
          const isToday = (viewYear === today.getFullYear() &&
                           viewMonth === today.getMonth() && d === today.getDate());
          const cls = "us-cal-cell" +
                      (past || beyond ? " us-cal-disabled" : "") +
                      (isToday ? " us-cal-today" : "");
          const cell = el("button", { type: "button", class: cls }, String(d));
          if (past || beyond) cell.disabled = true;
          else {
            cell.onclick = () => {
              [...calGrid.querySelectorAll("button")].forEach(x => x.classList.remove("us-cal-picked"));
              cell.classList.add("us-cal-picked");
              const dt = new Date(viewYear, viewMonth, d);
              pickedISO = dt.toISOString().slice(0,10);
              pickedSendDate = `${dayShort[dt.getDay()]} ${dt.getDate()} ${monthShort[dt.getMonth()]} ${dt.getFullYear()}`;
              timeLabel.textContent = `Pick a time for ${pickedSendDate}`;
              timeBlock.style.display = "";
              timeBlock.scrollIntoView({behavior:"smooth", block:"nearest"});
            };
          }
          calGrid.appendChild(cell);
        }
      }
      btnPrev.onclick = () => {
        if (viewMonth === 0) { viewMonth = 11; viewYear--; } else viewMonth--;
        _renderCalendar();
      };
      btnNext.onclick = () => {
        if (viewMonth === 11) { viewMonth = 0; viewYear++; } else viewMonth++;
        _renderCalendar();
      };

      // Build time slots once
      for (let h = 7; h <= 21; h++) {
        for (const m of [0, 30]) {
          if (h === 21 && m === 30) continue;
          const t24 = `${String(h).padStart(2,"0")}:${String(m).padStart(2,"0")}`;
          const ampm = h < 12 ? "AM" : "PM";
          const h12 = h % 12 || 12;
          const t12 = `${h12}:${String(m).padStart(2,"0")} ${ampm}`;
          const b = el("button", { type: "button", class: "us-picker-time" }, t12);
          b.onclick = () => {
            if (!pickedSendDate) return;
            [...wrap.querySelectorAll("button")].forEach(x => x.disabled = true);
            b.classList.add("us-picker-picked");
            input.value = `${pickedSendDate} at ${t24}`;
            form.requestSubmit();
          };
          timeGrid.appendChild(b);
        }
      }

      _renderCalendar();
    } else if (kind === "address") {
      // v1.24.90 — Slice A.5: in-chat pin-first address card.
      // Defers to web/address-picker.js (already in repo, used by /me-profile).
      // 1. Show "Saved places" dropdown if customer has any (lazy-fetched)
      // 2. Then the pin-on-map address card
      // On submit: auto-saves to /api/me/locations/upsert-from-pin AND
      // sends a structured one-line summary as the next chat message.
      const head = el("div", { class: "us-addr-head" });
      head.innerHTML =
        '<div style="font-weight:800;font-size:14px;color:var(--us-primary)">📍 Where should we come?</div>' +
        '<div style="font-size:11.5px;color:var(--us-muted);margin-top:3px">Pin the exact spot — area + city auto-fill from the map.</div>';
      wrap.appendChild(head);

      // Saved-places dropdown (only shown if user has any saved)
      const savedRow = el("div", { class: "us-addr-saved", style: "display:none;margin:8px 0" });
      wrap.appendChild(savedRow);

      // Address-picker mount point
      const apMount = el("div", { class: "us-addr-mount" });
      wrap.appendChild(apMount);

      function _commitAddress(a) {
        // Save to profile (upsert-from-pin dedupes)
        try {
          fetch("/api/me/locations/upsert-from-pin", {
            method: "POST", credentials: "include",
            headers: {"Content-Type":"application/json"},
            body: JSON.stringify(a),
          }).catch(()=>{});
        } catch(_) {}
        // Send a friendly one-line summary back to the bot
        const summary =
          (a.label ? `[${a.label}] ` : "") +
          [a.building, a.unit, a.area, a.city].filter(Boolean).join(", ");
        input.value = summary;
        // Tag the structured payload onto the form so /api/chat can read it
        try { window.__lastAddressPicked = a; } catch(_){}
        form.requestSubmit();
      }

      // Lazy-load the address-picker JS if not already on page
      function _mountPicker() {
        if (window.serviaAddressPicker && window.serviaAddressPicker.mount) {
          window.serviaAddressPicker.mount(apMount, { onPick: _commitAddress });
        } else {
          // Inject script tag if absent
          if (!document.querySelector('script[data-ap]')) {
            const s = document.createElement("script");
            s.src = "/address-picker.js?v=1.24.94"; s.dataset.ap = "1";
            s.onload = () => window.serviaAddressPicker &&
                              window.serviaAddressPicker.mount(apMount, { onPick: _commitAddress });
            document.head.appendChild(s);
          }
        }
      }

      // Pull saved locations
      fetch("/api/me/profile", { credentials: "include" })
        .then(r => r.json()).then(j => {
          if (j && j.ok && (j.locations || []).length) {
            savedRow.style.display = "block";
            savedRow.innerHTML = '<div style="font-size:11px;color:var(--us-muted);font-weight:700;margin-bottom:5px;text-transform:uppercase;letter-spacing:.05em">Saved places</div>';
            j.locations.forEach(loc => {
              const b = el("button", {
                type: "button",
                style: "display:block;width:100%;text-align:left;padding:8px 10px;background:#fff;border:1px solid #E2E8F0;border-radius:8px;margin-bottom:5px;cursor:pointer;font-family:inherit"
              });
              const sub = [loc.building, loc.unit, loc.area, loc.city].filter(Boolean).join(", ");
              b.innerHTML = `<b>📍 ${loc.label || "Saved"}</b><br><span style="color:#64748B;font-size:11.5px">${sub}</span>`;
              b.onclick = () => _commitAddress(loc);
              savedRow.appendChild(b);
            });
            const adder = el("div", { style: "font-size:12px;color:var(--us-muted);text-align:center;margin:8px 0" }, "— or pin a new spot below —");
            savedRow.appendChild(adder);
          }
          _mountPicker();
        }).catch(_mountPicker);
    }
    return wrap;
  }

  // v1.24.78 — in-chat quote card. Fetches /api/q/<id>/card?session_id=<sid>
  // and renders the full booking summary + signature pad + action buttons
  // INSIDE the chat message bubble. No need for the customer to navigate to
  // /q/<id> at all — they can review, sign, download, print, and pay all
  // from the conversation flow. Designed by senior UX-UI per CLAUDE.md
  // DESIGN-REVIEW gate.
  function _buildQuoteCard(qid) {
    const card = el("div", { class: "us-qcard" });
    card.innerHTML = `<div class="us-qcard-loading">Loading quote ${qid}…</div>`;
    const sid = (typeof sessionId !== "undefined" && sessionId) || window.LUMORA_SESSION_ID || sessionStorage.getItem("us.sid") || "";
    fetch(`/api/q/${qid}/card?session_id=${encodeURIComponent(sid)}`)
      .then(r => r.json())
      .then(j => {
        if (!j.ok) {
          card.innerHTML = `<div class="us-qcard-err">Couldn't load quote ${qid}. Open <a href="/q/${qid}" target="_blank">/q/${qid}</a></div>`;
          return;
        }
        _renderQuoteCard(card, j, sid);
      })
      .catch(() => {
        card.innerHTML = `<div class="us-qcard-err">Network error loading ${qid}.</div>`;
      });
    return card;
  }

  function _renderQuoteCard(card, q, sid) {
    // v1.24.82 — pass session_id to View/PDF/Print/Pay URLs so /q /p /i
    // can authenticate the user from chat session, skipping the phone
    // gate. UX: user is already in a verified chat session.
    const qsid = sid ? ("?sid=" + encodeURIComponent(sid)) : "";
    const items = (q.items || []).map((it, i) =>
      `<div class="us-qcard-line">
         <span class="us-qcard-num">${i+1}</span>
         <span class="us-qcard-name">${it.label || it.service_id}</span>
         <span class="us-qcard-detail">${it.detail || ''}</span>
         <span class="us-qcard-price">AED ${(it.price_aed||0).toLocaleString()}</span>
       </div>`).join("");
    const isSigned = !!q.signed_at;
    card.innerHTML = `
      <div class="us-qcard-head">
        <div class="us-qcard-title">📋 Quote ${q.quote_id}</div>
        ${isSigned ? '<div class="us-qcard-badge us-qcard-badge-ok">✓ Signed</div>' : '<div class="us-qcard-badge">Pending sign</div>'}
      </div>
      <div class="us-qcard-items">${items}</div>
      <div class="us-qcard-totals">
        <div class="us-qcard-trow"><span>Subtotal</span><span>AED ${(q.subtotal_aed||0).toLocaleString()}</span></div>
        <div class="us-qcard-trow"><span>VAT 5%</span><span>AED ${(q.vat_aed||0).toLocaleString()}</span></div>
        <div class="us-qcard-trow us-qcard-total"><span>Total</span><span>AED ${(q.total_aed||0).toLocaleString()}</span></div>
      </div>
      <div class="us-qcard-meta">
        <div>📅 <b>${q.target_date||''}</b> at <b>${q.time_slot||''}</b></div>
        <div>📍 ${q.address||''}</div>
        <div>👤 ${q.customer_name||''} · ${q.phone||''}</div>
      </div>
      <div class="us-qcard-actions">
        <a class="us-qcard-btn" href="${q.view_url}${qsid}" target="_blank">👁 View</a>
        <a class="us-qcard-btn" href="${q.pdf_url}${qsid}" target="_blank">📥 PDF</a>
        <a class="us-qcard-btn" href="${q.print_url}${qsid}" target="_blank">🖨 Print</a>
      </div>
      ${isSigned ? `
        <div class="us-qcard-signed">
          <div class="us-qcard-signed-msg">✅ Signed at ${q.signed_at}. <b>100% advance payment</b> applies — pay below to lock your slot.</div>
          <a class="us-qcard-pay" href="${q.pay_url}${qsid}" target="_blank">💳 Pay AED ${(q.total_aed||0).toLocaleString()}</a>
          <button type="button" class="us-qcard-btn us-qcard-revise" style="margin-top:10px">✏️ Revise quote</button>
        </div>
      ` : `
        <div class="us-qcard-sigblock">
          <div class="us-qcard-siglabel">✍️ Sign here to confirm this booking:</div>
          <canvas class="us-qcard-sigpad" width="380" height="90"></canvas>
          <div class="us-qcard-sigrow">
            <button type="button" class="us-qcard-btn us-qcard-clear">Clear</button>
            <button type="button" class="us-qcard-btn us-qcard-approve">✅ Approve &amp; sign</button>
          </div>
          <div class="us-qcard-payinfo" style="font-size:11px;color:var(--us-muted);margin-top:8px;text-align:center">
            🔒 <b>100% advance payment.</b> Required to lock your slot — fully refundable if we cancel.
          </div>
          <div class="us-qcard-msg"></div>
        </div>
      `}
    `;
    if (!isSigned) _wireSignPad(card, q, sid);
    else _wireReviseButton(card, q, sid);
  }

  // v1.24.82 — Revise button only appears AFTER sign. Tapping it sends
  // a structured "I want to revise quote Q-XXX" message to the bot,
  // which then asks what to change. The next create_multi_quote call
  // will use revise_of=Q-XXX → produces Q-XXX-1 (then -2, -3, ...).
  function _wireReviseButton(card, q, sid) {
    const btn = card.querySelector(".us-qcard-revise");
    if (!btn) return;
    btn.onclick = () => {
      btn.disabled = true;
      btn.textContent = "✏️ Revising…";
      input.value = `I want to revise quote ${q.quote_id} (tell me what to add, remove, or change)`;
      form.requestSubmit();
    };
  }

  function _wireSignPad(card, q, sid) {
    const canvas = card.querySelector(".us-qcard-sigpad");
    const ctx = canvas.getContext("2d");
    let drawing = false; let last = null; let hasInk = false;
    ctx.strokeStyle = "#0F172A"; ctx.lineWidth = 2; ctx.lineCap = "round";
    function pos(e) {
      const r = canvas.getBoundingClientRect();
      const t = e.touches && e.touches[0];
      return { x: ((t?t.clientX:e.clientX) - r.left) * (canvas.width/r.width),
               y: ((t?t.clientY:e.clientY) - r.top)  * (canvas.height/r.height) };
    }
    function down(e) { e.preventDefault(); drawing = true; last = pos(e); hasInk = true; }
    function move(e) {
      if (!drawing) return;
      e.preventDefault();
      const p = pos(e);
      ctx.beginPath(); ctx.moveTo(last.x, last.y); ctx.lineTo(p.x, p.y); ctx.stroke();
      last = p;
    }
    function up() { drawing = false; }
    canvas.addEventListener("mousedown", down);
    canvas.addEventListener("mousemove", move);
    canvas.addEventListener("mouseup", up);
    canvas.addEventListener("mouseleave", up);
    canvas.addEventListener("touchstart", down, {passive:false});
    canvas.addEventListener("touchmove", move, {passive:false});
    canvas.addEventListener("touchend", up);
    card.querySelector(".us-qcard-clear").onclick = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height); hasInk = false;
    };
    const msg = card.querySelector(".us-qcard-msg");
    card.querySelector(".us-qcard-approve").onclick = async () => {
      if (!hasInk) { msg.textContent = "Please draw your signature first."; msg.style.color="#DC2626"; return; }
      msg.textContent = "Submitting…"; msg.style.color = "var(--us-muted)";
      try {
        const r = await fetch(`/api/q/${q.quote_id}/sign`, {
          method: "POST", headers: {"Content-Type":"application/json"},
          body: JSON.stringify({
            signature_data_url: canvas.toDataURL("image/png"),
            session_id: sid,
          }),
        });
        const j = await r.json();
        if (j.ok) {
          q.signed_at = j.signed_at;
          _renderQuoteCard(card, q, sid);  // re-render with signed state
          _wireReviseButton(card, q, sid);
        } else {
          msg.textContent = "Failed: " + (j.error || "unknown error");
          msg.style.color = "#DC2626";
        }
      } catch (e) {
        msg.textContent = "Network error. Try again.";
        msg.style.color = "#DC2626";
      }
    };
  }

  function addMsgWithImage(who, text, imageUrl) {
    const div = el("div", { class: "us-msg " + (who === "user" ? "user" : "bot") });
    const img = el("img", { src: imageUrl, alt: "Attached photo",
      style: "max-width:200px;max-height:200px;border-radius:10px;margin-bottom:6px;display:block" });
    div.appendChild(img);
    if (text) {
      const t = document.createElement("div");
      t.innerHTML = formatMd(text);
      div.appendChild(t);
    }
    body.appendChild(div);
    body.scrollTop = body.scrollHeight;
  }

  function showTyping() {
    const t = el("div", { class: "us-typing" }, el("span"), el("span"), el("span"));
    body.appendChild(t);
    body.scrollTop = body.scrollHeight;
    return t;
  }

  function formatMd(s) {
    const escaped = (s || "").replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
    return escaped
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/_([^_]+)_/g, "<em>$1</em>")
      // Markdown links: [text](url) → clickable button-styled link.
      // Only allow http(s) + relative URLs (starts with /) to keep XSS safe.
      .replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+|\/[^)\s]*)\)/g,
        '<a href="$2" target="_blank" rel="noopener" style="display:inline-block;background:#0F766E;color:#fff;padding:4px 10px;border-radius:6px;font-weight:700;text-decoration:none;font-size:12.5px;margin:2px 2px 2px 0">$1 ↗</a>')
      // Auto-link bare URLs (only if not already inside an <a>)
      .replace(/(^|[^"'>])(https?:\/\/[^\s<>]+)/g,
        '$1<a href="$2" target="_blank" rel="noopener" style="color:#0F766E;font-weight:600;word-break:break-all">$2</a>')
      .replace(/^[•\-\*]\s+(.+)$/gm, "&nbsp;&nbsp;• $1")
      .replace(/\n/g, "<br>");
  }

  function el(tag, attrs, ...kids) {
    const e = document.createElement(tag);
    if (attrs) for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
    for (const k of kids) {
      if (k == null) continue;
      e.appendChild(typeof k === "string" ? document.createTextNode(k) : k);
    }
    return e;
  }

  // ---------- Voice input — Web Speech API w/ 15-lang map + live transcript ----------
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    micBtn.style.display = "none";
  } else {
    let rec = null;
    let listening = false;
    // v1.24.16 — track the LAST dictation so re-tapping mic replaces it
    // instead of treating it as prefix-to-append-to. This is what was
    // actually producing the dup-text bug ("I I want I want to I want
    // to know…"): the user kept tapping mic without sending, each tap
    // captured the previous dictation as prefix, and new dictation
    // appended. Now we strip the previous dictation off the input
    // before capturing prefix, so re-taps replace cleanly.
    let lastDictation = "";
    micBtn.onclick = () => {
      if (listening && rec) { try { rec.stop(); } catch {} return; }
      const lang = (window.lumoraLang ? lumoraLang() : "en");
      rec = new SR();
      rec.continuous = false;
      rec.interimResults = true;
      rec.lang = SR_LANG_MAP[lang] || "en-US";
      rec.onstart = () => { listening = true; micBtn.classList.add("recording");
                            micBtn.textContent = "🔴"; input.placeholder = "🎙 Listening… speak in any UAE language"; };
      rec.onend = () => { listening = false; micBtn.classList.remove("recording");
                          micBtn.textContent = "🎤"; input.placeholder = "Type your message…"; };
      // STRIP previous dictation so the new dictation REPLACES it.
      let cur = (input.value || "").trim();
      if (lastDictation) {
        if (cur === lastDictation) {
          cur = "";
        } else if (lastDictation.length >= 3 && cur.endsWith(" " + lastDictation)) {
          cur = cur.slice(0, cur.length - lastDictation.length - 1).trim();
        }
        input.value = cur;
      }
      const prefix = cur;
      // Use ONLY the latest result (the canonical current interpretation).
      // Never accumulate across e.results entries.
      rec.onresult = (e) => {
        if (!e.results || !e.results.length) return;
        const latest = e.results[e.results.length - 1];
        if (!latest) return;
        const txt = (latest[0].transcript || "").trim();
        lastDictation = txt;
        input.value = (prefix ? prefix + " " : "") + txt;
      };
      rec.onerror = (e) => {
        listening = false; micBtn.classList.remove("recording");
        micBtn.textContent = "🎤"; input.placeholder = "Type your message…";
        if (e.error === "not-allowed") {
          alert("Microphone permission denied. Enable it in your browser to use voice input.");
        }
      };
      try { rec.start(); } catch {}
    };
  }

  // ---------- 📍 Location share (v1.24.9) ----------
  // Tap → bottom sheet with: 🛰 Use my GPS · 🗺 Pin on map · ✏ Type address.
  // Detects whether the conversation context implies source+destination
  // (chauffeur / furniture move / recovery tow) by scanning the last few
  // user/assistant messages for keywords. If it does, the sheet shows two
  // location pickers stacked (FROM and TO). Otherwise just one location.
  locBtn.onclick = () => openLocationSheet(input);

  function openLocationSheet(targetInput) {
    if (document.getElementById("us-loc-sheet")) return;
    var needsDest = sniffNeedsDestination();
    var sheet = el("div", { id: "us-loc-sheet" });
    sheet.style.cssText =
      "position:fixed;inset:0;background:rgba(15,23,42,.55);z-index:100000;" +
      "display:flex;align-items:flex-end;justify-content:center;backdrop-filter:blur(4px)";
    sheet.innerHTML =
      '<div style="background:#fff;color:#0F172A;border-radius:24px 24px 0 0;width:100%;max-width:520px;padding:18px 16px 22px;max-height:90vh;overflow:auto;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif">'
      + '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px">'
        + '<h3 style="margin:0;font-size:18px">📍 Share location</h3>'
        + '<button id="us-loc-x" style="background:transparent;border:0;font-size:22px;cursor:pointer;color:#64748B" aria-label="Close">✕</button>'
      + '</div>'
      + '<p style="margin:0 0 12px;color:#64748B;font-size:12.5px">' + (needsDest
        ? 'This service needs a pickup AND drop-off.'
        : 'Use your GPS, pin the spot, or type the address.') + '</p>'
      + locationBlockHtml("from", needsDest ? "📍 Pickup (FROM)" : "📍 Where")
      + (needsDest ? locationBlockHtml("to", "🏁 Drop-off (TO)") : "")
      + '<button id="us-loc-go" style="display:block;width:100%;padding:14px;font-size:15px;font-weight:800;border:0;border-radius:14px;background:#0F766E;color:#fff;cursor:pointer;margin-top:10px">'
        + 'Send to Servia'
      + '</button>'
      + '</div>';
    document.body.appendChild(sheet);
    sheet.querySelector("#us-loc-x").onclick = function(){ sheet.remove(); };
    sheet.addEventListener("click", function(e){ if (e.target === sheet) sheet.remove(); });

    wireLocationBlock(sheet, "from");
    if (needsDest) wireLocationBlock(sheet, "to");

    sheet.querySelector("#us-loc-go").onclick = function(){
      var fromTxt = collectLocation(sheet, "from");
      if (!fromTxt) { alert("Pick or type the location first."); return; }
      var msg;
      if (needsDest) {
        var toTxt = collectLocation(sheet, "to");
        if (!toTxt) { alert("Add the drop-off too."); return; }
        msg = "📍 FROM: " + fromTxt + "\n🏁 TO: " + toTxt;
      } else {
        msg = "📍 " + fromTxt;
      }
      var existing = (targetInput.value || "").trim();
      targetInput.value = (existing ? existing + "\n" : "") + msg;
      sheet.remove();
      // Auto-submit so the chat round-trip starts immediately.
      try { sendBtn.click(); } catch (_) {}
    };
  }

  function locationBlockHtml(prefix, title) {
    return ''
    + '<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:14px;padding:12px;margin-bottom:10px">'
      + '<div style="font-size:11px;font-weight:800;color:#0F766E;letter-spacing:.05em;text-transform:uppercase;margin-bottom:6px">' + title + '</div>'
      + '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px">'
        + '<button data-act="gps" data-pre="' + prefix + '" style="flex:1;min-width:120px;padding:9px;border:1px solid #99F6E4;background:#F0FDFA;color:#0F766E;border-radius:10px;font-weight:700;font-size:12px;cursor:pointer">🛰 Use my GPS</button>'
        + '<button data-act="map" data-pre="' + prefix + '" style="flex:1;min-width:120px;padding:9px;border:1px solid #DDD;background:#fff;color:#0F172A;border-radius:10px;font-weight:700;font-size:12px;cursor:pointer">🗺 Pin on map</button>'
      + '</div>'
      + '<input id="us-loc-' + prefix + '-addr" type="text" placeholder="Or type address (Marina Pinnacle, Apt 1204, JLT…)" style="width:100%;padding:10px;border:1px solid #CBD5E1;border-radius:10px;font-size:13px;font-family:inherit;margin-bottom:6px">'
      + '<input id="us-loc-' + prefix + '-notes" type="text" placeholder="Notes (gate code, parking, etc)" style="width:100%;padding:10px;border:1px solid #CBD5E1;border-radius:10px;font-size:12px;font-family:inherit">'
      + '<div id="us-loc-' + prefix + '-status" style="font-size:11px;color:#64748B;margin-top:6px;min-height:14px"></div>'
      + '<input id="us-loc-' + prefix + '-coord" type="hidden">'
    + '</div>';
  }

  function wireLocationBlock(sheet, prefix) {
    var st = sheet.querySelector("#us-loc-" + prefix + "-status");
    var hidden = sheet.querySelector("#us-loc-" + prefix + "-coord");
    var addr = sheet.querySelector("#us-loc-" + prefix + "-addr");
    Array.prototype.forEach.call(
      sheet.querySelectorAll('button[data-pre="' + prefix + '"]'),
      function(b){
        b.onclick = function(){
          var act = b.getAttribute("data-act");
          if (act === "gps") {
            if (!navigator.geolocation) { st.textContent = "Geolocation not available."; return; }
            st.textContent = "📡 Getting GPS…";
            navigator.geolocation.getCurrentPosition(function(p){
              var lat = p.coords.latitude, lng = p.coords.longitude;
              hidden.value = lat.toFixed(5) + "," + lng.toFixed(5);
              st.textContent = "✅ GPS captured (±" + Math.round(p.coords.accuracy) + "m)";
              reverseGeocode(lat, lng, addr);
            }, function(e){
              st.textContent = "⚠ " + (e.code === 1 ? "Permission denied — type the address instead." : "Could not get GPS.");
            }, {enableHighAccuracy:true, timeout:12000, maximumAge:0});
          } else if (act === "map") {
            openMapPicker(function(lat, lng){
              hidden.value = lat.toFixed(5) + "," + lng.toFixed(5);
              st.textContent = "✅ Pin set (" + lat.toFixed(4) + "," + lng.toFixed(4) + ")";
              reverseGeocode(lat, lng, addr);
            }, hidden.value);
          }
        };
      });
  }

  function reverseGeocode(lat, lng, addrInput) {
    fetch("https://nominatim.openstreetmap.org/reverse?format=json&lat=" + lat + "&lon=" + lng,
      {headers:{"Accept-Language":"en"}})
      .then(function(r){ return r.json(); })
      .then(function(j){
        if (j && j.display_name && !addrInput.value) {
          addrInput.value = j.display_name.split(",").slice(0,3).join(",");
        }
      })
      .catch(function(){});
  }

  function collectLocation(sheet, prefix) {
    var addr = (sheet.querySelector("#us-loc-" + prefix + "-addr").value || "").trim();
    var coord = (sheet.querySelector("#us-loc-" + prefix + "-coord").value || "").trim();
    var notes = (sheet.querySelector("#us-loc-" + prefix + "-notes").value || "").trim();
    if (!addr && !coord) return null;
    var bits = [];
    if (addr) bits.push(addr);
    if (coord) bits.push("(" + coord + ")");
    if (notes) bits.push("[" + notes + "]");
    return bits.join(" ");
  }

  function sniffNeedsDestination() {
    // Walk the last 6 chat bubbles and look for keywords that imply a
    // pickup-AND-drop-off service. Conservative — only return true on a
    // clear signal so single-location services don't see a confusing
    // 2-block sheet.
    var bodyText = "";
    try {
      var bubbles = panel.querySelectorAll(".us-msg, .us-bubble");
      var n = Math.min(6, bubbles.length);
      for (var i = bubbles.length - n; i < bubbles.length; i++) {
        bodyText += " " + (bubbles[i].textContent || "").toLowerCase();
      }
      bodyText += " " + (input.value || "").toLowerCase();
    } catch (_) {}
    var rx = /(move|moving|movers|relocation|relocate|chauffeur|driver|tow|towing|recovery|deliver|delivery|airport|drop[- ]?off|pickup|pick[- ]?up|from .* to |destination)/i;
    return rx.test(bodyText);
  }

  // ---------- Map pin picker (Leaflet, lazy-loaded) ----------
  var _picker = null;
  function openMapPicker(onConfirm, currentCoord) {
    if (_picker) _picker.remove();
    _picker = el("div", { id: "us-mappick" });
    _picker.style.cssText =
      "position:fixed;inset:0;background:#0F172A;z-index:200000;display:flex;flex-direction:column";
    _picker.innerHTML =
      '<header style="padding:10px 14px;background:#0F172A;color:#fff;display:flex;align-items:center;gap:10px">'
        + '<button id="us-mp-back" style="background:transparent;color:#fff;border:0;font-size:20px;cursor:pointer">←</button>'
        + '<div style="flex:1"><div style="font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:#FCD34D;font-weight:800">Pin location</div>'
        + '<div style="font-size:13px;font-weight:600">Drag map · centre is your pin</div></div>'
      + '</header>'
      + '<div style="position:relative;flex:1;min-height:200px;background:#1E293B">'
        + '<div id="us-mp-map" style="position:absolute;inset:0;width:100%;height:100%"></div>'
        + '<div style="position:absolute;left:50%;top:50%;transform:translate(-50%,-100%);font-size:42px;text-shadow:0 4px 8px rgba(0,0,0,.4);pointer-events:none;z-index:500">📍</div>'
      + '</div>'
      + '<div style="padding:10px 12px;background:#fff;display:flex;gap:8px;align-items:center">'
        + '<input id="us-mp-q" type="text" placeholder="Search e.g. Marina, Burj Khalifa…" style="flex:1;padding:10px;border:1px solid #CBD5E1;border-radius:10px;font-size:14px">'
        + '<button id="us-mp-srch" style="background:#0F766E;color:#fff;border:0;padding:11px 14px;border-radius:10px;font-weight:800;cursor:pointer">Go</button>'
        + '<button id="us-mp-ok" style="background:#DC2626;color:#fff;border:0;padding:11px 14px;border-radius:10px;font-weight:800;cursor:pointer">✓ Use</button>'
      + '</div>';
    document.body.appendChild(_picker);
    _picker.querySelector("#us-mp-back").onclick = function(){ _picker.remove(); _picker = null; };

    // Lazy-load Leaflet CSS + JS once
    function ensureLeaflet(cb){
      if (window.L) return cb();
      var css = document.createElement("link"); css.rel = "stylesheet";
      css.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"; document.head.appendChild(css);
      var js = document.createElement("script");
      js.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
      js.onload = function(){ cb(); }; document.head.appendChild(js);
    }
    ensureLeaflet(function(){
      var startCoord = currentCoord ? currentCoord.split(",").map(parseFloat) : [25.2048, 55.2708];
      var map = L.map("us-mp-map", {zoomControl:true}).setView(startCoord, currentCoord ? 17 : 11);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {maxZoom:19, attribution:"© OpenStreetMap", subdomains:"abc"}).addTo(map);
      // triple invalidate (Samsung Internet quirk)
      setTimeout(function(){ map.invalidateSize(true); }, 120);
      setTimeout(function(){ map.invalidateSize(true); }, 350);
      setTimeout(function(){ map.invalidateSize(true); }, 800);
      _picker.querySelector("#us-mp-srch").onclick = function(){
        var q = _picker.querySelector("#us-mp-q").value.trim();
        if (!q) return;
        fetch("https://nominatim.openstreetmap.org/search?format=json&q=" +
              encodeURIComponent(q + ", United Arab Emirates") + "&limit=1")
          .then(function(r){ return r.json(); })
          .then(function(arr){
            if (!arr.length) return alert("Not found.");
            map.setView([arr[0].lat, arr[0].lon], 17);
          });
      };
      _picker.querySelector("#us-mp-ok").onclick = function(){
        var c = map.getCenter();
        onConfirm(c.lat, c.lng);
        _picker.remove(); _picker = null;
      };
    });
  }

  // ---------- Photo attachment with client-side compression ----------
  attachBtn.onclick = () => fileInput.click();
  fileInput.onchange = async () => {
    const f = fileInput.files && fileInput.files[0];
    if (!f) return;
    fileInput.value = "";
    if (!f.type.startsWith("image/")) {
      alert("Only image files are supported."); return;
    }
    previewWrap.style.display = "block";
    previewWrap.innerHTML =
      '<div style="display:flex;align-items:center;gap:8px;background:rgba(15,118,110,.08);padding:8px;border-radius:8px;font-size:12px;color:#0F766E">⚙ Compressing photo…</div>';
    try {
      const compressed = await compressImage(f, 1280, 0.65);
      // Upload to backend; get back a stored URL
      const fd = new FormData();
      fd.append("file", compressed, "photo.jpg");
      fd.append("session_id", sessionId || "");
      const r = await fetch(API_BASE + "/api/chat/upload", { method:"POST", body: fd });
      if (!r.ok) throw new Error("upload failed");
      const j = await r.json();
      pendingAttachment = { url: j.url, w: j.width, h: j.height, sizeKb: j.size_kb };
      const dataUrl = URL.createObjectURL(compressed);
      previewWrap.innerHTML =
        `<div style="display:flex;align-items:center;gap:10px;padding:8px;background:#F0FDF4;border:1px solid #6EE7B7;border-radius:10px;font-size:12px;color:#065F46">
          <img src="${dataUrl}" style="width:48px;height:48px;border-radius:8px;object-fit:cover">
          <div style="flex:1">📎 Photo ready · ${j.size_kb} KB · ${j.width}×${j.height}</div>
          <button type="button" class="us-attach-x" style="background:transparent;border:0;color:#065F46;cursor:pointer;font-size:16px">✕</button>
         </div>`;
      previewWrap.querySelector(".us-attach-x").onclick = () => {
        pendingAttachment = null;
        previewWrap.style.display = "none";
        previewWrap.innerHTML = "";
      };
    } catch (e) {
      previewWrap.innerHTML =
        '<div style="background:#FEE2E2;color:#991B1B;padding:8px;border-radius:8px;font-size:12px">❌ Upload failed — ' +
        (e.message || "unknown") + '</div>';
      setTimeout(() => { previewWrap.style.display = "none"; previewWrap.innerHTML = ""; }, 4000);
    }
  };

  function compressImage(file, maxEdge, quality) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const im = new Image();
        im.onload = () => {
          let { width, height } = im;
          if (width > maxEdge || height > maxEdge) {
            if (width > height) { height = Math.round(height * maxEdge / width); width = maxEdge; }
            else                { width = Math.round(width * maxEdge / height); height = maxEdge; }
          }
          const canvas = document.createElement("canvas");
          canvas.width = width; canvas.height = height;
          const ctx = canvas.getContext("2d");
          ctx.drawImage(im, 0, 0, width, height);
          canvas.toBlob(blob => {
            if (!blob) return reject(new Error("compression failed"));
            resolve(blob);
          }, "image/jpeg", quality);
        };
        im.onerror = () => reject(new Error("invalid image"));
        im.src = reader.result;
      };
      reader.onerror = () => reject(new Error("read failed"));
      reader.readAsDataURL(file);
    });
  }
})();
