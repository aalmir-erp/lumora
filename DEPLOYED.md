# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"c-1Q5WlYR922bVIPU79b0g"}`

## Build logs
```
uploading snapshot
[2/6] WORKDIR /app
[internal] load build context
[2/6] WORKDIR /app
[internal] load build context
[ 3/14] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 4/14] COPY requirements.txt ./
[ 5/14] RUN pip install -r requirements.txt
[ 6/14] COPY whatsapp_bridge ./whatsapp_bridge
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
containerimage.digest: sha256:4cd4150a977b5895cdaa180f08b177b78f8565ce019027e0b149b3195cbcba2c
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NGNkNDE1MGE5NzdiNTg5NWNkYWExODBmMDhiMTc3Yjc4Zjg1NjVjZTAxOTAyN2UwYjE0OWIzMTk1Y2JjYmEyYyIsInNpemUiOjM1MzMsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xNVQxNzowNDoxM1oifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:b996c120c3b690ce8e9c71739262cde52d9106a6c37c8689b0ea1d567bf14e4f
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
INFO:     100.64.0.5:44072 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.7:42424 - "GET /api/admin/bookings?status=pending&limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.7:42424 - "GET /api/admin/bookings?limit=300 HTTP/1.1" 200 OK
INFO:     100.64.0.5:44072 - "GET /api/admin/analytics HTTP/1.1" 200 OK
INFO:     100.64.0.5:14640 - "GET /api/admin/llm/diagnose HTTP/1.1" 200 OK
INFO:     100.64.0.5:44072 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.7:42424 - "GET /api/wa/status HTTP/1.1" 200 OK
INFO:     100.64.0.7:42438 - "POST /api/admin/push/subscribe HTTP/1.1" 200 OK
INFO:     100.64.0.5:44072 - "GET /api/admin/stats HTTP/1.1" 200 OK
INFO:     100.64.0.5:14640 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.5:44094 - "GET /api/videos/list?limit=500 HTTP/1.1" 200 OK
INFO:     100.64.0.5:44072 - "GET /api/blog/latest?limit=200 HTTP/1.1" 200 OK
INFO:     100.64.0.7:42438 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.5:44072 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.7:42438 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.5:44072 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.7:42438 - "GET /api/admin/auto-tests/runs?limit=30 HTTP/1.1" 200 OK
INFO:     100.64.0.7:49798 - "GET /api/admin/auto-tests/summary HTTP/1.1" 200 OK
INFO:     100.64.0.7:49812 - "GET /api/admin/auto-tests/findings?severity=error&resolved=0&limit=200 HTTP/1.1" 200 OK
INFO:     100.64.0.5:44072 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.7:49812 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.5:44072 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
[wa-bridge] send_retry_lid : No LID for user
s (https://static.whatsapp.net/rsrc.php/v4/yI/r/A3PSxQB1RSd.js:7
[push] converted PEM → raw b64url scalar (43 chars) for pywebpush
[push] sending '👋 New visitor on Servia' to 2 sub(s) (audience=all)
INFO:     100.64.0.5:24452 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.5:24452 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.5:24452 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.5:24452 - "GET /api/admin/auto-tests/findings?resolved=0&limit=200 HTTP/1.1" 200 OK
```
