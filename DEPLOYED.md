# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"ok":true,"service":"Lumora","version":"1.9.0","mode":"llm","model":"claude-opus-4-7","wa_bridge":false,"admin_token_hint":null}`

## Build logs
```
[internal] load .dockerignore
[internal] load .dockerignore
[7/7] RUN mkdir -p /data
[6/7] COPY web ./web
[5/7] COPY app ./app
[4/7] RUN pip install -r requirements.txt
[3/7] COPY requirements.txt ./
[internal] load build context
[2/6] WORKDIR /app
[1/6] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[1/6] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[1/6] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[internal] load build context
[internal] load build context
[internal] load build context
[2/6] WORKDIR /app
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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NzE5NGJjNzAzOGVlYzRhMzUyZjA1MWVmMWVhYzM0YjcwMTg0NGVkZGQwYmEzNjE3MTBmODJiMTk4NTgxMTIzMCIsInNpemUiOjIxOTEsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wM1QyMjoxNzoxNVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:1506ec3463afe3baf7b59dec1568e059b7bdffb569f29bb754ad201b064b3d32
containerimage.digest: sha256:7194bc7038eec4a352f051ef1eac34b701844eddd0ba361710f82b1985811230
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
Mounting volume on: /var/lib/containers/railwayapp/bind-mounts/133cb370-c413-431c-95d3-26103c7c5381/vol_onr647rhdeir9di9
Starting Container
[scheduler] not loaded: BaseScheduler.add_job() got multiple values for argument 'replace_existing'
INFO:     Started server process [2]
INFO:     Waiting for application startup.
[autoblog-seed] launching background thread to generate 10 articles
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     100.64.0.2:54353 - "GET /api/health HTTP/1.1" 200 OK
```
