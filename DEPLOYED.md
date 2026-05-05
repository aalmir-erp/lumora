# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"10sxEzfHTVyi1d7waP71AA"}`

## Build logs
```
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 2/11] WORKDIR /app
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[10/11] COPY start.sh /app/start.sh
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[internal] load build context
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6YWM3NGFmOGYwOWU0YjM4ODIyODM5ZmZmODFkMjYxNzEyNzk4OThiZDUwNWE2NGI0YjM0ZmZhZjEzNTFkMjY4YSIsInNpemUiOjI5NTcsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNVQwODo0Mzo0MloifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:416ee1d042faff9c797004d30101666fee3e9a48355a48579658512b3e6ab9e8
containerimage.digest: sha256:ac74af8f09e4b38822839fff81d26171279898bd505a64b4b34ffaf1351d268a
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
INFO:     100.64.0.5:44252 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
INFO:     100.64.0.4:18242 - "GET /share.js HTTP/1.1" 200 OK
INFO:     100.64.0.4:18216 - "GET /lazy-loaders.js HTTP/1.1" 200 OK
INFO:     100.64.0.4:18296 - "GET /widget.js HTTP/1.1" 200 OK
INFO:     100.64.0.4:18316 - "GET /cms.js HTTP/1.1" 200 OK
INFO:     100.64.0.4:18314 - "GET /api/blog/latest?limit=10 HTTP/1.1" 200 OK
INFO:     100.64.0.4:18326 - "GET /avatar.svg HTTP/1.1" 200 OK
INFO:     100.64.0.4:18194 - "GET /cart-badge.js HTTP/1.1" 200 OK
INFO:     100.64.0.4:18170 - "GET /social-strip.js HTTP/1.1" 200 OK
INFO:     100.64.0.4:18276 - "GET /_snippets.js HTTP/1.1" 200 OK
INFO:     100.64.0.4:18288 - "GET /social-proof.js HTTP/1.1" 200 OK
INFO:     100.64.0.4:18340 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.4:18242 - "GET /api/i18n HTTP/1.1" 200 OK
INFO:     100.64.0.4:18288 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.4:18276 - "GET /icon-192.svg HTTP/1.1" 200 OK
INFO:     100.64.0.4:18276 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.4:18194 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.4:18288 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.4:18170 - "POST /api/app-install HTTP/1.1" 200 OK
INFO:     100.64.0.4:18194 - "GET /api/reviews/platforms HTTP/1.1" 200 OK
INFO:     100.64.0.3:17248 - "GET /api/activity/live HTTP/1.1" 200 OK
INFO:     100.64.0.4:51778 - "GET /api/blog/hero/dubai-al-barsha-same-day-handyman-in-al-barsha--how-servia-delivers-in-hours.svg HTTP/1.1" 200 OK
INFO:     100.64.0.4:51788 - "GET /api/blog/hero/sharjah-carpet-cleaning-in-al-khan-sharjah---sand--oil--kid-spills-and-what-aed-80-covers.svg HTTP/1.1" 200 OK
INFO:     100.64.0.4:51778 - "GET /api/activity/live HTTP/1.1" 200 OK
INFO:     100.64.0.4:51788 - "GET /api/blog/hero/dubai-kitchen-deep-clean-in-jlt---the-ramadan-grease-problem-and-how-pros-solve-it.svg HTTP/1.1" 200 OK
INFO:     100.64.0.4:51792 - "GET /api/blog/hero/umm-al-quwain-handyman-in-uaq---the-6-small-fixes-every-villa-owner-should-batch-in-one-vi.svg HTTP/1.1" 200 OK
INFO:     100.64.0.4:51812 - "GET /api/blog/hero/dubai-sofa-shampoo-in-arabian-ranches---why-fabric-protectors-are-a-2026-must-have.svg HTTP/1.1" 200 OK
INFO:     100.64.0.4:51788 - "GET /api/blog/hero/abu-dhabi-bed-bugs-on-reem-island---why-80--of-treatments-fail-and-what-works-in-2026.svg HTTP/1.1" 200 OK
INFO:     100.64.0.4:51792 - "GET /api/blog/hero/ras-al-khaimah-rak-ac-service-tips---coastal-humidity-is-killing-your-compressor-faster-th.svg HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
```
