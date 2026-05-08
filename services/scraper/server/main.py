"""Scraper FastAPI server. Hosts:
  - /          static UI
  - /api/...   task CRUD + event stream (SSE)
  - /ws/agent  WebSocket endpoint where the local agent connects
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Header, Query
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import config
from .runtime.agent_registry import AGENT_REGISTRY
from .tasks import STORE, run_task


app = FastAPI(title="Lumora Scraper Agent")
WEB_DIR = Path(__file__).parent / "web"


class CreateTaskRequest(BaseModel):
    goal: str
    backend: str = config.DEFAULT_BACKEND
    runtime: str = config.DEFAULT_RUNTIME
    mode: str = "browser"
    agent_id: str | None = None
    max_steps: int = 25


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return {"ok": True, "agents": AGENT_REGISTRY.list_agents()}


@app.get("/api/diag")
def diag() -> dict[str, Any]:
    checks = []
    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})

    add("GOOGLE_API_KEY", bool(config.GOOGLE_API_KEY),
        "set if you'll use gemini-pro/flash/cu")
    add("ANTHROPIC_API_KEY", bool(config.ANTHROPIC_API_KEY),
        "set if you'll use claude-cu")
    add("LOCAL_AGENT_TOKEN", bool(config.LOCAL_AGENT_TOKEN),
        "required for local/desktop tasks; agents cannot connect without it")
    add("agents_connected", bool(AGENT_REGISTRY.list_agents()),
        f"connected: {AGENT_REGISTRY.list_agents()}")
    add("default_backend_buildable", True, config.DEFAULT_BACKEND)
    try:
        from .ai import build_backend
        build_backend(config.DEFAULT_BACKEND)
    except Exception as e:
        checks[-1]["ok"] = False
        checks[-1]["detail"] = f"{config.DEFAULT_BACKEND}: {e}"
    add("playwright_installed", _check_playwright(),
        "needed only for railway runtime; install via Dockerfile base image")

    summary = "ok" if all(c["ok"] for c in checks if c["name"] not in ("GOOGLE_API_KEY", "ANTHROPIC_API_KEY")) else "issues"
    return {
        "summary": summary,
        "default_backend": config.DEFAULT_BACKEND,
        "default_runtime": config.DEFAULT_RUNTIME,
        "force_local_hosts": config.FORCE_LOCAL_HOSTS,
        "checks": checks,
    }


def _check_playwright() -> bool:
    try:
        import playwright  # type: ignore  # noqa
        return True
    except Exception:
        return False


@app.get("/")
def root() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/config")
def get_config() -> dict[str, Any]:
    return {
        "default_backend": config.DEFAULT_BACKEND,
        "default_runtime": config.DEFAULT_RUNTIME,
        "backends": ["demo", "gemini-pro", "gemini-flash", "gemini-cu", "claude-cu"],
        "runtimes": ["railway", "local", "hybrid"],
        "modes": ["browser", "desktop"],
        "force_local_hosts": config.FORCE_LOCAL_HOSTS,
        "agents_connected": AGENT_REGISTRY.list_agents(),
    }


@app.post("/api/tasks")
async def create_task(req: CreateTaskRequest) -> dict[str, Any]:
    task = STORE.create(
        goal=req.goal, backend=req.backend, runtime=req.runtime,
        mode=req.mode, agent_id=req.agent_id, max_steps=req.max_steps,
    )
    asyncio.create_task(run_task(task))
    return {"id": task.id, "status": task.status}


@app.get("/api/tasks")
def list_tasks() -> dict[str, Any]:
    return {
        "tasks": [
            {"id": t.id, "goal": t.goal, "status": t.status, "backend": t.backend,
             "runtime": t.runtime, "active_runtime": t.active_runtime,
             "created_at": t.created_at, "updated_at": t.updated_at}
            for t in STORE.list()
        ]
    }


@app.get("/api/tasks/{tid}")
def get_task(tid: str) -> dict[str, Any]:
    t = STORE.get(tid)
    if not t:
        raise HTTPException(404)
    return {
        "id": t.id, "goal": t.goal, "status": t.status, "backend": t.backend,
        "runtime": t.runtime, "active_runtime": t.active_runtime,
        "mode": t.mode, "answer": t.final_answer, "error": t.error,
        "events": [{"ts": e.ts, "kind": e.kind, "data": _trim(e.data)} for e in t.events],
    }


def _trim(d: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for k, v in d.items():
        if k == "b64" and isinstance(v, str):
            out[k] = v[:64] + "...(truncated)"
        else:
            out[k] = v
    return out


@app.get("/api/tasks/{tid}/events")
async def stream_events(tid: str) -> StreamingResponse:
    t = STORE.get(tid)
    if not t:
        raise HTTPException(404)
    q = await STORE.subscribe(tid)

    async def gen():
        for e in t.events:
            yield f"data: {json.dumps({'kind': e.kind, 'data': _trim(e.data)})}\n\n"
        try:
            while True:
                ev = await asyncio.wait_for(q.get(), timeout=15)
                yield f"data: {json.dumps({'kind': ev.kind, 'data': _trim(ev.data)})}\n\n"
                if ev.kind in ("done", "error") and t.status in ("done", "failed", "cancelled"):
                    break
        except asyncio.TimeoutError:
            yield "event: ping\ndata: {}\n\n"
        finally:
            STORE.unsubscribe(tid, q)
    return StreamingResponse(gen(), media_type="text/event-stream")


@app.get("/api/tasks/{tid}/screenshot/{step}")
def get_screenshot(tid: str, step: int) -> JSONResponse:
    t = STORE.get(tid)
    if not t:
        raise HTTPException(404)
    for e in t.events:
        if e.kind == "screenshot" and e.data.get("step") == step:
            return JSONResponse({"b64": e.data.get("b64"), "url": e.data.get("url")})
    raise HTTPException(404)


@app.websocket("/ws/agent")
async def agent_ws(ws: WebSocket, token: str = Query(...), agent_id: str = Query(...)) -> None:
    if not config.LOCAL_AGENT_TOKEN or token != config.LOCAL_AGENT_TOKEN:
        await ws.close(code=4401)
        return
    await ws.accept()
    agent = await AGENT_REGISTRY.register(agent_id, ws)
    try:
        while True:
            msg = await ws.receive_text()
            try:
                payload = json.loads(msg)
            except Exception:
                continue
            await agent.push(payload)
    except WebSocketDisconnect:
        pass
    finally:
        await AGENT_REGISTRY.unregister(agent_id)


if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")
