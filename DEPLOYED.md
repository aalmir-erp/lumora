# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"yDUd1aC_SiKXjN3CGbGh5g"}`

## Build logs
```
[ 6/11] COPY whatsapp_bridge ./whatsapp_bridge
[ 5/11] RUN pip install -r requirements.txt
[ 4/11] COPY requirements.txt ./
[internal] load build context
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
[ 9/11] COPY web ./web
[10/11] COPY start.sh /app/start.sh
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
exporting to docker image format
exporting to docker image format
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6OTA3ZWE5ZWM1ZWI5YmQ3NzAxNzBlN2IzY2ZmOTE1ZmJhYmUwZmMzZmRlMDY0NWE4YjdjNTc2NGYzNzg1YjBiNyIsInNpemUiOjI5NTgsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNlQwNTo0Njo0M1oifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:cb710a41070db111d6775ed7c310de7241f1f6e58b908a560a9ee964b9b6c9fe
containerimage.digest: sha256:907ea9ec5eb9bd770170e7b3cff915fbabe0fc3fde0645a8b7c5764f3785b0b7
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
Starting Container
INFO:     100.64.0.3:50674 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.3:50674 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.3:50674 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:14246 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:14246 - "GET /api/blog/latest?limit=10 HTTP/1.1" 200 OK
INFO:     100.64.0.3:50674 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.3:14254 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.3:14254 - "GET /api/reviews/platforms HTTP/1.1" 200 OK
INFO:     100.64.0.3:14254 - "GET / HTTP/1.1" 304 Not Modified
INFO:     100.64.0.3:14254 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.3:14262 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:14272 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:14254 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.3:14262 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.3:14262 - "GET / HTTP/1.1" 304 Not Modified
INFO:     100.64.0.3:14272 - "GET /api/blog/latest?limit=10 HTTP/1.1" 200 OK
INFO:     100.64.0.3:14262 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.3:14254 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:14272 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:14262 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.3:14272 - "GET /api/blog/latest?limit=10 HTTP/1.1" 200 OK
INFO:     100.64.0.3:14254 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.3:14254 - "GET /api/reviews/platforms HTTP/1.1" 200 OK
INFO:     100.64.0.3:31516 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:31504 - "GET /share-rewards.html HTTP/1.1" 200 OK
INFO:     100.64.0.3:31518 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.4:13792 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
[wa-bridge] QR received. Open /qr in your browser to scan.
```
