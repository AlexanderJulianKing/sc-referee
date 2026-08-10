"""Closed, dependence-specific authorization-lock validation.

This module deliberately does not expose a generic trusted-record injection
surface.  It accepts one exact four-record dependence authorization bundle,
binds it to already frozen source, report, and material-input identities, and
returns a dataclass-replaced inspection context.
"""

from __future__ import annotations

import ast
import csv
import io
import json
import re
import unicodedata
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest, stable_id
from sc_referee.records.observed import controller_provenance
from sc_referee.scientific_checks.core import (
    FrozenBaseRecord,
    FrozenInspectionContext,
    InspectionDocument,
    RecordRef,
    ScopeJoinEdge,
    ScopeJoinProof,
    StaticScopeJoinGraph,
)
from sc_referee.scientific_checks.scope_joins import (
    STATIC_WRITER_OUTPUT_PROFILE,
    STATIC_WRITER_SOURCE_PROFILE,
    selected_static_writer_path,
)

LOCK_KIND = "dependence_method_authorization_v1"
AUTHORITY_LIMITATIONS = (
    "Authorization is limited to this case, input digest, procedure and ordered key.",
    "It establishes no execution, numerical impact or general scientific correctness.",
)
_ROOT_KEYS = frozenset(
    {
        "lock_kind",
        "case_id",
        "snapshot_digest",
        "intake_recorded_at",
        "records",
        "approval",
        "authority_limitations",
        "lock_digest",
    }
)
_RECORD_TYPES = (
    "analysis",
    "procedure",
    "result",
    "human_method_authorization",
)
_RECORD_ID_PREFIX = {
    "analysis": "analysis:",
    "procedure": "procedure:",
    "result": "result:",
    "human_method_authorization": "authorization:",
}
_PROCEDURES = frozenset(
    {
        "scipy.stats.ttest_ind",
        "scipy.stats.mannwhitneyu",
        "scipy.stats.ttest_rel",
    }
)
_DEFAULT_ROLE_MARKERS = frozenset(
    {
        "error_bearing",
        "corrected_twin",
        "valid_alternative",
        "hard_negative",
        "ambiguous",
        "unsupported",
        "positive_demonstrated",
        "verified_good_eligible",
        "ambiguous_control",
        "unsupported_control",
    }
)
_CASE_ID_RE = re.compile(r"case:[A-Za-z0-9][A-Za-z0-9._-]{7,127}\Z")
_RECORD_ID_RE = re.compile(r"[a-z][a-z0-9_-]*:[A-Za-z0-9][A-Za-z0-9._-]{7,127}\Z")
_SHA256_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")
_MAX_JSON_DEPTH = 32
_MAX_FREE_TEXT_LENGTH = 128
_CONFUSABLE_TO_LATIN = str.maketrans(
    {
        # Common Cyrillic lookalikes.
        "\u0430": "a",
        "\u0435": "e",
        "\u043e": "o",
        "\u0440": "p",
        "\u0441": "c",
        "\u0445": "x",
        "\u0443": "y",
        "\u0456": "i",
        "\u0458": "j",
        "\u0410": "A",
        "\u0412": "B",
        "\u0415": "E",
        "\u041a": "K",
        "\u041c": "M",
        "\u041d": "H",
        "\u041e": "O",
        "\u0420": "P",
        "\u0421": "C",
        "\u0422": "T",
        "\u0425": "X",
        # Common Greek lookalikes.
        "\u03b1": "a",
        "\u03b2": "b",
        "\u03b5": "e",
        "\u03b9": "i",
        "\u03ba": "k",
        "\u03bf": "o",
        "\u03c1": "p",
        "\u03c4": "t",
        "\u03c5": "y",
        "\u03c7": "x",
        "\u0391": "A",
        "\u0392": "B",
        "\u0395": "E",
        "\u0396": "Z",
        "\u0397": "H",
        "\u0399": "I",
        "\u039a": "K",
        "\u039c": "M",
        "\u039d": "N",
        "\u039f": "O",
        "\u03a1": "P",
        "\u03a4": "T",
        "\u03a5": "Y",
        "\u03a7": "X",
    }
)


class DependenceAuthorizationLockError(ValueError):
    """Raised when a private dependence authority lock fails closed."""


