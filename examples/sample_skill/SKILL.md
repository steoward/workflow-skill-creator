---
name: fetch-data-from-https
description: >-
  Automates workflow for: Fetch data from https://api.openalex.org/works and summarize the top citations. Use when asked to execute this pipeline.
---

# Fetch Data From Https

## Overview
Automates workflow for: Fetch data from https://api.openalex.org/works and summarize the top citations. Use when asked to execute this pipeline.

## Dependencies
- Python 3.10+ and `uv run`

## Quick Start
```bash
uv run scripts/fetch_data_from_https_cli.py run --input-file data.json --output results.json
```

## Utility Scripts
The primary helper script is located at `scripts/fetch_data_from_https_cli.py`.

- **run**: Executes the automated pipeline.
  `uv run scripts/fetch_data_from_https_cli.py run --input-file <path> --output <output_path>`

- **status**: Checks health / prerequisites.
  `uv run scripts/fetch_data_from_https_cli.py status --output <output_path>`

All subcommands accept `--output` to redirect structured results directly to a file,
preventing stdout buffer truncation and minimizing context token consumption.

## Rate Limiting & Concurrency
Built-in cross-process rate limiting with file locking prevents rate limit violations
when multiple subagents run in parallel.

## Common Mistakes
1. Printing large payloads directly to stdout instead of using `--output`.
2. Calling commands without verifying prerequisite input files.
