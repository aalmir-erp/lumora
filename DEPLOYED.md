# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"g5bFmS4fQnOyNqauxtoGcA"}`

## Build logs
```
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 2/11] WORKDIR /app
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[internal] load build context
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
containerimage.digest: sha256:9b2e6e93be922076e46ce251be8fc3bd9288e02197fa82c5457ffd0bb9d334e2
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6OWIyZTZlOTNiZTkyMjA3NmU0NmNlMjUxYmU4ZmMzYmQ5Mjg4ZTAyMTk3ZmE4MmM1NDU3ZmZkMGJiOWQzMzRlMiIsInNpemUiOjI5NTcsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNFQxMjowMjo1N1oifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:eb7b0257b8c0cc7f6eff0c8d88bda0fce63adb1cd26338ab29d6764afe285211
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
INFO:     100.64.0.8:61978 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
INFO:     100.64.0.18:19966 - "GET /logo.svg HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.19:44182 - "GET /api/blog/hero/%24%7Besc%28featured.slug%29%7D.svg HTTP/1.1" 200 OK
INFO:     100.64.0.20:36236 - "GET /install.js HTTP/1.1" 200 OK
INFO:     100.64.0.21:10896 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.22:46412 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
INFO:     100.64.0.23:15382 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.11:59654 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
INFO:     100.64.0.16:47798 - "GET /widget.css HTTP/1.1" 200 OK
INFO:     100.64.0.19:13852 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.15:28418 - "GET /social-proof.js HTTP/1.1" 200 OK
INFO:     100.64.0.3:19226 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.23:42672 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.3:55604 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
INFO:     100.64.0.22:43356 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.23:42672 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
INFO:     100.64.0.13:41718 - "GET /cms.js HTTP/1.1" 200 OK
INFO:     100.64.0.7:60212 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.8:57252 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
INFO:     100.64.0.11:48330 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.25:42048 - "GET /static/style/sys_files/index.js HTTP/1.1" 404 Not Found
INFO:     100.64.0.11:48330 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
INFO:     100.64.0.7:60212 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.24:31834 - "GET /api/blog/hero/%24%7Besc%28p.slug%29%7D.svg HTTP/1.1" 200 OK
INFO:     100.64.0.7:20578 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.23:27918 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
INFO:     100.64.0.8:33496 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.23:27918 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
```
