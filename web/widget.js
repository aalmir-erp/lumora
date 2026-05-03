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
      el("div", {},
        el("h3", {}, "Servia"),
        el("p", { class: "us-mode-line" }, "Concierge · 24×7 · 15 languages")),
      el("button", { class: "us-close", "aria-label": "Close" }, "×")),
    el("div", { class: "us-actions-bar" }),  // persistent action toolbar
    el("div", { class: "us-body" }),
    el("div", { class: "us-quickreplies" }),
    el("div", { class: "us-attach-preview", style: "display:none" }),
    el("form", { class: "us-input", autocomplete: "off" },
      el("button", { type: "button", class: "us-attach", "aria-label": "Attach photo", title: "Attach photo" }, "📎"),
      el("button", { type: "button", class: "us-mic", "aria-label": "Voice input", title: "Voice input" }, "🎤"),
      el("input", { type: "text", placeholder: "Type message, send a voice note 🎤 or photo 📎…", maxlength: "1000" }),
      el("button", { type: "submit", class: "us-send", "aria-label": "Send", title: "Send" }, "↑")),
    el("div", { class: "us-mode" }, ""));
  // Hidden file input for image attachment
  const fileInput = el("input", { type: "file", accept: "image/*",
    style: "display:none", capture: "environment" });
  panel.appendChild(fileInput);

  document.body.appendChild(launcher);
  document.body.appendChild(panel);

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
  // First tip 6s after page load, then every 25s
  setTimeout(() => { showTip(); tipTimer = setInterval(showTip, 25000); }, 6000);
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
  const previewWrap = panel.querySelector(".us-attach-preview");
  const modeBadge = panel.querySelector(".us-mode");
  const subtitle = panel.querySelector(".us-mode-line");

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
    if (!body.children.length) greet();
    setTimeout(() => input.focus(), 150);
    startPolling();
  };
  panel.querySelector(".us-close").onclick = () => panel.classList.remove("open");

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
      const resp = await fetch(API_BASE + "/api/chat", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text || (attachment ? "(photo)" : ""),
          session_id: sessionId,
          language: window.lumoraLang ? window.lumoraLang() : "en",
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
    cleanText = cleanText.replace(/\[\[\s*choices?\s*:\s*([^\]]+)\]\]/gi, (_, b) => {
      b.split(/\s*;\s*/).forEach(pair => {
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
      if (!out.length && /\?\s*$/.test(cleanText) &&
          /\b(confirm|proceed|continue|right|correct|sound good)\b/i.test(cleanText)) {
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
    body.scrollTop = body.scrollHeight;
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
    micBtn.onclick = () => {
      if (listening && rec) { try { rec.stop(); } catch {} return; }
      const lang = (window.lumoraLang ? lumoraLang() : "en");
      rec = new SR();
      rec.continuous = true;
      rec.interimResults = true;
      rec.lang = SR_LANG_MAP[lang] || "en-US";
      rec.onstart = () => { listening = true; micBtn.classList.add("recording");
                            micBtn.textContent = "🔴"; input.placeholder = "🎙 Listening… speak in any UAE language"; };
      rec.onend = () => { listening = false; micBtn.classList.remove("recording");
                          micBtn.textContent = "🎤"; input.placeholder = "Type your message…"; };
      let finalText = "";
      rec.onresult = (e) => {
        let interim = "";
        for (let i = e.resultIndex; i < e.results.length; i++) {
          const r = e.results[i];
          if (r.isFinal) finalText += r[0].transcript + " ";
          else interim += r[0].transcript;
        }
        input.value = (finalText + interim).trim();
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
