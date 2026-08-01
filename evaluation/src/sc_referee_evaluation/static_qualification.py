from __future__ import annotations

import ast
import csv
import io
import math
import sys
import time
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from re import IGNORECASE
from re import compile as compile_regex
from typing import Any

from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id
from sc_referee.version import SCHEMA_VERSION


class StaticQualificationError(ValueError):
    """A static proof authority input or existing proof is internally inconsistent."""


_DETECTOR_ID = "detector:bounded-report-mean-direction"
_DETECTOR_VERSION = "0.1.0"
_PROFILE_KIND = "bounded_report_mean_direction_v1"
_ENTRY_POINT = "sc_referee_evaluation.static_qualification:verify_bounded_direction_case"
_SUFFIXES = (".csv", ".md", ".py")
_SHARED_UTILITIES = (
    "canonical_json",
    "content_hashing",
    "schema_shape_validation",
    "source_reference_resolution",
)
_APPLICABILITY_CHECKS = (
    "candidate_enumeration_complete",
    "claim_result_relation",
    "exact_csv_recomputation",
    "full_identity_complete",
    "literal_alignment_complete",
    "report_direction_inventory_complete",
    "strict_utf8_complete",
    "supported_python_grammar_complete",
    "unique_dependency_closure",
)
_COUNTEREVIDENCE_CHECKS = ("opposite_direction_sibling_claim",)
_CLAIM_PATTERN = compile_regex(
    r"(?P<left>[A-Za-z][A-Za-z0-9_-]*)\s+"
    r"(?P<verb>increased|decreased)\s+"
    r"(?P<outcome>[A-Za-z][A-Za-z0-9_-]*)\s+relative\s+to\s+"
    r"(?P<right>[A-Za-z][A-Za-z0-9_-]*)\s*[.!?]",
    IGNORECASE,
)
_DIRECTION_TOKEN_PATTERN = compile_regex(r"\b(?:increased|decreased)\b", IGNORECASE)


@dataclass(frozen=True)
class _MeanFunction:
    name: str
    path_argument: str
    group_column: str
    outcome_column: str
    left_group: str
    right_group: str
    left_name: str
    right_name: str


@dataclass(frozen=True)
class _WriterClosure:
    source_path: str
    report_path: str
    data_path: str
    mean: _MeanFunction
    report_prefix: str
    report_suffix: str


