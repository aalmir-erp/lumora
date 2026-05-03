# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"ok":true,"service":"Lumora","version":"0.16.0","mode":"llm","model":"claude-opus-4-7","wa_bridge":false,"admin_token_hint":null}`

## Build logs
```
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
[6/7] COPY web ./web
[7/7] RUN mkdir -p /data
[7/7] RUN mkdir -p /data
exporting to docker image format
exporting to docker image format
containerimage.config.digest: sha256:aabac0485d54e0d0984c5797bb358e8170c2b4f689f2d72de1d12e124207afdf
containerimage.digest: sha256:d8974d79b246ef559c1532784fdf4457715f06d59f9aad7067b9afdb8b7d3667
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6ZDg5NzRkNzliMjQ2ZWY1NTljMTUzMjc4NGZkZjQ0NTc3MTVmMDZkNTlmOWFhZDcwNjdiOWFmZGI4YjdkMzY2NyIsInNpemUiOjIxOTEsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wM1QxOTo1Njo1OVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
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
               ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/anyio/_backends/_asyncio.py", line 1002, in run
  File "/usr/local/lib/python3.12/site-packages/fastapi/routing.py", line 674, in app
    result = context.run(func, *args)
    raw_response = await run_endpoint_function(
             ^^^^^^^^^^^^^^^^^^^^^^^^
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/admin.py", line 626, in list_customers
  File "/usr/local/lib/python3.12/site-packages/fastapi/routing.py", line 330, in run_endpoint_function
    return await run_in_threadpool(dependant.call, **values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/starlette/concurrency.py", line 32, in run_in_threadpool
    return await anyio.to_thread.run_sync(func)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/anyio/to_thread.py", line 63, in run_sync
    return await get_async_backend().run_sync_in_worker_thread(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/anyio/_backends/_asyncio.py", line 2518, in run_sync_in_worker_thread
    return await future
    rows = c.execute(
           ^^^^^^^^^^
sqlite3.OperationalError: no such column: customer_phone
INFO:     100.64.0.4:39892 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:57070 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.3:57070 - "GET /api/admin/bookings HTTP/1.1" 200 OK
INFO:     100.64.0.5:58966 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.6:57352 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.7:16444 - "GET /api/admin/services-summary HTTP/1.1" 200 OK
INFO:     100.64.0.4:39892 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
INFO:     100.64.0.8:29140 - "GET /api/admin/conversations?limit=20 HTTP/1.1" 200 OK
```
