# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"blCuL1_aRRGa2UjKBT7zVQ"}`

## Build logs
```
[internal] load build context
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 2/11] WORKDIR /app
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
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
containerimage.config.digest: sha256:22a0418d1167d75b1596592144f9537c5c9209a731a83799d48975f6028ab001
containerimage.digest: sha256:24b1edcb3cec76e538f835c6d33f0f19ca9a404f5b4fd0c0196474616cd99951
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6MjRiMWVkY2IzY2VjNzZlNTM4ZjgzNWM2ZDMzZjBmMTljYTlhNDA0ZjViNGZkMGMwMTk2NDc0NjE2Y2Q5OTk1MSIsInNpemUiOjI5NTcsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNFQxMDozMDo0N1oifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
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
Mounting volume on: /var/lib/containers/railwayapp/bind-mounts/4387ffe6-f10b-45ea-9402-00a9958351f5/vol_onr647rhdeir9di9
Starting Container
[start] launching whatsapp_bridge
[wa-bridge] listening on :3001
INFO:     Started server process [1]
INFO:     Waiting for application startup.
[scheduler] not loaded: BaseScheduler.add_job() got multiple values for argument 'replace_existing'
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.2:42195 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:25624 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.4:16526 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.4:16536 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.3:25624 - "GET /api/blog/latest?limit=10 HTTP/1.1" 200 OK
INFO:     100.64.0.4:16526 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.5:33638 - "GET /api/admin/cms HTTP/1.1" 401 Unauthorized
INFO:     100.64.0.6:52044 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.7:59014 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.5:33638 - "GET /sw.js HTTP/1.1" 200 OK
INFO:     100.64.0.4:16526 - "GET /icon-512.svg HTTP/1.1" 200 OK
INFO:     100.64.0.7:59014 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.3:25900 - "GET /mascots/cleaning.svg HTTP/1.1" 200 OK
INFO:     100.64.0.8:30600 - "GET /api/activity/live HTTP/1.1" 200 OK
INFO:     100.64.0.3:54532 - "GET /mascots/ac.svg HTTP/1.1" 200 OK
INFO:     100.64.0.9:12358 - "GET /mascots/handyman.svg HTTP/1.1" 200 OK
INFO:     100.64.0.8:42394 - "GET /mascots/pool.svg HTTP/1.1" 200 OK
INFO:     100.64.0.6:30444 - "GET /mascots/garden.svg HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.10:32972 - "GET /api/activity/live HTTP/1.1" 200 OK
```
