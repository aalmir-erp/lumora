# Lumora WhatsApp QR Bridge

Pairs a personal WhatsApp number to the Lumora bot via QR scan (same flow as
WhatsApp Web). Forwards inbound messages to the FastAPI backend, and exposes
`/send` so the bot can reply.

## Deploy on Railway as a separate service

1. Create a **second Railway service** in the same project. Set it to the
   `urbanservices_chatbot/whatsapp_bridge/` subpath and use the included
   `Dockerfile`.
2. **Add a persistent volume** mounted at `/app/.wwebjs_auth` (1 GiB is plenty).
   Without this, every redeploy logs you out of WhatsApp.
3. Set environment variables on the bridge service:
   ```
   BOT_WEBHOOK=https://sales.mir.ae/api/wa/webhook
   BRIDGE_TOKEN=<long random secret>
   PORT=3001
   ```
4. Set environment variables on the **bot** service:
   ```
   WA_BRIDGE_URL=https://<bridge-service>.railway.app
   WA_BRIDGE_TOKEN=<same secret>
   ```
5. Deploy both. Open `https://<bridge-service>.railway.app/qr` (auth: pass
   `Authorization: Bearer <BRIDGE_TOKEN>` — easiest with a curl-based reverse
   proxy or just open `?` URL with extension; you may also temporarily unset
   the token to scan the first time).
6. Scan with your phone: WhatsApp → Settings → Linked devices → Link a device.

After scanning, `/api/wa/status` on the bot service will show `ready: true`.

## Security

- The bridge controls a real WhatsApp account. **Restrict access** —
  ideally make it private/internal-only on Railway.
- Never expose `/qr` to the public internet without `BRIDGE_TOKEN`.
- Rotate `BRIDGE_TOKEN` periodically.

## Local dev

```bash
npm install
BOT_WEBHOOK=http://localhost:8000/api/wa/webhook node index.js
# open http://localhost:3001/qr in your browser, scan with phone
```
