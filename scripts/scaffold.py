"""Scaffolder CLI for creating production-ready agent skills.

Generates a fully compliant skill structure (SKILL.md, scripts, references, tests)
with zero friction, conforming to the Antigravity & Universal Agent Skills standard.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Optional


SKILL_CLI_TEMPLATE = """---
name: {name}
description: >-
  {description}
---

# {title}

## Overview
{description}

## Dependencies
- Standard Python 3 (stdlib) or `uv run`

## Quick Start
```bash
uv run scripts/{script_name}.py search --query "example" --limit 10 --output results.json
```

## Utility Scripts
The skill provides a robust multi-command CLI wrapper located at `scripts/{script_name}.py`:

- **search**:
  `uv run scripts/{script_name}.py search --query <term> --limit <int> --output <file.json>`
- **details**:
  `uv run scripts/{script_name}.py details --id <id> --output <file.json>`

All commands output structured JSON directly to `--output` files to optimize token usage and avoid terminal buffer overflow.

## Rate Limiting & Concurrency
External requests are metered using cross-process file locking to prevent HTTP 429 rate limit errors when concurrent agents run on the same system.

## Common Mistakes
1. Reading huge responses into stdout instead of using `--output`.
2. Forgetting to provide required arguments like `--limit`.
3. Running with unmanaged `python` instead of `uv run`.
"""

SKILL_INSTRUCTION_TEMPLATE = """---
name: {name}
description: >-
  {description}
---

# {title}

## Overview
{description}

## Dependencies
- None (Orchestration / instruction-only workflow)

## Quick Start
Follow the steps defined in the workflow section below.

## Workflow

### 1. Step 1: Initialize Context
Review initial parameters and verify all prerequisites are met.

### 2. Step 2: Core Execution
Execute the sequence of actions following the protocol.

### 3. Step 3: Verification & Reporting
Verify the result against the expected outcome and provide a structured summary.

## Common Mistakes
1. Skipping the verification step.
2. Proceeding when initial prerequisites are missing.
"""

PYTHON_CLI_CODE = """# Auto-generated CLI by workflow-skill-creator
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
    # Fallback inline minimal rate limiter
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


class APIClient:
    BASE_URL = "{api_url}"

    def __init__(self, rps: float = {rps}):
        self.limiter = CrossProcessRateLimiter("{name}", requests_per_second=rps)

    def _request(self, path: str, params: dict | None = None, retries: int = 3) -> dict:
        url = f"{{self.BASE_URL}}{{path}}"
        if params:
            url = f"{{url}}?{{urllib_parse.urlencode(params)}}"

        for attempt in range(retries):
            self.limiter.wait()
            try:
                req = urllib_request.Request(url, headers={{"Accept": "application/json"}})
                with urllib_request.urlopen(req, timeout=30) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib_error.HTTPError as e:
                if e.code == 429:
                    wait = 2 ** attempt
                    time.sleep(wait)
                    if attempt == retries - 1:
                        raise RateLimitError(f"HTTP 429 rate limit exceeded on {{url}}") from e
                    continue
                if e.code >= 500 and attempt < retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                try:
                    body = e.read().decode("utf-8", errors="replace")[:1000]
                except Exception:
                    body = str(e.reason)
                raise RuntimeError(f"HTTP {{e.code}} error on {{url}}: {{body}}") from e
            except urllib_error.URLError as e:
                if attempt == retries - 1:
                    raise RuntimeError(f"Connection error to {{url}}: {{e}}") from e
                time.sleep(2 ** attempt)
        raise RuntimeError("Request failed after all retries")

    def search(self, query: str, limit: int = 10) -> dict:
        return self._request("/search", {{"q": query, "limit": limit}})

    def get_details(self, item_id: str) -> dict:
        return self._request(f"/items/{{item_id}}")


def save_output(data: dict | list, file_path: str):
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Success! Output written to: {{file_path}}")


