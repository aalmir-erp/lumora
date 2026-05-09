# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** FAILED
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"17IevdvFSSqWx0lFU79b0g"}`

## Build logs
```
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:ec948fa5f90f4f8907e89f4800cfd2d2e91e391a4bce4a6afa77ba265bc3a2fe
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
containerimage.config.digest: sha256:d53e4f9b2aba972573b09bdad2261ae2ad89211fc6c2a8fc159b70186adad589
containerimage.digest: sha256:785d1c8a10e9495a97c5f3f93ed31816921ca97f28fa89bc46bc3ef7cde6edff
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6Nzg1ZDFjOGExMGU5NDk1YTk3YzVmM2Y5M2VkMzE4MTY5MjFjYTk3ZjI4ZmE4OWJjNDZiYzNlZjdjZGU2ZWRmZiIsInNpemUiOjI5NTksImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wOVQxNjo0MToxMloifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
image push
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
    run(
  File "/usr/local/lib/python3.12/site-packages/uvicorn/main.py", line 617, in run
    server.run()
  File "/usr/local/lib/python3.12/site-packages/uvicorn/server.py", line 75, in run
    return asyncio_run(self.serve(sockets=sockets), loop_factory=self.config.get_loop_factory())
  File "/usr/local/lib/python3.12/importlib/__init__.py", line 90, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
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
    app.include_router(_mqp_router_mod.admin_router)    # /api/admin/quote/{id}/status, line-status, upload, all
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
^^^^^^^^^^^
  File "<frozen importlib._bootstrap>", line 1387, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1360, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1331, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 935, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 999, in exec_module
  File "<frozen importlib._bootstrap>", line 488, in _call_with_frames_removed
  File "/app/app/main.py", line 228, in <module>
AttributeError: module 'app.multi_quote_pages' has no attribute 'admin_router'
Mounting volume on: /var/lib/containers/railwayapp/bind-mounts/df5e9daf-bf2a-484b-9e4f-3a3cd82a5c38/vol_onr647rhdeir9di9
```
