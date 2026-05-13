# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"UAB6g6NrRfu3Rl5kWUN5dQ"}`

## Build logs
```
[12/12] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[ 9/12] COPY web ./web
[ 4/12] COPY requirements.txt ./
[base-deps 1/3] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[base-deps 1/3] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[base-deps 1/3] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[internal] load build context
[internal] load build context
[internal] load build context
[ 2/12] WORKDIR /app
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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6YzdhODRmNmRhZTVhNTg0ZmRhZmU4ODRkNTc3MDJlODI0MjhmMmQwYmUzY2U5NDM4NzUyMjVjZGFmMjg0Y2NjZCIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xM1QwMzowNjozN1oifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:eddd23e3953027fe1bf31bfde04300f5c8d218bc9c9281c9d47d6713b31e38b6
containerimage.digest: sha256:c7a84f6dae5a584fdafe884d57702e82428f2d0be3ce943875225cdaf284cccd
image push
image push

[35m====================
Starting Healthcheck
====================
[0m

[92m[1/1] Healthcheck succeeded![0m
```

## Runtime logs
```
INFO:     100.64.0.4:22960 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.6:42212 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.6:42202 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.6:42186 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.6:42226 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.6:42236 - "GET /api/search/index HTTP/1.1" 200 OK
INFO:     100.64.0.6:42226 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:30576 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.5:57350 - "GET /api/blog/latest?limit=10 HTTP/1.1" 200 OK
INFO:     100.64.0.5:57340 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.3:30576 - "GET /cart-badge.js?v=29644028 HTTP/1.1" 200 OK
INFO:     100.64.0.8:35832 - "GET /social-strip.js?v=29644028 HTTP/1.1" 200 OK
INFO:     100.64.0.9:42714 - "GET /location-bar.js?v=29644028 HTTP/1.1" 200 OK
INFO:     100.64.0.4:26844 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.6:49788 - "GET /api/reviews/platforms HTTP/1.1" 200 OK
[chat] route=admin-router (admin_default='google/gemini-2.5-flash', other_keys_set=True)
[auto-quote] has_book_now=False has_summary=False sid=sw-ecBSDi6cAZY94R7R
INFO:     100.64.0.3:30576 - "POST /api/chat HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
[autoblog] catch-up SKIP (last_run @ 2026-05-13T02:00:00.001964Z is fresh AND ok)
INFO:     100.64.0.4:12168 - "GET /mascots/pool.svg HTTP/1.1" 200 OK
INFO:     100.64.0.7:32980 - "GET /mascots/garden.svg HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
[chat] route=admin-router (admin_default='google/gemini-2.5-flash', other_keys_set=True)
[auto-quote] has_book_now=False has_summary=False sid=sw-ecBSDi6cAZY94R7R
INFO:     100.64.0.5:48902 - "POST /api/chat HTTP/1.1" 200 OK
[chat] route=admin-router (admin_default='google/gemini-2.5-flash', other_keys_set=True)
[auto-quote] has_book_now=False has_summary=False sid=sw-ecBSDi6cAZY94R7R
INFO:     100.64.0.6:45366 - "GET /api/me/profile HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
```
