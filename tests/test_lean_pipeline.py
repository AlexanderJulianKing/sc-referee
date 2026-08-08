"""ADR-0068 lean-pipeline controls for the deterministic layers.

Model-call steps are exercised by real pilot runs; these tests lock the
fail-closed deterministic boundaries: the static workflow guard, sandboxed
ground-truth execution, intake admission, the manifest digest chain, and the
calibration-registry gate.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from sc_referee_evaluation.lean_pipeline import (
    LeanPipelineError,
    _manifest_read,
    _manifest_record,
    _manifest_require,
    _sandbox_run,
    _static_guard,
    ensure_calibrations,
    step_intake,
)

from sc_referee.core.ids import semantic_digest
from scripts.lean_pipeline import default_complete_domain_config

GOOD_WORKFLOW = """import csv
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/data.csv').open()))
planned = len(rows)
retained = [row for row in rows if row['kept'] == 'yes']
removed = planned - len(retained)
events = sum(1 for row in retained if row['event'] == 'yes')
rate = events / len(retained)
report = (
    '# Plot survey\\n\\n'
    f'Planned plots: {planned}\\n'
    f'Retained after screening: {len(retained)}\\n'
    f'Removed: {removed}\\n'
    f'Plots with the event: {events}\\n\\n'
    f'[selected-result] The event rate for the complete planned set of {planned} plots '
    f'is {rate:.3f}.\\n'
)
Path('results/report.md').write_text(report, encoding='utf-8')
"""

GOOD_CSV = (
    "plot,kept,event\n"
    + "\n".join(
        f"p{i},{'yes' if i <= 8 else 'no'},{'yes' if i <= 6 else 'no'}" for i in range(1, 11)
    )
    + "\n"
)


def _write_case(root: Path, workflow: str = GOOD_WORKFLOW, csv_text: str = GOOD_CSV) -> Path:
    (root / "inputs").mkdir(parents=True)
    (root / "workflow").mkdir()
    (root / "results").mkdir()
    (root / "inputs/data.csv").write_text(csv_text, encoding="utf-8")
    (root / "workflow/analysis.py").write_text(workflow, encoding="utf-8")
    (root / "results/report.md").write_text("placeholder\n", encoding="utf-8")
    return root


def test_static_guard_rejects_forbidden_imports_and_builtins() -> None:
    _static_guard(GOOD_WORKFLOW)
    with pytest.raises(LeanPipelineError, match="forbidden module"):
        _static_guard("import os\n")
    with pytest.raises(LeanPipelineError, match="forbidden module"):
        _static_guard("from subprocess import run\n")
    with pytest.raises(LeanPipelineError, match="forbidden builtin"):
        _static_guard("eval('1')\n")


def test_sandbox_run_is_deterministic_and_bounded(tmp_path: Path) -> None:
    case_root = _write_case(tmp_path / "case")
    first = _sandbox_run(case_root)
    second = _sandbox_run(case_root)
    assert first == second
    text = first.decode("utf-8")
    assert "[selected-result]" in text
    assert "0.750" in text
    # The sandbox runs a copy; the committed placeholder report is untouched.
    assert (case_root / "results/report.md").read_text(encoding="utf-8") == "placeholder\n"


def test_sandbox_run_rejects_extra_file_writes(tmp_path: Path) -> None:
    workflow = GOOD_WORKFLOW + "Path('results/extra.txt').write_text('x', encoding='utf-8')\n"
    case_root = _write_case(tmp_path / "case", workflow=workflow)
    with pytest.raises(LeanPipelineError, match="beyond the report"):
        _sandbox_run(case_root)


def test_manifest_chain_records_and_replays(tmp_path: Path) -> None:
    config = default_complete_domain_config()
    root = tmp_path / config.pipeline_relative
    root.mkdir(parents=True)
    artifact = {"artifact_kind": "demo", "value": 1}
    artifact["ledger_digest"] = semantic_digest(artifact)
    (root / "demo.json").write_text(json.dumps(artifact), encoding="utf-8")
    _manifest_record(
        tmp_path, config, "authoring", digest=artifact["ledger_digest"], relative_path="demo.json"
    )
    entry, loaded = _manifest_require(tmp_path, config, "authoring")
    assert entry["digest"] == artifact["ledger_digest"]
    assert loaded["value"] == 1
    with pytest.raises(LeanPipelineError, match="already recorded"):
        _manifest_record(
            tmp_path, config, "authoring", digest="sha256:" + "0" * 64, relative_path="demo.json"
        )
    with pytest.raises(LeanPipelineError, match="has not completed"):
        _manifest_require(tmp_path, config, "intake")
    tampered = {"artifact_kind": "demo", "value": 2, "ledger_digest": artifact["ledger_digest"]}
    (root / "demo.json").write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(LeanPipelineError, match="does not replay"):
        _manifest_require(tmp_path, config, "authoring")
    assert _manifest_read(tmp_path, config)["envelope_id"] == config.envelope_id


def test_calibration_gate_requires_passing_registry_entries(tmp_path: Path) -> None:
    config = default_complete_domain_config()
    with pytest.raises(LeanPipelineError, match="registry does not exist"):
        ensure_calibrations(tmp_path, config)
    registry_dir = tmp_path / "evaluation/qualification"
    registry_dir.mkdir(parents=True)
    (registry_dir / "calibration-registry.json").write_text(
        json.dumps({"entries": []}), encoding="utf-8"
    )
    with pytest.raises(LeanPipelineError, match="No passing calibration entry"):
        ensure_calibrations(tmp_path, config)


def test_step_intake_admits_only_execution_verified_cases(tmp_path: Path) -> None:
    config = default_complete_domain_config()
    root = tmp_path / config.pipeline_relative
    authoring = root / "authoring"
    authoring.mkdir(parents=True)

    case_root = _write_case(tmp_path / "seed-case")
    report = _sandbox_run(case_root).decode("utf-8")
    marker_line = next(
        index + 1
        for index, line in enumerate(report.splitlines())
        if line.startswith("[selected-result]")
    )
    case_id = "case:0000000000abcdefabcd"
    participant_id = "actor:v206m-author-opus-01"
    schema_stub = {"type": "object"}
    assignment = {
        "participant": {"participant_id": participant_id},
        "case_ids": [case_id],
        "prompt": "prompt",
        "prompt_digest": "sha256:" + "1" * 64,
        "output_schema": schema_stub,
        "call_identity_id": "00000000-0000-0000-0000-000000000000",
    }
    protocol = {
        "artifact_kind": "lean_pipeline_authoring_protocol",
        "envelope_id": config.envelope_id,
        "case_role_assignments": {case_id: "error_bearing"},
        "author_assignments": [assignment],
    }
    protocol["protocol_digest"] = semantic_digest(protocol)
    (authoring / "AUTHORING_PROTOCOL.json").write_text(json.dumps(protocol), encoding="utf-8")
    _manifest_record(
        tmp_path,
        config,
        "authoring",
        digest=protocol["protocol_digest"],
        relative_path="authoring/AUTHORING_PROTOCOL.json",
    )
    response = {
        "participant_id": participant_id,
        "cases": [
            {
                "case_id": case_id,
                "input_csv": GOOD_CSV,
                "analysis_py": GOOD_WORKFLOW,
                "report_md": report,
                "selected_result_line": marker_line,
            }
        ],
    }
    attempt = {
        "participant_id": participant_id,
        "protocol_digest": protocol["protocol_digest"],
        "raw_response": json.dumps(response),
    }
    (authoring / "incoming").mkdir()
    (authoring / "incoming" / "v206m-author-opus-01.json").write_text(
        json.dumps(attempt), encoding="utf-8"
    )
    ledger = step_intake(tmp_path, config)
    assert ledger["case_count"] == 1
    entry = ledger["entries"][0]
    assert entry["deterministic"] is True
    assert entry["sandbox_runs"] == 2
    assert ledger["ground_truth_execution"]["production_audit_execution"] is False
    admitted = root / "authoring" / "cases" / case_id.removeprefix("case:")
    assert (admitted / "results/report.md").read_text(encoding="utf-8") == report


def test_step_intake_rejects_report_not_matching_execution(tmp_path: Path) -> None:
    config = default_complete_domain_config()
    root = tmp_path / config.pipeline_relative
    authoring = root / "authoring"
    authoring.mkdir(parents=True)
    case_id = "case:1111111111abcdefabcd"
    participant_id = "actor:v206m-author-opus-01"
    assignment = {
        "participant": {"participant_id": participant_id},
        "case_ids": [case_id],
        "prompt": "prompt",
        "prompt_digest": "sha256:" + "1" * 64,
        "output_schema": {"type": "object"},
        "call_identity_id": "00000000-0000-0000-0000-000000000001",
    }
    protocol = {
        "artifact_kind": "lean_pipeline_authoring_protocol",
        "envelope_id": config.envelope_id,
        "case_role_assignments": {case_id: "error_bearing"},
        "author_assignments": [assignment],
    }
    protocol["protocol_digest"] = semantic_digest(protocol)
    (authoring / "AUTHORING_PROTOCOL.json").write_text(json.dumps(protocol), encoding="utf-8")
    _manifest_record(
        tmp_path,
        config,
        "authoring",
        digest=protocol["protocol_digest"],
        relative_path="authoring/AUTHORING_PROTOCOL.json",
    )
    response = {
        "participant_id": participant_id,
        "cases": [
            {
                "case_id": case_id,
                "input_csv": GOOD_CSV,
                "analysis_py": GOOD_WORKFLOW,
                "report_md": "[selected-result] A hand-written result the script never produced.\n",
                "selected_result_line": 1,
            }
        ],
    }
    attempt = {
        "participant_id": participant_id,
        "protocol_digest": protocol["protocol_digest"],
        "raw_response": json.dumps(response),
    }
    (authoring / "incoming").mkdir()
    (authoring / "incoming" / "v206m-author-opus-01.json").write_text(
        json.dumps(attempt), encoding="utf-8"
    )
    with pytest.raises(LeanPipelineError, match="does not equal its executed output"):
        step_intake(tmp_path, config)
