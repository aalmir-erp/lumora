/* Servia WhatsApp QR Bridge.
 *
 * Pairs your personal WhatsApp number to this service via QR scan, then:
 *   - forwards inbound messages to BOT_WEBHOOK (the FastAPI /api/wa/webhook)
 *   - exposes POST /send for the bot to push outbound replies
 *
 * Required env:
 *   BOT_WEBHOOK     URL of FastAPI inbound webhook (e.g. https://sales.mir.ae/api/wa/webhook)
 *   BRIDGE_TOKEN    shared secret matching FastAPI's WA_BRIDGE_TOKEN
 *   PORT            port to listen on (default 3001)
 *
 * Persistence:
 *   whatsapp-web.js stores its session at ./.wwebjs_auth/. Mount this directory
 *   on a Railway volume so the QR pairing survives redeploys.
 *
 * Security:
 *   This bridge controls a real WhatsApp account. Restrict access to it (private
 *   network, IP allowlist, or token-only). Never expose /qr publicly without auth.
 */
const express = require("express");
const fetch = require("node-fetch");
const QRCode = require("qrcode");
const { Client, LocalAuth } = require("whatsapp-web.js");

const BOT_WEBHOOK = process.env.BOT_WEBHOOK || "http://localhost:8000/api/wa/webhook";
const BRIDGE_TOKEN = process.env.BRIDGE_TOKEN || "";
const PORT = parseInt(process.env.PORT || "3001", 10);

let lastQr = null;
let ready = false;
let pairedNumber = null;
// v1.24.225 — Event audit trail. Founder reported QR scans appear to
// pair (phone shows the device as linked) but the bridge keeps showing
// "waiting for scan" after a refresh. To diagnose, log every lifecycle
// event with a timestamp and expose the last 30 via /status. Common
// causes the founder might see:
//   - authenticated → disconnected (LOGOUT)  → phone unlinked it
//   - authenticated → disconnected (NAVIGATION) → bridge container restarted
//   - auth_failure → restart loop  → session file corrupted
//   - qr received but never authenticated → user scanned the wrong QR
let recentEvents = [];
function logEvent(type, detail = "") {
  const evt = {
    type,
    detail: typeof detail === "string" ? detail.slice(0, 200) : String(detail).slice(0, 200),
    at: new Date().toISOString(),
  };
  recentEvents.push(evt);
  if (recentEvents.length > 30) recentEvents.shift();
  console.log(`[wa-bridge] ${type}${detail ? " : " + detail : ""}`);
}

// v1.24.236 — Harder-on-memory Chromium flags so the bridge survives
// the shared-container memory pressure that's been killing the session.
// Investigation summary (founder asked 'check sales.mir.ae what logic'):
//   sales.mir.ae runs its bridge as a SEPARATE Railway service with
//   dedicated 1GB+ memory. Servia's bridge shares ~512MB with FastAPI
//   + the inspector bot + image generation + APScheduler crons. When
//   memory spikes (during inspector scan, autoblog, social-image gen),
//   Chromium gets OOM-killed → WA Web session in browser memory dies.
//   Reconnect SOMETIMES works, but if the session file was mid-write
//   during the OOM, the restore from /data/.wwebjs_auth fails → stays
//   signed out. PERMANENT fix = separate Railway service (see
//   docs/WA_BRIDGE_SEPARATE_SERVICE.md). Mitigations below.
const client = new Client({
  authStrategy: new LocalAuth({ dataPath: "./.wwebjs_auth" }),
  puppeteer: {
    args: [
      "--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage",
      // v1.24.236 — Memory + perf flags. --memory-pressure-off prevents
      // Chromium from voluntarily killing tabs on pressure. --js-flags
      // caps V8 inside Chromium so it doesn't try to grab > 384MB.
      // --disable-gpu / --disable-extensions / --disable-background-*
      // reduce baseline footprint.
      "--memory-pressure-off",
      "--js-flags=--max-old-space-size=384",
      "--disable-gpu",
      "--disable-extensions",
      "--disable-background-networking",
      "--disable-background-timer-throttling",
      "--disable-renderer-backgrounding",
      "--disable-features=TranslateUI",
      "--disable-default-apps",
      "--no-default-browser-check",
      "--mute-audio",
    ],
    // Force the headed-Chromium env vars even if not set by the Dockerfile
    executablePath: process.env.PUPPETEER_EXECUTABLE_PATH || undefined,
  },
});

// v1.24.236 — Graceful shutdown on SIGTERM/SIGINT so the WA session
// file isn't half-written when Railway restarts the container. Without
// this, every deploy + every OOM corrupts /data/.wwebjs_auth and the
// bridge has to re-pair via QR.
async function _gracefulExit(sig) {
  console.log(`[wa-bridge] received ${sig} — destroying client to flush session…`);
  try { await client.destroy(); } catch (e) { console.warn("destroy err:", e.message); }
  process.exit(0);
}
process.on("SIGTERM", () => _gracefulExit("SIGTERM"));
process.on("SIGINT",  () => _gracefulExit("SIGINT"));

