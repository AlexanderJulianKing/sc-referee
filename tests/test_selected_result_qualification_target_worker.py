from __future__ import annotations

import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
import sc_referee_evaluation.selected_result_qualification_target_worker as target_worker_module
from jsonschema import Draft202012Validator
from sc_referee_evaluation.prospective_selected_result_verifier import (
    PYTHON_STATIC_MARKED_REPORT_PROFILE,
)
from sc_referee_evaluation.selected_result_qualification_target_worker import (
    TARGET_AUTHORIZATION_CASE_FIELDS,
    TARGET_AUTHORIZATION_FIELD_PROJECTION_DIGEST,
    TARGET_AUTHORIZATION_FIELDS,
    TARGET_AUTHORIZATION_IDENTITY_FIELDS,
    TARGET_AUTHORIZATION_PACKET_FIELDS,
    TARGET_AUTHORIZATION_SCHEMA_CONTENT_DIGEST,
    TARGET_AUTHORIZATION_SCHEMA_DIGEST,
    SelectedResultTargetWorkerError,
    _stable_runtime_file_record,
    load_target_authorization_schema,
    run_target_worker,
    target_authorization_field_projection,
    validate_target_authorization,
)
from sc_referee_evaluation.selected_result_qualification_target_worker import (
    main as target_worker_main,
)

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest

CASE_ID = "case:fedcba9876543210abcd"
DIGEST_A = "sha256:" + "a" * 64
REPORT = b"[selected-result] all,100\n"
SOURCE = b"domain,total\nall,100\n"
PRODUCER = (
    b"from pathlib import Path\n"
    b"table = Path('inputs/map.csv').read_text()\n"
    b"value = table.splitlines()[1]\n"
    b"report = f'[selected-result] {value}\\n'\n"
    b"Path('results/report.md').write_text(report)\n"
)


def _write_snapshot(root: Path) -> Path:
    case = root / "snapshots" / "case-01"
    (case / "results").mkdir(parents=True)
    (case / "workflow").mkdir()
    (case / "inputs").mkdir()
    (case / "results" / "report.md").write_bytes(REPORT)
    (case / "workflow" / "analysis.py").write_bytes(PRODUCER)
    (case / "inputs" / "map.csv").write_bytes(SOURCE)
    return case


def _snapshot_tree_digest() -> str:
    retained_files = [
        {
            "path": "inputs/map.csv",
            "content_digest": sha256_digest(SOURCE),
            "byte_length": len(SOURCE),
            "executable": False,
        },
        {
            "path": "results/report.md",
            "content_digest": sha256_digest(REPORT),
            "byte_length": len(REPORT),
            "executable": False,
        },
        {
            "path": "workflow/analysis.py",
            "content_digest": sha256_digest(PRODUCER),
            "byte_length": len(PRODUCER),
            "executable": False,
        },
    ]
    return semantic_digest(retained_files)


def _authorization() -> dict[str, Any]:
    value: dict[str, Any] = {
        "artifact_kind": "selected_result_verifier_target_authorization",
        "authorization_version": "1.0.0",
        "block": "pilot",
        "provider_slot": "provider-family-1",
        "assignment_digest": DIGEST_A,
        "runner_freeze_digest": "sha256:" + "b" * 64,
        "release_gate_digest": "sha256:" + "c" * 64,
        "target_identity": {
            "validator_id": "actor:isolated-target",
            "provider": "Target Provider",
            "execution_context_id": "context:isolated-target",
            "identity_evidence_digest": "sha256:" + "d" * 64,
        },
        "cases": [
            {
                "case_id": CASE_ID,
                "assignment_position": 1,
                "snapshot_path": "snapshots/case-01",
                "snapshot_tree_digest": _snapshot_tree_digest(),
                "target_packet": {
                    "case_id": CASE_ID,
                    "profile_id": PYTHON_STATIC_MARKED_REPORT_PROFILE,
                    "selected_report_path": "results/report.md",
                },
                "derived_at": "2026-08-05T02:00:00Z",
                "frozen_at": "2026-08-05T02:00:01Z",
            }
        ],
        "case_count": 1,
        "case_replacement_permitted": False,
        "qualification_authority": "none_target_release_authorization_only",
    }
    value["target_authorization_digest"] = semantic_digest(value)
    return value


