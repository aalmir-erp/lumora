# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"2XCjEogvRbSWFp54yCLmYg"}`

## Build logs
```
[runtime  2/12] WORKDIR /app
[11/12] COPY start.sh /app/start.sh
[10/12] COPY _e2e-shots ./_e2e-shots
[ 9/12] COPY web ./web
[12/12] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[internal] load build context
[internal] load build context
[internal] load build context
[ 3/12] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 4/12] COPY requirements.txt ./
[ 5/12] RUN pip install -r requirements.txt
[ 6/12] COPY whatsapp_bridge ./whatsapp_bridge
[ 7/12] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
[ 7/12] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
[ 8/12] COPY app ./app
[ 8/12] COPY app ./app
[ 9/12] COPY web ./web
[ 9/12] COPY web ./web
[10/12] COPY _e2e-shots ./_e2e-shots
[10/12] COPY _e2e-shots ./_e2e-shots
[11/12] COPY start.sh /app/start.sh
[11/12] COPY start.sh /app/start.sh
[12/12] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[12/12] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
exporting to docker image format
exporting to docker image format
containerimage.config.digest: sha256:b5f98e28f45a6221cdcbdc6dc6d132f4f73b130b6208b094db48a1588baa88a0
containerimage.digest: sha256:5aea753b7be0a9b8eabb1f6cf5d2d89b32deb377ddf8820a3146e6c42bc5bc10
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NWFlYTc1M2I3YmUwYTliOGVhYmIxZjZjZjVkMmQ4OWIzMmRlYjM3N2RkZjg4MjBhMzE0NmU2YzQyYmM1YmMxMCIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xMVQyMDo0MjoyMVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
image push
image push

[35m====================
Starting Healthcheck
====================
[0m
[37mPath: /api/health[0m
[37mRetry window: 1m0s[0m

[92m[1/1] Healthcheck succeeded![0m
```

## Runtime logs
```
[start] launching whatsapp_bridge
[wa-bridge] listening on :3001
Mounting volume on: /var/lib/containers/railwayapp/bind-mounts/02955cdb-5c7f-4e33-900e-93427c138e75/vol_onr647rhdeir9di9
Starting Container
INFO:     Started server process [1]
INFO:     Waiting for application startup.
[scheduler] started — autoblog 06:00 + 18:00, PSI 03:00, summary 21:00 (Asia/Dubai)
[purge] scan complete — 23 posts, 0 flagged
[seed-users] test accounts ready: test@servia.ae/test123, demo@servia.ae/demo123, vendor@servia.ae/vendor123
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.2:37717 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:34776 - "GET /services/car-wash?id=car_wash HTTP/1.1" 200 OK
INFO:     100.64.0.4:41534 - "GET /area.html HTTP/1.1" 200 OK
INFO:     100.64.0.4:56716 - "HEAD /api/videos/play/svc-car-wash HTTP/1.1" 404 Not Found
INFO:     100.64.0.4:56716 - "GET /api/activity/live HTTP/1.1" 200 OK
[autoblog] catch-up SKIP (last_run @ 2026-05-11T20:29:39.173006Z is fresh AND ok)
[wa-bridge] QR received. Open /qr in your browser to scan.
[wa-bridge] QR received. Open /qr in your browser to scan.
```
