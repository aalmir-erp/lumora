"""Full orchestrator tests using mocked AI backend and runtime.

These don't need network, API keys, or a browser. They prove the FULL state
machine works:
  - task created in store
  - AI backend asked for next step
  - runtime executes, observation flows back
  - history grows, screenshots emitted
  - done event fires, webhook called, status set

Run: cd services/scraper && python -m tests.test_orchestrator
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("LOCAL_AGENT_TOKEN", "t")

from server.tasks import STORE, run_task, Task
from server.runtime.base import BrowserRuntime, RuntimeAction, RuntimeObservation, RuntimeError
from server.ai.base import AIBackend, AIContext, AIPlan
from server import tasks as tasks_module


class FakeRuntime(BrowserRuntime):
    name = "fake"

    def __init__(self, *, fail_on: int | None = None, recoverable: bool = True) -> None:
        self.started = False
        self.stopped = False
        self.actions: list[RuntimeAction] = []
        self._step = 0
        self._fail_on = fail_on
        self._recoverable = recoverable

    async def start(self, *, mode="browser") -> None:
        self.started = True

    async def execute(self, action: RuntimeAction) -> RuntimeObservation:
        self.actions.append(action)
        self._step += 1
        if self._fail_on is not None and self._step == self._fail_on:
            raise RuntimeError("simulated", recoverable=self._recoverable)
        return RuntimeObservation(
            screenshot_b64="ZmFrZQ==",  # base64 "fake"
            url=action.args.get("url", "https://fake.example"),
            text="hello world",
        )

    async def stop(self) -> None:
        self.stopped = True


class FakeAI(AIBackend):
    name = "fake-ai"

    def __init__(self, plan: list[AIPlan]) -> None:
        self._plan = list(plan)
        self.calls = 0

    async def next_step(self, ctx: AIContext, observation: RuntimeObservation) -> AIPlan:
        self.calls += 1
        if not self._plan:
            return AIPlan(done=True, reasoning="exhausted")
        return self._plan.pop(0)


async def _run_with(plan: list[AIPlan], runtime: BrowserRuntime, **task_kwargs) -> Task:
    """Drop-in helper that monkey-patches the factories used by run_task."""
    from server import ai as ai_pkg, runtime as runtime_pkg
    fake_ai = FakeAI(plan)
    orig_ai = ai_pkg.build_backend
    orig_rt = runtime_pkg.build_runtime
    ai_pkg.build_backend = lambda name: fake_ai
    runtime_pkg.build_runtime = lambda name, agent_id=None: runtime
    # tasks.py does `from .ai import build_backend` so patch the import-site too:
    tasks_module.build_backend = lambda name: fake_ai
    tasks_module.build_runtime = lambda name, agent_id=None: runtime
    try:
        defaults = {"goal": "test", "backend": "fake", "runtime": "fake",
                    "mode": "browser", "max_steps": 10}
        defaults.update(task_kwargs)
        task = STORE.create(**defaults)
        await run_task(task)
        return task
    finally:
        ai_pkg.build_backend = orig_ai
        runtime_pkg.build_runtime = orig_rt
        tasks_module.build_backend = orig_ai
        tasks_module.build_runtime = orig_rt


# --- tests ---

async def test_happy_path():
    plan = [
        AIPlan(action=RuntimeAction(type="goto", args={"url": "https://x"})),
        AIPlan(action=RuntimeAction(type="extract_text", args={})),
        AIPlan(done=True, final_answer="ok", reasoning="found it"),
    ]
    rt = FakeRuntime()
    task = await _run_with(plan, rt)
    assert task.status == "done", task.status
    assert task.final_answer == "ok"
    assert rt.started and rt.stopped
    assert len(rt.actions) == 2
    kinds = [e.kind for e in task.events]
    assert "start" in kinds and "done" in kinds
    assert any(e.kind == "screenshot" for e in task.events)
    print("test_happy_path OK")


async def test_recoverable_error_still_continues():
    plan = [
        AIPlan(action=RuntimeAction(type="goto", args={"url": "https://x"})),
        AIPlan(action=RuntimeAction(type="goto", args={"url": "https://y"})),
        AIPlan(done=True, final_answer="recovered"),
    ]
    rt = FakeRuntime(fail_on=1, recoverable=True)
    task = await _run_with(plan, rt)
    assert task.status == "done", f"got {task.status}"
    assert task.final_answer == "recovered"
    assert any(e.kind == "error" for e in task.events)
    print("test_recoverable_error_still_continues OK")


async def test_unrecoverable_fails_task():
    plan = [
        AIPlan(action=RuntimeAction(type="goto", args={"url": "https://x"})),
        AIPlan(action=RuntimeAction(type="goto", args={"url": "https://y"})),
    ]
    rt = FakeRuntime(fail_on=1, recoverable=False)
    task = await _run_with(plan, rt)
    assert task.status == "failed", task.status
    assert "simulated" in (task.error or "")
    print("test_unrecoverable_fails_task OK")


async def test_max_steps_terminates():
    plan = [AIPlan(action=RuntimeAction(type="wait", args={"seconds": 0})) for _ in range(20)]
    rt = FakeRuntime()
    task = await _run_with(plan, rt, max_steps=3)
    assert task.status == "done"
    # Used exactly max_steps actions
    assert len(rt.actions) == 3
    print("test_max_steps_terminates OK")


async def test_demo_backend_real():
    """Run the real DemoBackend (no API keys) against FakeRuntime."""
    from server.ai.demo import DemoBackend
    from server import ai as ai_pkg, runtime as runtime_pkg
    rt = FakeRuntime()
    orig_ai = ai_pkg.build_backend
    orig_rt = runtime_pkg.build_runtime
    backend = DemoBackend()
    ai_pkg.build_backend = lambda name: backend
    runtime_pkg.build_runtime = lambda name, agent_id=None: rt
    tasks_module.build_backend = lambda name: backend
    tasks_module.build_runtime = lambda name, agent_id=None: rt
    try:
        task = STORE.create(goal="open https://example.com", backend="demo",
                            runtime="fake", mode="browser", max_steps=8)
        await run_task(task)
        assert task.status == "done"
        assert task.final_answer is not None
    finally:
        ai_pkg.build_backend = orig_ai
        runtime_pkg.build_runtime = orig_rt
        tasks_module.build_backend = orig_ai
        tasks_module.build_runtime = orig_rt
    print("test_demo_backend_real OK")


async def main():
    await test_happy_path()
    await test_recoverable_error_still_continues()
    await test_unrecoverable_fails_task()
    await test_max_steps_terminates()
    await test_demo_backend_real()
    print("\nALL ORCHESTRATOR TESTS OK")


if __name__ == "__main__":
    asyncio.run(main())
