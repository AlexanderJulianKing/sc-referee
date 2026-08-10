"""Closed authority-seat tests for dependence pilot plumbing."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

import sc_referee.dependence_recognition.authority_lock as authority_lock_module
from sc_referee.controller import run_audit
from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.dependence_recognition.authority_lock import (
    AUTHORITY_LIMITATIONS,
    DECLARED_EXECUTION_ROOT,
    LOCK_KIND,
    WRITER_SCOPE_EXECUTION_ROOT_MARKER,
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
from sc_referee.snapshot.repository import capture_repository

_DATA = b"k1,k2,tag,a,b\nx1,y1,t1,1,2\n"
_DATA_DIGEST = sha256_digest(_DATA)
_CASE_ID = "case:0123456789abcdefabcd"


def _context(
    *,
    snapshot_digest: str | None = None,
    data: bytes = _DATA,
) -> FrozenInspectionContext:
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
    data_digest = sha256_digest(data)
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
                "identity_evidence": {"kind": "full_digest", "digest": data_digest},
            },
        ),
    )
    return FrozenInspectionContext(
        snapshot_digest=snapshot_digest or sha256_digest(b"authority-seat-snapshot"),
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
                content=data,
                content_digest=data_digest,
            ),
        ),
    )


def _lock(
    *,
    case_id: str = _CASE_ID,
    snapshot_digest: str | None = None,
    intake_recorded_at: str | None = None,
    approved_at: str = "2026-08-10T12:00:00Z",
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "lock_kind": LOCK_KIND,
        "case_id": case_id,
        "snapshot_digest": snapshot_digest or _context().snapshot_digest,
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
                "input_content_digest": _DATA_DIGEST,
            },
        ],
        "approval": {
            "actor_kind": "human",
            "actor_id": "scientist:method-owner-01",
            "approved_projection_digest": "sha256:" + "0" * 64,
            "approved_at": approved_at,
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
    updated = apply_dependence_authorization_lock(
        context,
        _write(tmp_path / "lock.json", _lock()),
        expected_case_id=_CASE_ID,
    )
    assert len(updated.base_records) == len(context.base_records) + 4
    assert context.base_records != updated.base_records
    assert [
        item.ref.record_type
        for item in updated.base_records
        if item.ref.record_type in {"analysis", "procedure", "result", "human_method_authorization"}
    ] == ["analysis", "human_method_authorization", "procedure", "result"]


def test_unknown_declared_execution_root_is_refused(tmp_path: Path) -> None:
    value = _lock()
    value["declared_execution_root"] = "repository_root"
    _seal(value)

    with pytest.raises(DependenceAuthorizationLockError, match="execution root is invalid"):
        apply_dependence_authorization_lock(
            _context(),
            _write(tmp_path / "unknown-execution-root.json", value),
            expected_case_id=_CASE_ID,
        )


def test_tampered_input_digest_is_refused(tmp_path: Path) -> None:
    value = _lock()
    value["records"][3]["input_content_digest"] = "sha256:" + "f" * 64
    _seal(value)
    with pytest.raises(DependenceAuthorizationLockError, match="input path or digest"):
        apply_dependence_authorization_lock(
            _context(),
            _write(tmp_path / "tampered.json", value),
            expected_case_id=_CASE_ID,
        )


def test_extra_record_type_is_refused(tmp_path: Path) -> None:
    value = _lock()
    value["records"].append({"record_type": "claim", "record_id": "claim:0123456789abcdefabcd"})
    _seal(value)
    with pytest.raises(DependenceAuthorizationLockError, match="exactly four records"):
        apply_dependence_authorization_lock(
            _context(),
            _write(tmp_path / "extra.json", value),
            expected_case_id=_CASE_ID,
        )


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
        apply_dependence_authorization_lock(
            context,
            _write(tmp_path / "duplicate.json", _lock()),
            expected_case_id=_CASE_ID,
        )


def test_wrong_lock_kind_is_refused(tmp_path: Path) -> None:
    value = _lock()
    value["lock_kind"] = "generic_trusted_records_v1"
    _seal(value)
    with pytest.raises(DependenceAuthorizationLockError, match="kind"):
        apply_dependence_authorization_lock(
            _context(),
            _write(tmp_path / "wrong-kind.json", value),
            expected_case_id=_CASE_ID,
        )


def test_role_string_leakage_is_refused(tmp_path: Path) -> None:
    value = _lock(case_id="case:error_bearing_opaque_01")
    with pytest.raises(DependenceAuthorizationLockError, match="leaks a case role"):
        apply_dependence_authorization_lock(
            _context(),
            _write(tmp_path / "role-leak.json", value),
            expected_case_id="case:error_bearing_opaque_01",
        )


def test_unapproved_extra_field_is_refused(tmp_path: Path) -> None:
    value = _lock()
    value["records"][3]["trusted_records"] = []
    _seal(value)
    with pytest.raises(DependenceAuthorizationLockError, match="not closed"):
        apply_dependence_authorization_lock(
            _context(),
            _write(tmp_path / "extra-field.json", value),
            expected_case_id=_CASE_ID,
        )


def test_plaintext_role_label_is_refused_even_with_replayed_digests(tmp_path: Path) -> None:
    value = _lock()
    value["records"][3]["independent_unit_definition_id"] = "unit-definition:verified_good_eligible"
    _seal(value)
    with pytest.raises(DependenceAuthorizationLockError, match="leaks a case role"):
        apply_dependence_authorization_lock(
            _context(),
            _write(tmp_path / "label-leak.json", value),
            expected_case_id=_CASE_ID,
        )


def test_regression_p1_same_lock_refuses_a_different_frozen_snapshot(tmp_path: Path) -> None:
    first = _context()
    lock_path = _write(
        tmp_path / "snapshot-bound.json",
        _lock(snapshot_digest=first.snapshot_digest),
    )
    apply_dependence_authorization_lock(first, lock_path, expected_case_id=_CASE_ID)
    second = _context(snapshot_digest=sha256_digest(b"another-frozen-snapshot"))
    with pytest.raises(DependenceAuthorizationLockError, match="another frozen snapshot"):
        apply_dependence_authorization_lock(second, lock_path, expected_case_id=_CASE_ID)


def test_regression_p1_run_audit_requires_the_expected_case_id(
    tmp_path: Path,
    schema_root: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    lock_path = _write(tmp_path / "identity-required.json", _lock())
    with pytest.raises(ValueError, match="expected case id"):
        run_audit(
            repository,
            tmp_path / "audit",
            schema_root,
            dependence_authorization_lock=lock_path,
        )


@pytest.mark.parametrize(
    "leaked_definition",
    [
        "unit-definition:error bearing",
        "unit-definition:err\u043er_bearing",  # Cyrillic small o.
    ],
)
def test_regression_p3_whitespace_and_confusable_role_markers_are_refused(
    tmp_path: Path,
    leaked_definition: str,
) -> None:
    value = _lock()
    value["records"][3]["independent_unit_definition_id"] = leaked_definition
    _seal(value)
    with pytest.raises(DependenceAuthorizationLockError, match="leaks a case role"):
        apply_dependence_authorization_lock(
            _context(),
            _write(tmp_path / f"role-{semantic_digest(leaked_definition)}.json", value),
            expected_case_id=_CASE_ID,
        )


def test_regression_p4_unknown_authorized_key_column_is_refused(tmp_path: Path) -> None:
    value = _lock()
    value["records"][3]["authorized_key_columns"] = ["k1", "not_in_frozen_header"]
    _seal(value)
    with pytest.raises(DependenceAuthorizationLockError, match="outside the frozen CSV header"):
        apply_dependence_authorization_lock(
            _context(),
            _write(tmp_path / "unknown-column.json", value),
            expected_case_id=_CASE_ID,
        )


def test_regression_p5_json_recursion_error_is_wrapped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lock_path = _write(tmp_path / "recursive-json.json", _lock())

    def recurse(*_args: object, **_kwargs: object) -> object:
        raise RecursionError("injected JSON recursion")

    monkeypatch.setattr(authority_lock_module.json, "loads", recurse)
    with pytest.raises(DependenceAuthorizationLockError, match="not strict duplicate-free JSON"):
        authority_lock_module.verify_dependence_authorization_lock(lock_path)


@pytest.mark.parametrize("free_text_route", ["actor", "definition", "record_id", "approval"])
def test_regression_p6_free_text_and_approval_time_are_narrowed(
    tmp_path: Path,
    free_text_route: str,
) -> None:
    if free_text_route == "approval":
        value = _lock(
            intake_recorded_at="2026-08-10T13:00:00Z",
            approved_at="2026-08-10T12:59:59Z",
        )
        match = "predates the referenced intake"
    else:
        value = _lock()
        if free_text_route == "actor":
            value["records"][3]["actor_id"] = "scientist:method owner"
            value["approval"]["actor_id"] = "scientist:method owner"
            match = "actor is invalid"
        elif free_text_route == "definition":
            value["records"][3]["independent_unit_definition_id"] = "unit-definition:ordered key"
            match = "unit-definition id is invalid"
        else:
            value["records"][0]["record_id"] = "analysis:" + "a" * 121
            match = "record id is invalid"
        _seal(value)
    with pytest.raises(DependenceAuthorizationLockError, match=match):
        apply_dependence_authorization_lock(
            _context(),
            _write(tmp_path / f"free-text-{free_text_route}.json", value),
            expected_case_id=_CASE_ID,
        )


def test_regression_p7_pilot_evidence_asymmetry_is_disclosed(project_root: Path) -> None:
    text = (
        project_root / "docs/implementation/EXPERIMENT-0058-DEPENDENCE-SEMANTIC-V1-SHADOW.md"
    ).read_text(encoding="utf-8")
    normalized = " ".join(text.split())
    assert "authority presence is role-derived through `contract_free_roles`" in normalized
    assert "visible to the detector but not to the blind reviewer" in normalized


def test_regression_p2_run_audit_discloses_exact_applied_authority_lock(
    tmp_path: Path,
    schema_root: Path,
    monkeypatch: pytest.MonkeyPatch,
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
    preview = capture_repository(
        repository,
        tmp_path / "prospective-snapshot",
        "audit:prospective-authority-seat",
        preferred_full_digest_paths=("results/report.md",),
        material_full_digest_paths=("inputs/data.csv", "requirements.txt"),
    )
    value = _lock(snapshot_digest=str(preview.snapshot_record["snapshot_digest"]))
    value["records"][3]["input_content_digest"] = sha256_digest(data)
    _seal(value)
    lock_path = _write(tmp_path / "controller-authority.json", value)

    original = authority_lock_module.bind_dependence_selected_writer_scope
    proof_limitations: list[str] = []

    def observe_scope_rewrite(
        context: FrozenInspectionContext,
        *,
        declared_execution_root: str | None,
    ) -> FrozenInspectionContext:
        rewritten = original(
            context,
            declared_execution_root=declared_execution_root,
        )
        proof_limitations.extend(
            limitation
            for proof in (
                rewritten.scope_join_graph.proofs if rewritten.scope_join_graph is not None else ()
            )
            for limitation in proof.authority_limitations
        )
        return rewritten

    monkeypatch.setattr(
        authority_lock_module,
        "bind_dependence_selected_writer_scope",
        observe_scope_rewrite,
    )

    bundle = run_audit(
        repository,
        tmp_path / "audit",
        schema_root,
        report="results/report.md",
        material_inputs=("inputs/data.csv", "requirements.txt"),
        dependence_authorization_lock=lock_path,
        dependence_authorization_case_id=_CASE_ID,
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
    authority_disclosures = [
        item
        for item in bundle["disclosures"]
        if "x-dependence-authorization-lock" in item.get("extensions", {})
    ]
    assert len(authority_disclosures) == 1
    disclosure = authority_disclosures[0]
    assert disclosure["non_accusatory"] is True
    assert "severity" not in disclosure
    assert (
        "writer scope was established from the human-approved declared execution root, "
        "not from execution evidence"
    ) in disclosure["description"].casefold()
    assert disclosure["extensions"]["x-dependence-authorization-lock"] == {
        "lock_digest": value["lock_digest"],
        "approved_projection_digest": value["approval"]["approved_projection_digest"],
        "approver_actor_id": "scientist:method-owner-01",
        "record_refs": [
            {"record_type": str(item["record_type"]), "record_id": str(item["record_id"])}
            for item in value["records"]
        ],
        "snapshot_digest": preview.snapshot_record["snapshot_digest"],
        "declared_execution_root": DECLARED_EXECUTION_ROOT,
    }
    assert not [
        item
        for item in without_lock["disclosures"]
        if "x-dependence-authorization-lock" in item.get("extensions", {})
    ]
    assert WRITER_SCOPE_EXECUTION_ROOT_MARKER in proof_limitations
    assert bundle["findings"] == []
    assert without_lock["findings"] == []


def test_regression_b2_lock_without_execution_root_cannot_manufacture_writer_scope(
    tmp_path: Path,
    schema_root: Path,
    monkeypatch: pytest.MonkeyPatch,
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
    preview = capture_repository(
        repository,
        tmp_path / "prospective-snapshot",
        "audit:prospective-authority-seat",
        preferred_full_digest_paths=("results/report.md",),
        material_full_digest_paths=("inputs/data.csv", "requirements.txt"),
    )
    value = _lock(snapshot_digest=str(preview.snapshot_record["snapshot_digest"]))
    value["records"][3]["input_content_digest"] = sha256_digest(data)
    del value["declared_execution_root"]
    _seal(value)
    lock_path = _write(tmp_path / "legacy-controller-authority.json", value)

    original = authority_lock_module.bind_dependence_selected_writer_scope
    observed: dict[str, object] = {}

    def observe_scope_rewrite(
        context: FrozenInspectionContext,
        *,
        declared_execution_root: str | None,
    ) -> FrozenInspectionContext:
        rewritten = original(
            context,
            declared_execution_root=declared_execution_root,
        )
        observed["declared_execution_root"] = declared_execution_root
        observed["records_unchanged"] = rewritten.base_records == context.base_records
        observed["proof_limitations"] = tuple(
            limitation
            for proof in (
                rewritten.scope_join_graph.proofs if rewritten.scope_join_graph is not None else ()
            )
            for limitation in proof.authority_limitations
        )
        return rewritten

    monkeypatch.setattr(
        authority_lock_module,
        "bind_dependence_selected_writer_scope",
        observe_scope_rewrite,
    )
    run_audit(
        repository,
        tmp_path / "audit",
        schema_root,
        report="results/report.md",
        material_inputs=("inputs/data.csv", "requirements.txt"),
        dependence_authorization_lock=lock_path,
        dependence_authorization_case_id=_CASE_ID,
    )

    semantic_lock = json.loads((tmp_path / "audit/semantic.lock.json").read_text(encoding="utf-8"))
    evaluation = semantic_lock["scientific_check_registry"]["evaluation"]
    module = next(
        item
        for item in evaluation["modules"]
        if item["check_id"]
        == "check:authorized-independent-unit-entry-into-row-independent-procedure"
    )
    assert observed["declared_execution_root"] is None
    assert observed["records_unchanged"] is True
    assert WRITER_SCOPE_EXECUTION_ROOT_MARKER not in observed["proof_limitations"]
    assert module["state"] == "unsupported"
    assert [item["abstention_reason"] for item in module["observations"]] == [
        "selected-static-writer-scope-unavailable"
    ]
