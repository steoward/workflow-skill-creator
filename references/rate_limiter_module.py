"""Standalone copy-pasteable rate limiter module with cross-process file locking.

Add this file directly into your skill's `scripts/` directory to enable
concurrent multi-agent rate limiting across processes on Windows, macOS, and Linux.
"""

from __future__ import annotations

import functools
import json
import os
import random
import sys
import tempfile
import time
from typing import Any, Callable, Dict, Optional


class RateLimitError(Exception):
    """Raised when an API rate limit is exceeded."""
    pass


class FileLock:
    def __init__(self, lock_file_path: str, timeout: float = 60.0):
        self.lock_file_path = os.path.abspath(lock_file_path)
        self.timeout = timeout
        self.file_obj: Optional[Any] = None

    def __enter__(self) -> FileLock:
        start_time = time.monotonic()
        parent_dir = os.path.dirname(self.lock_file_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        self.file_obj = open(self.lock_file_path, "a+b")
        while True:
            try:
                if sys.platform == "win32":
                    import msvcrt
                    self.file_obj.seek(0)
                    if self.file_obj.tell() == 0 and os.fstat(self.file_obj.fileno()).st_size == 0:
                        self.file_obj.write(b"0")
                        self.file_obj.flush()
                    self.file_obj.seek(0)
                    msvcrt.locking(self.file_obj.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(self.file_obj.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self
            except (OSError, IOError):
                if time.monotonic() - start_time >= self.timeout:
                    self._cleanup()
                    raise TimeoutError(f"Timed out after {self.timeout}s waiting for lock: {self.lock_file_path}")
                time.sleep(0.05)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cleanup()

    def _cleanup(self):
        if self.file_obj is not None:
            try:
                if sys.platform == "win32":
                    import msvcrt
                    self.file_obj.seek(0)
                    msvcrt.locking(self.file_obj.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(self.file_obj.fileno(), fcntl.LOCK_UN)
            except Exception:
                pass
            finally:
                try:
                    self.file_obj.close()
                except Exception:
                    pass
                self.file_obj = None


class CrossProcessRateLimiter:
    def __init__(
        self,
        name: str,
        requests_per_second: float = 1.0,
        state_dir: Optional[str] = None,
        lock_timeout: float = 30.0,
    ):
        if requests_per_second <= 0:
            raise ValueError("requests_per_second must be positive")

        self.name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in name)
        self.requests_per_second = requests_per_second
        self.interval = 1.0 / requests_per_second
        self.lock_timeout = lock_timeout

        base_dir = state_dir or os.path.join(tempfile.gettempdir(), "agent_rate_limits")
        os.makedirs(base_dir, exist_ok=True)

        self.lock_path = os.path.join(base_dir, f"{self.name}.lock")
        self.state_path = os.path.join(base_dir, f"{self.name}.json")

    def _read_last_timestamp(self) -> float:
        if not os.path.exists(self.state_path):
            return 0.0
        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return float(data.get("last_request_time", 0.0))
        except (OSError, ValueError, json.JSONDecodeError):
            return 0.0

    def _write_last_timestamp(self, ts: float):
        try:
            with open(self.state_path, "w", encoding="utf-8") as f:
                json.dump({"last_request_time": ts, "rps": self.requests_per_second}, f)
        except OSError:
            pass

    def wait(self) -> float:
        with FileLock(self.lock_path, timeout=self.lock_timeout):
            last_time = self._read_last_timestamp()
            now = time.time()
            elapsed = now - last_time
            wait_time = 0.0

            if elapsed < self.interval:
                wait_time = self.interval - elapsed
                time.sleep(wait_time)
                now = time.time()

            self._write_last_timestamp(now)
            return wait_time
