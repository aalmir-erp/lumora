"""In-process log ring buffer so admin can read server logs from the
admin UI without Railway access.

How it works:
  - We tee sys.stdout / sys.stderr through a writer that pushes every
    line into a thread-safe deque (capped at 2,000 lines).
  - Lines flow normally to the original stdout/stderr so Railway logs
    are unchanged.
  - GET /api/admin/logs/tail returns the buffer + (optionally) only
    lines after a given timestamp/cursor.

Founder ask (v1.24.192): "instead of railway logs generate print produce
everything in front end in admin and see logs issue there itself."
"""
from __future__ import annotations
import collections, datetime as _dt, io, sys, threading
from dataclasses import dataclass

MAX_LINES = 2000

_lock = threading.Lock()
_buffer: collections.deque = collections.deque(maxlen=MAX_LINES)
_next_id = 0


@dataclass
class _LogLine:
    id: int
    ts: str       # ISO 8601 UTC
    stream: str   # 'stdout' | 'stderr'
    text: str


def _push(stream: str, text: str) -> None:
    global _next_id
    if not text:
        return
    # Split on newlines so each visual line is its own entry.
    for line in text.splitlines():
        line = line.rstrip("\r")
        if not line.strip():
            continue
        with _lock:
            _next_id += 1
            _buffer.append(_LogLine(
                id=_next_id,
                ts=_dt.datetime.utcnow().isoformat() + "Z",
                stream=stream,
                text=line[:2000],  # hard cap so a single rogue line can't blow up
            ))


class _TeeStream:
    """File-like wrapper that mirrors writes into the ring buffer."""

    def __init__(self, real, stream_name: str):
        self._real = real
        self._stream_name = stream_name
        # Carry through attributes that frameworks probe (e.g. .fileno).
        self.encoding = getattr(real, "encoding", "utf-8")

    def write(self, s):
        try:
            self._real.write(s)
        except Exception:
            pass
        try:
            _push(self._stream_name, s if isinstance(s, str) else s.decode("utf-8", "replace"))
        except Exception:
            pass
        return len(s) if isinstance(s, (str, bytes)) else 0

    def flush(self):
        try:
            self._real.flush()
        except Exception:
            pass

    def isatty(self):
        try:
            return self._real.isatty()
        except Exception:
            return False

    def fileno(self):
        return self._real.fileno()

    def __getattr__(self, item):
        return getattr(self._real, item)


def install() -> None:
    """Idempotently install the tee writers on sys.stdout/sys.stderr."""
    if isinstance(sys.stdout, _TeeStream) and isinstance(sys.stderr, _TeeStream):
        return
    if not isinstance(sys.stdout, _TeeStream):
        sys.stdout = _TeeStream(sys.stdout, "stdout")
    if not isinstance(sys.stderr, _TeeStream):
        sys.stderr = _TeeStream(sys.stderr, "stderr")


def tail(limit: int = 500, after_id: int = 0,
         q: str | None = None, stream: str | None = None) -> dict:
    """Return up to `limit` most-recent buffered lines (optionally
    filtered by stream and substring), plus the high-water-mark id so
    the client can poll for new entries only."""
    with _lock:
        snapshot = list(_buffer)
        head_id = _next_id
    out = []
    needle = (q or "").lower().strip() or None
    for entry in snapshot:
        if entry.id <= after_id:
            continue
        if stream and entry.stream != stream:
            continue
        if needle and needle not in entry.text.lower():
            continue
        out.append({"id": entry.id, "ts": entry.ts,
                    "stream": entry.stream, "text": entry.text})
    # Trim oldest first if over limit.
    if len(out) > limit:
        out = out[-limit:]
    return {"lines": out, "cursor": head_id, "size": len(snapshot)}


def manual(text: str, stream: str = "stdout") -> None:
    """Allow code to push a labeled marker directly (useful for boot)."""
    _push(stream, text)
