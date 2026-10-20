"""Lightweight timing recorder.

Writes one human-readable log line (``[TIMING:<KIND>] ...``) and, when
enabled, one JSON line to ``logs/timing.jsonl`` for every timed event
(HTTP request, report analysis, chat answer). ``scripts/timing_report.py``
summarises that file.

Only durations, route templates, provider/model names and counts are stored -
never request bodies, report text, prompts or user identifiers.
Recording is best effort: a failure here can never break a request.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger("app.timing")

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_MAX_BYTES = 5 * 1024 * 1024
_lock = threading.Lock()


def timing_log_path() -> Path:
    override = os.environ.get("TIMING_LOG_PATH")
    return Path(override) if override else _BACKEND_ROOT / "logs" / "timing.jsonl"


class Stopwatch:
    """Records named laps; ``laps_ms`` holds the duration of each lap."""

    def __init__(self) -> None:
        self._start = time.perf_counter()
        self._last = self._start
        self.laps_ms: dict[str, int] = {}

    def lap(self, name: str) -> int:
        now = time.perf_counter()
        ms = int((now - self._last) * 1000)
        self.laps_ms[name] = self.laps_ms.get(name, 0) + ms
        self._last = now
        return ms

    def add(self, name: str, ms: int) -> None:
        """Record a duration measured elsewhere (e.g. work done concurrently)."""
        self.laps_ms[name] = self.laps_ms.get(name, 0) + int(ms)

    def total_ms(self) -> int:
        return int((time.perf_counter() - self._start) * 1000)


def record(kind: str, name: str, total_ms: int, **fields: object) -> None:
    """Log and persist one timing event. Never raises."""
    try:
        detail = " ".join(f"{k}={v}" for k, v in fields.items() if v is not None)
        slow = total_ms >= int(settings.TIMING_SLOW_REQUEST_MS)
        line = f"[TIMING:{kind}] {name} total={total_ms}ms {detail}".rstrip()
        (logger.warning if slow else logger.info)(line + (" SLOW" if slow else ""))
        if not settings.TIMING_LOG_ENABLED:
            return
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "kind": kind,
            "name": name,
            "total_ms": int(total_ms),
            **{k: v for k, v in fields.items() if v is not None},
        }
        path = timing_log_path()
        with _lock:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists() and path.stat().st_size > _MAX_BYTES:
                path.replace(path.with_suffix(".jsonl.1"))
            with path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, default=str) + "\n")
    except Exception:  # pragma: no cover - timing must never break the app
        logger.debug("timing record failed", exc_info=True)
