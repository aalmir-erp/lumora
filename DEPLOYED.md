# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"fj4NZyI6Tj6On4itWUN5dQ"}`

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
containerimage.digest: sha256:61004a4d6d8d2efa67f77d85e0b1cc90c494935103a4cf17a24f0bfda5e5f079
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NjEwMDRhNGQ2ZDhkMmVmYTY3Zjc3ZDg1ZTBiMWNjOTBjNDk0OTM1MTAzYTRjZjE3YTI0ZjBiZmRhNWU1ZjA3OSIsInNpemUiOjM1MzMsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xNVQxOToxMTozNVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:d46b6f343d45c4e6249f1c5dbd7e7acea6827186d9dee80035b9af8e1c27cfdd
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
Mounting volume on: /var/lib/containers/railwayapp/bind-mounts/2e4913a2-2cf9-485a-90ac-142881cdffc8/vol_onr647rhdeir9di9
Starting Container
[start] launching whatsapp_bridge
[wa-bridge] listening on :3001
[wa-bridge] qr_received : len=239
INFO:     Waiting for application startup.
[lp] 17320 Google Ads landing-page routes registered (base=9384, qualifier=7752, near-me=184, 184 service aliases × 51 areas)
[lp-ar] 133 Arabic landing-page routes registered
INFO:     Started server process [1]
[scheduler] started — autoblog 06:00 + 18:00, PSI 03:00, summary 21:00 (Asia/Dubai)
[purge] scan complete — 34 posts, 0 flagged
[seed-users] test accounts ready: test@servia.ae/test123, demo@servia.ae/demo123, vendor@servia.ae/vendor123
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     100.64.0.2:34031 - "GET /api/health HTTP/1.1" 200 OK
[wa-bridge] qr_received : len=239
[autoblog] catch-up SKIP (last_run @ 2026-05-15T14:00:00.000743Z is fresh AND ok)
[wa-bridge] qr_received : len=239
```
