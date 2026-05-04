# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"E63QCf_LRdGLSGeEAax-fw"}`

## Build logs
```
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 2/11] WORKDIR /app
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[internal] load build context
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
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
containerimage.config.digest: sha256:121276f2a21ef2f3cf132feb9845fd5e8430144609c9d8daea6a86a06b48733c
containerimage.digest: sha256:2dbd09f567127c1ab156b85ecb7ecf9808888f3be56ee1b31704fd6f3a48bc9e
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6MmRiZDA5ZjU2NzEyN2MxYWIxNTZiODVlY2I3ZWNmOTgwODg4OGYzYmU1NmVlMWIzMTcwNGZkNmYzYTQ4YmM5ZSIsInNpemUiOjI5NTcsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNFQxMTo0MDoyM1oifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
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
Mounting volume on: /var/lib/containers/railwayapp/bind-mounts/0c3a5047-1b71-4d47-92cf-3fbad6983730/vol_onr647rhdeir9di9
Starting Container
[start] launching whatsapp_bridge
[wa-bridge] listening on :3001
[scheduler] not loaded: BaseScheduler.add_job() got multiple values for argument 'replace_existing'
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.2:37353 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:48370 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:14968 - "GET /api/activity/live HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.5:19544 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.6:56088 - "GET /banner.js HTTP/1.1" 200 OK
INFO:     100.64.0.7:49962 - "GET /install.js HTTP/1.1" 200 OK
INFO:     100.64.0.10:49454 - "GET /logo.svg HTTP/1.1" 200 OK
INFO:     100.64.0.7:49938 - "GET /social-strip.js HTTP/1.1" 200 OK
INFO:     100.64.0.9:30852 - "GET /share.js HTTP/1.1" 200 OK
INFO:     100.64.0.8:13956 - "GET /social-proof.js HTTP/1.1" 200 OK
INFO:     100.64.0.9:30852 - "GET /_snippets.js HTTP/1.1" 200 OK
INFO:     100.64.0.12:26540 - "GET /app.js HTTP/1.1" 200 OK
INFO:     100.64.0.11:35626 - "GET /mascot.svg HTTP/1.1" 200 OK
INFO:     100.64.0.7:49950 - "GET /cart-badge.js HTTP/1.1" 200 OK
INFO:     100.64.0.13:10558 - "GET /cms.js HTTP/1.1" 200 OK
INFO:     100.64.0.5:19544 - "GET /theme.js HTTP/1.1" 200 OK
INFO:     100.64.0.4:31274 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.14:46394 - "GET /api/activity/live HTTP/1.1" 200 OK
```
