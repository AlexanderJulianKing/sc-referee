from __future__ import annotations

import ast
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
from sc_referee_evaluation.snapshot_evidence import (
    SnapshotEvidenceError,
    read_full_digest_snapshot_file,
    validate_content_addressed_snapshot,
)


class AnalysisMethodQualificationError(ValueError):
    """A method-profile authority input or proof is internally inconsistent."""


_DETECTOR_ID = "detector:bounded-analysis-method-conflict"
_DETECTOR_VERSION = "0.1.0"
_CHECK_ID = "check:founder-orientation-before-hmm-emission"
_PROFILE_KIND = "bounded_analysis_method_conflict_v1"
_ENTRY_POINT = (
    "sc_referee_evaluation.analysis_method_qualification:verify_bounded_analysis_method_case"
)
_DIRECT = "use_supplied_founder_alleles_directly_in_hmm_emission"
_REPAIRED = "repair_ril_founder_orientation_before_hmm_emission"
_OPERANDS = {_DIRECT, _REPAIRED}
_SUFFIXES = (".md", ".py")
_ORIENTATION_CALLS = {
    "orient_ril_founder_alleles",
    "repair_ril_founder_orientation",
}
_SHARED_UTILITIES = (
    "canonical_json",
    "content_hashing",
    "schema_shape_validation",
    "source_reference_resolution",
)
_APPLICABILITY_CHECKS = (
    "answer_authority_complete",
    "candidate_enumeration_complete",
    "full_identity_complete",
    "observed_plane_agreement",
    "report_operand_unique",
    "selected_output_scope_closure",
    "source_operand_unique",
    "strict_utf8_complete",
    "unique_selected_output_writer",
)
_COUNTEREVIDENCE_CHECKS = (
    "alternate_or_superseding_intent",
    "approved_method_deviation",
    "conditional_applicability",
    "governing_protocol_amendment",
    "sensitivity_or_unsupported_qualifier",
)
_DIRECT_PATTERN = compile_regex(
    r"founder[- ]origin\s+HMM\s+was\s+fitted[^.!?]*"
    r"using\s+the\s+supplied\s+founder\s+alleles",
    IGNORECASE,
)
_REPAIRED_PATTERN = compile_regex(
    r"founder(?:\s+(?:0/1|binary))?(?:\s+marker)?\s+alleles\s+were\s+"
    r"(?:orientation-repaired|reoriented|oriented)[^.!?]*"
    r"before\s+(?:the\s+)?(?:HMM\s+)?emissions?",
    IGNORECASE,
)
_SENTENCE_PATTERN = compile_regex(r"[^.!?]*(?:[.!?]|$)")


@dataclass(frozen=True)
class _ResolvedFounder:
    state: str
    origin: str
    nodes: tuple[ast.AST, ...]


@dataclass(frozen=True)
class _SourceShape:
    operand: str
    nodes: tuple[ast.AST, ...]


@dataclass(frozen=True)
class _Writer:
    path: str
    node: ast.Call


