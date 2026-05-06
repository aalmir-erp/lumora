# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"fsFbDUa0S2W-yIsj0_TJvA"}`

## Build logs
```
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 2/11] WORKDIR /app
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[10/11] COPY start.sh /app/start.sh
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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NDQ4ZGM3NTAwODUwMGU1MjdiMjhjNTliYzIzMjJjMDhlMmUxNGEzYTBkOGU1NzFiMmU0NjQ2YzM1NzU0Y2Y5NCIsInNpemUiOjI5NTgsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNlQwMDoyNjo0OFoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:b09fe6849e4d90fd1b5c96f5dbbeaa3ac71683aed62d09046eb9be49050e07a5
containerimage.digest: sha256:448dc75008500e527b28c59bc2322c08e2e14a3a0d8e571b2e4646c35754cf94
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
INFO:     100.64.0.5:53820 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.5:53852 - "GET /book.html?service=deep_cleaning HTTP/1.1" 304 Not Modified
INFO:     100.64.0.5:53820 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.5:53852 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.5:53830 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.5:53846 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.5:53852 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.5:53830 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.5:53862 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.6:29864 - "GET /book.html?nfc=zzzzbogus99 HTTP/1.1" 200 OK
INFO:     100.64.0.11:52748 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.11:52730 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.11:52748 - "GET /api/nfc/tag/zzzzbogus99 HTTP/1.1" 404 Not Found
INFO:     100.64.0.11:52754 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.11:52758 - "GET /book.html?nfc=zzzzbogus99 HTTP/1.1" 304 Not Modified
INFO:     100.64.0.11:52730 - "GET /api/services HTTP/1.1" 200 OK
INFO:     Shutting down
INFO:     100.64.0.11:52774 - "GET /api/nfc/tag/zzzzbogus99 HTTP/1.1" 404 Not Found
INFO:     100.64.0.11:52748 - "GET /api/services HTTP/1.1" 200 OK
INFO:     Waiting for application shutdown.
INFO:     100.64.0.11:52754 - "GET /api/services HTTP/1.1" 200 OK
INFO:     Application shutdown complete.
INFO:     Finished server process [1]
INFO:     100.64.0.11:52748 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.11:52730 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.11:52758 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.11:52748 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.11:52758 - "GET /api/i18n HTTP/1.1" 200 OK
Stopping Container
Stopping Container
```
