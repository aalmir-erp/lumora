
(function () {
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
  const launcher = el("button", { class: "us-launcher", "aria-label": "Open chat" }, "💬");
  const panel = el("div", { class: "us-panel", role: "dialog" },
    el("div", { class: "us-header" },
      el("img", { src: "/avatar.svg", width: "36", height: "36",
        style: "border-radius:50%;background:rgba(255,255,255,.18)" }),
      el("div", {},
        el("h3", {}, "Servia"),
        el("p", { class: "us-mode-line" }, "your home services concierge")),
      el("button", { class: "us-close", "aria-label": "Close" }, "×")),
    el("div", { class: "us-body" }),
    el("div", { class: "us-quickreplies" }),
    el("form", { class: "us-input", autocomplete: "off" },
      el("input", { type: "text", placeholder: "Type your message…", required: "true", maxlength: "1000" }),
      el("button", { type: "button", class: "us-mic", "aria-label": "Voice input" }, "🎤"),
      el("button", { type: "submit" }, "Send")),
    el("div", { class: "us-mode" }, ""));
  document.body.appendChild(launcher);
  document.body.appendChild(panel);
  const body = panel.querySelector(".us-body");
  const quickWrap = panel.querySelector(".us-quickreplies");
  const form = panel.querySelector(".us-input");
  const input = form.querySelector("input");
  const sendBtn = form.querySelector("button");
  const modeBadge = panel.querySelector(".us-mode");
  const subtitle = panel.querySelector(".us-mode-line");
  let sessionId = localStorage.getItem(SESSION_KEY);
  let since = +localStorage.getItem(SINCE_KEY) || 0;
  let busy = false;
  let pollT = null;
  let agentMode = false;
  let chatStarted = !!localStorage.getItem(STARTED_KEY) || !!sessionId;
  let userMsgCount = chatStarted ? 1 : 0;
  function applyI18n() {
    const t = (k, d) => (window.lumoraT ? window.lumoraT(k, d) : d);
    input.placeholder = t("bot_placeholder", "Type your message…");
    sendBtn.textContent = t("bot_send", "Send");
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
    if (!body.children.length) greet();
    setTimeout(() => input.focus(), 150);
    startPolling();
  };
  panel.querySelector(".us-close").onclick = () => panel.classList.remove("open");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (busy) return;
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    addMsg("user", text);
    userMsgCount++;
    chatStarted = true;
    localStorage.setItem(STARTED_KEY, "1");
    hideQuickReplies();
    await send(text);
  });
  if (new URLSearchParams(location.search).get("chat") === "1") setTimeout(() => launcher.click(), 400);
  function hideQuickReplies() {
    quickWrap.style.display = "none";
  }
  function greet() {
    const t = window.lumoraT ? window.lumoraT("bot_greeting") : null;
    addMsg("bot", t || "Hi! I'm Lumi, your home services concierge. What do you need today?");
    fetch(API_BASE + "/api/health").then(r => r.json())
      .then(j => {
        modeBadge.textContent = j.mode === "llm"
          ? (window.lumoraT ? window.lumoraT("bot_powered") : "powered by Claude")
          : (window.lumoraT ? window.lumoraT("bot_demo") : "demo mode");
      }).catch(() => {});
  }
  async function send(text) {
    busy = true; sendBtn.disabled = true;
    const typing = showTyping();
    try {
      const resp = await fetch(API_BASE + "/api/chat", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          session_id: sessionId,
          language: window.lumoraLang ? window.lumoraLang() : "en",
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
      addMsg("bot", "Sorry, I'm having trouble. WhatsApp us at +971 56 4020087.");
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
        const r = await fetch(API_BASE + "/api/chat/poll?session_id=" + encodeURIComponent(sessionId) +
                              "&since_id=" + since);
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
    cleanText = cleanText.replace(/\[\[\s*choices?\s*:\s*([^\]]+)\]\]/gi, (_, body) => {
      body.split(/\s*;\s*/).forEach(pair => {
        const m = pair.match(/^\s*(.+?)\s*=\s*(.+?)\s*$/);
        if (m) out.push({ label: m[1], send: m[2] });
        else if (pair.trim()) out.push({ label: pair.trim(), send: pair.trim() });
      });
      return "";
    }).replace(/\n{3,}/g, "\n\n").trim();
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
      if (!out.length && /\?\s*$/.test(cleanText) && /\b(confirm|proceed|continue|right|correct|sound good)\b/i.test(cleanText)) {
        out.push({ label: "✅ Yes", send: "Yes" });
        out.push({ label: "❌ No", send: "No" });
      }
    }
    return { cleanText, actions: out };
  }
  function addMsg(who, text, toolCalls, isAgent) {
    let cleanText = text;
    let actions = [];
    if (who === "bot") {
      const ex = extractActions(text, toolCalls);
      cleanText = ex.cleanText;
      actions = ex.actions;
    }
    const div = el("div", { class: "us-msg " + (who === "user" ? "user" : "bot") });
    div.innerHTML = formatMd(cleanText);
    if (isAgent) {
      const tag = el("div", { class: "us-tool-tag" }, "👤 Live agent");
      div.prepend(tag);
    } else if (toolCalls && toolCalls.length) {
      const names = [...new Set(toolCalls.map(t => t.name))].join(", ");
      const tag = el("div", { class: "us-tool-tag" }, "Used: " + names);
      div.appendChild(tag);
    }
    body.appendChild(div);
    if (who === "bot" && actions.length) {
      const wrap = el("div", { class: "us-actions" });
      actions.forEach(a => {
        const b = el("button", { type: "button" }, a.label);
        b.onclick = () => {
          [...wrap.querySelectorAll("button")].forEach(x => x.disabled = true);
          b.classList.add("us-action-picked");
          input.value = a.send;
          form.requestSubmit();
        };
        wrap.appendChild(b);
      });
      body.appendChild(wrap);
    }
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
  const micBtn = panel.querySelector(".us-mic");
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) micBtn.style.display = "none";
  else {
    const rec = new SR();
    rec.continuous = false; rec.interimResults = true;
    rec.onstart = () => { micBtn.classList.add("recording"); micBtn.textContent = "🔴"; };
    rec.onend = () => { micBtn.classList.remove("recording"); micBtn.textContent = "🎤"; };
    rec.onresult = (e) => {
      let txt = "";
      for (let i = 0; i < e.results.length; i++) txt += e.results[i][0].transcript;
      input.value = txt;
      if (e.results[e.results.length-1].isFinal) form.requestSubmit();
    };
    rec.onerror = () => { micBtn.classList.remove("recording"); micBtn.textContent = "🎤"; };
    micBtn.onclick = () => {
      const lang = (window.lumoraLang ? lumoraLang() : "en");
      rec.lang = { en: "en-US", ar: "ar-AE", hi: "hi-IN", tl: "fil-PH" }[lang] || "en-US";
      try { rec.start(); } catch {}
    };
  }
})();
