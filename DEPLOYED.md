# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"nmVyrzf2TIGhitTxPvyhXg"}`

## Build logs
```
[internal] load build context
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
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
containerimage.digest: sha256:489607a067f06c59c5bc2760472bcdc39d9dc9e2e137c7b2366e6d2bcaf5b671
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NDg5NjA3YTA2N2YwNmM1OWM1YmMyNzYwNDcyYmNkYzM5ZDlkYzllMmUxMzdjN2IyMzY2ZTZkMmJjYWY1YjY3MSIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xMlQyMDo1MDoxOFoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:b8a5707984b3cadefe19da63a61ba409253c1fcc5a8f2c57683cec613c26222b
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
INFO:     100.64.0.3:61808 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=635 HTTP/1.1" 200 OK
INFO:     100.64.0.3:61808 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=635 HTTP/1.1" 200 OK
INFO:     100.64.0.3:61808 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=635 HTTP/1.1" 200 OK
INFO:     100.64.0.3:61808 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=635 HTTP/1.1" 200 OK
INFO:     100.64.0.3:61808 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=635 HTTP/1.1" 200 OK
INFO:     100.64.0.3:61808 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=635 HTTP/1.1" 200 OK
INFO:     100.64.0.3:61808 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=635 HTTP/1.1" 200 OK
INFO:     100.64.0.3:61808 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=635 HTTP/1.1" 200 OK
INFO:     100.64.0.3:61808 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=635 HTTP/1.1" 200 OK
INFO:     100.64.0.3:61808 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=635 HTTP/1.1" 200 OK
INFO:     100.64.0.3:61808 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=635 HTTP/1.1" 200 OK
INFO:     100.64.0.3:61808 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=635 HTTP/1.1" 200 OK
INFO:     100.64.0.3:61808 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=635 HTTP/1.1" 200 OK
INFO:     100.64.0.3:61808 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=635 HTTP/1.1" 200 OK
INFO:     100.64.0.3:61808 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=635 HTTP/1.1" 200 OK
INFO:     100.64.0.3:61808 - "POST /api/cart/quote HTTP/1.1" 200 OK
INFO:     100.64.0.3:61808 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=635 HTTP/1.1" 200 OK
INFO:     100.64.0.3:61808 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=635 HTTP/1.1" 200 OK
INFO:     100.64.0.3:61808 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=635 HTTP/1.1" 200 OK
INFO:     100.64.0.3:61808 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=635 HTTP/1.1" 200 OK
INFO:     100.64.0.3:61808 - "POST /api/cart/checkout HTTP/1.1" 200 OK
INFO:     100.64.0.3:61808 - "GET /q/Q-A98C73 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.3:39040 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=635 HTTP/1.1" 200 OK
INFO:     100.64.0.3:39046 - "POST /api/app-install HTTP/1.1" 200 OK
[autoblog] catch-up SKIP (last_run @ 2026-05-12T20:49:01.229312Z is fresh AND ok)
INFO:     100.64.0.3:39046 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=635 HTTP/1.1" 200 OK
INFO:     100.64.0.3:39046 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=635 HTTP/1.1" 200 OK
INFO:     100.64.0.3:39052 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=635 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
```
