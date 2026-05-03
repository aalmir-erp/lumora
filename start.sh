#!/bin/sh
# Servia process supervisor — starts the WhatsApp QR bridge alongside FastAPI.
# Both run in the same Railway container so the admin only has to scan the QR
# in the admin panel (no separate Railway service to deploy or maintain).

set -e
mkdir -p /data/.wwebjs_auth
ln -sfn /data/.wwebjs_auth /app/whatsapp_bridge/.wwebjs_auth || true

# Auto-generate a bridge token if not provided externally. Both the bot and
# the bridge read the same env var so they always match. Persist to
# /data/.bridge_token so the token is stable across restarts.
if [ -z "${WA_BRIDGE_TOKEN:-}" ]; then
  if [ ! -f /data/.bridge_token ]; then
    head -c 32 /dev/urandom | base64 | tr -d '/+=\n' > /data/.bridge_token
  fi
  export WA_BRIDGE_TOKEN="$(cat /data/.bridge_token)"
fi
export BRIDGE_TOKEN="$WA_BRIDGE_TOKEN"
export BOT_WEBHOOK="${BOT_WEBHOOK:-http://127.0.0.1:${PORT:-8000}/api/wa/webhook}"
export PORT="${PORT:-8000}"

# Start the WhatsApp bridge in the background. It crashes are auto-restarted
# so a transient Chromium glitch doesn't kill admin alerting.
(
  cd /app/whatsapp_bridge
  while true; do
    echo "[start] launching whatsapp_bridge"
    PORT=3001 node index.js || echo "[start] bridge exited; restarting in 5s..."
    sleep 5
  done
) &

# Run FastAPI in the foreground so Railway sees the main process.
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