@dataclass(frozen=True)
class VerifiedDependenceAuthorizationLock:
    """One closed lock after schema, digest, and case-binding verification."""

    case_id: str
    snapshot_digest: str
    records: tuple[dict[str, Any], ...]
    record_refs: tuple[RecordRef, ...]
    approver_actor_id: str
    approved_projection_digest: str
    lock_digest: str
    canonical_payload: bytes


def approval_projection(lock: Mapping[str, Any]) -> dict[str, Any]:
    """Return the exact projection a human approves before review."""

    return {
        "lock_kind": lock.get("lock_kind"),
        "case_id": lock.get("case_id"),
        "snapshot_digest": lock.get("snapshot_digest"),
        "intake_recorded_at": lock.get("intake_recorded_at"),
        "records": lock.get("records"),
        "authority_limitations": lock.get("authority_limitations"),
    }


def lock_projection(lock: Mapping[str, Any]) -> dict[str, Any]:
    """Return the exact lock-digest projection (everything except its digest)."""

    return {key: value for key, value in lock.items() if key != "lock_digest"}


def verify_dependence_authorization_lock(
    lock_path: Path,
    *,
    expected_case_id: str | None = None,
    expected_snapshot_digest: str | None = None,
    expected_intake_recorded_at: str | None = None,
    source_paths: Iterable[str] | None = None,
    selected_report_path: str | None = None,
    material_input_digests: Mapping[str, str] | None = None,
    forbidden_role_markers: Iterable[str] = (),
) -> VerifiedDependenceAuthorizationLock:
    """Parse and verify one exact private dependence authorization lock.

    The optional bindings are controller facts, not caller-supplied record
    extensions.  When present they narrow the accepted source, selected report,
    material input, case id, and role-blindness envelope.
    """

    try:
        payload = lock_path.read_bytes()
    except OSError as error:
        raise DependenceAuthorizationLockError("dependence authority lock is unreadable") from error
    if not payload or len(payload) > 64 * 1024:
        raise DependenceAuthorizationLockError("dependence authority lock size is invalid")
    try:
        text = payload.decode("utf-8", errors="strict")
        if not _json_depth_within_bound(text):
            raise DependenceAuthorizationLockError(
                "dependence authority lock exceeds the JSON depth bound"
            )
        value = json.loads(text, object_pairs_hook=_closed_object)
    except DependenceAuthorizationLockError:
        raise
    except Exception as error:
        raise DependenceAuthorizationLockError(
            "dependence authority lock is not strict duplicate-free JSON"
        ) from error
    if not isinstance(value, dict) or set(value) != _ROOT_KEYS:
        raise DependenceAuthorizationLockError("dependence authority lock root is not closed")
    if value.get("lock_kind") != LOCK_KIND:
        raise DependenceAuthorizationLockError("dependence authority lock kind is invalid")

    case_id = value.get("case_id")
    if not isinstance(case_id, str) or _CASE_ID_RE.fullmatch(case_id) is None:
        raise DependenceAuthorizationLockError("dependence authority case id is not opaque")
    if expected_case_id is not None and case_id != expected_case_id:
        raise DependenceAuthorizationLockError("dependence authority lock names another case")
    snapshot_digest = value.get("snapshot_digest")
    if not isinstance(snapshot_digest, str) or _SHA256_RE.fullmatch(snapshot_digest) is None:
        raise DependenceAuthorizationLockError("dependence authority snapshot digest is invalid")
    if expected_snapshot_digest is not None and snapshot_digest != expected_snapshot_digest:
        raise DependenceAuthorizationLockError(
            "dependence authority lock names another frozen snapshot"
        )
    intake_recorded_at = _optional_timestamp(value.get("intake_recorded_at"), "intake time")
    if (
        expected_intake_recorded_at is not None
        and value.get("intake_recorded_at") != expected_intake_recorded_at
    ):
        raise DependenceAuthorizationLockError(
            "dependence authority lock names another intake time"
        )

    markers = _normalized_markers((*_DEFAULT_ROLE_MARKERS, *forbidden_role_markers))
    if _contains_marker(value, markers):
        raise DependenceAuthorizationLockError("dependence authority lock leaks a case role")

    records = value.get("records")
    if not isinstance(records, list) or len(records) != len(_RECORD_TYPES):
        raise DependenceAuthorizationLockError(
            "dependence authority lock requires exactly four records"
        )
    if [item.get("record_type") if isinstance(item, dict) else None for item in records] != list(
        _RECORD_TYPES
    ):
        raise DependenceAuthorizationLockError(
            "dependence authority lock record types or order are invalid"
        )
    analysis, procedure, result, authorization = records
    _verify_analysis_record(analysis, source_paths)
    _verify_procedure_record(procedure)
    _verify_result_record(result, selected_report_path)
    _verify_authorization_record(
        authorization,
        analysis=analysis,
        procedure=procedure,
        material_input_digests=material_input_digests,
    )

    refs = [(str(item["record_type"]), str(item["record_id"])) for item in records]
    if len(refs) != len(set(refs)):
        raise DependenceAuthorizationLockError("dependence authority lock repeats a record ref")

    limitations = value.get("authority_limitations")
    if limitations != list(AUTHORITY_LIMITATIONS):
        raise DependenceAuthorizationLockError(
            "dependence authority limitations are not the closed v1 text"
        )
    approval = _verify_approval(
        value.get("approval"), authorization, intake_recorded_at=intake_recorded_at
    )
    expected_approval_digest = semantic_digest(approval_projection(value))
    if approval["approved_projection_digest"] != expected_approval_digest:
        raise DependenceAuthorizationLockError(
            "dependence authority approved projection digest does not replay"
        )
    expected_lock_digest = semantic_digest(lock_projection(value))
    if value.get("lock_digest") != expected_lock_digest:
        raise DependenceAuthorizationLockError("dependence authority lock digest does not replay")

    return VerifiedDependenceAuthorizationLock(
        case_id=case_id,
        snapshot_digest=snapshot_digest,
        records=tuple(dict(item) for item in records),
        record_refs=tuple(RecordRef(record_type, record_id) for record_type, record_id in refs),
        approver_actor_id=str(approval["actor_id"]),
        approved_projection_digest=expected_approval_digest,
        lock_digest=expected_lock_digest,
        canonical_payload=(canonical_json(value) + "\n").encode("utf-8"),
    )


