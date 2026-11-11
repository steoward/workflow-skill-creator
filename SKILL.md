---
name: workflow-skill-creator
description: >-
  Distills a completed user workflow, interaction trace, or transcript into a
  reusable, standardized agent skill. Use when the user asks to turn their
  workflow into a skill, package an interaction, or when saying "make this a
  skill", "create a skill from what we just did", or "distill this workflow".
---

# Workflow Skill Creator & Distiller

Turn completed interactions and multi-step agent workflows into battle-tested,
reusable agent skills conforming to the Antigravity & Universal Agent Skills standard.

## Overview

When an agent successfully completes an exploratory task, multi-step pipeline,
or complex troubleshooting session with the user, that knowledge should not be
lost. **Workflow Skill Creator** extracts the core procedure, API endpoints,
CLI arguments, rate limits, and verification steps, packaging them into a
clean, isolated, and self-documenting agent skill.

It supports two complementary modes:
1. **Interactive Brainstorming**: A structured 4-phase design dialogue with the user.
2. **Automated Distillation Tooling**: Bundled CLI tools (`distill.py`, `validator.py`, `scaffold.py`) to parse transcripts and scaffold skills automatically.

---

## Bundled CLI Tools

All tools run with `uv run` and require standard Python 3.10+ without external packages:

### 1. Automated Workflow Distiller (`scripts/distill.py`)
Parses conversation transcripts (`transcript.jsonl`) or workflow specs to synthesize a complete skill:
```bash
# Distill from conversation transcript
uv run scripts/distill.py --transcript path/to/transcript.jsonl --output-dir ./my-skill --validate

# Distill from structured spec
uv run scripts/distill.py --spec workflow_spec.json --output-dir ./my-skill --validate
```

### 2. Comprehensive Skill Validator (`scripts/validator.py`)
Validates frontmatter YAML rules, character limits, section structures, and Python script syntax:
```bash
# Validate current directory
uv run scripts/validator.py .

# Output JSON report
uv run scripts/validator.py ./my-skill --json
```

### 3. Rapid Skill Scaffolder (`scripts/scaffold.py`)
Scaffolds a new compliant skill skeleton in seconds:
```bash
uv run scripts/scaffold.py --name "ncbi-query-tool" \
  --description "Fetches and analyzes gene sequences from NCBI E-Utilities." \
  --type cli --dest ./skills/ncbi-query-tool --rps 3.0
```

---

## 4-Phase Interactive Workflow

When working interactively with the user to distill a workflow:

### Phase 1: Brainstorming (Mandatory)
Do NOT jump directly into writing files. Ask 2-3 focused questions at a time:
- **Round 1 (Scope & Purpose)**: Summarize observed actions. Clarify inputs, outputs, and trigger conditions.
- **Round 2 (Strict vs. Flexible)**: Which steps are deterministic? How should errors / missing data be handled?
- **Round 3 (Dependencies & Overlaps)**: Does an existing installed skill cover part of the pipeline? If so, reference it rather than re-implementing.
- **Round 4 (CLI vs. Instruction Pattern)**: If any step calls APIs, processes files, or computes data, generate a CLI helper script. If purely conceptual/orchestration, use an instruction-only skill.
- **Round 5 (Rate Limits & Credentials)**: Identify API rate limits and secret handling.

### Phase 2: Design Document
Draft an implementation plan (or markdown artifact) containing:
1. **Skill Name**: Lowercase letters, digits, single hyphens (max 64 chars).
2. **Trigger Description**: Explicit conditions explaining when the agent must activate it.
3. **Directory Structure**:
   ```
   my-skill/
   ├── SKILL.md
   ├── scripts/
   │   └── my_skill_cli.py
   ├── references/
   └── tests/
   ```
4. **Rate Limiting & Error Handling Strategy**.

*Seek user approval before writing code.*

### Phase 3: Implementation Rules

- **Rule 1 (Reuse Existing Skills)**: Reference pre-installed skills in a `## Dependencies` section.
- **Rule 2 (True Cross-Process Rate Limiting)**: For external APIs, use the provided `scripts/rate_limiter.py` or `references/rate_limiter_module.py`. It uses cross-platform file locking (`msvcrt` on Windows, `fcntl` on POSIX) so parallel agents sharing the machine collectively respect limits.
- **Rule 3 (Default to File Output)**: All scripts must accept `--output` to write results to disk. Stdout should only receive compact progress notes. Never stream huge payloads into terminal stdout.
- **Rule 4 (No Silent Defaults on Limits)**: Arguments like `--limit` must be required to avoid silent truncation assumptions.
- **Rule 5 (Execution Isolation)**: Always recommend `uv run scripts/<tool>.py` rather than generic `python`.

### Phase 4: Validation & Testing
1. Run `uv run scripts/validator.py <skill_directory>` to verify schema compliance.
2. Run test execution on a sample input:
   ```bash
   uv run <skill_script>.py <subcommand> --output test_out.json
   ```
3. Verify output contents and inspect exit codes.

---

## Standard SKILL.md Structure

Every distilled skill's `SKILL.md` must adhere to this template:

```markdown
---
name: {skill-name}
description: >-
  {Specific, action-oriented description of what the skill does and when to use it.}
---

# {Skill Title}

## Overview
{High-level explanation of the workflow and its capabilities.}

## Dependencies
{List of required runtimes, existing skills, or environment variables.}

## Quick Start
{Copy-pasteable one-line command to get started immediately.}

## Utility Scripts (if CLI-based)
{Detailed breakdown of each subcommand with example arguments and outputs.}

## Workflow (if instruction-only)
{Sequential numbered steps guiding agent execution.}

## Rate Limiting & Concurrency
{Documented requests per second, headers, and concurrency handling.}

## Common Mistakes
{2-3 common agent anti-patterns to avoid.}
```

---

## Reference Templates Included

- `references/api_cli_template.py`: Multi-command API client with retry and file locking.
- `references/pipeline_template.py`: Data transformation and ETL pipeline.
- `references/orchestrator_template.py`: Multi-agent / multi-skill coordination.
- `references/rate_limiter_module.py`: Standalone cross-process file-locking rate limiter.
