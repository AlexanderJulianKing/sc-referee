from __future__ import annotations

import copy
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import PurePosixPath
from typing import Any

from sc_referee.core.ids import canonical_json, semantic_digest, stable_id
from sc_referee.method_contracts import SCIENTIFIC_CONTRACT_DIMENSIONS
from sc_referee.posthoc_method_ledger import (
    POSTHOC_METHOD_LEDGER_MANIFEST,
    POSTHOC_METHOD_LEDGER_PROFILE,
    POSTHOC_METHOD_LEDGER_VERSION,
    validate_posthoc_requirement,
)
from sc_referee.records.observed import controller_provenance, typed_ref
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.scientific_checks.core import CheckManifest, RequirementCandidate
from sc_referee.scientific_checks.profiles import default_scientific_check_registry
from sc_referee.scientific_checks.registry import ScientificCheckRegistry
from sc_referee.version import SCHEMA_VERSION, __version__

SCIENTIFIC_REQUIREMENT_PROFILE_ID = "scientific_check_requirement_v1"
SCIENTIFIC_REQUIREMENT_PROFILE_VERSION = "1.1.0"
MULTIPLE_TESTING_SCIENTIFIC_REQUIREMENT_PROFILE_VERSION = "1.2.0"
LEGACY_SCIENTIFIC_REQUIREMENT_PROFILE_VERSION = "1.0.0"
ANSWER_DIGEST_PROFILE = "canonical-json-excluding-answer-digest-v1"
DRAFT_PROVENANCE_EXTENSION_KEY = "x-method-profile-draft-provenance"
_DEPENDENCE_CHECK_ID = "check:authorized-independent-unit-entry-into-row-independent-procedure"
_DEPENDENCE_CANDIDATE_ID = "one-analyzed-row-per-authorized-independent-unit"
_UNIT_AUTHORITY_ROLE = "authorized_independent_unit_key"
_MULTIPLE_TESTING_CHECK_ID = "check:authorized-complete-family-correction-over-code-test-battery"
_MULTIPLE_TESTING_CANDIDATE_ID = "complete-correction-over-authorized-outcome-family"
_MULTIPLE_TESTING_AUTHORITY_ROLE = "authorized_test_family"
_MULTIPLE_TESTING_FAMILY_MEMBER_RULE = "one-two-group-test-per-named-outcome-column"
_MULTIPLE_TESTING_CORRECTION_SCOPE = "complete-authorized-family"
_SAFE_AUTHORITY_SEGMENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
_SAFE_AUTHORITY_COLUMN = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,127}\Z")


class ScientificRequirementContractError(ValueError):
    """Raised when a pre-analysis scientific requirement is incomplete or drifted."""


@dataclass(frozen=True)
class ResolvedScientificRequirement:
    check_manifest: dict[str, Any]
    check_manifest_digest: str
    candidate: dict[str, Any]
    profile_version: str = SCIENTIFIC_REQUIREMENT_PROFILE_VERSION
    semantic_role_authority: dict[str, Any] | None = None
    authority_binding_snapshot: dict[str, Any] | None = None

    @property
    def check_id(self) -> str:
        return str(self.check_manifest["check_id"])

    @property
    def check_version(self) -> str:
        return str(self.check_manifest["check_version"])

    @property
    def dimension(self) -> str:
        return str(self.check_manifest["dimension"])

    @property
    def comparison_form(self) -> str:
        return str(self.check_manifest["comparison_form"])

    @property
    def candidate_id(self) -> str:
        return str(self.candidate["candidate_id"])

    @property
    def value(self) -> object:
        operand = self.candidate["operand"]
        assert isinstance(operand, Mapping)
        return copy.deepcopy(operand["value"])

    @property
    def manifest(self) -> dict[str, Any]:
        value = {
            "profile_id": SCIENTIFIC_REQUIREMENT_PROFILE_ID,
            "profile_version": self.profile_version,
            "check_manifest": copy.deepcopy(self.check_manifest),
            "check_manifest_digest": self.check_manifest_digest,
            "selected_candidate": copy.deepcopy(self.candidate),
            "posthoc_method_ledger": {
                "profile_id": POSTHOC_METHOD_LEDGER_PROFILE,
                "profile_version": POSTHOC_METHOD_LEDGER_VERSION,
                "manifest_digest": semantic_digest(POSTHOC_METHOD_LEDGER_MANIFEST),
            },
        }
        if self.profile_version == SCIENTIFIC_REQUIREMENT_PROFILE_VERSION:
            value["semantic_role_authority"] = copy.deepcopy(self.semantic_role_authority or {})
            value["authority_binding_snapshot"] = copy.deepcopy(
                self.authority_binding_snapshot or {}
            )
        elif self.profile_version == MULTIPLE_TESTING_SCIENTIFIC_REQUIREMENT_PROFILE_VERSION:
            value["semantic_role_authority"] = copy.deepcopy(self.semantic_role_authority or {})
            value["authority_binding_snapshot"] = copy.deepcopy(
                self.authority_binding_snapshot or {}
            )
        return value

    def with_authority_binding_snapshot(
        self, snapshot: Mapping[str, Any]
    ) -> ResolvedScientificRequirement:
        if self.profile_version not in {
            SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
            MULTIPLE_TESTING_SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
        }:
            raise ScientificRequirementContractError(
                "legacy scientific requirement cannot bind semantic-role authority"
            )
        return replace(self, authority_binding_snapshot=copy.deepcopy(dict(snapshot)))


def is_scientific_requirement_profile(profile: object) -> bool:
    return isinstance(profile, Mapping) and profile.get("profile_id") == (
        SCIENTIFIC_REQUIREMENT_PROFILE_ID
    )


def _has_semantic_role_authority(profile_version: str) -> bool:
    return profile_version == SCIENTIFIC_REQUIREMENT_PROFILE_VERSION or profile_version == (
        MULTIPLE_TESTING_SCIENTIFIC_REQUIREMENT_PROFILE_VERSION
    )


