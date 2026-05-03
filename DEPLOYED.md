# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"ok":true,"service":"Lumora","version":"0.10.0","mode":"llm","model":"claude-opus-4-7","wa_bridge":false,"admin_token_hint":null}`

## Build logs
```
[7/7] RUN mkdir -p /data
[6/7] COPY web ./web
[5/7] COPY app ./app
[4/7] RUN pip install -r requirements.txt
[3/7] COPY requirements.txt ./
[internal] load build context
[2/7] WORKDIR /app
[1/7] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[internal] load build context
[1/7] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[1/7] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[1/7] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[1/7] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[internal] load build context
[internal] load build context
[2/7] WORKDIR /app
[3/7] COPY requirements.txt ./
[4/7] RUN pip install -r requirements.txt
[4/7] RUN pip install -r requirements.txt
[5/7] COPY app ./app
[5/7] COPY app ./app
[6/7] COPY web ./web
[6/7] COPY web ./web
[7/7] RUN mkdir -p /data
[7/7] RUN mkdir -p /data
exporting to docker image format
exporting to docker image format
containerimage.digest: sha256:72dd674e75ec10c475c5dedc6b0f44662d17975537aa6fcefbb3c672809b0dc9
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NzJkZDY3NGU3NWVjMTBjNDc1YzVkZWRjNmIwZjQ0NjYyZDE3OTc1NTM3YWE2ZmNlZmJiM2M2NzI4MDliMGRjOSIsInNpemUiOjIxOTAsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wM1QxNjoxMjo1NloifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:9047b7d182445d6d9ffca6b178653f3bcdacee847a37d045f56108aeacf3043b
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
Mounting volume on: /var/lib/containers/railwayapp/bind-mounts/172f9c44-0d3d-43f7-a982-b78026191f7d/vol_onr647rhdeir9di9
Starting Container
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     100.64.0.2:58067 - "GET /api/health HTTP/1.1" 200 OK
INFO:     Started server process [2]
INFO:     Waiting for application startup.
```
