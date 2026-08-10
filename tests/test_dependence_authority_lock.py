"""Closed authority-seat tests for dependence pilot plumbing."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from sc_referee.controller import run_audit
from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.dependence_recognition.authority_lock import (
    AUTHORITY_LIMITATIONS,
    LOCK_KIND,
    DependenceAuthorizationLockError,
    apply_dependence_authorization_lock,
    approval_projection,
    lock_projection,
)
from sc_referee.scientific_checks.core import (
    FrozenBaseRecord,
    FrozenInspectionContext,
    FrozenMaterialInput,
    InspectionDocument,
    RecordRef,
)

_DATA = b"k1,k2,tag,a,b\nx1,y1,t1,1,2\n"
_DATA_DIGEST = sha256_digest(_DATA)


def _context() -> FrozenInspectionContext:
    surface_ref = RecordRef("publication_surface", "surface:authority-seat")
    artifact_ref = RecordRef("artifact", "artifact:selected-report")
    snapshot_ref = RecordRef("repository_snapshot", "snapshot:authority-seat")
    source_ref = RecordRef("file_record", "file:analysis-source")
    parser_ref = RecordRef("parser_result", "parser:analysis-source")
    data_ref = RecordRef("file_record", "file:authority-data")
    identity_ref = RecordRef("asset_identity", "asset:authority-data")
    parser_payload = canonical_json(
        {"parser_id": "parser:python-ast-tokenize", "parser_version": "0.15.1"}
    ).encode()
    source = b"result = scipy.stats.ttest_ind(left, right)\n"
    records = (
        FrozenBaseRecord.from_record(
            surface_ref, {"publication_surface_id": surface_ref.record_id}
        ),
        FrozenBaseRecord.from_record(
            artifact_ref,
            {"artifact_id": artifact_ref.record_id, "path": "results/report.md"},
        ),
        FrozenBaseRecord.from_record(
            snapshot_ref,
            {
                "snapshot_id": snapshot_ref.record_id,
                "extensions": {"x-material-full-digest-paths": ["inputs/data.csv"]},
            },
        ),
        FrozenBaseRecord.from_record(source_ref, {"file_record_id": source_ref.record_id}),
        FrozenBaseRecord.from_record(parser_ref, {"parser_result_id": parser_ref.record_id}),
        FrozenBaseRecord.from_record(
            data_ref,
            {
                "file_record_id": data_ref.record_id,
                "path": "inputs/data.csv",
                "entry_kind": "regular_file",
                "asset_identity_ref": identity_ref.to_dict(),
            },
        ),
        FrozenBaseRecord.from_record(
            identity_ref,
            {
                "asset_identity_id": identity_ref.record_id,
                "tier": "full_digest",
                "asset_ref": data_ref.to_dict(),
                "identity_evidence": {"kind": "full_digest", "digest": _DATA_DIGEST},
            },
        ),
    )
    return FrozenInspectionContext(
        snapshot_digest=sha256_digest(b"authority-seat-snapshot"),
        selected_surface_ref=surface_ref,
        selected_artifact_ref=artifact_ref,
        documents=(
            InspectionDocument(
                path="workflow/analysis.py",
                file_ref=source_ref,
                content=source,
                content_digest=sha256_digest(source),
                media_type="text/x-python",
                parser_result_ref=parser_ref,
                parser_result_payload=parser_payload,
                parser_result_digest=sha256_digest(parser_payload),
            ),
        ),
        base_records=records,
        material_inputs=(
            FrozenMaterialInput(
                path="inputs/data.csv",
                file_ref=data_ref,
                asset_identity_ref=identity_ref,
                content=_DATA,
                content_digest=_DATA_DIGEST,
            ),
        ),
    )


def _lock(*, case_id: str = "case:0123456789abcdefabcd") -> dict[str, Any]:
    value: dict[str, Any] = {
        "lock_kind": LOCK_KIND,
        "case_id": case_id,
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
                "input_content_digest": _DATA_DIGEST,
            },
        ],
        "approval": {
            "actor_kind": "human",
            "actor_id": "scientist:method-owner-01",
            "approved_projection_digest": "sha256:" + "0" * 64,
            "approved_at": "2026-08-10T12:00:00Z",
        },
        "authority_limitations": list(AUTHORITY_LIMITATIONS),
        "lock_digest": "sha256:" + "0" * 64,
    }
    return _seal(value)


def _seal(value: dict[str, Any]) -> dict[str, Any]:
    value["approval"]["approved_projection_digest"] = semantic_digest(approval_projection(value))
    value["lock_digest"] = semantic_digest(lock_projection(value))
    return value


def _write(path: Path, value: dict[str, Any]) -> Path:
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")
    return path


def test_valid_dependence_authority_lock_is_accepted(tmp_path: Path) -> None:
    context = _context()
    updated = apply_dependence_authorization_lock(context, _write(tmp_path / "lock.json", _lock()))
    assert len(updated.base_records) == len(context.base_records) + 4
    assert context.base_records != updated.base_records
    assert [
        item.ref.record_type
        for item in updated.base_records
        if item.ref.record_type in {"analysis", "procedure", "result", "human_method_authorization"}
    ] == ["analysis", "human_method_authorization", "procedure", "result"]


def test_tampered_input_digest_is_refused(tmp_path: Path) -> None:
    value = _lock()
    value["records"][3]["input_content_digest"] = "sha256:" + "f" * 64
    _seal(value)
    with pytest.raises(DependenceAuthorizationLockError, match="input path or digest"):
        apply_dependence_authorization_lock(_context(), _write(tmp_path / "tampered.json", value))


def test_extra_record_type_is_refused(tmp_path: Path) -> None:
    value = _lock()
    value["records"].append({"record_type": "claim", "record_id": "claim:0123456789abcdefabcd"})
    _seal(value)
    with pytest.raises(DependenceAuthorizationLockError, match="exactly four records"):
        apply_dependence_authorization_lock(_context(), _write(tmp_path / "extra.json", value))


def test_duplicate_ref_collision_is_refused(tmp_path: Path) -> None:
    context = _context()
    duplicate = FrozenBaseRecord.from_record(
        RecordRef("analysis", "analysis:0123456789abcdefabcd"),
        {"record_type": "analysis", "record_id": "analysis:0123456789abcdefabcd"},
    )
    context = replace(
        context,
        base_records=tuple(sorted((*context.base_records, duplicate), key=lambda item: item.ref)),
    )
    with pytest.raises(DependenceAuthorizationLockError, match="collides"):
        apply_dependence_authorization_lock(context, _write(tmp_path / "duplicate.json", _lock()))


def test_wrong_lock_kind_is_refused(tmp_path: Path) -> None:
    value = _lock()
    value["lock_kind"] = "generic_trusted_records_v1"
    _seal(value)
    with pytest.raises(DependenceAuthorizationLockError, match="kind"):
        apply_dependence_authorization_lock(_context(), _write(tmp_path / "wrong-kind.json", value))


def test_role_string_leakage_is_refused(tmp_path: Path) -> None:
    value = _lock(case_id="case:error_bearing_opaque_01")
    with pytest.raises(DependenceAuthorizationLockError, match="leaks a case role"):
        apply_dependence_authorization_lock(_context(), _write(tmp_path / "role-leak.json", value))


def test_unapproved_extra_field_is_refused(tmp_path: Path) -> None:
    value = _lock()
    value["records"][3]["trusted_records"] = []
    _seal(value)
    with pytest.raises(DependenceAuthorizationLockError, match="not closed"):
        apply_dependence_authorization_lock(
            _context(), _write(tmp_path / "extra-field.json", value)
        )


def test_plaintext_role_label_is_refused_even_with_replayed_digests(tmp_path: Path) -> None:
    value = _lock()
    value["records"][3]["independent_unit_definition_id"] = "unit-definition:verified_good_eligible"
    _seal(value)
    with pytest.raises(DependenceAuthorizationLockError, match="leaks a case role"):
        apply_dependence_authorization_lock(_context(), _write(tmp_path / "label-leak.json", value))


def test_run_audit_applies_authority_after_context_freeze_before_registry_evaluation(
    tmp_path: Path,
    schema_root: Path,
) -> None:
    repository = tmp_path / "repository"
    (repository / "inputs").mkdir(parents=True)
    (repository / "workflow").mkdir()
    (repository / "results").mkdir()
    data = b"k1,k2,tag,a,b\nx1,y1,t1,1,2\nx1,y1,t2,2,3\n"
    (repository / "inputs/data.csv").write_bytes(data)
    (repository / "requirements.txt").write_bytes(b"scipy==1.14.0\n")
    (repository / "workflow/analysis.py").write_text(
        """import csv
