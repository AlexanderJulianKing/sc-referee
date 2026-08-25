from __future__ import annotations

import copy
import json
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any
from uuid import uuid4

from sc_referee.controller import _empty_bundle, _finalize_bundle
from sc_referee.core.ids import canonical_json, semantic_digest, stable_id
from sc_referee.method_contracts import (
    EXPECTED_COUNT_PROFILE_ID,
    EXPECTED_COUNT_PROFILE_MANIFEST,
    EXPECTED_COUNT_PROFILE_VERSION,
    EXPECTED_COUNT_REQUIRED_DIMENSIONS,
    SCIENTIFIC_CONTRACT_DIMENSIONS,
    expected_count_dimension_values,
    expected_count_profile_from_dimensions,
    validate_expected_count_profile,
)
from sc_referee.records.normalization import write_normalized_json
from sc_referee.records.observed import build_file_records, controller_provenance, typed_ref
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.scientific_checks.core import (
    FrozenBaseRecord,
    FrozenInspectionContext,
    FrozenMaterialInput,
    RecordRef,
)
from sc_referee.scientific_checks.registry import ScientificCheckLane, ScientificCheckRegistry
from sc_referee.scientific_requirement_contract import (
    MULTIPLE_TESTING_SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
    SCIENTIFIC_REQUIREMENT_PROFILE_ID,
    SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
    ResolvedScientificRequirement,
    ScientificRequirementContractError,
    bind_scientific_requirement_to_audit,
    build_scientific_requirement_records,
    compatible_dependence_code_lane_requirement,
    is_scientific_requirement_profile,
    resolve_scientific_requirement_profile,
    resolved_scientific_requirement_from_lock_profile,
    scientific_requirement_lock_profile,
    verify_parent_scientific_requirement,
)
from sc_referee.snapshot.repository import capture_repository
from sc_referee.storage.jsonl import JsonlRecordStore
from sc_referee.storage.layout import AuditLayout
from sc_referee.version import SCHEMA_VERSION, __version__

METHOD_CONTRACT_LOCK_KIND = "method_contract_v1"
METHOD_CONTRACT_LOCK_VERSION = "0.1.0"
_ANSWER_DIGEST_PROFILE = "canonical-json-excluding-answer-digest-v1"


class MethodContractRunError(ValueError):
    """Raised when a claimless method contract cannot be frozen or bound exactly."""


def _scientific_authority_material_paths(
    resolved: ResolvedScientificRequirement | None,
) -> tuple[str, ...]:
    if resolved is None or resolved.profile_version not in {
        SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
        MULTIPLE_TESTING_SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
    }:
        return ()
    authority = resolved.semantic_role_authority or {}
    role = (
        "authorized_independent_unit_key"
        if resolved.profile_version == SCIENTIFIC_REQUIREMENT_PROFILE_VERSION
        else "authorized_test_family"
    )
    value = authority.get(role)
    if not isinstance(value, Mapping):
        return ()
    path = value.get("material_input_path")
    return (path,) if isinstance(path, str) else ()


def _bind_scientific_authority_snapshot(
    resolved: ResolvedScientificRequirement,
    file_records: Sequence[Mapping[str, Any]],
    asset_identities: Sequence[Mapping[str, Any]],
) -> ResolvedScientificRequirement:
    paths = _scientific_authority_material_paths(resolved)
    if not paths:
        return (
            resolved.with_authority_binding_snapshot({})
            if resolved.profile_version
            in {
                SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
                MULTIPLE_TESTING_SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
            }
            else resolved
        )
    path = paths[0]
    files = [
        item
        for item in file_records
        if item.get("path") == path and item.get("entry_kind") == "regular_file"
    ]
    if len(files) != 1:
        raise MethodContractRunError(
            "scientific requirement material input is not one regular file"
        )
    identity_ref = files[0].get("asset_identity_ref")
    identity_id = identity_ref.get("record_id") if isinstance(identity_ref, Mapping) else None
    identities = [
        item
        for item in asset_identities
        if item.get("asset_identity_id") == identity_id
        and item.get("tier") == "full_digest"
        and item.get("asset_ref") == typed_ref("file_record", str(files[0].get("file_record_id")))
        and item.get("identity_evidence", {}).get("kind") == "full_digest"
    ]
    if len(identities) != 1:
        raise MethodContractRunError(
            "scientific requirement material input lacks one full-digest identity"
        )
    digest = identities[0].get("identity_evidence", {}).get("digest")
    role = (
        "authorized_independent_unit_key"
        if resolved.profile_version == SCIENTIFIC_REQUIREMENT_PROFILE_VERSION
        else "authorized_test_family"
    )
    authority = (resolved.semantic_role_authority or {}).get(role)
    if not isinstance(authority, Mapping) or not isinstance(digest, str):
        raise MethodContractRunError("scientific requirement authority is malformed")
    bound = copy.deepcopy(dict(authority))
    bound["material_input_content_digest"] = digest
    return resolved.with_authority_binding_snapshot({role: bound})


