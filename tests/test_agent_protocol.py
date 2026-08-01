from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sc_referee.agent_protocol import (
    load_audit_status,
)
from sc_referee.cli import app
from sc_referee.controller import run_audit


def _write_project(root: Path) -> None:
    (root / "report.md").write_text(
        "# Results\n\nTreatment increased yield relative to control.\n",
        encoding="utf-8",
    )
    (root / "analysis.py").write_text("value = 1\n", encoding="utf-8")


def test_typed_agent_status_verifies_a_general_audit(schema_root: Path, tmp_path: Path) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    _write_project(repository)
    output = tmp_path / "audit"
    run_audit(repository, output, schema_root, report="report.md")

    status = load_audit_status(output, schema_root)

    assert status.run_state == "complete"
    assert status.terminal is True
    assert status.integrity == "verified"
    assert status.overall_status == "partial_evidence_unavailable"
    assert status.publication_surface_status == "resolved"
    assert status.assessment_counts.findings == 0
    assert status.model_calls_recorded == 0
    assert status.model_access_after_lock is False
    assert status.deadline_policy is not None
    assert status.deadline_policy.mode == "standard"
    assert status.deadline_policy.scheduling_cutoff_seconds == 480.0
    assert status.deadline_policy.hard_seconds == 600.0


def test_status_cli_emits_the_typed_json_payload(schema_root: Path, tmp_path: Path) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    _write_project(repository)
    output = tmp_path / "audit"
    run_audit(repository, output, schema_root, report="report.md")

    result = CliRunner().invoke(
        app,
        ["status", str(output), "--json", "--schema-root", str(schema_root)],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["protocol_version"] == "0.1.0"
    assert payload["integrity"] == "verified"
    assert payload["assessment_counts"]["findings"] == 0


def test_typed_agent_status_rejects_report_byte_tampering(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    _write_project(repository)
    output = tmp_path / "audit"
    run_audit(repository, output, schema_root, report="report.md")
    (output / "report.html").write_text("<html>tampered</html>", encoding="utf-8")

    with pytest.raises(ValueError, match="report bytes"):
        load_audit_status(output, schema_root)
