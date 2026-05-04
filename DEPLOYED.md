# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"CMNSLYRzQMavZUxcwoOzXw"}`

## Build logs
```
[10/11] COPY start.sh /app/start.sh
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[ 6/11] COPY whatsapp_bridge ./whatsapp_bridge
[internal] load build context
[1/6] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[1/6] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[1/6] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[2/6] WORKDIR /app
[2/6] WORKDIR /app
[internal] load build context
[internal] load build context
[internal] load build context
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
containerimage.digest: sha256:943cabc0bd6fd9c913537a7883af3d24e8f361ddfa99888b532a17c2a81f2497
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6OTQzY2FiYzBiZDZmZDljOTEzNTM3YTc4ODNhZjNkMjRlOGYzNjFkZGZhOTk4ODhiNTMyYTE3YzJhODFmMjQ5NyIsInNpemUiOjI5NTcsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNFQxMToxMzoxM1oifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:9b36b5976ed3c60f37c202ac4e8f5f56787a8cef207d34740a072ee718307bf2
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
INFO:     100.64.0.3:40518 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
INFO:     100.64.0.3:40518 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.9:34770 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.8:20324 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
INFO:     100.64.0.9:34778 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.4:36296 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
INFO:     100.64.0.3:27294 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.3:27294 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.6:39902 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.8:24156 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
INFO:     100.64.0.9:27334 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.8:54246 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.8:54246 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
INFO:     100.64.0.6:42124 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.9:27334 - "POST /api/admin/ai/test/openai HTTP/1.1" 200 OK
INFO:     100.64.0.9:27334 - "POST /api/admin/ai/test/google HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.4:43254 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:54550 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.10:58844 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
INFO:     100.64.0.4:43254 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:54564 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:54564 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.11:13200 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:58992 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.4:58992 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.9:52392 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:58992 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
```
