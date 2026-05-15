# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"ztptQYVtQwWlBjWcCx5-qw"}`

## Build logs
```
[2/7] WORKDIR /app
[internal] load build context
[internal] load build context
[internal] load build context
[ 3/14] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 4/14] COPY requirements.txt ./
[ 5/14] RUN pip install -r requirements.txt
[ 6/14] COPY whatsapp_bridge ./whatsapp_bridge
[ 7/14] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
[ 8/14] COPY app ./app
[ 8/14] COPY app ./app
[ 9/14] COPY web ./web
[ 9/14] COPY web ./web
uploading snapshot
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
exporting to docker image format
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6MGJlZDlmY2M4MzJiZDUyMzM0NzFiZWJjNzgwMDE5YWRmM2JlZThjODg2YzAxODM2M2FkMjA1ZGJmYjUxMmJhNiIsInNpemUiOjM1MzMsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xNVQxNTowMTowNFoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:0aa03218d7b2fd38c72d83993dae9835b7dded76ffcfd4d54d721de1971627e0
containerimage.digest: sha256:0bed9fcc832bd5233471bebc780019adf3bee8c886c018363ad205dbfb512ba6
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
INFO:     100.64.0.3:25880 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
INFO:     100.64.0.3:41004 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.3:41004 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
INFO:     100.64.0.3:29836 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.3:29836 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
INFO:     100.64.0.3:53000 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.3:53000 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
INFO:     100.64.0.3:33956 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.3:33956 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
[autoblog] catch-up SKIP (last_run @ 2026-05-15T14:00:00.000743Z is fresh AND ok)
INFO:     100.64.0.3:57184 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.3:57184 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
INFO:     100.64.0.3:57188 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:57200 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.5:56396 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:27950 - "GET /api/chat/poll?session_id=sw-m-fcU-u8sZ01srRg&since_id=711 HTTP/1.1" 200 OK
INFO:     100.64.0.3:57200 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.5:56396 - "GET /api/chat/poll?session_id=sw-m-fcU-u8sZ01srRg&since_id=711 HTTP/1.1" 200 OK
INFO:     100.64.0.3:57200 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.3:57200 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.3:62256 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.3:62256 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
INFO:     100.64.0.3:62262 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.3:62262 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.3:46478 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.3:46478 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
INFO:     100.64.0.6:30542 - "GET /faq.html HTTP/1.1" 200 OK
```