def apply_dependence_authorization_lock(
    context: FrozenInspectionContext,
    lock_path: Path,
    *,
    expected_case_id: str,
) -> FrozenInspectionContext:
    """Validate and append the closed four-record bundle to a frozen context."""

    updated, _verified = apply_dependence_authorization_lock_with_receipt(
        context, lock_path, expected_case_id=expected_case_id
    )
    return updated


def apply_dependence_authorization_lock_with_receipt(
    context: FrozenInspectionContext,
    lock_path: Path,
    *,
    expected_case_id: str,
) -> tuple[FrozenInspectionContext, VerifiedDependenceAuthorizationLock]:
    """Apply one lock and retain its exact verified disclosure projection."""

    selected_report_path = _selected_report_path(context)
    if selected_report_path is None:
        raise DependenceAuthorizationLockError(
            "dependence authority lock lacks one selected report binding"
        )
    if any(
        not reverify_material_digest(item.content, item.content_digest)
        for item in context.material_inputs
    ):
        raise DependenceAuthorizationLockError(
            "dependence authority material bytes do not replay their frozen digest"
        )
    verified = verify_dependence_authorization_lock(
        lock_path,
        expected_case_id=expected_case_id,
        expected_snapshot_digest=context.snapshot_digest,
        source_paths=(item.path for item in context.documents),
        selected_report_path=selected_report_path,
        material_input_digests={item.path: item.content_digest for item in context.material_inputs},
    )
    _verify_frozen_authorized_columns(context, verified)

    additions: list[FrozenBaseRecord] = []
    existing_refs = {item.ref for item in context.base_records}
    for record in verified.records:
        ref = RecordRef(str(record["record_type"]), str(record["record_id"]))
        if ref in existing_refs or any(item.ref == ref for item in additions):
            raise DependenceAuthorizationLockError(
                "dependence authority record ref collides with the frozen base view"
            )
        additions.append(FrozenBaseRecord.from_record(ref, record))
    updated = replace(
        context,
        base_records=tuple(sorted((*context.base_records, *additions), key=lambda item: item.ref)),
    )
    return updated, verified


