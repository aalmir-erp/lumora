# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"fohnY4aaR-Krbp59Cx5-qw"}`

## Build logs
```

added 300 packages in 9s

npm notice
npm notice New major version of npm available! 10.8.2 -> 11.14.1
npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.14.1
npm notice To update run: npm install -g npm@11.14.1
npm notice

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
containerimage.digest: sha256:de83ca7d589c1932a324cc07fb4e993a4cef84b6a0dece0f8eb61c8910093677
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6ZGU4M2NhN2Q1ODljMTkzMmEzMjRjYzA3ZmI0ZTk5M2E0Y2VmODRiNmEwZGVjZTBmOGViNjFjODkxMDA5MzY3NyIsInNpemUiOjM1MzMsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xNVQxNTo0MjowMVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:6ab78a8a14a7df6837759ea941905006b8bf8c17ec58f1f7becd4ac4fb789541
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
INFO:     100.64.0.3:19674 - "GET /api/chat/poll?session_id=sw-m-fcU-u8sZ01srRg&since_id=711 HTTP/1.1" 200 OK
INFO:     100.64.0.7:17342 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.6:53290 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:58388 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.7:17342 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.3:19674 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
INFO:     100.64.0.6:53290 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.4:58388 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:19674 - "POST /api/admin/whatsapp/send HTTP/1.1" 200 OK
INFO:     100.64.0.4:58388 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.3:19674 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
[wa-bridge] qr_received : len=239
INFO:     100.64.0.4:58388 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:19674 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.4:58388 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
INFO:     100.64.0.3:19674 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.8:13362 - "GET /services/move-in-out/arabian-ranches HTTP/1.1" 200 OK
INFO:     100.64.0.4:58388 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.3:19674 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
INFO:     100.64.0.4:58388 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:19674 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.4:58388 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
INFO:     100.64.0.3:19674 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.4:58388 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.3:19674 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
INFO:     100.64.0.4:58388 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:19674 - "GET /api/admin/whatsapp/qr HTTP/1.1" 200 OK
INFO:     100.64.0.4:58388 - "GET /api/admin/alerts?limit=80 HTTP/1.1" 200 OK
[wa-bridge] qr_received : len=239
INFO:     100.64.0.3:19674 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
```
