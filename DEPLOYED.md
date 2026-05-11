# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"uPzGak4jTjCwKyyX9o6EoQ"}`

## Build logs
```
npm warn deprecated glob@10.5.0: Old versions of glob are not supported, and contain widely publicized security vulnerabilities, which have been fixed in the current version. Please update. Support for old versions may be purchased (at exorbitant rates) by contacting i@izs.me

npm warn deprecated fluent-ffmpeg@2.1.3: Package no longer supported. Contact Support at https://www.npmjs.com/support for more info.


added 300 packages in 9s

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
containerimage.config.digest: sha256:76c1fb7ae709199c9198d7d2c138e3e8c3bd6d01c19cefbaa27bddfc32e7171f
containerimage.digest: sha256:967a658b8578130831f5e9265cf672f64df523227974c7ec0923d637fbe1a221
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6OTY3YTY1OGI4NTc4MTMwODMxZjVlOTI2NWNmNjcyZjY0ZGY1MjMyMjc5NzRjN2VjMDkyM2Q2MzdmYmUxYTIyMSIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xMVQyMDoxMDo1OFoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
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
Mounting volume on: /var/lib/containers/railwayapp/bind-mounts/890b03c2-6356-4499-9526-78bd17478510/vol_onr647rhdeir9di9
[start] launching whatsapp_bridge
[wa-bridge] listening on :3001
Starting Container
INFO:     Waiting for application startup.
[scheduler] started — autoblog 06:00 + 18:00, PSI 03:00, summary 21:00 (Asia/Dubai)
INFO:     Started server process [1]
[purge] scan complete — 22 posts, 0 flagged
[wa-bridge] QR received. Open /qr in your browser to scan.
[seed-users] test accounts ready: test@servia.ae/test123, demo@servia.ae/demo123, vendor@servia.ae/vendor123
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     100.64.0.2:41397 - "GET /api/health HTTP/1.1" 200 OK
[autoblog] catch-up SKIP (last_run @ 2026-05-11T17:02:49.261862Z is fresh AND ok)
[wa-bridge] QR received. Open /qr in your browser to scan.
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.3:13994 - "GET /brand/servia-ziina-avatar-1024.png HTTP/1.1" 200 OK
INFO:     100.64.0.4:16424 - "GET /index.html HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.4:16438 - "GET / HTTP/1.1" 200 OK
[push] pywebpush not installed — skipping push send
INFO:     100.64.0.4:16424 - "GET /index.html HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
```
