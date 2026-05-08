import pytest

from app.conversation import InMemoryStore, Turn


@pytest.mark.asyncio
async def test_in_memory_append_and_history():
    store = InMemoryStore(max_turns=3)
    await store.append("u1", Turn(role="user", content="hi", ts=1.0))
    await store.append("u1", Turn(role="assistant", content="hello", ts=2.0))
    h = await store.history("u1")
    assert [(t.role, t.content) for t in h] == [("user", "hi"), ("assistant", "hello")]


@pytest.mark.asyncio
async def test_in_memory_caps_at_2x_turns():
    store = InMemoryStore(max_turns=2)  # capacity = 4 messages
    for i in range(10):
        await store.append("u1", Turn(role="user", content=str(i), ts=float(i)))
    h = await store.history("u1")
    assert len(h) == 4
    assert h[0].content == "6"
    assert h[-1].content == "9"


@pytest.mark.asyncio
async def test_clear():
    store = InMemoryStore(max_turns=3)
    await store.append("u1", Turn(role="user", content="x", ts=1.0))
    await store.clear("u1")
    assert await store.history("u1") == []