def freeze_protocol_artifact(
    artifact_kind: str,
    artifact_id: str,
    created_at: str,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Freeze one private selection artifact without interpreting a scientific label."""

    if artifact_kind not in {
        "corpus_selection_protocol",
        "opaque_case_assignment",
        "scientific_label_freeze",
    }:
        raise AnalysisMethodQualificationError("Unsupported qualification artifact kind.")
    _timestamp(created_at)
    if not artifact_id:
        raise AnalysisMethodQualificationError("Protocol artifact identity must be non-empty.")
    artifact = {
        "artifact_kind": artifact_kind,
        "artifact_id": artifact_id,
        "created_at": created_at,
        "payload": deepcopy(dict(payload)),
    }
    artifact["content_digest"] = semantic_digest(artifact)
    return artifact


def freeze_bounded_analysis_method_profile(
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
    """Freeze the exact non-executing ADR-0041 qualification profile."""

    _validate_detector_manifest(detector_manifest)
    protocol = _validate_protocol_artifact(selection_protocol_artifact, "corpus_selection_protocol")
    if _timestamp(frozen_at) < _timestamp(str(protocol["created_at"])):
        raise AnalysisMethodQualificationError("Profile freeze predates its selection protocol.")
    parsers = _bound_records(parser_manifests, "parser_manifest", "parser_id")
    semantic_profiles = _bound_private_manifests(
        semantic_profile_manifests, "semantic_profile_manifest", "profile_id"
    )
    versions = _bound_private_manifests(
        version_manifests, "version_manifest", "version_manifest_id"
    )
    if not parsers or not semantic_profiles or not versions:
        raise AnalysisMethodQualificationError(
            "Method profile requires exact parser, semantic-profile, and version manifests."
        )
    budgets = {
        "max_candidate_files": max_candidate_files,
        "max_total_bytes": max_total_bytes,
        "max_recursion_depth": max_recursion_depth,
        "max_elapsed_milliseconds": max_elapsed_milliseconds,
    }
    if any(not isinstance(value, int) or value <= 0 for value in budgets.values()):
        raise AnalysisMethodQualificationError("Every profile budget must be a positive integer.")
    manifest = deepcopy(dict(detector_manifest))
    implementation_lock = _implementation_lock()
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
            "dependency_closure": "unique_supported_founder_operand_writer_selected_report_path",
            "parser_completeness": "strict_utf8_full_bytes_supported_grammar_or_unavailable",
            "report_path_source": "opaque_case_assignment_manifest",
            "surface_inventory": (
                "every_closed_founder_orientation_declaration_in_selected_report_and_python_candidates"
            ),
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
        "provenance": _provenance(frozen_at, "deterministic_analysis_method_profile_freeze"),
    }
    record["profile_semantic_digest"] = _self_digest(record, "profile_semantic_digest")
    return record


def verify_bounded_analysis_method_case(
    workspace_root: Path,
    profile: Mapping[str, Any],
    case_assignment_artifact: Mapping[str, Any],
    label_freeze_artifact: Mapping[str, Any],
    snapshot: Mapping[str, Any],
    file_records: Sequence[Mapping[str, Any]],
    asset_identities: Sequence[Mapping[str, Any]],
    material_questions: Sequence[Mapping[str, Any]],
    answers: Sequence[Mapping[str, Any]],
    scientific_contracts: Sequence[Mapping[str, Any]],
    semantic_assertions: Sequence[Mapping[str, Any]],
    *,
    detector_manifest: Mapping[str, Any],
    parser_manifests: Sequence[Mapping[str, Any]],
    semantic_profile_manifests: Sequence[Mapping[str, Any]],
    version_manifests: Sequence[Mapping[str, Any]],
    proof_frozen_at: str,
) -> dict[str, Any]:
    """Independently derive the closed method facts without importing project code."""

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
    selected_report = _selected_report_path(assignment)
    chronology = _chronology(frozen_profile, assignment, label, proof_frozen_at)
    root = workspace_root.resolve(strict=True)
    if not root.is_dir():
        raise AnalysisMethodQualificationError("Qualification workspace is not a directory.")
    snapshot_value = deepcopy(dict(snapshot))
    files = [deepcopy(dict(item)) for item in file_records]
    identities = [deepcopy(dict(item)) for item in asset_identities]
    questions = [deepcopy(dict(item)) for item in material_questions]
    answer_values = [deepcopy(dict(item)) for item in answers]
    contracts = [deepcopy(dict(item)) for item in scientific_contracts]
    assertions = [deepcopy(dict(item)) for item in semantic_assertions]
    retained: list[dict[str, Any]] = []
    failure: str | None = None
    try:
        candidates, retained, decoded = _read_candidates(
            root, snapshot_value, files, identities, frozen_profile, started
        )
        report_operand, report_declarations = _report_declarations(selected_report, decoded)
        source_operand, source_declarations, writer_path, exclusions = _source_closure(
            selected_report, decoded
        )
        authority = _authority_facts(questions, answer_values, contracts, assertions)
        if writer_path != source_declarations[0]["path"]:
            raise _Unavailable(
                "selected_output_scope_closure",
                "The unique report writer and unique source operand are not in the same file.",
            )
        supported_paths = sorted({selected_report, writer_path})
        excluded = list(exclusions)
        for path in candidates:
            if path not in supported_paths and not any(item["path"] == path for item in excluded):
                excluded.append(
                    {"path": path, "reason_code": "candidate_outside_supported_closure"}
                )
        excluded.sort(key=lambda item: (item["path"], item["reason_code"]))
        facts = {
            "selected_report_path": selected_report,
            "writer_path": writer_path,
            "report_operand": report_operand,
            "source_operand": source_operand,
            "requirement_operand": authority["requirement_operand"],
            "report_declarations": report_declarations,
            "source_declarations": source_declarations,
            "governing_question": authority["governing_question"],
            "governing_answer": authority["governing_answer"],
            "governing_contract": authority["governing_contract"],
            "requirement_assertion": authority["requirement_assertion"],
            "candidate_paths": candidates,
            "supported_closure_paths": supported_paths,
            "supported_exclusions": excluded,
        }
        conflict = report_operand != source_operand
        applicability = [
            _check(
                check_id,
                "completed",
                (
                    "conflict_present"
                    if check_id == "observed_plane_agreement" and conflict
                    else "conflict_absent"
                    if check_id == "observed_plane_agreement"
                    else "agreement"
                ),
                _applicability_paths(check_id, selected_report, writer_path),
                "closed_search_complete",
            )
            for check_id in _APPLICABILITY_CHECKS
        ]
        counterevidence = _counterevidence(assertions, authority, selected_report, writer_path)
        proof_status = "complete"
    except _Unavailable as error:
        failure = error.detail
        facts = None
        applicability = _unavailable_checks(_APPLICABILITY_CHECKS, error.check_id, error.detail)
        counterevidence = _unavailable_checks(_COUNTEREVIDENCE_CHECKS, error.check_id, error.detail)
        proof_status = "unavailable"

    graph = _dependency_graph(retained, facts, applicability, counterevidence)
    proof_id = stable_id(
        "static-qualification-proof",
        str(frozen_profile["profile_id"]),
        str(assignment["artifact_id"]),
        str(label["artifact_id"]),
        str(snapshot_value["snapshot_id"]),
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
        "snapshot": _bound_record(snapshot_value, "repository_snapshot", "snapshot_id"),
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
                "The proof establishes declarations and a review requirement, not execution or numerical effect.",
                "The human Answer governs only this review and does not establish universal method adequacy.",
                *([f"Static proof unavailable: {failure}"] if failure is not None else []),
            }
        ),
        "provenance": _provenance(
            proof_frozen_at, "independent_static_analysis_method_verification"
        ),
    }
    record["proof_semantic_digest"] = _self_digest(record, "proof_semantic_digest")
    return record


def revalidate_analysis_method_proof(
    proof: Mapping[str, Any],
    workspace_root: Path,
    profile: Mapping[str, Any],
    case_assignment_artifact: Mapping[str, Any],
    label_freeze_artifact: Mapping[str, Any],
    snapshot: Mapping[str, Any],
    file_records: Sequence[Mapping[str, Any]],
    asset_identities: Sequence[Mapping[str, Any]],
    material_questions: Sequence[Mapping[str, Any]],
    answers: Sequence[Mapping[str, Any]],
    scientific_contracts: Sequence[Mapping[str, Any]],
    semantic_assertions: Sequence[Mapping[str, Any]],
    detector_manifest: Mapping[str, Any],
    parser_manifests: Sequence[Mapping[str, Any]],
    semantic_profile_manifests: Sequence[Mapping[str, Any]],
    version_manifests: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Rebuild a method proof and require exact semantic equality."""

    current = deepcopy(dict(proof))
    if (
        current.get("record_type") != "static_qualification_proof"
        or current.get("proof_profile_kind") != _PROFILE_KIND
        or current.get("proof_semantic_digest") != _self_digest(current, "proof_semantic_digest")
    ):
        raise AnalysisMethodQualificationError("Expected one self-verifying method proof.")
    chronology = current.get("chronology")
    if not isinstance(chronology, Mapping):
        raise AnalysisMethodQualificationError("Method proof chronology is absent.")
    rebuilt = verify_bounded_analysis_method_case(
        workspace_root,
        profile,
        case_assignment_artifact,
        label_freeze_artifact,
        snapshot,
        file_records,
        asset_identities,
        material_questions,
        answers,
        scientific_contracts,
        semantic_assertions,
        detector_manifest=detector_manifest,
        parser_manifests=parser_manifests,
        semantic_profile_manifests=semantic_profile_manifests,
        version_manifests=version_manifests,
        proof_frozen_at=str(chronology.get("proof_frozen_at", "")),
    )
    if rebuilt != current:
        raise AnalysisMethodQualificationError(
            "Method proof does not replay from the supplied raw and authority inputs."
        )
    return rebuilt


class _Unavailable(Exception):
    def __init__(self, check_id: str, detail: str) -> None:
        super().__init__(detail)
        self.check_id = check_id
        self.detail = detail


def _validate_detector_manifest(manifest: Mapping[str, Any]) -> None:
    implementation = manifest.get("implementation")
    if (
        manifest.get("record_type") != "detector_manifest"
        or manifest.get("detector_id") != _DETECTOR_ID
        or manifest.get("detector_version") != _DETECTOR_VERSION
        or not isinstance(implementation, Mapping)
        or implementation.get("deterministic") is not True
        or not isinstance(implementation.get("implementation_digest"), str)
    ):
        raise AnalysisMethodQualificationError("The profile target is not the exact detector.")


def _implementation_lock() -> list[dict[str, str]]:
    runtime = f"{sys.implementation.name}:{sys.version}"
    return sorted(
        [
            {
                "dependency_kind": "implementation",
                "path": "sc_referee_evaluation/analysis_method_qualification.py",
                "content_digest": sha256_digest(Path(__file__).read_bytes()),
            },
            {
                "dependency_kind": "implementation",
                "path": "sc_referee_evaluation/snapshot_evidence.py",
                "content_digest": sha256_digest(
                    Path(__file__).with_name("snapshot_evidence.py").read_bytes()
                ),
            },
            {
                "dependency_kind": "runtime",
                "path": "python-runtime",
                "content_digest": sha256_digest(runtime.encode("utf-8")),
            },
        ],
        key=lambda item: (item["dependency_kind"], item["path"]),
    )


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
        or value.get("profile_semantic_digest") != _self_digest(value, "profile_semantic_digest")
    ):
        raise AnalysisMethodQualificationError("Method profile version or digest is unsupported.")
    _validate_detector_manifest(detector_manifest)
    target = value.get("target_detector")
    verifier = value.get("verifier")
    rules = value.get("selection_rules")
    vocabulary = value.get("vocabularies")
    if not all(isinstance(item, Mapping) for item in (target, verifier, rules, vocabulary)):
        raise AnalysisMethodQualificationError("Method profile structure is incomplete.")
    assert isinstance(target, Mapping)
    assert isinstance(verifier, Mapping)
    assert isinstance(rules, Mapping)
    assert isinstance(vocabulary, Mapping)
    implementation = detector_manifest["implementation"]
    assert isinstance(implementation, Mapping)
    if (
        target.get("detector_id") != _DETECTOR_ID
        or target.get("detector_version") != _DETECTOR_VERSION
        or target.get("manifest")
        != _bound_record(detector_manifest, "detector_manifest", "detector_id")
        or target.get("implementation_digest") != implementation.get("implementation_digest")
        or target.get("parser_manifests")
        != _bound_records(parser_manifests, "parser_manifest", "parser_id")
        or target.get("semantic_profile_manifests")
        != _bound_private_manifests(
            semantic_profile_manifests, "semantic_profile_manifest", "profile_id"
        )
        or target.get("version_manifests")
        != _bound_private_manifests(version_manifests, "version_manifest", "version_manifest_id")
        or target.get("material_premise_class") != "static_closed_scope"
        or verifier.get("entry_point") != _ENTRY_POINT
        or verifier.get("implementation_digest") != sha256_digest(Path(__file__).read_bytes())
        or verifier.get("dependency_closure") != _implementation_lock()
        or verifier.get("allowed_shared_utilities") != list(_SHARED_UTILITIES)
        or rules.get("candidate_suffixes") != list(_SUFFIXES)
        or vocabulary.get("applicability_obligation_ids") != list(_APPLICABILITY_CHECKS)
        or vocabulary.get("counterevidence_check_ids") != list(_COUNTEREVIDENCE_CHECKS)
    ):
        raise AnalysisMethodQualificationError("Method profile implementation or envelope drifted.")
    return value


