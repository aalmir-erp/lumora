"""Smoke tests that import everything and exercise the static factories.

Run: cd services/scraper && python -m pytest tests/test_smoke.py
(or just: python -m tests.test_smoke)
"""
import os
import sys

os.environ.setdefault("DEFAULT_BACKEND", "gemini-pro")
os.environ.setdefault("DEFAULT_RUNTIME", "hybrid")
os.environ.setdefault("LOCAL_AGENT_TOKEN", "test-token")

from server import config  # noqa
from server.runtime import build_runtime
from server.runtime.base import RuntimeAction, RuntimeError
from server.runtime.hybrid import HybridRuntime, _force_local
from server.ai import build_backend


def test_runtime_factory():
    assert build_runtime("railway").name == "railway"
    assert build_runtime("local").name == "local"
    assert isinstance(build_runtime("hybrid"), HybridRuntime)


def test_backend_factory():
    for n in ["gemini-pro", "gemini-flash", "gemini-cu", "claude-cu"]:
        b = build_backend(n)
        assert b.name == n


def test_force_local_routing():
    assert _force_local("https://web.whatsapp.com/") is True
    assert _force_local("https://api.example.com/") is False
    assert _force_local(None) is False


def test_runtime_error():
    e = RuntimeError("captcha", recoverable=True)
    assert e.recoverable is True


if __name__ == "__main__":
    test_runtime_factory()
    test_backend_factory()
    test_force_local_routing()
    test_runtime_error()
    print("OK")
