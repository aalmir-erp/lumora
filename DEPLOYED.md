# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"Em1LLgWsTDGuVmafCx5-qw"}`

## Build logs
```
[ 1/14] FROM docker.io/library/python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461
[internal] load build context
[internal] load build context
[ 2/14] WORKDIR /app
[ 3/14] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 4/14] COPY requirements.txt ./
[ 5/14] RUN pip install -r requirements.txt
[ 6/14] COPY whatsapp_bridge ./whatsapp_bridge
[ 7/14] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
[ 8/14] COPY app ./app
[ 8/14] COPY app ./app
[ 9/14] COPY web ./web
uploading snapshot
[ 9/14] COPY web ./web
[10/14] COPY _e2e-shots ./_e2e-shots
[10/14] COPY _e2e-shots ./_e2e-shots
[11/14] COPY _release/android ./_release/android
[11/14] COPY _release/android ./_release/android
[12/14] COPY twa/android/twa-manifest.json ./twa/android/twa-manifest.json
[12/14] COPY twa/android/twa-manifest.json ./twa/android/twa-manifest.json
[13/14] COPY start.sh /app/start.sh
[13/14] COPY start.sh /app/start.sh
[14/14] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[14/14] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
exporting to docker image format
exporting to docker image format
containerimage.config.digest: sha256:3060c2e82a8ef370446f0b6714dea867533d389d659d355e141c72b5498a980f
containerimage.digest: sha256:e249738cde6d05aba649d3caf205b2bb8daf301f9ec30bd6ccb13bc4e28d5595
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6ZTI0OTczOGNkZTZkMDVhYmE2NDlkM2NhZjIwNWIyYmI4ZGFmMzAxZjllYzMwYmQ2Y2NiMTNiYzRlMjhkNTU5NSIsInNpemUiOjM1MzMsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xNVQxNTozNTo0MloifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
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
INFO:     100.64.0.3:32640 - "GET /api/admin/ai/catalog HTTP/1.1" 200 OK
INFO:     100.64.0.4:46114 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:46114 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:46114 - "POST /api/admin/conversations/translate HTTP/1.1" 200 OK
INFO:     100.64.0.4:46102 - "POST /api/admin/conversations/translate HTTP/1.1" 200 OK
INFO:     100.64.0.3:19138 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:19138 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:19126 - "POST /api/admin/conversations/translate HTTP/1.1" 200 OK
INFO:     100.64.0.3:27666 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:50190 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:50178 - "POST /api/admin/conversations/translate HTTP/1.1" 200 OK
INFO:     100.64.0.4:50202 - "POST /api/admin/conversations/translate HTTP/1.1" 200 OK
INFO:     100.64.0.3:27674 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:51420 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:50202 - "POST /api/admin/conversations/translate HTTP/1.1" 200 OK
INFO:     100.64.0.4:50202 - "POST /api/admin/conversations/translate HTTP/1.1" 200 OK
INFO:     100.64.0.4:50202 - "POST /api/admin/conversations/translate HTTP/1.1" 200 OK
INFO:     100.64.0.4:50202 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:51418 - "POST /api/admin/conversations/translate HTTP/1.1" 200 OK
INFO:     100.64.0.11:35934 - "GET /api/videos/play/svc-general-cleaning HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.3:52414 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:20042 - "GET /api/chat/poll?session_id=sw-m-fcU-u8sZ01srRg&since_id=711 HTTP/1.1" 200 OK
INFO:     100.64.0.7:23224 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.13:60492 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.3:52414 - "GET /api/chat/poll?session_id=sw-m-fcU-u8sZ01srRg&since_id=711 HTTP/1.1" 200 OK
INFO:     100.64.0.7:23224 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.13:60492 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.4:20042 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:52416 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:46206 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
```
