"""Tests for the agent registry — the WebSocket message routing layer
between server runtime and connected local agents.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("LOCAL_AGENT_TOKEN", "t")

from server.runtime.agent_registry import AgentRegistry, ConnectedAgent


class FakeWS:
    def __init__(self) -> None:
        self.sent: list = []

    async def send_json(self, m) -> None:
        self.sent.append(m)


async def test_register_pick_unregister():
    reg = AgentRegistry()
    ws = FakeWS()
    a = await reg.register("pc1", ws)  # type: ignore
    assert reg.pick("pc1") is a
    assert reg.pick() is a  # auto-pick first available
    assert "pc1" in reg.list_agents()
    await reg.unregister("pc1")
    assert reg.pick() is None
    print("test_register_pick_unregister OK")


async def test_send_recv_roundtrip():
    reg = AgentRegistry()
    ws = FakeWS()
    a = await reg.register("pc1", ws)  # type: ignore
    await a.send({"op": "ping"})
    assert ws.sent == [{"op": "ping"}]
    await a.push({"op": "pong"})
    msg = await asyncio.wait_for(a.recv(timeout=1), timeout=1)
    assert msg == {"op": "pong"}
    print("test_send_recv_roundtrip OK")


async def test_re_register_replaces_old():
    reg = AgentRegistry()
    ws1 = FakeWS()
    ws2 = FakeWS()
    a1 = await reg.register("pc1", ws1)  # type: ignore
    a2 = await reg.register("pc1", ws2)  # type: ignore
    assert a1.closed
    assert not a2.closed
    assert reg.pick("pc1") is a2
    print("test_re_register_replaces_old OK")


async def test_recv_timeout():
    reg = AgentRegistry()
    a = await reg.register("pc1", FakeWS())  # type: ignore
    try:
        await a.recv(timeout=0.1)
    except asyncio.TimeoutError:
        print("test_recv_timeout OK")
        return
    raise AssertionError("expected timeout")


async def main():
    await test_register_pick_unregister()
    await test_send_recv_roundtrip()
    await test_re_register_replaces_old()
    await test_recv_timeout()
    print("\nALL AGENT REGISTRY TESTS OK")


if __name__ == "__main__":
    asyncio.run(main())
