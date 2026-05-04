# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"ok":true,"service":"Lumora","version":"1.18.3","mode":"llm","model":"claude-opus-4-7","wa_bridge":true,"admin_token_hint":null}`

## Build logs
```
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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6ZTcwN2RiYmJlMTI3MmY0MTljZGIwMGMwM2VhMjYxMDkyODVhYzJmZjIzNWUxYjc2NDhlNjM1ZTU0NjRjNmE4OCIsInNpemUiOjI5NTcsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNFQwNTozOTo0M1oifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:46a48535958e21d21818b3441d6c82ed5e691b995e95c74be512336a92de0a0d
containerimage.digest: sha256:e707dbbbe1272f419cdb00c03ea26109285ac2ff235e1b7648e635e5464c6a88
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
Mounting volume on: /var/lib/containers/railwayapp/bind-mounts/72082d3c-1e18-4b78-9855-f5fc178e652d/vol_onr647rhdeir9di9
[start] launching whatsapp_bridge
Starting Container
[wa-bridge] listening on :3001
[scheduler] not loaded: BaseScheduler.add_job() got multiple values for argument 'replace_existing'
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     100.64.0.2:45639 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:24878 - "GET /api/admin/conversations?session_id=sw-d0jeCdh4pRKd_iK6 HTTP/1.1" 200 OK
INFO:     100.64.0.3:24878 - "GET /api/admin/ai/catalog HTTP/1.1" 200 OK
INFO:     100.64.0.5:34002 - "GET /api/admin/sessions?q=sw-EF1g8WxazhbO8Qa4 HTTP/1.1" 200 OK
INFO:     100.64.0.5:34002 - "GET /api/admin/ai/catalog HTTP/1.1" 200 OK
INFO:     100.64.0.5:34002 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
```
