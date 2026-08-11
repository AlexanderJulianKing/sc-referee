"""Executable six-role fixture for the copy-dosage pilot envelope.

Provider transport is recorded in-process.  Intake executes only the fixture
workflow commissioned here, twice, in the dedicated sklearn qualification
runtime; the production audit path remains non-executing.
"""

from __future__ import annotations

import json
import warnings
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation import lean_pipeline
from sc_referee_evaluation.lean_pipeline import (
    _probe_sandbox_runtime,
    step_authoring,
    step_detector,
    step_intake,
    step_labels,
    step_review,
)

from sc_referee.controller import replay
from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.scientific_checks.copy_dosage_adapter import (
    _accountings,
    _identified_accounting,
    _number_tokens,
)
from scripts.lean_pipeline import (
    _DOSAGE_FROZEN_PROCEDURE_BY_ROLE,
    _DOSAGE_FROZEN_WORKFLOW_BODY,
    _DOSAGE_INPUT_CSV,
    _DOSAGE_RESULT_NUMBER_BY_ROLE,
    DOSAGE_SANDBOX_PYTHON,
    ENVELOPE_CONFIGS,
    default_dosage_config,
    default_founder_orientation_f_config,
)

_ROLES = (
    "error_bearing",
    "corrected_twin",
    "valid_alternative",
    "hard_negative",
    "ambiguous",
    "unsupported",
)
_CASE_BY_ROLE = {role: f"case:{index:020x}" for index, role in enumerate(_ROLES, start=1)}
_ROLE_BY_CASE = {case_id: role for role, case_id in _CASE_BY_ROLE.items()}

if DOSAGE_SANDBOX_PYTHON.is_file():
    DOSAGE_SANDBOX_AVAILABILITY_MARKER = f"AVAILABLE:{DOSAGE_SANDBOX_PYTHON}"
else:
    DOSAGE_SANDBOX_AVAILABILITY_MARKER = (
        "PILOT BLOCKER: dedicated sklearn qualification interpreter absent at "
        f"{DOSAGE_SANDBOX_PYTHON}"
    )
    warnings.warn(DOSAGE_SANDBOX_AVAILABILITY_MARKER, stacklevel=1)


def _workflow(role: str) -> str:
    return _DOSAGE_FROZEN_WORKFLOW_BODY.replace("PROCEDURE", _DOSAGE_FROZEN_PROCEDURE_BY_ROLE[role])


def _report(role: str) -> str:
    return f"[selected-result] {_DOSAGE_RESULT_NUMBER_BY_ROLE[role]}\n"


def _authored_case(role: str) -> dict[str, Any]:
    return {
        "case_id": _CASE_BY_ROLE[role],
        "input_csv": _DOSAGE_INPUT_CSV,
        "analysis_py": _workflow(role),
        "report_md": _report(role),
        "selected_result_line": 1,
    }


def _isolated_project_root(tmp_path: Path, project_root: Path) -> Path:
    (tmp_path / "src").symlink_to(project_root / "src")
    (tmp_path / "reference").symlink_to(project_root / "reference")
    return tmp_path


def test_dosage_config_freezes_the_approved_envelope() -> None:
    config = default_dosage_config()
    assert ENVELOPE_CONFIGS["dosage"] is default_dosage_config
    assert config.envelope_id == ("classifier-derived-copy-dosage-representation-v2.0.4-lean-a")
    assert config.input_csv_row_bounds == (12, 24)
    assert config.allowed_import_roots == frozenset({"csv", "pathlib", "numpy", "sklearn"})
    assert config.required_sandbox_distributions == {}
    assert config.required_sandbox_module_distributions == {
        "numpy": ("numpy", "2.2.6"),
        "sklearn": ("scikit-learn", "1.9.0"),
    }
    assert config.controller_material_files == {}
    assert config.material_input_paths == ("inputs/data.csv",)
    assert config.record_expected_audit_snapshot_digest is True
    assert config.frozen_workflow_procedure_by_role["ambiguous"] == "plain"
    assert _workflow("ambiguous") != _workflow("corrected_twin")
    assert "plain = mean\nexposure = plain" in _workflow("ambiguous")
    assert "neutral" not in _workflow("ambiguous")
    assert "The quantities the case does not name are computed and not used." in config.common_task
    assert "%.6f" in config.author_case_requirements
    assert _DOSAGE_FROZEN_WORKFLOW_BODY in config.author_case_requirements
    assert config.authors.keys() == {
        "actor:dosage-a-author-opus-25",
        "actor:dosage-a-author-opus-26",
    }
    assert config.reviewer.participant_id == "actor:dosage-a-reviewer-fable-15"
    assert config.escalation_reviewer.participant_id == "actor:dosage-a-reviewer-opus-12"


