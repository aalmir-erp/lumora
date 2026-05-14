# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"NfRis7RNR5CCX-Vhn6XIxQ"}`

## Build logs
```
[ 1/14] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
[internal] load build context
[internal] load build context
[ 2/14] WORKDIR /app
[ 3/14] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 4/14] COPY requirements.txt ./
[ 5/14] RUN pip install -r requirements.txt
[ 6/14] COPY whatsapp_bridge ./whatsapp_bridge
[ 7/14] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
[ 8/14] COPY app ./app
[ 8/14] COPY app ./app
[ 9/14] COPY web ./web
[ 9/14] COPY web ./web
[10/14] COPY _e2e-shots ./_e2e-shots
[10/14] COPY _e2e-shots ./_e2e-shots
[11/14] COPY _release/android ./_release/android
[11/14] COPY _release/android ./_release/android
[12/14] COPY twa/android/twa-manifest.json ./twa/android/twa-manifest.json
[12/14] COPY twa/android/twa-manifest.json ./twa/android/twa-manifest.json
[13/14] COPY start.sh /app/start.sh
[13/14] COPY start.sh /app/start.sh
[14/14] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[14/14] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
exporting to docker image format
uploading snapshot
exporting to docker image format
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NzA4YzUwMDNkYmI4ODVmM2Y1MWYyMjcwOGNmNDZiZmE5NmZmYWU2YjNlNGQzZDU1MTlhMTAyNDVkM2RkODg3NCIsInNpemUiOjM1MzMsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xNFQyMDo0NjoxN1oifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:605c5f02ac68514e77df077aaf19b94e8f9dab7552d3a1baeddab1143912effc
containerimage.digest: sha256:708c5003dbb885f3f51f22708cf46bfa96ffae6b3e4d3d5519a10245d3dd8874
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
INFO:     100.64.0.3:58796 - "GET /api/admin/push/subscribers/summary HTTP/1.1" 200 OK
INFO:     100.64.0.3:58816 - "GET /api/admin/push/log?limit=50 HTTP/1.1" 200 OK
INFO:     100.64.0.3:58810 - "GET /api/app/latest HTTP/1.1" 200 OK
INFO:     100.64.0.3:58780 - "GET /__admin_token__ HTTP/1.1" 403 Forbidden
INFO:     100.64.0.3:58828 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:58778 - "GET /api/admin/play-store/status HTTP/1.1" 403 Forbidden
INFO:     100.64.0.3:58796 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:58816 - "GET /api/admin/stats HTTP/1.1" 200 OK
INFO:     100.64.0.3:58778 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:58846 - "GET /api/admin/twa/installs HTTP/1.1" 200 OK
INFO:     100.64.0.3:58816 - "GET /api/admin/push/subscribers/summary HTTP/1.1" 200 OK
INFO:     100.64.0.3:58832 - "GET /api/admin/push/log?limit=50 HTTP/1.1" 200 OK
INFO:     100.64.0.3:58796 - "GET /api/admin/twa/credentials HTTP/1.1" 200 OK
INFO:     100.64.0.3:58796 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.3:58816 - "GET /api/app/latest HTTP/1.1" 200 OK
INFO:     100.64.0.3:58796 - "GET /__admin_token__ HTTP/1.1" 403 Forbidden
INFO:     100.64.0.3:58832 - "GET /api/admin/play-store/status HTTP/1.1" 403 Forbidden
INFO:     100.64.0.3:58846 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:58778 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:58828 - "GET /api/admin/stats HTTP/1.1" 200 OK
INFO:     100.64.0.3:58816 - "GET /api/admin/twa/installs HTTP/1.1" 200 OK
INFO:     100.64.0.3:58846 - "GET /api/admin/push/log?limit=50 HTTP/1.1" 200 OK
INFO:     100.64.0.3:58778 - "GET /api/admin/push/subscribers/summary HTTP/1.1" 200 OK
INFO:     100.64.0.3:58828 - "GET /api/health HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.4:61358 - "GET /api/admin/twa/credentials HTTP/1.1" 200 OK
INFO:     100.64.0.4:61360 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.3:58846 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:61376 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:60338 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
```