def dependence_authorization_disclosure(
    verified: VerifiedDependenceAuthorizationLock,
    *,
    run_id: str,
    created_at: str,
    affected_ref: RecordRef,
) -> dict[str, Any]:
    """Describe the exact bounded authority injection without an accusation."""

    return {
        "schema_version": "0.18.0",
        "record_type": "disclosure",
        "disclosure_id": stable_id(
            "disclosure-dependence-authority-lock", run_id, verified.lock_digest
        ),
        "audit_run_id": run_id,
        "disclosure_kind": "other",
        "title": "A bounded human dependence-authorization lock was applied",
        "description": (
            "The controller applied one digest-sealed four-record human authorization "
            "bundle before question-only static scientific-check evaluation."
        ),
        "importance": "informational",
        "non_accusatory": True,
        "affected_refs": [affected_ref.to_dict()],
        "source_refs": [],
        "coverage_status": "covered",
        "interpretive_consequence": (
            "The lock supplies only its stated case-, snapshot-, input-, procedure-, and "
            "ordered-key authority; it establishes no execution, correctness, numerical "
            "impact, or production Finding eligibility."
        ),
        "created_at": created_at,
        "provenance": controller_provenance(
            "deterministic_dependence_authority_lock_disclosure_v1", created_at
        ),
        "extensions": {
            "x-dependence-authorization-lock": {
                "lock_digest": verified.lock_digest,
                "approved_projection_digest": verified.approved_projection_digest,
                "approver_actor_id": verified.approver_actor_id,
                "record_refs": [item.to_dict() for item in verified.record_refs],
                "snapshot_digest": verified.snapshot_digest,
            }
        },
    }


