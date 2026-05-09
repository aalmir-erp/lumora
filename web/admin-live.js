/* v1.24.55 — Servia Admin Live PWA frontend.
   Polls /api/admin/live/feed every 4s, updates the visitor + chat lists,
   plays sound on new events, and on first run subscribes the browser to
   Web Push so phone (and paired Wear OS / Apple Watch) gets native
   notifications even when the PWA is closed.
*/
'use strict';

const TOKEN_KEY = "servia.admin.token";
const SOUND_KEY = "servia.admin.sound_on";
const POLL_MS   = 4000;

let token = localStorage.getItem(TOKEN_KEY) || "";
let soundOn = (localStorage.getItem(SOUND_KEY) ?? "1") === "1";
let pollSince = "";
let openSid   = null;
let seenVis   = new Set();
let seenMsgs  = new Set();
let visitors  = [];
let chats     = [];

const $ = id => document.getElementById(id);

/* ----------------------------- login ----------------------------- */
function adminLogin() {
  const t = ($("token-input").value || "").trim();
  if (!t) return alert("Paste the admin token");
  // Probe — just hit a cheap admin endpoint
  fetch("/api/admin/live/active-chats", {
    headers: { Authorization: "Bearer " + t }
  }).then(r => {
    if (r.ok) {
      localStorage.setItem(TOKEN_KEY, t);
      token = t;
      bootApp();
    } else {
      alert("Token rejected (HTTP " + r.status + "). Check ADMIN_TOKEN in Railway.");
    }
  }).catch(e => alert("Network error: " + e.message));
}
function logout() {
  if (!confirm("Sign out and clear token?")) return;
  localStorage.removeItem(TOKEN_KEY);
  location.reload();
}
function adm(path, init = {}) {
  init.headers = Object.assign({}, init.headers || {}, {
    Authorization: "Bearer " + token,
  });
  if (init.body && typeof init.body !== "string") {
    init.body = JSON.stringify(init.body);
    init.headers["Content-Type"] = "application/json";
  }
  return fetch(path, init).then(r => r.ok ? r.json() : Promise.reject(r));
}

/* ----------------------------- boot ----------------------------- */
function bootApp() {
  $("login").style.display = "none";
  $("app").style.display = "";
  refreshSoundUi();
  // Tabs
  document.querySelectorAll("#tabs button").forEach(b => {
    b.onclick = () => {
      document.querySelectorAll("#tabs button").forEach(x => x.classList.remove("active"));
      b.classList.add("active");
      const t = b.dataset.tab;
      $("visitors-panel").hidden = t !== "visitors";
      $("chats-panel").hidden = t !== "chats";
    };
  });
  // Service worker (for Web Push)
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/admin-live-sw.js").catch(e =>
      console.warn("[push] sw register failed:", e));
  }
  // Initial load + start polling
  loadInitial();
  setInterval(poll, POLL_MS);
  // Send/back keyboard shortcut
  $("reply-input").addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendReply(); }
  });
}

async function loadInitial() {
  try {
    const [v, c] = await Promise.all([
      adm("/api/admin/live/visitors"),
      adm("/api/admin/live/active-chats"),
    ]);
    visitors = v.visitors || [];
    chats = c.chats || [];
    visitors.forEach(x => seenVis.add(x.visitor_id));
    chats.forEach(x => seenMsgs.add(x.session_id + "@" + (x.last_at || "")));
    renderVisitors(); renderChats();
    pollSince = new Date().toISOString();
  } catch (e) {
    setStatus(false);
  }
}

