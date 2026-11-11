# Workflow Skill Creator & Distiller ⚡

[![CI](https://github.com/steoward/workflow-skill-creator/actions/workflows/ci.yml/badge.svg)](https://github.com/steoward/workflow-skill-creator/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Agent Standard](https://img.shields.io/badge/Agent_Standard-Antigravity_2.0-purple.svg)](https://antigravity.google)

> **English & العربية**  
> Turn completed AI agent interactions, debug sessions, and multi-step terminal traces into robust, standardized, production-ready agent skills.  
> أداة متطورة لتحويل وتلخيص مهام وجلسات الذكاء الاصطناعي (Agent Workflows & Traces) إلى مهارات وكلاء معيارية وقابلة لإعادة الاستخدام فورياً.

---

## 🌟 Key Features / أبرز المميزات

- 🔄 **Automated Workflow Distiller (`scripts/distill.py`)**:
  Extracts intent, API calls, tool invocations, and commands from conversation transcripts (`transcript.jsonl`) or workflow specs to generate a full skill package automatically.
- 🛡️ **Cross-Process File-Lock Rate Limiting (`scripts/rate_limiter.py`)**:
  True concurrency-safe rate limiter supporting Windows (`msvcrt`) and POSIX (`fcntl`). Ensures multiple concurrent agents or subagents sharing a machine strictly respect API rate limits without HTTP 429 errors.
- ✅ **Rigorous Skill Validator (`scripts/validator.py`)**:
  Verifies YAML frontmatter, naming constraints (`a-z0-9-`), description lengths, required markdown sections, and Python AST syntax.
- ⚡ **Rapid Scaffolder (`scripts/scaffold.py`)**:
  Instantly scaffolds production-ready CLI or instruction-based skills in seconds.
- 🧩 **Battle-Tested Templates**:
  - `api_cli_template.py`: Multi-command CLI with backoff, jitter, and error-body extraction.
  - `pipeline_template.py`: File ingestion, transformation, and ETL workflows.
  - `orchestrator_template.py`: Multi-agent orchestration across existing tools.
  - `rate_limiter_module.py`: Standalone, zero-dependency copyable module.
- 🧪 **Comprehensive Test Suite**:
  13 automated unit & integration tests covering concurrent locking, backoff, AST validation, and transcript parsing.

---

## 🏛️ Architecture / بنية المشروع

```text
workflow-skill-creator/
├── .github/workflows/ci.yml   # Multi-platform CI (Ubuntu & Windows, Python 3.10-3.13)
├── scripts/
│   ├── distill.py            # Automated distillation from transcripts/specs
│   ├── validator.py          # Validates skills against agent standards
│   ├── scaffold.py           # Scaffolds new skill packages
│   └── rate_limiter.py       # Cross-platform, cross-process rate limiter
├── references/
│   ├── api_cli_template.py   # Multi-command API CLI template
│   ├── pipeline_template.py  # Data transformation pipeline template
│   ├── orchestrator_template.py # Multi-skill orchestration template
│   └── rate_limiter_module.py # Drop-in rate limiter module
├── examples/
│   ├── sample_transcript.jsonl # Sample transcript for testing
│   └── sample_skill/         # Complete distilled example skill
├── tests/
│   ├── test_distiller.py     # Distiller unit & integration tests
│   ├── test_rate_limiter.py  # Concurrency, locking & backoff tests
│   ├── test_scaffold.py      # Scaffolding tests
│   └── test_validator.py     # Validation tests
├── SKILL.md                  # Master skill specification
├── pyproject.toml            # Modern Python packaging configuration
└── LICENSE                   # Apache 2.0 License
```

---

## 🚀 Quick Start / البدء السريع

### 1. Install & Test
```bash
# Clone repository
git clone https://github.com/steoward/workflow-skill-creator.git
cd workflow-skill-creator

# Run test suite with uv
uv run --with pytest pytest -v
```

### 2. Distill a Workflow from a Transcript
Turn any recorded `transcript.jsonl` into a fully formed skill:
```bash
uv run scripts/distill.py \
  --transcript examples/sample_transcript.jsonl \
  --output-dir ./skills/my-new-skill \
  --validate
```

### 3. Validate Any Skill
Check that a skill complies with Antigravity / Claude Code / Codex agent specifications:
```bash
uv run scripts/validator.py ./skills/my-new-skill
```

### 4. Scaffold a New Skill from Scratch
```bash
uv run scripts/scaffold.py \
  --name "chembl-query" \
  --description "Queries ChEMBL database for bioactive molecules and IC50 assays." \
  --type cli \
  --dest ./skills/chembl-query \
  --rps 3.0
```

---

## 📖 The 4-Phase Distillation Process

1. **Phase 1: Brainstorming**: Interactive dialogue to determine scope, inputs/outputs, and whether code is needed.
2. **Phase 2: Skill Design**: Drafting an implementation plan with frontmatter, directory layout, and rate limits.
3. **Phase 3: Implementation**:
   - Reuse existing skills where possible.
   - Embed cross-process file-locking for external APIs.
   - Enforce file outputs (`--output`) to keep agent context windows lean and token-efficient.
4. **Phase 4: Validation**: Automated linting with `scripts/validator.py` and behavioral smoke tests.

---

## 🧪 Testing & Verification

All components have been tested under Windows and POSIX environments:

```text
tests/test_distiller.py::test_distill_from_transcript PASSED             [  7%]
tests/test_distiller.py::test_distill_from_spec PASSED                   [ 15%]
tests/test_rate_limiter.py::test_file_lock_basic PASSED                  [ 23%]
tests/test_rate_limiter.py::test_rate_limiter_interval PASSED            [ 30%]
tests/test_rate_limiter.py::test_concurrent_rate_limiting PASSED         [ 38%]
tests/test_rate_limiter.py::test_retry_with_backoff_success PASSED       [ 46%]
tests/test_rate_limiter.py::test_retry_with_backoff_exhausted PASSED     [ 53%]
tests/test_scaffold.py::test_scaffold_cli_skill PASSED                   [ 61%]
tests/test_scaffold.py::test_scaffold_instruction_skill PASSED           [ 69%]
tests/test_validator.py::test_validator_valid_skill PASSED               [ 76%]
tests/test_validator.py::test_validator_invalid_name PASSED              [ 84%]
tests/test_validator.py::test_validator_missing_frontmatter PASSED       [ 92%]
tests/test_validator.py::test_validator_python_syntax_error PASSED       [100%]

============================= 13 passed in 0.79s ==============================
```

---

## 📜 License

Distributed under the **Apache 2.0 License**. See [LICENSE](LICENSE) for details.