def bind_dependence_selected_writer_scope(
    context: FrozenInspectionContext,
) -> FrozenInspectionContext:
    """Add only the closed pilot writer proof for an exact authorized sink.

    The general Python inventory conservatively resolves relative ``Path``
    literals beside their source file.  Pilot workflows are commissioned and
    intake-executed from the case root, but that execution evidence is not
    imported into production audit.  This helper therefore proves only the
    static declaration: one trusted analysis record, one trusted result
    record, and one parsed module-level ``Path(<selected report>).write_*``
    call with an exact literal.  It establishes neither execution nor byte
    production, and any ambiguity leaves the original graph unchanged.
    """

    graph = context.scope_join_graph
    if graph is None:
        return context
    python_documents = tuple(
        item for item in context.documents if item.media_type == "text/x-python"
    )
    analyses = _records_of_type(context, "analysis")
    results = _records_of_type(context, "result")
    if len(python_documents) != 1 or len(analyses) != 1 or len(results) != 1:
        return context
    analysis_ref, analysis = analyses[0]
    result_ref, result = results[0]
    analysis_path = analysis.get("path")
    result_path = result.get("path")
    if not isinstance(analysis_path, str) or not isinstance(result_path, str):
        return context
    document = python_documents[0]
    if document.path != analysis_path or document.parser_result_ref is None:
        return context
    if result_ref not in {item.ref for item in context.base_records}:
        return context
    selected = _base_record_value(context, context.selected_artifact_ref)
    if not isinstance(selected, dict) or selected.get("path") != result_path:
        return context
    if selected_static_writer_path(
        graph,
        document=document,
        selected_artifact_ref=context.selected_artifact_ref,
        selected_surface_ref=context.selected_surface_ref,
    ):
        return context

    call = _one_direct_selected_writer(document, result_path)
    if call is None:
        return context
    writer_matches: list[tuple[RecordRef, dict[str, Any]]] = []
    for record in context.base_records:
        if record.ref.record_type != "operation":
            continue
        value = _record_payload(record)
        if not isinstance(value, dict) or not _operation_matches_writer(
            value, document=document, call=call
        ):
            continue
        writer_matches.append((record.ref, value))
    if len(writer_matches) != 1:
        return context
    writer_ref, writer = writer_matches[0]
    output_values = writer.get("output_refs")
    if not isinstance(output_values, list) or len(output_values) != 1:
        return context
    parsed_output_ref = _closed_record_ref(output_values[0], "artifact")
    if parsed_output_ref is None or parsed_output_ref == context.selected_artifact_ref:
        return context
    parsed_output = _base_record_value(context, parsed_output_ref)
    if not isinstance(parsed_output, dict):
        return context
    expected_parser_path = (
        PurePosixPath(document.path).parent / PurePosixPath(result_path)
    ).as_posix()
    writer_ref_value = writer_ref.to_dict()
    if (
        parsed_output.get("path") != expected_parser_path
        or parsed_output.get("kind") != "result_file"
        or parsed_output.get("observed_role") != "output_file"
        or parsed_output.get("producer_operation_refs") != [writer_ref_value]
        or selected.get("kind") != "report"
        or selected.get("observed_role") != "publication_surface_candidate"
        or selected.get("producer_operation_refs") != []
    ):
        return context

    # Resolve only this lock-authorized direct declaration from the parser's
    # conservative source-directory-relative artifact to the selected report.
    # The displaced parser artifact remains frozen but no longer claims the
    # operation as its producer, keeping the relation internally one-to-one.
    updated_writer = {**writer, "output_refs": [context.selected_artifact_ref.to_dict()]}
    updated_selected = {**selected, "producer_operation_refs": [writer_ref_value]}
    updated_parser_output = {**parsed_output, "producer_operation_refs": []}
    updated_payloads = {
        writer_ref: updated_writer,
        context.selected_artifact_ref: updated_selected,
        parsed_output_ref: updated_parser_output,
    }
    updated_base_records = tuple(
        FrozenBaseRecord.from_record(item.ref, updated_payloads[item.ref])
        if item.ref in updated_payloads
        else item
        for item in context.base_records
    )
    evidence_refs = (
        document.file_ref,
        document.parser_result_ref,
        analysis_ref,
        result_ref,
        writer_ref,
        context.selected_artifact_ref,
        parsed_output_ref,
    )
    records: dict[RecordRef, dict[str, Any]] = {}
    for item in updated_base_records:
        payload = _record_payload(item)
        if not isinstance(payload, dict):
            return context
        records[item.ref] = payload
    if any(ref not in records for ref in evidence_refs):
        return context
    if any(ref not in records for proof in graph.proofs for ref in proof.evidence_refs):
        return context
    rebased_proofs = tuple(
        ScopeJoinProof.create(
            edge=proof.edge,
            profile=proof.profile,
            evidence_refs=proof.evidence_refs,
            evidence_payload_digests=tuple(
                semantic_digest(records[ref]) for ref in proof.evidence_refs
            ),
            snapshot_digest=proof.snapshot_digest,
            authority_limitations=proof.authority_limitations,
        )
        for proof in graph.proofs
    )
    limitation = (
        "The exact authorized source declares one direct writer for the selected report path; "
        "this static relation does not establish execution or produced bytes.",
    )
    proofs = (
        ScopeJoinProof.create(
            edge=ScopeJoinEdge(
                document.file_ref,
                "contains_unique_static_selected_output_writer",
                writer_ref,
            ),
            profile=STATIC_WRITER_SOURCE_PROFILE,
            evidence_refs=evidence_refs,
            evidence_payload_digests=tuple(semantic_digest(records[ref]) for ref in evidence_refs),
            snapshot_digest=context.snapshot_digest,
            authority_limitations=limitation,
        ),
        ScopeJoinProof.create(
            edge=ScopeJoinEdge(
                writer_ref,
                "declares_selected_output_artifact",
                context.selected_artifact_ref,
            ),
            profile=STATIC_WRITER_OUTPUT_PROFILE,
            evidence_refs=evidence_refs,
            evidence_payload_digests=tuple(semantic_digest(records[ref]) for ref in evidence_refs),
            snapshot_digest=context.snapshot_digest,
            authority_limitations=limitation,
        ),
    )
    merged = tuple(
        sorted(
            (*rebased_proofs, *proofs),
            key=lambda item: canonical_json(item.to_dict()),
        )
    )
    return replace(
        context,
        base_records=updated_base_records,
        scope_join_graph=StaticScopeJoinGraph(
            snapshot_digest=graph.snapshot_digest,
            proofs=merged,
            max_path_edges=graph.max_path_edges,
        ),
    )


def _closed_record_ref(value: object, record_type: str) -> RecordRef | None:
    if not isinstance(value, dict) or set(value) != {"record_type", "record_id"}:
        return None
    record_id = value.get("record_id")
    if value.get("record_type") != record_type or not isinstance(record_id, str):
        return None
    try:
        return RecordRef(record_type, record_id)
    except (TypeError, ValueError):
        return None


def _records_of_type(
    context: FrozenInspectionContext, record_type: str
) -> list[tuple[RecordRef, dict[str, Any]]]:
    matches: list[tuple[RecordRef, dict[str, Any]]] = []
    for record in context.base_records:
        if record.ref.record_type != record_type:
            continue
        value = _record_payload(record)
        if isinstance(value, dict):
            matches.append((record.ref, value))
    return matches


