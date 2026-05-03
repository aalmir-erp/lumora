# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"ok":true,"service":"Lumora","version":"0.9.0","mode":"llm","model":"claude-opus-4-7","wa_bridge":false,"admin_token_hint":null}`

## Build logs
```
[internal] load .dockerignore
[internal] load .dockerignore
[internal] load .dockerignore
[7/7] RUN mkdir -p /data
[6/7] COPY web ./web
[5/7] COPY app ./app
[4/7] RUN pip install -r requirements.txt
[3/7] COPY requirements.txt ./
[internal] load build context
[2/7] WORKDIR /app
[1/7] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[1/7] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[1/7] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[internal] load build context
[internal] load build context
[internal] load build context
[2/7] WORKDIR /app
[3/7] COPY requirements.txt ./
[4/7] RUN pip install -r requirements.txt
[5/7] COPY app ./app
[5/7] COPY app ./app
[6/7] COPY web ./web
[6/7] COPY web ./web
[7/7] RUN mkdir -p /data
[7/7] RUN mkdir -p /data
exporting to docker image format
exporting to docker image format
containerimage.config.digest: sha256:8a0259f04dc9053a0a7014ae42154b5d6b343524b8b0856008508db700f930a5
containerimage.digest: sha256:a944b1523f0c14f81f57e58470f74c06ad2222b105d4ee59f7b9f0aff3b16e41
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6YTk0NGIxNTIzZjBjMTRmODFmNTdlNTg0NzBmNzRjMDZhZDIyMjJiMTA1ZDRlZTU5ZjdiOWYwYWZmM2IxNmU0MSIsInNpemUiOjIxOTAsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wM1QxMzowNTowMVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
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
Mounting volume on: /var/lib/containers/railwayapp/bind-mounts/918e5e36-f7a6-4829-ab68-6e25ef474667/vol_onr647rhdeir9di9
Starting Container
INFO:     Started server process [2]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     100.64.0.2:57435 - "GET /api/health HTTP/1.1" 200 OK
```
