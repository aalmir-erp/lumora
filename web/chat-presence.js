/* Servia chat presence + persistence helper.
 *
 * Sits on top of the existing widget.js (which already persists session_id
 * in localStorage). This file adds three things widget.js doesn't:
 *
 * 1. "Online" green-pulse indicator on the chat FAB - communicates to the
 *    user that the bot is live and ready, even before they click.
 * 2. "Bot is typing" / "Servia is composing..." indicator above the FAB
 *    when the bot is mid-reply - same idea as WhatsApp / Messenger.
 * 3. Chat-open-state-across-pages: if the user had the chat panel OPEN
 *    when they navigated, it auto-reopens on the next page. Also remembers
 *    the unread count.
 *
 * This file is loaded on every public page via the lazy-loader chain.
 * Idempotent - safe if widget.js hasn't loaded yet (we wait for it).
 */
(function () {
  if (window.__servia_chat_presence) return;
  window.__servia_chat_presence = true;

  const OPEN_KEY    = "servia.chat.open.v1";
  const UNREAD_KEY  = "servia.chat.unread.v1";
  const TYPING_KEY  = "servia.chat.typing.v1";

  // Inject CSS for the dot + typing pill - small + non-invasive.
  const css = document.createElement("style");
  css.textContent = `
    .servia-chat-online {
      position:fixed; bottom:14px; right:78px; z-index:99;
      background:#fff; color:#0F172A;
      padding:6px 12px 6px 10px; border-radius:999px;
      font-size:11.5px; font-weight:700;
      display:inline-flex; gap:6px; align-items:center;
      box-shadow:0 6px 18px rgba(15,23,42,.18);
      pointer-events:none;
      opacity:0; transform:translateX(8px);
      transition:opacity .25s, transform .25s;
    }
    .servia-chat-online.show { opacity:1; transform:translateX(0); }
    .servia-chat-online .dot {
      width:8px; height:8px; border-radius:50%;
      background:#10B981; box-shadow:0 0 0 0 rgba(16,185,129,.6);
      animation:servia-presence-pulse 1.6s ease-out infinite;
    }
    @keyframes servia-presence-pulse {
      0%   { box-shadow:0 0 0 0 rgba(16,185,129,.6); }
      70%  { box-shadow:0 0 0 8px rgba(16,185,129,0); }
      100% { box-shadow:0 0 0 0 rgba(16,185,129,0); }
    }
    .servia-chat-online .lbl em { font-style:normal; color:#0F766E; }
    .servia-chat-online .typing-dots {
      display:inline-flex; gap:2px; vertical-align:middle; margin-inline-start:4px;
    }
    .servia-chat-online .typing-dots span {
      width:4px; height:4px; background:#94A3B8; border-radius:50%;
      animation:servia-typing-dot 1.2s ease-in-out infinite;
    }
    .servia-chat-online .typing-dots span:nth-child(2) { animation-delay:.15s; }
    .servia-chat-online .typing-dots span:nth-child(3) { animation-delay:.3s; }
    @keyframes servia-typing-dot { 0%,80%,100% { opacity:.3 } 40% { opacity:1 } }
    /* Position higher on mobile so it doesn't collide with mobile-nav. */
    @media (max-width:720px) {
      .servia-chat-online { bottom:80px; right:72px; font-size:11px; padding:5px 10px 5px 8px; }
    }
    @media (prefers-reduced-motion:reduce) {
      .servia-chat-online .dot { animation:none; box-shadow:0 0 0 2px rgba(16,185,129,.3); }
      .servia-chat-online .typing-dots span { animation:none; opacity:.6; }
    }
  `;
  document.head.appendChild(css);

  // Build the indicator badge. It's purely informational - no clicks, the
  // existing chat FAB handles the click.
  const badge = document.createElement("div");
  badge.className = "servia-chat-online";
  badge.setAttribute("aria-live", "polite");
  badge.innerHTML = `<span class="dot" aria-hidden="true"></span><span class="lbl"><em>Servia</em> · Online</span>`;
  document.body.appendChild(badge);

  function setStatus(state) {
    const lbl = badge.querySelector(".lbl");
    if (state === "typing") {
      lbl.innerHTML = `<em>Servia</em> · typing<span class="typing-dots"><span></span><span></span><span></span></span>`;
    } else if (state === "unread") {
      const n = parseInt(localStorage.getItem(UNREAD_KEY) || "0") || 0;
      lbl.innerHTML = n > 0
        ? `<em>Servia</em> · ${n} new`
        : `<em>Servia</em> · Online`;
    } else {
      lbl.innerHTML = `<em>Servia</em> · Online`;
    }
  }

  // Show the badge once the chat FAB exists on the page (widget.js drops one
  // in). Wait up to 8s; if no FAB, the badge stays hidden (doesn't make sense
  // without a chat surface).
  let attempts = 0;
  function waitForChatFab() {
    const fab = document.querySelector(".us-launcher, .servia-chat-fab, [data-chat-launcher]");
    if (fab) {
      badge.classList.add("show");
      setStatus("unread");
      // Reflect open state from localStorage. If the chat was OPEN on the
      // previous page, auto-click the FAB so the panel restores.
      try {
        const wasOpen = localStorage.getItem(OPEN_KEY) === "1";
        if (wasOpen && !document.querySelector(".us-panel.open, .servia-chat-panel.open")) {
          // Defer slightly so widget.js has time to wire its click handlers.
          setTimeout(() => fab.click(), 600);
        }
      } catch (_) {}
      return;
    }
    if (++attempts < 80) setTimeout(waitForChatFab, 100);  // wait up to 8s
  }
  waitForChatFab();

  // Listen for events the widget fires (or fall back to DOM watching).
  // widget.js currently emits no custom events — observe the panel directly
  // (only once it exists) and debounce, so heavy DOM rewrites by other tools
  // (e.g. Google Translate translating every text node on lang-switch) don't
  // pummel us with thousands of synchronous callbacks.
  let lastState = "";
  let debounceTimer = null;
  function evalPanelState() {
    debounceTimer = null;
    const panel = document.querySelector(".us-panel, .servia-chat-panel");
    if (!panel) return;
    const isOpen = panel.classList.contains("open");
    const typing = panel.querySelector(".us-typing, .servia-chat-typing");
    const typingActive = typing && getComputedStyle(typing).display !== "none";
    const state = (typingActive ? "T" : "_") + (isOpen ? "O" : "_");
    if (state === lastState) return;
    lastState = state;
    try { localStorage.setItem(OPEN_KEY, isOpen ? "1" : "0"); } catch (_) {}
    if (typingActive) {
      setStatus("typing");
    } else if (isOpen) {
      try { localStorage.setItem(UNREAD_KEY, "0"); } catch (_) {}
      setStatus("online");
    } else {
      setStatus("unread");
    }
  }
  function scheduleEval() {
    if (debounceTimer) return;
    debounceTimer = setTimeout(evalPanelState, 200);
  }

  // Wait for the panel to exist, then observe ONLY the panel (not the whole
  // body subtree). This is dramatically cheaper and immune to Google Translate
  // mutating every text node in <body> on language change.
  let panelObserver = null;
  function attachPanelObserver() {
    if (panelObserver) return;
    const panel = document.querySelector(".us-panel, .servia-chat-panel");
    if (!panel) return;
    panelObserver = new MutationObserver(scheduleEval);
    panelObserver.observe(panel, { attributes:true, attributeFilter:["class","style"], childList:true, subtree:false });
    // Also observe the typing indicator container if present.
    const typing = panel.querySelector(".us-typing, .servia-chat-typing");
    if (typing) panelObserver.observe(typing, { attributes:true, attributeFilter:["style","class"] });
    evalPanelState();
  }
  // Poll for the panel for up to 12s, then stop. Cheap.
  let panelAttempts = 0;
  (function waitForPanel() {
    if (panelObserver) return;
    attachPanelObserver();
    if (!panelObserver && ++panelAttempts < 60) setTimeout(waitForPanel, 200);
  })();

  // Listen for the conv.js custom event so we can flag unread without
  // depending on widget.js internals. When a bot reply arrives while panel
  // is closed, increment unread.
  window.addEventListener("servia:bot-reply", () => {
    if (!document.querySelector(".us-panel.open, .servia-chat-panel.open")) {
      try {
        const n = (parseInt(localStorage.getItem(UNREAD_KEY) || "0") || 0) + 1;
        localStorage.setItem(UNREAD_KEY, String(n));
        setStatus("unread");
      } catch (_) {}
    }
  });
})();
