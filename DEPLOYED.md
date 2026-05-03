# Lumora deploy

**URL:** https://lumora-production-4071.up.railway.app
**Status:** SUCCESS
**Health:** `{"ok":true,"service":"Lumora","version":"1.3.0","mode":"llm","model":"claude-opus-4-7","wa_bridge":false,"admin_token_hint":null}`

## Build logs
```

Downloading sniffio-1.3.1-py3-none-any.whl (10 kB)

Downloading charset_normalizer-3.4.7-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (216 kB)

Downloading urllib3-2.6.3-py3-none-any.whl (131 kB)

Installing collected packages: websockets, uvloop, urllib3, typing-extensions, sniffio, pyyaml, python-multipart, python-dotenv, jiter, idna, httptools, h11, docstring-parser, distro, click, charset_normalizer, certifi, annotated-types, annotated-doc, uvicorn, typing-inspection, requests, pydantic-core, httpcore, anyio, watchfiles, stripe, starlette, pydantic, httpx, fastapi, anthropic

Successfully installed annotated-doc-0.0.4 annotated-types-0.7.0 anthropic-0.97.0 anyio-4.13.0 certifi-2026.4.22 charset_normalizer-3.4.7 click-8.3.3 distro-1.9.0 docstring-parser-0.18.0 fastapi-0.136.1 h11-0.16.0 httpcore-1.0.9 httptools-0.7.1 httpx-0.28.1 idna-3.13 jiter-0.14.0 pydantic-2.13.3 pydantic-core-2.46.3 python-dotenv-1.2.2 python-multipart-0.0.27 pyyaml-6.0.3 requests-2.33.1 sniffio-1.3.1 starlette-1.0.0 stripe-15.1.0 typing-extensions-4.15.0 typing-inspection-0.4.2 urllib3-2.6.3 uvicorn-0.46.0 uvloop-0.22.1 watchfiles-1.1.1 websockets-16.0

WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system package manager, possibly rendering your system unusable. It is recommended to use a virtual environment instead: https://pip.pypa.io/warnings/venv. Use the --root-user-action option if you know what you are doing and want to suppress this warning.


[notice] A new release of pip is available: 25.0.1 -> 26.1
[notice] To update, run: pip install --upgrade pip

[4/7] RUN pip install -r requirements.txt
[5/7] COPY app ./app
[5/7] COPY app ./app
[6/7] COPY web ./web
[6/7] COPY web ./web
[7/7] RUN mkdir -p /data
[7/7] RUN mkdir -p /data
exporting to docker image format
exporting to docker image format
containerimage.digest: sha256:592b8516fc12f54b2c6a86c6936fc133278e22ef6b34e13c0d8df148a30ea4a4
containerimage.descriptor: eyJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQub2NpLmltYWdlLm1hbmlmZXN0LnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6NTkyYjg1MTZmYzEyZjU0YjJjNmE4NmM2OTM2ZmMxMzMyNzhlMjJlZjZiMzRlMTNjMGQ4ZGYxNDhhMzBlYTRhNCIsInNpemUiOjIxOTEsImFubm90YXRpb25zIjp7Im9yZy5vcGVuY29udGFpbmVycy5pbWFnZS5jcmVhdGVkIjoiMjAyNi0wNS0wM1QyMTowMTowOVoifSwicGxhdGZvcm0iOnsiYXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJvcyI6ImxpbnV4In19
containerimage.config.digest: sha256:64bc53d343d0af4e1de903867b89c17797373d4530872ba6da3044d45161476e
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
Mounting volume on: /var/lib/containers/railwayapp/bind-mounts/3e452542-13ea-44fc-b545-a03d012b0163/vol_onr647rhdeir9di9
Starting Container
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     100.64.0.2:51391 - "GET /api/health HTTP/1.1" 200 OK
```
