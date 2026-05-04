# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"HqcfSUMBRHeLsGhEBT7zVQ"}`

## Build logs
```
npm warn deprecated glob@10.5.0: Old versions of glob are not supported, and contain widely publicized security vulnerabilities, which have been fixed in the current version. Please update. Support for old versions may be purchased (at exorbitant rates) by contacting i@izs.me

npm warn deprecated fluent-ffmpeg@2.1.3: Package no longer supported. Contact Support at https://www.npmjs.com/support for more info.


added 301 packages in 8s

npm notice
npm notice New major version of npm available! 10.8.2 -> 11.13.0
npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.13.0
npm notice To update run: npm install -g npm@11.13.0
npm notice

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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6MzE2MDFlOWNkOGQ2Y2NiZDE2ZDE0YjdjZjBmMDFhYTVhNGZjNGE5NjIyMzc4ZTIxZWY0ODdjZWY3ZjdlYjRmMSIsInNpemUiOjI5NTcsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNFQyMDoyNjo1MFoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:f984b8eee9b08dae33637d8cf4fc814bf22b74cbc3a6296381d4ed40bdd97599
containerimage.digest: sha256:31601e9cd8d6ccbd16d14b7cf0f01aa5a4fc4a9622378e21ef487cef7f7eb4f1
image push
image push
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
INFO:     100.64.0.6:57080 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.6:57104 - "GET /api/admin/bookings?status=pending&limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.6:57122 - "GET /api/admin/bookings?limit=8 HTTP/1.1" 200 OK
INFO:     100.64.0.6:57114 - "GET /api/admin/psi/latest HTTP/1.1" 200 OK
INFO:     100.64.0.6:57114 - "GET /api/admin/analytics HTTP/1.1" 200 OK
INFO:     100.64.0.6:57106 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.6:57122 - "GET /api/admin/bookings?limit=300 HTTP/1.1" 200 OK
INFO:     100.64.0.6:57104 - "GET /api/wa/status HTTP/1.1" 200 OK
INFO:     100.64.0.6:57104 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.6:57122 - "GET /api/admin/stats HTTP/1.1" 200 OK
INFO:     100.64.0.6:57122 - "POST /api/admin/push/subscribe HTTP/1.1" 200 OK
INFO:     100.64.0.6:57104 - "GET /api/videos/list?limit=500 HTTP/1.1" 200 OK
INFO:     100.64.0.6:57106 - "GET /api/blog/latest?limit=200 HTTP/1.1" 200 OK
INFO:     100.64.0.6:57106 - "GET /sw.js HTTP/1.1" 200 OK
INFO:     100.64.0.6:57106 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.6:57106 - "GET /api/admin/ai-listings HTTP/1.1" 200 OK
INFO:     100.64.0.6:57106 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.6:57106 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.6:57106 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.6:57106 - "GET /api/admin/social-images/list?limit=200 HTTP/1.1" 200 OK
INFO:     100.64.0.6:57106 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.6:57106 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.6:57106 - "GET /api/admin/services-summary HTTP/1.1" 200 OK
INFO:     100.64.0.6:57106 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.6:57106 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.6:57106 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.6:57106 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.6:57106 - "POST /api/admin/social-images/generate HTTP/1.1" 200 OK
```
