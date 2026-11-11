import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from scaffold import scaffold_skill
from validator import SkillValidator


def test_scaffold_cli_skill():
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = os.path.join(tmpdir, "my-cli-skill")
        scaffold_skill(
            name="my-cli-skill",
            description="A test CLI skill for querying sample resources.",
            skill_type="cli",
            dest_dir=dest,
            api_url="https://api.example.com",
            rps=2.0,
        )

        assert os.path.exists(os.path.join(dest, "SKILL.md"))
        assert os.path.exists(os.path.join(dest, "scripts", "my_cli_skill.py"))
        assert os.path.exists(os.path.join(dest, "tests", "test_my_cli_skill.py"))

        # Self-validation check
        validator = SkillValidator(dest)
        assert validator.validate() is True
        errors = [i for i in validator.issues if i.level == "ERROR"]
        assert len(errors) == 0


def test_scaffold_instruction_skill():
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = os.path.join(tmpdir, "my-protocol-skill")
        scaffold_skill(
            name="my-protocol-skill",
            description="A test instruction-only skill for orchestrating tasks.",
            skill_type="instructions",
            dest_dir=dest,
        )

        assert os.path.exists(os.path.join(dest, "SKILL.md"))
        validator = SkillValidator(dest)
        assert validator.validate() is True
