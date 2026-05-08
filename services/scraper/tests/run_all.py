"""Single entry point that runs every unit/integration test.

Intentionally NOT pytest — keeps deps minimal and CI fast. Returns non-zero
exit on any failure.
"""
import asyncio
import importlib
import os
import sys
import traceback


TESTS = [
    ("test_smoke", None),
    ("test_agent_registry", "main"),
    ("test_orchestrator", "main"),
    ("test_runtime_local", "main"),
    ("test_api", "main"),
]


def run_module(name: str, entry: str | None) -> tuple[bool, str]:
    sys.path.insert(0, os.path.dirname(__file__))
    try:
        mod = importlib.import_module(f"tests.{name}")
        if entry is None:
            # test_smoke uses bare functions; call all test_* attrs
            for attr in dir(mod):
                if attr.startswith("test_") and callable(getattr(mod, attr)):
                    getattr(mod, attr)()
        else:
            fn = getattr(mod, entry)
            res = fn()
            if asyncio.iscoroutine(res):
                asyncio.run(res)
        return True, ""
    except Exception:
        return False, traceback.format_exc()


def main() -> int:
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    os.environ.setdefault("LOCAL_AGENT_TOKEN", "t")
    failures = []
    for name, entry in TESTS:
        print(f"\n=== {name} ===")
        ok, err = run_module(name, entry)
        if not ok:
            print(err)
            failures.append(name)
    print("\n" + "=" * 60)
    if failures:
        print(f"FAIL: {failures}")
        return 1
    print("ALL TESTS OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
