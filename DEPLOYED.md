# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"GDgLGY_MRCS-Zz3uU79b0g"}`

## Build logs
```
[10/11] COPY start.sh /app/start.sh
[ 9/11] COPY web ./web
[ 8/11] COPY app ./app
[internal] load build context
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6YjExYTMyYWI4OGJhY2ExNjk1Nzk5OGEzMzNhZTc5Njk0NmRhNmFmNDlkNjY4NDJlZmExM2RjNTY2MTcyYTViYiIsInNpemUiOjI5NTksImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wOVQxNjo0NzowOFoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:369535b98261f44cd341acba7a895b15a14cefd29c236edb908ef204e2f68254
containerimage.digest: sha256:b11a32ab88baca16957998a333ae796946da6af49d66842efa13dc566172a5bb
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
INFO:     100.64.0.3:41446 - "GET /api/chat/poll?session_id=sw-Ic8jepbVq2x8mZVK&since_id=428 HTTP/1.1" 200 OK
INFO:     100.64.0.3:41446 - "GET /api/reviews/platforms HTTP/1.1" 200 OK
INFO:     100.64.0.3:41446 - "GET /api/admin/live/feed?since=2026-05-09T16%3A48%3A27.528428Z HTTP/1.1" 200 OK
INFO:     100.64.0.3:41446 - "GET /api/chat/poll?session_id=sw-Ic8jepbVq2x8mZVK&since_id=428 HTTP/1.1" 200 OK
INFO:     100.64.0.3:41446 - "GET /api/chat/poll?session_id=sw-HCas2tyyj37gmad4&since_id=0 HTTP/1.1" 200 OK
INFO:     100.64.0.3:41446 - "GET /api/admin/live/feed?since=2026-05-09T16%3A48%3A31.523790Z HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.3:41446 - "GET /api/chat/poll?session_id=sw-Ic8jepbVq2x8mZVK&since_id=428 HTTP/1.1" 200 OK
INFO:     100.64.0.3:41446 - "GET /api/chat/poll?session_id=sw-HCas2tyyj37gmad4&since_id=433 HTTP/1.1" 200 OK
INFO:     100.64.0.3:41446 - "GET /api/admin/live/feed?since=2026-05-09T16%3A48%3A35.530217Z HTTP/1.1" 200 OK
INFO:     100.64.0.3:41446 - "GET /api/chat/poll?session_id=sw-Ic8jepbVq2x8mZVK&since_id=428 HTTP/1.1" 200 OK
INFO:     100.64.0.3:41446 - "GET /api/chat/poll?session_id=sw-Ic8jepbVq2x8mZVK&since_id=428 HTTP/1.1" 200 OK
INFO:     100.64.0.3:41446 - "GET /api/admin/live/feed?since=2026-05-09T16%3A48%3A39.522695Z HTTP/1.1" 200 OK
INFO:     100.64.0.3:41446 - "GET /api/chat/poll?session_id=sw-Ic8jepbVq2x8mZVK&since_id=428 HTTP/1.1" 200 OK
INFO:     100.64.0.3:41446 - "GET /api/admin/live/feed?since=2026-05-09T16%3A48%3A43.528276Z HTTP/1.1" 200 OK
INFO:     100.64.0.3:41446 - "GET /api/chat/poll?session_id=sw-Ic8jepbVq2x8mZVK&since_id=428 HTTP/1.1" 200 OK
INFO:     100.64.0.3:41446 - "GET /api/admin/live/feed?since=2026-05-09T16%3A48%3A47.527979Z HTTP/1.1" 200 OK
INFO:     100.64.0.3:41446 - "GET /api/chat/poll?session_id=sw-Ic8jepbVq2x8mZVK&since_id=428 HTTP/1.1" 200 OK
INFO:     100.64.0.3:41446 - "GET /api/admin/live/feed?since=2026-05-09T16%3A48%3A51.508248Z HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.3:41446 - "GET /api/chat/poll?session_id=sw-Ic8jepbVq2x8mZVK&since_id=428 HTTP/1.1" 200 OK
INFO:     100.64.0.3:41446 - "GET /api/admin/live/feed?since=2026-05-09T16%3A48%3A55.504716Z HTTP/1.1" 200 OK
INFO:     100.64.0.3:41446 - "GET /api/chat/poll?session_id=sw-Ic8jepbVq2x8mZVK&since_id=428 HTTP/1.1" 200 OK
INFO:     100.64.0.3:41446 - "GET /api/admin/live/feed?since=2026-05-09T16%3A48%3A59.524716Z HTTP/1.1" 200 OK
INFO:     100.64.0.3:41446 - "GET /api/chat/poll?session_id=sw-Ic8jepbVq2x8mZVK&since_id=428 HTTP/1.1" 200 OK
INFO:     100.64.0.3:41446 - "GET /api/admin/live/feed?since=2026-05-09T16%3A49%3A03.497600Z HTTP/1.1" 200 OK
INFO:     100.64.0.3:41446 - "GET /api/chat/poll?session_id=sw-Ic8jepbVq2x8mZVK&since_id=428 HTTP/1.1" 200 OK
INFO:     100.64.0.3:41446 - "GET /api/chat/poll?session_id=sw-Ic8jepbVq2x8mZVK&since_id=428 HTTP/1.1" 200 OK
INFO:     100.64.0.3:41446 - "GET /api/chat/poll?session_id=sw-Ic8jepbVq2x8mZVK&since_id=428 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
```