def test_dosage_opt_ins_leave_founder_f_defaults_closed() -> None:
    config = default_founder_orientation_f_config()
    assert config.required_sandbox_module_distributions is None
    assert config.record_expected_audit_snapshot_digest is False


def test_dosage_one_number_report_has_no_hard_state_accounting() -> None:
    for role in _ROLES:
        tokens = _number_tokens(_report(role))
        integers = [item for item in tokens if item.is_integer and not item.is_percent]
        decimals = [item for item in tokens if not item.is_integer and not item.is_percent]
        accountings = _accountings(integers, decimals)
        assert accountings == [], role
        assert _identified_accounting(accountings) is None, role


@pytest.mark.skipif(not DOSAGE_SANDBOX_PYTHON.is_file(), reason=DOSAGE_SANDBOX_AVAILABILITY_MARKER)
def test_dosage_dedicated_runtime_probe_passes_for_real() -> None:
    record = _probe_sandbox_runtime(
        DOSAGE_SANDBOX_PYTHON,
        {},
        {
            "numpy": ("numpy", "2.2.6"),
            "sklearn": ("scikit-learn", "1.9.0"),
        },
    )
    assert record["required_module_distributions"] == {
        "numpy": {"distribution_name": "numpy", "required_version": "2.2.6"},
        "sklearn": {
            "distribution_name": "scikit-learn",
            "required_version": "1.9.0",
        },
    }
    assert record["observed_distributions"]["numpy"]["module_version"] == "2.2.6"
    assert record["observed_distributions"]["sklearn"]["distribution_version"] == "1.9.0"


