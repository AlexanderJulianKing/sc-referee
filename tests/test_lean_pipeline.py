"""ADR-0068 lean-pipeline controls for the deterministic layers.

Model-call steps are exercised by real pilot runs; these tests lock the
fail-closed deterministic boundaries: the static workflow guard, sandboxed
ground-truth execution, intake admission, the manifest digest chain, and the
calibration-registry gate.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation import lean_pipeline
from sc_referee_evaluation.lean_pipeline import (
    DEFAULT_ALLOWED_IMPORT_ROOTS,
    DEPENDENCE_RECOGNITION_CHECK_ID,
    STEP_ORDER,
    LeanPipelineError,
    _manifest_read,
    _manifest_record,
    _manifest_require,
    _probe_sandbox_runtime,
    _sandbox_run,
    _static_guard,
    _validate_bounded_input_csv,
    ensure_calibrations,
    pipeline_step_order,
    step_authority,
    step_detector,
    step_intake,
    step_review,
)

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.dependence_recognition.authority_lock import (
    AUTHORITY_LIMITATIONS,
    DECLARED_EXECUTION_ROOT,
    LOCK_KIND,
    approval_projection,
    lock_projection,
)
from scripts.lean_pipeline import (
    default_complete_domain_config,
    default_founder_orientation_f_config,
)

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
    _static_guard(GOOD_WORKFLOW, DEFAULT_ALLOWED_IMPORT_ROOTS)
    with pytest.raises(LeanPipelineError, match="forbidden module"):
        _static_guard("import os\n", DEFAULT_ALLOWED_IMPORT_ROOTS)
    with pytest.raises(LeanPipelineError, match="forbidden module"):
        _static_guard("from subprocess import run\n", DEFAULT_ALLOWED_IMPORT_ROOTS)
    with pytest.raises(LeanPipelineError, match="forbidden builtin"):
        _static_guard("eval('1')\n", DEFAULT_ALLOWED_IMPORT_ROOTS)


def test_static_guard_uses_the_configured_import_roots() -> None:
    with pytest.raises(LeanPipelineError, match="forbidden module"):
        _static_guard("import scipy.stats\n", DEFAULT_ALLOWED_IMPORT_ROOTS)
    _static_guard("import scipy.stats\n", DEFAULT_ALLOWED_IMPORT_ROOTS | {"scipy"})


def test_sandbox_run_is_deterministic_and_bounded(tmp_path: Path) -> None:
    case_root = _write_case(tmp_path / "case")
    first = _sandbox_run(case_root, Path(sys.executable))
    second = _sandbox_run(case_root, Path(sys.executable))
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
        _sandbox_run(case_root, Path(sys.executable))


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
    report = _sandbox_run(case_root, Path(sys.executable)).decode("utf-8")
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


def test_runtime_probe_records_both_exact_scipy_versions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    interpreter = tmp_path / "pilot-python"
    interpreter.write_bytes(b"interpreter")
    observed = {
        "python_version": "3.11.15 (pilot)",
        "sys_prefix": "/private/pilot-venv",
        "distributions": {
            "scipy": {
                "distribution_version": "1.14.0",
                "module_version": "1.14.0",
                "module_path": "/private/pilot-venv/site-packages/scipy/__init__.py",
            }
        },
    }

    def _run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        del kwargs
        return subprocess.CompletedProcess(
            args[0], 0, canonical_json(observed).encode() + b"\n", b""
        )

    monkeypatch.setattr(lean_pipeline.subprocess, "run", _run)
    record = _probe_sandbox_runtime(interpreter, {"scipy": "1.14.0"})
    assert record["interpreter_path"] == interpreter.as_posix()
    assert record["interpreter_digest"] == sha256_digest(b"interpreter")
    assert record["sys_prefix"] == "/private/pilot-venv"
    assert record["observed_distributions"]["scipy"]["distribution_version"] == "1.14.0"
    assert record["observed_distributions"]["scipy"]["module_version"] == "1.14.0"
    projection = dict(record)
    assert projection.pop("probe_digest") == semantic_digest(projection)


def test_runtime_probe_refuses_a_module_distribution_version_disagreement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    interpreter = tmp_path / "pilot-python"
    interpreter.write_bytes(b"interpreter")
    observed = {
        "python_version": "3.11.15",
        "sys_prefix": "/private/pilot-venv",
        "distributions": {
            "scipy": {
                "distribution_version": "1.14.0",
                "module_version": "1.14.1",
                "module_path": "/private/pilot-venv/site-packages/scipy/__init__.py",
            }
        },
    }
    monkeypatch.setattr(
        lean_pipeline.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 0, canonical_json(observed).encode() + b"\n", b""
        ),
    )
    with pytest.raises(LeanPipelineError, match=r"exact scipy==1\.14\.0 pin"):
        _probe_sandbox_runtime(interpreter, {"scipy": "1.14.0"})


def test_runtime_probe_supports_a_closed_module_to_distribution_mapping(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    interpreter = tmp_path / "pilot-python"
    interpreter.write_bytes(b"interpreter")
    observed = {
        "python_version": "3.11.15",
        "sys_prefix": "/private/pilot-venv",
        "distributions": {
            "sklearn": {
                "distribution_name": "scikit-learn",
                "distribution_version": "1.9.0",
                "module_version": "1.9.0",
                "module_path": "/private/pilot-venv/site-packages/sklearn/__init__.py",
            }
        },
    }
    monkeypatch.setattr(
        lean_pipeline.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 0, canonical_json(observed).encode() + b"\n", b""
        ),
    )
    record = _probe_sandbox_runtime(interpreter, {}, {"sklearn": ("scikit-learn", "1.9.0")})
    assert record["required_distributions"] == {}
    assert record["required_module_distributions"] == {
        "sklearn": {
            "distribution_name": "scikit-learn",
            "required_version": "1.9.0",
        }
    }
    assert record["observed_distributions"] == observed["distributions"]
    projection = dict(record)
    assert projection.pop("probe_digest") == semantic_digest(projection)


def test_runtime_probe_refuses_combined_pin_channels(tmp_path: Path) -> None:
    interpreter = tmp_path / "pilot-python"
    interpreter.write_bytes(b"interpreter")
    with pytest.raises(LeanPipelineError, match="cannot be combined"):
        _probe_sandbox_runtime(
            interpreter,
            {"numpy": "2.2.6"},
            {"sklearn": ("scikit-learn", "1.9.0")},
        )


def test_dependence_csv_bound_is_structural_and_closed() -> None:
    config = replace(
        default_complete_domain_config(),
        check_id=DEPENDENCE_RECOGNITION_CHECK_ID,
        input_csv_row_bounds=(1, 2),
    )
    _validate_bounded_input_csv("k1,k2,tag,a,b\nx1,y1,t1,1,2\n", config)
    _validate_bounded_input_csv("k1,k2,tag,a,b\nx1,y1,t1,1,2\nx2,y2,t2,3,4\n", config)
    with pytest.raises(LeanPipelineError, match="row count"):
        _validate_bounded_input_csv(
            "k1,k2,tag,a,b\nx1,y1,t1,1,2\nx2,y2,t2,3,4\nx3,y3,t3,5,6\n",
            config,
        )
    with pytest.raises(LeanPipelineError, match="frozen envelope"):
        _validate_bounded_input_csv("unit,k2,tag,a,b\nx1,y1,t1,1,2\n", config)
    with pytest.raises(LeanPipelineError, match="empty or ragged"):
        _validate_bounded_input_csv("k1,k2,tag,a,b\nx1,y1,t1,1\n", config)


def _authority_test_lock(
    case_id: str,
    input_digest: str,
    *,
    snapshot_digest: str,
    intake_recorded_at: str,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "lock_kind": LOCK_KIND,
        "case_id": case_id,
        "snapshot_digest": snapshot_digest,
        "intake_recorded_at": intake_recorded_at,
        "declared_execution_root": DECLARED_EXECUTION_ROOT,
        "records": [
            {
                "record_type": "analysis",
                "record_id": "analysis:0123456789abcdefabcd",
                "path": "workflow/analysis.py",
            },
            {
                "record_type": "procedure",
                "record_id": "procedure:0123456789abcdefabcd",
                "resolved_callable": "scipy.stats.ttest_ind",
            },
            {
                "record_type": "result",
                "record_id": "result:0123456789abcdefabcd",
                "path": "results/report.md",
            },
            {
                "record_type": "human_method_authorization",
                "record_id": "authorization:0123456789abcdefabcd",
                "actor_id": "scientist:method-owner-01",
                "authority_state": "authorized",
                "analysis_target_ref": {
                    "record_type": "analysis",
                    "record_id": "analysis:0123456789abcdefabcd",
                },
                "procedure_ref": {
                    "record_type": "procedure",
                    "record_id": "procedure:0123456789abcdefabcd",
                },
                "independent_unit_definition_id": "unit-definition:ordered-k1-k2-source",
                "authorized_key_columns": ["k1", "k2"],
                "input_path": "inputs/data.csv",
                "input_content_digest": input_digest,
            },
        ],
        "approval": {
            "actor_kind": "human",
            "actor_id": "scientist:method-owner-01",
            "approved_projection_digest": "sha256:" + "0" * 64,
            "approved_at": intake_recorded_at,
        },
        "authority_limitations": list(AUTHORITY_LIMITATIONS),
        "lock_digest": "sha256:" + "0" * 64,
    }
    value["approval"]["approved_projection_digest"] = semantic_digest(approval_projection(value))
    value["lock_digest"] = semantic_digest(lock_projection(value))
    return value


def _record_artifact(
    project_root: Path,
    config: Any,
    step: str,
    relative: str,
    artifact: dict[str, Any],
    digest_field: str,
) -> None:
    artifact[digest_field] = semantic_digest(artifact)
    path = project_root / config.pipeline_relative / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(artifact) + "\n", encoding="utf-8")
    _manifest_record(
        project_root,
        config,
        step,
        digest=artifact[digest_field],
        relative_path=relative,
    )


def test_authority_step_freezes_before_review_and_keys_only_by_opaque_case_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = default_complete_domain_config()
    participant_id = next(iter(base.authors))
    authorized_case = "case:0123456789abcdefabcd"
    withheld_case = "case:fedcba9876543210abcd"
    config = replace(
        base,
        pipeline_relative=Path("evaluation/qualification/dependence-authority-test"),
        check_id=DEPENDENCE_RECOGNITION_CHECK_ID,
        author_roles={participant_id: ["error_bearing", "ambiguous"]},
        authors={participant_id: base.authors[participant_id]},
        candidate_by_role={"error_bearing": "candidate", "ambiguous": "candidate"},
        task_by_role={"error_bearing": "task", "ambiguous": "task"},
        role_constraints={"error_bearing": [], "ambiguous": []},
        contract_free_roles={"ambiguous"},
        expected_verdict_by_role={
            "error_bearing": "demonstrated_issue",
            "ambiguous": "no_demonstrated_issue_within_scope",
        },
        mq_tolerant_roles={"ambiguous"},
    )
    roles = {authorized_case: "error_bearing", withheld_case: "ambiguous"}
    protocol = {
        "artifact_kind": "lean_pipeline_authoring_protocol",
        "envelope_id": config.envelope_id,
        "case_role_assignments": roles,
        "detector_tuple_digest": "sha256:" + "9" * 64,
    }
    _record_artifact(
        tmp_path,
        config,
        "authoring",
        "authoring/AUTHORING_PROTOCOL.json",
        protocol,
        "protocol_digest",
    )
    entries = []
    expected_snapshot_digest = "sha256:" + "8" * 64
    intake_recorded_at = "2026-08-10T12:00:00Z"
    csv_payload = b"k1,k2,tag,a,b\nx1,y1,t1,1,2\n"
    source_payload = b"result = 1\n"
    report_payload = b"[selected-result] 1\n"
    for case_id in roles:
        case_root = (
            tmp_path / config.pipeline_relative / "authoring/cases" / case_id.removeprefix("case:")
        )
        for relative, payload in {
            "inputs/data.csv": csv_payload,
            "workflow/analysis.py": source_payload,
            "results/report.md": report_payload,
        }.items():
            path = case_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        entries.append(
            {
                "case_id": case_id,
                "expected_audit_snapshot_digest": expected_snapshot_digest,
                "file_digests": {
                    "inputs/data.csv": sha256_digest(csv_payload),
                    "workflow/analysis.py": sha256_digest(source_payload),
                    "results/report.md": sha256_digest(report_payload),
                },
            }
        )
    intake = {
        "artifact_kind": "lean_pipeline_intake_ledger",
        "envelope_id": config.envelope_id,
        "entries": entries,
        "recorded_at": intake_recorded_at,
    }
    _record_artifact(
        tmp_path,
        config,
        "intake",
        "authoring/INTAKE_LEDGER.json",
        intake,
        "ledger_digest",
    )
    incoming = (
        tmp_path
        / config.pipeline_relative
        / "authority/incoming"
        / f"{authorized_case.removeprefix('case:')}.json"
    )
    incoming.parent.mkdir(parents=True)
    incoming.write_text(
        canonical_json(
            _authority_test_lock(
                authorized_case,
                sha256_digest(csv_payload),
                snapshot_digest=expected_snapshot_digest,
                intake_recorded_at=intake_recorded_at,
            )
        )
        + "\n",
        encoding="utf-8",
    )

    assert pipeline_step_order(config) == (
        "authoring",
        "intake",
        "authority",
        "review",
        "labels",
        "detector",
    )
    ledger = step_authority(tmp_path, config)
    assert ledger["frozen_before_review"] is True
    assert [entry["case_id"] for entry in ledger["entries"]] == sorted(roles)
    assert all("case_role" not in entry for entry in ledger["entries"])
    assert ledger["authorized_count"] == 1
    assert ledger["withheld_count"] == 1
    authorized = next(entry for entry in ledger["entries"] if entry["case_id"] == authorized_case)
    assert authorized["frozen_lock_relative"].endswith(
        f"/{authorized_case.removeprefix('case:')}.json"
    )
    assert "error_bearing" not in canonical_json(ledger)
    assert "ambiguous" not in canonical_json(ledger)

    monkeypatch.setattr(lean_pipeline, "ensure_calibrations", lambda root, selected: {})

    def _review_call(
        _project_root: Path,
        selected: Any,
        _review_root: Path,
        participant: Any,
        case_subset: list[str],
        _preparations: dict[str, dict[str, Any]],
        _workspace_payloads: dict[str, dict[str, bytes]],
        _tuple_digest: str,
        label: str,
    ) -> dict[str, Any]:
        rows = []
        for index, case_id in enumerate(case_subset):
            role = roles[case_id]
            verdict = selected.expected_verdict(role)
            rows.append(
                {
                    "case_id": case_id,
                    "review_role": label,
                    "participant_id": participant.participant_id,
                    "review_id": f"review:{index:08d}",
                    "review_digest": "sha256:" + f"{index + 1:064x}",
                    "packet_digest": "sha256:" + f"{index + 11:064x}",
                    "capture_digest": "sha256:" + f"{index + 21:064x}",
                    "verdict": verdict,
                    "issue_class": (
                        selected.canonical_issue_class if verdict == "demonstrated_issue" else None
                    ),
                    "unresolved_material_question_count": 0,
                }
            )
        return {
            "entries": rows,
            "call_identity_id": f"call:{label}",
            "prompt_digest": "sha256:" + "1" * 64,
            "output_schema_digest": "sha256:" + "2" * 64,
            "shared_transcript_digest": "sha256:" + "3" * 64,
            "packet_digests": {
                case_id: "sha256:" + f"{index + 11:064x}"
                for index, case_id in enumerate(case_subset)
            },
        }

    monkeypatch.setattr(lean_pipeline, "_run_review_call", _review_call)
    review = step_review(tmp_path, config)
    review_protocol = json.loads(
        (tmp_path / config.pipeline_relative / "review/REVIEW_PROTOCOL.json").read_text(
            encoding="utf-8"
        )
    )
    assert review_protocol["authority_ledger_digest"] == ledger["ledger_digest"]
    assert review["authority_ledger_digest"] == ledger["ledger_digest"]


def test_founder_f_defaults_and_frozen_manifest_replay_are_unchanged(
    project_root: Path,
) -> None:
    config = default_founder_orientation_f_config()
    assert config.allowed_import_roots == DEFAULT_ALLOWED_IMPORT_ROOTS
    assert config.detector_id == "detector:bounded-analysis-method-conflict"
    assert config.sandbox_python is None
    assert config.required_sandbox_distributions == {}
    assert config.required_sandbox_module_distributions is None
    assert config.controller_material_files == {}
    assert config.material_input_paths == ()
    assert config.input_csv_row_bounds is None
    assert config.frozen_workflow_template is None
    assert config.frozen_workflow_procedure_by_role == {}
    assert config.record_expected_audit_snapshot_digest is False
    assert config.requires_dependence_authority is False
    assert pipeline_step_order(config) == STEP_ORDER
    manifest_path = project_root / config.pipeline_relative / "MANIFEST.json"
    assert sha256_digest(manifest_path.read_bytes()) == (
        "sha256:d10a83c57b9f6dd26a107f96caf7e12c5e646a78e8ec151a971592b46235b15f"
    )
    entry, intake = _manifest_require(project_root, config, "intake")
    assert (
        entry["digest"] == "sha256:db99422ca19a7a7532590628f79a8063aa08ffdeccfa96f8253512db9683c720"
    )
    assert intake["ledger_digest"] == entry["digest"]


def test_detector_gate_rejects_authority_digest_not_bound_by_review(tmp_path: Path) -> None:
    base = default_complete_domain_config()
    participant_id = next(iter(base.authors))
    case_id = "case:0123456789abcdefabcd"
    config = replace(
        base,
        pipeline_relative=Path("evaluation/qualification/dependence-authority-gate"),
        check_id=DEPENDENCE_RECOGNITION_CHECK_ID,
        authors={participant_id: base.authors[participant_id]},
        author_roles={participant_id: ["ambiguous"]},
        candidate_by_role={"ambiguous": "candidate"},
        task_by_role={"ambiguous": "task"},
        role_constraints={"ambiguous": []},
        contract_free_roles={"ambiguous"},
    )
    protocol = {
        "artifact_kind": "lean_pipeline_authoring_protocol",
        "envelope_id": config.envelope_id,
        "case_role_assignments": {case_id: "ambiguous"},
        "detector_tuple": {"detector_id": config.detector_id},
        "detector_tuple_digest": "sha256:" + "1" * 64,
    }
    _record_artifact(
        tmp_path,
        config,
        "authoring",
        "authoring/AUTHORING_PROTOCOL.json",
        protocol,
        "protocol_digest",
    )
    authority = {
        "artifact_kind": "lean_pipeline_dependence_authority_ledger",
        "envelope_id": config.envelope_id,
        "entries": [
            {
                "case_id": case_id,
                "authority_state": "unresolved_or_withheld",
                "frozen_lock_relative": None,
            }
        ],
    }
    _record_artifact(
        tmp_path,
        config,
        "authority",
        "authority/AUTHORITY_LEDGER.json",
        authority,
        "ledger_digest",
    )
    review = {
        "artifact_kind": "lean_pipeline_review_ledger",
        "envelope_id": config.envelope_id,
        "authority_ledger_digest": "sha256:" + "f" * 64,
    }
    _record_artifact(
        tmp_path,
        config,
        "review",
        "review/REVIEW_LEDGER.json",
        review,
        "ledger_digest",
    )
    labels = {
        "artifact_kind": "lean_pipeline_scientific_label_ledger",
        "envelope_id": config.envelope_id,
        "detector_output_observed": False,
        "entries": [],
    }
    _record_artifact(
        tmp_path,
        config,
        "labels",
        "SCIENTIFIC_LABEL_LEDGER.json",
        labels,
        "ledger_digest",
    )

    with pytest.raises(LeanPipelineError, match="differs from blind review"):
        step_detector(tmp_path, config)
