# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"wSFSHIBKSWSTcRHdaP71AA"}`

## Build logs
```
npm notice
npm notice New major version of npm available! 10.8.2 -> 11.14.1
npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.14.1
npm notice To update run: npm install -g npm@11.14.1
npm notice


added 300 packages in 14s

[ 7/14] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
[ 8/14] COPY app ./app
[ 8/14] COPY app ./app
[ 9/14] COPY web ./web
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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NWVmODlhODlkMTQ2ZDExY2U5MWJiZTA4ZGU1Y2I0NzAyZjI0OGNjMTU5M2M3Njc5ZDM4NGJhNTUxNWM4YTMwZiIsInNpemUiOjM1MzMsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xNVQxNzoxMjoyN1oifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:dd6fe6e74ff3dae31c035c2bbd16472225d1730f34400687428bf44df811585e
containerimage.digest: sha256:5ef89a89d146d11ce91bbe08de5cb4702f248cc1593c7679d384ba5515c8a30f
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
INFO:     100.64.0.4:21182 - "GET /api/chat/poll?session_id=sw-m-fcU-u8sZ01srRg&since_id=759 HTTP/1.1" 200 OK
INFO:     100.64.0.3:46458 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:46458 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:46458 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:46458 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:46458 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:46458 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.5:25330 - "GET /app.js?v=1.24.221 HTTP/1.1" 200 OK
INFO:     100.64.0.3:46458 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:46458 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
[wa-bridge] qr_received : len=239
INFO:     100.64.0.3:46458 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
[autoblog] catch-up SKIP (last_run @ 2026-05-15T14:00:00.000743Z is fresh AND ok)
INFO:     100.64.0.3:46458 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:46458 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:46458 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:46458 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
[wa-bridge] qr_received : len=239
INFO:     100.64.0.3:46458 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:46458 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:46458 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:27030 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:46458 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.3:27030 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.6:23058 - "GET /api/chat/poll?session_id=sw-m-fcU-u8sZ01srRg&since_id=759 HTTP/1.1" 200 OK
INFO:     100.64.0.3:27030 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:27030 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
[wa-bridge] qr_received : len=239
INFO:     100.64.0.3:27030 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:27030 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
```