def freeze_protocol_artifact(
    artifact_kind: str,
    artifact_id: str,
    created_at: str,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Freeze one private protocol artifact without interpreting its scientific meaning."""

    if artifact_kind not in {
        "corpus_selection_protocol",
        "opaque_case_assignment",
        "scientific_label_freeze",
    }:
        raise StaticQualificationError("Unsupported static qualification artifact kind.")
    _timestamp(created_at)
    if not artifact_id:
        raise StaticQualificationError("Protocol artifact identity must be non-empty.")
    artifact = {
        "artifact_kind": artifact_kind,
        "artifact_id": artifact_id,
        "created_at": created_at,
        "payload": deepcopy(dict(payload)),
    }
    artifact["content_digest"] = semantic_digest(artifact)
    return artifact


def freeze_bounded_direction_profile(
    detector_manifest: Mapping[str, Any],
    parser_manifests: Sequence[Mapping[str, Any]],
    semantic_profile_manifests: Sequence[Mapping[str, Any]],
    version_manifests: Sequence[Mapping[str, Any]],
    selection_protocol_artifact: Mapping[str, Any],
    *,
    frozen_at: str,
    max_candidate_files: int = 1_000,
    max_total_bytes: int = 10_000_000,
    max_recursion_depth: int = 32,
    max_elapsed_milliseconds: int = 5_000,
) -> dict[str, Any]:
    """Freeze the only ADR-0022 profile before any qualification case is assigned."""

    _validate_detector_manifest(detector_manifest)
    protocol = _validate_protocol_artifact(selection_protocol_artifact, "corpus_selection_protocol")
    if _timestamp(frozen_at) < _timestamp(str(protocol["created_at"])):
        raise StaticQualificationError("Profile freeze predates its selection protocol.")
    parsers = _bound_records(parser_manifests, "parser_manifest", "parser_id")
    if not parsers:
        raise StaticQualificationError(
            "Static profile requires at least one exact parser manifest."
        )
    semantic_profiles = _bound_private_manifests(
        semantic_profile_manifests,
        "semantic_profile_manifest",
        "profile_id",
    )
    versions = _bound_private_manifests(
        version_manifests,
        "version_manifest",
        "version_manifest_id",
    )
    if not semantic_profiles or not versions:
        raise StaticQualificationError(
            "Static profile requires exact semantic-profile and version manifests."
        )
    budgets = {
        "max_candidate_files": max_candidate_files,
        "max_total_bytes": max_total_bytes,
        "max_recursion_depth": max_recursion_depth,
        "max_elapsed_milliseconds": max_elapsed_milliseconds,
    }
    if any(not isinstance(value, int) or value <= 0 for value in budgets.values()):
        raise StaticQualificationError("Every static profile budget must be a positive integer.")
    implementation_lock = _implementation_lock()
    manifest = deepcopy(dict(detector_manifest))
    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "static_qualification_profile",
        "profile_kind": _PROFILE_KIND,
        "profile_id": stable_id(
            "static-qualification-profile",
            _DETECTOR_ID,
            _DETECTOR_VERSION,
            semantic_digest(manifest),
            semantic_digest(implementation_lock),
            str(protocol["content_digest"]),
            frozen_at,
        ),
        "profile_version": "1.0.0",
        "target_detector": {
            "manifest": _bound_record(manifest, "detector_manifest", "detector_id"),
            "detector_id": _DETECTOR_ID,
            "detector_version": _DETECTOR_VERSION,
            "implementation_digest": str(manifest["implementation"]["implementation_digest"]),
            "material_premise_class": "static_closed_scope",
            "parser_manifests": parsers,
            "semantic_profile_manifests": semantic_profiles,
            "version_manifests": versions,
        },
        "verifier": {
            "entry_point": _ENTRY_POINT,
            "implementation_digest": sha256_digest(Path(__file__).read_bytes()),
            "dependency_closure": implementation_lock,
            "allowed_shared_utilities": list(_SHARED_UTILITIES),
        },
        "selection_rules": {
            "candidate_suffixes": list(_SUFFIXES),
            "candidate_enumeration": "all_matching_regular_files_in_snapshot_sorted_by_path",
            "dependency_closure": "unique_supported_csv_mean_writer_report_transitive_path",
            "parser_completeness": "strict_utf8_full_bytes_supported_grammar_or_unavailable",
            "report_path_source": "opaque_case_assignment_manifest",
            "surface_inventory": ("every_literal_directional_sentence_in_complete_selected_report"),
        },
        "budgets": budgets,
        "vocabularies": {
            "applicability_obligation_ids": list(_APPLICABILITY_CHECKS),
            "counterevidence_check_ids": list(_COUNTEREVIDENCE_CHECKS),
            "completion_statuses": ["completed", "error", "unavailable"],
            "outcomes": [
                "agreement",
                "conflict_absent",
                "conflict_present",
                "counterevidence_absent",
                "counterevidence_present",
            ],
        },
        "selection_protocol_artifact": _artifact_ref(protocol),
        "frozen_at": frozen_at,
        "profile_semantic_digest": "sha256:" + "0" * 64,
        "provenance": _provenance(frozen_at, "deterministic_static_profile_freeze"),
    }
    record["profile_semantic_digest"] = _self_digest(record, "profile_semantic_digest")
    return record


def verify_bounded_direction_case(
    workspace_root: Path,
    profile: Mapping[str, Any],
    case_assignment_artifact: Mapping[str, Any],
    label_freeze_artifact: Mapping[str, Any],
    snapshot: Mapping[str, Any],
    file_records: Sequence[Mapping[str, Any]],
    asset_identities: Sequence[Mapping[str, Any]],
    *,
    detector_manifest: Mapping[str, Any],
    parser_manifests: Sequence[Mapping[str, Any]],
    semantic_profile_manifests: Sequence[Mapping[str, Any]],
    version_manifests: Sequence[Mapping[str, Any]],
    proof_frozen_at: str,
) -> dict[str, Any]:
    """Independently derive the bounded direction facts from immutable raw bytes.

    The implementation intentionally does not import a production parser, semantic adapter,
    detector, or production fact helper, and it never imports or executes a project file.
    """

    started = time.monotonic_ns()
    frozen_profile = _validate_profile(
        profile,
        detector_manifest,
        parser_manifests,
        semantic_profile_manifests,
        version_manifests,
    )
    assignment = _validate_protocol_artifact(case_assignment_artifact, "opaque_case_assignment")
    label = _validate_protocol_artifact(label_freeze_artifact, "scientific_label_freeze")
    _validate_assignment_protocol(frozen_profile, assignment)
    root = workspace_root.resolve(strict=True)
    if not root.is_dir():
        raise StaticQualificationError("Static qualification workspace is not a directory.")
    selected_report = _selected_report_path(assignment)
    chronology = _chronology(frozen_profile, assignment, label, proof_frozen_at)
    snapshot_record = deepcopy(dict(snapshot))
    _validate_snapshot(snapshot_record)
    file_values = [deepcopy(dict(value)) for value in file_records]
    identity_values = [deepcopy(dict(value)) for value in asset_identities]

    retained: list[dict[str, Any]] = []
    candidate_payloads: dict[str, bytes] = {}
    candidates: list[str] = []
    failure: str | None = None
    try:
        candidates = _enumerate_candidates(
            root,
            snapshot_record,
            file_values,
            identity_values,
            frozen_profile,
            started,
        )
        retained, candidate_payloads = _bind_retained_bytes(
            root,
            candidates,
            snapshot_record,
            file_values,
            identity_values,
            frozen_profile,
            started,
        )
        decoded = _decode_candidates(candidate_payloads)
        report_claims = _inventory_report_claims(selected_report, decoded)
        closures, exclusions = _enumerate_python_closures(selected_report, decoded)
        if len(closures) != 1:
            raise _Unavailable(
                "unique_dependency_closure",
                f"Expected one supported dependency closure; observed {len(closures)}.",
            )
        closure = closures[0]
        values = _read_csv_values(closure, decoded)
        _validate_rendered_report(closure, decoded, values)
        facts = _derive_facts(candidates, closure, exclusions, report_claims, values)
        conflict = any(
            claim["orientation"] != facts["computed_orientation"]
            for claim in facts["literal_claims"]
        )
        applicability = [
            _check(
                check_id,
                "completed",
                (
                    ("conflict_present" if conflict else "conflict_absent")
                    if check_id == "claim_result_relation"
                    else "agreement"
                ),
                facts["supported_closure_paths"],
                check_id,
            )
            for check_id in _APPLICABILITY_CHECKS
        ]
        opposite = _has_opposite_sibling(report_claims)
        counterevidence = [
            _check(
                _COUNTEREVIDENCE_CHECKS[0],
                "completed",
                "counterevidence_present" if opposite else "counterevidence_absent",
                [selected_report],
                "opposite_sibling_present" if opposite else "full_report_search_complete",
            )
        ]
        proof_status = "complete"
    except _Unavailable as error:
        failure = error.detail
        facts = None
        applicability = _unavailable_checks(_APPLICABILITY_CHECKS, error.check_id, error.detail)
        counterevidence = [
            _check(
                _COUNTEREVIDENCE_CHECKS[0],
                "unavailable",
                None,
                [selected_report],
                "applicability_incomplete",
            )
        ]
        proof_status = "unavailable"

    graph = _dependency_graph(retained, facts, applicability, counterevidence)
    proof_id = stable_id(
        "static-qualification-proof",
        str(frozen_profile["profile_id"]),
        str(assignment["artifact_id"]),
        str(label["artifact_id"]),
        str(snapshot_record["snapshot_id"]),
        semantic_digest(retained),
        proof_frozen_at,
    )
    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "static_qualification_proof",
        "proof_profile_kind": _PROFILE_KIND,
        "proof_id": proof_id,
        "profile": _bound_record(frozen_profile, "static_qualification_profile", "profile_id"),
        "case_assignment_artifact": _artifact_ref(assignment),
        "label_freeze_artifact": _artifact_ref(label),
        "snapshot": _bound_record(snapshot_record, "repository_snapshot", "snapshot_id"),
        "retained_bytes": retained,
        "dependency_graph": graph,
        "applicability_results": applicability,
        "counterevidence_results": counterevidence,
        "derived_facts": facts,
        "chronology": chronology,
        "proof_status": proof_status,
        "proof_semantic_digest": "sha256:" + "0" * 64,
        "limitations": sorted(
            {
                "No project-authored code was imported or executed.",
                "The proof covers only the frozen raw two-group mean/report-direction profile.",
                *([f"Static proof unavailable: {failure}"] if failure is not None else []),
            }
        ),
        "provenance": _provenance(proof_frozen_at, "independent_static_direction_verification"),
    }
    record["proof_semantic_digest"] = _self_digest(record, "proof_semantic_digest")
    return record


def revalidate_static_proof(
    proof: Mapping[str, Any],
    workspace_root: Path,
    profile: Mapping[str, Any],
    case_assignment_artifact: Mapping[str, Any],
    label_freeze_artifact: Mapping[str, Any],
    snapshot: Mapping[str, Any],
    file_records: Sequence[Mapping[str, Any]],
    asset_identities: Sequence[Mapping[str, Any]],
    detector_manifest: Mapping[str, Any],
    parser_manifests: Sequence[Mapping[str, Any]],
    semantic_profile_manifests: Sequence[Mapping[str, Any]],
    version_manifests: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Rebuild a proof from its raw inputs and require byte-for-byte semantic equality."""

    current = deepcopy(dict(proof))
    if (
        current.get("record_type") != "static_qualification_proof"
        or current.get("proof_profile_kind") != _PROFILE_KIND
    ):
        raise StaticQualificationError("Expected one StaticQualificationProof.")
    if current.get("proof_semantic_digest") != _self_digest(current, "proof_semantic_digest"):
        raise StaticQualificationError("Static proof self digest does not verify.")
    chronology = current.get("chronology")
    if not isinstance(chronology, Mapping):
        raise StaticQualificationError("Static proof chronology is absent.")
    rebuilt = verify_bounded_direction_case(
        workspace_root,
        profile,
        case_assignment_artifact,
        label_freeze_artifact,
        snapshot,
        file_records,
        asset_identities,
        detector_manifest=detector_manifest,
        parser_manifests=parser_manifests,
        semantic_profile_manifests=semantic_profile_manifests,
        version_manifests=version_manifests,
        proof_frozen_at=str(chronology.get("proof_frozen_at", "")),
    )
    if rebuilt != current:
        raise StaticQualificationError("Static proof does not replay from the supplied raw bytes.")
    return rebuilt


class _Unavailable(Exception):
    def __init__(self, check_id: str, detail: str) -> None:
        super().__init__(detail)
        self.check_id = check_id
        self.detail = detail


def _validate_detector_manifest(manifest: Mapping[str, Any]) -> None:
    if (
        manifest.get("record_type") != "detector_manifest"
        or manifest.get("detector_id") != _DETECTOR_ID
        or manifest.get("detector_version") != _DETECTOR_VERSION
    ):
        raise StaticQualificationError("The profile target is not the exact bounded detector.")
    implementation = manifest.get("implementation")
    if not isinstance(implementation, Mapping):
        raise StaticQualificationError("Detector implementation identity is absent.")
    if implementation.get("deterministic") is not True or not isinstance(
        implementation.get("implementation_digest"), str
    ):
        raise StaticQualificationError("Detector implementation identity is incomplete.")


def _implementation_lock() -> list[dict[str, str]]:
    runtime = f"{sys.implementation.name}:{sys.version}"
    values = [
        {
            "dependency_kind": "implementation",
            "path": "sc_referee_evaluation/static_qualification.py",
            "content_digest": sha256_digest(Path(__file__).read_bytes()),
        },
        {
            "dependency_kind": "runtime",
            "path": "python-runtime",
            "content_digest": sha256_digest(runtime.encode("utf-8")),
        },
    ]
    return sorted(values, key=lambda item: (item["dependency_kind"], item["path"]))


def _validate_profile(
    profile: Mapping[str, Any],
    detector_manifest: Mapping[str, Any],
    parser_manifests: Sequence[Mapping[str, Any]],
    semantic_profile_manifests: Sequence[Mapping[str, Any]],
    version_manifests: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    value = deepcopy(dict(profile))
    if (
        value.get("schema_version") != SCHEMA_VERSION
        or value.get("record_type") != "static_qualification_profile"
        or value.get("profile_kind") != _PROFILE_KIND
        or value.get("profile_version") != "1.0.0"
    ):
        raise StaticQualificationError("Static profile version or record type is unsupported.")
    if value.get("profile_semantic_digest") != _self_digest(value, "profile_semantic_digest"):
        raise StaticQualificationError("Static profile self digest does not verify.")
    target = value.get("target_detector")
    verifier = value.get("verifier")
    rules = value.get("selection_rules")
    vocabulary = value.get("vocabularies")
    if not all(isinstance(item, Mapping) for item in (target, verifier, rules, vocabulary)):
        raise StaticQualificationError("Static profile structure is incomplete.")
    assert isinstance(target, Mapping)
    assert isinstance(verifier, Mapping)
    assert isinstance(rules, Mapping)
    assert isinstance(vocabulary, Mapping)
    _validate_detector_manifest(detector_manifest)
    implementation = detector_manifest["implementation"]
    assert isinstance(implementation, Mapping)
    expected_manifest = _bound_record(detector_manifest, "detector_manifest", "detector_id")
    expected_parsers = _bound_records(parser_manifests, "parser_manifest", "parser_id")
    expected_semantic_profiles = _bound_private_manifests(
        semantic_profile_manifests,
        "semantic_profile_manifest",
        "profile_id",
    )
    expected_versions = _bound_private_manifests(
        version_manifests,
        "version_manifest",
        "version_manifest_id",
    )
    if (
        target.get("detector_id") != _DETECTOR_ID
        or target.get("detector_version") != _DETECTOR_VERSION
        or target.get("manifest") != expected_manifest
        or target.get("implementation_digest") != implementation.get("implementation_digest")
        or target.get("parser_manifests") != expected_parsers
        or target.get("semantic_profile_manifests") != expected_semantic_profiles
        or target.get("version_manifests") != expected_versions
        or target.get("material_premise_class") != "static_closed_scope"
        or verifier.get("entry_point") != _ENTRY_POINT
        or verifier.get("implementation_digest") != sha256_digest(Path(__file__).read_bytes())
        or verifier.get("dependency_closure") != _implementation_lock()
        or verifier.get("allowed_shared_utilities") != list(_SHARED_UTILITIES)
        or rules.get("candidate_suffixes") != list(_SUFFIXES)
        or vocabulary.get("applicability_obligation_ids") != list(_APPLICABILITY_CHECKS)
        or vocabulary.get("counterevidence_check_ids") != list(_COUNTEREVIDENCE_CHECKS)
    ):
        raise StaticQualificationError("Static profile implementation or envelope has drifted.")
    return value


def _validate_protocol_artifact(value: Mapping[str, Any], kind: str) -> dict[str, Any]:
    artifact = deepcopy(dict(value))
    if (
        artifact.get("artifact_kind") != kind
        or not isinstance(artifact.get("artifact_id"), str)
        or not isinstance(artifact.get("created_at"), str)
        or not isinstance(artifact.get("payload"), Mapping)
        or not isinstance(artifact.get("content_digest"), str)
    ):
        raise StaticQualificationError(f"Malformed {kind} artifact.")
    _timestamp(str(artifact["created_at"]))
    digest = artifact.pop("content_digest")
    if digest != semantic_digest(artifact):
        raise StaticQualificationError(f"{kind} artifact digest does not verify.")
    artifact["content_digest"] = digest
    return artifact


def _selected_report_path(assignment: Mapping[str, Any]) -> str:
    payload = assignment.get("payload")
    selected = payload.get("selected_report_path") if isinstance(payload, Mapping) else None
    if not isinstance(selected, str):
        raise StaticQualificationError("Case assignment has no selected report path.")
    return _safe_relative(selected)


def _validate_assignment_protocol(
    profile: Mapping[str, Any], assignment: Mapping[str, Any]
) -> None:
    protocol = profile.get("selection_protocol_artifact")
    payload = assignment.get("payload")
    if (
        not isinstance(protocol, Mapping)
        or protocol.get("artifact_kind") != "corpus_selection_protocol"
        or not isinstance(protocol.get("artifact_id"), str)
        or not _is_digest(protocol.get("content_digest"))
        or not isinstance(payload, Mapping)
        or payload.get("selection_protocol_artifact_id") != protocol.get("artifact_id")
        or payload.get("selection_protocol_artifact_digest") != protocol.get("content_digest")
    ):
        raise StaticQualificationError(
            "Case assignment is not bound to the profile's frozen selection protocol."
        )


def _chronology(
    profile: Mapping[str, Any],
    assignment: Mapping[str, Any],
    label: Mapping[str, Any],
    proof_frozen_at: str,
) -> dict[str, Any]:
    profile_time = _timestamp(str(profile["frozen_at"]))
    assignment_time = _timestamp(str(assignment["created_at"]))
    label_time = _timestamp(str(label["created_at"]))
    proof_time = _timestamp(proof_frozen_at)
    if not profile_time < assignment_time < label_time < proof_time:
        raise StaticQualificationError(
            "Required profile, assignment, label, and proof chronology is not strictly ordered."
        )
    return {
        "profile_frozen_at": str(profile["frozen_at"]),
        "case_assigned_at": str(assignment["created_at"]),
        "label_frozen_at": str(label["created_at"]),
        "proof_frozen_at": proof_frozen_at,
        "detector_dispatched_at": None,
        "stage3_started_at": None,
    }


def _validate_snapshot(snapshot: Mapping[str, Any]) -> None:
    if (
        snapshot.get("record_type") != "repository_snapshot"
        or snapshot.get("schema_version") != SCHEMA_VERSION
        or snapshot.get("immutability") is not True
        or not isinstance(snapshot.get("snapshot_id"), str)
        or not isinstance(snapshot.get("snapshot_digest"), str)
    ):
        raise StaticQualificationError("Static proof requires one immutable exact snapshot.")


def _enumerate_candidates(
    root: Path,
    snapshot: Mapping[str, Any],
    file_records: Sequence[Mapping[str, Any]],
    asset_identities: Sequence[Mapping[str, Any]],
    profile: Mapping[str, Any],
    started_ns: int,
) -> list[str]:
    files = _validate_snapshot_inventory(snapshot, file_records, asset_identities)
    budgets = profile["budgets"]
    paths: list[str] = []
    total_bytes = 0
    for relative, record in sorted(files.items()):
        _check_elapsed(profile, started_ns)
        if PurePosixPath(relative).suffix.casefold() not in _SUFFIXES:
            continue
        if len(PurePosixPath(relative).parts) > int(budgets["max_recursion_depth"]):
            raise _Unavailable(
                "candidate_enumeration_complete", "Candidate recursion budget was exceeded."
            )
        paths.append(relative)
        total_bytes += int(record["byte_size"])
        if len(paths) > int(budgets["max_candidate_files"]):
            raise _Unavailable(
                "candidate_enumeration_complete", "Candidate file-count budget was exceeded."
            )
        if total_bytes > int(budgets["max_total_bytes"]):
            raise _Unavailable(
                "candidate_enumeration_complete", "Candidate byte budget was exceeded."
            )
    if not paths:
        raise _Unavailable("candidate_enumeration_complete", "No profile candidate exists.")
    materialized: list[str] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        _check_elapsed(profile, started_ns)
        if path.suffix.casefold() not in _SUFFIXES:
            continue
        relative = path.relative_to(root).as_posix()
        if path.is_symlink() or not path.is_file():
            raise _Unavailable(
                "candidate_enumeration_complete",
                f"Materialized candidate {relative!r} is not a regular file.",
            )
        materialized.append(relative)
    if materialized != paths:
        raise _Unavailable(
            "candidate_enumeration_complete",
            "Materialized candidate paths do not equal the complete snapshot candidate inventory.",
        )
    return paths


def _validate_snapshot_inventory(
    snapshot: Mapping[str, Any],
    file_records: Sequence[Mapping[str, Any]],
    asset_identities: Sequence[Mapping[str, Any]],
) -> dict[str, Mapping[str, Any]]:
    snapshot_id = str(snapshot["snapshot_id"])
    audit_run_id = str(snapshot.get("audit_run_id", ""))
    files_by_path: dict[str, Mapping[str, Any]] = {}
    files_by_id: dict[str, Mapping[str, Any]] = {}
    for record in file_records:
        path = record.get("path")
        file_id = record.get("file_record_id")
        byte_size = record.get("byte_size")
        if (
            record.get("schema_version") != SCHEMA_VERSION
            or record.get("record_type") != "file_record"
            or record.get("audit_run_id") != audit_run_id
            or record.get("snapshot_ref")
            != {"record_type": "repository_snapshot", "record_id": snapshot_id}
            or not isinstance(path, str)
            or _safe_relative(path) != path
            or not isinstance(file_id, str)
            or not isinstance(byte_size, int)
            or byte_size < 0
            or path in files_by_path
            or file_id in files_by_id
        ):
            raise _Unavailable(
                "candidate_enumeration_complete", "Snapshot FileRecord inventory is malformed."
            )
        files_by_path[path] = record
        files_by_id[file_id] = record
    if not files_by_path:
        raise _Unavailable(
            "candidate_enumeration_complete", "Snapshot FileRecord inventory is empty."
        )

    identities_by_file: dict[str, Mapping[str, Any]] = {}
    identity_ids: set[str] = set()
    for identity in asset_identities:
        asset_ref = identity.get("asset_ref")
        identity_id = identity.get("asset_identity_id")
        file_id = str(asset_ref.get("record_id", "")) if isinstance(asset_ref, Mapping) else ""
        if (
            identity.get("schema_version") != SCHEMA_VERSION
            or identity.get("record_type") != "asset_identity"
            or identity.get("audit_run_id") != audit_run_id
            or not isinstance(asset_ref, Mapping)
            or asset_ref.get("record_type") != "file_record"
            or not isinstance(identity_id, str)
            or not file_id
            or file_id in identities_by_file
            or identity_id in identity_ids
        ):
            raise _Unavailable(
                "candidate_enumeration_complete", "Snapshot AssetIdentity inventory is malformed."
            )
        identities_by_file[file_id] = identity
        identity_ids.add(identity_id)
    if set(identities_by_file) != set(files_by_id):
        raise _Unavailable(
            "candidate_enumeration_complete",
            "Snapshot FileRecord and AssetIdentity inventories do not close exactly.",
        )

    manifest: list[dict[str, Any]] = []
    for path, file_record in sorted(files_by_path.items()):
        file_id = str(file_record["file_record_id"])
        identity = identities_by_file[file_id]
        evidence = identity.get("identity_evidence")
        tier = identity.get("tier")
        entry_kind = str(file_record.get("entry_kind", ""))
        if not isinstance(evidence, Mapping) or not isinstance(tier, str):
            raise _Unavailable(
                "candidate_enumeration_complete", "Snapshot identity evidence is malformed."
            )
        expected_file_id = stable_id("file", path, tier, semantic_digest(dict(evidence)))
        expected_identity_id = stable_id(
            "asset-identity",
            audit_run_id,
            "file_record",
            file_id,
            tier,
            semantic_digest(dict(evidence)),
        )
        if (
            file_id != expected_file_id
            or identity.get("asset_identity_id") != expected_identity_id
            or file_record.get("asset_identity_ref")
            != {"record_type": "asset_identity", "record_id": expected_identity_id}
        ):
            raise _Unavailable(
                "candidate_enumeration_complete", "Snapshot identity derivation drifted."
            )
        manifest.append(
            {
                "path": path,
                "size_bytes": int(file_record["byte_size"]),
                "role": _snapshot_role(path, entry_kind),
                "tier": tier,
                "identity_evidence": deepcopy(dict(evidence)),
                "limitations": list(identity.get("limitations", [])),
            }
        )
    snapshot_digest = semantic_digest(manifest)
    if snapshot.get("snapshot_digest") != snapshot_digest or snapshot_id != stable_id(
        "snapshot", snapshot_digest
    ):
        raise _Unavailable(
            "candidate_enumeration_complete", "Snapshot inventory digest does not verify."
        )
    return files_by_path


def _snapshot_role(path: str, entry_kind: str) -> str:
    if entry_kind == "symlink":
        return "symlink_not_followed"
    if entry_kind == "special":
        return "unsupported_special_file"
    candidate = PurePosixPath(path)
    name = candidate.name.casefold()
    if "report" in name or "manuscript" in name:
        return "report_candidate"
    if candidate.suffix.casefold() in {".py", ".r", ".sh"}:
        return "analysis_source"
    if candidate.suffix.casefold() in {".csv", ".tsv", ".parquet"}:
        return "data_or_result"
    return "other"


def _bind_retained_bytes(
    root: Path,
    candidates: Sequence[str],
    snapshot: Mapping[str, Any],
    file_records: Sequence[Mapping[str, Any]],
    asset_identities: Sequence[Mapping[str, Any]],
    profile: Mapping[str, Any],
    started_ns: int,
) -> tuple[list[dict[str, Any]], dict[str, bytes]]:
    files = {str(record.get("path", "")): record for record in file_records}
    if len(files) != len(file_records):
        raise _Unavailable("full_identity_complete", "FileRecord paths are missing or duplicated.")
    identities = {str(record.get("asset_identity_id", "")): record for record in asset_identities}
    retained: list[dict[str, Any]] = []
    payloads: dict[str, bytes] = {}
    for relative in candidates:
        _check_elapsed(profile, started_ns)
        file_record = files.get(relative)
        if file_record is None:
            raise _Unavailable(
                "full_identity_complete", f"Candidate {relative!r} has no exact FileRecord."
            )
        identity_ref = file_record.get("asset_identity_ref")
        identity_id = (
            str(identity_ref.get("record_id", "")) if isinstance(identity_ref, Mapping) else ""
        )
        identity = identities.get(identity_id)
        evidence = identity.get("identity_evidence") if isinstance(identity, Mapping) else None
        if (
            file_record.get("record_type") != "file_record"
            or file_record.get("schema_version") != SCHEMA_VERSION
            or file_record.get("entry_kind") != "regular_file"
            or file_record.get("identity_disposition") != "recorded"
            or file_record.get("snapshot_ref", {}).get("record_id") != snapshot["snapshot_id"]
            or not isinstance(identity, Mapping)
            or identity.get("record_type") != "asset_identity"
            or identity.get("schema_version") != SCHEMA_VERSION
            or identity.get("tier") != "full_digest"
            or not isinstance(evidence, Mapping)
            or evidence.get("kind") != "full_digest"
        ):
            raise _Unavailable(
                "full_identity_complete", f"Candidate {relative!r} lacks full identity."
            )
        try:
            payload = (root / relative).read_bytes()
        except OSError as error:
            raise _Unavailable(
                "full_identity_complete", f"Candidate {relative!r} bytes are unavailable."
            ) from error
        digest = sha256_digest(payload)
        if (
            evidence.get("digest") != digest
            or file_record.get("byte_size") != len(payload)
            or identity.get("asset_ref", {}).get("record_id") != file_record.get("file_record_id")
        ):
            raise _Unavailable(
                "full_identity_complete", f"Candidate {relative!r} bytes or identity drifted."
            )
        retained.append(
            {
                "path": relative,
                "byte_size": len(payload),
                "content_digest": digest,
                "encoding": "utf-8",
                "file_record": _bound_record(file_record, "file_record", "file_record_id"),
                "asset_identity": _bound_record(identity, "asset_identity", "asset_identity_id"),
            }
        )
        payloads[relative] = payload
    return retained, payloads


def _decode_candidates(payloads: Mapping[str, bytes]) -> dict[str, str]:
    decoded: dict[str, str] = {}
    for path, payload in sorted(payloads.items()):
        try:
            decoded[path] = payload.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise _Unavailable(
                "strict_utf8_complete", f"Candidate {path!r} is not strict UTF-8."
            ) from error
    return decoded


def _inventory_report_claims(report_path: str, decoded: Mapping[str, str]) -> list[dict[str, Any]]:
    report = decoded.get(report_path)
    if report is None or not report_path.casefold().endswith(".md"):
        raise _Unavailable(
            "report_direction_inventory_complete",
            "The assigned selected report is not one retained Markdown candidate.",
        )
    claims: list[dict[str, Any]] = []
    for match in _CLAIM_PATTERN.finditer(report):
        verb = match.group("verb").casefold()
        claims.append(
            {
                "sentence": match.group(0),
                "orientation": "left_higher" if verb == "increased" else "right_higher",
                "left_group": match.group("left"),
                "right_group": match.group("right"),
                "outcome": match.group("outcome"),
                "start": match.start(),
                "end": match.end(),
            }
        )
    directional_tokens = len(_DIRECTION_TOKEN_PATTERN.findall(report))
    if directional_tokens != len(claims) or not claims:
        raise _Unavailable(
            "report_direction_inventory_complete",
            "The selected report contains zero or unsupported directional sentences.",
        )
    return claims


def _enumerate_python_closures(
    report_path: str, decoded: Mapping[str, str]
) -> tuple[list[_WriterClosure], list[dict[str, str]]]:
    closures: list[_WriterClosure] = []
    exclusions: list[dict[str, str]] = []
    for path, source in sorted(decoded.items()):
        if not path.casefold().endswith(".py"):
            continue
        try:
            tree = ast.parse(source, filename=path)
        except SyntaxError as error:
            raise _Unavailable(
                "supported_python_grammar_complete", f"Python candidate {path!r} is invalid."
            ) from error
        means = {
            item.name: item
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            if (item := _parse_mean_function(node)) is not None
        }
        relevant = "DictReader" in source or "write_text" in source
        found = _parse_writer_closures(path, tree, means, report_path)
        if relevant and not found:
            raise _Unavailable(
                "supported_python_grammar_complete",
                f"Relevant Python candidate {path!r} is outside the frozen grammar.",
            )
        if found:
            closures.extend(found)
        else:
            exclusions.append({"path": path, "reason_code": "no_supported_mean_writer_shape"})
    return closures, exclusions


def _parse_mean_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> _MeanFunction | None:
    if isinstance(node, ast.AsyncFunctionDef) or len(node.args.args) != 1:
        return None
    path_argument = node.args.args[0].arg
    list_specs: dict[str, tuple[str, str, str, str]] = {}
    return_node: ast.Return | None = None
    reader_targets: set[str] = set()
    reader_call_count = 0
    for child in ast.walk(node):
        if isinstance(child, ast.Call) and _call_name(child.func) == "csv.DictReader":
            reader_call_count += 1
        if isinstance(child, ast.Assign) and len(child.targets) == 1:
            target = child.targets[0]
            if isinstance(target, ast.Name):
                if _is_exact_reader_assignment(child.value, path_argument):
                    reader_targets.add(target.id)
                parsed = _parse_group_list(child.value)
                if parsed is not None:
                    list_specs[target.id] = parsed
        if isinstance(child, ast.Return):
            if return_node is not None:
                return None
            return_node = child
    if reader_call_count != 1 or len(reader_targets) != 1 or return_node is None:
        return None
    pair = _parse_mean_subtraction(return_node.value)
    if pair is None or pair[0] not in list_specs or pair[1] not in list_specs:
        return None
    left = list_specs[pair[0]]
    right = list_specs[pair[1]]
    if (
        left[0] != right[0]
        or left[1] != right[1]
        or left[2] == right[2]
        or left[3] != right[3]
        or left[3] not in reader_targets
    ):
        return None
    return _MeanFunction(
        name=node.name,
        path_argument=path_argument,
        group_column=left[0],
        outcome_column=left[1],
        left_group=left[2],
        right_group=right[2],
        left_name=pair[0],
        right_name=pair[1],
    )


def _is_exact_reader_assignment(value: ast.AST, path_argument: str) -> bool:
    if (
        not isinstance(value, ast.Call)
        or _call_name(value.func) != "list"
        or len(value.args) != 1
        or value.keywords
    ):
        return False
    reader = value.args[0]
    if (
        not isinstance(reader, ast.Call)
        or _call_name(reader.func) != "csv.DictReader"
        or len(reader.args) != 1
        or reader.keywords
    ):
        return False
    opened = reader.args[0]
    return (
        isinstance(opened, ast.Call)
        and isinstance(opened.func, ast.Attribute)
        and opened.func.attr == "open"
        and isinstance(opened.func.value, ast.Name)
        and opened.func.value.id == path_argument
        and not opened.args
        and not opened.keywords
    )


def _parse_group_list(value: ast.AST) -> tuple[str, str, str, str] | None:
    if not isinstance(value, ast.ListComp) or len(value.generators) != 1:
        return None
    generator = value.generators[0]
    if generator.is_async or len(generator.ifs) != 1 or not isinstance(generator.target, ast.Name):
        return None
    row = generator.target.id
    outcome_expr = value.elt
    if (
        isinstance(outcome_expr, ast.Call)
        and isinstance(outcome_expr.func, ast.Name)
        and outcome_expr.func.id == "float"
        and len(outcome_expr.args) == 1
    ):
        outcome_expr = outcome_expr.args[0]
    outcome = _literal_subscript(outcome_expr, row)
    condition = generator.ifs[0]
    if (
        outcome is None
        or not isinstance(condition, ast.Compare)
        or len(condition.ops) != 1
        or not isinstance(condition.ops[0], ast.Eq)
        or len(condition.comparators) != 1
    ):
        return None
    group_column = _literal_subscript(condition.left, row)
    comparator = condition.comparators[0]
    if (
        group_column is None
        or not isinstance(comparator, ast.Constant)
        or not isinstance(comparator.value, str)
    ):
        return None
    if not isinstance(generator.iter, ast.Name):
        return None
    return group_column, outcome, comparator.value, generator.iter.id


def _literal_subscript(value: ast.AST, name: str) -> str | None:
    if not isinstance(value, ast.Subscript) or not isinstance(value.value, ast.Name):
        return None
    if value.value.id != name or not isinstance(value.slice, ast.Constant):
        return None
    return value.slice.value if isinstance(value.slice.value, str) else None


def _parse_mean_subtraction(value: ast.AST | None) -> tuple[str, str] | None:
    if not isinstance(value, ast.BinOp) or not isinstance(value.op, ast.Sub):
        return None
    left = _mean_name(value.left)
    right = _mean_name(value.right)
    return (left, right) if left is not None and right is not None else None


def _mean_name(value: ast.AST) -> str | None:
    if not isinstance(value, ast.BinOp) or not isinstance(value.op, ast.Div):
        return None
    if not isinstance(value.left, ast.Call) or not isinstance(value.right, ast.Call):
        return None
    if _call_name(value.left.func) != "sum" or _call_name(value.right.func) != "len":
        return None
    if len(value.left.args) != 1 or len(value.right.args) != 1:
        return None
    left = value.left.args[0]
    right = value.right.args[0]
    if not isinstance(left, ast.Name) or not isinstance(right, ast.Name) or left.id != right.id:
        return None
    return left.id


def _parse_writer_closures(
    source_path: str,
    tree: ast.Module,
    means: Mapping[str, _MeanFunction],
    selected_report: str,
) -> list[_WriterClosure]:
    closures: list[_WriterClosure] = []
    selected_writes = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "write_text" or not isinstance(node.func.value, ast.Call):
            continue
        target = _path_literal(node.func.value)
        if target is None:
            continue
        resolved_target = _resolve_from_source(source_path, target)
        if resolved_target != selected_report:
            continue
        selected_writes += 1
        calls = (
            [
                child
                for child in ast.walk(node.args[0])
                if isinstance(child, ast.Call)
                and isinstance(child.func, ast.Name)
                and child.func.id in means
            ]
            if len(node.args) == 1 and isinstance(node.args[0], ast.JoinedStr)
            else []
        )
        if len(calls) != 1 or len(calls[0].args) != 1:
            continue
        data_literal = _path_literal(calls[0].args[0])
        if data_literal is None:
            continue
        function = calls[0].func
        if not isinstance(function, ast.Name):
            continue
        rendered_parts = _fstring_parts(node.args[0], calls[0])
        if rendered_parts is None:
            continue
        closures.append(
            _WriterClosure(
                source_path=source_path,
                report_path=selected_report,
                data_path=_resolve_from_source(source_path, data_literal),
                mean=means[function.id],
                report_prefix=rendered_parts[0],
                report_suffix=rendered_parts[1],
            )
        )
    if selected_writes != len(closures):
        return []
    return closures


def _fstring_parts(value: ast.AST, expected_call: ast.Call) -> tuple[str, str] | None:
    if not isinstance(value, ast.JoinedStr):
        return None
    formatted = [item for item in value.values if isinstance(item, ast.FormattedValue)]
    if (
        len(formatted) != 1
        or formatted[0].value is not expected_call
        or formatted[0].conversion != -1
        or formatted[0].format_spec is not None
    ):
        return None
    position = value.values.index(formatted[0])
    literals = [item for item in value.values if isinstance(item, ast.Constant)]
    if len(literals) != len(value.values) - 1 or any(
        not isinstance(item.value, str) for item in literals
    ):
        return None
    prefix = "".join(str(item.value) for item in literals[:position])
    suffix = "".join(str(item.value) for item in literals[position:])
    return prefix, suffix


def _path_literal(value: ast.AST) -> str | None:
    if (
        isinstance(value, ast.Call)
        and _call_name(value.func) in {"Path", "pathlib.Path"}
        and len(value.args) == 1
        and isinstance(value.args[0], ast.Constant)
        and isinstance(value.args[0].value, str)
    ):
        try:
            return _safe_relative(value.args[0].value)
        except StaticQualificationError:
            return None
    return None


def _call_name(value: ast.AST) -> str | None:
    if isinstance(value, ast.Name):
        return value.id
    if isinstance(value, ast.Attribute) and isinstance(value.value, ast.Name):
        return f"{value.value.id}.{value.attr}"
    return None


def _resolve_from_source(source_path: str, relative: str) -> str:
    parent = PurePosixPath(source_path).parent
    return _safe_relative((parent / relative).as_posix())


def _read_csv_values(
    closure: _WriterClosure, decoded: Mapping[str, str]
) -> tuple[list[float], list[float]]:
    source = decoded.get(closure.data_path)
    if source is None:
        raise _Unavailable(
            "exact_csv_recomputation",
            f"Data path {closure.data_path!r} is not one retained CSV candidate.",
        )
    try:
        rows = list(csv.DictReader(io.StringIO(source, newline=""), strict=True))
    except (csv.Error, UnicodeError) as error:
        raise _Unavailable("exact_csv_recomputation", "CSV parsing failed.") from error
    mean = closure.mean
    if not rows or mean.group_column not in (rows[0].keys() if rows else ()):
        raise _Unavailable("exact_csv_recomputation", "CSV group column is absent.")
    if mean.outcome_column not in (rows[0].keys() if rows else ()):
        raise _Unavailable("exact_csv_recomputation", "CSV outcome column is absent.")
    left: list[float] = []
    right: list[float] = []
    try:
        for row in rows:
            group = row[mean.group_column]
            if group not in {mean.left_group, mean.right_group}:
                continue
            value = float(row[mean.outcome_column])
            if not math.isfinite(value):
                raise ValueError("non-finite")
            (left if group == mean.left_group else right).append(value)
    except (KeyError, TypeError, ValueError) as error:
        raise _Unavailable(
            "exact_csv_recomputation", "CSV numeric operands are incomplete or non-finite."
        ) from error
    if not left or not right:
        raise _Unavailable(
            "exact_csv_recomputation", "One or both exact literal groups have no values."
        )
    return left, right


def _validate_rendered_report(
    closure: _WriterClosure,
    decoded: Mapping[str, str],
    values: tuple[list[float], list[float]],
) -> None:
    left, right = values
    rendered = (
        closure.report_prefix
        + str(math.fsum(left) / len(left) - math.fsum(right) / len(right))
        + closure.report_suffix
    )
    if decoded.get(closure.report_path) != rendered:
        raise _Unavailable(
            "unique_dependency_closure",
            "Selected report bytes do not equal the exact supported static writer output.",
        )


def _derive_facts(
    candidates: Sequence[str],
    closure: _WriterClosure,
    exclusions: Sequence[dict[str, str]],
    claims: Sequence[dict[str, Any]],
    values: tuple[list[float], list[float]],
) -> dict[str, Any]:
    mean = closure.mean
    relevant = [
        claim
        for claim in claims
        if _normalized(str(claim["left_group"])) == _normalized(mean.left_group)
        and _normalized(str(claim["right_group"])) == _normalized(mean.right_group)
        and _normalized(str(claim["outcome"])) == _normalized(mean.outcome_column)
    ]
    if len(relevant) != len(claims):
        raise _Unavailable(
            "literal_alignment_complete",
            "A directional sentence does not exactly align to the closed group/outcome labels.",
        )
    left, right = values
    left_mean = math.fsum(left) / len(left)
    right_mean = math.fsum(right) / len(right)
    orientation = (
        "left_higher"
        if left_mean > right_mean
        else "right_higher"
        if right_mean > left_mean
        else "equal"
    )
    closure_paths = sorted({closure.source_path, closure.data_path, closure.report_path})
    excluded = list(exclusions)
    for path in candidates:
        if path not in closure_paths and not any(item["path"] == path for item in excluded):
            excluded.append({"path": path, "reason_code": "non_python_candidate_outside_closure"})
    excluded.sort(key=lambda item: (item["path"], item["reason_code"]))
    return {
        "selected_report_path": closure.report_path,
        "data_path": closure.data_path,
        "writer_path": closure.source_path,
        "group_column": mean.group_column,
        "outcome_column": mean.outcome_column,
        "left_group": mean.left_group,
        "right_group": mean.right_group,
        "left_values": left,
        "right_values": right,
        "left_mean": left_mean,
        "right_mean": right_mean,
        "computed_orientation": orientation,
        "literal_claims": [
            {
                "sentence": claim["sentence"],
                "orientation": claim["orientation"],
                "start": claim["start"],
                "end": claim["end"],
            }
            for claim in relevant
        ],
        "candidate_paths": list(candidates),
        "supported_closure_paths": closure_paths,
        "supported_exclusions": excluded,
    }


def _has_opposite_sibling(claims: Sequence[Mapping[str, Any]]) -> bool:
    orientations = {str(claim["orientation"]) for claim in claims}
    return "left_higher" in orientations and "right_higher" in orientations


def _dependency_graph(
    retained: Sequence[Mapping[str, Any]],
    facts: Mapping[str, Any] | None,
    applicability: Sequence[Mapping[str, Any]],
    counterevidence: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    nodes = [
        {
            "node_id": stable_id("static-proof-node", str(item["path"])),
            "node_kind": "raw_byte_source",
            "path": item["path"],
            "semantic_digest": item["content_digest"],
        }
        for item in retained
    ]
    if not nodes:
        nodes.append(
            {
                "node_id": "static-proof-node:unavailable",
                "node_kind": "check",
                "path": None,
                "semantic_digest": semantic_digest(
                    {"applicability": applicability, "counterevidence": counterevidence}
                ),
            }
        )
    fact_id: str | None = None
    if facts is not None:
        fact_id = stable_id("static-proof-node", "derived-facts", semantic_digest(facts))
        nodes.append(
            {
                "node_id": fact_id,
                "node_kind": "derived_fact",
                "path": None,
                "semantic_digest": semantic_digest(facts),
            }
        )
    edges = []
    if fact_id is not None:
        edges = [
            {"from_node_id": node["node_id"], "to_node_id": fact_id, "relation": "derives"}
            for node in nodes
            if node["node_kind"] == "raw_byte_source"
        ]
    return {
        "nodes": sorted(nodes, key=lambda item: str(item["node_id"])),
        "edges": sorted(
            edges,
            key=lambda item: (
                str(item["from_node_id"]),
                str(item["to_node_id"]),
                str(item["relation"]),
            ),
        ),
    }


def _check(
    check_id: str,
    completion_status: str,
    outcome: str | None,
    evidence_paths: Sequence[str],
    detail_code: str,
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "completion_status": completion_status,
        "outcome": outcome,
        "evidence_paths": sorted(set(evidence_paths)),
        "detail_code": detail_code,
    }


def _unavailable_checks(
    check_ids: Sequence[str], failed_check: str, detail: str
) -> list[dict[str, Any]]:
    return [
        _check(
            check_id,
            "unavailable",
            None,
            [],
            detail if check_id == failed_check else f"blocked_by:{failed_check}",
        )
        for check_id in check_ids
    ]


def _check_elapsed(profile: Mapping[str, Any], started_ns: int) -> None:
    elapsed_ms = (time.monotonic_ns() - started_ns) // 1_000_000
    if elapsed_ms > int(profile["budgets"]["max_elapsed_milliseconds"]):
        raise _Unavailable("candidate_enumeration_complete", "Elapsed-time budget was exceeded.")


def _bound_records(
    records: Sequence[Mapping[str, Any]], record_type: str, identity_field: str
) -> list[dict[str, Any]]:
    values = [_bound_record(record, record_type, identity_field) for record in records]
    identities = [str(item["record_ref"]["record_id"]) for item in values]
    if len(identities) != len(set(identities)):
        raise StaticQualificationError(f"Duplicate {record_type} identity.")
    return sorted(values, key=lambda item: str(item["record_ref"]["record_id"]))


def _bound_record(
    record: Mapping[str, Any], record_type: str, identity_field: str
) -> dict[str, Any]:
    if record.get("record_type") != record_type or not isinstance(record.get(identity_field), str):
        raise StaticQualificationError(f"Expected one exact {record_type} record.")
    return {
        "record_ref": {
            "record_type": record_type,
            "record_id": str(record[identity_field]),
        },
        "semantic_digest": semantic_digest(record),
    }


def _bound_private_manifests(
    records: Sequence[Mapping[str, Any]], manifest_kind: str, identity_field: str
) -> list[dict[str, str]]:
    values: list[dict[str, str]] = []
    for record in records:
        identity = record.get(identity_field)
        if not isinstance(identity, str) or not identity:
            raise StaticQualificationError(f"Expected one exact {manifest_kind} record.")
        values.append(
            {
                "manifest_kind": manifest_kind,
                "manifest_id": identity,
                "semantic_digest": semantic_digest(record),
            }
        )
    identities = [item["manifest_id"] for item in values]
    if len(identities) != len(set(identities)):
        raise StaticQualificationError(f"Duplicate {manifest_kind} identity.")
    return sorted(values, key=lambda item: item["manifest_id"])


def _artifact_ref(artifact: Mapping[str, Any]) -> dict[str, str]:
    return {
        "artifact_kind": str(artifact["artifact_kind"]),
        "artifact_id": str(artifact["artifact_id"]),
        "content_digest": str(artifact["content_digest"]),
    }


def _self_digest(record: Mapping[str, Any], field: str) -> str:
    basis = deepcopy(dict(record))
    basis.pop(field, None)
    digest = semantic_digest(basis)
    if not isinstance(digest, str):
        raise StaticQualificationError("Semantic digest helper returned a non-string value.")
    return digest


def _is_digest(value: object) -> bool:
    if not isinstance(value, str) or not value.startswith("sha256:") or len(value) != 71:
        return False
    return all(char in "0123456789abcdef" for char in value[7:])


def _safe_relative(value: str) -> str:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or value != path.as_posix():
        raise StaticQualificationError("Static qualification path is not a safe relative path.")
    return value


def _normalized(value: str) -> str:
    return " ".join(value.casefold().split())


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise StaticQualificationError(f"Invalid timestamp {value!r}.") from error
    if parsed.tzinfo is None:
        raise StaticQualificationError("Static qualification timestamps require a timezone.")
    return parsed


def _provenance(created_at: str, method: str) -> dict[str, Any]:
    return {
        "actor": {
            "actor_kind": "controller",
            "actor_id": "software:sc-referee-eval-static-verifier",
            "display_name": "independent static qualification verifier",
        },
        "method": method,
        "created_at": created_at,
        "tool": "sc-referee-eval",
        "tool_version": "0.2.0",
    }
