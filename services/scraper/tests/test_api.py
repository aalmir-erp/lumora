"""HTTP API tests using FastAPI's TestClient — proves all endpoints respond,
auth works, diag endpoint reports correctly.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("LOCAL_AGENT_TOKEN", "t")

from fastapi.testclient import TestClient

from server.main import app


client = TestClient(app)


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["ok"] is True
    print("test_healthz OK")


def test_root_serves_ui():
    r = client.get("/")
    assert r.status_code == 200
    assert "LUMORA SCRAPER" in r.text or "scraper" in r.text.lower()
    print("test_root_serves_ui OK")


def test_config():
    r = client.get("/api/config")
    assert r.status_code == 200
    j = r.json()
    assert "demo" in j["backends"]
    assert set(j["runtimes"]) == {"railway", "local", "hybrid"}
    print("test_config OK")


def test_diag_no_keys():
    r = client.get("/api/diag")
    assert r.status_code == 200
    j = r.json()
    names = [c["name"] for c in j["checks"]]
    assert "GOOGLE_API_KEY" in names
    assert "ANTHROPIC_API_KEY" in names
    assert "LOCAL_AGENT_TOKEN" in names
    assert "agents_connected" in names
    print("test_diag_no_keys OK")


def test_create_task_and_list():
    r = client.post("/api/tasks", json={"goal": "demo task", "backend": "demo",
                                        "runtime": "railway", "mode": "browser"})
    assert r.status_code == 200, r.text
    tid = r.json()["id"]
    assert tid
    r = client.get("/api/tasks")
    assert r.status_code == 200
    ids = [t["id"] for t in r.json()["tasks"]]
    assert tid in ids
    r = client.get(f"/api/tasks/{tid}")
    assert r.status_code == 200
    print("test_create_task_and_list OK")


def test_get_unknown_task():
    r = client.get("/api/tasks/does-not-exist")
    assert r.status_code == 404
    print("test_get_unknown_task OK")


def test_ws_rejects_bad_token():
    """WebSocket should reject connections without/with wrong token."""
    from starlette.websockets import WebSocketDisconnect
    try:
        with client.websocket_connect("/ws/agent?token=wrong&agent_id=pc1"):
            raise AssertionError("expected reject")
    except WebSocketDisconnect:
        pass
    print("test_ws_rejects_bad_token OK")


def main():
    test_healthz()
    test_root_serves_ui()
    test_config()
    test_diag_no_keys()
    test_create_task_and_list()
    test_get_unknown_task()
    test_ws_rejects_bad_token()
    print("\nALL API TESTS OK")


if __name__ == "__main__":
    main()