def _base_record_value(context: FrozenInspectionContext, ref: RecordRef) -> dict[str, Any] | None:
    matches = [item for item in context.base_records if item.ref == ref]
    if len(matches) != 1:
        return None
    value = _record_payload(matches[0])
    return value if isinstance(value, dict) else None


def _record_payload(record: FrozenBaseRecord) -> object:
    try:
        return json.loads(record.canonical_payload)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None


def _one_direct_selected_writer(
    document: InspectionDocument, selected_report_path: str
) -> ast.Call | None:
    try:
        tree = ast.parse(document.content.decode("utf-8", errors="strict"), type_comments=True)
    except (SyntaxError, UnicodeDecodeError, ValueError, MemoryError, RecursionError):
        return None
    pathlib_imports = [
        statement
        for statement in tree.body
        if isinstance(statement, ast.ImportFrom)
        and statement.level == 0
        and statement.module == "pathlib"
        and len(statement.names) == 1
        and statement.names[0].name == "Path"
        and statement.names[0].asname is None
    ]
    if len(pathlib_imports) != 1 or any(
        isinstance(node, ast.Name)
        and node.id == "Path"
        and isinstance(node.ctx, (ast.Store, ast.Del))
        for node in ast.walk(tree)
    ):
        return None
    matches: list[ast.Call] = []
    for statement in tree.body:
        if not isinstance(statement, ast.Expr) or not isinstance(statement.value, ast.Call):
            continue
        call = statement.value
        if not isinstance(call.func, ast.Attribute) or call.func.attr not in {
            "write_text",
            "write_bytes",
        }:
            continue
        receiver = call.func.value
        if not (
            isinstance(receiver, ast.Call)
            and isinstance(receiver.func, ast.Name)
            and receiver.func.id == "Path"
            and len(receiver.args) == 1
            and not receiver.keywords
            and isinstance(receiver.args[0], ast.Constant)
            and receiver.args[0].value == selected_report_path
        ):
            continue
        matches.append(call)
    return matches[0] if len(matches) == 1 else None


def _operation_matches_writer(
    value: dict[str, Any], *, document: InspectionDocument, call: ast.Call
) -> bool:
    implementation = value.get("implementation")
    name = implementation.get("name") if isinstance(implementation, dict) else implementation
    refs = value.get("source_refs")
    return bool(
        value.get("kind") == "write"
        and value.get("inspection_status") == "supported"
        and isinstance(name, str)
        and name.endswith((".write_text", ".write_bytes"))
        and isinstance(refs, list)
        and len(refs) == 1
        and isinstance(refs[0], dict)
        and refs[0].get("path") == document.path
        and refs[0].get("content_digest") == document.content_digest
        and refs[0].get("start_line") == call.lineno
        and refs[0].get("end_line") == getattr(call, "end_lineno", call.lineno)
        and refs[0].get("start_column") == call.col_offset + 1
        and refs[0].get("end_column") == getattr(call, "end_col_offset", call.col_offset) + 1
    )


def _closed_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise DependenceAuthorizationLockError(
                "dependence authority lock contains a duplicate JSON key"
            )
        value[key] = item
    return value


def _verify_analysis_record(record: object, source_paths: Iterable[str] | None) -> None:
    value = _require_record(record, "analysis", {"record_type", "record_id", "path"})
    path = _relative_path(value.get("path"), "analysis source")
    if source_paths is not None and list(source_paths).count(path) != 1:
        raise DependenceAuthorizationLockError(
            "dependence authority analysis source is not exactly frozen once"
        )


def _verify_procedure_record(record: object) -> None:
    value = _require_record(
        record,
        "procedure",
        {"record_type", "record_id", "resolved_callable"},
    )
    if value.get("resolved_callable") not in _PROCEDURES:
        raise DependenceAuthorizationLockError(
            "dependence authority procedure is outside the v1 registry"
        )


def _verify_result_record(record: object, selected_report_path: str | None) -> None:
    value = _require_record(record, "result", {"record_type", "record_id", "path"})
    path = _relative_path(value.get("path"), "selected result")
    if selected_report_path is not None and path != selected_report_path:
        raise DependenceAuthorizationLockError(
            "dependence authority result does not name the selected report"
        )


