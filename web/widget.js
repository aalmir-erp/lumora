/* Lumora chatbot widget — multi-language, live-agent aware. */
(function () {
  const script = document.currentScript || document.querySelector("script[data-api-base]");
  const API_BASE = (script && script.dataset.apiBase) ||
                   (window.LUMORA_API_BASE || window.location.origin);
  const SESSION_KEY = "lumora.chat.sid";
  const SINCE_KEY = "lumora.chat.since";

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
        el("h3", {}, "Lumora"),
        el("p", { class: "us-mode-line" }, "your home services concierge")),
      el("button", { class: "us-close", "aria-label": "Close" }, "×")),
    el("div", { class: "us-body" }),
    el("div", { class: "us-quickreplies" }),
    el("form", { class: "us-input", autocomplete: "off" },
      el("input", { type: "text", placeholder: "Type your message…", required: "true", maxlength: "1000" }),
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

  // i18n integration
  function applyI18n() {
    const t = (k, d) => (window.lumoraT ? window.lumoraT(k, d) : d);
    input.placeholder = t("bot_placeholder", "Type your message…");
    sendBtn.textContent = t("bot_send", "Send");
    quickWrap.innerHTML = "";
    const qs = QR_FALLBACK;
    qs.forEach((q) => {
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
    await send(text);
  });

  // Auto-open if URL has ?chat=1
  if (new URLSearchParams(location.search).get("chat") === "1") setTimeout(() => launcher.click(), 400);

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
      addMsg("bot", "Sorry, I'm having trouble. WhatsApp us at +971 56 6900255.");
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
          // We already render our own user messages and bot replies; only render
          // agent-injected assistant messages here.
          if (m.role === "assistant" && m.agent_handled) {
            addMsg("bot", m.content, null, true);
          }
        }
      } catch {}
    }, 3500);
  }

  function addMsg(who, text, toolCalls, isAgent) {
    const div = el("div", { class: "us-msg " + (who === "user" ? "user" : "bot") });
    div.innerHTML = formatMd(text);
    if (isAgent) {
      const tag = el("div", { class: "us-tool-tag" }, "👤 Live agent");
      div.prepend(tag);
    } else if (toolCalls && toolCalls.length) {
      const tag = el("div", { class: "us-tool-tag" },
        "Used: " + toolCalls.map(t => t.name).join(", "));
      div.appendChild(tag);
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
})();