def resolve_scientific_requirement_profile(
    profile: object,
    *,
    registry: ScientificCheckRegistry | None = None,
) -> ResolvedScientificRequirement:
    """Resolve one human check/candidate selection through the installed closed registry."""

    if not isinstance(profile, Mapping):
        raise ScientificRequirementContractError("scientific requirement profile must be an object")
    profile_version = profile.get("profile_version")
    if profile_version == SCIENTIFIC_REQUIREMENT_PROFILE_VERSION:
        expected_keys = {
            "profile_id",
            "profile_version",
            "check_id",
            "candidate_id",
            "semantic_role_authority",
        }
    elif profile_version == MULTIPLE_TESTING_SCIENTIFIC_REQUIREMENT_PROFILE_VERSION:
        expected_keys = {
            "profile_id",
            "profile_version",
            "check_id",
            "candidate_id",
            "semantic_role_authority",
        }
    elif profile_version == LEGACY_SCIENTIFIC_REQUIREMENT_PROFILE_VERSION:
        expected_keys = {"profile_id", "profile_version", "check_id", "candidate_id"}
    else:
        raise ScientificRequirementContractError(
            "unsupported scientific requirement profile version"
        )
    if set(profile) != expected_keys:
        raise ScientificRequirementContractError(
            "scientific requirement profile has the wrong exact versioned field set"
        )
    if profile.get("profile_id") != SCIENTIFIC_REQUIREMENT_PROFILE_ID:
        raise ScientificRequirementContractError("unsupported scientific requirement profile ID")
    check_id = profile.get("check_id")
    candidate_id = profile.get("candidate_id")
    if not isinstance(check_id, str) or not check_id:
        raise ScientificRequirementContractError("check_id must identify one installed check")
    if not isinstance(candidate_id, str) or not candidate_id:
        raise ScientificRequirementContractError(
            "candidate_id must identify one published requirement option"
        )
    active = registry or default_scientific_check_registry()
    module_lane = (
        active.modules_for_lane("development")
        if profile_version == MULTIPLE_TESTING_SCIENTIFIC_REQUIREMENT_PROFILE_VERSION
        and registry is None
        else active.modules
    )
    modules = [module for module in module_lane if module.manifest.check_id == check_id]
    if len(modules) != 1:
        raise ScientificRequirementContractError(
            f"check_id does not resolve to one installed scientific check: {check_id}"
        )
    manifest = modules[0].manifest
    candidates = [
        candidate
        for candidate in manifest.requirement_candidates
        if candidate.candidate_id == candidate_id
    ]
    if len(candidates) != 1:
        raise ScientificRequirementContractError(
            f"candidate_id is not published by {check_id}: {candidate_id}"
        )
    _validate_candidate_against_manifest(manifest, candidates[0])
    authority = (
        _validate_semantic_role_authority(
            profile.get("semantic_role_authority"),
            check_id=check_id,
            candidate_id=candidate_id,
            profile_version=str(profile_version),
        )
        if profile_version
        in {
            SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
            MULTIPLE_TESTING_SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
        }
        else {}
    )
    return ResolvedScientificRequirement(
        check_manifest=manifest.to_dict(),
        check_manifest_digest=manifest.manifest_digest,
        candidate=candidates[0].to_dict(),
        profile_version=str(profile_version),
        semantic_role_authority=authority,
        authority_binding_snapshot={},
    )


def resolved_scientific_requirement_from_lock_profile(
    profile_record: object,
) -> ResolvedScientificRequirement:
    if not isinstance(profile_record, Mapping):
        raise ScientificRequirementContractError("method-contract profile record is malformed")
    manifest = profile_record.get("profile_manifest")
    if not isinstance(manifest, Mapping):
        raise ScientificRequirementContractError("scientific requirement manifest is unavailable")
    profile_version = manifest.get("profile_version")
    if manifest.get("profile_id") != SCIENTIFIC_REQUIREMENT_PROFILE_ID or profile_version not in {
        SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
        MULTIPLE_TESTING_SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
        LEGACY_SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
    }:
        raise ScientificRequirementContractError("scientific requirement manifest identity drifted")
    check_manifest = manifest.get("check_manifest")
    candidate = manifest.get("selected_candidate")
    check_digest = manifest.get("check_manifest_digest")
    ledger = manifest.get("posthoc_method_ledger")
    if (
        not isinstance(check_manifest, Mapping)
        or not isinstance(candidate, Mapping)
        or not isinstance(check_digest, str)
        or semantic_digest(check_manifest) != check_digest
        or ledger
        != {
            "profile_id": POSTHOC_METHOD_LEDGER_PROFILE,
            "profile_version": POSTHOC_METHOD_LEDGER_VERSION,
            "manifest_digest": semantic_digest(POSTHOC_METHOD_LEDGER_MANIFEST),
        }
    ):
        raise ScientificRequirementContractError("scientific requirement manifest content drifted")
    if profile_record.get("profile_manifest_digest") != semantic_digest(manifest):
        raise ScientificRequirementContractError("scientific requirement manifest digest drifted")
    resolved = ResolvedScientificRequirement(
        check_manifest=copy.deepcopy(dict(check_manifest)),
        check_manifest_digest=check_digest,
        candidate=copy.deepcopy(dict(candidate)),
        profile_version=str(profile_version),
        semantic_role_authority=(
            _validate_semantic_role_authority(
                manifest.get("semantic_role_authority"),
                check_id=str(check_manifest.get("check_id", "")),
                candidate_id=str(candidate.get("candidate_id", "")),
                profile_version=str(profile_version),
            )
            if profile_version
            in {
                SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
                MULTIPLE_TESTING_SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
            }
            else {}
        ),
        authority_binding_snapshot=(
            _validate_authority_binding_snapshot(
                manifest.get("authority_binding_snapshot"),
                manifest.get("semantic_role_authority"),
                check_id=str(check_manifest.get("check_id", "")),
                candidate_id=str(candidate.get("candidate_id", "")),
                profile_version=str(profile_version),
            )
            if profile_version
            in {
                SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
                MULTIPLE_TESTING_SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
            }
            else {}
        ),
    )
    _validate_resolved_shape(resolved)
    if (
        profile_record.get("profile_id") != SCIENTIFIC_REQUIREMENT_PROFILE_ID
        or profile_record.get("profile_version") != profile_version
        or profile_record.get("resolution_status") != "resolved"
        or profile_record.get("check_id") != resolved.check_id
        or profile_record.get("candidate_id") != resolved.candidate_id
    ):
        raise ScientificRequirementContractError("scientific requirement lock projection drifted")
    return resolved


def scientific_requirement_lock_profile(
    resolved: ResolvedScientificRequirement,
) -> dict[str, Any]:
    manifest = resolved.manifest
    return {
        "profile_id": SCIENTIFIC_REQUIREMENT_PROFILE_ID,
        "profile_version": resolved.profile_version,
        "profile_manifest": manifest,
        "profile_manifest_digest": semantic_digest(manifest),
        "resolution_status": "resolved",
        "check_id": resolved.check_id,
        "candidate_id": resolved.candidate_id,
    }


