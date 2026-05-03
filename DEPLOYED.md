# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"ok":true,"service":"Lumora","version":"0.14.0","mode":"llm","model":"claude-opus-4-7","wa_bridge":false,"admin_token_hint":null}`

## Build logs
```
[internal] load metadata for docker.io/library/python:3.12-slim
[internal] load .dockerignore
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
[internal] load build context
[1/7] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[1/7] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[1/7] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[internal] load build context
[internal] load build context
[2/7] WORKDIR /app
[3/7] COPY requirements.txt ./
[4/7] RUN pip install -r requirements.txt
[5/7] COPY app ./app
[6/7] COPY web ./web
[7/7] RUN mkdir -p /data
exporting to docker image format
exporting to docker image format
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6YzU5ZTA2YmE5ZmFiNjcxN2MxNzRmMDZjMjA0MWRiODJjNTMwNTI1MmEyMzYxMDNjM2ZlM2MzZjk2ZWMwNWE5MSIsInNpemUiOjIxOTEsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wM1QxOTozMzowMFoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:992742223b307b1bc9e1a6214525d2d4a1d57d2164e415dea26539b397220bcb
containerimage.digest: sha256:c59e06ba9fab6717c174f06c2041db82c5305252a236103c3fe3c3f96ec05a91
image push

[35m====================
Starting Healthcheck
====================
[0m
[37mPath: /api/health[0m
[37mRetry window: 1m0s[0m
```

## Runtime logs
```
INFO:     Started server process [2]
INFO:     Waiting for application startup.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```
