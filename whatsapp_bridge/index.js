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

const client = new Client({
  authStrategy: new LocalAuth({ dataPath: "./.wwebjs_auth" }),
  puppeteer: {
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
  },
});

client.on("qr", (qr) => {
  lastQr = qr;
  console.log("[wa-bridge] QR received. Open /qr in your browser to scan.");
});
client.on("ready", () => {
  ready = true;
  pairedNumber = client.info?.wid?.user || null;
  console.log("[wa-bridge] WhatsApp paired:", pairedNumber);
});
client.on("disconnected", (reason) => {
  ready = false;
  console.warn("[wa-bridge] disconnected:", reason);
});

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
  res.json({ ready, paired_number: pairedNumber, has_qr: !!lastQr });
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

app.post("/send", checkAuth, async (req, res) => {
  const { to, text } = req.body || {};
  if (!to || !text) return res.status(400).json({ error: "to + text required" });
  if (!ready) return res.status(503).json({ error: "WhatsApp not paired yet — open /qr" });
  try {
    const chatId = to.includes("@") ? to : `${to.replace(/\D/g, "")}@c.us`;
    const sent = await client.sendMessage(chatId, text);
    res.json({ ok: true, id: sent.id?._serialized });
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

app.listen(PORT, () => console.log(`[wa-bridge] listening on :${PORT}`));