/* ----------------------------- polling ----------------------------- */
async function poll() {
  try {
    const url = "/api/admin/live/feed?since=" + encodeURIComponent(pollSince);
    const j = await adm(url);
    pollSince = j.until || pollSince;
    let newVis = false, newMsg = false;
    (j.new_visitors || []).forEach(v => {
      if (!seenVis.has(v.visitor_id)) {
        seenVis.add(v.visitor_id);
        newVis = true;
        // Re-fetch full visitor list to get parsed UA + traffic source
      }
    });
    (j.new_messages || []).forEach(m => {
      const k = m.session_id + "@" + m.created_at;
      if (!seenMsgs.has(k)) {
        seenMsgs.add(k);
        newMsg = true;
      }
    });
    if (newVis || newMsg) {
      // refresh both panels
      const [v, c] = await Promise.all([
        adm("/api/admin/live/visitors"),
        adm("/api/admin/live/active-chats"),
      ]);
      visitors = v.visitors || [];
      chats = c.chats || [];
      renderVisitors(); renderChats();
      if (newMsg)  beep("chat");
      else if (newVis) beep("visitor");
      // If the open chat got a new message, refresh it too
      if (openSid && j.new_messages.find(m => m.session_id === openSid)) {
        loadChatDetail(openSid);
      }
    }
    setStatus(true);
    $("last-sync").textContent = new Date().toLocaleTimeString();
  } catch (e) {
    setStatus(false);
  }
}

function setStatus(ok) {
  const d = $("status-dot");
  d.classList.toggle("off", !ok);
}

/* ----------------------------- render ----------------------------- */
function renderVisitors() {
  const p = $("visitors-panel");
  if (!visitors.length) { p.innerHTML = '<div class="empty">No active visitors right now.</div>'; return; }
  p.innerHTML = visitors.map(v => {
    const flag  = v.flag_emoji || (v.country ? "" : "");
    const ago   = v.seconds_ago != null ? humanAgo(v.seconds_ago) : "";
    const src   = v.traffic_source || "direct";
    const label = v.source_label || "Direct";
    const q     = v.search_query;
    const chip  = `<span class="chip ${src}">${escapeHtml(label)}${q ? " · \"" + escapeHtml(q.slice(0,30)) + "\"" : ""}</span>`;
    const ua    = (v.browser || "") + (v.os ? " · " + v.os : "");
    return `<div class="card">
      <div class="row">
        <div class="head">${flag} ${escapeHtml(v.country || "??")} · ${escapeHtml(v.last_path || "/")}</div>
        <div class="when">${ago}</div>
      </div>
      <div class="meta">${chip} ${escapeHtml(ua)}${v.hit_count > 1 ? " · " + v.hit_count + " hits" : ""}</div>
    </div>`;
  }).join("");
  $("vis-badge").textContent = visitors.length;
  $("vis-badge").hidden = visitors.length === 0;
}

function renderChats() {
  const p = $("chats-panel");
  if (!chats.length) { p.innerHTML = '<div class="empty">No active chats in the last 30 min.</div>'; return; }
  p.innerHTML = chats.map(c => {
    const ago = humanAgoIso(c.last_at);
    const taken = c.taken_over ? '<span class="chip taken">AGENT</span>' : "";
    const phone = c.phone ? "📞 " + c.phone : "Anonymous";
    return `<div class="card" onclick="openChat('${c.session_id}')">
      <div class="row">
        <div class="head">${taken}${escapeHtml(phone)} · ${c.user_msg_count || 0} msgs</div>
        <div class="when">${ago}</div>
      </div>
      <div class="preview">${escapeHtml(c.preview || "(no preview)")}</div>
    </div>`;
  }).join("");
  const newCount = chats.filter(c => !c.taken_over).length;
  $("chat-badge").textContent = newCount;
  $("chat-badge").hidden = newCount === 0;
}