@pytest.mark.skipif(not DOSAGE_SANDBOX_PYTHON.is_file(), reason=DOSAGE_SANDBOX_AVAILABILITY_MARKER)
def test_dosage_preflight_strings_recompute_in_pinned_runtime(tmp_path: Path) -> None:
    for role in _ROLES:
        case_root = tmp_path / role
        (case_root / "inputs").mkdir(parents=True)
        (case_root / "workflow").mkdir()
        (case_root / "results").mkdir()
        (case_root / "inputs/data.csv").write_text(_DOSAGE_INPUT_CSV, encoding="utf-8")
        (case_root / "workflow/analysis.py").write_text(_workflow(role), encoding="utf-8")
        completed = lean_pipeline.subprocess.run(
            [str(DOSAGE_SANDBOX_PYTHON), "-I", "workflow/analysis.py"],
            cwd=case_root,
            env={"NO_COLOR": "1"},
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0
        assert completed.stderr == b""
        assert (case_root / "results/report.md").read_text(encoding="utf-8") == _report(role)


@pytest.mark.skipif(not DOSAGE_SANDBOX_PYTHON.is_file(), reason=DOSAGE_SANDBOX_AVAILABILITY_MARKER)
def test_dosage_six_role_fixture_runs_real_pipeline(
    tmp_path: Path,
    project_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    isolated_root = _isolated_project_root(tmp_path, project_root)
    base = default_dosage_config()
    config = replace(
        base,
        pipeline_relative=Path("evaluation/qualification/dosage-six-role-fixture"),
        sealed_case_assignments={case_id: role for role, case_id in _CASE_BY_ROLE.items()},
    )
    monkeypatch.setattr(lean_pipeline, "ensure_calibrations", lambda _root, _config: {})

    def _recorded_author_transport(
        selected: Any,
        participant: Any,
        _prompt: str,
        _session_id: str,
        capture_root: Path,
    ) -> dict[str, Any]:
        roles = selected.author_roles[participant.participant_id]
        payload = {
            "participant_id": participant.participant_id,
            "cases": [_authored_case(role) for role in roles],
        }
        capture_root.mkdir(parents=True, exist_ok=True)
        return {
            "raw_response": canonical_json(payload),
            "transport_error": None,
            "process_record": {"capture_digest": semantic_digest(payload)},
            "started_at": "2026-08-11T12:01:00Z",
            "completed_at": "2026-08-11T12:01:01Z",
        }

    monkeypatch.setattr(lean_pipeline, "_call_cli", _recorded_author_transport)
    protocol = step_authoring(isolated_root, config)
    assert protocol["case_role_assignments"] == {
        case_id: _ROLE_BY_CASE[case_id] for case_id in sorted(_ROLE_BY_CASE)
    }

    intake = step_intake(isolated_root, config)
    assert intake["case_count"] == 6
    assert intake["ground_truth_execution"]["runs_per_case"] == 2
    assert intake["sandbox_runtime_probe"]["required_distributions"] == {}
    assert intake["sandbox_runtime_probe"]["required_module_distributions"] == {
        "numpy": {"distribution_name": "numpy", "required_version": "2.2.6"},
        "sklearn": {
            "distribution_name": "scikit-learn",
            "required_version": "1.9.0",
        },
    }
    assert all("expected_audit_snapshot_digest" in row for row in intake["entries"])
    intake_by_role = {str(row["case_role"]): row for row in intake["entries"]}

    def _recorded_review_transport(
        _project_root: Path,
        selected: Any,
        _review_root: Path,
        participant: Any,
        case_subset: list[str],
        _preparations_by_case: dict[str, dict[str, Any]],
        workspace_payloads: dict[str, dict[str, bytes]],
        _tuple_digest: str,
        label: str,
    ) -> dict[str, Any]:
        assert label == "primary"
        assert all(
            set(payloads)
            == {"task.md", "inputs/data.csv", "workflow/analysis.py", "results/report.md"}
            for payloads in workspace_payloads.values()
        )
        entries = []
        for index, case_id in enumerate(case_subset, start=1):
            role = _ROLE_BY_CASE[case_id]
            verdict = selected.expected_verdict(role)
            entries.append(
                {
                    "case_id": case_id,
                    "review_role": label,
                    "participant_id": participant.participant_id,
                    "review_id": f"review:{index:020x}",
                    "review_digest": "sha256:" + f"{index:064x}",
                    "packet_digest": "sha256:" + f"{index + 10:064x}",
                    "capture_digest": "sha256:" + f"{index + 20:064x}",
                    "verdict": verdict,
                    "issue_class": (
                        selected.canonical_issue_class if verdict == "demonstrated_issue" else None
                    ),
                    "unresolved_material_question_count": 0,
                }
            )
        return {
            "entries": entries,
            "call_identity_id": f"call:{label}",
            "prompt_digest": "sha256:" + "1" * 64,
            "output_schema_digest": "sha256:" + "2" * 64,
            "shared_transcript_digest": "sha256:" + "3" * 64,
            "packet_digests": {
                case_id: "sha256:" + f"{index + 10:064x}"
                for index, case_id in enumerate(case_subset, start=1)
            },
        }

    monkeypatch.setattr(lean_pipeline, "_run_review_call", _recorded_review_transport)
    step_review(isolated_root, config)
    step_labels(isolated_root, config)
    detector = step_detector(isolated_root, config)
    rows_by_role = {str(row["case_role"]): row for row in detector["entries"]}
    assert rows_by_role["error_bearing"]["comparison_outcome"] == "true_positive"
    assert rows_by_role["error_bearing"]["finding_candidate_count"] == 1
    for role in set(_ROLES) - {"error_bearing"}:
        assert rows_by_role[role]["comparison_outcome"] == "true_negative"
        assert rows_by_role[role]["finding_candidate_count"] == 0
    assert detector["pilot_metrics"] == {
        "opportunity_count": 6,
        "true_positive_count": 1,
        "true_negative_count": 5,
        "false_accusation_count": 0,
        "missed_error_count": 0,
        "sensitivity": 1.0,
        "false_accusation_rate": 0.0,
    }
    assert detector["production_finding_count"] == 0
    assert all(row["production_findings"] == 0 for row in rows_by_role.values())
    assert all(row["replay_equal"] is True for row in detector["entries"])
    assert all(row["project_code_executions"] == 0 for row in detector["entries"])

    replayed_by_role: dict[str, dict[str, Any]] = {}
    locks_by_role: dict[str, dict[str, Any]] = {}
    for role, case_id in _CASE_BY_ROLE.items():
        slug = case_id.removeprefix("case:")
        lock_path = (
            isolated_root
            / config.pipeline_relative
            / "detector-run/runs"
            / slug
            / "audit/semantic.lock.json"
        )
        locks_by_role[role] = json.loads(lock_path.read_bytes())
        assert (
            locks_by_role[role]["snapshot_digest"]
            == intake_by_role[role]["expected_audit_snapshot_digest"]
        )
        replayed_by_role[role] = replay(
            lock_path,
            isolated_root / "fixture-replay" / slug,
            isolated_root / "reference/schemas-v0.19.0",
        )

    detector_id = config.detector_id
    states_by_role = {
        role: [
            str(result["state"])
            for result in bundle["detector_results"]
            if result.get("detector_id") == detector_id
        ]
        for role, bundle in replayed_by_role.items()
    }
    assert states_by_role["error_bearing"] == ["evaluation_finding_candidate"]
    for role in ("corrected_twin", "valid_alternative", "hard_negative"):
        assert states_by_role[role] == ["no_issue_detected_within_coverage"]
    assert states_by_role["ambiguous"] == []
    assert states_by_role["unsupported"] == []
    ambiguous_module = next(
        item
        for item in locks_by_role["ambiguous"]["scientific_check_registry"]["evaluation"]["modules"]
        if item["check_id"] == config.check_id
    )
    assert ambiguous_module["state"] == "applicable"
    assert "ambiguous" in config.contract_free_roles
    unsupported_module = next(
        item
        for item in locks_by_role["unsupported"]["scientific_check_registry"]["evaluation"][
            "modules"
        ]
        if item["check_id"] == config.check_id
    )
    assert unsupported_module["state"] == "unsupported"
    assert [item["abstention_reason"] for item in unsupported_module["observations"]] == [
        "The workflow source uses steps or control flow beyond the supported dataflow trace, "
        "and the report arithmetic cannot stand in for it."
    ]
    assert all(not bundle["findings"] for bundle in replayed_by_role.values())
    for role, row in intake_by_role.items():
        assert row["sandbox_report_digest"] == sha256_digest(_report(role))


def test_dosage_sandbox_execution_tests_cannot_silently_skip_when_runtime_exists() -> None:
    guarded_tests = (
        test_dosage_dedicated_runtime_probe_passes_for_real,
        test_dosage_preflight_strings_recompute_in_pinned_runtime,
        test_dosage_six_role_fixture_runs_real_pipeline,
    )
    skip_conditions: list[bool] = []
    for test in guarded_tests:
        marks = [mark for mark in getattr(test, "pytestmark", ()) if mark.name == "skipif"]
        assert len(marks) == 1
        skip_conditions.append(bool(marks[0].args[0]))
    if DOSAGE_SANDBOX_PYTHON.is_file():
        assert DOSAGE_SANDBOX_AVAILABILITY_MARKER.startswith("AVAILABLE:")
        assert skip_conditions == [False, False, False]
    else:
        assert DOSAGE_SANDBOX_AVAILABILITY_MARKER.startswith("PILOT BLOCKER:")
        assert skip_conditions == [True, True, True]
