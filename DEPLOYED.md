# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"j-Q0CSvQQNKzqrLx9I3ezw"}`

## Build logs
```
[internal] load build context
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 2/11] WORKDIR /app
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[10/11] COPY start.sh /app/start.sh
[ 9/11] COPY web ./web
[ 8/11] COPY app ./app
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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6MzE4NTc0YTZjMGRlN2I4MjUyNDhiZGRkZjA1YTBmYTJmNjhmMDA5MmM3OWEyNmJiZGJiY2ViODJmMDc3YWI1ZCIsInNpemUiOjI5NTgsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNlQwNTo1MzowNFoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:cc5ece4d021b847a36fda4ff440747aa0e45359bd3afe232c5737dc0eebc60e9
containerimage.digest: sha256:318574a6c0de7b825248bdddf05a0fa2f68f0092c79a26bbdbbceb82f077ab5d
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
INFO:     100.64.0.3:58854 - "GET / HTTP/1.1" 304 Not Modified
INFO:     100.64.0.3:58854 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:58832 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.4:62550 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:58832 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.4:62550 - "GET /api/blog/latest?limit=10 HTTP/1.1" 200 OK
INFO:     100.64.0.4:21750 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.4:62550 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.3:18218 - "GET /api/reviews/platforms HTTP/1.1" 200 OK
INFO:     100.64.0.4:21770 - "GET / HTTP/1.1" 304 Not Modified
INFO:     100.64.0.3:18228 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.3:18236 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:18248 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:18274 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.3:18264 - "GET /api/blog/latest?limit=10 HTTP/1.1" 200 OK
INFO:     100.64.0.3:18280 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.4:21770 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:18228 - "GET / HTTP/1.1" 304 Not Modified
INFO:     100.64.0.4:21770 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.4:21462 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.4:21478 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.3:18228 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.4:21462 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.4:21478 - "GET /api/blog/latest?limit=10 HTTP/1.1" 200 OK
INFO:     100.64.0.4:21770 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.3:26156 - "GET /api/reviews/platforms HTTP/1.1" 200 OK
INFO:     100.64.0.5:32144 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:43010 - "GET /nfc.html HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
[wa-bridge] QR received. Open /qr in your browser to scan.
```
