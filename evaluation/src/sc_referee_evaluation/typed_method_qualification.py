from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Literal, Protocol

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest, stable_id
from sc_referee.version import SCHEMA_VERSION
from sc_referee_evaluation.snapshot_evidence import (
    SnapshotEvidenceError,
    read_full_digest_snapshot_file,
    validate_content_addressed_snapshot,
)

OperandKind = Literal["canonical_scalar", "unique_string_array", "ordered_step_names"]
ComparisonForm = Literal["value_equals", "set_relation", "step_precedes"]
EvidencePlane = Literal["reported_text", "static_source"]

_RELATION_KIND: dict[ComparisonForm, OperandKind] = {
    "value_equals": "canonical_scalar",
    "set_relation": "unique_string_array",
    "step_precedes": "ordered_step_names",
}
_FINITE_COUNTEREVIDENCE = {
    "approved_method_deviation",
    "governing_protocol_amendment",
    "method_obligation_applicability",
}
_PROFILE_KIND = "typed_static_method_conflict_v1"
_VERIFIER_ENTRY_POINT = "sc_referee_evaluation.typed_method_qualification:verify_typed_method_case"
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


class TypedMethodQualificationError(ValueError):
    """A typed qualification binding or independently derived proof is malformed."""


@dataclass(frozen=True)
class IndependentDeclaration:
    evidence_plane: EvidencePlane
    path: str
    start_line: int
    end_line: int
    retained_text: str

    def __post_init__(self) -> None:
        if (
            not self.path
            or self.start_line < 1
            or self.end_line < self.start_line
            or not self.retained_text
        ):
            raise TypedMethodQualificationError("independent declaration location is incomplete")

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_plane": self.evidence_plane,
            "path": self.path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "retained_text": self.retained_text,
        }


@dataclass(frozen=True)
class IndependentObservation:
    evidence_plane: EvidencePlane
    operand_kind: OperandKind
    operand: object
    declarations: tuple[IndependentDeclaration, ...]
    candidate_paths: tuple[str, ...]
    scope_join_path: tuple[Mapping[str, Any], ...]

    def __post_init__(self) -> None:
        _typed_operand(self.operand_kind, self.operand, requirement=False)
        if not self.declarations or any(
            item.evidence_plane != self.evidence_plane for item in self.declarations
        ):
            raise TypedMethodQualificationError(
                "independent declarations must be non-empty and plane-consistent"
            )
        if (
            not self.candidate_paths
            or len(self.candidate_paths) != len(set(self.candidate_paths))
            or tuple(sorted(self.candidate_paths)) != self.candidate_paths
        ):
            raise TypedMethodQualificationError(
                "independent candidate paths must be non-empty, unique, and sorted"
            )
        if not self.scope_join_path:
            raise TypedMethodQualificationError("independent selected-output scope is unavailable")

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_plane": self.evidence_plane,
            "operand": {"kind": self.operand_kind, "value": self.operand},
            "declarations": [item.to_dict() for item in self.declarations],
            "candidate_paths": list(self.candidate_paths),
            "scope_join_path": [dict(item) for item in self.scope_join_path],
            "scope_join_digest": semantic_digest([dict(item) for item in self.scope_join_path]),
        }


class IndependentQualificationAdapter(Protocol):
    @property
    def adapter_id(self) -> str: ...

    @property
    def adapter_version(self) -> str: ...

    @property
    def implementation_digest(self) -> str: ...

    def inspect(
        self,
        retained_bytes: Mapping[str, bytes],
        assignment: Mapping[str, Any],
        binding: Mapping[str, Any],
    ) -> tuple[IndependentObservation, ...]: ...


def inspect_with_independent_adapter(
    *,
    adapter: IndependentQualificationAdapter,
    retained_bytes: Mapping[str, bytes],
    assignment: Mapping[str, Any],
    binding: Mapping[str, Any],
) -> tuple[IndependentObservation, ...]:
    """Run one explicitly bound answer-side adapter over retained bytes only."""

    qualification_adapter = binding.get("qualification_adapter")
    if (
        not isinstance(qualification_adapter, Mapping)
        or qualification_adapter.get("adapter_id") != adapter.adapter_id
        or qualification_adapter.get("adapter_version") != adapter.adapter_version
        or qualification_adapter.get("implementation_digest") != adapter.implementation_digest
        or not adapter.adapter_id.startswith("qualification-adapter:")
    ):
        raise TypedMethodQualificationError("qualification adapter identity drifted")
    observations = adapter.inspect(retained_bytes, assignment, binding)
    return tuple(sorted(observations, key=lambda item: item.evidence_plane))


