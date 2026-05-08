"""Task store + orchestrator that drives the AI <-> Runtime loop."""
from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Literal

import httpx

from . import config
from .ai import build_backend
from .ai.base import AIContext
from .runtime import build_runtime
from .runtime.base import RuntimeAction, RuntimeObservation, RuntimeError


TaskStatus = Literal["pending", "running", "done", "failed", "cancelled"]


@dataclass
class TaskEvent:
    ts: float
    kind: str  # "start" | "step" | "screenshot" | "status" | "error" | "done"
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class Task:
    id: str
    goal: str
    backend: str
    runtime: str
    mode: str
    agent_id: str | None = None
    max_steps: int = 25
    status: TaskStatus = "pending"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    events: list[TaskEvent] = field(default_factory=list)
    final_answer: Any = None
    error: str | None = None
    active_runtime: str = ""

    def add(self, kind: str, **data: Any) -> TaskEvent:
        ev = TaskEvent(ts=time.time(), kind=kind, data=data)
        self.events.append(ev)
        self.updated_at = ev.ts
        return ev


class TaskStore:
    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}
        self._listeners: dict[str, list[asyncio.Queue[TaskEvent]]] = {}

    def create(self, **kw: Any) -> Task:
        tid = uuid.uuid4().hex[:12]
        t = Task(id=tid, **kw)
        self._tasks[tid] = t
        self._listeners[tid] = []
        return t

    def get(self, tid: str) -> Task | None:
        return self._tasks.get(tid)

    def list(self) -> list[Task]:
        return list(self._tasks.values())

    async def subscribe(self, tid: str) -> asyncio.Queue[TaskEvent]:
        q: asyncio.Queue[TaskEvent] = asyncio.Queue()
        self._listeners.setdefault(tid, []).append(q)
        return q

    def unsubscribe(self, tid: str, q: asyncio.Queue) -> None:
        if tid in self._listeners and q in self._listeners[tid]:
            self._listeners[tid].remove(q)

    def emit(self, tid: str, ev: TaskEvent) -> None:
        for q in self._listeners.get(tid, []):
            try:
                q.put_nowait(ev)
            except Exception:
                pass


STORE = TaskStore()


async def _post_webhook(payload: dict[str, Any]) -> None:
    if not config.STATUS_WEBHOOK_URL:
        return
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            await c.post(config.STATUS_WEBHOOK_URL, json=payload)
    except Exception:
        pass


async def run_task(task: Task) -> None:
    task.status = "running"
    task.add("start", goal=task.goal, backend=task.backend, runtime=task.runtime, mode=task.mode)
    STORE.emit(task.id, task.events[-1])
    await _post_webhook({"event": "start", "task_id": task.id, "goal": task.goal})

    backend = build_backend(task.backend)
    runtime = build_runtime(task.runtime, agent_id=task.agent_id)

    try:
        await runtime.start(mode=task.mode)  # type: ignore
        task.active_runtime = getattr(runtime, "active_runtime", runtime.name)
        ctx = AIContext(goal=task.goal, max_steps=task.max_steps, mode=task.mode)
        observation = RuntimeObservation()

        for step in range(task.max_steps):
            if task.status == "cancelled":
                break
            plan = await backend.next_step(ctx, observation)
            if plan.done or plan.action is None:
                task.final_answer = plan.final_answer
                task.add("done", reasoning=plan.reasoning, answer=plan.final_answer)
                STORE.emit(task.id, task.events[-1])
                break
            ev = task.add("step", step=step, action=plan.action.type, args=plan.action.args, reasoning=plan.reasoning)
            STORE.emit(task.id, ev)
            try:
                observation = await runtime.execute(plan.action)
            except RuntimeError as e:
                task.add("error", message=str(e), recoverable=e.recoverable)
                STORE.emit(task.id, task.events[-1])
                if not e.recoverable:
                    raise
                observation = RuntimeObservation(error=str(e))
            ctx.history.append({
                "step": step,
                "action": plan.action.type,
                "url": observation.url,
                "error": observation.error,
            })
            if observation.screenshot_b64:
                shot = task.add("screenshot", step=step, b64=observation.screenshot_b64, url=observation.url)
                STORE.emit(task.id, shot)
            task.active_runtime = getattr(runtime, "active_runtime", runtime.name)

        task.status = "done" if task.status != "cancelled" else "cancelled"
    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        task.add("error", message=str(e))
        STORE.emit(task.id, task.events[-1])
    finally:
        try:
            await runtime.stop()
        except Exception:
            pass
        await _post_webhook({
            "event": "done",
            "task_id": task.id,
            "status": task.status,
            "answer": task.final_answer,
            "error": task.error,
        })