def build_scientific_requirement_records(
    *,
    run_id: str,
    created_at: str,
    snapshot_digest: str,
    task_record: Mapping[str, Any],
    task_source_ref: Mapping[str, Any],
    resolved: ResolvedScientificRequirement,
    actor_id: str,
    files_total: int,
    draft_provenance: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a claimless parent contract for one closed scientific-check requirement.

    ``draft_provenance``, when supplied, is one already-validated confirmation record for a
    profile that a deterministic draft step proposed and this named human actor confirmed. It is
    recorded in the contract's open ``x-`` extension surface. It carries no Finding, clearance, or
    authority weight of its own: the confirmed family remains the only authority.
    """

    task_ref = typed_ref("file_record", str(task_record["file_record_id"]))
    contract_id = stable_id(
        "scientific-contract-analysis",
        run_id,
        str(task_source_ref["content_digest"]),
        SCIENTIFIC_REQUIREMENT_PROFILE_ID,
        resolved.check_manifest_digest,
        resolved.candidate_id,
    )
    question_id = stable_id("question-method-contract", run_id, contract_id)
    answer_value = {resolved.dimension: resolved.value}
    if _has_semantic_role_authority(resolved.profile_version):
        answer_value["semantic_role_authority"] = copy.deepcopy(
            resolved.semantic_role_authority or {}
        )
    answer_id = stable_id(
        "answer-method-contract",
        run_id,
        question_id,
        semantic_digest(answer_value),
        actor_id,
    )
    answer: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "answer",
        "answer_id": answer_id,
        "audit_run_id": run_id,
        "question_ref": typed_ref("material_question", question_id),
        "source_snapshot_digest": snapshot_digest,
        "answer_kind": "structured_value",
        "answer_value": copy.deepcopy(answer_value),
        "respondent": {"actor_kind": "human", "actor_id": actor_id},
        "response_source": "provided_answer_file",
        "authority_scope": {
            "authority_kind": "scientific_intent",
            "subject_refs": [typed_ref("scientific_contract", contract_id)],
            "semantic_dimensions": [resolved.dimension],
        },
        "certainty": {
            "level": "explicit",
            "basis": "The named human selected one published closed requirement option.",
        },
        "timestamp_status": "available",
        "answered_at": created_at,
        "supersedes_answer_refs": [],
        "answer_digest_profile": ANSWER_DIGEST_PROFILE,
        "created_at": created_at,
        "provenance": {
            "actor": {"actor_kind": "human", "actor_id": actor_id},
            "method": "scientist_answer",
            "created_at": created_at,
            "tool": "sc-referee",
            "tool_version": __version__,
        },
        "extensions": {
            "x-scientific-check-id": resolved.check_id,
            "x-scientific-check-manifest-digest": resolved.check_manifest_digest,
            "x-selected-candidate-id": resolved.candidate_id,
            **(
                {"x-semantic-role-authority": copy.deepcopy(resolved.semantic_role_authority or {})}
                if _has_semantic_role_authority(resolved.profile_version)
                else {}
            ),
        },
    }
    answer["answer_digest"] = semantic_digest(answer)
    declaration_id = stable_id(
        "assertion-method-contract-declaration", answer_id, resolved.dimension
    )
    declaration = _parent_requirement_assertion(
        assertion_id=declaration_id,
        run_id=run_id,
        contract_id=contract_id,
        resolved=resolved,
        created_at=created_at,
        source_ref=task_source_ref,
        actor_id=actor_id,
        answer=answer,
        declaration_id=None,
    )
    verified = _parent_requirement_assertion(
        assertion_id=stable_id(
            "assertion-verified-method-contract",
            answer_id,
            resolved.dimension,
            canonical_json(resolved.value),
        ),
        run_id=run_id,
        contract_id=contract_id,
        resolved=resolved,
        created_at=created_at,
        source_ref=task_source_ref,
        actor_id=actor_id,
        answer=answer,
        declaration_id=declaration_id,
    )
    dimensions: dict[str, Any] = {}
    for dimension in SCIENTIFIC_CONTRACT_DIMENSIONS:
        if dimension == resolved.dimension:
            dimensions[dimension] = {
                "state": "known",
                "assertion_ids": [declaration_id, verified["assertion_id"]],
                "accepted_assertion_ids": [declaration_id, verified["assertion_id"]],
                "notes": (
                    "Human-declared closed requirement plus a controller-verified derivation; "
                    "neither establishes execution or universal scientific correctness."
                ),
            }
        else:
            dimensions[dimension] = {
                "state": "unknown",
                "reason": "This dimension is outside the selected atomic requirement contract.",
                "searched_source_refs": [copy.deepcopy(dict(task_source_ref))],
            }
    contract = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "scientific_contract",
        "contract_id": contract_id,
        "audit_run_id": run_id,
        "title": f"Claimless scientific requirement for {resolved.check_id}",
        "status": "draft",
        "scope": {"level": "analysis", "subject_refs": [task_ref]},
        "dimensions": dimensions,
        "source_refs": [copy.deepcopy(dict(task_source_ref))],
        "created_at": created_at,
        "notes": (
            "Only one registry-published atomic requirement is frozen. Every unrelated "
            "scientific-contract dimension remains unknown."
        ),
        "extensions": {
            "x-method-contract-lifecycle": "claimless_v1",
            "x-method-profile-id": SCIENTIFIC_REQUIREMENT_PROFILE_ID,
            "x-method-profile-version": resolved.profile_version,
            "x-method-profile-manifest-digest": semantic_digest(resolved.manifest),
            "x-method-profile-resolution-status": "resolved",
            "x-scientific-check-id": resolved.check_id,
            "x-scientific-check-version": resolved.check_version,
            "x-scientific-check-manifest-digest": resolved.check_manifest_digest,
            "x-selected-candidate-id": resolved.candidate_id,
            "x-project-code-executed": False,
            **(
                {DRAFT_PROVENANCE_EXTENSION_KEY: copy.deepcopy(dict(draft_provenance))}
                if draft_provenance is not None
                else {}
            ),
        },
    }
    question = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "material_question",
        "question_id": question_id,
        "audit_run_id": run_id,
        "question": str(resolved.check_manifest["permitted_wording"]),
        "unknown_semantic_dimension": "scientific_contract",
        "why_it_matters": (
            "A later audit can compare an exact observed method operand with this pre-analysis "
            "human requirement without asking the auditor to invent authority after seeing results."
        ),
        "candidate_answers": [
            {
                "answer_id": stable_id("answer-option", question_id, resolved.candidate_id),
                "label": str(resolved.candidate["label"]),
                "value": {
                    "candidate_id": resolved.candidate_id,
                    resolved.dimension: resolved.value,
                },
                "consequence": (
                    "Only this published operand governs the exact later review scope."
                ),
            },
            {
                "answer_id": stable_id("answer-option", question_id, "retain-unknown"),
                "label": "Retain unresolved",
                "value": {"action": "retain_unknown"},
                "consequence": "No later method-compatibility conclusion is available.",
            },
        ],
        "evidence_searched": [
            {
                "source": "installed digest-bound scientific-check registry",
                "result": (
                    f"The controller resolved {resolved.candidate_id} as one option published "
                    f"by {resolved.check_id}; it did not infer or rank that option."
                ),
            }
        ],
        "blocked_detector_ids": ["detector:bounded-analysis-method-conflict"],
        "affected_claim_ids": [],
        "linked_conditional_concern_ids": [],
        "priority": "high",
        "status": "answered",
        "answer_ids": [answer_id],
        "created_at": created_at,
        "provenance": controller_provenance(
            "deterministic_claimless_scientific_requirement_question_v1", created_at
        ),
        "extensions": {
            "x-contract-ref": typed_ref("scientific_contract", contract_id),
            "x-unresolved-dimensions": [resolved.dimension],
            "x-method-profile-id": SCIENTIFIC_REQUIREMENT_PROFILE_ID,
            "x-answer-shape": "one-listed-scientific-check-requirement",
            "x-claimless": True,
            "x-scientific-check-id": resolved.check_id,
            "x-scientific-check-version": resolved.check_version,
            "x-scientific-check-manifest-digest": resolved.check_manifest_digest,
            "x-selected-candidate-id": resolved.candidate_id,
        },
    }
    disclosure = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "disclosure",
        "disclosure_id": stable_id("disclosure-method-contract", run_id, contract_id),
        "audit_run_id": run_id,
        "disclosure_kind": "coverage_gap",
        "title": "Scientific requirement contract has an atomic scope",
        "description": (
            f"This claimless run records one {resolved.check_id} requirement and does not "
            "inspect analysis code, results, or scientific adequacy."
        ),
        "importance": "important",
        "non_accusatory": True,
        "affected_refs": [typed_ref("scientific_contract", contract_id)],
        "source_refs": [copy.deepcopy(dict(task_source_ref))],
        "coverage_status": "partially_covered",
        "interpretive_consequence": (
            "The selection establishes review-scoped human intent only; unrelated dimensions "
            "and later execution remain unknown."
        ),
        "next_step": "Bind this lock to a later audit of the unchanged governing task.",
        "created_at": created_at,
        "provenance": controller_provenance(
            "deterministic_scientific_requirement_contract_disclosure", created_at
        ),
    }
    return {
        "contract": contract,
        "assertions": [declaration, verified],
        "question": question,
        "answers": [answer],
        "disclosure": disclosure,
        "coverage_inputs": {
            "files_total": files_total,
            "task_path": str(task_record["path"]),
            "resolved": True,
            "profile_id": SCIENTIFIC_REQUIREMENT_PROFILE_ID,
            "resolved_dimensions": [resolved.dimension],
            "scope_description": (
                f"one atomic {resolved.check_id} requirement ({resolved.candidate_id})"
            ),
        },
    }


def verify_parent_scientific_requirement(
    locked: Mapping[str, Any], registry: LocalSchemaRegistry
) -> tuple[
    dict[str, Any],
    ResolvedScientificRequirement,
    list[dict[str, Any]],
    dict[str, Any],
]:
    """Verify the complete parent authority chain without consulting mutable project content."""

    resolved = resolved_scientific_requirement_from_lock_profile(
        locked.get("method_contract_profile")
    )
    contracts = _record_list(locked, "scientific_contracts")
    assertions = _record_list(locked, "semantic_assertions")
    answers = _record_list(locked, "answers")
    questions = _record_list(locked, "material_questions")
    if len(contracts) != 1 or len(answers) != 1 or len(questions) != 1:
        raise ScientificRequirementContractError(
            "resolved scientific requirement records are incomplete"
        )
    contract, answer, question = contracts[0], answers[0], questions[0]
    for record in [contract, answer, question, *assertions]:
        registry.validate(record)
    if (
        contract.get("scope", {}).get("level") != "analysis"
        or contract.get("extensions", {}).get("x-method-profile-id")
        != SCIENTIFIC_REQUIREMENT_PROFILE_ID
        or contract.get("extensions", {}).get("x-method-profile-version")
        != resolved.profile_version
        or contract.get("extensions", {}).get("x-method-profile-manifest-digest")
        != semantic_digest(resolved.manifest)
        or contract.get("extensions", {}).get("x-scientific-check-id") != resolved.check_id
        or contract.get("extensions", {}).get("x-scientific-check-manifest-digest")
        != resolved.check_manifest_digest
        or contract.get("extensions", {}).get("x-selected-candidate-id") != resolved.candidate_id
        or contract.get("extensions", {}).get("x-project-code-executed") is not False
        or question.get("status") != "answered"
        or question.get("answer_ids") != [answer.get("answer_id")]
        or answer.get("question_ref")
        != typed_ref("material_question", str(question.get("question_id")))
        or answer.get("authority_scope", {}).get("subject_refs")
        != [typed_ref("scientific_contract", str(contract.get("contract_id")))]
        or answer.get("authority_scope", {}).get("semantic_dimensions") != [resolved.dimension]
        or answer.get("respondent", {}).get("actor_kind") != "human"
        or answer.get("response_source") != "provided_answer_file"
        or answer.get("source_snapshot_digest") != locked.get("snapshot_digest")
        or answer.get("answer_value") != _resolved_answer_value(resolved)
        or (
            _has_semantic_role_authority(resolved.profile_version)
            and answer.get("extensions", {}).get("x-semantic-role-authority")
            != (resolved.semantic_role_authority or {})
        )
    ):
        raise ScientificRequirementContractError(
            "resolved scientific requirement authority or scope is invalid"
        )
    _verify_answer_digest(answer)
    declarations = _matching_parent_assertions(
        assertions, contract, answer, resolved, derived=False
    )
    verified = _matching_parent_assertions(assertions, contract, answer, resolved, derived=True)
    if len(declarations) != 1 or len(verified) != 1:
        raise ScientificRequirementContractError(
            "scientific requirement has no unique declaration and verification pair"
        )
    declaration, derivation = declarations[0], verified[0]
    if (
        declaration.get("object") != resolved.value
        or derivation.get("object") != resolved.value
        or derivation.get("extensions", {}).get("x-original-declaration-ref")
        != typed_ref("semantic_assertion", str(declaration["assertion_id"]))
    ):
        raise ScientificRequirementContractError("scientific requirement assertion values drifted")
    slot = contract.get("dimensions", {}).get(resolved.dimension, {})
    expected_ids = [declaration["assertion_id"], derivation["assertion_id"]]
    if (
        slot.get("assertion_ids") != expected_ids
        or slot.get("accepted_assertion_ids") != expected_ids
    ):
        raise ScientificRequirementContractError(
            "scientific requirement contract does not bind its exact assertion pair"
        )
    return contract, resolved, assertions, answer


def bind_scientific_requirement_to_audit(
    *,
    parent: Mapping[str, Any],
    parent_contract: Mapping[str, Any],
    resolved: ResolvedScientificRequirement,
    parent_answer: Mapping[str, Any],
    current_source_ref: Mapping[str, Any],
    snapshot_record: Mapping[str, Any],
    questions: list[dict[str, Any]],
    answers: list[dict[str, Any]],
    contracts: list[dict[str, Any]],
    assertions: list[dict[str, Any]],
    active_registry: ScientificCheckRegistry,
    schema_registry: LocalSchemaRegistry,
    run_id: str,
    created_at: str,
) -> dict[str, Any]:
    """Bind one frozen requirement to the exact matching current scientific-check question."""

    active_profile: dict[str, Any] = {
        "profile_id": SCIENTIFIC_REQUIREMENT_PROFILE_ID,
        "profile_version": resolved.profile_version,
        "check_id": resolved.check_id,
        "candidate_id": resolved.candidate_id,
    }
    if _has_semantic_role_authority(resolved.profile_version):
        active_profile["semantic_role_authority"] = copy.deepcopy(
            resolved.semantic_role_authority or {}
        )
    active = resolve_scientific_requirement_profile(
        active_profile,
        registry=active_registry,
    )
    active = replace(
        active,
        authority_binding_snapshot=copy.deepcopy(resolved.authority_binding_snapshot or {}),
    )
    if active != resolved and not compatible_dependence_code_lane_requirement(resolved, active):
        raise ScientificRequirementContractError(
            "active scientific check or selected candidate drifted from the frozen contract"
        )
    resolved = active
    candidates = [
        question
        for question in questions
        if question.get("status") == "open"
        and question.get("extensions", {}).get("x-scientific-check-id") == resolved.check_id
        and question.get("extensions", {}).get("x-scientific-check-version")
        == resolved.check_version
        and question.get("extensions", {}).get("x-scientific-check-manifest-digest")
        == resolved.check_manifest_digest
    ]
    if not candidates:
        return {
            "parent_contract_id": str(parent_contract["contract_id"]),
            "parent_semantic_lock_digest": str(parent["semantic_lock_digest"]),
            "parent_snapshot_digest": str(parent["snapshot_digest"]),
            "current_snapshot_digest": str(snapshot_record["snapshot_digest"]),
            "governing_task_path": str(current_source_ref["path"]),
            "governing_task_content_digest": str(current_source_ref["content_digest"]),
            "bound_claim_ids": [],
            "bound_question_ids": [],
            "binding_status": "not_applicable",
            "binding_basis": (
                "The frozen check remains installed and unchanged, but the current immutable "
                "evidence did not produce one applicable question for that check."
            ),
            "profile_id": SCIENTIFIC_REQUIREMENT_PROFILE_ID,
            "profile_version": resolved.profile_version,
            "check_id": resolved.check_id,
            "candidate_id": resolved.candidate_id,
        }
    if len(candidates) != 1:
        raise ScientificRequirementContractError(
            "frozen requirement does not resolve to one applicable current scientific question"
        )
    question = candidates[0]
    extensions = question.get("extensions", {})
    current_candidates = extensions.get("x-scientific-check-requirement-candidates")
    frozen_candidates = resolved.check_manifest.get("requirement_candidates")
    if (
        extensions.get("x-posthoc-comparison-forms")
        != {resolved.dimension: resolved.comparison_form}
        or not isinstance(current_candidates, list)
        or not isinstance(frozen_candidates, list)
        or sorted(current_candidates, key=lambda item: str(item.get("candidate_id")))
        != sorted(frozen_candidates, key=lambda item: str(item.get("candidate_id")))
        or extensions.get("x-output-ceiling") != "question_only"
    ):
        raise ScientificRequirementContractError(
            "current scientific question differs from the frozen closed requirement profile"
        )
    contract_ref = extensions.get("x-contract-ref")
    contract_id = contract_ref.get("record_id") if isinstance(contract_ref, Mapping) else None
    matching_contracts = [item for item in contracts if item.get("contract_id") == contract_id]
    if len(matching_contracts) != 1:
        raise ScientificRequirementContractError(
            "current scientific question has no unique analysis contract"
        )
    contract = matching_contracts[0]
    subject = extensions.get("x-analysis-subject-ref")
    if (
        not isinstance(subject, Mapping)
        or contract.get("scope", {}).get("level") != "analysis"
        or contract.get("scope", {}).get("subject_refs") != [subject]
    ):
        raise ScientificRequirementContractError("current scientific requirement scope drifted")
    parent_digest = str(parent["semantic_lock_digest"])
    answer_value = _resolved_answer_value(resolved)
    answer_id = stable_id(
        "answer-bound-scientific-requirement",
        run_id,
        str(question["question_id"]),
        parent_digest,
        str(parent_answer["answer_id"]),
    )
    answer: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "answer",
        "answer_id": answer_id,
        "audit_run_id": run_id,
        "question_ref": typed_ref("material_question", str(question["question_id"])),
        "source_snapshot_digest": str(snapshot_record["snapshot_digest"]),
        "answer_kind": "structured_value",
        "answer_value": copy.deepcopy(answer_value),
        "respondent": copy.deepcopy(parent_answer["respondent"]),
        "response_source": "prior_scientist_record",
        "authority_scope": {
            "authority_kind": "scientific_intent",
            "subject_refs": [copy.deepcopy(dict(subject))],
            "semantic_dimensions": [resolved.dimension],
        },
        "certainty": copy.deepcopy(parent_answer["certainty"]),
        "timestamp_status": "available",
        "answered_at": str(parent_answer["answered_at"]),
        "supersedes_answer_refs": [],
        "answer_digest_profile": ANSWER_DIGEST_PROFILE,
        "created_at": created_at,
        "provenance": {
            "actor": copy.deepcopy(parent_answer["respondent"]),
            "method": "scientist_answer",
            "created_at": str(parent_answer["answered_at"]),
            "tool": "sc-referee",
            "tool_version": __version__,
        },
        "extensions": {
            "x-parent-answer-ref": typed_ref("answer", str(parent_answer["answer_id"])),
            "x-parent-answer-digest": str(parent_answer["answer_digest"]),
            "x-parent-contract-ref": typed_ref(
                "scientific_contract", str(parent_contract["contract_id"])
            ),
            "x-parent-semantic-lock-digest": parent_digest,
            "x-scientific-check-id": resolved.check_id,
            "x-scientific-check-manifest-digest": resolved.check_manifest_digest,
            "x-selected-candidate-id": resolved.candidate_id,
            **_resolved_authority_extensions(resolved, include_snapshot=True),
        },
    }
    answer["answer_digest"] = semantic_digest(answer)
    scope_digest = str(extensions["x-scientific-check-scope-join-digest"])
    requirement_id = (
        "assertion-verified-posthoc-intent:"
        + stable_id(
            "bound-scientific-requirement",
            run_id,
            str(question["question_id"]),
            parent_digest,
        ).split(":", 1)[1]
    )
    requirement = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "semantic_assertion",
        "assertion_id": requirement_id,
        "audit_run_id": run_id,
        "subject_ref": copy.deepcopy(dict(subject)),
        "predicate": f"verified_intended_{resolved.dimension}",
        "object": resolved.value,
        "semantic_role": "intended",
        "assertion_class": "deterministic_derivation",
        "epistemic_status": "accepted",
        "authority_scope": "scientific_intent",
        "independently_checkable": True,
        "finding_eligibility": "ineligible",
        "verification": {
            "status": "verified",
            "method": "deterministic_comparison",
            "validator_id": "controller:frozen-scientific-requirement-binding-v1",
            "verified_at": created_at,
        },
        "certainty": copy.deepcopy(parent_answer["certainty"]),
        "rationale": (
            "The controller verified the pre-analysis human selection, parent lock digest, "
            "unchanged governing task, current check manifest, candidate value, and exact "
            "selected-analysis scope. This establishes review-scoped intent only."
        ),
        "source_refs": _deduplicate_source_refs(
            [*contract.get("source_refs", []), current_source_ref]
        ),
        "provenance": controller_provenance(
            "deterministic_frozen_scientific_requirement_binding_v1", created_at
        ),
        "extensions": {
            "x-answer-ref": typed_ref("answer", answer_id),
            "x-answer-digest": answer["answer_digest"],
            "x-parent-answer-ref": typed_ref("answer", str(parent_answer["answer_id"])),
            "x-parent-contract-ref": typed_ref(
                "scientific_contract", str(parent_contract["contract_id"])
            ),
            "x-parent-semantic-lock-digest": parent_digest,
            "x-scientific-check-id": resolved.check_id,
            "x-scientific-check-manifest-digest": resolved.check_manifest_digest,
            "x-scientific-check-scope-join-digest": scope_digest,
            "x-selected-candidate-id": resolved.candidate_id,
            **_resolved_authority_extensions(resolved, include_snapshot=True),
            "x-authority-limitation": (
                "Pre-analysis review requirement only; historical intent, execution, numeric "
                "causality, and universal correctness are not established."
            ),
        },
    }
    schema_registry.validate(answer)
    schema_registry.validate(requirement)
    answers.append(answer)
    assertions.append(requirement)
    contract["dimensions"][resolved.dimension] = {
        "state": "known",
        "assertion_ids": [requirement_id],
        "accepted_assertion_ids": [requirement_id],
        "notes": (
            "Bound from an immutable pre-analysis human requirement after exact registry and "
            "task-identity verification."
        ),
    }
    contract.setdefault("extensions", {})["x-method-contract-parent-lock-digest"] = parent_digest
    contract["extensions"]["x-method-profile-resolution-status"] = "resolved"
    contract["extensions"]["x-selected-candidate-id"] = resolved.candidate_id
    question["status"] = "answered"
    question["answer_ids"] = [answer_id]
    question.setdefault("extensions", {})["x-method-contract-parent-lock-digest"] = parent_digest
    question["extensions"]["x-selected-candidate-id"] = resolved.candidate_id
    return {
        "parent_contract_id": str(parent_contract["contract_id"]),
        "parent_semantic_lock_digest": parent_digest,
        "parent_snapshot_digest": str(parent["snapshot_digest"]),
        "current_snapshot_digest": str(snapshot_record["snapshot_digest"]),
        "governing_task_path": str(current_source_ref["path"]),
        "governing_task_content_digest": str(current_source_ref["content_digest"]),
        "bound_claim_ids": [],
        "bound_question_ids": [str(question["question_id"])],
        "binding_status": "bound",
        "profile_id": SCIENTIFIC_REQUIREMENT_PROFILE_ID,
        "profile_version": SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
        "check_id": resolved.check_id,
        "candidate_id": resolved.candidate_id,
    }


def compatible_dependence_code_lane_requirement(
    frozen: ResolvedScientificRequirement,
    active: ResolvedScientificRequirement,
) -> bool:
    """Accept only the ADR-0076 dual-lane migrations through 3.1.0.

    The human-selected operand, authority surface, frozen material binding,
    comparison relation, and candidate remain byte-equivalent.  Adapter,
    semantic-role, and evidence-plane changes are intentionally excluded from
    the authority claim and remain governed by the new check manifest.
    """

    if not (
        frozen.profile_version == SCIENTIFIC_REQUIREMENT_PROFILE_VERSION
        and active.profile_version == SCIENTIFIC_REQUIREMENT_PROFILE_VERSION
        and frozen.check_id == _DEPENDENCE_CHECK_ID == active.check_id
        and frozen.check_version
        in {
            "1.2.0",
            "1.3.0",
            "1.3.1",
            "1.3.2",
            "1.3.3",
            "2.0.0",
            "2.1.0",
            "2.2.0",
            "2.3.0",
            "3.0.0",
            "3.1.0",
        }
        and active.check_version in {"2.1.0", "2.3.0", "3.0.0", "3.1.0"}
        and frozen.candidate_id == _DEPENDENCE_CANDIDATE_ID == active.candidate_id
        and frozen.dimension == active.dimension == "dependence_structure"
        and frozen.comparison_form == active.comparison_form == "value_equals"
        and frozen.value == active.value
        and frozen.candidate == active.candidate
        and frozen.semantic_role_authority == active.semantic_role_authority
        and frozen.authority_binding_snapshot == active.authority_binding_snapshot
    ):
        return False
    frozen_candidates = frozen.check_manifest.get("requirement_candidates")
    active_candidates = active.check_manifest.get("requirement_candidates")
    return bool(
        isinstance(frozen_candidates, list)
        and isinstance(active_candidates, list)
        and frozen_candidates == active_candidates
    )


def _parent_requirement_assertion(
    *,
    assertion_id: str,
    run_id: str,
    contract_id: str,
    resolved: ResolvedScientificRequirement,
    created_at: str,
    source_ref: Mapping[str, Any],
    actor_id: str,
    answer: Mapping[str, Any],
    declaration_id: str | None,
) -> dict[str, Any]:
    derived = declaration_id is not None
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "semantic_assertion",
        "assertion_id": assertion_id,
        "audit_run_id": run_id,
        "subject_ref": typed_ref("scientific_contract", contract_id),
        "predicate": f"{'verified_' if derived else ''}intended_{resolved.dimension}",
        "object": resolved.value,
        "semantic_role": "intended",
        "assertion_class": "deterministic_derivation" if derived else "scientist_declaration",
        "epistemic_status": "accepted",
        "authority_scope": "scientific_intent",
        "independently_checkable": derived,
        "finding_eligibility": "eligible" if derived else "ineligible",
        "verification": {
            "status": "verified",
            "method": "deterministic_comparison" if derived else "scientist_confirmation",
            "validator_id": (
                "controller:claimless-scientific-requirement-answer-v1"
                if derived
                else "controller:claimless-answer-authority-scope-v1"
            ),
            "verified_at": created_at,
        },
        "certainty": copy.deepcopy(answer["certainty"]),
        "rationale": (
            "The controller verified that the human selected one exact candidate published by "
            "the frozen check manifest. This derives governing review intent only."
            if derived
            else "The assertion preserves the human selection without establishing execution or truth."
        ),
        "source_refs": [copy.deepcopy(dict(source_ref))],
        "provenance": (
            controller_provenance(
                "deterministic_claimless_scientific_requirement_derivation_v1", created_at
            )
            if derived
            else {
                "actor": {"actor_kind": "human", "actor_id": actor_id},
                "method": "scientist_answer",
                "created_at": created_at,
                "source_refs": [copy.deepcopy(dict(source_ref))],
                "tool": "sc-referee",
                "tool_version": __version__,
            }
        ),
        "extensions": {
            "x-answer-ref": typed_ref("answer", str(answer["answer_id"])),
            "x-answer-digest": str(answer["answer_digest"]),
            "x-profile-id": SCIENTIFIC_REQUIREMENT_PROFILE_ID,
            "x-profile-version": resolved.profile_version,
            "x-scientific-check-id": resolved.check_id,
            "x-scientific-check-manifest-digest": resolved.check_manifest_digest,
            "x-selected-candidate-id": resolved.candidate_id,
            **_resolved_authority_extensions(resolved, include_snapshot=derived),
            **(
                {"x-original-declaration-ref": typed_ref("semantic_assertion", declaration_id)}
                if declaration_id is not None
                else {}
            ),
            "x-authority-limitation": (
                "Scoped human intent only; execution and general scientific correctness are "
                "not established."
            ),
        },
    }


def _matching_parent_assertions(
    assertions: Sequence[Mapping[str, Any]],
    contract: Mapping[str, Any],
    answer: Mapping[str, Any],
    resolved: ResolvedScientificRequirement,
    *,
    derived: bool,
) -> list[dict[str, Any]]:
    expected_class = "deterministic_derivation" if derived else "scientist_declaration"
    expected_predicate = f"{'verified_' if derived else ''}intended_{resolved.dimension}"
    expected_actor = "controller" if derived else "human"
    return [
        copy.deepcopy(dict(item))
        for item in assertions
        if item.get("predicate") == expected_predicate
        and item.get("subject_ref")
        == typed_ref("scientific_contract", str(contract["contract_id"]))
        and item.get("assertion_class") == expected_class
        and item.get("semantic_role") == "intended"
        and item.get("authority_scope") == "scientific_intent"
        and item.get("independently_checkable") is derived
        and item.get("finding_eligibility") == ("eligible" if derived else "ineligible")
        and item.get("epistemic_status") == "accepted"
        and item.get("extensions", {}).get("x-answer-ref")
        == typed_ref("answer", str(answer["answer_id"]))
        and item.get("extensions", {}).get("x-answer-digest") == answer.get("answer_digest")
        and item.get("extensions", {}).get("x-scientific-check-id") == resolved.check_id
        and item.get("extensions", {}).get("x-scientific-check-manifest-digest")
        == resolved.check_manifest_digest
        and item.get("extensions", {}).get("x-profile-version") == resolved.profile_version
        and (
            not _has_semantic_role_authority(resolved.profile_version)
            or item.get("extensions", {}).get("x-semantic-role-authority")
            == (resolved.semantic_role_authority or {})
        )
        and (
            not _has_semantic_role_authority(resolved.profile_version)
            or (
                item.get("extensions", {}).get("x-authority-binding-snapshot")
                == (resolved.authority_binding_snapshot or {})
                if derived
                else "x-authority-binding-snapshot" not in item.get("extensions", {})
            )
        )
        and item.get("provenance", {}).get("actor", {}).get("actor_kind") == expected_actor
    ]


def _verify_answer_digest(answer: Mapping[str, Any]) -> None:
    value = copy.deepcopy(dict(answer))
    recorded = value.pop("answer_digest", None)
    if not isinstance(recorded, str) or semantic_digest(value) != recorded:
        raise ScientificRequirementContractError("scientific requirement Answer digest mismatch")


def _resolved_answer_value(resolved: ResolvedScientificRequirement) -> dict[str, Any]:
    value: dict[str, Any] = {resolved.dimension: resolved.value}
    if _has_semantic_role_authority(resolved.profile_version):
        value["semantic_role_authority"] = copy.deepcopy(resolved.semantic_role_authority or {})
    return value


def _resolved_authority_extensions(
    resolved: ResolvedScientificRequirement, *, include_snapshot: bool
) -> dict[str, Any]:
    if not _has_semantic_role_authority(resolved.profile_version):
        return {}
    value = {"x-semantic-role-authority": copy.deepcopy(resolved.semantic_role_authority or {})}
    if include_snapshot:
        value["x-authority-binding-snapshot"] = copy.deepcopy(
            resolved.authority_binding_snapshot or {}
        )
    return value


def _validate_candidate_against_manifest(
    manifest: CheckManifest, candidate: RequirementCandidate
) -> None:
    value = validate_posthoc_requirement(
        manifest.dimension, manifest.comparison_form, candidate.operand.value
    )
    if canonical_json(value) != canonical_json(candidate.operand.value):
        raise ScientificRequirementContractError(
            "published requirement candidate is not canonical for its comparison form"
        )


def _validate_semantic_role_authority(
    value: object,
    *,
    check_id: str,
    candidate_id: str,
    profile_version: str,
) -> dict[str, Any]:
    if profile_version == MULTIPLE_TESTING_SCIENTIFIC_REQUIREMENT_PROFILE_VERSION:
        return _validate_multiple_testing_semantic_role_authority(
            value,
            check_id=check_id,
            candidate_id=candidate_id,
        )
    if profile_version != SCIENTIFIC_REQUIREMENT_PROFILE_VERSION:
        raise ScientificRequirementContractError(
            "unsupported scientific requirement profile version"
        )
    if check_id != _DEPENDENCE_CHECK_ID or candidate_id != _DEPENDENCE_CANDIDATE_ID:
        if value != {}:
            raise ScientificRequirementContractError(
                "non-dependence scientific requirements require empty semantic-role authority"
            )
        return {}
    if not isinstance(value, Mapping) or set(value) != {_UNIT_AUTHORITY_ROLE}:
        raise ScientificRequirementContractError(
            "dependence semantic-role authority has the wrong exact role set"
        )
    authority = value.get(_UNIT_AUTHORITY_ROLE)
    if not isinstance(authority, Mapping) or set(authority) != {
        "material_input_path",
        "column_name",
        "group_contrast_column",
    }:
        raise ScientificRequirementContractError(
            "authorized independent-unit authority has the wrong exact field set"
        )
    path = authority.get("material_input_path")
    column = authority.get("column_name")
    group = authority.get("group_contrast_column")
    if not isinstance(path, str) or not _valid_authority_path(path):
        raise ScientificRequirementContractError(
            "authorized independent-unit material path is invalid"
        )
    if not isinstance(column, str) or _SAFE_AUTHORITY_COLUMN.fullmatch(column) is None:
        raise ScientificRequirementContractError(
            "authorized independent-unit column name is invalid"
        )
    if (
        not isinstance(group, str)
        or _SAFE_AUTHORITY_COLUMN.fullmatch(group) is None
        or group == column
    ):
        raise ScientificRequirementContractError("authorized group/contrast column name is invalid")
    return {
        _UNIT_AUTHORITY_ROLE: {
            "material_input_path": path,
            "column_name": column,
            "group_contrast_column": group,
        }
    }


def _validate_multiple_testing_semantic_role_authority(
    value: object,
    *,
    check_id: str,
    candidate_id: str,
) -> dict[str, Any]:
    if check_id != _MULTIPLE_TESTING_CHECK_ID or candidate_id != _MULTIPLE_TESTING_CANDIDATE_ID:
        raise ScientificRequirementContractError(
            "scientific requirement profile 1.2.0 is unavailable for this check/candidate"
        )
    if not isinstance(value, Mapping) or set(value) != {_MULTIPLE_TESTING_AUTHORITY_ROLE}:
        raise ScientificRequirementContractError(
            "multiple-testing semantic-role authority has the wrong exact role set"
        )
    authority = value.get(_MULTIPLE_TESTING_AUTHORITY_ROLE)
    if not isinstance(authority, Mapping) or set(authority) != {
        "material_input_path",
        "group_contrast_column",
        "outcome_columns",
        "family_member_rule",
        "correction_scope",
    }:
        raise ScientificRequirementContractError(
            "authorized test-family authority has the wrong exact field set"
        )
    path = authority.get("material_input_path")
    group = authority.get("group_contrast_column")
    outcomes = authority.get("outcome_columns")
    if not isinstance(path, str) or not _valid_authority_path(path):
        raise ScientificRequirementContractError("authorized test-family material path is invalid")
    if not isinstance(group, str) or _SAFE_AUTHORITY_COLUMN.fullmatch(group) is None:
        raise ScientificRequirementContractError(
            "authorized test-family group/contrast column is invalid"
        )
    if (
        not isinstance(outcomes, Sequence)
        or isinstance(outcomes, (str, bytes))
        or len(outcomes) < 3
        or not all(
            isinstance(item, str) and _SAFE_AUTHORITY_COLUMN.fullmatch(item) is not None
            for item in outcomes
        )
        or len(outcomes) != len(set(outcomes))
        or group in outcomes
    ):
        raise ScientificRequirementContractError(
            "authorized test-family outcome columns are invalid"
        )
    if authority.get("family_member_rule") != _MULTIPLE_TESTING_FAMILY_MEMBER_RULE:
        raise ScientificRequirementContractError("authorized test-family member rule is invalid")
    if authority.get("correction_scope") != _MULTIPLE_TESTING_CORRECTION_SCOPE:
        raise ScientificRequirementContractError(
            "authorized test-family correction scope is invalid"
        )
    return {
        _MULTIPLE_TESTING_AUTHORITY_ROLE: {
            "material_input_path": path,
            "group_contrast_column": group,
            "outcome_columns": list(outcomes),
            "family_member_rule": _MULTIPLE_TESTING_FAMILY_MEMBER_RULE,
            "correction_scope": _MULTIPLE_TESTING_CORRECTION_SCOPE,
        }
    }


def _valid_authority_path(value: str) -> bool:
    if (
        not value
        or len(value) > 512
        or not value.isascii()
        or value.startswith("/")
        or PurePosixPath(value).as_posix() != value
        or PurePosixPath(value).suffix.lower() != ".csv"
    ):
        return False
    parts = PurePosixPath(value).parts
    return bool(parts) and all(
        part not in {".", ".."} and _SAFE_AUTHORITY_SEGMENT.fullmatch(part) is not None
        for part in parts
    )


def _validate_authority_binding_snapshot(
    value: object,
    authority_value: object,
    *,
    check_id: str,
    candidate_id: str,
    profile_version: str,
) -> dict[str, Any]:
    authority = _validate_semantic_role_authority(
        authority_value,
        check_id=check_id,
        candidate_id=candidate_id,
        profile_version=profile_version,
    )
    if not authority:
        if value != {}:
            raise ScientificRequirementContractError(
                "empty semantic authority requires an empty binding snapshot"
            )
        return {}
    role = (
        _UNIT_AUTHORITY_ROLE
        if profile_version == SCIENTIFIC_REQUIREMENT_PROFILE_VERSION
        else _MULTIPLE_TESTING_AUTHORITY_ROLE
    )
    if not isinstance(value, Mapping) or set(value) != {role}:
        raise ScientificRequirementContractError(
            "authority binding snapshot has the wrong exact role set"
        )
    bound = value.get(role)
    expected_authority = authority[role]
    expected_fields = (
        {
            "material_input_path",
            "column_name",
            "group_contrast_column",
            "material_input_content_digest",
        }
        if profile_version == SCIENTIFIC_REQUIREMENT_PROFILE_VERSION
        else {
            "material_input_path",
            "group_contrast_column",
            "outcome_columns",
            "family_member_rule",
            "correction_scope",
            "material_input_content_digest",
        }
    )
    if not isinstance(bound, Mapping) or set(bound) != expected_fields:
        raise ScientificRequirementContractError(
            "authority binding snapshot has the wrong exact field set"
        )
    digest = bound.get("material_input_content_digest")
    if (
        {key: bound.get(key) for key in expected_authority} != expected_authority
        or not isinstance(digest, str)
        or re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is None
    ):
        raise ScientificRequirementContractError("authority binding snapshot drifted")
    return {
        role: {
            **copy.deepcopy(expected_authority),
            "material_input_content_digest": digest,
        }
    }


def _validate_resolved_shape(resolved: ResolvedScientificRequirement) -> None:
    required_manifest_fields = {
        "check_id",
        "check_version",
        "dimension",
        "comparison_form",
        "requirement_candidates",
        "permitted_wording",
    }
    if not required_manifest_fields.issubset(resolved.check_manifest):
        raise ScientificRequirementContractError("frozen check manifest is incomplete")
    if resolved.dimension not in SCIENTIFIC_CONTRACT_DIMENSIONS:
        raise ScientificRequirementContractError("frozen check dimension is unsupported")
    published = resolved.check_manifest.get("requirement_candidates")
    if not isinstance(published, list) or published.count(resolved.candidate) != 1:
        raise ScientificRequirementContractError(
            "selected candidate is not uniquely published by the frozen check"
        )
    validate_posthoc_requirement(resolved.dimension, resolved.comparison_form, resolved.value)


def _record_list(locked: Mapping[str, Any], field: str) -> list[dict[str, Any]]:
    value = locked.get(field)
    if not isinstance(value, list) or not all(isinstance(item, Mapping) for item in value):
        raise ScientificRequirementContractError(f"method-contract {field} is malformed")
    return [copy.deepcopy(dict(item)) for item in value]


def _deduplicate_source_refs(values: Sequence[object]) -> list[dict[str, Any]]:
    unique: dict[str, dict[str, Any]] = {}
    for value in values:
        if isinstance(value, Mapping):
            item = copy.deepcopy(dict(value))
            unique[canonical_json(item)] = item
    return [unique[key] for key in sorted(unique)]
