# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** BUILDING
**Health:** `{"status":"error","code":404,"message":"Application not found","request_id":"lE1B7KUjSumZpOPNLPU1MQ"}`

## Build logs
```
scheduling build on Metal builder "builder-zoruvv"
[snapshot] received sha256:fb0a7e9d719ab346dc436023433f69112ad1f078dc92d78a535ec3f7814ce564 md5:1fa9b5a775f76f5cdc3f3f527e4d1925
receiving snapshot
found 'Dockerfile' at 'Dockerfile'
found 'railway.json' at 'railway.json'
skipping 'Dockerfile' at 'whatsapp_bridge/Dockerfile' as it is not rooted at a valid path (root_dir=, fileOpts={acceptChildOfRepoRoot:false})
analyzing snapshot
unpacking archive
[internal] load build definition from Dockerfile
[internal] load build definition from Dockerfile
[internal] load build definition from Dockerfile
uploading snapshot
[internal] load build definition from Dockerfile
[internal] load metadata for docker.io/library/python:3.12-slim
[internal] load metadata for docker.io/library/python:3.12-slim
[internal] load .dockerignore
[internal] load .dockerignore
[internal] load .dockerignore
[ 5/11] RUN pip install -r requirements.txt
[ 4/11] COPY requirements.txt ./
[ 7/11] RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund
[ 3/11] RUN apt-get update && apt-get install -y --no-install-recommends       curl ca-certificates gnupg       chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0       libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2       libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y --no-install-recommends nodejs &&     apt-get clean && rm -rf /var/lib/apt/lists/*
[ 8/11] COPY app ./app
[ 9/11] COPY web ./web
[10/11] COPY start.sh /app/start.sh
[11/11] RUN chmod +x /app/start.sh &&     mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth
[ 6/11] COPY whatsapp_bridge ./whatsapp_bridge
[internal] load build context
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[ 1/11] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[ 2/11] WORKDIR /app
[ 2/11] WORKDIR /app
[internal] load build context
[internal] load build context
```

## Runtime logs
```

```