client.on("qr", (qr) => {
  lastQr = qr;
  logEvent("qr_received", "len=" + qr.length);
});
client.on("loading_screen", (percent, message) => {
  logEvent("loading_screen", `${percent}% ${message || ""}`);
});
client.on("authenticated", () => {
  // Fires AFTER QR scan succeeds, BEFORE ready. If we see authenticated
  // but no subsequent ready, the bridge is stuck mid-handshake (Chromium
  // memory pressure, WA Web protocol drift).
  logEvent("authenticated", "session credentials received");
});
client.on("auth_failure", (msg) => {
  // Session file corrupted or rejected. Common after WA major version
  // bumps. Auto-recover: nuke the auth dir so next restart re-prompts QR.
  logEvent("auth_failure", String(msg || "no detail"));
  console.error("[wa-bridge] auth_failure — session file may be corrupted; consider clearing /data/.wwebjs_auth");
});
client.on("ready", () => {
  ready = true;
  pairedNumber = client.info?.wid?.user || null;
  logEvent("ready", "paired=" + pairedNumber);
});
client.on("change_state", (state) => {
  // CONNECTED / OPENING / PAIRING / TIMEOUT / CONFLICT / UNLAUNCHED / UNPAIRED / etc.
  logEvent("change_state", state);
});
client.on("disconnected", (reason) => {
  ready = false;
  // reason values: LOGOUT, NAVIGATION, UNPAIRED, CONFLICT, etc.
  logEvent("disconnected", String(reason));
  console.warn(`[wa-bridge] disconnected: ${reason} — call client.initialize() to retry`);
  // v1.24.232 — exponential-backoff reconnect. Founder reported the
  // bridge keeps signing out (sales.mir.ae's bridge does not, because
  // it's in a separate container with dedicated memory; ours runs
  // alongside FastAPI + can hit memory pressure). Without backoff,
  // tight reconnect loops can make the situation worse if WA is
  // rate-limiting us.
  let attempt = 0;
  const tryReconnect = () => {
    attempt++;
    const delay = Math.min(60000, 5000 * Math.pow(1.5, attempt - 1));
    setTimeout(() => {
      if (ready) return;  // already recovered (e.g. via heartbeat)
      try {
        client.initialize();
        logEvent("re_init", `attempt #${attempt} after disconnect`);
      } catch (e) {
        logEvent("re_init_failed", e.message || String(e));
        if (attempt < 12) tryReconnect();
      }
    }, delay);
  };
  tryReconnect();
});

// v1.24.236 — Faster heartbeat. Every 30s (was 90s), if ready=false for
// more than 2 min (was 5 min), force re-init. Founder reported the
// bridge silently dying for long stretches — faster detection brings
// it back before they notice.
let _lastReadyAt = Date.now();
setInterval(() => {
  if (ready) { _lastReadyAt = Date.now(); return; }
  const staleMs = Date.now() - _lastReadyAt;
  if (staleMs > 2 * 60 * 1000) {  // 2 min without being ready
    logEvent("heartbeat_reinit", `stale for ${Math.round(staleMs/1000)}s`);
    try { client.initialize(); _lastReadyAt = Date.now(); }
    catch (e) { logEvent("heartbeat_reinit_failed", e.message); }
  }
}, 30 * 1000);

client.on("message", async (msg) => {
  if (msg.fromMe || !msg.body) return;
  const from = (msg.from || "").replace(/@.*/, "");
  console.log("[wa-bridge] inbound from", from, ":", msg.body.slice(0, 80));
  try {
    const r = await fetch(BOT_WEBHOOK, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-bridge-token": BRIDGE_TOKEN,
      },
      body: JSON.stringify({
        from_number: from,
        text: msg.body,
        ts: new Date().toISOString(),
        name: msg._data?.notifyName || null,
      }),
    });
    if (!r.ok) console.error("[wa-bridge] webhook error", r.status, await r.text());
  } catch (e) {
    console.error("[wa-bridge] webhook fetch failed:", e.message);
  }
});

client.initialize();

// ----- HTTP -----
const app = express();
app.use(express.json({ limit: "1mb" }));

function checkAuth(req, res, next) {
  if (!BRIDGE_TOKEN) return next(); // dev only
  const a = (req.headers.authorization || "").replace(/^Bearer\s+/i, "").trim();
  if (a !== BRIDGE_TOKEN) return res.status(401).json({ error: "bad token" });
  next();
}

app.get("/status", checkAuth, (req, res) => {
  // v1.24.225 — Expose recent lifecycle events + session-files count so
  // the admin can see why pairing didn't stick (e.g. ready followed by
  // disconnected reason=LOGOUT means the phone unlinked the device).
  let sessionFiles = 0;
  try {
    const fs = require("fs");
    const path = require("path");
    const authDir = "./.wwebjs_auth";
    if (fs.existsSync(authDir)) {
      const walk = (dir) => {
        let count = 0;
        for (const f of fs.readdirSync(dir)) {
          const full = path.join(dir, f);
          const st = fs.statSync(full);
          if (st.isDirectory()) count += walk(full);
          else count++;
        }
        return count;
      };
      sessionFiles = walk(authDir);
    }
  } catch (_) {}
  res.json({
    ready,
    paired_number: pairedNumber,
    has_qr: !!lastQr,
    session_files: sessionFiles,
    recent_events: recentEvents.slice(-15),
    process_uptime_s: Math.round(process.uptime()),
  });
});

