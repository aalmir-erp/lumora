# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"gr-qA3X5SMq2CuZjGbGh5g"}`

## Build logs
```
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
uploading snapshot
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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6YTIzMGMyODM1YWIwZDg3MzAxZmYwMDc4MWQ2ZTYyZTI0MDM3ZDFiZDRlMGRmMDI1MDMwYjU3YjU3NWMzM2U5ZiIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xMVQyMDo0ODowMVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:7a6633cd272ce74670fa7f8cd62dd06e3f056f4a6b2683b8aabcbbfa3df8aebb
containerimage.digest: sha256:a230c2835ab0d87301ff00781d6e62e24037d1bd4e0df025030b57b575c33e9f
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
INFO:     100.64.0.3:37618 - "GET /api/reviews/platforms HTTP/1.1" 200 OK
INFO:     100.64.0.4:12576 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.4:12590 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.4:12586 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.4:12580 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.7:39306 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.3:37602 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:37618 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:37576 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.3:37626 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.4:41408 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.11:48658 - "GET /api/blog/hero/sharjah-muwaileh-ant-control-kitchen-targeted-2026.svg HTTP/1.1" 200 OK
[autoblog] catch-up SKIP (last_run @ 2026-05-11T20:29:39.173006Z is fresh AND ok)
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.7:39658 - "GET /blog HTTP/1.1" 200 OK
INFO:     100.64.0.3:59662 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:59674 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.6:25076 - "GET /api/blog/hero/abu-dhabi-reem-island-bed-bugs-why-80-percent-fail.svg HTTP/1.1" 200 OK
INFO:     100.64.0.9:45408 - "GET /api/blog/hero/jumeirah-pre-moving-in-pest-checklist-villa.svg HTTP/1.1" 200 OK
INFO:     100.64.0.10:44624 - "GET /api/blog/hero/dubai-jlt-cockroach-infestation-pre-summer-may-2026.svg HTTP/1.1" 200 OK
INFO:     100.64.0.10:44630 - "GET /api/blog/hero/dubai-marina-termite-early-warning-signs-2026.svg HTTP/1.1" 200 OK
INFO:     100.64.0.4:52796 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.4:52798 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.7:27242 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.3:28268 - "GET /blog/sharjah-silverfish-bathrooms-humidity-fix-2026 HTTP/1.1" 200 OK
INFO:     100.64.0.4:25544 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.4:25552 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.7:27256 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.3:49662 - "POST /api/app-install HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
```
