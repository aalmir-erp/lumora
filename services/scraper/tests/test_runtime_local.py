"""LocalRuntime test using a fake ConnectedAgent — proves the WebSocket
forwarding contract works end-to-end without a real local PC.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("LOCAL_AGENT_TOKEN", "t")

from server.runtime.local import LocalRuntime
from server.runtime.agent_registry import AGENT_REGISTRY, ConnectedAgent
from server.runtime.base import RuntimeAction


class CannedAgent:
    """Stand-in for ConnectedAgent that yields scripted server-bound replies."""

    def __init__(self, scripted_replies: list[dict]) -> None:
        self.sent: list = []
        self._replies = list(scripted_replies)
        self.closed = False
        self.agent_id = "fake"

    async def send(self, msg) -> None:
        self.sent.append(msg)

    async def recv(self, timeout: float = 60.0) -> dict:
        return self._replies.pop(0)


async def test_local_runtime_executes_via_ws():
    canned = CannedAgent([
        {"op": "started", "mode": "browser"},                                # start ack
        {"op": "result", "id": None, "data": {"screenshot_b64": "AA==", "url": "https://x"}},
    ])
    rt = LocalRuntime()
    # Inject our fake into the registry so rt.start() picks it up
    AGENT_REGISTRY._agents["fake"] = canned  # type: ignore
    try:
        await rt.start(mode="browser")
        obs = await rt.execute(RuntimeAction(type="goto", args={"url": "https://x"}))
        assert obs.url == "https://x"
        assert obs.screenshot_b64 == "AA=="
        # Verify the server actually sent a start + action
        assert canned.sent[0]["op"] == "start"
        assert canned.sent[1]["op"] == "action"
        assert canned.sent[1]["type"] == "goto"
    finally:
        AGENT_REGISTRY._agents.pop("fake", None)
    print("test_local_runtime_executes_via_ws OK")


async def test_local_runtime_no_agent_fails_clearly():
    rt = LocalRuntime(agent_id="missing")
    AGENT_REGISTRY._agents.clear()
    try:
        await rt.start(mode="browser")
    except Exception as e:
        assert "No local agent connected" in str(e)
        print("test_local_runtime_no_agent_fails_clearly OK")
        return
    raise AssertionError("expected error")


async def test_local_runtime_propagates_agent_error():
    canned = CannedAgent([
        {"op": "started", "mode": "browser"},
        {"op": "error", "id": None, "message": "captcha", "recoverable": True},
    ])
    rt = LocalRuntime()
    AGENT_REGISTRY._agents["fake"] = canned  # type: ignore
    try:
        await rt.start(mode="browser")
        try:
            await rt.execute(RuntimeAction(type="goto", args={"url": "https://x"}))
        except Exception as e:
            assert "captcha" in str(e)
            print("test_local_runtime_propagates_agent_error OK")
            return
        raise AssertionError("expected error")
    finally:
        AGENT_REGISTRY._agents.pop("fake", None)


async def main():
    await test_local_runtime_executes_via_ws()
    await test_local_runtime_no_agent_fails_clearly()
    await test_local_runtime_propagates_agent_error()
    print("\nALL LOCAL RUNTIME TESTS OK")


if __name__ == "__main__":
    asyncio.run(main())
