# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"0670PvV-TsmMOxr7g4a9AQ"}`

## Build logs
```
[10/11] COPY start.sh /app/start.sh
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[ 8/11] COPY app ./app
[ 4/11] COPY requirements.txt ./
[python-base 1/5] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[python-base 1/5] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[python-base 1/5] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[internal] load build context
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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6N2I5YjNiZDU5MjdkZTA4ZWE3ZDBjYTZlNzUxY2FmODU1ZDVkNTNhMGZkOWNjMzNiYjY1ODcwZDVmNTIzNzVhNiIsInNpemUiOjI5NTgsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNVQxODoyMjoyMVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:f5434fd53762601a4845322998b27022c1cd56f8567e706fc160cbc373b4f1c9
containerimage.digest: sha256:7b9b3bd5927de08ea7d0ca6e751caf855d5d53a0fd9cc33bb65870d5f52375a6
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
INFO:     100.64.0.18:44798 - "GET /api/blog/latest?limit=10 HTTP/1.1" 200 OK
INFO:     100.64.0.16:16434 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.16:16434 - "GET /api/reviews/platforms HTTP/1.1" 200 OK
INFO:     100.64.0.16:16434 - "GET /mascots/cleaning.svg HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.16:16434 - "GET /api/blog/list?limit=80 HTTP/1.1" 404 Not Found
INFO:     100.64.0.7:18412 - "GET /brand/servia-icon-1024x1024.png HTTP/1.1" 200 OK
INFO:     100.64.0.19:32184 - "GET /mascots/ac.svg HTTP/1.1" 200 OK
INFO:     100.64.0.5:23588 - "GET /mascots/handyman.svg HTTP/1.1" 200 OK
INFO:     100.64.0.13:59852 - "GET /mascots/pool.svg HTTP/1.1" 200 OK
INFO:     100.64.0.17:45386 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:27326 - "GET /mascots/garden.svg HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.11:11370 - "GET / HTTP/1.1" 200 OK
[push] pywebpush not installed — skipping push send
INFO:     100.64.0.16:45530 - "GET /services.html HTTP/1.1" 200 OK
INFO:     100.64.0.16:45530 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.16:45542 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.16:45560 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.11:11370 - "GET /?lang=en HTTP/1.1" 200 OK
INFO:     100.64.0.16:45560 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.16:45530 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.7:45082 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.16:45560 - "GET /api/blog/list?limit=80 HTTP/1.1" 404 Not Found
INFO:     100.64.0.4:60354 - "GET /conv.js HTTP/1.1" 200 OK
INFO:     100.64.0.18:59662 - "GET /search-widget.js HTTP/1.1" 200 OK
INFO:     100.64.0.7:38074 - "GET /assets/js/qr_modal.js HTTP/1.1" 404 Not Found
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.11:24122 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.6:28252 - "GET /brand/servia-icon-1024x1024.png HTTP/1.1" 200 OK
```