from pathlib import Path
import scipy.stats as st

rows = list(csv.DictReader(Path("inputs/data.csv").open(newline="", encoding="utf-8")))
left = [float(row["a"]) for row in rows]
right = [float(row["b"]) for row in rows]
result = st.ttest_ind(left, right)
Path("results/report.md").write_text(f"[selected-result] {result}\\n", encoding="utf-8")
""",
        encoding="utf-8",
    )
    (repository / "results/report.md").write_text(
        "[selected-result] frozen pilot result\n", encoding="utf-8"
    )
    value = _lock()
    value["records"][3]["input_content_digest"] = sha256_digest(data)
    _seal(value)
    lock_path = _write(tmp_path / "controller-authority.json", value)

    bundle = run_audit(
        repository,
        tmp_path / "audit",
        schema_root,
        report="results/report.md",
        material_inputs=("inputs/data.csv", "requirements.txt"),
        dependence_authorization_lock=lock_path,
    )

    semantic_lock = json.loads((tmp_path / "audit/semantic.lock.json").read_text(encoding="utf-8"))
    evaluation = semantic_lock["scientific_check_registry"]["evaluation"]
    module = next(
        item
        for item in evaluation["modules"]
        if item["check_id"]
        == "check:authorized-independent-unit-entry-into-row-independent-procedure"
    )
    without_lock = run_audit(
        repository,
        tmp_path / "audit-without-authority",
        schema_root,
        report="results/report.md",
        material_inputs=("inputs/data.csv", "requirements.txt"),
    )
    without_lock_semantic = json.loads(
        (tmp_path / "audit-without-authority/semantic.lock.json").read_text(encoding="utf-8")
    )
    assert (
        evaluation["context_digest"]
        != without_lock_semantic["scientific_check_registry"]["evaluation"]["context_digest"]
    )
    assert module["check_id"].startswith("check:authorized-independent-unit-entry")
    assert bundle["findings"] == []
    assert without_lock["findings"] == []