def freeze_typed_method_profile(
    *,
    binding: Mapping[str, Any],
    adapter: IndependentQualificationAdapter,
    detector_manifest: Mapping[str, Any],
    parser_manifests: Sequence[Mapping[str, Any]],
    semantic_profile_manifests: Sequence[Mapping[str, Any]],
    version_manifests: Sequence[Mapping[str, Any]],
    selection_protocol_artifact: Mapping[str, Any],
    candidate_suffixes: Sequence[str],
    frozen_at: str,
    max_candidate_files: int = 1_000,
    max_total_bytes: int = 10_000_000,
    max_recursion_depth: int = 32,
    max_elapsed_milliseconds: int = 5_000,
) -> dict[str, Any]:
    """Freeze one content-addressed typed qualification profile before case assignment."""

    normalized = _validate_binding(binding)
    _validate_adapter_identity(adapter, normalized)
    protocol = _protocol_artifact(selection_protocol_artifact, "corpus_selection_protocol")
    if _timestamp(frozen_at) < _timestamp(str(protocol["created_at"])):
        raise TypedMethodQualificationError("typed profile predates its selection protocol")
    suffixes = _canonical_suffixes(candidate_suffixes)
    budgets = {
        "max_candidate_files": max_candidate_files,
        "max_total_bytes": max_total_bytes,
        "max_recursion_depth": max_recursion_depth,
        "max_elapsed_milliseconds": max_elapsed_milliseconds,
    }
    if any(not isinstance(value, int) or value <= 0 for value in budgets.values()):
        raise TypedMethodQualificationError("typed profile budgets must be positive integers")
    detector = deepcopy(dict(detector_manifest))
    implementation = detector.get("implementation")
    if (
        detector.get("record_type") != "detector_manifest"
        or detector.get("detector_id") != normalized["detector_id"]
        or detector.get("detector_version") != normalized["detector_version"]
        or semantic_digest(detector) != normalized["detector_manifest_digest"]
        or not isinstance(implementation, Mapping)
        or implementation.get("deterministic") is not True
        or not isinstance(implementation.get("implementation_digest"), str)
    ):
        raise TypedMethodQualificationError("typed profile detector manifest drifted")
    parsers = _bound_records(parser_manifests, "parser_manifest", "parser_id")
    semantic_profiles = _bound_private_manifests(
        semantic_profile_manifests, "semantic_profile_manifest", "profile_id"
    )
    versions = _bound_private_manifests(
        version_manifests, "version_manifest", "version_manifest_id"
    )
    if not parsers or not semantic_profiles or not versions:
        raise TypedMethodQualificationError("typed profile manifest closure is incomplete")
    verifier_closure = _verifier_dependency_closure(normalized)
    profile: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "static_qualification_profile",
        "profile_kind": _PROFILE_KIND,
        "profile_id": stable_id(
            "static-qualification-profile",
            str(normalized["binding_id"]),
            str(normalized["binding_digest"]),
            semantic_digest(detector),
            semantic_digest(verifier_closure),
            str(protocol["content_digest"]),
            frozen_at,
        ),
        "profile_version": "1.0.0",
        "method_binding": _public_binding(normalized),
        "target_detector": {
            "manifest": _bound_record(detector, "detector_manifest", "detector_id"),
            "detector_id": normalized["detector_id"],
            "detector_version": normalized["detector_version"],
            "implementation_digest": implementation["implementation_digest"],
            "material_premise_class": "static_closed_scope",
            "parser_manifests": parsers,
            "semantic_profile_manifests": semantic_profiles,
            "version_manifests": versions,
        },
        "verifier": {
            "entry_point": _VERIFIER_ENTRY_POINT,
            "implementation_digest": semantic_digest(verifier_closure),
            "dependency_closure": verifier_closure,
            "allowed_shared_utilities": list(_SHARED_UTILITIES),
        },
        "selection_rules": {
            "candidate_suffixes": list(suffixes),
            "candidate_enumeration": "all_matching_regular_files_in_snapshot_sorted_by_path",
            "dependency_closure": ("registered_independent_qualification_adapter_selected_scope"),
            "parser_completeness": "strict_utf8_full_bytes_supported_grammar_or_unavailable",
            "report_path_source": "opaque_case_assignment_manifest",
            "surface_inventory": "every_binding_declared_report_and_static_evidence_plane",
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
        "provenance": _provenance(frozen_at, "deterministic_typed_method_profile_freeze"),
    }
    profile["profile_semantic_digest"] = _self_digest(profile, "profile_semantic_digest")
    return profile


def verify_registered_typed_method_case(
    *,
    workspace_root: Path,
    profile: Mapping[str, Any],
    adapter: IndependentQualificationAdapter,
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
    proof_frozen_at: str,
) -> dict[str, Any]:
    """Independently rederive one typed method proof from retained snapshot bytes."""

    frozen_profile = _validate_typed_profile(
        profile=profile,
        adapter=adapter,
        detector_manifest=detector_manifest,
        parser_manifests=parser_manifests,
        semantic_profile_manifests=semantic_profile_manifests,
        version_manifests=version_manifests,
    )
    binding = frozen_profile["method_binding"]
    assert isinstance(binding, Mapping)
    assignment = _protocol_artifact(case_assignment_artifact, "opaque_case_assignment")
    label = _protocol_artifact(label_freeze_artifact, "scientific_label_freeze")
    _validate_assignment_protocol(frozen_profile, assignment)
    chronology = _chronology(frozen_profile, assignment, label, proof_frozen_at)
    retained, payloads = _retained_candidate_bytes(
        workspace_root,
        snapshot,
        file_records,
        asset_identities,
        frozen_profile,
    )
    authority = _typed_authority(
        binding,
        material_questions,
        answers,
        scientific_contracts,
        semantic_assertions,
    )
    adapter_assignment = _adapter_assignment(assignment, authority, file_records)
    observations = inspect_with_independent_adapter(
        adapter=adapter,
        retained_bytes=payloads,
        assignment=adapter_assignment,
        binding=binding,
    )
    applicability = _applicability_results(observations)
    counterevidence = _counterevidence_results(
        binding,
        authority,
        semantic_assertions,
        observations,
    )
    proof_id = stable_id(
        "static-qualification-proof",
        str(frozen_profile["profile_id"]),
        str(assignment["artifact_id"]),
        str(label["artifact_id"]),
        str(snapshot.get("snapshot_id")),
        semantic_digest(retained),
        proof_frozen_at,
    )
    envelope = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "static_qualification_proof",
        "proof_id": proof_id,
        "profile": _bound_record(frozen_profile, "static_qualification_profile", "profile_id"),
        "case_assignment_artifact": _artifact_ref(assignment),
        "label_freeze_artifact": _artifact_ref(label),
        "snapshot": _bound_record(snapshot, "repository_snapshot", "snapshot_id"),
        "retained_bytes": retained,
        "dependency_graph": _dependency_graph(retained, binding),
        "chronology": chronology,
        "provenance": _provenance(proof_frozen_at, "independent_typed_method_verification"),
    }
    return verify_typed_method_case(
        proof_envelope=envelope,
        binding=binding,
        requirement=authority["requirement"],
        observations=observations,
        applicability_results=applicability,
        counterevidence_results=counterevidence,
        authority_records=authority["bound_records"],
        supported_exclusions=(),
    )


def revalidate_registered_typed_method_proof(
    proof: Mapping[str, Any],
    **inputs: Any,
) -> dict[str, Any]:
    """Rebuild a typed proof and require exact semantic equality."""

    current = deepcopy(dict(proof))
    if (
        current.get("record_type") != "static_qualification_proof"
        or current.get("proof_profile_kind") != _PROFILE_KIND
        or current.get("proof_semantic_digest") != _self_digest(current, "proof_semantic_digest")
    ):
        raise TypedMethodQualificationError("expected one self-verifying typed method proof")
    chronology = current.get("chronology")
    if not isinstance(chronology, Mapping):
        raise TypedMethodQualificationError("typed method proof chronology is absent")
    rebuilt = verify_registered_typed_method_case(
        **inputs,
        proof_frozen_at=str(chronology.get("proof_frozen_at", "")),
    )
    if rebuilt != current:
        raise TypedMethodQualificationError(
            "typed method proof does not replay from its raw and authority inputs"
        )
    return rebuilt


