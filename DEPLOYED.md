# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** FAILED
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"puYCYNmLQymldofec9o55Q"}`

## Build logs
```
[internal] load build context
[ 2/12] WORKDIR /app
[ 3/12] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 4/12] COPY requirements.txt ./
[ 5/12] RUN pip install -r requirements.txt
[ 6/12] COPY whatsapp_bridge ./whatsapp_bridge
[ 7/12] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
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
containerimage.config.digest: sha256:be9244b72d6b25b6fe44603b4c5b5a3d69bdd0025024fcf945c620c7b91f1f7f
containerimage.digest: sha256:10f040457832ac46283f241c1daa70bae443cf0975706105aa8a42b584969fc9
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6MTBmMDQwNDU3ODMyYWM0NjI4M2YyNDFjMWRhYTcwYmFlNDQzY2YwOTc1NzA2MTA1YWE4YTQyYjU4NDk2OWZjOSIsInNpemUiOjMxNTIsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0xM1QxNDo1ODoyNFoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
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
    return _bootstrap._gcd_import(name[level:], package, level)
  File "/usr/local/lib/python3.12/site-packages/uvicorn/server.py", line 86, in _serve
    config.load()
  File "uvloop/loop.pyx", line 1518, in uvloop.loop.Loop.run_until_complete
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/uvicorn/config.py", line 449, in load
  File "/usr/local/lib/python3.12/site-packages/uvicorn/server.py", line 79, in serve
    self.loaded_app = import_from_string(self.app)
    await self._serve(sockets)
  File "/usr/local/lib/python3.12/importlib/__init__.py", line 90, in import_module
                      ^^^^^^^^^^^^^^^^^^^
^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/uvicorn/importer.py", line 19, in import_from_string
    module = importlib.import_module(module_str)
  File "/app/app/main.py", line 18, in <module>
    from . import admin, admin_live as _admin_live, ai_router, airbnb_ical as _airbnb_ical, brand_contact as _brand_contact, cart, checkout_central as _checkout, commerce as _commerce, db, demo_brain, google_home as _gha, inbox as _inbox, kb, launch, live_visitors, llm, me_location as _me_loc, nfc as _nfc_mod, portal, portal_v2, psi as _psi_mod, push_notifications, quotes, recovery as _recovery_mod, recovery_auction as _rec_auc, rlaif as _rlaif, selftest, social_publisher, sos_custom as _sos_custom_mod, staff_portraits, tools, videos, visibility, wear_diag as _wear_diag, whatsapp
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
^^^^^^^^^^^
  File "<frozen importlib._bootstrap>", line 1387, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1360, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1331, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 935, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 999, in exec_module
  File "<frozen importlib._bootstrap>", line 488, in _call_with_frames_removed
  File "/app/app/admin.py", line 12, in <module>
    from . import auth_users, db, kb, quotes, tools
  File "/app/app/kb.py", line 6, in <module>
    from .config import get_settings
ImportError: cannot import name 'get_settings' from 'app.config' (/app/app/config.py)
Mounting volume on: /var/lib/containers/railwayapp/bind-mounts/129bf508-b3de-4d25-bce0-138d99a908b1/vol_onr647rhdeir9di9
```
