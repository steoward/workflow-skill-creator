import os
import sys
import tempfile
import threading
import time
import pytest

# Ensure scripts directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from rate_limiter import FileLock, CrossProcessRateLimiter, RateLimitError, retry_with_backoff


def test_file_lock_basic():
    with tempfile.TemporaryDirectory() as tmpdir:
        lock_path = os.path.join(tmpdir, "test.lock")
        with FileLock(lock_path, timeout=5.0):
            assert os.path.exists(lock_path)


def test_rate_limiter_interval():
    with tempfile.TemporaryDirectory() as tmpdir:
        # 5 requests per second -> 0.20s interval
        limiter = CrossProcessRateLimiter("test_api", requests_per_second=5.0, state_dir=tmpdir)
        t0 = time.time()
        limiter.wait()
        w = limiter.wait()
        t1 = time.time()

        elapsed = t1 - t0
        assert elapsed >= 0.15, f"Expected elapsed >= 0.15s, got {elapsed:.3f}s"
        assert w > 0.0


def test_concurrent_rate_limiting():
    with tempfile.TemporaryDirectory() as tmpdir:
        # 10 requests per second -> 0.10s interval
        num_workers = 4
        records = []

        def worker():
            limiter = CrossProcessRateLimiter("concurrent_test", requests_per_second=10.0, state_dir=tmpdir)
            limiter.wait()
            records.append(time.time())

        t0 = time.time()
        threads = [threading.Thread(target=worker) for _ in range(num_workers)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        total_time = time.time() - t0

        assert len(records) == num_workers
        # 4 requests at 10 rps should take at least ~0.25s
        assert total_time >= 0.20, f"Expected total_time >= 0.20s, got {total_time:.3f}s"


def test_retry_with_backoff_success():
    calls = 0

    @retry_with_backoff(retries=3, base_delay=0.01, jitter=False)
    def flaky_func():
        nonlocal calls
        calls += 1
        if calls < 2:
            raise RateLimitError("Rate limit hit")
        return "success"

    assert flaky_func() == "success"
    assert calls == 2


def test_retry_with_backoff_exhausted():
    calls = 0

    @retry_with_backoff(retries=2, base_delay=0.01, jitter=False)
    def failing_func():
        nonlocal calls
        calls += 1
        raise RateLimitError("Always fails")

    with pytest.raises(RateLimitError):
        failing_func()
    assert calls == 2