def qualify_typed_method_observations(
    *,
    binding: Mapping[str, Any],
    requirement: object,
    observations: Sequence[IndependentObservation],
    applicability_results: Sequence[Mapping[str, Any]],
    counterevidence_results: Sequence[Mapping[str, Any]],
    authority_records: Mapping[str, Mapping[str, Any]],
    supported_exclusions: Sequence[Mapping[str, str]] = (),
) -> dict[str, Any]:
    """Validate and compare independently extracted operands using the closed algebra."""

    normalized = _validate_binding(binding)
    kind = normalized["operand_kind"]
    relation = normalized["comparison_form"]
    assert isinstance(kind, str) and isinstance(relation, str)
    required_value = _typed_operand(kind, requirement, requirement=True)

    required_planes = normalized["required_evidence_planes"]
    assert isinstance(required_planes, tuple)
    by_plane: dict[str, list[IndependentObservation]] = {
        plane: [item for item in observations if item.evidence_plane == plane]
        for plane in required_planes
    }
    if set(item.evidence_plane for item in observations) != set(required_planes) or any(
        len(items) != 1 for items in by_plane.values()
    ):
        return _unavailable(
            normalized,
            "required_evidence_plane_unique",
            "Every binding-required evidence plane must produce exactly one observation.",
        )
    selected = [by_plane[plane][0] for plane in required_planes]
    if any(item.operand_kind != kind for item in selected):
        return _unavailable(
            normalized,
            "operand_kind_agreement",
            "An independently extracted operand has the wrong closed type.",
        )
    observed_values = [_typed_operand(kind, item.operand, requirement=False) for item in selected]
    if len({canonical_json(value) for value in observed_values}) != 1:
        return _unavailable(
            normalized,
            "observed_plane_agreement",
            "The independently extracted evidence planes disagree.",
        )
    applicability_problem = _incomplete_check(applicability_results, "agreement")
    if applicability_problem is not None:
        return _unavailable(normalized, *applicability_problem)
    counterevidence_problem = _incomplete_check(counterevidence_results, "counterevidence_absent")
    if counterevidence_problem is not None:
        return _unavailable(normalized, *counterevidence_problem)

    observed_value = observed_values[0]
    comparison = _compare(
        relation,
        required_value,
        observed_value,
        forbidden_members=normalized["forbidden_members"],
    )
    authority = _authority_records(authority_records)
    exclusions = _supported_exclusions(supported_exclusions)
    candidate_paths = sorted(
        {path for observation in selected for path in observation.candidate_paths}
    )
    comparison["comparison_form"] = relation
    facts = {
        "binding_id": normalized["binding_id"],
        "binding_digest": normalized["binding_digest"],
        "check_id": normalized["check_id"],
        "dimension": normalized["dimension"],
        "comparison_form": relation,
        "operand_kind": kind,
        "qualification_adapter": deepcopy(normalized["qualification_adapter"]),
        "requirement_operand": {"kind": kind, "value": required_value},
        "observed_operand": {"kind": kind, "value": observed_value},
        "forbidden_members": list(normalized["forbidden_members"]),
        "observations": [item.to_dict() for item in selected],
        "comparison": comparison,
        **authority,
        "candidate_paths": candidate_paths,
        "supported_exclusions": exclusions,
        "production_finding_permitted": False,
    }
    result = {
        "proof_profile_kind": "typed_static_method_conflict_v1",
        "proof_status": "complete",
        "qualification_outcome": comparison["outcome"],
        "derived_facts": facts,
        "limitations": [
            "Independent static qualification does not establish project execution.",
            "The result does not establish numerical causality or universal method adequacy.",
            "An experimental qualification result cannot become a production Finding.",
        ],
    }
    result["proof_semantic_digest"] = semantic_digest(result)
    return result


def verify_typed_method_case(
    *,
    proof_envelope: Mapping[str, Any],
    binding: Mapping[str, Any],
    requirement: object,
    observations: Sequence[IndependentObservation],
    applicability_results: Sequence[Mapping[str, Any]],
    counterevidence_results: Sequence[Mapping[str, Any]],
    authority_records: Mapping[str, Mapping[str, Any]],
    supported_exclusions: Sequence[Mapping[str, str]] = (),
) -> dict[str, Any]:
    """Build one public proof from a caller-validated frozen envelope and independent facts."""

    required_envelope = {
        "schema_version",
        "record_type",
        "proof_id",
        "profile",
        "case_assignment_artifact",
        "label_freeze_artifact",
        "snapshot",
        "retained_bytes",
        "dependency_graph",
        "chronology",
        "provenance",
    }
    forbidden = {
        "proof_profile_kind",
        "proof_status",
        "derived_facts",
        "applicability_results",
        "counterevidence_results",
        "proof_semantic_digest",
        "limitations",
    }
    if set(proof_envelope) != required_envelope or forbidden & set(proof_envelope):
        raise TypedMethodQualificationError("typed proof envelope is incomplete or authoritative")
    if proof_envelope.get("record_type") != "static_qualification_proof":
        raise TypedMethodQualificationError("typed proof envelope has the wrong record type")
    evaluation = qualify_typed_method_observations(
        binding=binding,
        requirement=requirement,
        observations=observations,
        applicability_results=applicability_results,
        counterevidence_results=counterevidence_results,
        authority_records=authority_records,
        supported_exclusions=supported_exclusions,
    )
    proof = deepcopy(dict(proof_envelope))
    proof.update(
        {
            "proof_profile_kind": "typed_static_method_conflict_v1",
            "proof_status": evaluation["proof_status"],
            "derived_facts": evaluation["derived_facts"],
            "applicability_results": [deepcopy(dict(item)) for item in applicability_results],
            "counterevidence_results": [deepcopy(dict(item)) for item in counterevidence_results],
            "limitations": evaluation["limitations"],
            "proof_semantic_digest": "sha256:" + "0" * 64,
        }
    )
    digest_basis = deepcopy(proof)
    digest_basis.pop("proof_semantic_digest")
    proof["proof_semantic_digest"] = semantic_digest(digest_basis)
    return proof


