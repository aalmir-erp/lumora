# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"P9JJ0QLTTKy092FVnpoFkQ"}`

## Build logs
```
[ 7/11] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
[ 6/11] COPY whatsapp_bridge ./whatsapp_bridge
[ 5/11] RUN pip install -r requirements.txt
[ 4/11] COPY requirements.txt ./
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
[ 9/11] COPY web ./web
[10/11] COPY start.sh /app/start.sh
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
exporting to docker image format
exporting to docker image format
containerimage.digest: sha256:b981ddd88510589c6140f53fecc9d8e99dd836e8c85b3260cd7d68f9cb4bebea
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6Yjk4MWRkZDg4NTEwNTg5YzYxNDBmNTNmZWNjOWQ4ZTk5ZGQ4MzZlOGM4NWIzMjYwY2Q3ZDY4ZjljYjRiZWJlYSIsInNpemUiOjI5NTgsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNlQwNzo1MjowMVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:c3f5b2384573ae39d5d6c2507253f6c1c2bd4c8304029c46be52dfc93eea1cfa
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
INFO:     100.64.0.4:24438 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.4:24422 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.4:24434 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.4:24422 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.4:24422 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.3:33668 - "GET /book.html?nfc=zzzzbogus99 HTTP/1.1" 200 OK
INFO:     100.64.0.6:41344 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.6:41356 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.6:41364 - "GET /api/nfc/tag/zzzzbogus99 HTTP/1.1" 404 Not Found
INFO:     100.64.0.6:41344 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.6:41368 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.6:41356 - "GET /book.html?nfc=zzzzbogus99 HTTP/1.1" 304 Not Modified
INFO:     100.64.0.5:23254 - "GET /cart.html HTTP/1.1" 200 OK
INFO:     100.64.0.6:41356 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.6:41344 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.6:41368 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.7:50350 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.7:50350 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.4:24422 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.4:24438 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.4:24438 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.4:24422 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.4:24422 - "GET / HTTP/1.1" 304 Not Modified
INFO:     100.64.0.9:24842 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [1]
Stopping Container
Stopping Container
```
