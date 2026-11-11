"""API CLI Script Template with Cross-Process Rate Limiting.

Copy and adapt this pattern when generating multi-command CLI scripts for external APIs.
Designed specifically for AI agents:
- Argparse subcommands map to workflow operations.
- Direct output to files via '--output' (never floods stdout).
- Stdlib-only (urllib, json, argparse) for maximum portability.
- Cross-process file-locking rate limiter prevents HTTP 429 when concurrent agents execute.
- Reads error bodies for rich agent self-correction.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

try:
    from rate_limiter import CrossProcessRateLimiter, RateLimitError
except ImportError:
    # Graceful fallback to inline local rate limiter
    class RateLimitError(Exception): pass
    class CrossProcessRateLimiter:
        def __init__(self, name: str, requests_per_second: float = 1.0):
            self.delay = 1.0 / requests_per_second
            self.last = 0.0
        def wait(self):
            elapsed = time.monotonic() - self.last
            if elapsed < self.delay:
                time.sleep(self.delay - elapsed)
            self.last = time.monotonic()


class MyAPIClient:
    """Client for target API with cross-process rate limiting."""

    BASE_URL = "https://api.example.com/v1"
    REQUESTS_PER_SECOND = 5.0

    def __init__(self):
        self.limiter = CrossProcessRateLimiter(
            name="example_api",
            requests_per_second=self.REQUESTS_PER_SECOND,
        )

    def _request(self, path: str, params: dict | None = None, retries: int = 3) -> dict | list:
        url = f"{self.BASE_URL}{path}"
        if params:
            url = f"{url}?{urllib_parse.urlencode(params)}"

        for attempt in range(retries):
            self.limiter.wait()
            try:
                req = urllib_request.Request(url)
                req.add_header("Accept", "application/json")
                req.add_header("User-Agent", "AgentSkill/2.0")

                with urllib_request.urlopen(req, timeout=30) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib_error.HTTPError as e:
                if e.code == 429:
                    wait = 2 ** attempt
                    print(
                        f"Rate limited (429), retrying in {wait}s (attempt {attempt + 1}/{retries})...",
                        file=sys.stderr,
                    )
                    if attempt == retries - 1:
                        raise RateLimitError(
                            f"HTTP 429 Too Many Requests from {self.BASE_URL} after {retries} retries."
                        ) from e
                    time.sleep(wait)
                    continue

                if e.code >= 500:
                    wait = 2 ** attempt
                    print(
                        f"Server error {e.code}, retrying in {wait}s (attempt {attempt + 1}/{retries})...",
                        file=sys.stderr,
                    )
                    if attempt == retries - 1:
                        raise RuntimeError(f"Server error {e.code} from {url} after {retries} retries.") from e
                    time.sleep(wait)
                    continue

                # Read body for actionable agent error guidance
                try:
                    body = e.read().decode("utf-8", errors="replace")[:1000]
                except Exception:
                    body = str(e.reason)
                raise RuntimeError(f"HTTP {e.code} from {url}: {body}") from e
            except urllib_error.URLError as e:
                if attempt == retries - 1:
                    raise RuntimeError(f"Failed to connect to {url} after {retries} attempts: {e}") from e
                time.sleep(2 ** attempt)

        raise RuntimeError(f"Failed to retrieve {url} after all retries.")

    def search(self, query: str, limit: int = 100) -> dict:
        return self._request("/search", params={"q": query, "limit": limit})

    def get_details(self, item_id: str) -> dict:
        return self._request(f"/items/{item_id}")


def write_output(data: dict | list, output_file: str):
    """Writes data to a JSON file cleanly."""
    try:
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Success! Data written to: {output_file}")
    except (OSError, TypeError) as e:
        print(f"Error writing to file {output_file}: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="API Wrapper Script")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: search
    p_search = subparsers.add_parser("search", help="Search items by query")
    p_search.add_argument("--query", required=True, help="Search query string")
    p_search.add_argument("--limit", type=int, required=True, help="Result limit (required, no silent capping)")
    p_search.add_argument("--output", required=True, help="Output JSON destination file path")

    # Subcommand: details
    p_details = subparsers.add_parser("details", help="Get item details")
    p_details.add_argument("--id", required=True, dest="item_id", help="Item identifier")
    p_details.add_argument("--output", required=True, help="Output JSON destination file path")

    args = parser.parse_args()
    client = MyAPIClient()

    if args.command == "search":
        data = client.search(args.query, limit=args.limit)
    elif args.command == "details":
        data = client.get_details(args.item_id)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        sys.exit(1)

    write_output(data, args.output)


if __name__ == "__main__":
    main()
