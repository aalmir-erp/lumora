# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** BUILDING
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"qzF1OJhQSPWvHjhCnpoFkQ"}`

## Build logs
```
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 2/11] WORKDIR /app
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[internal] load build context
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
containerimage.config.digest: sha256:a998b069d59195718be0060b1b85a2772dc278e1775442519ffe554e01b93c22
containerimage.digest: sha256:e2eabc0cf8f575e4931b6a1f2471c6e430b4fcc3a52acb91966ee945a8439b45
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6ZTJlYWJjMGNmOGY1NzVlNDkzMWI2YTFmMjQ3MWM2ZTQzMGI0ZmNjM2E1MmFjYjkxOTY2ZWU5NDVhODQzOWI0NSIsInNpemUiOjI5NTcsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNFQxNTo1ODo1M1oifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
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
Mounting volume on: /var/lib/containers/railwayapp/bind-mounts/309dc608-8606-47af-ad43-c7b6036731dc/vol_onr647rhdeir9di9
Starting Container
[start] launching whatsapp_bridge
[wa-bridge] listening on :3001
[scheduler] not loaded: BaseScheduler.add_job() got multiple values for argument 'replace_existing'
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     100.64.0.2:37087 - "GET /api/health HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.3:17780 - "POST /api/pay/start HTTP/1.1" 200 OK
INFO:     100.64.0.4:56174 - "GET /me.html?b=LM-FCCDD4 HTTP/1.1" 200 OK
INFO:     100.64.0.8:35502 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.9:40608 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.4:56174 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.6:29096 - "GET /login.html HTTP/1.1" 200 OK
INFO:     100.64.0.3:26278 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.5:31908 - "GET /api/me HTTP/1.1" 401 Unauthorized
INFO:     100.64.0.7:47766 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.10:33516 - "GET /sw.js HTTP/1.1" 200 OK
INFO:     100.64.0.10:33516 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.7:49696 - "GET /sw.js HTTP/1.1" 304 Not Modified
[wa-bridge] QR received. Open /qr in your browser to scan.
```