def _verify_authorization_record(
    record: object,
    *,
    analysis: dict[str, Any],
    procedure: dict[str, Any],
    material_input_digests: Mapping[str, str] | None,
) -> None:
    value = _require_record(
        record,
        "human_method_authorization",
        {
            "record_type",
            "record_id",
            "actor_id",
            "authority_state",
            "analysis_target_ref",
            "procedure_ref",
            "independent_unit_definition_id",
            "authorized_key_columns",
            "input_path",
            "input_content_digest",
        },
    )
    actor_id = value.get("actor_id")
    if not _bounded_identifier(actor_id) or not str(actor_id).startswith("scientist:"):
        raise DependenceAuthorizationLockError("dependence authority actor is invalid")
    if value.get("authority_state") != "authorized":
        raise DependenceAuthorizationLockError("dependence authority state is not authorized")
    if value.get("analysis_target_ref") != {
        "record_type": "analysis",
        "record_id": analysis["record_id"],
    }:
        raise DependenceAuthorizationLockError("dependence authority analysis ref is invalid")
    if value.get("procedure_ref") != {
        "record_type": "procedure",
        "record_id": procedure["record_id"],
    }:
        raise DependenceAuthorizationLockError("dependence authority procedure ref is invalid")
    if not _bounded_identifier(value.get("independent_unit_definition_id")):
        raise DependenceAuthorizationLockError("dependence authority unit-definition id is invalid")
    columns = value.get("authorized_key_columns")
    if not (
        isinstance(columns, list)
        and 1 <= len(columns) <= 4
        and all(_trimmed(item) for item in columns)
        and len(columns) == len(set(columns))
    ):
        raise DependenceAuthorizationLockError(
            "dependence authority ordered key columns are invalid"
        )
    input_path = _relative_path(value.get("input_path"), "material input")
    digest = value.get("input_content_digest")
    if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
        raise DependenceAuthorizationLockError("dependence authority input digest is invalid")
    if material_input_digests is not None and material_input_digests.get(input_path) != digest:
        raise DependenceAuthorizationLockError(
            "dependence authority input path or digest is not frozen"
        )


def _verify_approval(
    approval: object,
    authorization: dict[str, Any],
    *,
    intake_recorded_at: datetime | None,
) -> dict[str, Any]:
    if not isinstance(approval, dict) or set(approval) != {
        "actor_kind",
        "actor_id",
        "approved_projection_digest",
        "approved_at",
    }:
        raise DependenceAuthorizationLockError("dependence authority approval is not closed")
    if approval.get("actor_kind") != "human":
        raise DependenceAuthorizationLockError("dependence authority approval is not human")
    if approval.get("actor_id") != authorization.get("actor_id"):
        raise DependenceAuthorizationLockError("dependence authority approval actor mismatches")
    digest = approval.get("approved_projection_digest")
    if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
        raise DependenceAuthorizationLockError("dependence authority approval digest is invalid")
    parsed = _required_timestamp(approval.get("approved_at"), "approval time")
    if intake_recorded_at is not None and parsed < intake_recorded_at:
        raise DependenceAuthorizationLockError(
            "dependence authority approval predates the referenced intake"
        )
    return approval


def _require_record(
    record: object,
    record_type: str,
    keys: set[str],
) -> dict[str, Any]:
    if not isinstance(record, dict) or set(record) != keys:
        raise DependenceAuthorizationLockError(
            f"dependence authority {record_type} record is not closed"
        )
    if record.get("record_type") != record_type:
        raise DependenceAuthorizationLockError(
            f"dependence authority {record_type} record type is invalid"
        )
    record_id = record.get("record_id")
    if (
        not isinstance(record_id, str)
        or _RECORD_ID_RE.fullmatch(record_id) is None
        or len(record_id) > _MAX_FREE_TEXT_LENGTH
        or any(character.isspace() for character in record_id)
        or not record_id.startswith(_RECORD_ID_PREFIX[record_type])
    ):
        raise DependenceAuthorizationLockError(
            f"dependence authority {record_type} record id is invalid"
        )
    return record


