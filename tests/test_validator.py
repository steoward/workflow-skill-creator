import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from validator import SkillValidator


def test_validator_valid_skill():
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_file = os.path.join(tmpdir, "SKILL.md")
        with open(skill_file, "w", encoding="utf-8") as f:
            f.write(
                "---\n"
                "name: my-valid-skill\n"
                "description: >-\n"
                "  A thoroughly validated test skill that performs operations.\n"
                "---\n\n"
                "# My Valid Skill\n\n"
                "## Overview\nValid overview.\n\n"
                "## Dependencies\nNone\n\n"
                "## Quick Start\n`uv run scripts/test.py`\n\n"
                "## Workflow\n1. Do something.\n\n"
                "## Common Mistakes\nNone.\n"
            )
        validator = SkillValidator(tmpdir)
        is_valid = validator.validate()
        errors = [i for i in validator.issues if i.level == "ERROR"]
        assert is_valid is True
        assert len(errors) == 0


def test_validator_invalid_name():
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_file = os.path.join(tmpdir, "SKILL.md")
        with open(skill_file, "w", encoding="utf-8") as f:
            f.write(
                "---\n"
                "name: Invalid_Name_With_Uppercase\n"
                "description: Test description\n"
                "---\n\n"
                "# Title\n"
            )
        validator = SkillValidator(tmpdir)
        is_valid = validator.validate()
        assert is_valid is False
        errors = [i for i in validator.issues if i.level == "ERROR"]
        assert any("lowercase letters" in str(e) for e in errors)


def test_validator_missing_frontmatter():
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_file = os.path.join(tmpdir, "SKILL.md")
        with open(skill_file, "w", encoding="utf-8") as f:
            f.write("# Just a title without YAML frontmatter\n")
        validator = SkillValidator(tmpdir)
        assert validator.validate() is False


def test_validator_python_syntax_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_file = os.path.join(tmpdir, "SKILL.md")
        with open(skill_file, "w", encoding="utf-8") as f:
            f.write(
                "---\n"
                "name: broken-script-skill\n"
                "description: Skill with broken script\n"
                "---\n\n"
                "# Broken Skill\n"
            )
        scripts_dir = os.path.join(tmpdir, "scripts")
        os.makedirs(scripts_dir, exist_ok=True)
        with open(os.path.join(scripts_dir, "bad.py"), "w", encoding="utf-8") as f:
            f.write("def broken_syntax(:\n")  # Syntax error

        validator = SkillValidator(tmpdir)
        assert validator.validate() is False
        errors = [i for i in validator.issues if i.level == "ERROR"]
        assert any("syntax error" in str(e).lower() for e in errors)