/* ----------------------------- chat detail ----------------------------- */
function openChat(sid) {
  openSid = sid;
  $("chat-detail").classList.add("open");
  $("chat-title").textContent = "…" + sid.slice(-8);
  loadChatDetail(sid);
}
function closeChat() {
  openSid = null;
  $("chat-detail").classList.remove("open");
}
async function loadChatDetail(sid) {
  try {
    const j = await adm("/api/admin/live/chat/" + encodeURIComponent(sid));
    const box = $("chat-messages");
    box.innerHTML = (j.messages || []).map(m =>
      `<div class="msg ${m.role}">
         <div class="role">${m.role}${m.model_used ? " · " + escapeHtml(m.model_used) : ""}</div>
         ${escapeHtml(m.content || "").replace(/\n/g,"<br>")}
       </div>`).join("");
    box.scrollTop = box.scrollHeight;
  } catch (e) { console.error(e); }
}
async function sendReply() {
  const text = $("reply-input").value.trim();
  if (!text || !openSid) return;
  $("reply-btn").disabled = true;
  try {
    await adm("/api/admin/live/chat/" + encodeURIComponent(openSid) + "/reply",
              { method: "POST", body: { text } });
    $("reply-input").value = "";
    loadChatDetail(openSid);
  } catch (e) {
    alert("Reply failed");
  } finally {
    $("reply-btn").disabled = false;
  }
}
async function releaseChat() {
  if (!openSid) return;
  if (!confirm("Hand this chat back to the bot?")) return;
  await adm("/api/admin/live/chat/" + encodeURIComponent(openSid) + "/release",
            { method: "POST" });
  closeChat();
}

/* ----------------------------- sound + push ----------------------------- */
let audioCtx;
function beep(kind) {
  if (!soundOn) return;
  try {
    audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
    const t = audioCtx.currentTime;
    function tone(freq, dur, delay = 0) {
      const o = audioCtx.createOscillator();
      const g = audioCtx.createGain();
      o.type = "sine"; o.frequency.value = freq;
      g.gain.setValueAtTime(0, t + delay);
      g.gain.linearRampToValueAtTime(0.18, t + delay + 0.01);
      g.gain.linearRampToValueAtTime(0, t + delay + dur);
      o.connect(g); g.connect(audioCtx.destination);
      o.start(t + delay); o.stop(t + delay + dur + 0.05);
    }
    if (kind === "chat")    { tone(880, 0.15); tone(1320, 0.15, 0.18); }
    else /* visitor */      { tone(660, 0.12); }
  } catch (_) {}
}
function toggleSound() {
  soundOn = !soundOn;
  localStorage.setItem(SOUND_KEY, soundOn ? "1" : "0");
  refreshSoundUi();
}
function refreshSoundUi() {
  const b = $("snd-btn");
  b.textContent = soundOn ? "🔔" : "🔕";
  b.classList.toggle("active", soundOn);
}

async function enablePush() {
  try {
    const reg = await navigator.serviceWorker.ready;
    const k = await fetch("/api/push/vapid-key").then(r => r.json());
    if (!k.public) return alert("Server has no VAPID key configured.");
    let sub = await reg.pushManager.getSubscription();
    if (!sub) {
      sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlB64ToUint8(k.public),
      });
    }
    await adm("/api/admin/push/subscribe", {
      method: "POST",
      body: JSON.parse(JSON.stringify(sub)),
    });
    alert("✅ Push notifications on. Phone notifications will mirror to your watch automatically.");
  } catch (e) {
    alert("Push setup failed: " + e.message);
  }
}
function urlB64ToUint8(s) {
  const padding = "=".repeat((4 - s.length % 4) % 4);
  const base = (s + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(base);
  return Uint8Array.from(raw, c => c.charCodeAt(0));
}

/* ----------------------------- utils ----------------------------- */
function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g,
    c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}
function humanAgo(secs) {
  if (secs < 60) return secs + "s";
  if (secs < 3600) return Math.floor(secs/60) + "m";
  return Math.floor(secs/3600) + "h";
}
function humanAgoIso(iso) {
  if (!iso) return "";
  const t = new Date(iso).getTime();
  if (isNaN(t)) return "";
  return humanAgo(Math.floor((Date.now() - t)/1000));
}

/* ----------------------------- entrypoint ----------------------------- */
if (token) bootApp();