def _read_candidates(
    root: Path,
    snapshot: Mapping[str, Any],
    file_records: Sequence[Mapping[str, Any]],
    asset_identities: Sequence[Mapping[str, Any]],
    profile: Mapping[str, Any],
    started: int,
) -> tuple[list[str], list[dict[str, Any]], dict[str, str]]:
    try:
        index = validate_content_addressed_snapshot(
            deepcopy(dict(snapshot)),
            [deepcopy(dict(item)) for item in file_records],
            [deepcopy(dict(item)) for item in asset_identities],
        )
    except (SnapshotEvidenceError, KeyError, TypeError, ValueError) as error:
        raise _Unavailable("candidate_enumeration_complete", str(error)) from error
    candidates: list[str] = []
    total = 0
    budgets = profile["budgets"]
    for path, record in sorted(index.files_by_path.items()):
        _check_elapsed(profile, started)
        relative = PurePosixPath(path)
        if relative.suffix.casefold() not in _SUFFIXES:
            continue
        if len(relative.parts) > int(budgets["max_recursion_depth"]):
            raise _Unavailable("candidate_enumeration_complete", "Recursion budget exceeded.")
        if record.get("entry_kind") != "regular_file":
            raise _Unavailable(
                "candidate_enumeration_complete", f"Candidate {path!r} is not a regular file."
            )
        candidates.append(path)
        total += int(record["byte_size"])
        if len(candidates) > int(budgets["max_candidate_files"]):
            raise _Unavailable("candidate_enumeration_complete", "File-count budget exceeded.")
        if total > int(budgets["max_total_bytes"]):
            raise _Unavailable("candidate_enumeration_complete", "Byte budget exceeded.")
    materialized = [
        path.relative_to(root).as_posix()
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix())
        if path.suffix.casefold() in _SUFFIXES
    ]
    if materialized != candidates or not candidates:
        raise _Unavailable(
            "candidate_enumeration_complete",
            "Materialized candidates differ from the complete snapshot candidate inventory.",
        )
    retained: list[dict[str, Any]] = []
    decoded: dict[str, str] = {}
    for path in candidates:
        _check_elapsed(profile, started)
        try:
            file_record, identity, payload, digest = read_full_digest_snapshot_file(
                index, root, path
            )
        except (SnapshotEvidenceError, OSError) as error:
            raise _Unavailable("full_identity_complete", str(error)) from error
        try:
            decoded[path] = payload.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise _Unavailable(
                "strict_utf8_complete", f"Candidate {path!r} is not UTF-8."
            ) from error
        retained.append(
            {
                "path": path,
                "byte_size": len(payload),
                "content_digest": digest,
                "encoding": "utf-8",
                "file_record": _bound_record(file_record, "file_record", "file_record_id"),
                "asset_identity": _bound_record(identity, "asset_identity", "asset_identity_id"),
            }
        )
    return candidates, retained, decoded


