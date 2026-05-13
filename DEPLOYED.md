# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"C0VTx88ZSrK60IyNezItjw"}`

## Build logs
```
npm warn deprecated glob@10.5.0: Old versions of glob are not supported, and contain widely publicized security vulnerabilities, which have been fixed in the current version. Please update. Support for old versions may be purchased (at exorbitant rates) by contacting i@izs.me

npm warn deprecated fluent-ffmpeg@2.1.3: Package no longer supported. Contact Support at https://www.npmjs.com/support for more info.


added 300 packages in 8s

npm notice
npm notice New major version of npm available! 10.8.2 -> 11.14.1
npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.14.1
npm notice To update run: npm install -g npm@11.14.1
npm notice

[ 7/12] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
[ 8/12] COPY app ./app
[ 8/12] COPY app ./app
[ 9/12] COPY web ./web
[ 9/12] COPY web ./web
[10/12] COPY _e2e-shots ./_e2e-shots
[10/12] COPY _e2e-shots ./_e2e-shots
[11/12] COPY start.sh /app/start.sh
[11/12] COPY start.sh /app/start.sh
[12/12] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[12/12] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
exporting to docker image format
exporting to docker image format
containerimage.digest: sha256:668535f34e1e4e449cfa2e40e4336cc4f38b6ab1ee965a976a0c27d567846678
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NjY4NTM1ZjM0ZTFlNGU0NDljZmEyZTQwZTQzMzZjYzRmMzhiNmFiMWVlOTY1YTk3NmEwYzI3ZDU2Nzg0NjY3OCIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xM1QxODo0MDowNVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:bdf27dea067018e8d5ce318507bd60f0f0b8b3804f083b73a50880d9d7126a44
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
Starting Container
[start] launching whatsapp_bridge
[wa-bridge] listening on :3001
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     Waiting for application startup.
[scheduler] started — autoblog 06:00 + 18:00, PSI 03:00, summary 21:00 (Asia/Dubai)
[lp-ar] 133 Arabic landing-page routes registered
INFO:     Started server process [1]
[lp] 17320 Google Ads landing-page routes registered (base=9384, qualifier=7752, near-me=184, 184 service aliases × 51 areas)
[purge] scan complete — 29 posts, 0 flagged
[seed-users] test accounts ready: test@servia.ae/test123, demo@servia.ae/demo123, vendor@servia.ae/vendor123
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     100.64.0.2:33913 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.5:58384 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.6:59510 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.4:35328 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.3:12382 - "GET /gate.html?inv=Q-1778690765082&amount=367.5 HTTP/1.1" 200 OK
INFO:     100.64.0.3:12382 - "GET / HTTP/1.1" 200 OK
INFO:     100.64.0.3:12392 - "GET /index.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.3:12392 - "GET /index.html HTTP/1.1" 200 OK
INFO:     100.64.0.3:12392 - "GET /q/Q-1778690765082 HTTP/1.1" 200 OK
INFO:     100.64.0.7:40352 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
INFO:     100.64.0.5:42888 - "GET /api/q/Q-1778690765082 HTTP/1.1" 200 OK
INFO:     100.64.0.6:40792 - "GET /api/q/Q-1778690765082 HTTP/1.1" 200 OK
INFO:     100.64.0.6:40792 - "GET /api/q/Q-1778690765082 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
[autoblog] catch-up SKIP (last_run @ 2026-05-13T14:00:00.000637Z is fresh AND ok)
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.8:14352 - "GET /api/chat/poll?session_id=sw-I6iuwfPXJ2LRdtDe&since_id=647 HTTP/1.1" 200 OK
```