def run_method_contract(
    repository: Path,
    task: str,
    output: Path,
    schema_root: Path,
    *,
    profile: object | None = None,
    actor_id: str | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Freeze one claimless analysis-level method contract."""

    if output.exists() or output.is_symlink():
        raise FileExistsError(f"method-contract output already exists: {output}")
    task_path = _normalize_task_path(task)
    scientific_requirement = (
        resolve_scientific_requirement_profile(profile)
        if is_scientific_requirement_profile(profile)
        else None
    )
    normalized_profile = (
        None
        if scientific_requirement is not None
        else validate_expected_count_profile(profile)
        if profile is not None
        else None
    )
    normalized_actor = actor_id.strip() if isinstance(actor_id, str) else ""
    if (
        normalized_profile is not None or scientific_requirement is not None
    ) and not normalized_actor:
        raise MethodContractRunError(
            "actor_id must identify the scientist who supplied the governing profile"
        )
    if normalized_profile is None and scientific_requirement is None and normalized_actor:
        raise MethodContractRunError("actor_id is accepted only with a complete profile")

    timestamp = created_at or _timestamp_now()
    run_id = f"audit:{uuid4().hex}"
    repository = repository.resolve()
    layout = AuditLayout(output)
    layout.create()
    registry = LocalSchemaRegistry(schema_root)
    observed_store = JsonlRecordStore(layout.observed)

    snapshot = capture_repository(
        repository,
        layout.observed / "snapshot",
        run_id,
        captured_at=timestamp,
        material_full_digest_paths=_scientific_authority_material_paths(scientific_requirement),
    )
    registry.validate(snapshot.snapshot_record)
    write_normalized_json(layout.observed / "snapshot.json", snapshot.snapshot_record)
    file_records = build_file_records(
        snapshot.file_records,
        snapshot.asset_identity_records,
        str(snapshot.snapshot_record["snapshot_id"]),
        timestamp,
    )
    for record in [*file_records, *snapshot.asset_identity_records]:
        registry.validate(record)
        observed_store.append(record)

    task_record, task_identity = _exact_task_records(
        task_path, file_records, snapshot.asset_identity_records
    )
    source_ref = _task_source_ref(task_record, task_identity)
    if scientific_requirement is not None:
        scientific_requirement = _bind_scientific_authority_snapshot(
            scientific_requirement,
            file_records,
            snapshot.asset_identity_records,
        )
        assert normalized_actor
        records = build_scientific_requirement_records(
            run_id=run_id,
            created_at=timestamp,
            snapshot_digest=str(snapshot.snapshot_record["snapshot_digest"]),
            task_record=task_record,
            task_source_ref=source_ref,
            resolved=scientific_requirement,
            actor_id=normalized_actor,
            files_total=len(file_records),
        )
        lock_profile = scientific_requirement_lock_profile(scientific_requirement)
    else:
        records = _build_claimless_records(
            run_id=run_id,
            created_at=timestamp,
            snapshot_digest=str(snapshot.snapshot_record["snapshot_digest"]),
            task_record=task_record,
            task_source_ref=source_ref,
            profile=normalized_profile,
            actor_id=normalized_actor or None,
            files_total=len(file_records),
        )
        lock_profile = {
            "profile_id": EXPECTED_COUNT_PROFILE_ID,
            "profile_version": EXPECTED_COUNT_PROFILE_VERSION,
            "profile_manifest_digest": semantic_digest(EXPECTED_COUNT_PROFILE_MANIFEST),
            "resolution_status": "resolved" if normalized_profile is not None else "unresolved",
        }
    locked: dict[str, Any] = {
        "lock_kind": METHOD_CONTRACT_LOCK_KIND,
        "lock_version": METHOD_CONTRACT_LOCK_VERSION,
        "audit_run_id": run_id,
        "locked_at": timestamp,
        "snapshot_digest": snapshot.snapshot_record["snapshot_digest"],
        "model_calls": [],
        "model_access_after_lock": False,
        "project_code_executed": False,
        "repository_snapshot": snapshot.snapshot_record,
        "file_records": file_records,
        "asset_identities": snapshot.asset_identity_records,
        "scientific_contracts": [records["contract"]],
        "semantic_assertions": records["assertions"],
        "claims": [],
        "publication_surfaces": [],
        "material_questions": [records["question"]],
        "answers": records["answers"],
        "disclosures": [records["disclosure"]],
        "method_contract_profile": lock_profile,
        "coverage_inputs": records["coverage_inputs"],
    }
    locked["semantic_lock_digest"] = semantic_digest(locked)
    write_normalized_json(layout.lock_path, locked)
    return derive_method_contract_from_lock(locked, output, schema_root)


def replay_method_contract(lock_path: Path, output: Path, schema_root: Path) -> dict[str, Any]:
    """Replay a claimless method contract without model or project-code access."""

    if output.exists() or output.is_symlink():
        raise FileExistsError(f"replay output already exists: {output}")
    locked = _read_lock(lock_path)
    layout = AuditLayout(output)
    layout.create()
    registry = LocalSchemaRegistry(schema_root)
    snapshot = _mapping(locked.get("repository_snapshot"), "repository snapshot")
    registry.validate(snapshot)
    write_normalized_json(layout.observed / "snapshot.json", snapshot)
    observed_store = JsonlRecordStore(layout.observed)
    for record in [
        *_record_list(locked, "file_records"),
        *_record_list(locked, "asset_identities"),
    ]:
        registry.validate(record)
        observed_store.append(record)
    write_normalized_json(layout.lock_path, locked)
    return derive_method_contract_from_lock(locked, output, schema_root)


def preflight_frozen_scientific_requirement(
    *,
    lock_path: Path,
    schema_root: Path,
    context: FrozenInspectionContext,
    file_records: Sequence[Mapping[str, Any]],
    asset_identities: Sequence[Mapping[str, Any]],
    scientific_check_registry: ScientificCheckRegistry,
    scientific_check_lane: ScientificCheckLane,
) -> FrozenInspectionContext:
    """Expose one already-verified Answer/assertion pair to adapters before evaluation."""

    parent = _read_lock(lock_path)
    profile = parent.get("method_contract_profile")
    if not (
        isinstance(profile, Mapping)
        and profile.get("profile_id") == SCIENTIFIC_REQUIREMENT_PROFILE_ID
        and profile.get("profile_version")
        in {
            SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
            MULTIPLE_TESTING_SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
        }
    ):
        return context
    parent_schema_registry = _parent_scientific_requirement_registry(parent, schema_root)
    parent_contract, resolved, assertions, parent_answer = verify_parent_scientific_requirement(
        parent, parent_schema_registry
    )
    dependence_contract = (
        resolved.profile_version == SCIENTIFIC_REQUIREMENT_PROFILE_VERSION
        and resolved.check_id
        == "check:authorized-independent-unit-entry-into-row-independent-procedure"
        and resolved.candidate_id == "one-analyzed-row-per-authorized-independent-unit"
    )
    multiple_testing_contract = (
        resolved.profile_version == MULTIPLE_TESTING_SCIENTIFIC_REQUIREMENT_PROFILE_VERSION
        and resolved.check_id
        == "check:authorized-complete-family-correction-over-code-test-battery"
        and resolved.candidate_id == "complete-correction-over-authorized-outcome-family"
    )
    if not dependence_contract and not multiple_testing_contract:
        return context
    if multiple_testing_contract and scientific_check_lane != "development":
        return context
    _verify_current_task_identity(
        parent_contract,
        parent,
        file_records,
        asset_identities,
    )
    _verify_current_authority_material(resolved, context.material_inputs)
    verified = [
        item
        for item in assertions
        if item.get("predicate") == f"verified_intended_{resolved.dimension}"
        and item.get("extensions", {}).get("x-answer-ref")
        == typed_ref("answer", str(parent_answer["answer_id"]))
    ]
    if len(verified) != 1 or context.shared_derivations:
        raise MethodContractRunError(
            "scientific requirement preflight authority is duplicate or incomplete"
        )
    active_profile = {
        "profile_id": SCIENTIFIC_REQUIREMENT_PROFILE_ID,
        "profile_version": resolved.profile_version,
        "check_id": resolved.check_id,
        "candidate_id": resolved.candidate_id,
        "semantic_role_authority": copy.deepcopy(resolved.semantic_role_authority or {}),
    }
    active_lane_registry = ScientificCheckRegistry(
        scientific_check_registry.modules_for_lane(scientific_check_lane),
        unavailable_manifests=scientific_check_registry.unavailable_manifests,
        method_conflict_bindings=scientific_check_registry.bindings_for_lane(scientific_check_lane),
    )
    active = resolve_scientific_requirement_profile(
        active_profile,
        registry=active_lane_registry,
    ).with_authority_binding_snapshot(copy.deepcopy(resolved.authority_binding_snapshot or {}))
    if active != resolved:
        if multiple_testing_contract:
            raise MethodContractRunError(
                "scientific requirement is incompatible with the active check lane"
            )
        # A contract frozen by the previously qualified 2.1.0 lane may retain its exact
        # human authority under the promoted 3.1.0 lane. Contracts frozen by intervening
        # development grammars remain ineligible for production reinterpretation.
        if scientific_check_lane == "qualified" and not (
            resolved.check_version == "2.1.0" and active.check_version == "3.1.0"
        ):
            return context
        if not compatible_dependence_code_lane_requirement(resolved, active):
            raise MethodContractRunError(
                "scientific requirement is incompatible with the active check lane"
            )
    preflight_answer = copy.deepcopy(parent_answer)
    preflight_answer["extensions"]["x-scientific-check-manifest-digest"] = (
        active.check_manifest_digest
    )
    preflight_answer.pop("answer_digest", None)
    preflight_answer["answer_digest"] = semantic_digest(preflight_answer)
    preflight_assertion = copy.deepcopy(verified[0])
    preflight_assertion["extensions"]["x-scientific-check-manifest-digest"] = (
        active.check_manifest_digest
    )
    preflight_assertion["extensions"]["x-answer-digest"] = preflight_answer["answer_digest"]
    return FrozenInspectionContext(
        snapshot_digest=context.snapshot_digest,
        selected_surface_ref=context.selected_surface_ref,
        selected_artifact_ref=context.selected_artifact_ref,
        documents=context.documents,
        base_records=context.base_records,
        material_inputs=context.material_inputs,
        shared_derivations=(
            FrozenBaseRecord.from_record(
                RecordRef("answer", str(preflight_answer["answer_id"])), preflight_answer
            ),
            FrozenBaseRecord.from_record(
                RecordRef("semantic_assertion", str(preflight_assertion["assertion_id"])),
                preflight_assertion,
            ),
        ),
        scope_join_graph=context.scope_join_graph,
    )


def _parent_scientific_requirement_registry(
    locked: Mapping[str, Any], active_schema_root: Path
) -> LocalSchemaRegistry:
    """Validate an immutable v0.19 parent lock without restamping its records."""

    records: list[Mapping[str, Any]] = []
    snapshot = locked.get("repository_snapshot")
    if isinstance(snapshot, Mapping):
        records.append(snapshot)
    for field in (
        "answers",
        "asset_identities",
        "claims",
        "disclosures",
        "file_records",
        "material_questions",
        "publication_surfaces",
        "scientific_contracts",
        "semantic_assertions",
    ):
        value = locked.get(field)
        if not isinstance(value, list):
            raise MethodContractRunError("method-contract lock record collection is malformed")
        records.extend(item for item in value if isinstance(item, Mapping))
    versions = {item.get("schema_version") for item in records}
    if versions == {SCHEMA_VERSION}:
        return LocalSchemaRegistry(active_schema_root)
    historical_version = next(iter(versions)) if len(versions) == 1 else None
    if (
        SCHEMA_VERSION in {"0.20.0", "0.21.0"}
        and historical_version in {"0.19.0", "0.20.0"}
        and historical_version != SCHEMA_VERSION
    ):
        if active_schema_root.name != f"schemas-v{SCHEMA_VERSION}":
            raise MethodContractRunError(
                "active schema root cannot resolve the immutable parent schema package"
            )
        historical_root = active_schema_root.parent / f"schemas-v{historical_version}"
        if not historical_root.is_dir() or historical_root.is_symlink():
            raise MethodContractRunError("immutable parent schema package is unavailable")
        return LocalSchemaRegistry(historical_root)
    raise MethodContractRunError("method-contract lock has mixed or unsupported schema versions")


def derive_method_contract_from_lock(
    locked: Mapping[str, Any], output: Path, schema_root: Path
) -> dict[str, Any]:
    """Derive the public claimless bundle from one verified method-contract lock."""

    value = copy.deepcopy(dict(locked))
    _verify_lock_envelope(value)
    layout = AuditLayout(output)
    registry = LocalSchemaRegistry(schema_root)
    bundle = _empty_bundle(value)
    bundle["repository_snapshots"] = [copy.deepcopy(value["repository_snapshot"])]
    for field in (
        "file_records",
        "asset_identities",
        "scientific_contracts",
        "semantic_assertions",
        "claims",
        "publication_surfaces",
        "material_questions",
        "answers",
        "disclosures",
    ):
        bundle[field] = copy.deepcopy(value.get(field, []))
    coverage = _method_contract_coverage(value, bundle)
    bundle["coverage_records"] = [coverage]

    for record in [
        value["repository_snapshot"],
        *bundle["file_records"],
        *bundle["asset_identities"],
        *bundle["scientific_contracts"],
        *bundle["semantic_assertions"],
        *bundle["material_questions"],
        *bundle["answers"],
        *bundle["disclosures"],
        coverage,
    ]:
        registry.validate(record)
    derived_store = JsonlRecordStore(layout.derived)
    for field in (
        "scientific_contracts",
        "semantic_assertions",
        "material_questions",
        "answers",
        "disclosures",
    ):
        for record in bundle[field]:
            derived_store.append(record)
    derived_store.append(coverage)
    return _finalize_bundle(bundle, value, layout, registry, derived_store)


def bind_frozen_method_contract(
    *,
    lock_path: Path,
    schema_root: Path,
    snapshot_record: Mapping[str, Any],
    file_records: Sequence[Mapping[str, Any]],
    asset_identities: Sequence[Mapping[str, Any]],
    claims: list[dict[str, Any]],
    contracts: list[dict[str, Any]],
    assertions: list[dict[str, Any]],
    questions: list[dict[str, Any]],
    answers: list[dict[str, Any]],
    scientific_check_registry: ScientificCheckRegistry,
    run_id: str,
    created_at: str,
    material_inputs: Sequence[FrozenMaterialInput] = (),
) -> dict[str, Any]:
    """Bind a verified frozen analysis contract to applicable later Claim contracts."""

    parent = _read_lock(lock_path)
    parent_schema_registry = _parent_scientific_requirement_registry(parent, schema_root)
    active_schema_registry = LocalSchemaRegistry(schema_root)
    profile_record = parent.get("method_contract_profile")
    if (
        isinstance(profile_record, Mapping)
        and profile_record.get("profile_id") == SCIENTIFIC_REQUIREMENT_PROFILE_ID
    ):
        parent_contract, resolved_requirement, _, parent_answer = (
            verify_parent_scientific_requirement(parent, parent_schema_registry)
        )
        current_source_ref = _verify_current_task_identity(
            parent_contract,
            parent,
            file_records,
            asset_identities,
        )
        _verify_current_authority_material(resolved_requirement, material_inputs)
        return bind_scientific_requirement_to_audit(
            parent=parent,
            parent_contract=parent_contract,
            resolved=resolved_requirement,
            parent_answer=parent_answer,
            current_source_ref=current_source_ref,
            snapshot_record=snapshot_record,
            questions=questions,
            answers=answers,
            contracts=contracts,
            assertions=assertions,
            active_registry=scientific_check_registry,
            schema_registry=active_schema_registry,
            run_id=run_id,
            created_at=created_at,
        )
    parent_contract, parent_profile, parent_assertions, parent_answer = (
        _verified_resolved_parent_contract(parent, parent_schema_registry)
    )
    current_source_ref = _verify_current_task_identity(
        parent_contract,
        parent,
        file_records,
        asset_identities,
    )
    by_contract_id = {str(item["contract_id"]): item for item in contracts}
    bound_claim_ids: list[str] = []
    derived: list[dict[str, Any]] = []
    dimension_values = expected_count_dimension_values(parent_profile)
    parent_digest = str(parent["semantic_lock_digest"])
    parent_contract_id = str(parent_contract["contract_id"])
    answer_id = str(parent_answer["answer_id"])
    parent_by_predicate = {
        str(item["predicate"]): item
        for item in parent_assertions
        if item.get("predicate", "").startswith("verified_intended_")
    }
    for claim in claims:
        if (
            claim.get("claim_kind") != "quantitative"
            or claim.get("extensions", {}).get("x-method-profile-id") != EXPECTED_COUNT_PROFILE_ID
        ):
            continue
        contract = by_contract_id.get(str(claim.get("scientific_contract_id")))
        if contract is None:
            raise MethodContractRunError("applicable Claim has no ScientificContract")
        scope = contract.get("scope")
        if not isinstance(scope, dict) or scope.get("level") != "claim":
            raise MethodContractRunError("applicable Claim contract has an invalid scope")
        scope["parent_contract_id"] = parent_contract_id
        contract["source_refs"] = _deduplicate_source_refs(
            [*contract.get("source_refs", []), current_source_ref]
        )
        child_ids: list[str] = []
        for dimension in EXPECTED_COUNT_REQUIRED_DIMENSIONS:
            parent_assertion = parent_by_predicate[f"verified_intended_{dimension}"]
            assertion_id = stable_id(
                "assertion-bound-method-intent",
                run_id,
                str(claim["claim_id"]),
                parent_digest,
                str(parent_assertion["assertion_id"]),
            )
            child = {
                "schema_version": SCHEMA_VERSION,
                "record_type": "semantic_assertion",
                "assertion_id": assertion_id,
                "audit_run_id": run_id,
                "subject_ref": typed_ref("claim", str(claim["claim_id"])),
                "predicate": f"verified_intended_{dimension}",
                "object": copy.deepcopy(dimension_values[dimension]),
                "semantic_role": "intended",
                "assertion_class": "deterministic_derivation",
                "epistemic_status": "accepted",
                "authority_scope": "scientific_intent",
                "independently_checkable": True,
                "finding_eligibility": "eligible",
                "verification": {
                    "status": "verified",
                    "method": "deterministic_comparison",
                    "validator_id": "controller:frozen-method-contract-binding-v1",
                    "verified_at": created_at,
                },
                "certainty": copy.deepcopy(parent_answer["certainty"]),
                "rationale": (
                    "The controller verified the frozen human-authorized analysis contract, "
                    "its semantic-lock digest, and the unchanged governing task before binding "
                    "this value to the later Claim. This establishes scoped intent only."
                ),
                "source_refs": [copy.deepcopy(current_source_ref)],
                "provenance": controller_provenance(
                    "deterministic_frozen_method_contract_binding_v1", created_at
                ),
                "extensions": {
                    "x-answer-ref": typed_ref("answer", answer_id),
                    "x-parent-contract-ref": typed_ref("scientific_contract", parent_contract_id),
                    "x-parent-assertion-ref": typed_ref(
                        "semantic_assertion", str(parent_assertion["assertion_id"])
                    ),
                    "x-parent-semantic-lock-digest": parent_digest,
                    "x-profile-id": EXPECTED_COUNT_PROFILE_ID,
                    "x-profile-version": EXPECTED_COUNT_PROFILE_VERSION,
                    "x-authority-limitation": (
                        "Frozen human intent for this Claim only; scientific correctness and "
                        "executed computation are not established."
                    ),
                },
            }
            active_schema_registry.validate(child)
            derived.append(child)
            child_ids.append(assertion_id)
            contract["dimensions"][dimension] = {
                "state": "known",
                "assertion_ids": [assertion_id],
                "accepted_assertion_ids": [assertion_id],
                "notes": (
                    "Bound deterministically from the frozen analysis-level method contract; "
                    "no execution or correctness conclusion follows."
                ),
            }
        contract.setdefault("extensions", {})["x-method-contract-parent-lock-digest"] = (
            parent_digest
        )
        contract["extensions"]["x-method-profile-resolution-status"] = "resolved"
        claim.setdefault("extensions", {})["x-expected-count-profile-resolved"] = True
        claim["extensions"]["x-method-contract-parent-id"] = parent_contract_id
        extraction = claim.setdefault("extraction", {})
        extraction["semantic_assertion_ids"] = [
            *extraction.get("semantic_assertion_ids", []),
            *child_ids,
        ]
        bound_claim_ids.append(str(claim["claim_id"]))
    assertions.extend(derived)
    return {
        "parent_contract_id": parent_contract_id,
        "parent_semantic_lock_digest": parent_digest,
        "parent_snapshot_digest": str(parent["snapshot_digest"]),
        "current_snapshot_digest": str(snapshot_record["snapshot_digest"]),
        "governing_task_path": str(current_source_ref["path"]),
        "governing_task_content_digest": str(current_source_ref["content_digest"]),
        "bound_claim_ids": sorted(bound_claim_ids),
        "profile_id": EXPECTED_COUNT_PROFILE_ID,
        "profile_version": EXPECTED_COUNT_PROFILE_VERSION,
    }


def _build_claimless_records(
    *,
    run_id: str,
    created_at: str,
    snapshot_digest: str,
    task_record: Mapping[str, Any],
    task_source_ref: Mapping[str, Any],
    profile: Mapping[str, Any] | None,
    actor_id: str | None,
    files_total: int,
) -> dict[str, Any]:
    task_ref = typed_ref("file_record", str(task_record["file_record_id"]))
    contract_id = stable_id(
        "scientific-contract-analysis",
        run_id,
        str(task_source_ref["content_digest"]),
        EXPECTED_COUNT_PROFILE_ID,
    )
    question_id = stable_id("question-method-contract", run_id, contract_id)
    answer_values = expected_count_dimension_values(profile) if profile is not None else None
    assertions: list[dict[str, Any]] = []
    answers: list[dict[str, Any]] = []
    answer_id: str | None = None
    if answer_values is not None and actor_id is not None:
        answer_id = stable_id(
            "answer-method-contract",
            run_id,
            question_id,
            semantic_digest(answer_values),
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
            "answer_value": copy.deepcopy(answer_values),
            "respondent": {"actor_kind": "human", "actor_id": actor_id},
            "response_source": "provided_answer_file",
            "authority_scope": {
                "authority_kind": "scientific_intent",
                "subject_refs": [typed_ref("scientific_contract", contract_id)],
                "semantic_dimensions": sorted(EXPECTED_COUNT_REQUIRED_DIMENSIONS),
            },
            "certainty": {
                "level": "explicit",
                "basis": (
                    "The named human explicitly supplied the complete closed method profile."
                ),
            },
            "timestamp_status": "available",
            "answered_at": created_at,
            "supersedes_answer_refs": [],
            "answer_digest_profile": _ANSWER_DIGEST_PROFILE,
            "created_at": created_at,
            "provenance": {
                "actor": {"actor_kind": "human", "actor_id": actor_id},
                "method": "scientist_answer",
                "created_at": created_at,
                "tool": "sc-referee",
                "tool_version": __version__,
            },
        }
        answer["answer_digest"] = semantic_digest(answer)
        answers.append(answer)
        for dimension in EXPECTED_COUNT_REQUIRED_DIMENSIONS:
            declaration_id = stable_id(
                "assertion-method-contract-declaration", answer_id, dimension
            )
            declaration = _method_intent_assertion(
                assertion_id=declaration_id,
                run_id=run_id,
                contract_id=contract_id,
                dimension=dimension,
                value=answer_values[dimension],
                created_at=created_at,
                source_ref=task_source_ref,
                actor_id=actor_id,
                answer_id=answer_id,
                declaration_id=None,
            )
            assertions.append(declaration)
            assertions.append(
                _method_intent_assertion(
                    assertion_id=stable_id(
                        "assertion-verified-method-contract",
                        answer_id,
                        dimension,
                        canonical_json(answer_values[dimension]),
                    ),
                    run_id=run_id,
                    contract_id=contract_id,
                    dimension=dimension,
                    value=answer_values[dimension],
                    created_at=created_at,
                    source_ref=task_source_ref,
                    actor_id=actor_id,
                    answer_id=answer_id,
                    declaration_id=declaration_id,
                )
            )
    by_predicate = {str(item["predicate"]): item for item in assertions}
    dimensions: dict[str, Any] = {}
    for dimension in SCIENTIFIC_CONTRACT_DIMENSIONS:
        if answer_values is not None and dimension in EXPECTED_COUNT_REQUIRED_DIMENSIONS:
            declaration = by_predicate[f"intended_{dimension}"]
            derived = by_predicate[f"verified_intended_{dimension}"]
            dimensions[dimension] = {
                "state": "known",
                "assertion_ids": [declaration["assertion_id"], derived["assertion_id"]],
                "accepted_assertion_ids": [
                    declaration["assertion_id"],
                    derived["assertion_id"],
                ],
                "notes": (
                    "Human-declared intent plus a separate closed-profile controller "
                    "derivation; neither establishes scientific truth or execution."
                ),
            }
        else:
            dimensions[dimension] = {
                "state": "unknown",
                "reason": (
                    "This dimension is unresolved in the claimless expected-count profile."
                    if dimension in EXPECTED_COUNT_REQUIRED_DIMENSIONS
                    else "This dimension is outside the first closed method-contract slice."
                ),
                "searched_source_refs": [copy.deepcopy(dict(task_source_ref))],
                **(
                    {"material_question_id": question_id}
                    if dimension in EXPECTED_COUNT_REQUIRED_DIMENSIONS and answer_values is None
                    else {}
                ),
            }
    contract = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "scientific_contract",
        "contract_id": contract_id,
        "audit_run_id": run_id,
        "title": "Claimless expected-count analysis method contract",
        "status": "draft",
        "scope": {"level": "analysis", "subject_refs": [task_ref]},
        "dimensions": dimensions,
        "source_refs": [copy.deepcopy(dict(task_source_ref))],
        "created_at": created_at,
        "notes": (
            "Only the six expected_count_background_v1 dimensions may be resolved here. "
            "The draft status preserves every other scientific-contract dimension as unknown."
        ),
        "extensions": {
            "x-method-contract-lifecycle": "claimless_v1",
            "x-method-profile-id": EXPECTED_COUNT_PROFILE_ID,
            "x-method-profile-version": EXPECTED_COUNT_PROFILE_VERSION,
            "x-method-profile-manifest-digest": semantic_digest(EXPECTED_COUNT_PROFILE_MANIFEST),
            "x-method-profile-resolution-status": (
                "resolved" if answer_values is not None else "unresolved"
            ),
            "x-project-code-executed": False,
        },
    }
    question = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "material_question",
        "question_id": question_id,
        "audit_run_id": run_id,
        "question": ("Which complete expected-count/background profile governs this analysis?"),
        "unknown_semantic_dimension": "scientific_contract",
        "why_it_matters": (
            "The coding agent must not silently choose the governing expected-count method. "
            "A complete human-authorized profile can later be compared with exact reported wording."
        ),
        "candidate_answers": [
            {
                "answer_id": stable_id("answer-option", question_id, "provide-profile"),
                "label": "Provide closed profile",
                "value": {"action": "provide_expected_count_background_v1"},
                "consequence": (
                    "Only the six supported profile dimensions become declared intent."
                ),
            },
            {
                "answer_id": stable_id("answer-option", question_id, "retain-unknown"),
                "label": "Retain unresolved",
                "value": {"action": "retain_unknown"},
                "consequence": "Later method compatibility remains unavailable.",
            },
        ],
        "evidence_searched": [
            {
                "source": "exact governing task file identity",
                "result": (
                    "The task file was identity-bound for scope; its scientific prose was not "
                    "interpreted into a governing method profile."
                ),
            }
        ],
        "blocked_detector_ids": ["detector:bounded-reported-method-contract-conflict"],
        "affected_claim_ids": [],
        "linked_conditional_concern_ids": [],
        "priority": "high",
        "status": "answered" if answer_id is not None else "open",
        "answer_ids": [answer_id] if isinstance(answer_id, str) else [],
        "created_at": created_at,
        "provenance": controller_provenance(
            "deterministic_claimless_method_question_generation", created_at
        ),
        "extensions": {
            "x-contract-ref": typed_ref("scientific_contract", contract_id),
            "x-unresolved-dimensions": list(EXPECTED_COUNT_REQUIRED_DIMENSIONS),
            "x-method-profile-id": EXPECTED_COUNT_PROFILE_ID,
            "x-answer-shape": "expected_count_background_v1-dimension-values",
            "x-claimless": True,
        },
    }
    disclosure = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "disclosure",
        "disclosure_id": stable_id("disclosure-method-contract", run_id, contract_id),
        "audit_run_id": run_id,
        "disclosure_kind": "coverage_gap",
        "title": "Method contract has a deliberately narrow scope",
        "description": (
            "This claimless run records only the expected_count_background_v1 profile and "
            "does not inspect analysis code, results, or scientific adequacy."
        ),
        "importance": "important",
        "non_accusatory": True,
        "affected_refs": [typed_ref("scientific_contract", contract_id)],
        "source_refs": [copy.deepcopy(dict(task_source_ref))],
        "coverage_status": "partially_covered",
        "interpretive_consequence": (
            "A resolved profile establishes scoped human intent only; all unrelated dimensions "
            "and any later execution remain unknown."
        ),
        "next_step": (
            "Supply a complete supported profile if unresolved, then bind this lock to a later audit."
        ),
        "created_at": created_at,
        "provenance": controller_provenance("deterministic_method_contract_disclosure", created_at),
    }
    return {
        "contract": contract,
        "assertions": sorted(assertions, key=lambda item: str(item["assertion_id"])),
        "question": question,
        "answers": answers,
        "disclosure": disclosure,
        "coverage_inputs": {
            "files_total": files_total,
            "task_path": str(task_record["path"]),
            "resolved": answer_values is not None,
        },
    }


def _method_intent_assertion(
    *,
    assertion_id: str,
    run_id: str,
    contract_id: str,
    dimension: str,
    value: object,
    created_at: str,
    source_ref: Mapping[str, Any],
    actor_id: str,
    answer_id: str,
    declaration_id: str | None,
) -> dict[str, Any]:
    derived = declaration_id is not None
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "semantic_assertion",
        "assertion_id": assertion_id,
        "audit_run_id": run_id,
        "subject_ref": typed_ref("scientific_contract", contract_id),
        "predicate": f"{'verified_' if derived else ''}intended_{dimension}",
        "object": copy.deepcopy(value),
        "semantic_role": "intended",
        "assertion_class": ("deterministic_derivation" if derived else "scientist_declaration"),
        "epistemic_status": "accepted",
        "authority_scope": "scientific_intent",
        "independently_checkable": derived,
        "finding_eligibility": "eligible" if derived else "ineligible",
        "verification": {
            "status": "verified",
            "method": "deterministic_comparison" if derived else "scientist_confirmation",
            "validator_id": (
                "controller:claimless-expected-count-answer-v1"
                if derived
                else "controller:claimless-answer-authority-scope-v1"
            ),
            "verified_at": created_at,
        },
        "certainty": {
            "level": "explicit",
            "basis": "The named human explicitly supplied the closed profile values.",
        },
        "rationale": (
            "The controller verified the human Answer digest, analysis scope, complete closed "
            "profile, and exact task identity. This derives governing intent only."
            if derived
            else "The assertion preserves the human declaration and does not establish execution or scientific truth."
        ),
        "source_refs": [copy.deepcopy(dict(source_ref))],
        "provenance": (
            controller_provenance("deterministic_claimless_method_answer_derivation_v1", created_at)
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
            "x-answer-ref": typed_ref("answer", answer_id),
            "x-profile-id": EXPECTED_COUNT_PROFILE_ID,
            "x-profile-version": EXPECTED_COUNT_PROFILE_VERSION,
            **(
                {"x-original-declaration-ref": typed_ref("semantic_assertion", declaration_id)}
                if declaration_id is not None
                else {}
            ),
            "x-authority-limitation": (
                "Scoped human intent only; execution and general scientific correctness are not established."
            ),
        },
    }


def _method_contract_coverage(
    locked: Mapping[str, Any], bundle: Mapping[str, Any]
) -> dict[str, Any]:
    inputs = _mapping(locked.get("coverage_inputs"), "method-contract coverage inputs")
    resolved = inputs.get("resolved") is True
    profile_id = str(inputs.get("profile_id", EXPECTED_COUNT_PROFILE_ID))
    resolved_dimensions = inputs.get("resolved_dimensions")
    if not isinstance(resolved_dimensions, list):
        resolved_dimensions = list(EXPECTED_COUNT_REQUIRED_DIMENSIONS)
    scope_description = str(inputs.get("scope_description", "six expected-count method dimensions"))
    zero_grade = {
        dimension: {
            "complete": 0,
            "partial": 0,
            "missing": 0,
            "unavailable": 0,
            "opaque": 0,
            "total": 0,
        }
        for dimension in (
            "report_origin",
            "result_origin",
            "computational_origin",
            "input_origin",
            "execution_origin",
            "semantic_origin",
        )
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "coverage_record",
        "coverage_id": f"coverage:{locked['audit_run_id']}",
        "audit_run_id": locked["audit_run_id"],
        "generated_at": locked["locked_at"],
        "overall_status": "complete_within_plan",
        "scope": {
            "inventory_scope": "whole_repository",
            "deep_inspection_scope": (
                "Exact identity and analysis scope for one governing task file; scientific "
                "prose, code, results, and execution were not inspected."
            ),
            "publication_surface_refs": [],
            "publication_surface_status": "unavailable",
            "selection_envelope_included": False,
        },
        "inventory_summary": {
            "files_total": int(inputs["files_total"]),
            "files_classified": int(inputs["files_total"]),
            "files_deeply_inspected": 1,
        },
        "assessment_counts": {
            "findings": 0,
            "conditional_concerns": 0,
            "material_questions": len(bundle["material_questions"]),
            "disclosures": len(bundle["disclosures"]),
        },
        "claim_coverage": {
            "claims_total": 0,
            "claims_inspected": 0,
            "claims_with_complete_lineage": 0,
            "lineage_grade_counts": zero_grade,
        },
        "parser_coverage": [
            {
                "surface": f"method-contract task identity:{inputs['task_path']}",
                "status": "covered",
                "details": (
                    "The exact task file identity and scope were captured without interpreting "
                    "its prose into scientific intent."
                ),
            }
        ],
        "detector_coverage": [
            {
                "detector_id": (
                    "detector:bounded-analysis-method-conflict"
                    if profile_id == SCIENTIFIC_REQUIREMENT_PROFILE_ID
                    else "detector:bounded-reported-method-contract-conflict"
                ),
                "status": "not_applicable",
                "targets_total": 0,
                "targets_evaluated": 0,
                "details": "No Claim or reported method exists in the claimless lifecycle.",
            }
        ],
        "unknown_semantic_ids": (
            [] if resolved else [str(bundle["material_questions"][0]["question_id"])]
        ),
        "opaque_boundary_refs": [],
        "uninspected_paths": [
            str(item["path"])
            for item in bundle["file_records"]
            if item.get("path") != inputs["task_path"]
        ],
        "known_gaps": [
            (
                f"Only {scope_description} is frozen; all unrelated ScientificContract "
                "dimensions remain unknown."
                if resolved
                else f"The supported dimensions remain unresolved: {resolved_dimensions}."
            ),
            "No Claim, publication surface, result, computation, or execution was created or inspected.",
        ],
        "interpretation_policy": {
            "correctness_conclusion_allowed": False,
            "global_risk_rating_allowed": False,
            "absence_of_finding_statement": (
                "No finding means only that no issue was admitted within the declared evidence and validated detector coverage."
            ),
        },
        "provenance": controller_provenance(
            "deterministic_claimless_method_contract_coverage", str(locked["locked_at"])
        ),
        "extensions": {
            "x-run-state": "complete",
            "x-termination-reason": "completed",
            "x-pending-work": (
                [] if resolved else ["Obtain a human-authorized complete supported method profile."]
            ),
            "x-deeply-inspected-paths": [str(inputs["task_path"])],
            "x-uninspected-path-policy": (
                "All non-task paths were inventoried only and provide no negative evidence."
            ),
            "x-method-contract-lifecycle": "claimless_v1",
        },
    }


def _verified_resolved_parent_contract(
    locked: Mapping[str, Any], registry: LocalSchemaRegistry
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    if locked.get("method_contract_profile") != {
        "profile_id": EXPECTED_COUNT_PROFILE_ID,
        "profile_version": EXPECTED_COUNT_PROFILE_VERSION,
        "profile_manifest_digest": semantic_digest(EXPECTED_COUNT_PROFILE_MANIFEST),
        "resolution_status": "resolved",
    }:
        raise MethodContractRunError("method-contract lock has no resolved supported profile")
    contracts = _record_list(locked, "scientific_contracts")
    assertions = _record_list(locked, "semantic_assertions")
    answers = _record_list(locked, "answers")
    questions = _record_list(locked, "material_questions")
    if len(contracts) != 1 or len(answers) != 1 or len(questions) != 1:
        raise MethodContractRunError("resolved method-contract records are incomplete")
    contract = contracts[0]
    answer = answers[0]
    question = questions[0]
    for record in [contract, answer, question, *assertions]:
        registry.validate(record)
    if (
        contract.get("scope", {}).get("level") != "analysis"
        or contract.get("extensions", {}).get("x-method-profile-resolution-status") != "resolved"
        or contract.get("extensions", {}).get("x-method-contract-lifecycle") != "claimless_v1"
        or contract.get("extensions", {}).get("x-method-profile-id") != EXPECTED_COUNT_PROFILE_ID
        or contract.get("extensions", {}).get("x-method-profile-version")
        != EXPECTED_COUNT_PROFILE_VERSION
        or contract.get("extensions", {}).get("x-method-profile-manifest-digest")
        != semantic_digest(EXPECTED_COUNT_PROFILE_MANIFEST)
        or contract.get("extensions", {}).get("x-project-code-executed") is not False
        or question.get("status") != "answered"
        or question.get("answer_ids") != [answer.get("answer_id")]
        or answer.get("question_ref")
        != typed_ref("material_question", str(question.get("question_id")))
        or answer.get("authority_scope", {}).get("subject_refs")
        != [typed_ref("scientific_contract", str(contract.get("contract_id")))]
        or answer.get("authority_scope", {}).get("semantic_dimensions")
        != sorted(EXPECTED_COUNT_REQUIRED_DIMENSIONS)
        or answer.get("respondent", {}).get("actor_kind") != "human"
        or answer.get("response_source") != "provided_answer_file"
        or answer.get("source_snapshot_digest") != locked.get("snapshot_digest")
    ):
        raise MethodContractRunError("resolved method-contract authority or scope is invalid")
    answer_input = copy.deepcopy(answer)
    answer_digest = answer_input.pop("answer_digest", None)
    if not isinstance(answer_digest, str) or semantic_digest(answer_input) != answer_digest:
        raise MethodContractRunError("method-contract Answer digest mismatch")
    values: dict[str, Any] = {}
    for dimension in EXPECTED_COUNT_REQUIRED_DIMENSIONS:
        predicate = f"verified_intended_{dimension}"
        candidates = [
            item
            for item in assertions
            if item.get("predicate") == predicate
            and item.get("subject_ref")
            == typed_ref("scientific_contract", str(contract["contract_id"]))
            and item.get("finding_eligibility") == "eligible"
            and item.get("assertion_class") == "deterministic_derivation"
            and item.get("semantic_role") == "intended"
            and item.get("authority_scope") == "scientific_intent"
            and item.get("independently_checkable") is True
            and item.get("epistemic_status") == "accepted"
            and item.get("verification", {}).get("method") == "deterministic_comparison"
            and item.get("extensions", {}).get("x-answer-ref")
            == typed_ref("answer", str(answer["answer_id"]))
            and item.get("provenance", {}).get("actor", {}).get("actor_kind") == "controller"
        ]
        if len(candidates) != 1:
            raise MethodContractRunError(
                f"method-contract has no unique verified {dimension} assertion"
            )
        assertion = candidates[0]
        declarations = [
            item
            for item in assertions
            if item.get("predicate") == f"intended_{dimension}"
            and item.get("subject_ref")
            == typed_ref("scientific_contract", str(contract["contract_id"]))
            and item.get("assertion_class") == "scientist_declaration"
            and item.get("semantic_role") == "intended"
            and item.get("authority_scope") == "scientific_intent"
            and item.get("independently_checkable") is False
            and item.get("finding_eligibility") == "ineligible"
            and item.get("epistemic_status") == "accepted"
            and item.get("extensions", {}).get("x-answer-ref")
            == typed_ref("answer", str(answer["answer_id"]))
            and item.get("provenance", {}).get("actor") == answer.get("respondent")
        ]
        if len(declarations) != 1:
            raise MethodContractRunError(
                f"method-contract has no unique preserved human {dimension} declaration"
            )
        declaration = declarations[0]
        if assertion.get("object") != declaration.get("object") or assertion.get(
            "extensions", {}
        ).get("x-original-declaration-ref") != typed_ref(
            "semantic_assertion", str(declaration["assertion_id"])
        ):
            raise MethodContractRunError(
                f"method-contract verified {dimension} assertion differs from its declaration"
            )
        slot = contract.get("dimensions", {}).get(dimension, {})
        if slot.get("accepted_assertion_ids") != [
            declaration["assertion_id"],
            assertion["assertion_id"],
        ] or slot.get("assertion_ids") != [
            declaration["assertion_id"],
            assertion["assertion_id"],
        ]:
            raise MethodContractRunError(
                f"method-contract {dimension} slot does not bind its exact declaration pair"
            )
        values[dimension] = copy.deepcopy(assertion["object"])
    profile = expected_count_profile_from_dimensions(values)
    if answer.get("answer_value") != expected_count_dimension_values(profile):
        raise MethodContractRunError("method-contract Answer and verified profile disagree")
    return contract, profile, assertions, answer


def _verify_current_task_identity(
    parent_contract: Mapping[str, Any],
    parent_lock: Mapping[str, Any],
    current_files: Sequence[Mapping[str, Any]],
    current_identities: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    subjects = parent_contract.get("scope", {}).get("subject_refs", [])
    if not isinstance(subjects, list) or len(subjects) != 1:
        raise MethodContractRunError("method-contract has no unique governing task subject")
    parent_file_id = subjects[0].get("record_id")
    parent_file = next(
        (
            item
            for item in _record_list(parent_lock, "file_records")
            if item.get("file_record_id") == parent_file_id
        ),
        None,
    )
    if parent_file is None:
        raise MethodContractRunError("method-contract governing task FileRecord is unavailable")
    parent_identity = _identity_for_file(parent_file, _record_list(parent_lock, "asset_identities"))
    path = str(parent_file["path"])
    current_file = next((item for item in current_files if item.get("path") == path), None)
    if current_file is None:
        raise MethodContractRunError("governing task file changed or is no longer present")
    current_identity = _identity_for_file(current_file, current_identities)
    parent_digest = _full_digest(parent_identity)
    current_digest = _full_digest(current_identity)
    if parent_digest != current_digest:
        raise MethodContractRunError("governing task file changed after method contracting")
    return {
        "source_kind": "file_span",
        "locator": path,
        "path": path,
        "content_digest": current_digest,
        "external": False,
    }


def _verify_current_authority_material(
    resolved: ResolvedScientificRequirement,
    material_inputs: Sequence[FrozenMaterialInput],
) -> FrozenMaterialInput | None:
    snapshot = resolved.authority_binding_snapshot or {}
    if not snapshot:
        if material_inputs:
            return None
        return None
    role = (
        "authorized_independent_unit_key"
        if resolved.profile_version == SCIENTIFIC_REQUIREMENT_PROFILE_VERSION
        else "authorized_test_family"
    )
    authority = snapshot.get(role)
    if not isinstance(authority, Mapping):
        raise MethodContractRunError("scientific requirement authority snapshot is malformed")
    matches = [
        item
        for item in material_inputs
        if item.path == authority.get("material_input_path")
        and item.content_digest == authority.get("material_input_content_digest")
    ]
    if len(material_inputs) != 1 or len(matches) != 1:
        raise MethodContractRunError(
            "current material selection differs from the frozen scientific authority"
        )
    return matches[0]


def _verify_lock_envelope(locked: Mapping[str, Any]) -> None:
    if locked.get("lock_kind") != METHOD_CONTRACT_LOCK_KIND:
        raise MethodContractRunError("semantic lock is not a claimless method contract")
    if locked.get("lock_version") != METHOD_CONTRACT_LOCK_VERSION:
        raise MethodContractRunError("unsupported method-contract lock version")
    digest_input = copy.deepcopy(dict(locked))
    recorded = digest_input.pop("semantic_lock_digest", None)
    if not isinstance(recorded, str) or semantic_digest(digest_input) != recorded:
        raise MethodContractRunError("method-contract semantic lock digest mismatch")
    if (
        locked.get("model_calls") != []
        or locked.get("model_access_after_lock") is not False
        or locked.get("project_code_executed") is not False
        or locked.get("claims") != []
        or locked.get("publication_surfaces") != []
    ):
        raise MethodContractRunError("method-contract lock violates its claimless boundary")
    profile = locked.get("method_contract_profile")
    if not isinstance(profile, Mapping):
        raise MethodContractRunError("method-contract profile manifest identity mismatch")
    if profile.get("profile_id") == SCIENTIFIC_REQUIREMENT_PROFILE_ID:
        try:
            resolved_scientific_requirement_from_lock_profile(profile)
        except ScientificRequirementContractError as error:
            raise MethodContractRunError(str(error)) from error
    elif profile.get("profile_manifest_digest") != semantic_digest(EXPECTED_COUNT_PROFILE_MANIFEST):
        raise MethodContractRunError("method-contract profile manifest identity mismatch")


def _read_lock(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise MethodContractRunError(f"method-contract lock is unavailable or unsafe: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise MethodContractRunError("method-contract lock must contain one JSON object")
    _verify_lock_envelope(value)
    return value


def _normalize_task_path(task: str) -> str:
    value = task.strip()
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or value != path.as_posix():
        raise MethodContractRunError("task must be one normalized repository-relative POSIX path")
    return value


def _exact_task_records(
    task_path: str,
    files: Sequence[Mapping[str, Any]],
    identities: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    matches = [item for item in files if item.get("path") == task_path]
    if len(matches) != 1 or matches[0].get("entry_kind") != "regular_file":
        raise MethodContractRunError("task must identify one regular file in the repository")
    task = copy.deepcopy(dict(matches[0]))
    identity = _identity_for_file(task, identities)
    _full_digest(identity)
    return task, identity


def _identity_for_file(
    file_record: Mapping[str, Any], identities: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    expected = file_record.get("asset_identity_ref", {}).get("record_id")
    matches = [item for item in identities if item.get("asset_identity_id") == expected]
    if len(matches) != 1:
        raise MethodContractRunError("governing task has no unique AssetIdentity")
    return copy.deepcopy(dict(matches[0]))


def _full_digest(identity: Mapping[str, Any]) -> str:
    digest = identity.get("identity_evidence", {}).get("digest")
    if identity.get("tier") != "full_digest" or not isinstance(digest, str):
        raise MethodContractRunError(
            "governing task requires an independently computed full digest"
        )
    return digest


def _task_source_ref(task_record: Mapping[str, Any], identity: Mapping[str, Any]) -> dict[str, Any]:
    path = str(task_record["path"])
    return {
        "source_kind": "file_span",
        "locator": path,
        "path": path,
        "content_digest": _full_digest(identity),
        "external": False,
    }


def _record_list(locked: Mapping[str, Any], field: str) -> list[dict[str, Any]]:
    value = locked.get(field)
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise MethodContractRunError(f"method-contract lock field {field!r} is malformed")
    return [copy.deepcopy(item) for item in value]


def _mapping(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise MethodContractRunError(f"{label} is unavailable")
    return copy.deepcopy(dict(value))


def _deduplicate_source_refs(
    refs: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    by_value = {canonical_json(dict(ref)): copy.deepcopy(dict(ref)) for ref in refs}
    return [by_value[key] for key in sorted(by_value)]


def _timestamp_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