def _write_authorization(path: Path, value: dict[str, Any]) -> None:
    path.write_bytes((canonical_json(value) + "\n").encode("utf-8"))


def _all_keys(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [str(key) for key in value] + [
            nested for item in value.values() for nested in _all_keys(item)
        ]
    if isinstance(value, list):
        return [nested for item in value for nested in _all_keys(item)]
    return []


def test_target_worker_runtime_import_closure_excludes_answer_side_modules(
    project_root: Path,
) -> None:
    package_root = project_root / "evaluation" / "src"
    core_root = project_root / "src"
    script = f"""
import sys
sys.path[:0] = [{str(package_root)!r}, {str(core_root)!r}]
import sc_referee_evaluation.selected_result_qualification_target_worker
forbidden = (
    'sc_referee_evaluation.selected_result_qualification_oracle',
    'sc_referee_evaluation.selected_result_verifier_qualification',
)
loaded = [name for name in forbidden if name in sys.modules]
if loaded:
    raise SystemExit(','.join(loaded))
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_target_authorization_projection_has_no_answer_bearing_fields() -> None:
    accepted = validate_target_authorization(_authorization())
    forbidden_fragments = ("oracle", "certificate", "label")

    assert not any(
        fragment in key.casefold()
        for key in _all_keys(accepted)
        for fragment in forbidden_fragments
    )


def test_target_authorization_schema_is_packaged_exact_and_replayable(
    project_root: Path,
) -> None:
    canonical_path = (
        project_root
        / "evaluation"
        / "qualification"
        / "selected-result-verifier-v1.1.0-precase"
        / "target-authorization-schema.json"
    )
    packaged_path = (
        project_root
        / "evaluation"
        / "src"
        / "sc_referee_evaluation"
        / "qualification_resources"
        / "selected_result_v1_1"
        / "target-authorization-schema.json"
    )
    canonical_payload = canonical_path.read_bytes()
    packaged_payload = packaged_path.read_bytes()
    schema = load_target_authorization_schema()

    assert canonical_payload == packaged_payload
    assert sha256_digest(packaged_payload) == TARGET_AUTHORIZATION_SCHEMA_CONTENT_DIGEST
    assert semantic_digest(schema) == TARGET_AUTHORIZATION_SCHEMA_DIGEST
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(TARGET_AUTHORIZATION_FIELDS)
    assert set(schema["properties"]) == set(TARGET_AUTHORIZATION_FIELDS)
    assert set(schema["$defs"]["targetCase"]["properties"]) == set(TARGET_AUTHORIZATION_CASE_FIELDS)
    assert set(schema["$defs"]["targetIdentity"]["properties"]) == set(
        TARGET_AUTHORIZATION_IDENTITY_FIELDS
    )
    assert set(schema["$defs"]["targetPacket"]["properties"]) == set(
        TARGET_AUTHORIZATION_PACKET_FIELDS
    )
    assert TARGET_AUTHORIZATION_FIELD_PROJECTION_DIGEST == semantic_digest(
        target_authorization_field_projection()
    )
    Draft202012Validator.check_schema(schema)
    assert list(Draft202012Validator(schema).iter_errors(_authorization())) == []


@pytest.mark.parametrize(
    ("location", "field"),
    [
        ("top", "oracle_phase_digest"),
        ("top", "construction_certificate"),
        ("top", "scientific_label"),
        ("case", "expected_state"),
        ("case", "reason_codes"),
        ("packet", "selected_result_binding"),
    ],
)
def test_target_authorization_rejects_answer_bearing_extensions(location: str, field: str) -> None:
    mutated = deepcopy(_authorization())
    mutated.pop("target_authorization_digest")
    if location == "top":
        mutated[field] = DIGEST_A
    elif location == "case":
        mutated["cases"][0][field] = "V"
    else:
        mutated["cases"][0]["target_packet"][field] = DIGEST_A
    mutated["target_authorization_digest"] = semantic_digest(mutated)

    with pytest.raises(SelectedResultTargetWorkerError, match="recursively forbidden"):
        validate_target_authorization(mutated)


@pytest.mark.parametrize("location", ["top", "identity", "case", "packet"])
def test_target_authorization_rejects_every_recursive_extra_field(location: str) -> None:
    mutated = deepcopy(_authorization())
    mutated.pop("target_authorization_digest")
    if location == "top":
        mutated["metadata"] = "not admitted"
    elif location == "identity":
        mutated["target_identity"]["metadata"] = "not admitted"
    elif location == "case":
        mutated["cases"][0]["metadata"] = "not admitted"
    else:
        mutated["cases"][0]["target_packet"]["metadata"] = "not admitted"
    mutated["target_authorization_digest"] = semantic_digest(mutated)

    schema = load_target_authorization_schema()
    assert list(Draft202012Validator(schema).iter_errors(mutated))
    with pytest.raises(SelectedResultTargetWorkerError, match="unsupported shape"):
        validate_target_authorization(mutated)


def test_target_authorization_recursively_rejects_hidden_forbidden_field_name() -> None:
    mutated = deepcopy(_authorization())
    mutated.pop("target_authorization_digest")
    mutated["target_identity"]["provider"] = {"wrapper": [{"DeepOracleAnswer": DIGEST_A}]}
    mutated["target_authorization_digest"] = semantic_digest(mutated)

    with pytest.raises(SelectedResultTargetWorkerError, match="recursively forbidden"):
        validate_target_authorization(mutated)


def test_target_worker_writes_replayable_canonical_output(tmp_path: Path) -> None:
    _write_snapshot(tmp_path)
    authorization = _authorization()
    authorization_path = tmp_path / "TARGET_AUTHORIZATION.json"
    _write_authorization(authorization_path, authorization)

    first = run_target_worker(
        authorization_path=authorization_path,
        snapshot_root=tmp_path,
        output_root=tmp_path / "output-a",
    )
    second = run_target_worker(
        authorization_path=authorization_path,
        snapshot_root=tmp_path,
        output_root=tmp_path / "output-b",
    )

    assert first == second
    assert first["record_count"] == 1
    assert first["uncontrolled_failure_count"] == 0
    assert first["project_code_executed"] is False
    for relative in (
        "TARGET_WORKER_MANIFEST.json",
        "target-records/fedcba9876543210abcd.json",
    ):
        first_payload = (tmp_path / "output-a" / relative).read_bytes()
        second_payload = (tmp_path / "output-b" / relative).read_bytes()
        assert first_payload == second_payload
        parsed = json.loads(first_payload)
        assert first_payload == (canonical_json(parsed) + "\n").encode("utf-8")


def test_target_worker_rejects_snapshot_byte_drift(tmp_path: Path) -> None:
    case = _write_snapshot(tmp_path)
    authorization_path = tmp_path / "TARGET_AUTHORIZATION.json"
    _write_authorization(authorization_path, _authorization())
    (case / "inputs" / "map.csv").write_bytes(b"domain,total\nall,101\n")

    with pytest.raises(SelectedResultTargetWorkerError, match="snapshot bytes have drifted"):
        run_target_worker(
            authorization_path=authorization_path,
            snapshot_root=tmp_path,
            output_root=tmp_path / "output",
        )


def test_runtime_manifest_mode_is_mutually_exclusive(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as raised:
        target_worker_main(
            [
                "--runtime-manifest",
                str(tmp_path / "runtime.json"),
                "--output",
                str(tmp_path / "target-output"),
            ]
        )

    assert raised.value.code == 2
    assert not (tmp_path / "runtime.json").exists()


def test_runtime_file_evidence_is_descriptor_read_and_bounded(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    runtime_file = tmp_path / "runtime.bin"
    runtime_file.write_bytes(b"abcd")
    runtime_file.chmod(0o755)

    record = _stable_runtime_file_record(runtime_file, recorded_path="runtime.bin")

    assert record == {
        "recorded_path": "runtime.bin",
        "installed_path": runtime_file.resolve().as_posix(),
        "content_digest": sha256_digest(b"abcd"),
        "byte_length": 4,
        "mode": 0o755,
        "executable": True,
    }
    link = tmp_path / "runtime-link"
    try:
        os.symlink(runtime_file, link)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    with pytest.raises(SelectedResultTargetWorkerError, match="real regular files"):
        _stable_runtime_file_record(link, recorded_path="runtime-link")

    monkeypatch.setattr(target_worker_module, "MAX_RUNTIME_FILE_BYTES", 3)
    with pytest.raises(SelectedResultTargetWorkerError, match="finite byte ceiling"):
        _stable_runtime_file_record(runtime_file, recorded_path="runtime.bin")
