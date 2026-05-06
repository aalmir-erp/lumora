# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"KnLcwl0SRkq8X4abc9o55Q"}`

## Build logs
```
[ 8/11] COPY app ./app
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
[internal] load build context
uploading snapshot
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
containerimage.config.digest: sha256:3d6d3989573e6ab015b63b1f78fab788f2ca40599974dc544e6d5a69983debce
containerimage.digest: sha256:41c1da55f0db2404ad4f63850be7bdfe5999ba05a34639a48ec74193bbac8b3b
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NDFjMWRhNTVmMGRiMjQwNGFkNGY2Mzg1MGJlN2JkZmU1OTk5YmEwNWEzNDYzOWE0OGVjNzQxOTNiYmFjOGIzYiIsInNpemUiOjI5NTksImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNlQxODo1ODozOVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
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
INFO:     100.64.0.8:14286 - "GET /api/chat/poll?session_id=sw-_Keo61ma9Y8rH3js&since_id=343 HTTP/1.1" 200 OK
INFO:     100.64.0.4:22726 - "GET /api/chat/poll?session_id=sw-_Keo61ma9Y8rH3js&since_id=343 HTTP/1.1" 200 OK
INFO:     100.64.0.6:58302 - "GET /api/chat/poll?session_id=sw-_Keo61ma9Y8rH3js&since_id=343 HTTP/1.1" 200 OK
INFO:     100.64.0.9:24002 - "GET /api/chat/poll?session_id=sw-_Keo61ma9Y8rH3js&since_id=343 HTTP/1.1" 200 OK
INFO:     100.64.0.6:58316 - "GET /api/chat/poll?session_id=sw-_Keo61ma9Y8rH3js&since_id=343 HTTP/1.1" 200 OK
INFO:     100.64.0.7:19478 - "GET /api/chat/poll?session_id=sw-_Keo61ma9Y8rH3js&since_id=343 HTTP/1.1" 200 OK
INFO:     100.64.0.6:58330 - "GET /api/chat/poll?session_id=sw-_Keo61ma9Y8rH3js&since_id=343 HTTP/1.1" 200 OK
INFO:     100.64.0.4:22734 - "GET /api/chat/poll?session_id=sw-_Keo61ma9Y8rH3js&since_id=343 HTTP/1.1" 200 OK
INFO:     100.64.0.4:22740 - "GET /api/chat/poll?session_id=sw-_Keo61ma9Y8rH3js&since_id=343 HTTP/1.1" 200 OK
INFO:     100.64.0.3:40018 - "GET /api/chat/poll?session_id=sw-_Keo61ma9Y8rH3js&since_id=343 HTTP/1.1" 200 OK
INFO:     100.64.0.9:24002 - "GET /api/chat/poll?session_id=sw-_Keo61ma9Y8rH3js&since_id=343 HTTP/1.1" 200 OK
INFO:     100.64.0.8:14286 - "GET /api/chat/poll?session_id=sw-_Keo61ma9Y8rH3js&since_id=343 HTTP/1.1" 200 OK
INFO:     100.64.0.7:19478 - "GET /api/chat/poll?session_id=sw-_Keo61ma9Y8rH3js&since_id=343 HTTP/1.1" 200 OK
INFO:     100.64.0.4:22740 - "GET /api/chat/poll?session_id=sw-_Keo61ma9Y8rH3js&since_id=343 HTTP/1.1" 200 OK
INFO:     100.64.0.4:22740 - "GET /api/chat/poll?session_id=sw-_Keo61ma9Y8rH3js&since_id=343 HTTP/1.1" 200 OK
INFO:     100.64.0.3:40018 - "GET /api/chat/poll?session_id=sw-_Keo61ma9Y8rH3js&since_id=343 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.5:40444 - "GET /api/chat/poll?session_id=sw-_Keo61ma9Y8rH3js&since_id=343 HTTP/1.1" 200 OK
INFO:     100.64.0.10:51072 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.6:10844 - "GET /api/chat/poll?session_id=sw-_Keo61ma9Y8rH3js&since_id=343 HTTP/1.1" 200 OK
INFO:     100.64.0.3:12532 - "GET /api/chat/poll?session_id=sw-_Keo61ma9Y8rH3js&since_id=343 HTTP/1.1" 200 OK
INFO:     100.64.0.6:10854 - "GET /api/chat/poll?session_id=sw-_Keo61ma9Y8rH3js&since_id=343 HTTP/1.1" 200 OK
INFO:     100.64.0.4:39254 - "GET /api/chat/poll?session_id=sw-_Keo61ma9Y8rH3js&since_id=343 HTTP/1.1" 200 OK
INFO:     100.64.0.6:19144 - "GET /api/chat/poll?session_id=sw-_Keo61ma9Y8rH3js&since_id=343 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.5:14802 - "GET /api/chat/poll?session_id=sw-_Keo61ma9Y8rH3js&since_id=343 HTTP/1.1" 200 OK
INFO:     100.64.0.6:60582 - "GET /api/chat/poll?session_id=sw-_Keo61ma9Y8rH3js&since_id=343 HTTP/1.1" 200 OK
INFO:     100.64.0.3:12282 - "GET /api/chat/poll?session_id=sw-_Keo61ma9Y8rH3js&since_id=343 HTTP/1.1" 200 OK
INFO:     100.64.0.6:55272 - "GET /api/chat/poll?session_id=sw-_Keo61ma9Y8rH3js&since_id=343 HTTP/1.1" 200 OK
INFO:     100.64.0.4:28272 - "GET /api/chat/poll?session_id=sw-_Keo61ma9Y8rH3js&since_id=343 HTTP/1.1" 200 OK
```
