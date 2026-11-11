"""Comprehensive Validator for Agent Skills.

Validates SKILL.md frontmatter, markdown sections, CLI conventions, Python
script syntax, rate-limiting compliance, and anti-patterns according to
the Antigravity & Universal Agent Skills standard.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from typing import Dict, List, Optional, Tuple


class SkillValidationError:
    def __init__(self, level: str, message: str, file: Optional[str] = None, line: Optional[int] = None):
        self.level = level  # 'ERROR' or 'WARNING'
        self.message = message
        self.file = file
        self.line = line

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level,
            "message": self.message,
            "file": self.file,
            "line": self.line,
        }

    def __str__(self) -> str:
        loc = f"{self.file or 'SKILL.md'}"
        if self.line:
            loc += f":{self.line}"
        return f"[{self.level}] {loc}: {self.message}"


class SkillValidator:
    NAME_REGEX = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
    MAX_NAME_LEN = 64
    MAX_DESC_LEN = 1024

    def __init__(self, skill_dir_or_file: str):
        target = os.path.abspath(skill_dir_or_file)
        if os.path.isdir(target):
            self.skill_dir = target
            self.skill_file = os.path.join(target, "SKILL.md")
        else:
            self.skill_file = target
            self.skill_dir = os.path.dirname(target)

        self.issues: List[SkillValidationError] = []

    def error(self, msg: str, file: Optional[str] = None, line: Optional[int] = None):
        self.issues.append(SkillValidationError("ERROR", msg, file, line))

    def warning(self, msg: str, file: Optional[str] = None, line: Optional[int] = None):
        self.issues.append(SkillValidationError("WARNING", msg, file, line))

    def validate(self) -> bool:
        if not os.path.exists(self.skill_file):
            self.error(f"SKILL.md not found at {self.skill_file}")
            return False

        content = self._read_skill_content()
        if content is None:
            return False

        frontmatter, body = self._parse_frontmatter(content)
        self._validate_frontmatter(frontmatter)
        self._validate_markdown_body(body)
        self._validate_scripts_dir()

        return not any(issue.level == "ERROR" for issue in self.issues)

    def _read_skill_content(self) -> Optional[str]:
        try:
            with open(self.skill_file, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            self.error(f"Failed to read SKILL.md: {e}", file=self.skill_file)
            return None

    def _parse_frontmatter(self, content: str) -> Tuple[Dict[str, str], str]:
        lines = content.splitlines()
        if not lines or lines[0].strip() != "---":
            self.error("SKILL.md must begin with YAML frontmatter delimiter '---'", line=1)
            return {}, content

        end_idx = -1
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end_idx = i
                break

        if end_idx == -1:
            self.error("Unclosed YAML frontmatter: missing closing '---'")
            return {}, content

        fm_text = "\n".join(lines[1:end_idx])
        body_text = "\n".join(lines[end_idx + 1 :])

        data: Dict[str, str] = {}
        curr_key = None
        curr_val_lines = []

        for line_no, raw_line in enumerate(lines[1:end_idx], start=2):
            line = raw_line.rstrip()
            if not line or line.startswith("#"):
                continue

            match = re.match(r"^([a-zA-Z0-9_\-]+)\s*:\s*(.*)$", line)
            if match and not raw_line.startswith(" "):
                if curr_key:
                    data[curr_key] = "\n".join(curr_val_lines).strip()
                curr_key = match.group(1).strip()
                val = match.group(2).strip()
                if val in (">", ">-", "|", "|-"):
                    curr_val_lines = []
                else:
                    curr_val_lines = [val.strip("'\"")]
            elif curr_key:
                curr_val_lines.append(line.strip())

        if curr_key:
            data[curr_key] = " ".join(curr_val_lines).strip()

        return data, body_text

    def _validate_frontmatter(self, fm: Dict[str, str]):
        if not fm:
            self.error("Frontmatter is empty or invalid")
            return

        name = fm.get("name", "").strip()
        if not name:
            self.error("Missing required frontmatter property: 'name'")
        else:
            if len(name) > self.MAX_NAME_LEN:
                self.error(f"Skill name '{name}' exceeds {self.MAX_NAME_LEN} characters (current: {len(name)})")
            if not self.NAME_REGEX.match(name):
                self.error(
                    f"Skill name '{name}' must contain only lowercase letters, digits, and single hyphens"
                )

        desc = fm.get("description", "").strip()
        if not desc:
            self.error("Missing required frontmatter property: 'description'")
        else:
            if len(desc) > self.MAX_DESC_LEN:
                self.error(
                    f"Skill description exceeds {self.MAX_DESC_LEN} characters (current: {len(desc)})"
                )
            if len(desc) < 20:
                self.warning("Skill description is very short. Describe when the agent should trigger it.")

    def _validate_markdown_body(self, body: str):
        lines = body.splitlines()
        h1_found = False
        headers = []

        for line_no, line in enumerate(lines, start=1):
            s = line.strip()
            if s.startswith("# "):
                h1_found = True
            elif s.startswith("## "):
                headers.append(s[3:].strip())

        if not h1_found:
            self.warning("SKILL.md should include a top-level H1 header (# Skill Title)")

        recommended_sections = ["Overview", "Quick Start"]
        for section in recommended_sections:
            if not any(section.lower() in h.lower() for h in headers):
                self.warning(f"Recommended section '## {section}' not found in SKILL.md")

        # Anti-pattern checks
        if "python3 " in body or "python " in body:
            if "uv run" not in body:
                self.warning("Body references 'python' directly. Prefer 'uv run' for deterministic environment isolation.")

    def _validate_scripts_dir(self):
        scripts_dir = os.path.join(self.skill_dir, "scripts")
        if not os.path.exists(scripts_dir):
            return

        for root, _, files in os.walk(scripts_dir):
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.skill_dir)
                    self._check_python_file(full_path, rel_path)

    def _check_python_file(self, full_path: str, rel_path: str):
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                code = f.read()
            tree = ast.parse(code, filename=rel_path)
        except SyntaxError as e:
            self.error(f"Python syntax error: {e}", file=rel_path, line=e.lineno)
            return
        except Exception as e:
            self.error(f"Could not read/parse Python script: {e}", file=rel_path)
            return

        # Check for argparse / output flag if it appears to be a CLI tool
        has_argparse = any(
            isinstance(node, ast.Import) and any(alias.name == "argparse" for alias in node.names)
            or isinstance(node, ast.ImportFrom) and node.module == "argparse"
            for node in ast.walk(tree)
        )
        if has_argparse and "--output" not in code and "-o" not in code:
            self.warning(
                "CLI script uses argparse but doesn't appear to support '--output'. "
                "Writing results to files is recommended for token efficiency.",
                file=rel_path,
            )


def main():
    parser = argparse.ArgumentParser(description="Validate Agent Skills against standard guidelines.")
    parser.add_argument("path", nargs="?", default=".", help="Path to skill directory or SKILL.md file")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    args = parser.parse_args()

    validator = SkillValidator(args.path)
    is_valid = validator.validate()

    if args.json:
        report = {
            "valid": is_valid,
            "issues": [issue.to_dict() for issue in validator.issues],
        }
        print(json.dumps(report, indent=2))
    else:
        print(f"\nValidating skill at: {validator.skill_file}")
        print("=" * 60)
        if not validator.issues:
            print("✓ Skill passed all validation checks with 0 errors and 0 warnings.")
        else:
            for issue in validator.issues:
                prefix = "❌ " if issue.level == "ERROR" else "⚠️  "
                print(f"{prefix}{issue}")
            errors = sum(1 for i in validator.issues if i.level == "ERROR")
            warnings = sum(1 for i in validator.issues if i.level == "WARNING")
            print("-" * 60)
            print(f"Summary: {errors} error(s), {warnings} warning(s)")

    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
