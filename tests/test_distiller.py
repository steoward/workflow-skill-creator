import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from distill import WorkflowDistiller
from validator import SkillValidator


def test_distill_from_transcript():
    transcript_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "examples", "sample_transcript.jsonl")
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = os.path.join(tmpdir, "distilled-alex-skill")
        distiller = WorkflowDistiller(output_dir=output_dir, skill_name="alex-citations")
        distiller.load_from_transcript_jsonl(transcript_path)

        assert len(distiller.user_goals) >= 2
        assert len(distiller.commands_executed) >= 1
        assert "run_command" in distiller.tools_used

        distilled_path = distiller.distill()
        assert os.path.exists(os.path.join(distilled_path, "SKILL.md"))
        assert os.path.exists(os.path.join(distilled_path, "scripts", "alex_citations_cli.py"))

        # Verify distilled skill validity
        v = SkillValidator(distilled_path)
        assert v.validate() is True
        errors = [i for i in v.issues if i.level == "ERROR"]
        assert len(errors) == 0


def test_distill_from_spec():
    spec = {
        "name": "data-sync-pipeline",
        "goals": ["Sync datasets from remote storage and format them"],
        "steps": [
            {"title": "Download Archive", "description": "Download payload from remote storage"},
            {"title": "Extract and Clean", "description": "Clean records and write summary"},
        ],
        "tools": ["curl", "tar"],
        "commands": ["tar -xzf data.tar.gz"],
        "apis": [],
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = os.path.join(tmpdir, "data-sync-pipeline")
        distiller = WorkflowDistiller(output_dir=output_dir)
        distiller.load_from_workflow_spec(spec)
        distilled_path = distiller.distill()

        assert os.path.exists(os.path.join(distilled_path, "SKILL.md"))
        v = SkillValidator(distilled_path)
        assert v.validate() is True
