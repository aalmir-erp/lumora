# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"e7Pge-kTS0ywj_lXaP71AA"}`

## Build logs
```
[ 4/11] COPY requirements.txt ./
[internal] load build context
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[builder 1/6] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[builder 1/6] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[stage-3  2/15] WORKDIR /app
[stage-3  2/15] WORKDIR /app
[builder 1/6] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[builder 1/6] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[10/11] COPY start.sh /app/start.sh
[ 9/11] COPY web ./web
[ 8/11] COPY app ./app
[ 7/11] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
[ 6/11] COPY whatsapp_bridge ./whatsapp_bridge
[internal] load build context
[internal] load build context
[internal] load build context
[internal] load build context
[ 7/11] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
[ 8/11] COPY app ./app
[ 9/11] COPY web ./web
[10/11] COPY start.sh /app/start.sh
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
exporting to docker image format
exporting to docker image format
containerimage.digest: sha256:23e1e1ab9b6bc2d7f4879007356475857c02a67fe49e012a83f2b3622ad394d6
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6MjNlMWUxYWI5YjZiYzJkN2Y0ODc5MDA3MzU2NDc1ODU3YzAyYTY3ZmU0OWUwMTJhODNmMmIzNjIyYWQzOTRkNiIsInNpemUiOjI5NTgsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNVQxODoyNjo1M1oifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:9240add11673c1bab470d80ea71b1f07a647994585eca1510475aa7777f12c6b
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
INFO:     Waiting for application startup.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     Application startup complete.
INFO:     100.64.0.2:40243 - "GET /api/health HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.3:20194 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:59172 - "GET / HTTP/1.1" 200 OK
[push] pywebpush not installed — skipping push send
INFO:     100.64.0.4:59172 - "GET //wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
INFO:     100.64.0.4:59172 - "GET //xmlrpc.php?rsd HTTP/1.1" 404 Not Found
INFO:     100.64.0.4:59172 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.4:59172 - "GET //blog/wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
INFO:     100.64.0.4:59172 - "GET //web/wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
INFO:     100.64.0.4:59172 - "GET //wordpress/wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
INFO:     100.64.0.4:59172 - "GET //website/wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
INFO:     100.64.0.4:59172 - "GET //wp/wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
INFO:     100.64.0.4:59172 - "GET //news/wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
INFO:     100.64.0.4:59172 - "GET //2018/wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
INFO:     100.64.0.4:59172 - "GET //2019/wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
INFO:     100.64.0.4:59172 - "GET //shop/wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
INFO:     100.64.0.4:59172 - "GET //wp1/wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
INFO:     100.64.0.4:59172 - "GET //test/wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
INFO:     100.64.0.4:59172 - "GET //media/wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
INFO:     100.64.0.4:59172 - "GET //wp2/wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
INFO:     100.64.0.4:59172 - "GET //site/wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
INFO:     100.64.0.4:59172 - "GET //cms/wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
INFO:     100.64.0.4:59172 - "GET //sito/wp-includes/wlwmanifest.xml HTTP/1.1" 404 Not Found
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.5:45708 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
```
