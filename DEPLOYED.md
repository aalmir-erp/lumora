# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"QWpQeZQFSK2UVpPCCx5-qw"}`

## Build logs
```
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 2/11] WORKDIR /app
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[internal] load build context
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[internal] load build context
[internal] load build context
[ 2/11] WORKDIR /app
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 4/11] COPY requirements.txt ./
[ 5/11] RUN pip install -r requirements.txt
[ 6/11] COPY whatsapp_bridge ./whatsapp_bridge
[ 7/11] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
[ 8/11] COPY app ./app
[ 8/11] COPY app ./app
[ 9/11] COPY web ./web
[ 9/11] COPY web ./web
[10/11] COPY start.sh /app/start.sh
[10/11] COPY start.sh /app/start.sh
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
exporting to docker image format
exporting to docker image format
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6ZDZkYjQ4OTA2NzdkZDAxNjcyOWFiMjQ4YjU4NzAzOTI1YmExYjQ0YWIxY2NlZDkyM2FjZWQzNjE1YzY5MTA5YiIsInNpemUiOjI5NTksImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wOVQyMDo1NToxM1oifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:bd1c8ed6a1d129f6a5fc99d7297a1ce96b857a52af5c6ae81eeb72e822dd0a16
containerimage.digest: sha256:d6db4890677dd016729ab248b58703925ba1b44ab1cced923aced3615c69109b
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
INFO:     100.64.0.3:36808 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=521 HTTP/1.1" 200 OK
INFO:     100.64.0.4:31212 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=521 HTTP/1.1" 200 OK
INFO:     100.64.0.4:31212 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=521 HTTP/1.1" 200 OK
INFO:     100.64.0.5:29614 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.6:26246 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=521 HTTP/1.1" 200 OK
INFO:     100.64.0.7:26466 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=521 HTTP/1.1" 200 OK
INFO:     100.64.0.8:46136 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=521 HTTP/1.1" 200 OK
INFO:     100.64.0.3:50076 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=521 HTTP/1.1" 200 OK
INFO:     100.64.0.3:50076 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=521 HTTP/1.1" 200 OK
INFO:     100.64.0.4:56182 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=521 HTTP/1.1" 200 OK
INFO:     100.64.0.9:39000 - "GET /robots.txt HTTP/1.1" 200 OK
INFO:     100.64.0.4:43902 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=521 HTTP/1.1" 200 OK
[chat] route=admin-router (admin_default='google/gemini-2.5-flash', other_keys_set=True)
INFO:     100.64.0.6:39536 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=521 HTTP/1.1" 200 OK
INFO:     100.64.0.6:39536 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=521 HTTP/1.1" 200 OK
INFO:     100.64.0.6:39536 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=521 HTTP/1.1" 200 OK
INFO:     100.64.0.6:39536 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=521 HTTP/1.1" 200 OK
[auto-quote] has_book_now=False has_summary=False sid=sw-9Orcqse_nw7WzrpB
INFO:     100.64.0.6:39534 - "POST /api/chat HTTP/1.1" 200 OK
INFO:     100.64.0.7:18346 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=521 HTTP/1.1" 200 OK
INFO:     100.64.0.8:42262 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=523 HTTP/1.1" 200 OK
INFO:     100.64.0.3:37984 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=523 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.3:31632 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=523 HTTP/1.1" 200 OK
INFO:     100.64.0.4:62896 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=523 HTTP/1.1" 200 OK
INFO:     100.64.0.4:62896 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=523 HTTP/1.1" 200 OK
INFO:     100.64.0.6:62788 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=523 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.7:43200 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=523 HTTP/1.1" 200 OK
INFO:     100.64.0.8:56118 - "GET /api/chat/poll?session_id=sw-9Orcqse_nw7WzrpB&since_id=523 HTTP/1.1" 200 OK
```
