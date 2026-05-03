# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"ok":true,"service":"Lumora","version":"1.6.0","mode":"llm","model":"claude-opus-4-7","wa_bridge":false,"admin_token_hint":null}`

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
[builder 1/5] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[builder 1/5] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[builder 1/5] FROM docker.io/library/python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3
[internal] load build context
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
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6N2RkYzY5M2FkMTgxM2Y5MWNlZTQwNGM0NzA4NzNiOGNjMzBmZGYyM2I1YzA2OTFjY2YzZTdiM2ViOTFjYmE4YSIsInNpemUiOjIxOTEsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wM1QyMTozNjowNFoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:98c73bb2d3e4460d8629048925a7a65f36dec5be59ff6c06cab0cc73637e96d9
containerimage.digest: sha256:7ddc693ad1813f91cee404c470873b8cc30fdf23b5c0691ccf3e7b3eb91cba8a
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
Mounting volume on: /var/lib/containers/railwayapp/bind-mounts/6a94463e-07f4-4bcf-91ed-a88ce1b9f6c1/vol_onr647rhdeir9di9
Starting Container
INFO:     Started server process [2]
INFO:     Application startup complete.
INFO:     100.64.0.2:37257 - "GET /api/health HTTP/1.1" 200 OK
INFO:     100.64.0.3:48312 - "GET /widget.css HTTP/1.1" 200 OK
INFO:     100.64.0.3:48312 - "GET /theme.js HTTP/1.1" 200 OK
INFO:     100.64.0.6:40632 - "GET /app.js HTTP/1.1" 200 OK
INFO:     100.64.0.9:39438 - "GET /api/admin/cms HTTP/1.1" 401 Unauthorized
INFO:     100.64.0.10:30902 - "GET /api/brand HTTP/1.1" 200 OK
INFO:     100.64.0.11:62052 - "GET /sw.js HTTP/1.1" 200 OK
INFO:     100.64.0.7:43648 - "GET /sw.js HTTP/1.1" 200 OK
INFO:     100.64.0.4:52750 - "GET /widget.js HTTP/1.1" 200 OK
INFO:     100.64.0.13:35804 - "GET /manifest.webmanifest HTTP/1.1" 200 OK
```