def main():
    parser = argparse.ArgumentParser(description="{name} CLI wrapper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: search
    p_search = subparsers.add_parser("search", help="Search items")
    p_search.add_argument("--query", required=True, help="Search query")
    p_search.add_argument("--limit", type=int, required=True, help="Result limit")
    p_search.add_argument("--output", required=True, help="Output JSON path")

    # Subcommand: details
    p_details = subparsers.add_parser("details", help="Get item details")
    p_details.add_argument("--id", required=True, help="Item ID")
    p_details.add_argument("--output", required=True, help="Output JSON path")

    args = parser.parse_args()
    client = APIClient()

    try:
        if args.command == "search":
            res = client.search(args.query, args.limit)
        elif args.command == "details":
            res = client.get_details(args.id)
        else:
            sys.exit(f"Unknown command: {{args.command}}")

        save_output(res, args.output)
    except Exception as e:
        print(f"Error: {{e}}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
"""


def scaffold_skill(
    name: str,
    description: str,
    skill_type: str = "cli",
    dest_dir: Optional[str] = None,
    api_url: str = "https://api.example.com",
    rps: float = 2.0,
) -> str:
    # Normalize name
    clean_name = re.sub(r"[^a-z0-9\-]+", "-", name.lower()).strip("-")
    target_dir = os.path.abspath(dest_dir or clean_name)
    os.makedirs(target_dir, exist_ok=True)

    title = clean_name.replace("-", " ").title()
    script_name = clean_name.replace("-", "_")

    # Write SKILL.md
    if skill_type == "instructions":
        skill_md = SKILL_INSTRUCTION_TEMPLATE.format(
            name=clean_name,
            title=title,
            description=description,
        )
    else:
        skill_md = SKILL_CLI_TEMPLATE.format(
            name=clean_name,
            title=title,
            description=description,
            script_name=script_name,
        )

    with open(os.path.join(target_dir, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write(skill_md.strip() + "\n")

    # Create scripts if CLI
    if skill_type == "cli":
        scripts_dir = os.path.join(target_dir, "scripts")
        os.makedirs(scripts_dir, exist_ok=True)
        py_code = PYTHON_CLI_CODE.format(
            name=clean_name,
            script_name=script_name,
            api_url=api_url,
            rps=rps,
        )
        with open(os.path.join(scripts_dir, f"{script_name}.py"), "w", encoding="utf-8") as f:
            f.write(py_code.strip() + "\n")

    # Create tests
    tests_dir = os.path.join(target_dir, "tests")
    os.makedirs(tests_dir, exist_ok=True)
    with open(os.path.join(tests_dir, f"test_{script_name}.py"), "w", encoding="utf-8") as f:
        f.write(
            f'"""Smoke test for {clean_name}."""\n'
            f'import os\n\n'
            f'def test_skill_structure():\n'
            f'    base = os.path.dirname(os.path.dirname(__file__))\n'
            f'    assert os.path.exists(os.path.join(base, "SKILL.md"))\n'
        )

    return target_dir


def main():
    parser = argparse.ArgumentParser(description="Scaffold a new agent skill")
    parser.add_argument("--name", required=True, help="Skill name (lowercase and hyphens)")
    parser.add_argument("--description", required=True, help="Skill description (triggers and capabilities)")
    parser.add_argument("--type", choices=["cli", "instructions"], default="cli", help="Skill architecture")
    parser.add_argument("--dest", help="Destination folder (defaults to skill name)")
    parser.add_argument("--api-url", default="https://api.example.com", help="Base API URL for CLI skills")
    parser.add_argument("--rps", type=float, default=2.0, help="Rate limit in requests per second")

    args = parser.parse_args()
    path = scaffold_skill(
        name=args.name,
        description=args.description,
        skill_type=args.type,
        dest_dir=args.dest,
        api_url=args.api_url,
        rps=args.rps,
    )
    print(f"Successfully scaffolded skill '{args.name}' at: {path}")


if __name__ == "__main__":
    main()
