# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"QDiRoOFDQzCCu2CQGbGh5g"}`

## Build logs
```
[internal] load build context
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[internal] load build context
uploading snapshot
[internal] load build context
[ 2/12] WORKDIR /app
[ 3/12] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 4/12] COPY requirements.txt ./
[ 5/12] RUN pip install -r requirements.txt
[ 6/12] COPY whatsapp_bridge ./whatsapp_bridge
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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6OTQ3MDRkZDMwNjc1ZDU3ZTdhZTdiYTU2OGVmNTUwMjg1MmU0NzI5NWRkMTlkMzZhZjU0OWYxZmQ0YjlhNzhiYyIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xMlQyMDozOTo1MloifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:bc5c34f86e13dc1b8e2228128f675ca1ef832cf218896db6f4edb653443fdae5
containerimage.digest: sha256:94704dd30675d57e7ae7ba568ef5502852e47295dd19d36af549f1fd4b9a78bc
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
Mounting volume on: /var/lib/containers/railwayapp/bind-mounts/510222c2-178d-42f6-ad84-9db14099a9d7/vol_onr647rhdeir9di9
Starting Container
[wa-bridge] listening on :3001
[wa-bridge] QR received. Open /qr in your browser to scan.
[lp] 17320 Google Ads landing-page routes registered (base=9384, qualifier=7752, near-me=184, 184 service aliases × 51 areas)
[lp-ar] 133 Arabic landing-page routes registered
INFO:     Started server process [1]
INFO:     Waiting for application startup.
[scheduler] started — autoblog 06:00 + 18:00, PSI 03:00, summary 21:00 (Asia/Dubai)
[purge] scan complete — 26 posts, 0 flagged
[seed-users] test accounts ready: test@servia.ae/test123, demo@servia.ae/demo123, vendor@servia.ae/vendor123
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     100.64.0.2:56695 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:24928 - "GET /%D8%AC%D9%84%D9%8A%D8%B3%D8%A9-%D8%A7%D8%B7%D9%81%D8%A7%D9%84-%D8%B1%D8%A7%D8%B3-%D8%A7%D9%84%D8%AE%D9%8A%D9%85%D8%A9?id=babysitting&lang=ar HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
[autoblog] catch-up SKIP (last_run @ 2026-05-12T14:00:00.000611Z is fresh AND ok)
[chat] route=admin-router (admin_default='google/gemini-2.5-flash', other_keys_set=True)
[auto-quote] has_book_now=False has_summary=False sid=sw-JqcxcQLEwS9xFAXx
INFO:     100.64.0.3:40056 - "POST /api/chat HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
[chat] route=admin-router (admin_default='google/gemini-2.5-flash', other_keys_set=True)
[auto-quote] has_book_now=False has_summary=False sid=sw-JqcxcQLEwS9xFAXx
INFO:     100.64.0.3:21470 - "POST /api/chat HTTP/1.1" 200 OK
[auto-quote] has_book_now=False has_summary=False sid=sw-JqcxcQLEwS9xFAXx
INFO:     100.64.0.3:47450 - "POST /api/chat HTTP/1.1" 200 OK
[auto-quote] has_book_now=False has_summary=False sid=sw-JqcxcQLEwS9xFAXx
INFO:     100.64.0.3:47450 - "POST /api/chat HTTP/1.1" 200 OK
INFO:     100.64.0.4:19256 - "GET /address-picker.js?v=1.24.108 HTTP/1.1" 200 OK
```
