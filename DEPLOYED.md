# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"jvGAFBsIQkWbJHWABT7zVQ"}`

## Build logs
```
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 2/11] WORKDIR /app
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[internal] load build context
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[internal] load build context
[internal] load build context
[ 2/11] WORKDIR /app
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 4/11] COPY requirements.txt ./
[ 5/11] RUN pip install -r requirements.txt
[ 6/11] COPY whatsapp_bridge ./whatsapp_bridge
[ 7/11] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6OTlmOWZiMzY1ZTAzYWUzNTBmNzFmOTc5MWE3ZWI4MTgyZDQxZGZhMmU3NDc5ZWVhZWZiMGRlYzNlNjg0ODkwOCIsInNpemUiOjI5NTcsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNFQyMDo1MjozNloifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:da0e00afc3d86a6be287aea0f6cdb5c2ea271419fa8d79d23df72119c96ef434
containerimage.digest: sha256:99f9fb365e03ae350f71f9791a7eb8182d41dfa2e7479eeaefb0dec3e6848908
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
INFO:     100.64.0.4:61576 - "GET /api/blog/hero/dubai-sofa-shampoo-in-arabian-ranches---why-fabric-protectors-are-a-2026-must-have.svg HTTP/1.1" 200 OK
INFO:     100.64.0.4:61594 - "GET /api/blog/hero/abu-dhabi-bed-bugs-on-reem-island---why-80--of-treatments-fail-and-what-works-in-2026.svg HTTP/1.1" 200 OK
INFO:     100.64.0.4:61554 - "GET /api/blog/hero/ras-al-khaimah-rak-ac-service-tips---coastal-humidity-is-killing-your-compressor-faster-th.svg HTTP/1.1" 200 OK
INFO:     100.64.0.5:61718 - "GET /api/blog/hero/umm-al-quwain-handyman-in-uaq---the-6-small-fixes-every-villa-owner-should-batch-in-one-vi.svg HTTP/1.1" 200 OK
INFO:     100.64.0.4:61602 - "GET /api/blog/hero/abu-dhabi-deep-cleaning-a-khalifa-city-villa-after-sandstorm-season---a-checklist.svg HTTP/1.1" 200 OK
INFO:     100.64.0.4:61576 - "GET /api/blog/latest?limit=10 HTTP/1.1" 200 OK
INFO:     100.64.0.5:61718 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.4:61576 - "GET /api/blog/hero/abu-dhabi-bed-bugs-on-reem-island---why-80--of-treatments-fail-and-what-works-in-2026.svg HTTP/1.1" 200 OK
INFO:     100.64.0.4:61602 - "GET /api/blog/hero/abu-dhabi-deep-cleaning-a-khalifa-city-villa-after-sandstorm-season---a-checklist.svg HTTP/1.1" 200 OK
INFO:     100.64.0.4:61554 - "GET /api/blog/hero/dubai-sofa-shampoo-in-arabian-ranches---why-fabric-protectors-are-a-2026-must-have.svg HTTP/1.1" 200 OK
INFO:     100.64.0.6:38514 - "GET /api/blog/hero/sharjah-carpet-cleaning-in-al-khan-sharjah---sand--oil--kid-spills-and-what-aed-80-covers.svg HTTP/1.1" 200 OK
INFO:     100.64.0.6:38522 - "GET /api/blog/hero/ras-al-khaimah-rak-ac-service-tips---coastal-humidity-is-killing-your-compressor-faster-th.svg HTTP/1.1" 200 OK
INFO:     100.64.0.6:27228 - "GET /api/blog/hero/dubai-kitchen-deep-clean-in-jlt---the-ramadan-grease-problem-and-how-pros-solve-it.svg HTTP/1.1" 200 OK
INFO:     100.64.0.6:38514 - "GET /api/blog/hero/umm-al-quwain-handyman-in-uaq---the-6-small-fixes-every-villa-owner-should-batch-in-one-vi.svg HTTP/1.1" 200 OK
INFO:     100.64.0.4:61554 - "GET /social-strip.js HTTP/1.1" 200 OK
INFO:     100.64.0.5:61718 - "GET /cart-badge.js HTTP/1.1" 200 OK
INFO:     100.64.0.6:27228 - "GET /social-proof.js HTTP/1.1" 200 OK
INFO:     100.64.0.6:38514 - "GET /_snippets.js HTTP/1.1" 200 OK
INFO:     100.64.0.6:38514 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.4:61554 - "GET /social-strip.js HTTP/1.1" 200 OK
INFO:     100.64.0.5:21924 - "GET /social-proof.js HTTP/1.1" 200 OK
INFO:     100.64.0.5:61718 - "GET /_snippets.js HTTP/1.1" 200 OK
INFO:     100.64.0.6:27228 - "GET /cart-badge.js HTTP/1.1" 200 OK
INFO:     100.64.0.6:27228 - "GET /api/site/social HTTP/1.1" 200 OK
INFO:     100.64.0.4:61554 - "GET /mascots/cleaning.svg HTTP/1.1" 200 OK
INFO:     100.64.0.4:61554 - "GET /mascots/cleaning.svg HTTP/1.1" 200 OK
INFO:     100.64.0.7:37994 - "GET /sitemap.xml HTTP/1.1" 200 OK
INFO:     100.64.0.7:37994 - "GET /sw.js HTTP/1.1" 200 OK
[wa-bridge] QR received. Open /qr in your browser to scan.
[wa-bridge] QR received. Open /qr in your browser to scan.
```