def _report_declarations(
    selected_report: str, decoded: Mapping[str, str]
) -> tuple[str, list[dict[str, Any]]]:
    report = decoded.get(selected_report)
    if report is None or PurePosixPath(selected_report).suffix.casefold() != ".md":
        raise _Unavailable(
            "report_operand_unique", "Selected report is not one retained Markdown candidate."
        )
    declarations: list[dict[str, Any]] = []
    relevant = 0
    for match in _SENTENCE_PATTERN.finditer(report):
        sentence = match.group(0)
        normalized = " ".join(sentence.split())
        if not normalized:
            continue
        lowered = normalized.casefold()
        if (
            "founder" not in lowered
            or "allele" not in lowered
            or not any(token in lowered for token in ("hmm", "emission"))
        ):
            continue
        relevant += 1
        direct = bool(_DIRECT_PATTERN.search(normalized))
        repaired = bool(_REPAIRED_PATTERN.search(normalized))
        if direct == repaired:
            raise _Unavailable(
                "report_operand_unique",
                "A relevant selected-report sentence is unsupported or ambiguous.",
            )
        start = match.start() + len(sentence) - len(sentence.lstrip())
        rendered = sentence.strip()
        declarations.append(
            {
                "operand": _DIRECT if direct else _REPAIRED,
                "path": selected_report,
                "start": start,
                "end": start + len(rendered),
                "sentence": rendered,
            }
        )
    if relevant != 1 or len(declarations) != 1:
        raise _Unavailable(
            "report_operand_unique",
            f"Expected one closed report declaration; observed {len(declarations)} of {relevant} relevant sentences.",
        )
    return str(declarations[0]["operand"]), declarations


def _source_closure(
    selected_report: str, decoded: Mapping[str, str]
) -> tuple[str, list[dict[str, Any]], str, list[dict[str, str]]]:
    shapes: list[tuple[str, _SourceShape]] = []
    writers: list[_Writer] = []
    exclusions: list[dict[str, str]] = []
    for path, source in sorted(decoded.items()):
        if PurePosixPath(path).suffix.casefold() != ".py":
            continue
        try:
            tree = ast.parse(source, filename=path, type_comments=True)
        except SyntaxError as error:
            raise _Unavailable(
                "source_operand_unique", f"Python candidate {path!r} is invalid."
            ) from error
        found_shapes = _founder_shapes(tree)
        triggered = _founder_triggered(tree)
        if triggered and not found_shapes:
            raise _Unavailable(
                "source_operand_unique",
                f"Relevant founder-emission flow in {path!r} is outside the closed grammar.",
            )
        shapes.extend((path, shape) for shape in found_shapes)
        found_writers, unresolved = _writers(path, tree, selected_report)
        if unresolved:
            raise _Unavailable(
                "unique_selected_output_writer",
                f"Python candidate {path!r} has a dynamic or unsupported report writer.",
            )
        writers.extend(found_writers)
        if not found_shapes and not found_writers:
            exclusions.append({"path": path, "reason_code": "no_supported_method_or_writer_shape"})
    if len(shapes) != 1:
        raise _Unavailable(
            "source_operand_unique",
            f"Expected one supported source operand; observed {len(shapes)}.",
        )
    if len(writers) != 1:
        raise _Unavailable(
            "unique_selected_output_writer",
            f"Expected one selected-report writer; observed {len(writers)}.",
        )
    path, shape = shapes[0]
    writer = writers[0]
    start = min(int(getattr(node, "lineno", 1)) for node in shape.nodes)
    end = max(int(getattr(node, "end_lineno", getattr(node, "lineno", 1))) for node in shape.nodes)
    return (
        shape.operand,
        [{"operand": shape.operand, "path": path, "start_line": start, "end_line": end}],
        writer.path,
        exclusions,
    )


def _founder_shapes(tree: ast.Module) -> list[_SourceShape]:
    parents = _parent_map(tree)
    functions = _local_functions(tree)
    shapes: list[_SourceShape] = []
    for candidates in functions.values():
        if len(candidates) != 1:
            continue
        function = candidates[0]
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and _terminal_call_name(node) == function.name
            and len(node.args) >= 2
        ]
        shape = _shape_for_function(tree, function, calls, parents, functions)
        if shape is not None:
            shapes.append(shape)
    return shapes


