# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** FAILED
**Health:** `curl: (28) Operation timed out after 8002 milliseconds with 0 bytes received`

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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6MDU0OTI4NzUxMmRmZjcxOWU4MWY2YjQ0MDliZGFhOTk0OTliYjI2NWNhYzllM2NlZTBmN2VjNDYyNTM0NGM4YiIsInNpemUiOjI5NTcsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wNFQwNDowOToxMFoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:61a197994953875dd6f2e4e41b9a5bd6ccafafaa48e2ecec1d067af1456e42e5
containerimage.digest: sha256:0549287512dff719e81f6b4409bdaa99499bb265cac9e3cee0f7ec4625344c8b
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
  File "/usr/local/lib/python3.12/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "uvloop/loop.pyx", line 1518, in uvloop.loop.Loop.run_until_complete
  File "/usr/local/lib/python3.12/site-packages/uvicorn/server.py", line 79, in serve
    await self._serve(sockets)
  File "/usr/local/lib/python3.12/site-packages/uvicorn/server.py", line 86, in _serve
    config.load()
  File "/usr/local/lib/python3.12/site-packages/uvicorn/config.py", line 449, in load
    self.loaded_app = import_from_string(self.app)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/uvicorn/importer.py", line 19, in import_from_string
    module = importlib.import_module(module_str)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/importlib/__init__.py", line 90, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen importlib._bootstrap>", line 1387, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1360, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1331, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 935, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 999, in exec_module
  File "<frozen importlib._bootstrap>", line 488, in _call_with_frames_removed
  File "/app/app/main.py", line 17, in <module>
    from . import admin, ai_router, cart, db, demo_brain, kb, launch, llm, portal, portal_v2, quotes, social_publisher, staff_portraits, tools, videos, whatsapp
  File "/app/app/portal_v2.py", line 75, in <module>
    @public_router.post("/auth/magic-link")
     ^^^^^
^^^^^^^^
NameError: name 'public_router' is not defined
```