def _validate_binding(binding: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(binding)
    supplied_digest = value.pop("binding_digest", None)
    if supplied_digest != semantic_digest(value):
        raise TypedMethodQualificationError("method-conflict binding digest drifted")
    required_strings = (
        "binding_id",
        "check_id",
        "check_version",
        "check_manifest_digest",
        "detector_id",
        "detector_version",
        "detector_manifest_digest",
        "dimension",
        "comparison_form",
        "operand_kind",
    )
    if any(not isinstance(value.get(field), str) or not value[field] for field in required_strings):
        raise TypedMethodQualificationError("method-conflict binding identity is incomplete")
    relation = value["comparison_form"]
    kind = value["operand_kind"]
    if relation not in _RELATION_KIND or _RELATION_KIND[relation] != kind:
        raise TypedMethodQualificationError("comparison relation and operand kind disagree")
    planes = _unique_strings(value.get("required_evidence_planes"), allow_empty=False)
    if not set(planes).issubset({"reported_text", "static_source"}):
        raise TypedMethodQualificationError("binding evidence plane is unsupported")
    assertion_roles = _unique_strings(value.get("required_assertion_roles"), allow_empty=False)
    expected_roles = {"reported" if plane == "reported_text" else "observed" for plane in planes}
    if set(assertion_roles) != expected_roles:
        raise TypedMethodQualificationError(
            "binding assertion roles do not match its evidence planes"
        )
    semantic_roles = _unique_strings(value.get("required_semantic_roles"), allow_empty=False)
    predicates = _unique_strings(value.get("counterevidence_predicates"), allow_empty=False)
    if set(predicates) != _FINITE_COUNTEREVIDENCE:
        raise TypedMethodQualificationError("finite counterevidence protocol drifted")
    forbidden = _unique_strings(value.get("forbidden_members"), allow_empty=True)
    if relation != "set_relation" and forbidden:
        raise TypedMethodQualificationError("forbidden members require set_relation")
    if value.get("production_finding_permitted") is not False:
        raise TypedMethodQualificationError("qualification binding cannot permit Findings")
    return {
        **value,
        "binding_digest": supplied_digest,
        "required_evidence_planes": tuple(sorted(planes)),
        "required_assertion_roles": tuple(sorted(assertion_roles)),
        "required_semantic_roles": tuple(sorted(semantic_roles)),
        "counterevidence_predicates": tuple(sorted(predicates)),
        "forbidden_members": tuple(sorted(forbidden)),
    }


def _authority_records(
    records: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    expected = {
        "governing_question": "material_question",
        "governing_answer": "answer",
        "governing_contract": "scientific_contract",
        "requirement_assertion": "semantic_assertion",
    }
    if set(records) != set(expected):
        raise TypedMethodQualificationError("qualification authority record set is incomplete")
    normalized: dict[str, dict[str, Any]] = {}
    for name, record_type in expected.items():
        value = records[name]
        ref = value.get("record_ref")
        if (
            not isinstance(ref, Mapping)
            or ref.get("record_type") != record_type
            or not isinstance(ref.get("record_id"), str)
            or not isinstance(value.get("semantic_digest"), str)
        ):
            raise TypedMethodQualificationError(
                f"qualification authority record is malformed: {name}"
            )
        normalized[name] = deepcopy(dict(value))
    return normalized


def _supported_exclusions(
    exclusions: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    normalized = [
        {"path": str(item.get("path", "")), "reason_code": str(item.get("reason_code", ""))}
        for item in exclusions
    ]
    if any(not item["path"] or not item["reason_code"] for item in normalized):
        raise TypedMethodQualificationError("qualification exclusion is malformed")
    canonical = sorted(normalized, key=lambda item: (item["path"], item["reason_code"]))
    if len({canonical_json(item) for item in canonical}) != len(canonical):
        raise TypedMethodQualificationError("qualification exclusions are duplicated")
    return canonical


def _typed_operand(kind: str, value: object, *, requirement: bool) -> object:
    if kind == "canonical_scalar":
        if value is None or isinstance(value, (str, bool)):
            return value
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        if isinstance(value, float) and math.isfinite(value):
            return value
        raise TypedMethodQualificationError("canonical scalar operand is invalid")
    if kind == "unique_string_array":
        return _unique_strings(value, allow_empty=True)
    if kind == "ordered_step_names":
        steps = _unique_strings(value, allow_empty=False, preserve_order=True)
        if requirement and len(steps) != 2:
            raise TypedMethodQualificationError("step_precedes requires exactly two steps")
        return steps
    raise TypedMethodQualificationError("operand kind is unsupported")


def _compare(
    relation: str,
    requirement: object,
    observed: object,
    *,
    forbidden_members: object,
) -> dict[str, Any]:
    if relation == "value_equals":
        equal = canonical_json(requirement) == canonical_json(observed)
        return {
            "outcome": "covered_negative" if equal else "exact_conflict_candidate",
            "values_equal": equal,
        }
    if relation == "set_relation":
        required = set(_unique_strings(requirement, allow_empty=True))
        observed_members = set(_unique_strings(observed, allow_empty=True))
        forbidden = set(_unique_strings(forbidden_members, allow_empty=True))
        if required & forbidden:
            raise TypedMethodQualificationError("required and forbidden set members overlap")
        missing = sorted(required - observed_members)
        present_forbidden = sorted(forbidden & observed_members)
        compatible = not missing and not present_forbidden
        return {
            "outcome": "covered_negative" if compatible else "exact_conflict_candidate",
            "missing_required_members": missing,
            "present_forbidden_members": present_forbidden,
        }
    if relation == "step_precedes":
        required_steps = _unique_strings(requirement, allow_empty=False, preserve_order=True)
        observed_steps = _unique_strings(observed, allow_empty=False, preserve_order=True)
        earlier, later = required_steps
        missing = [step for step in required_steps if step not in observed_steps]
        if missing:
            return {"outcome": "unsupported_path", "missing_steps": missing}
        precedes = observed_steps.index(earlier) < observed_steps.index(later)
        return {
            "outcome": "covered_negative" if precedes else "exact_conflict_candidate",
            "required_order_present": precedes,
        }
    raise TypedMethodQualificationError("comparison relation is unsupported")


def _incomplete_check(
    results: Sequence[Mapping[str, Any]], expected_outcome: str
) -> tuple[str, str] | None:
    if not results:
        return "finite_checks_complete", "A required finite check inventory is absent."
    check_ids = [item.get("check_id") for item in results]
    if any(not isinstance(item, str) or not item for item in check_ids) or len(check_ids) != len(
        set(check_ids)
    ):
        return "finite_checks_complete", "A required finite check inventory is malformed."
    for item in results:
        if item.get("completion_status") != "completed":
            return str(item["check_id"]), "A finite check did not complete."
        if item.get("outcome") != expected_outcome:
            return str(item["check_id"]), "A finite check did not clear the candidate."
    return None


def _unavailable(binding: Mapping[str, Any], check_id: str, reason: str) -> dict[str, Any]:
    result = {
        "proof_profile_kind": "typed_static_method_conflict_v1",
        "proof_status": "unavailable",
        "qualification_outcome": "unavailable",
        "derived_facts": None,
        "failed_check_id": check_id,
        "limitations": [reason],
        "binding_ref": {
            "binding_id": binding["binding_id"],
            "binding_digest": binding["binding_digest"],
        },
    }
    result["proof_semantic_digest"] = semantic_digest(result)
    return result


def _validate_adapter_identity(
    adapter: IndependentQualificationAdapter, binding: Mapping[str, Any]
) -> None:
    expected = binding.get("qualification_adapter")
    if not isinstance(expected, Mapping):
        raise TypedMethodQualificationError("qualification adapter binding is absent")
    closure = expected.get("dependency_closure")
    if (
        expected.get("adapter_id") != adapter.adapter_id
        or expected.get("adapter_version") != adapter.adapter_version
        or expected.get("implementation_digest") != adapter.implementation_digest
        or expected.get("imports_production_semantic_implementation") is not False
        or not isinstance(closure, Sequence)
        or isinstance(closure, (str, bytes))
        or not closure
    ):
        raise TypedMethodQualificationError("qualification adapter identity drifted")


def _public_binding(binding: Mapping[str, Any]) -> dict[str, Any]:
    value = deepcopy(dict(binding))
    for field in (
        "required_evidence_planes",
        "required_assertion_roles",
        "required_semantic_roles",
        "counterevidence_predicates",
        "forbidden_members",
    ):
        value[field] = list(value[field])
    return value


def _verifier_dependency_closure(binding: Mapping[str, Any]) -> list[dict[str, str]]:
    adapter = binding.get("qualification_adapter")
    if not isinstance(adapter, Mapping):
        raise TypedMethodQualificationError("qualification adapter binding is absent")
    raw_closure = adapter.get("dependency_closure")
    if not isinstance(raw_closure, Sequence) or isinstance(raw_closure, (str, bytes)):
        raise TypedMethodQualificationError("qualification adapter closure is malformed")
    dependencies = [
        {
            "dependency_kind": "implementation",
            "path": "sc_referee_evaluation/typed_method_qualification.py",
            "content_digest": sha256_digest(Path(__file__).read_bytes()),
        }
    ]
    for item in raw_closure:
        if not isinstance(item, Mapping):
            raise TypedMethodQualificationError("qualification adapter closure is malformed")
        dependencies.append(
            {
                "dependency_kind": "implementation",
                "path": str(item.get("path", "")),
                "content_digest": str(item.get("content_digest", "")),
            }
        )
    unique = {
        (item["dependency_kind"], item["path"]): item
        for item in dependencies
        if item["path"] and item["content_digest"].startswith("sha256:")
    }
    if len(unique) != len({(item["dependency_kind"], item["path"]) for item in dependencies}):
        raise TypedMethodQualificationError("qualification dependency closure is invalid")
    return [unique[key] for key in sorted(unique)]


def _validate_typed_profile(
    *,
    profile: Mapping[str, Any],
    adapter: IndependentQualificationAdapter,
    detector_manifest: Mapping[str, Any],
    parser_manifests: Sequence[Mapping[str, Any]],
    semantic_profile_manifests: Sequence[Mapping[str, Any]],
    version_manifests: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    value = deepcopy(dict(profile))
    binding_value = value.get("method_binding")
    if not isinstance(binding_value, Mapping):
        raise TypedMethodQualificationError("typed profile binding is absent")
    binding = _validate_binding(binding_value)
    _validate_adapter_identity(adapter, binding)
    detector = deepcopy(dict(detector_manifest))
    implementation = detector.get("implementation")
    target = value.get("target_detector")
    verifier = value.get("verifier")
    rules = value.get("selection_rules")
    vocabulary = value.get("vocabularies")
    budgets = value.get("budgets")
    if not all(
        isinstance(item, Mapping) for item in (target, verifier, rules, vocabulary, budgets)
    ):
        raise TypedMethodQualificationError("typed profile structure is incomplete")
    assert isinstance(target, Mapping)
    assert isinstance(verifier, Mapping)
    assert isinstance(rules, Mapping)
    assert isinstance(vocabulary, Mapping)
    assert isinstance(budgets, Mapping)
    expected_closure = _verifier_dependency_closure(binding)
    if (
        value.get("schema_version") != SCHEMA_VERSION
        or value.get("record_type") != "static_qualification_profile"
        or value.get("profile_kind") != _PROFILE_KIND
        or value.get("profile_version") != "1.0.0"
        or value.get("profile_semantic_digest") != _self_digest(value, "profile_semantic_digest")
        or value.get("method_binding") != _public_binding(binding)
        or detector.get("record_type") != "detector_manifest"
        or semantic_digest(detector) != binding["detector_manifest_digest"]
        or not isinstance(implementation, Mapping)
        or target.get("manifest") != _bound_record(detector, "detector_manifest", "detector_id")
        or target.get("detector_id") != binding["detector_id"]
        or target.get("detector_version") != binding["detector_version"]
        or target.get("implementation_digest") != implementation.get("implementation_digest")
        or target.get("material_premise_class") != "static_closed_scope"
        or target.get("parser_manifests")
        != _bound_records(parser_manifests, "parser_manifest", "parser_id")
        or target.get("semantic_profile_manifests")
        != _bound_private_manifests(
            semantic_profile_manifests, "semantic_profile_manifest", "profile_id"
        )
        or target.get("version_manifests")
        != _bound_private_manifests(version_manifests, "version_manifest", "version_manifest_id")
        or verifier.get("entry_point") != _VERIFIER_ENTRY_POINT
        or verifier.get("dependency_closure") != expected_closure
        or verifier.get("implementation_digest") != semantic_digest(expected_closure)
        or verifier.get("allowed_shared_utilities") != list(_SHARED_UTILITIES)
        or rules.get("candidate_suffixes")
        != list(_canonical_suffixes(rules.get("candidate_suffixes", ())))
        or rules.get("candidate_enumeration")
        != "all_matching_regular_files_in_snapshot_sorted_by_path"
        or rules.get("dependency_closure")
        != "registered_independent_qualification_adapter_selected_scope"
        or rules.get("parser_completeness")
        != "strict_utf8_full_bytes_supported_grammar_or_unavailable"
        or rules.get("report_path_source") != "opaque_case_assignment_manifest"
        or rules.get("surface_inventory")
        != "every_binding_declared_report_and_static_evidence_plane"
        or vocabulary.get("applicability_obligation_ids") != list(_APPLICABILITY_CHECKS)
        or vocabulary.get("counterevidence_check_ids") != list(_COUNTEREVIDENCE_CHECKS)
        or any(not isinstance(item, int) or item <= 0 for item in budgets.values())
    ):
        raise TypedMethodQualificationError("typed profile implementation or envelope drifted")
    return value


def _retained_candidate_bytes(
    workspace_root: Path,
    snapshot: Mapping[str, Any],
    file_records: Sequence[Mapping[str, Any]],
    asset_identities: Sequence[Mapping[str, Any]],
    profile: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, bytes]]:
    try:
        index = validate_content_addressed_snapshot(
            deepcopy(dict(snapshot)),
            [deepcopy(dict(item)) for item in file_records],
            [deepcopy(dict(item)) for item in asset_identities],
        )
    except (SnapshotEvidenceError, KeyError, TypeError, ValueError) as error:
        raise TypedMethodQualificationError(str(error)) from error
    suffixes = tuple(profile["selection_rules"]["candidate_suffixes"])
    budgets = profile["budgets"]
    candidates: list[str] = []
    total_bytes = 0
    for path, record in sorted(index.files_by_path.items()):
        relative = PurePosixPath(path)
        if relative.suffix.casefold() not in suffixes:
            continue
        if record.get("entry_kind") != "regular_file":
            raise TypedMethodQualificationError("typed qualification candidate is not regular")
        if len(relative.parts) > int(budgets["max_recursion_depth"]):
            raise TypedMethodQualificationError("typed qualification recursion budget exceeded")
        candidates.append(path)
        total_bytes += int(record["byte_size"])
    if (
        not candidates
        or len(candidates) > int(budgets["max_candidate_files"])
        or total_bytes > int(budgets["max_total_bytes"])
    ):
        raise TypedMethodQualificationError("typed qualification candidate budget failed")
    root = workspace_root.resolve(strict=True)
    materialized = sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and not path.is_symlink() and path.suffix.casefold() in suffixes
    )
    if materialized != candidates:
        raise TypedMethodQualificationError(
            "typed qualification materialization differs from snapshot candidates"
        )
    retained: list[dict[str, Any]] = []
    payloads: dict[str, bytes] = {}
    for path in candidates:
        try:
            file_record, identity, payload, digest = read_full_digest_snapshot_file(
                index, root, path
            )
            payload.decode("utf-8", errors="strict")
        except (SnapshotEvidenceError, UnicodeDecodeError) as error:
            raise TypedMethodQualificationError(str(error)) from error
        payloads[path] = payload
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
    return retained, payloads


def _typed_authority(
    binding: Mapping[str, Any],
    material_questions: Sequence[Mapping[str, Any]],
    answers: Sequence[Mapping[str, Any]],
    scientific_contracts: Sequence[Mapping[str, Any]],
    semantic_assertions: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    check_id = str(binding["check_id"])
    dimension = str(binding["dimension"])
    relation = str(binding["comparison_form"])
    kind = str(binding["operand_kind"])
    questions = [
        item
        for item in material_questions
        if item.get("record_type") == "material_question"
        and item.get("status") == "answered"
        and item.get("extensions", {}).get("x-scientific-check-id") == check_id
    ]
    if len(questions) != 1:
        raise TypedMethodQualificationError("expected one answered binding-scoped question")
    question = questions[0]
    extensions = question.get("extensions")
    if not isinstance(extensions, Mapping):
        raise TypedMethodQualificationError("typed question extensions are absent")
    subject = extensions.get("x-analysis-subject-ref")
    contract_ref = extensions.get("x-contract-ref")
    scope_path = extensions.get("x-scientific-check-scope-join-path")
    scope_digest = extensions.get("x-scientific-check-scope-join-digest")
    candidates = extensions.get("x-scientific-check-requirement-candidates")
    candidate_values = []
    if isinstance(candidates, Sequence) and not isinstance(candidates, (str, bytes)):
        for candidate in candidates:
            operand = candidate.get("operand") if isinstance(candidate, Mapping) else None
            if isinstance(operand, Mapping) and operand.get("kind") == kind:
                candidate_values.append(operand.get("value"))
    if (
        not _record_ref(subject, "publication_surface")
        or not _record_ref(contract_ref, "scientific_contract")
        or extensions.get("x-output-ceiling") != "question_only"
        or extensions.get("x-posthoc-comparison-forms", {}).get(dimension) != relation
        or not isinstance(scope_path, list)
        or not scope_path
        or semantic_digest(scope_path) != scope_digest
        or not candidate_values
    ):
        raise TypedMethodQualificationError("typed question candidates or scope drifted")
    question_id = str(question.get("question_id", ""))
    matching_answers = [
        item
        for item in answers
        if item.get("record_type") == "answer"
        and item.get("question_ref")
        == {"record_type": "material_question", "record_id": question_id}
    ]
    if len(matching_answers) != 1:
        raise TypedMethodQualificationError("expected one exact typed Answer")
    answer = matching_answers[0]
    answer_basis = deepcopy(dict(answer))
    answer_digest = answer_basis.pop("answer_digest", None)
    requirement = answer.get("answer_value", {}).get(dimension)
    normalized_requirement = _typed_operand(kind, requirement, requirement=True)
    if (
        answer_digest != semantic_digest(answer_basis)
        or not any(
            canonical_json(normalized_requirement)
            == canonical_json(_typed_operand(kind, item, requirement=True))
            for item in candidate_values
        )
        or answer.get("respondent", {}).get("actor_kind") != "human"
        or answer.get("provenance", {}).get("actor", {}).get("actor_kind") != "human"
        or answer.get("authority_scope")
        != {
            "authority_kind": "scientific_intent",
            "subject_refs": [subject],
            "semantic_dimensions": [dimension],
        }
    ):
        raise TypedMethodQualificationError("typed Answer authority or operand drifted")
    assert isinstance(contract_ref, Mapping)
    contracts = [
        item
        for item in scientific_contracts
        if item.get("record_type") == "scientific_contract"
        and item.get("contract_id") == contract_ref.get("record_id")
    ]
    if len(contracts) != 1:
        raise TypedMethodQualificationError("expected one governing typed contract")
    contract = contracts[0]
    slot = contract.get("dimensions", {}).get(dimension)
    if (
        contract.get("scope") != {"level": "analysis", "subject_refs": [subject]}
        or not isinstance(slot, Mapping)
        or slot.get("state") != "known"
        or not isinstance(slot.get("accepted_assertion_ids"), list)
        or not slot["accepted_assertion_ids"]
    ):
        raise TypedMethodQualificationError("typed contract scope or dimension drifted")
    accepted_ids = {str(item) for item in slot["accepted_assertion_ids"]}
    assertions = [
        item
        for item in semantic_assertions
        if item.get("record_type") == "semantic_assertion"
        and item.get("assertion_id") in accepted_ids
        and item.get("predicate") == f"verified_intended_{dimension}"
    ]
    if len(assertions) != 1:
        raise TypedMethodQualificationError("typed requirement assertion is not unique")
    assertion = assertions[0]
    assertion_extensions = assertion.get("extensions")
    if (
        assertion.get("subject_ref") != subject
        or canonical_json(assertion.get("object")) != canonical_json(normalized_requirement)
        or assertion.get("assertion_class") != "deterministic_derivation"
        or assertion.get("epistemic_status") != "accepted"
        or assertion.get("authority_scope") != "scientific_intent"
        or assertion.get("finding_eligibility") != "ineligible"
        or assertion.get("verification", {}).get("status") != "verified"
        or not isinstance(assertion_extensions, Mapping)
        or assertion_extensions.get("x-answer-ref")
        != {"record_type": "answer", "record_id": answer.get("answer_id")}
        or assertion_extensions.get("x-answer-digest") != answer_digest
        or assertion_extensions.get("x-scientific-check-id") != check_id
        or assertion_extensions.get("x-scientific-check-scope-join-digest") != scope_digest
    ):
        raise TypedMethodQualificationError("typed requirement assertion authority drifted")
    return {
        "requirement": normalized_requirement,
        "subject": deepcopy(subject),
        "scope_path": deepcopy(scope_path),
        "scope_digest": scope_digest,
        "requirement_assertion_id": assertion["assertion_id"],
        "bound_records": {
            "governing_question": _bound_record(question, "material_question", "question_id"),
            "governing_answer": _bound_record(answer, "answer", "answer_id"),
            "governing_contract": _bound_record(contract, "scientific_contract", "contract_id"),
            "requirement_assertion": _bound_record(assertion, "semantic_assertion", "assertion_id"),
        },
    }


def _adapter_assignment(
    assignment: Mapping[str, Any],
    authority: Mapping[str, Any],
    file_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    payload = assignment.get("payload")
    if not isinstance(payload, Mapping):
        raise TypedMethodQualificationError("typed assignment payload is absent")
    selected_report = _safe_path(payload.get("selected_report_path"))
    scope_path = authority["scope_path"]
    first = scope_path[0]
    source_ref = first.get("source_ref") if isinstance(first, Mapping) else None
    source_id = (
        source_ref.get("record_id")
        if isinstance(source_ref, Mapping) and source_ref.get("record_type") == "file_record"
        else None
    )
    source_paths = [
        str(item.get("path"))
        for item in file_records
        if item.get("file_record_id") == source_id and isinstance(item.get("path"), str)
    ]
    if len(source_paths) != 1:
        raise TypedMethodQualificationError("typed scope source does not resolve uniquely")
    return {
        "selected_report_path": selected_report,
        "scope_source_path": source_paths[0],
        "scope_artifact_path": selected_report,
        "scope_join_path": deepcopy(scope_path),
        "scope_join_digest": authority["scope_digest"],
    }


def _applicability_results(
    observations: Sequence[IndependentObservation],
) -> list[dict[str, Any]]:
    paths = sorted({path for item in observations for path in item.candidate_paths})
    return [
        _check_result(check_id, "agreement", paths, "closed_search_complete")
        for check_id in _APPLICABILITY_CHECKS
    ]


def _counterevidence_results(
    binding: Mapping[str, Any],
    authority: Mapping[str, Any],
    semantic_assertions: Sequence[Mapping[str, Any]],
    observations: Sequence[IndependentObservation],
) -> list[dict[str, Any]]:
    subject = authority["subject"]
    same_subject = [
        item
        for item in semantic_assertions
        if item.get("record_type") == "semantic_assertion"
        and item.get("epistemic_status") == "accepted"
        and item.get("subject_ref") == subject
    ]
    dimension = str(binding["dimension"])
    requirement_id = authority["requirement_assertion_id"]
    by_check = {
        "alternate_or_superseding_intent": [
            item
            for item in same_subject
            if item.get("predicate") == f"verified_intended_{dimension}"
            and item.get("assertion_id") != requirement_id
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
        "governing_protocol_amendment": [
            item for item in same_subject if item.get("predicate") == "governing_protocol_amendment"
        ],
        "sensitivity_or_unsupported_qualifier": [
            item
            for item in semantic_assertions
            if item.get("epistemic_status") == "accepted"
            and item.get("extensions", {}).get("x-scientific-check-id") == binding["check_id"]
            and item.get("extensions", {}).get("x-scientific-check-scope-join-digest")
            == authority["scope_digest"]
            and (
                item.get("extensions", {}).get("x-sensitivity-only") is True
                or bool(item.get("extensions", {}).get("x-unsupported-method-constructs"))
            )
        ],
    }
    default_paths = sorted({path for item in observations for path in item.candidate_paths})
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
            _check_result(
                check_id,
                "counterevidence_present" if matches else "counterevidence_absent",
                paths or default_paths,
                "counterevidence_present" if matches else "closed_search_complete",
            )
        )
    return results


def _check_result(
    check_id: str, outcome: str, paths: Sequence[str], detail_code: str
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "completion_status": "completed",
        "outcome": outcome,
        "evidence_paths": sorted(set(paths)),
        "detail_code": detail_code,
    }


def _dependency_graph(
    retained: Sequence[Mapping[str, Any]], binding: Mapping[str, Any]
) -> dict[str, Any]:
    adapter = binding["qualification_adapter"]
    adapter_node = "node:qualification-adapter"
    nodes = [
        {
            "node_id": adapter_node,
            "node_kind": "dependency",
            "path": adapter["entry_point"],
            "semantic_digest": adapter["implementation_digest"],
        }
    ]
    edges = []
    for index, item in enumerate(retained, start=1):
        node_id = f"node:retained:{index}"
        nodes.append(
            {
                "node_id": node_id,
                "node_kind": "raw_byte_source",
                "path": item["path"],
                "semantic_digest": item["content_digest"],
            }
        )
        edges.append({"from_node_id": node_id, "to_node_id": adapter_node, "relation": "reads"})
    return {"nodes": nodes, "edges": edges}


def _bound_record(
    record: Mapping[str, Any], record_type: str, identity_field: str
) -> dict[str, Any]:
    if record.get("record_type") != record_type or not isinstance(record.get(identity_field), str):
        raise TypedMethodQualificationError(f"invalid {record_type} binding input")
    return {
        "record_ref": {
            "record_type": record_type,
            "record_id": record[identity_field],
        },
        "semantic_digest": semantic_digest(record),
    }


def _bound_records(
    records: Sequence[Mapping[str, Any]], record_type: str, identity_field: str
) -> list[dict[str, Any]]:
    values = [_bound_record(item, record_type, identity_field) for item in records]
    return sorted(values, key=lambda item: str(item["record_ref"]["record_id"]))


def _bound_private_manifests(
    records: Sequence[Mapping[str, Any]], manifest_kind: str, identity_field: str
) -> list[dict[str, Any]]:
    values = []
    for record in records:
        identity = record.get(identity_field)
        if not isinstance(identity, str) or not identity:
            raise TypedMethodQualificationError("private manifest identity is invalid")
        values.append(
            {
                "manifest_kind": manifest_kind,
                "manifest_id": identity,
                "semantic_digest": semantic_digest(record),
            }
        )
    return sorted(values, key=lambda item: str(item["manifest_id"]))


def _protocol_artifact(value: Mapping[str, Any], expected_kind: str) -> dict[str, Any]:
    artifact = deepcopy(dict(value))
    supplied = artifact.pop("content_digest", None)
    if (
        value.get("artifact_kind") != expected_kind
        or not isinstance(value.get("artifact_id"), str)
        or supplied != semantic_digest(artifact)
        or not isinstance(value.get("payload"), Mapping)
    ):
        raise TypedMethodQualificationError("qualification protocol artifact drifted")
    _timestamp(str(value.get("created_at", "")))
    return deepcopy(dict(value))


def _artifact_ref(artifact: Mapping[str, Any]) -> dict[str, str]:
    return {
        "artifact_kind": str(artifact["artifact_kind"]),
        "artifact_id": str(artifact["artifact_id"]),
        "content_digest": str(artifact["content_digest"]),
    }


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
        or not isinstance(payload.get("selected_report_path"), str)
    ):
        raise TypedMethodQualificationError("typed assignment is not profile-bound")


def _chronology(
    profile: Mapping[str, Any],
    assignment: Mapping[str, Any],
    label: Mapping[str, Any],
    proof_frozen_at: str,
) -> dict[str, Any]:
    times = [
        _timestamp(str(profile.get("frozen_at", ""))),
        _timestamp(str(assignment.get("created_at", ""))),
        _timestamp(str(label.get("created_at", ""))),
        _timestamp(proof_frozen_at),
    ]
    if not times[0] < times[1] < times[2] < times[3]:
        raise TypedMethodQualificationError("typed proof chronology is invalid")
    return {
        "profile_frozen_at": str(profile["frozen_at"]),
        "case_assigned_at": str(assignment["created_at"]),
        "label_frozen_at": str(label["created_at"]),
        "proof_frozen_at": proof_frozen_at,
        "detector_dispatched_at": None,
        "stage3_started_at": None,
    }


def _canonical_suffixes(value: object) -> tuple[str, ...]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or not value
        or not all(isinstance(item, str) and item.startswith(".") for item in value)
    ):
        raise TypedMethodQualificationError("typed candidate suffixes are invalid")
    suffixes = tuple(sorted(str(item).casefold() for item in value))
    if len(suffixes) != len(set(suffixes)):
        raise TypedMethodQualificationError("typed candidate suffixes are duplicated")
    return suffixes


def _safe_path(value: object) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise TypedMethodQualificationError("qualification path is invalid")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != value:
        raise TypedMethodQualificationError("qualification path is unsafe")
    return value


def _record_ref(value: object, record_type: str) -> bool:
    return (
        isinstance(value, Mapping)
        and value.get("record_type") == record_type
        and isinstance(value.get("record_id"), str)
        and bool(value["record_id"])
    )


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise TypedMethodQualificationError("qualification timestamp is invalid") from error
    if parsed.tzinfo is None:
        raise TypedMethodQualificationError("qualification timestamp must include a timezone")
    return parsed


def _self_digest(value: Mapping[str, Any], field: str) -> str:
    basis = deepcopy(dict(value))
    basis.pop(field, None)
    return semantic_digest(basis)


def _provenance(created_at: str, method: str) -> dict[str, Any]:
    return {
        "actor": {
            "actor_kind": "controller",
            "actor_id": "software:sc-referee-eval",
            "display_name": "sc-referee evaluation controller",
        },
        "method": method,
        "created_at": created_at,
        "tool": "sc-referee-eval",
        "tool_version": "0.7.0",
    }


def _unique_strings(value: object, *, allow_empty: bool, preserve_order: bool = False) -> list[str]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or not all(isinstance(item, str) and item for item in value)
    ):
        raise TypedMethodQualificationError("string collection is invalid")
    values = list(value)
    if len(values) != len(set(values)) or (not allow_empty and not values):
        raise TypedMethodQualificationError("string collection must be unique and non-empty")
    return values if preserve_order else sorted(values)
