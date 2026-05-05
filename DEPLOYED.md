# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"FrqCPzXBReSR_G7LaP71AA"}`

## Build logs
```
[ 7/11] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6M2UzODhlYmU1ODQ3YTU2NGZkOTM0YjY0ZWUyODViMDVlY2RkMTEyNzE4ZjZlMDc2ZjVmZDcwODJhZWM4ZjRmZCIsInNpemUiOjI5NTcsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNVQxMzowNzoxOVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:03882d23235a4511f98f792f766e51f602d925085e18c557e0c2fb1c2f598c9e
containerimage.digest: sha256:3e388ebe5847a564fd934b64ee285b05ecdd112718f6e076f5fd7082aec8f4fd
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
Mounting volume on: /var/lib/containers/railwayapp/bind-mounts/5a4e6f70-1d9e-46a5-8d64-6ef09175adbb/vol_onr647rhdeir9di9
Starting Container
[start] launching whatsapp_bridge
[wa-bridge] listening on :3001
[scheduler] not loaded: BaseScheduler.add_job() got multiple values for argument 'replace_existing'
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     100.64.0.2:54639 - "GET /api/health HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
INFO:     100.64.0.3:54682 - "GET / HTTP/1.1" 200 OK
[push] pywebpush not installed — skipping push send
INFO:     100.64.0.4:31162 - "GET /api/services HTTP/1.1" 200 OK
INFO:     100.64.0.5:59394 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.5:33882 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.5:33882 - "GET /api/reviews/platforms HTTP/1.1" 200 OK
INFO:     100.64.0.3:36454 - "GET /icon-512.svg HTTP/1.1" 200 OK
INFO:     100.64.0.6:61936 - "GET /logo.svg HTTP/1.1" 200 OK
INFO:     100.64.0.3:36454 - "GET /icon-192.svg HTTP/1.1" 200 OK
INFO:     100.64.0.7:19588 - "GET /api/blog/hero/%24%7Besc%28featured.slug%29%7D.svg HTTP/1.1" 200 OK
INFO:     100.64.0.8:45352 - "GET /avatar.svg HTTP/1.1" 200 OK
INFO:     100.64.0.9:12084 - "GET /api/blog/hero/%24%7Besc%28p.slug%29%7D.svg HTTP/1.1" 200 OK
INFO:     100.64.0.10:23476 - "GET /mascot.svg HTTP/1.1" 200 OK
INFO:     100.64.0.11:52540 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 301 Moved Permanently
INFO:     100.64.0.12:10398 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 401 Unauthorized
[wa-bridge] QR received. Open /qr in your browser to scan.
[wa-bridge] QR received. Open /qr in your browser to scan.
```
