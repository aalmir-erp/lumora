# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"hOp6MSnIQ9aFfZkXqmzx2A"}`

## Build logs
```
[ 6/12] COPY whatsapp_bridge ./whatsapp_bridge
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
[internal] load build context
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
[ 1/12] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
[internal] load build context
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
containerimage.config.digest: sha256:58e84004fba1561a32b08ddbcca08081efafdcfe133e46ec27839dc8eb6d9a84
containerimage.digest: sha256:548bf6cd1ba3f73b9bb1507e283009942da31d5f69c52b704bf414d1fae231b9
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NTQ4YmY2Y2QxYmEzZjczYjliYjE1MDdlMjgzMDA5OTQyZGEzMWQ1ZjY5YzUyYjcwNGJmNDE0ZDFmYWUyMzFiOSIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xM1QxNzozMDo1OFoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
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
INFO:     100.64.0.8:46754 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.9:43518 - "GET /api/blog/latest?limit=10 HTTP/1.1" 200 OK
INFO:     100.64.0.9:43512 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.10:48436 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.11:11240 - "GET /_snippets.js?v=29644893 HTTP/1.1" 200 OK
INFO:     100.64.0.12:55330 - "GET /location-bar.js?v=29644893 HTTP/1.1" 200 OK
INFO:     100.64.0.13:20796 - "GET /cart-badge.js?v=29644893 HTTP/1.1" 200 OK
INFO:     100.64.0.9:43532 - "GET /social-strip.js?v=29644893 HTTP/1.1" 200 OK
INFO:     100.64.0.14:53098 - "GET /about-app.js?v=29644893 HTTP/1.1" 200 OK
INFO:     100.64.0.9:43518 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=0 HTTP/1.1" 200 OK
INFO:     100.64.0.9:43512 - "GET /?lang=en HTTP/1.1" 200 OK
[push] pywebpush not installed — skipping push send
INFO:     100.64.0.8:46768 - "GET /style.css?v=1.24.169 HTTP/1.1" 200 OK
INFO:     100.64.0.5:29546 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.15:48764 - "GET /widget.css?v=1.24.169 HTTP/1.1" 200 OK
INFO:     100.64.0.5:29530 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.13:20796 - "GET /widget.js?v=1.24.169 HTTP/1.1" 200 OK
INFO:     100.64.0.5:29528 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.5:29554 - "GET /api/search/index HTTP/1.1" 200 OK
INFO:     100.64.0.9:43512 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.4:51654 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=0 HTTP/1.1" 200 OK
INFO:     100.64.0.4:51654 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.4:51660 - "GET /api/blog/latest?limit=10 HTTP/1.1" 200 OK
INFO:     100.64.0.4:51668 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.4:51668 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=0 HTTP/1.1" 200 OK
INFO:     100.64.0.4:51660 - "GET /api/me/profile HTTP/1.1" 200 OK
INFO:     100.64.0.7:24860 - "GET /api/me/profile HTTP/1.1" 200 OK
INFO:     100.64.0.6:25696 - "GET /api/reviews/platforms HTTP/1.1" 200 OK
INFO:     100.64.0.8:17614 - "GET /api/chat/poll?session_id=sw-6Bmkcdcnl0ZCsdME&since_id=677 HTTP/1.1" 200 OK
INFO:     100.64.0.5:54932 - "GET /?lang=en HTTP/1.1" 304 Not Modified
```
