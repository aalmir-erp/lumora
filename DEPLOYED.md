# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** FAILED
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"ct4180EXRvSU2APqaP71AA"}`

## Build logs
```
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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6MDRmMTU4ZDdmMTBkNjZmZDNiMTJkNmI5NjQzZjY5YmYxMWVkNmNlYzg5YTA1ZGY0NGNkMjg5NWQzN2JiYTQxZSIsInNpemUiOjI5NTgsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNlQwMDowNzowMVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:1c6d0660b3f74284f7c5863a79c424e772adeb0b6f32baa14ae8254164ba86c9
containerimage.digest: sha256:04f158d7f10d66fd3b12d6b9643f69bf11ed6cec89a05df44cd2895d37bba41e
image push
image push

[35m====================
Starting Healthcheck
====================
[0m
[37mPath: /api/health[0m
[37mRetry window: 1m0s[0m

[93mAttempt #1 failed with service unavailable. Continuing to retry for 49s[0m
[93mAttempt #2 failed with service unavailable. Continuing to retry for 38s[0m
[93mAttempt #3 failed with service unavailable. Continuing to retry for 26s[0m
[93mAttempt #4 failed with service unavailable. Continuing to retry for 12s[0m

[91m1/1 replicas never became healthy![0m
[91mHealthcheck failed![0m
```

## Runtime logs
```
[scheduler] not loaded: BaseScheduler.add_job() got multiple values for argument 'replace_existing'
INFO:     Started server process [1]
INFO:     Waiting for application startup.
[seed-demo] starting seed (force=False)…
[seed-demo] customer +971501110001 skipped: no such table: customer_wallet
Mounting volume on: /var/lib/containers/railwayapp/bind-mounts/45bf45b8-16c8-4f9b-bb3d-fd4838bf0f25/vol_onr647rhdeir9di9
Starting Container
[seed-demo] customer +971501110011 skipped: no such table: customer_wallet
[seed-demo] customer +971501110005 skipped: no such table: customer_wallet
[seed-demo] customer +971501110002 skipped: no such table: customer_wallet
[seed-demo] customer +971501110006 skipped: no such table: customer_wallet
[seed-demo] customer +971501110003 skipped: no such table: customer_wallet
[seed-demo] customer +971501110007 skipped: no such table: customer_wallet
[seed-demo] customer +971501110008 skipped: no such table: customer_wallet
[wa-bridge] QR received. Open /qr in your browser to scan.
[seed-demo] customer +971501110009 skipped: no such table: customer_wallet
[seed-demo] customer +971501110010 skipped: no such table: customer_wallet
[seed-demo] customer +971501110012 skipped: no such table: customer_wallet
[seed-demo] customer +971501110014 skipped: no such table: customer_wallet
[seed-demo] customer +971501110015 skipped: no such table: customer_wallet
[seed-demo] customer +971501110016 skipped: no such table: customer_wallet
[seed-demo] customer +971501110017 skipped: no such table: customer_wallet
[seed-demo] customer +971501110018 skipped: no such table: customer_wallet
[seed-demo] customer +971501110019 skipped: no such table: customer_wallet
[seed-demo] customer +971501110020 skipped: no such table: customer_wallet
[wa-bridge] QR received. Open /qr in your browser to scan.
[wa-bridge] QR received. Open /qr in your browser to scan.
[wa-bridge] QR received. Open /qr in your browser to scan.
[wa-bridge] QR received. Open /qr in your browser to scan.
[wa-bridge] QR received. Open /qr in your browser to scan.
```
