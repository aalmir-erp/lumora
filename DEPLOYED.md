# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"k06H4re7QGux7EIDn6XIxQ"}`

## Build logs
```
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
containerimage.digest: sha256:4a6be7de9ac03f5cbe6436f80d7cd3c5862d4e6d9f71be9e7a07bb628cab7f81
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NGE2YmU3ZGU5YWMwM2Y1Y2JlNjQzNmY4MGQ3Y2QzYzU4NjJkNGU2ZDlmNzFiZTllN2EwN2JiNjI4Y2FiN2Y4MSIsInNpemUiOjI5NTgsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNVQyMTo0ODozNVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:cae9d23cbaaa298657d72a7685daf0e127609a03fcb6e302cb9d1599378f875a
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
INFO:     100.64.0.2:49923 - "GET /api/health HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
Starting Container
INFO:     100.64.0.3:61212 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:37626 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.4:37634 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.5:34866 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.4:37634 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.4:37626 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.5:34866 - "GET /about-app.js HTTP/1.1" 200 OK
INFO:     100.64.0.4:37688 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.4:37642 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.4:37626 - "GET /api/blog/latest?limit=10 HTTP/1.1" 200 OK
INFO:     100.64.0.6:13694 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.4:37654 - "GET /api/brand HTTP/1.1" 200 OK
[push] pywebpush not installed — skipping push send
INFO:     100.64.0.4:37664 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.4:37672 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.6:13694 - "GET / HTTP/1.1" 200 OK
[push] pywebpush not installed — skipping push send
INFO:     100.64.0.6:13694 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.7:33518 - "GET / HTTP/1.1" 200 OK
[push] pywebpush not installed — skipping push send
INFO:     100.64.0.4:61666 - "GET /api/reviews/platforms HTTP/1.1" 200 OK
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [1]
Stopping Container
Stopping Container
```