def _shape_for_function(
    tree: ast.Module,
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    calls: list[ast.Call],
    parents: Mapping[ast.AST, ast.AST],
    functions: Mapping[str, tuple[ast.FunctionDef | ast.AsyncFunctionDef, ...]],
) -> _SourceShape | None:
    if not calls:
        return None
    parameters = (*function.args.posonlyargs, *function.args.args)
    if len(parameters) < 2:
        return None
    comparisons = [
        node
        for node in _nodes_in_scope(function, parents)
        if isinstance(node, ast.Compare)
        and parameters[0].arg in _names(node)
        and parameters[1].arg in _names(node)
    ]
    if len(comparisons) != 1:
        return None
    resolved: list[_ResolvedFounder] = []
    for call in calls:
        item = _resolve_founder(
            call.args[1],
            _enclosing_scope(tree, call, parents),
            tree,
            parents,
            functions,
            frozenset(),
        )
        if item is None:
            return None
        resolved.append(item)
    if len({item.state for item in resolved}) != 1 or len({item.origin for item in resolved}) != 1:
        return None
    state = resolved[0].state
    nodes = _unique_nodes(
        (comparisons[0], *calls, *(node for item in resolved for node in item.nodes))
    )
    return _SourceShape(_REPAIRED if state == "repaired" else _DIRECT, nodes)


def _resolve_founder(
    expression: ast.expr,
    scope: ast.Module | ast.FunctionDef | ast.AsyncFunctionDef,
    tree: ast.Module,
    parents: Mapping[ast.AST, ast.AST],
    functions: Mapping[str, tuple[ast.FunctionDef | ast.AsyncFunctionDef, ...]],
    seen: frozenset[tuple[int, str]],
) -> _ResolvedFounder | None:
    if isinstance(expression, ast.Call):
        if _terminal_call_name(expression) in _ORIENTATION_CALLS:
            return _ResolvedFounder(
                "repaired", ast.dump(expression, include_attributes=False), (expression,)
            )
        return None
    if isinstance(expression, ast.Attribute):
        if expression.attr == "founder_alleles":
            return _ResolvedFounder(
                "direct",
                f"{id(scope)}:{ast.dump(expression, include_attributes=False)}",
                (expression,),
            )
        return _resolve_founder(expression.value, scope, tree, parents, functions, seen)
    if isinstance(expression, ast.Subscript):
        return _resolve_founder(expression.value, scope, tree, parents, functions, seen)
    if not isinstance(expression, ast.Name):
        return None
    key = (id(scope), expression.id)
    if key in seen:
        return None
    bindings = _name_bindings(scope, expression.id, parents)
    if len(bindings) != 1:
        return None
    assignment, value, tuple_index = bindings[0]
    if tuple_index is None:
        item = _resolve_founder(value, scope, tree, parents, functions, seen | {key})
    else:
        item = _resolve_return_component(value, tuple_index, tree, parents, functions, seen | {key})
    if item is None:
        return None
    return _ResolvedFounder(item.state, item.origin, (assignment, *item.nodes))


def _resolve_return_component(
    value: ast.expr,
    index: int,
    tree: ast.Module,
    parents: Mapping[ast.AST, ast.AST],
    functions: Mapping[str, tuple[ast.FunctionDef | ast.AsyncFunctionDef, ...]],
    seen: frozenset[tuple[int, str]],
) -> _ResolvedFounder | None:
    if not isinstance(value, ast.Call):
        return None
    candidates = functions.get(_terminal_call_name(value), ())
    if len(candidates) != 1:
        return None
    function = candidates[0]
    returns = [
        node
        for node in _nodes_in_scope(function, parents)
        if isinstance(node, ast.Return) and node.value is not None
    ]
    if len(returns) != 1 or not isinstance(returns[0].value, (ast.Tuple, ast.List)):
        return None
    values = returns[0].value.elts
    if index >= len(values):
        return None
    item = _resolve_founder(values[index], function, tree, parents, functions, seen)
    if item is None:
        return None
    return _ResolvedFounder(item.state, item.origin, (value, returns[0], *item.nodes))


def _writers(source_path: str, tree: ast.Module, report_path: str) -> tuple[list[_Writer], bool]:
    root_aliases = {
        target.id
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance((target := node.targets[0]), ast.Name)
        and _is_source_parent(node.value)
    }
    parents = _parent_map(tree)
    writers: list[_Writer] = []
    unresolved = False
    for node in ast.walk(tree):
        if (
            not isinstance(node, ast.Call)
            or not isinstance(node.func, ast.Attribute)
            or node.func.attr not in {"write_text", "write_bytes"}
        ):
            continue
        resolved = _writer_path(node.func.value, root_aliases, source_path)
        if resolved is None:
            unresolved = True
            continue
        if resolved == report_path:
            if not _writer_context_supported(node, tree, parents):
                unresolved = True
            else:
                writers.append(_Writer(source_path, node))
    return writers, unresolved


def _is_source_parent(value: ast.AST) -> bool:
    # Exact: Path(__file__).resolve().parent
    return (
        isinstance(value, ast.Attribute)
        and value.attr == "parent"
        and isinstance(value.value, ast.Call)
        and not value.value.args
        and not value.value.keywords
        and isinstance(value.value.func, ast.Attribute)
        and value.value.func.attr == "resolve"
        and isinstance(value.value.func.value, ast.Call)
        and _terminal_call_name(value.value.func.value) == "Path"
        and len(value.value.func.value.args) == 1
        and isinstance(value.value.func.value.args[0], ast.Name)
        and value.value.func.value.args[0].id == "__file__"
    )


def _writer_path(value: ast.AST, roots: set[str], source_path: str) -> str | None:
    parts: list[str] = []
    current = value
    while isinstance(current, ast.BinOp) and isinstance(current.op, ast.Div):
        if not isinstance(current.right, ast.Constant) or not isinstance(current.right.value, str):
            return None
        parts.append(current.right.value)
        current = current.left
    if not isinstance(current, ast.Name) or current.id not in roots or not parts:
        return None
    parts.reverse()
    try:
        relative = PurePosixPath(source_path).parent.joinpath(*parts)
        return _safe_relative(relative.as_posix())
    except AnalysisMethodQualificationError:
        return None


def _writer_context_supported(
    call: ast.Call, tree: ast.Module, parents: Mapping[ast.AST, ast.AST]
) -> bool:
    scope = _enclosing_scope(tree, call, parents)
    if isinstance(scope, ast.Module):
        return True
    if isinstance(scope, ast.AsyncFunctionDef) or scope.args.args or scope.args.posonlyargs:
        return False
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and _terminal_call_name(node) == scope.name
    ]
    return len(calls) == 1 and _inside_main_guard(calls[0], parents)


