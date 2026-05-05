/* Servia site-wide command palette.
 *
 * Press Cmd/Ctrl+K (or just / on most pages) to open a centred modal with
 * the same instant-search index used by /search.html. Pick a result to
 * navigate. Hit Tab to flip into AI-mode and chat with the concierge.
 *
 * Loaded via <script src="/search-widget.js" defer> on every page that
 * already includes /conv.js. Idempotent — multiple includes are safe.
 */
(function () {
  if (window.__servia_search_palette) return;
  window.__servia_search_palette = true;

  const RECENT_KEY = "servia.search.recent.v1";
  const GPT_URL = "https://chatgpt.com/g/g-69f9f43427c88191bca61c0fe0977b53-servia-uae-helper";

  // -------- Static index (synced with /search.html STATIC list) --------
  const STATIC = [
    {kind:"page",  title:"All services",          body:"32 services UAE catalogue",                url:"/services.html"},
    {kind:"page",  title:"Book a service",        body:"book online quote pay schedule",           url:"/book.html"},
    {kind:"page",  title:"Coverage map",          body:"areas emirates covered live",              url:"/coverage.html"},
    {kind:"page",  title:"Videos",                body:"how-to explainer mascot",                  url:"/videos.html"},
    {kind:"page",  title:"Gallery",               body:"photos before after jobs",                 url:"/gallery.html"},
    {kind:"page",  title:"Servia Journal (Blog)", body:"articles tips guides",                     url:"/blog"},
    {kind:"page",  title:"Contact us",            body:"whatsapp email support",                   url:"/contact.html"},
    {kind:"page",  title:"Ambassador rewards",    body:"refer earn discount tier",                 url:"/share-rewards.html"},
    {kind:"page",  title:"FAQ",                   body:"questions answers pricing payment",        url:"/faq.html"},
    {kind:"page",  title:"Install Servia app",    body:"PWA installable iOS Android desktop GPT",  url:"/install.html"},
    {kind:"page",  title:"My account",            body:"bookings invoices saved addresses",        url:"/me.html"},
    {kind:"page",  title:"Cart",                  body:"checkout multi-service",                   url:"/cart.html"},
    {kind:"area", title:"Dubai",          body:"jumeirah marina jlt downtown business bay",  url:"/area.html?city=dubai"},
    {kind:"area", title:"Abu Dhabi",      body:"khalifa city yas reem saadiyat raha",        url:"/area.html?city=abu-dhabi"},
    {kind:"area", title:"Sharjah",        body:"al khan al majaz nahda muwaileh",            url:"/area.html?city=sharjah"},
    {kind:"area", title:"Ajman",          body:"al nuaimiya rashidiya rawda corniche",       url:"/area.html?city=ajman"},
    {kind:"area", title:"Ras Al Khaimah", body:"al hamra mina al arab al nakheel",           url:"/area.html?city=ras-al-khaimah"},
    {kind:"area", title:"Umm Al Quwain",  body:"al ramlah al salamah uaq marina",            url:"/area.html?city=umm-al-quwain"},
    {kind:"area", title:"Fujairah",       body:"dibba al faseel sakamkam",                   url:"/area.html?city=fujairah"},
  ];

  let docs = STATIC.slice();
  let indexLoaded = false;

  // -------- DOM --------
  const overlay = document.createElement("div");
  overlay.id = "servia-cmdk";
  overlay.innerHTML = `
    <div class="cmdk-back" data-close></div>
    <div class="cmdk-shell" role="dialog" aria-modal="true" aria-label="Search Servia">
      <div class="cmdk-input-row">
        <span class="cmdk-ico" aria-hidden="true">🔍</span>
        <input type="search" id="cmdk-q" placeholder="Search Servia… (Tab for AI, / for tips, Esc to close)" autocomplete="off" aria-label="Search">
        <button class="cmdk-mic" id="cmdk-mic" type="button" title="Voice" aria-label="Voice search">🎤</button>
        <button class="cmdk-close" data-close type="button" aria-label="Close">✕</button>
      </div>
      <div class="cmdk-tabs">
        <button class="cmdk-tab active" data-mode="search" type="button">🔍 Search</button>
        <button class="cmdk-tab"        data-mode="ai"     type="button">✨ Ask AI</button>
        <span class="cmdk-spacer"></span>
        <a class="cmdk-link" href="${GPT_URL}" target="_blank" rel="noopener" data-event="open_chatgpt_gpt">🚀 ChatGPT GPT ↗</a>
        <a class="cmdk-link" href="/search.html">Full search ↗</a>
      </div>
      <div class="cmdk-results" id="cmdk-results"></div>
      <div class="cmdk-ai" id="cmdk-ai" hidden>
        <div class="cmdk-msg bot">Hi! Ask me anything about UAE home services. I'll help you find a service, get a quote, or book.</div>
      </div>
      <div class="cmdk-foot">
        <span><kbd>↑</kbd><kbd>↓</kbd> navigate</span>
        <span><kbd>↵</kbd> select</span>
        <span><kbd>Tab</kbd> flip mode</span>
        <span><kbd>Esc</kbd> close</span>
      </div>
    </div>`;

  const css = document.createElement("style");
  css.textContent = `
    #servia-cmdk { position:fixed; inset:0; z-index:99998; display:none; align-items:flex-start; justify-content:center; padding:14vh 16px 16px; }
    #servia-cmdk.open { display:flex; animation:cmdkfade .15s ease-out }
    @keyframes cmdkfade { from { opacity:0 } to { opacity:1 } }
    .cmdk-back { position:absolute; inset:0; background:rgba(15,23,42,.5); backdrop-filter:blur(4px); }
    .cmdk-shell { position:relative; width:100%; max-width:640px; background:#fff; border-radius:16px;
      box-shadow:0 24px 80px rgba(15,23,42,.4); overflow:hidden;
      animation:cmdkin .18s cubic-bezier(.2,.9,.3,1.3) }
    @keyframes cmdkin { from { transform:translateY(-12px) scale(.97); opacity:0 } to { transform:translateY(0) scale(1); opacity:1 } }
    .cmdk-input-row { display:flex; align-items:center; gap:8px; padding:12px 14px; border-bottom:1px solid #E2E8F0 }
    .cmdk-ico { font-size:18px; color:#64748B }
    #cmdk-q { flex:1; border:0; outline:none; font-size:16px; padding:8px 4px; background:transparent; color:#0F172A; min-width:0 }
    .cmdk-mic, .cmdk-close { background:transparent; border:0; width:32px; height:32px; border-radius:8px; cursor:pointer; font-size:14px; color:#475569; display:flex; align-items:center; justify-content:center }
    .cmdk-mic:hover, .cmdk-close:hover { background:#F1F5F9; color:#0F766E }
    .cmdk-mic.listening { background:#DC2626; color:#fff }
    .cmdk-tabs { display:flex; gap:6px; padding:8px 14px; border-bottom:1px solid #F1F5F9; align-items:center; background:#FAFAFA }
    .cmdk-tab { background:transparent; border:0; font-size:12.5px; font-weight:700; padding:5px 10px; border-radius:6px; cursor:pointer; color:#475569 }
    .cmdk-tab.active { background:#0F766E; color:#fff }
    .cmdk-spacer { flex:1 }
    .cmdk-link { font-size:11.5px; color:#0F766E; font-weight:700; text-decoration:none; padding:5px 10px; border-radius:6px }
    .cmdk-link:hover { background:#F0FDFA }
    .cmdk-results { max-height:50vh; overflow-y:auto; padding:6px 0 }
    .cmdk-ai { max-height:50vh; overflow-y:auto; padding:14px; display:flex; flex-direction:column; gap:8px }
    .cmdk-foot { display:flex; gap:14px; padding:8px 14px; border-top:1px solid #E2E8F0; font-size:11px; color:#64748B; background:#FAFAFA; flex-wrap:wrap }
    .cmdk-foot kbd { background:#fff; border:1px solid #E2E8F0; border-radius:4px; padding:1px 5px; font-family:ui-monospace,monospace; font-size:10px; color:#0F172A; margin-right:3px }
    .cmdk-section { font-size:10.5px; font-weight:800; letter-spacing:.08em; text-transform:uppercase; color:#94A3B8; padding:8px 16px 4px }
    .cmdk-row { display:flex; align-items:center; gap:10px; padding:9px 16px; cursor:pointer; text-decoration:none; color:#0F172A; transition:background .1s }
    .cmdk-row:hover, .cmdk-row.sel { background:#F0FDFA; outline:none }
    .cmdk-row .icon { font-size:16px; flex-shrink:0; width:22px; text-align:center }
    .cmdk-row .body { flex:1; min-width:0 }
    .cmdk-row .ttl { font-size:13.5px; font-weight:700; line-height:1.3; overflow:hidden; text-overflow:ellipsis; white-space:nowrap }
    .cmdk-row .sub { font-size:11.5px; color:#64748B; line-height:1.3; overflow:hidden; text-overflow:ellipsis; white-space:nowrap }
    .cmdk-row .kind { font-size:9.5px; font-weight:800; letter-spacing:.04em; text-transform:uppercase; padding:2px 7px; border-radius:999px; background:#F1F5F9; color:#475569; flex-shrink:0 }
    .cmdk-row .kind.service { background:#ECFDF5; color:#065F46 }
    .cmdk-row .kind.area    { background:#EFF6FF; color:#1E40AF }
    .cmdk-row .kind.blog    { background:#FEF3C7; color:#92400E }
    .cmdk-row .kind.faq     { background:#F3E8FF; color:#5B21B6 }
    .cmdk-row .kind.video   { background:#FCE7F3; color:#9F1239 }
    .cmdk-row mark          { background:#FEF3C7; color:#7C2D12; padding:0 2px; border-radius:3px }
    .cmdk-msg { padding:11px 14px; border-radius:14px; font-size:14px; line-height:1.5; max-width:92% }
    .cmdk-msg.user { background:#0F766E; color:#fff; align-self:flex-end; border-bottom-right-radius:4px }
    .cmdk-msg.bot  { background:#F1F5F9; color:#0F172A; align-self:flex-start; border-bottom-left-radius:4px }
    .cmdk-msg .typing { display:inline-flex; gap:3px }
    .cmdk-msg .typing span { width:5px; height:5px; background:#94A3B8; border-radius:50%; animation:cmdkdot 1.2s ease-in-out infinite }
    .cmdk-msg .typing span:nth-child(2) { animation-delay:.15s }
    .cmdk-msg .typing span:nth-child(3) { animation-delay:.3s }
    @keyframes cmdkdot { 0%,80%,100% { opacity:.3 } 40% { opacity:1 } }
    .cmdk-empty { text-align:center; padding:22px 16px; color:#64748B; font-size:13px }
    .cmdk-empty a { color:#5B21B6; font-weight:700; text-decoration:none }
    .cmdk-fab { position:fixed; bottom:152px; right:18px; z-index:90; width:48px; height:48px; border-radius:50%;
      background:#fff; border:1px solid #E2E8F0; box-shadow:0 8px 22px rgba(15,23,42,.18);
      cursor:pointer; font-size:18px; color:#0F766E; display:flex; align-items:center; justify-content:center;
      transition:transform .15s }
    .cmdk-fab:hover { transform:scale(1.06); box-shadow:0 12px 28px rgba(15,118,110,.3) }
    @media (max-width:720px) { .cmdk-fab { bottom:140px; right:14px; width:44px; height:44px; font-size:16px } }
  `;
  document.head.appendChild(css);
  document.body.appendChild(overlay);

  const fab = document.createElement("button");
  fab.className = "cmdk-fab"; fab.title = "Search Servia (Cmd/Ctrl+K)"; fab.setAttribute("aria-label", "Open search palette");
  fab.textContent = "🔍";
  fab.addEventListener("click", () => open());
  document.body.appendChild(fab);

  const qInput = document.getElementById("cmdk-q");
  const resultsDiv = document.getElementById("cmdk-results");
  const aiDiv = document.getElementById("cmdk-ai");
  const tabs = overlay.querySelectorAll(".cmdk-tab");
  const micBtn = document.getElementById("cmdk-mic");
  let mode = "search";
  let selectedIdx = 0;
  let aiSession = null;

  function isOpen(){ return overlay.classList.contains("open"); }
  function open(){
    if (isOpen()) return;
    overlay.classList.add("open");
    qInput.value = "";
    setMode("search");
    render();
    setTimeout(() => qInput.focus(), 50);
    document.body.style.overflow = "hidden";
  }
  function close(){
    overlay.classList.remove("open");
    document.body.style.overflow = "";
  }
  overlay.querySelectorAll("[data-close]").forEach(el => el.addEventListener("click", close));

  function setMode(next){
    mode = next;
    tabs.forEach(t => t.classList.toggle("active", t.dataset.mode === next));
    aiDiv.hidden = next !== "ai";
    resultsDiv.hidden = next === "ai";
    qInput.placeholder = next === "ai"
      ? "Ask anything: 'I need a cleaner in JVC tomorrow morning'"
      : "Search Servia… (Tab for AI, ↑↓ navigate, ↵ open)";
    if (next === "search") render();
  }
  tabs.forEach(t => t.addEventListener("click", () => setMode(t.dataset.mode)));

  function escapeRe(s){ return (s||"").replace(/[.*+?^${}()|[\]\\]/g,'\\$&'); }
  function score(doc, terms){
    if (!terms.length) return 0;
    const t = (doc.title||"").toLowerCase(); const b = (doc.body||"").toLowerCase();
    let s = 0;
    for (const term of terms) {
      const re = new RegExp(`\\b${escapeRe(term)}\\b`);
      if (re.test(t)) s += 12; else if (t.includes(term)) s += 6;
      if (re.test(b)) s += 3; else if (b.includes(term)) s += 1;
    }
    return s;
  }
  function highlight(text, terms){
    if (!terms.length || !text) return (text||"").replace(/</g,"&lt;");
    let out = (text||"").replace(/</g,"&lt;");
    for (const term of terms) {
      if (!term || term.length < 2) continue;
      out = out.replace(new RegExp("("+escapeRe(term)+")","ig"), "<mark>$1</mark>");
    }
    return out;
  }
  function loadRecent(){ try { return JSON.parse(localStorage.getItem(RECENT_KEY)||"[]"); } catch(_) { return []; } }
  function pushRecent(query){
    if (!query || query.length < 2) return;
    let r = loadRecent().filter(x => x.toLowerCase() !== query.toLowerCase());
    r.unshift(query);
    try { localStorage.setItem(RECENT_KEY, JSON.stringify(r.slice(0,8))); } catch(_) {}
  }

  let rendered = [];   // currently-shown rows (for keyboard nav)

  function render(){
    if (mode !== "search") return;
    const query = qInput.value.trim();
    const terms = query.toLowerCase().split(/\s+/).filter(Boolean);

    // Empty state: show recent + suggested actions
    if (!terms.length) {
      const recent = loadRecent();
      const sections = [];
      if (recent.length) {
        sections.push(`<div class="cmdk-section">Recent</div>`);
        sections.push(...recent.map(r => `<a class="cmdk-row" data-q="${r.replace(/"/g,'&quot;')}" href="#"><span class="icon">⏱</span><div class="body"><div class="ttl">${r.replace(/</g,'&lt;')}</div><div class="sub">Run this search again</div></div></a>`));
      }
      sections.push(`<div class="cmdk-section">Quick actions</div>`);
      const quick = [
        ["📋", "All services",  "/services.html",      "Browse the full 32-service catalog"],
        ["➕", "Book a service","/book.html",          "Pick + pay in 60s"],
        ["🗺️", "Coverage map",   "/coverage.html",      "Live map of all 7 emirates"],
        ["🚀", "Open ChatGPT",  GPT_URL,               "Talk to Servia GPT in ChatGPT"],
        ["📲", "Install app",   "/install.html",       "Install Servia on your phone or desktop"],
        ["💬", "Contact us",    "/contact.html",       "WhatsApp / email"],
      ];
      sections.push(...quick.map(([i, t, u, s]) => `<a class="cmdk-row" href="${u}"${u.startsWith("http")?' target="_blank" rel="noopener"':''}><span class="icon">${i}</span><div class="body"><div class="ttl">${t}</div><div class="sub">${s}</div></div></a>`));
      resultsDiv.innerHTML = sections.join("");
      rendered = Array.from(resultsDiv.querySelectorAll(".cmdk-row"));
      selectedIdx = 0;
      updateSel();
      bindRecentClicks();
      return;
    }

    let scored = docs.map(d => ({...d, _s: score(d, terms)})).filter(d => d._s > 0);
    scored.sort((a,b) => b._s - a._s);
    const top = scored.slice(0, 16);
    if (!top.length) {
      resultsDiv.innerHTML = `<div class="cmdk-empty">No results. Switch to <b>Ask AI</b> (Tab) or
        <a href="${GPT_URL}" target="_blank" rel="noopener">ask Servia GPT</a>.</div>`;
      rendered = []; return;
    }
    const ICONS = {service:"✨", area:"📍", blog:"📰", faq:"❓", video:"🎬", page:"📄"};
    resultsDiv.innerHTML = top.map(d => `
      <a class="cmdk-row" href="${d.url}"${d.url.startsWith("/api/videos/")?' target="_blank"':''}>
        <span class="icon">${ICONS[d.kind] || "📄"}</span>
        <div class="body">
          <div class="ttl">${highlight(d.title, terms)}</div>
          <div class="sub">${highlight(d.body || "", terms).slice(0, 90)}</div>
        </div>
        <span class="kind ${d.kind}">${d.kind}</span>
      </a>`).join("");
    rendered = Array.from(resultsDiv.querySelectorAll(".cmdk-row"));
    selectedIdx = 0;
    updateSel();
  }

  function bindRecentClicks(){
    resultsDiv.querySelectorAll(".cmdk-row[data-q]").forEach(r => r.addEventListener("click", e => {
      e.preventDefault();
      qInput.value = r.dataset.q;
      render(); qInput.focus();
    }));
  }
  function updateSel(){
    rendered.forEach((r, i) => r.classList.toggle("sel", i === selectedIdx));
    const sel = rendered[selectedIdx];
    if (sel) sel.scrollIntoView({block: "nearest"});
  }

  // ---------- AI mode (calls /api/chat) ----------
  async function aiSend(text){
    if (!text || !text.trim()) return;
    aiDiv.insertAdjacentHTML("beforeend", `<div class="cmdk-msg user">${text.replace(/</g,'&lt;')}</div>`);
    aiDiv.insertAdjacentHTML("beforeend", `<div class="cmdk-msg bot" id="cmdk-pending"><span class="typing"><span></span><span></span><span></span></span></div>`);
    const pending = document.getElementById("cmdk-pending");
    aiDiv.scrollTop = aiDiv.scrollHeight;
    try {
      const r = await fetch("/api/chat", {
        method:"POST", headers:{"content-type":"application/json"},
        body: JSON.stringify({ message: text, session_id: aiSession || undefined,
                               language: (navigator.language||"en").slice(0,2) })
      });
      const j = await r.json();
      aiSession = j.session_id || aiSession;
      pending.id = ""; pending.textContent = j.text || j.detail || "Sorry, no response.";
    } catch (e) {
      pending.id = ""; pending.textContent = "Couldn't reach Servia AI right now. Try /contact.html or open Servia GPT.";
    }
    pushRecent(text);
    aiDiv.scrollTop = aiDiv.scrollHeight;
  }

  // ---------- Wire input ----------
  qInput.addEventListener("input", () => { if (mode === "search") render(); });
  qInput.addEventListener("keydown", e => {
    if (e.key === "Escape")    { e.preventDefault(); close(); return; }
    if (e.key === "Tab" && !e.shiftKey) {
      e.preventDefault(); setMode(mode === "search" ? "ai" : "search"); return;
    }
    if (mode === "ai" && e.key === "Enter") {
      e.preventDefault();
      const v = qInput.value.trim();
      if (v) { aiSend(v); qInput.value = ""; }
      return;
    }
    if (mode === "search") {
      if (e.key === "ArrowDown") { e.preventDefault(); if (selectedIdx < rendered.length - 1) selectedIdx++; updateSel(); }
      else if (e.key === "ArrowUp") { e.preventDefault(); if (selectedIdx > 0) selectedIdx--; updateSel(); }
      else if (e.key === "Enter") {
        e.preventDefault();
        const sel = rendered[selectedIdx];
        if (sel) {
          if (sel.dataset.q) { qInput.value = sel.dataset.q; render(); qInput.focus(); }
          else if (sel.target === "_blank") { window.open(sel.href, "_blank"); }
          else { pushRecent(qInput.value.trim()); location.href = sel.href; }
        }
      }
    }
  });

  // ---------- Voice input ----------
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (Recognition) {
    const rec = new Recognition();
    rec.continuous = false; rec.interimResults = true;
    rec.lang = (navigator.language || "en-US");
    let listening = false;
    micBtn.addEventListener("click", () => { if (listening) rec.stop(); else { try { rec.start(); } catch(_){} } });
    rec.onstart = () => { listening = true; micBtn.classList.add("listening"); micBtn.textContent = "🔴"; };
    rec.onend   = () => { listening = false; micBtn.classList.remove("listening"); micBtn.textContent = "🎤"; };
    rec.onerror = () => { listening = false; micBtn.classList.remove("listening"); micBtn.textContent = "🎤"; };
    rec.onresult = e => {
      qInput.value = Array.from(e.results).map(r => r[0].transcript).join("");
      if (mode === "search") render();
      else if (e.results[0].isFinal) { const v = qInput.value.trim(); if (v) { aiSend(v); qInput.value = ""; } }
    };
  } else {
    micBtn.style.display = "none";
  }

  // ---------- Lazy load full index when palette opens ----------
  async function lazyLoadIndex(){
    if (indexLoaded) return; indexLoaded = true;
    try {
      const tasks = [
        fetch("/api/services").then(r=>r.json()).then(j => (j.services||[]).map(s => ({
          kind:"service", title:s.name, body:(s.description||""),
          url:`/service.html?id=${s.id}` }))).catch(()=>[]),
        fetch("/api/blog/list?limit=80").then(r=>r.ok?r.json():null).then(j => j ? (j.posts||[]).map(p => ({
          kind:"blog", title:p.topic||p.slug, body:(p.emirate||""),
          url:`/blog/${p.slug}` })) : []).catch(()=>[]),
      ];
      const r = await Promise.allSettled(tasks);
      docs = [...STATIC, ...r.flatMap(x => x.status === "fulfilled" ? x.value : [])];
    } catch(_) {}
  }

  // ---------- Global key bindings ----------
  document.addEventListener("keydown", e => {
    // Cmd/Ctrl + K opens
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      if (isOpen()) close(); else { open(); lazyLoadIndex(); }
    }
    // / opens (when not focused on an input)
    else if (e.key === "/" && !isOpen()) {
      const tag = (document.activeElement?.tagName || "").toLowerCase();
      if (tag !== "input" && tag !== "textarea" && tag !== "select") {
        e.preventDefault(); open(); lazyLoadIndex();
      }
    }
  });
})();
