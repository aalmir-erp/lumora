"""In-memory session store. Keyed by session_id. Trim to last N turns.

For production, swap this for Redis or Postgres so sessions survive a deploy.
"""
import secrets
import time
from collections import OrderedDict
from threading import Lock

MAX_TURNS = 30          # 15 user + 15 assistant
SESSION_TTL_SEC = 60 * 60 * 6  # 6 hours
MAX_SESSIONS = 1000


class SessionStore:
    def __init__(self) -> None:
        self._data: "OrderedDict[str, dict]" = OrderedDict()
        self._lock = Lock()

    def new_id(self) -> str:
        return "us-" + secrets.token_urlsafe(12)

    def get(self, sid: str) -> dict:
        with self._lock:
            self._evict()
            sess = self._data.get(sid)
            if not sess:
                sess = {"messages": [], "created": time.time(), "last": time.time()}
                self._data[sid] = sess
            sess["last"] = time.time()
            self._data.move_to_end(sid)
            return sess

    def append(self, sid: str, role: str, content) -> None:
        sess = self.get(sid)
        sess["messages"].append({"role": role, "content": content})
        # Keep only the last MAX_TURNS messages
        if len(sess["messages"]) > MAX_TURNS:
            sess["messages"] = sess["messages"][-MAX_TURNS:]

    def _evict(self) -> None:
        now = time.time()
        # TTL eviction
        stale = [k for k, v in self._data.items() if now - v["last"] > SESSION_TTL_SEC]
        for k in stale:
            self._data.pop(k, None)
        # LRU cap
        while len(self._data) > MAX_SESSIONS:
            self._data.popitem(last=False)


store = SessionStore()