def _inside_main_guard(call: ast.Call, parents: Mapping[ast.AST, ast.AST]) -> bool:
    current: ast.AST = call
    while current in parents:
        current = parents[current]
        if isinstance(current, ast.If):
            return _is_main_guard(current.test)
    return False


def _is_main_guard(value: ast.AST) -> bool:
    if not isinstance(value, ast.Compare) or len(value.ops) != 1 or len(value.comparators) != 1:
        return False
    if not isinstance(value.ops[0], ast.Eq):
        return False
    sides = (value.left, value.comparators[0])
    return any(isinstance(side, ast.Name) and side.id == "__name__" for side in sides) and any(
        isinstance(side, ast.Constant) and side.value == "__main__" for side in sides
    )


def _authority_facts(
    questions: Sequence[Mapping[str, Any]],
    answers: Sequence[Mapping[str, Any]],
    contracts: Sequence[Mapping[str, Any]],
    assertions: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    eligible = [
        item
        for item in questions
        if item.get("record_type") == "material_question"
        and item.get("status") == "answered"
        and item.get("extensions", {}).get("x-scientific-check-id") == _CHECK_ID
    ]
    if len(eligible) != 1:
        raise _Unavailable(
            "answer_authority_complete", "Expected one answered founder-orientation question."
        )
    question = eligible[0]
    extensions = question.get("extensions")
    if not isinstance(extensions, Mapping):
        raise _Unavailable("answer_authority_complete", "Question extensions are absent.")
    subject = extensions.get("x-analysis-subject-ref")
    contract_ref = extensions.get("x-contract-ref")
    scope_path = extensions.get("x-scientific-check-scope-join-path")
    scope_digest = extensions.get("x-scientific-check-scope-join-digest")
    candidate_values = {
        operand.get("value")
        for item in extensions.get("x-scientific-check-requirement-candidates", [])
        if isinstance(item, Mapping)
        and isinstance((operand := item.get("operand")), Mapping)
        and operand.get("kind") == "canonical_scalar"
    }
    if (
        not _record_ref(subject, "publication_surface")
        or not _record_ref(contract_ref, "scientific_contract")
        or extensions.get("x-output-ceiling") != "question_only"
        or extensions.get("x-posthoc-comparison-forms") != {"scale_and_orientation": "value_equals"}
        or not isinstance(scope_path, list)
        or semantic_digest(scope_path) != scope_digest
        or not _OPERANDS.issubset(candidate_values)
    ):
        raise _Unavailable(
            "answer_authority_complete", "Question candidates, scope, or comparison form drifted."
        )
    question_id = str(question.get("question_id", ""))
    matching_answers = [
        item
        for item in answers
        if item.get("record_type") == "answer"
        and item.get("question_ref")
        == {"record_type": "material_question", "record_id": question_id}
    ]
    if len(matching_answers) != 1:
        raise _Unavailable("answer_authority_complete", "Expected one matching Answer.")
    answer = matching_answers[0]
    digest_basis = deepcopy(dict(answer))
    answer_digest = digest_basis.pop("answer_digest", None)
    requirement = answer.get("answer_value", {}).get("scale_and_orientation")
    if (
        answer_digest != semantic_digest(digest_basis)
        or requirement not in _OPERANDS
        or answer.get("respondent", {}).get("actor_kind") != "human"
        or answer.get("provenance", {}).get("actor", {}).get("actor_kind") != "human"
        or answer.get("authority_scope")
        != {
            "authority_kind": "scientific_intent",
            "subject_refs": [subject],
            "semantic_dimensions": ["scale_and_orientation"],
        }
    ):
        raise _Unavailable(
            "answer_authority_complete",
            "Answer digest, human authority, scope, or operand drifted.",
        )
    assert isinstance(contract_ref, Mapping)
    contract_id = str(contract_ref.get("record_id"))
    matching_contracts = [
        item
        for item in contracts
        if item.get("record_type") == "scientific_contract"
        and item.get("contract_id") == contract_id
    ]
    if len(matching_contracts) != 1:
        raise _Unavailable("answer_authority_complete", "Expected one governing contract.")
    contract = matching_contracts[0]
    slot = contract.get("dimensions", {}).get("scale_and_orientation")
    if (
        contract.get("scope") != {"level": "analysis", "subject_refs": [subject]}
        or not isinstance(slot, Mapping)
        or slot.get("state") != "known"
        or not isinstance(slot.get("accepted_assertion_ids"), list)
        or not slot["accepted_assertion_ids"]
    ):
        raise _Unavailable("answer_authority_complete", "Contract scope or dimension drifted.")
    accepted_ids = {str(value) for value in slot["accepted_assertion_ids"]}
    matching_assertions = [
        item
        for item in assertions
        if item.get("record_type") == "semantic_assertion"
        and item.get("assertion_id") in accepted_ids
        and item.get("predicate") == "verified_intended_scale_and_orientation"
    ]
    if len(matching_assertions) != 1:
        raise _Unavailable("answer_authority_complete", "Requirement assertion is not unique.")
    assertion = matching_assertions[0]
    assertion_id = str(assertion["assertion_id"])
    ax = assertion.get("extensions")
    if (
        assertion.get("subject_ref") != subject
        or assertion.get("predicate") != "verified_intended_scale_and_orientation"
        or assertion.get("object") != requirement
        or assertion.get("assertion_class") != "deterministic_derivation"
        or assertion.get("epistemic_status") != "accepted"
        or assertion.get("authority_scope") != "scientific_intent"
        or assertion.get("finding_eligibility") != "ineligible"
        or assertion.get("verification", {}).get("status") != "verified"
        or not isinstance(ax, Mapping)
        or ax.get("x-answer-ref") != {"record_type": "answer", "record_id": answer.get("answer_id")}
        or ax.get("x-answer-digest") != answer_digest
        or ax.get("x-scientific-check-id") != _CHECK_ID
        or ax.get("x-scientific-check-scope-join-digest") != scope_digest
    ):
        raise _Unavailable("answer_authority_complete", "Requirement assertion authority drifted.")
    return {
        "requirement_operand": requirement,
        "subject": subject,
        "scope_digest": scope_digest,
        "governing_question": _bound_record(question, "material_question", "question_id"),
        "governing_answer": _bound_record(answer, "answer", "answer_id"),
        "governing_contract": _bound_record(contract, "scientific_contract", "contract_id"),
        "requirement_assertion": _bound_record(assertion, "semantic_assertion", "assertion_id"),
        "requirement_assertion_id": assertion_id,
    }


def _counterevidence(
    assertions: Sequence[Mapping[str, Any]],
    authority: Mapping[str, Any],
    report_path: str,
    writer_path: str,
) -> list[dict[str, Any]]:
    same_subject = [
        item
        for item in assertions
        if item.get("record_type") == "semantic_assertion"
        and item.get("epistemic_status") == "accepted"
        and item.get("subject_ref") == authority["subject"]
    ]
    extra_requirements = [
        item
        for item in same_subject
        if item.get("predicate") == "verified_intended_scale_and_orientation"
        and item.get("assertion_id") != authority["requirement_assertion_id"]
    ]
    by_check = {
        "alternate_or_superseding_intent": extra_requirements,
        "governing_protocol_amendment": [
            item for item in same_subject if item.get("predicate") == "governing_protocol_amendment"
        ],
        "approved_method_deviation": [
            item for item in same_subject if item.get("predicate") == "approved_method_deviation"
        ],
        "conditional_applicability": [
            item
            for item in same_subject
            if item.get("predicate") == "method_obligation_applicability"
            and item.get("object") != "applies"
        ],
        "sensitivity_or_unsupported_qualifier": [
            item
            for item in assertions
            if item.get("epistemic_status") == "accepted"
            and item.get("extensions", {}).get("x-scientific-check-id") == _CHECK_ID
            and item.get("extensions", {}).get("x-scientific-check-scope-join-digest")
            == authority["scope_digest"]
            and (
                item.get("extensions", {}).get("x-sensitivity-only") is True
                or bool(item.get("extensions", {}).get("x-unsupported-method-constructs"))
            )
        ],
    }
    results = []
    for check_id in _COUNTEREVIDENCE_CHECKS:
        matches = by_check[check_id]
        paths = sorted(
            {
                str(source["path"])
                for item in matches
                for source in item.get("source_refs", [])
                if isinstance(source, Mapping) and isinstance(source.get("path"), str)
            }
        )
        results.append(
            _check(
                check_id,
                "completed",
                "counterevidence_present" if matches else "counterevidence_absent",
                paths or [report_path, writer_path],
                "counterevidence_present" if matches else "closed_search_complete",
            )
        )
    return results


def _applicability_paths(check_id: str, report: str, writer: str) -> list[str]:
    if check_id in {"report_operand_unique"}:
        return [report]
    if check_id in {"source_operand_unique", "unique_selected_output_writer"}:
        return [writer]
    return [report, writer]


def _founder_triggered(tree: ast.Module) -> bool:
    has_founder = any(
        isinstance(node, ast.Attribute) and node.attr == "founder_alleles"
        for node in ast.walk(tree)
    )
    has_comparison = any(isinstance(node, ast.Compare) for node in ast.walk(tree))
    has_repair = any(
        isinstance(node, ast.Call) and _terminal_call_name(node) in _ORIENTATION_CALLS
        for node in ast.walk(tree)
    )
    return has_founder and (has_comparison or has_repair)


def _parent_map(tree: ast.Module) -> dict[ast.AST, ast.AST]:
    return {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}


def _local_functions(
    tree: ast.Module,
) -> dict[str, tuple[ast.FunctionDef | ast.AsyncFunctionDef, ...]]:
    grouped: dict[str, list[ast.FunctionDef | ast.AsyncFunctionDef]] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            grouped.setdefault(node.name, []).append(node)
    return {name: tuple(values) for name, values in grouped.items()}


def _nodes_in_scope(
    scope: ast.FunctionDef | ast.AsyncFunctionDef, parents: Mapping[ast.AST, ast.AST]
) -> list[ast.AST]:
    return [
        node
        for node in ast.walk(scope)
        if node is scope or _enclosing_function(node, parents) is scope
    ]


def _enclosing_function(
    node: ast.AST, parents: Mapping[ast.AST, ast.AST]
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current
    return None


def _enclosing_scope(
    tree: ast.Module, node: ast.AST, parents: Mapping[ast.AST, ast.AST]
) -> ast.Module | ast.FunctionDef | ast.AsyncFunctionDef:
    return _enclosing_function(node, parents) or tree


def _name_bindings(
    scope: ast.Module | ast.FunctionDef | ast.AsyncFunctionDef,
    name: str,
    parents: Mapping[ast.AST, ast.AST],
) -> list[tuple[ast.AST, ast.expr, int | None]]:
    bindings: list[tuple[ast.AST, ast.expr, int | None]] = []
    nodes = ast.walk(scope) if isinstance(scope, ast.Module) else _nodes_in_scope(scope, parents)
    for node in nodes:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id == name:
                bindings.append((node, node.value, None))
            elif isinstance(target, (ast.Tuple, ast.List)):
                indexes = [
                    index
                    for index, item in enumerate(target.elts)
                    if isinstance(item, ast.Name) and item.id == name
                ]
                bindings.extend((node, node.value, index) for index in indexes)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == name and node.value is not None:
                bindings.append((node, node.value, None))
    return bindings


def _names(node: ast.AST) -> set[str]:
    return {child.id for child in ast.walk(node) if isinstance(child, ast.Name)}


def _terminal_call_name(node: ast.Call | ast.AST) -> str:
    value = node.func if isinstance(node, ast.Call) else node
    while isinstance(value, ast.Attribute):
        if not isinstance(value.value, ast.Attribute):
            return value.attr
        value = value.value
    return value.id if isinstance(value, ast.Name) else ""


def _unique_nodes(nodes: Sequence[ast.AST]) -> tuple[ast.AST, ...]:
    seen: set[int] = set()
    values: list[ast.AST] = []
    for node in nodes:
        if id(node) not in seen:
            seen.add(id(node))
            values.append(node)
    return tuple(values)


def _record_ref(value: Any, record_type: str) -> bool:
    return (
        isinstance(value, Mapping)
        and value.get("record_type") == record_type
        and isinstance(value.get("record_id"), str)
    )


def _validate_protocol_artifact(value: Mapping[str, Any], kind: str) -> dict[str, Any]:
    artifact = deepcopy(dict(value))
    if (
        artifact.get("artifact_kind") != kind
        or not isinstance(artifact.get("artifact_id"), str)
        or not isinstance(artifact.get("created_at"), str)
        or not isinstance(artifact.get("payload"), Mapping)
        or not isinstance(artifact.get("content_digest"), str)
    ):
        raise AnalysisMethodQualificationError(f"Malformed {kind} artifact.")
    _timestamp(str(artifact["created_at"]))
    digest = artifact.pop("content_digest")
    if digest != semantic_digest(artifact):
        raise AnalysisMethodQualificationError(f"{kind} artifact digest does not verify.")
    artifact["content_digest"] = digest
    return artifact


def _validate_assignment_protocol(
    profile: Mapping[str, Any], assignment: Mapping[str, Any]
) -> None:
    protocol = profile.get("selection_protocol_artifact")
    payload = assignment.get("payload")
    if (
        not isinstance(protocol, Mapping)
        or not isinstance(payload, Mapping)
        or payload.get("selection_protocol_artifact_id") != protocol.get("artifact_id")
        or payload.get("selection_protocol_artifact_digest") != protocol.get("content_digest")
    ):
        raise AnalysisMethodQualificationError("Assignment does not bind the frozen protocol.")


def _selected_report_path(assignment: Mapping[str, Any]) -> str:
    payload = assignment.get("payload")
    selected = payload.get("selected_report_path") if isinstance(payload, Mapping) else None
    if not isinstance(selected, str):
        raise AnalysisMethodQualificationError("Assignment has no selected report path.")
    return _safe_relative(selected)


def _chronology(
    profile: Mapping[str, Any],
    assignment: Mapping[str, Any],
    label: Mapping[str, Any],
    proof_frozen_at: str,
) -> dict[str, Any]:
    if not (
        _timestamp(str(profile["frozen_at"]))
        < _timestamp(str(assignment["created_at"]))
        < _timestamp(str(label["created_at"]))
        < _timestamp(proof_frozen_at)
    ):
        raise AnalysisMethodQualificationError("Qualification chronology is not strictly ordered.")
    return {
        "profile_frozen_at": str(profile["frozen_at"]),
        "case_assigned_at": str(assignment["created_at"]),
        "label_frozen_at": str(label["created_at"]),
        "proof_frozen_at": proof_frozen_at,
        "detector_dispatched_at": None,
        "stage3_started_at": None,
    }


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
    edges = (
        [
            {"from_node_id": node["node_id"], "to_node_id": fact_id, "relation": "derives"}
            for node in nodes
            if node["node_kind"] == "raw_byte_source"
        ]
        if fact_id is not None
        else []
    )
    return {
        "nodes": sorted(nodes, key=lambda item: str(item["node_id"])),
        "edges": sorted(edges, key=lambda item: str(item["from_node_id"])),
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


def _check_elapsed(profile: Mapping[str, Any], started: int) -> None:
    elapsed_ms = (time.monotonic_ns() - started) // 1_000_000
    if elapsed_ms > int(profile["budgets"]["max_elapsed_milliseconds"]):
        raise _Unavailable("candidate_enumeration_complete", "Elapsed-time budget exceeded.")


def _bound_records(
    records: Sequence[Mapping[str, Any]], record_type: str, identity_field: str
) -> list[dict[str, Any]]:
    values = [_bound_record(record, record_type, identity_field) for record in records]
    identities = [str(item["record_ref"]["record_id"]) for item in values]
    if len(identities) != len(set(identities)):
        raise AnalysisMethodQualificationError(f"Duplicate {record_type} identity.")
    return sorted(values, key=lambda item: str(item["record_ref"]["record_id"]))


def _bound_record(
    record: Mapping[str, Any], record_type: str, identity_field: str
) -> dict[str, Any]:
    if record.get("record_type") != record_type or not isinstance(record.get(identity_field), str):
        raise AnalysisMethodQualificationError(f"Expected one exact {record_type} record.")
    return {
        "record_ref": {"record_type": record_type, "record_id": str(record[identity_field])},
        "semantic_digest": semantic_digest(record),
    }


def _bound_private_manifests(
    records: Sequence[Mapping[str, Any]], manifest_kind: str, identity_field: str
) -> list[dict[str, str]]:
    values: list[dict[str, str]] = []
    for record in records:
        identity = record.get(identity_field)
        if not isinstance(identity, str) or not identity:
            raise AnalysisMethodQualificationError(f"Expected one exact {manifest_kind} record.")
        values.append(
            {
                "manifest_kind": manifest_kind,
                "manifest_id": identity,
                "semantic_digest": semantic_digest(record),
            }
        )
    identities = [item["manifest_id"] for item in values]
    if len(identities) != len(set(identities)):
        raise AnalysisMethodQualificationError(f"Duplicate {manifest_kind} identity.")
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
    value = semantic_digest(basis)
    if not isinstance(value, str):
        raise AnalysisMethodQualificationError("Semantic digest helper returned a non-string.")
    return value


def _safe_relative(value: str) -> str:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or value != path.as_posix():
        raise AnalysisMethodQualificationError("Qualification path is not safely relative.")
    return value


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise AnalysisMethodQualificationError(f"Invalid timestamp {value!r}.") from error
    if parsed.tzinfo is None:
        raise AnalysisMethodQualificationError("Qualification timestamps require a timezone.")
    return parsed


def _provenance(created_at: str, method: str) -> dict[str, Any]:
    return {
        "actor": {
            "actor_kind": "controller",
            "actor_id": "software:sc-referee-eval-static-method-verifier",
            "display_name": "independent static method qualification verifier",
        },
        "method": method,
        "created_at": created_at,
        "tool": "sc-referee-eval",
        "tool_version": "0.2.0",
    }
