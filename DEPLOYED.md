# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"hc04xuGKRyKEX9VK0_TJvA"}`

## Build logs
```
[ 4/11] COPY requirements.txt ./
[internal] load build context
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 2/11] WORKDIR /app
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[internal] load build context
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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NmNhODc5MDQ0MTJkYTJmNDUxNTg3YTMxZjY1MDQ2MmY1YTA0ODI0ZjA5NDliMmI4NzAxMTlmMWViZDVkOTNiNCIsInNpemUiOjI5NTcsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNVQwOToxMDoyOVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:9c56a89429f7038dbebb4f978a457170595194ea5f03fa6861c43cdd34088376
containerimage.digest: sha256:6ca87904412da2f451587a31f650462f5a04824f0949b2b870119f1ebd5d93b4
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
Mounting volume on: /var/lib/containers/railwayapp/bind-mounts/12c9c8ff-a256-4f77-b230-92ddb2fcfeff/vol_onr647rhdeir9di9
Starting Container
[start] launching whatsapp_bridge
[wa-bridge] listening on :3001
[scheduler] not loaded: BaseScheduler.add_job() got multiple values for argument 'replace_existing'
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     100.64.0.2:54665 - "GET /api/health HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.3:52508 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:50876 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:60708 - "GET /redoc HTTP/1.1" 404 Not Found
INFO:     100.64.0.3:60708 - "GET /sw.js HTTP/1.1" 200 OK
INFO:     100.64.0.3:14340 - "GET //docs HTTP/1.1" 404 Not Found
INFO:     100.64.0.3:14340 - "GET /sw.js HTTP/1.1" 304 Not Modified
INFO:     100.64.0.3:14340 - "GET /docs HTTP/1.1" 404 Not Found
INFO:     100.64.0.3:14340 - "GET /sw.js HTTP/1.1" 304 Not Modified
INFO:     100.64.0.3:41332 - "GET /openapi.json HTTP/1.1" 200 OK
INFO:     100.64.0.3:41332 - "GET /favicon.ico HTTP/1.1" 404 Not Found
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.3:24178 - "GET /docs HTTP/1.1" 404 Not Found
INFO:     100.64.0.3:24178 - "GET /favicon.ico HTTP/1.1" 404 Not Found
INFO:     100.64.0.3:24178 - "GET /redoc HTTP/1.1" 404 Not Found
INFO:     100.64.0.3:24178 - "GET /favicon.ico HTTP/1.1" 404 Not Found
INFO:     100.64.0.3:24178 - "GET /redoc HTTP/1.1" 404 Not Found
INFO:     100.64.0.3:24178 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:18306 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
```
