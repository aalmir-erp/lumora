# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"ok":true,"service":"Lumora","version":"1.14.2","mode":"llm","model":"claude-opus-4-7","wa_bridge":true,"admin_token_hint":null}`

## Build logs
```
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[10/11] COPY start.sh /app/start.sh
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[internal] load build context
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[internal] load build context
[internal] load build context
[ 2/11] WORKDIR /app
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 4/11] COPY requirements.txt ./
[ 5/11] RUN pip install -r requirements.txt
[ 6/11] COPY whatsapp_bridge ./whatsapp_bridge
[ 7/11] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
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
containerimage.digest: sha256:348f99d71d4a4273ed6f80257bc78fb63c73ea129330c9d3151c56d4cdb17783
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6MzQ4Zjk5ZDcxZDRhNDI3M2VkNmY4MDI1N2JjNzhmYjYzYzczZWExMjkzMzBjOWQzMTUxYzU2ZDRjZGIxNzc4MyIsInNpemUiOjI5NTcsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNFQwMDo1Nzo1N1oifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:99b0011624011a3f8a873d37047b9f43f441c39d34c3be1c6c8f1a83482066d5
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
Starting Container
[wa-bridge] listening on :3001
INFO:     Started server process [1]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.4:19020 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.5:58554 - "GET /style.css HTTP/1.1" 200 OK
INFO:     100.64.0.4:19020 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.5:58554 - "GET /social-strip.js HTTP/1.1" 200 OK
INFO:     100.64.0.3:54204 - "GET /app.js HTTP/1.1" 200 OK
INFO:     100.64.0.8:40590 - "GET /cms.js HTTP/1.1" 200 OK
INFO:     100.64.0.4:19032 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.7:54212 - "GET /api/admin/cms HTTP/1.1" 401 Unauthorized
INFO:     100.64.0.5:58556 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.5:58556 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.3:54204 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.10:31486 - "POST /api/app-install HTTP/1.1" 200 OK
```