def _selected_report_path(context: FrozenInspectionContext) -> str | None:
    matches = [item for item in context.base_records if item.ref == context.selected_artifact_ref]
    if len(matches) != 1:
        return None
    try:
        payload = json.loads(matches[0].canonical_payload)
    except (json.JSONDecodeError, RecursionError, MemoryError, TypeError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    path = payload.get("path")
    return path if isinstance(path, str) and _is_relative_path(path) else None


def _relative_path(value: object, label: str) -> str:
    if not isinstance(value, str) or not _is_relative_path(value):
        raise DependenceAuthorizationLockError(f"dependence authority {label} path is invalid")
    return value


def _is_relative_path(value: str) -> bool:
    path = PurePosixPath(value)
    return (
        bool(value) and not path.is_absolute() and "." not in path.parts and ".." not in path.parts
    )


def _trimmed(value: object) -> bool:
    return isinstance(value, str) and bool(value) and value == value.strip()


def _bounded_identifier(value: object) -> bool:
    return bool(
        isinstance(value, str)
        and 1 <= len(value) <= _MAX_FREE_TEXT_LENGTH
        and value == value.strip()
        and not any(character.isspace() for character in value)
    )


def _required_timestamp(value: object, label: str) -> datetime:
    if not _trimmed(value):
        raise DependenceAuthorizationLockError(f"dependence authority {label} is invalid")
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (OverflowError, TypeError, ValueError) as error:
        raise DependenceAuthorizationLockError(
            f"dependence authority {label} is invalid"
        ) from error
    if parsed.tzinfo is None:
        raise DependenceAuthorizationLockError(f"dependence authority {label} lacks a zone")
    return parsed


def _optional_timestamp(value: object, label: str) -> datetime | None:
    return None if value is None else _required_timestamp(value, label)


def _normalized_markers(markers: Iterable[str]) -> frozenset[str]:
    normalized: set[str] = set()
    for marker in markers:
        if not marker:
            continue
        normalized.update(_marker_variants(marker))
    return frozenset(normalized)


def _contains_marker(value: object, markers: frozenset[str]) -> bool:
    if isinstance(value, str):
        return any(
            marker in candidate for candidate in _marker_variants(value) for marker in markers
        )
    if isinstance(value, dict):
        return any(
            _contains_marker(key, markers) or _contains_marker(item, markers)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_marker(item, markers) for item in value)
    return False


def _marker_variants(value: str) -> frozenset[str]:
    folded = unicodedata.normalize("NFKC", value).translate(_CONFUSABLE_TO_LATIN).casefold()
    underscore = re.sub(r"[\s_-]+", "_", folded)
    hyphen = re.sub(r"[\s_-]+", "-", folded)
    return frozenset({folded, underscore, hyphen})


def _json_depth_within_bound(text: str) -> bool:
    depth = 0
    in_string = False
    escaped = False
    for character in text:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character in "[{":
            depth += 1
            if depth > _MAX_JSON_DEPTH:
                return False
        elif character in "]}":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0 and not in_string


def _verify_frozen_authorized_columns(
    context: FrozenInspectionContext,
    verified: VerifiedDependenceAuthorizationLock,
) -> None:
    authorization = verified.records[-1]
    input_path = authorization.get("input_path")
    input_digest = authorization.get("input_content_digest")
    columns = authorization.get("authorized_key_columns")
    matches = [
        item
        for item in context.material_inputs
        if item.path == input_path and item.content_digest == input_digest
    ]
    if len(matches) != 1 or not isinstance(columns, list):
        raise DependenceAuthorizationLockError(
            "dependence authority ordered key lacks one frozen CSV input"
        )
    material = matches[0]
    try:
        text = material.content.decode("utf-8", errors="strict")
        reader = csv.reader(io.StringIO(text, newline=""))
        header = next(reader)
    except (
        UnicodeDecodeError,
        csv.Error,
        StopIteration,
        RecursionError,
        MemoryError,
        TypeError,
        ValueError,
    ) as error:
        raise DependenceAuthorizationLockError(
            "dependence authority frozen CSV header is unavailable"
        ) from error
    if not header or any(not item for item in header) or len(header) != len(set(header)):
        raise DependenceAuthorizationLockError("dependence authority frozen CSV header is invalid")
    if any(column not in header for column in columns):
        raise DependenceAuthorizationLockError(
            "dependence authority ordered key names a column outside the frozen CSV header"
        )


def reverify_material_digest(content: bytes, expected_digest: str) -> bool:
    """Small explicit helper used by callers holding frozen material bytes."""

    return sha256_digest(content) == expected_digest