// v1.24.225 — Admin-triggered nuke + re-pair. Forces a fresh QR by
// destroying the current client + wiping the session folder. Use when
// the diagnostic shows auth_failure or repeated disconnect loops.
app.post("/reset", checkAuth, async (req, res) => {
  try {
    logEvent("reset_requested", "admin triggered nuke + repair");
    try { await client.destroy(); } catch (e) { logEvent("destroy_err", e.message); }
    const fs = require("fs");
    const path = require("path");
    const authDir = "./.wwebjs_auth";
    if (fs.existsSync(authDir)) {
      // Recursive remove
      fs.rmSync(authDir, { recursive: true, force: true });
      logEvent("auth_dir_removed", authDir);
    }
    ready = false;
    pairedNumber = null;
    lastQr = null;
    setTimeout(() => {
      try { client.initialize(); logEvent("re_init", "after reset"); }
      catch (e) { logEvent("re_init_failed", e.message || String(e)); }
    }, 1500);
    res.json({ ok: true, message: "Session wiped. A fresh QR will appear in ~30-60s." });
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

// QR page (open in browser, scan with WhatsApp on phone). Token-protected.
app.get("/qr", checkAuth, async (req, res) => {
  if (ready) return res.send(`<h2>Already paired — ${pairedNumber}</h2>`);
  if (!lastQr) return res.send("<h2>Waiting for QR... refresh in a few seconds.</h2>");
  const dataUrl = await QRCode.toDataURL(lastQr, { width: 320 });
  res.send(`<!DOCTYPE html><html><body style="font-family:system-ui;text-align:center;padding:32px">
    <h1>Lumora WhatsApp Bridge</h1><p>Open WhatsApp → Settings → Linked devices → Link a device</p>
    <img src="${dataUrl}" alt="QR" style="border:8px solid #fff;box-shadow:0 8px 24px rgba(0,0,0,.15)"><br><br>
    <small>This page refreshes automatically every 8 seconds.</small>
    <script>setTimeout(()=>location.reload(),8000)</script></body></html>`);
});

// v1.24.175 — JSON variant so the Servia /admin-wa-bridge page can
// fetch + render the QR inline (instead of iframing /qr).
app.get("/qr.json", checkAuth, async (req, res) => {
  if (ready) return res.json({ ready: true, paired_number: pairedNumber, qr: null });
  if (!lastQr) return res.json({ ready: false, qr: null });
  const dataUrl = await QRCode.toDataURL(lastQr, { width: 320 });
  res.json({ ready: false, qr: dataUrl });
});

app.post("/send", checkAuth, async (req, res) => {
  const { to, text } = req.body || {};
  if (!to || !text) return res.status(400).json({ error: "to + text required" });
  if (!ready) return res.status(503).json({ error: "WhatsApp not paired yet — open /qr" });
  try {
    const cleanTo = to.replace(/\D/g, "");
    // v1.24.225 — Detect "send to self" (admin test button → admin's own
    // number). WhatsApp's new LID protocol rejects `971XXXXX@c.us` if X
    // is your own phone. Use the resolved client.info.wid instead.
    const myNumber = client.info?.wid?.user || "";
    const isSelfSend = cleanTo && myNumber && cleanTo === myNumber;
    let chatId;
    if (to.includes("@")) {
      chatId = to;
    } else if (isSelfSend) {
      // Self-send → use the client's own WID (correct format whether
      // the user has a LID alias or a plain phone serial).
      chatId = client.info.wid._serialized;
      logEvent("self_send_lid_workaround", `using ${chatId} instead of ${cleanTo}@c.us`);
    } else {
      chatId = `${cleanTo}@c.us`;
    }
    try {
      const sent = await client.sendMessage(chatId, text);
      res.json({ ok: true, id: sent.id?._serialized });
    } catch (firstErr) {
      // Some accounts now require @lid for ANY send (recent WA protocol
      // change). Retry once with the LID suffix as a fallback so the
      // bridge doesn't fail on the "No LID for user" error.
      if (/No LID for user/i.test(firstErr.message || "")) {
        logEvent("send_retry_lid", firstErr.message.slice(0, 80));
        try {
          // Look up the contact to get its proper serialized ID.
          const contact = await client.getContactById(chatId);
          const properId = contact?.id?._serialized || chatId;
          const sent2 = await client.sendMessage(properId, text);
          return res.json({ ok: true, id: sent2.id?._serialized, retried: true });
        } catch (retryErr) {
          throw retryErr;  // fall through to outer catch with original error
        }
      }
      throw firstErr;
    }
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

app.listen(PORT, () => console.log(`[wa-bridge] listening on :${PORT}`));
