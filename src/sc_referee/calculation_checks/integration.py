from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

from sc_referee.calculation_checks.core import (
    CalculationContext,
    CalculationRegistryEvaluation,
    FrozenCalculationInput,
    public_observation_record,
)
from sc_referee.calculation_checks.material_context import MaterialCalculationContext
from sc_referee.core.ids import stable_id
from sc_referee.records.observed import controller_provenance, typed_ref
from sc_referee.scientific_checks import FrozenInspectionContext, RecordRef
from sc_referee.scientific_checks.scope_joins import (
    FULL_DIGEST_PROFILE,
    PUBLICATION_PROFILE,
    full_digest_identity_path,
    selected_review_path,
)
from sc_referee.snapshot.repository import SnapshotOutput
from sc_referee.version import SCHEMA_VERSION

MAX_CONTEXT_TABLES = 128
MAX_CONTEXT_TABLE_BYTES = 1_000_000
MAX_CONTEXT_TOTAL_BYTES = 8_000_000
MAX_MATERIAL_CONTEXT_INPUTS = 8


@dataclass(frozen=True)
class CalculationCompilation:
    observations: tuple[dict[str, Any], ...]
    questions: tuple[dict[str, Any], ...]
    disclosures: tuple[dict[str, Any], ...]


def build_calculation_context(
    *,
    snapshot: SnapshotOutput,
    scientific_context: FrozenInspectionContext,
    artifacts: list[dict[str, Any]],
) -> CalculationContext | None:
    artifacts_by_id = {str(item["artifact_id"]): item for item in artifacts}
    selected = artifacts_by_id.get(scientific_context.selected_artifact_ref.record_id)
    if selected is None or not isinstance(selected.get("path"), str):
        return None
    selected_path = str(selected["path"])
    graph = scientific_context.scope_join_graph
    if graph is None:
        return None
    snapshot_refs = {
        proof.edge.target_ref
        for proof in graph.proofs_for_profile(FULL_DIGEST_PROFILE)
        if proof.edge.target_ref.record_type == "repository_snapshot"
    }
    if len(snapshot_refs) != 1:
        return None
    snapshot_ref = next(iter(snapshot_refs))
    report_scope = graph.unique_path(
        scientific_context.selected_artifact_ref,
        scientific_context.selected_surface_ref,
        profiles=(PUBLICATION_PROFILE,),
    )
    if not report_scope:
        return None
    report_documents = [
        item
        for item in scientific_context.documents
        if item.path == selected_path and item.source_location is not None
    ]
    if len(report_documents) != 1:
        return None
    report_document = report_documents[0]
    assert report_document.source_location is not None
    report_source = report_document.source_location.to_dict()
    report_input = FrozenCalculationInput(
        path=selected_path,
        artifact_ref=scientific_context.selected_artifact_ref,
        content=report_document.content,
        content_digest=report_document.content_digest,
        source_ref=report_source,
        scope_join_path=report_scope,
    )

    artifact_paths: dict[str, list[dict[str, Any]]] = {}
    for artifact in artifacts:
        path = artifact.get("path")
        if isinstance(path, str) and PurePosixPath(path).suffix.casefold() in {".csv", ".tsv"}:
            artifact_paths.setdefault(path, []).append(artifact)
    raw_files = {
        str(item["path"]): item
        for item in snapshot.file_records
        if item.get("entry_kind") == "regular_file"
    }
    identities = {
        str(item.get("asset_ref", {}).get("record_id")): item
        for item in snapshot.asset_identity_records
        if item.get("asset_ref", {}).get("record_type") == "file_record"
    }
    tables: list[FrozenCalculationInput] = []
    total_bytes = 0
    for path, matches in sorted(artifact_paths.items()):
        if len(tables) >= MAX_CONTEXT_TABLES or len(matches) != 1:
            continue
        file_record = raw_files.get(path)
        if file_record is None:
            continue
        identity = identities.get(str(file_record["file_id"]))
        digest = (
            identity.get("identity_evidence", {}).get("digest")
            if isinstance(identity, dict) and identity.get("tier") == "full_digest"
            else None
        )
        if not isinstance(digest, str):
            continue
        artifact_ref = RecordRef("artifact", str(matches[0]["artifact_id"]))
        identity_scope = full_digest_identity_path(
            graph,
            source_ref=artifact_ref,
            snapshot_ref=snapshot_ref,
        )
        if not identity_scope:
            continue
        materialized = snapshot.materialized_root / path
        try:
            size = materialized.stat().st_size
        except OSError:
            continue
        if (
            materialized.is_symlink()
            or not materialized.is_file()
            or size > MAX_CONTEXT_TABLE_BYTES
            or total_bytes + size > MAX_CONTEXT_TOTAL_BYTES
        ):
            continue
        try:
            content = materialized.read_bytes()
        except OSError:
            continue
        try:
            table = FrozenCalculationInput(
                path=path,
                artifact_ref=artifact_ref,
                content=content,
                content_digest=digest,
                source_ref={
                    "source_kind": "artifact",
                    "locator": path,
                    "path": path,
                    "artifact_id": str(matches[0]["artifact_id"]),
                    "content_digest": digest,
                },
                scope_join_path=identity_scope,
            )
        except ValueError:
            continue
        tables.append(table)
        total_bytes += size

    selected_material_paths = snapshot.snapshot_record.get("extensions", {}).get(
        "x-material-full-digest-paths", []
    )
    material_inputs: list[FrozenCalculationInput] = []
    material_total_bytes = 0
    if isinstance(selected_material_paths, list):
        for path in sorted(value for value in selected_material_paths if isinstance(value, str))[
            :MAX_MATERIAL_CONTEXT_INPUTS
        ]:
            if path == selected_path:
                continue
            matches = [item for item in artifacts if item.get("path") == path]
            file_record = raw_files.get(path)
            if len(matches) > 1 or file_record is None:
                continue
            identity = identities.get(str(file_record["file_id"]))
            digest = (
                identity.get("identity_evidence", {}).get("digest")
                if isinstance(identity, dict) and identity.get("tier") == "full_digest"
                else None
            )
            if not isinstance(digest, str):
                continue
            materialized = snapshot.materialized_root / path
            try:
                size = materialized.stat().st_size
            except OSError:
                continue
            if (
                materialized.is_symlink()
                or not materialized.is_file()
                or material_total_bytes + size
                > snapshot.identity_policy.material_full_digest_byte_budget
            ):
                continue
            try:
                content = materialized.read_bytes()
                if matches:
                    input_ref = RecordRef("artifact", str(matches[0]["artifact_id"]))
                    input_source_ref = {
                        "source_kind": "artifact",
                        "locator": path,
                        "path": path,
                        "artifact_id": str(matches[0]["artifact_id"]),
                        "content_digest": digest,
                    }
                else:
                    input_ref = RecordRef("file_record", str(file_record["file_id"]))
                    input_source_ref = {
                        "source_kind": "file_span",
                        "locator": path,
                        "path": path,
                        "content_digest": digest,
                    }
                material_scope = selected_review_path(
                    graph,
                    kind="material_input",
                    source_ref=input_ref,
                    selected_surface_ref=scientific_context.selected_surface_ref,
                )
                if not material_scope:
                    continue
                material_input = FrozenCalculationInput(
                    path=path,
                    artifact_ref=input_ref,
                    content=content,
                    content_digest=digest,
                    source_ref=input_source_ref,
                    scope_join_path=material_scope,
                )
            except (OSError, ValueError):
                continue
            material_inputs.append(material_input)
            material_total_bytes += size
    if material_inputs:
        return MaterialCalculationContext(
            snapshot_digest=scientific_context.snapshot_digest,
            selected_surface_ref=scientific_context.selected_surface_ref,
            selected_artifact_ref=scientific_context.selected_artifact_ref,
            selected_report=report_input,
            tabular_inputs=tuple(tables),
            material_inputs=tuple(material_inputs),
        )
    return CalculationContext(
        snapshot_digest=scientific_context.snapshot_digest,
        selected_surface_ref=scientific_context.selected_surface_ref,
        selected_artifact_ref=scientific_context.selected_artifact_ref,
        selected_report=report_input,
        tabular_inputs=tuple(tables),
    )


def compile_calculation_records(
    evaluation: CalculationRegistryEvaluation,
    *,
    run_id: str,
    created_at: str,
) -> CalculationCompilation:
    observations: list[dict[str, Any]] = []
    questions: list[dict[str, Any]] = []
    disclosures: list[dict[str, Any]] = []
    for module in evaluation.modules:
        record = public_observation_record(module, run_id=run_id, created_at=created_at)
        if record is None:
            continue
        observations.append(record)
        observation = module.observation
        assert observation is not None
        observation_ref = typed_ref(
            "deterministic_check_observation",
            str(record["deterministic_check_observation_id"]),
        )
        if observation.applicability == "ambiguous":
            question_id = stable_id(
                "question-calculation-check",
                run_id,
                str(record["observation_digest"]),
            )
            questions.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "record_type": "material_question",
                    "question_id": question_id,
                    "audit_run_id": run_id,
                    "question": (
                        "Does the referenced table contain the complete tested hypothesis family, "
                        "and which multiplicity procedure governs the reported discovery calls?"
                    ),
                    "unknown_semantic_dimension": "multiplicity_contract",
                    "why_it_matters": (
                        "A selected-hits table cannot support a deterministic multiple-testing "
                        "comparison until the complete family and governing procedure are known."
                    ),
                    "candidate_answers": [
                        {
                            "answer_id": stable_id("answer-option", question_id, "complete-bh"),
                            "label": "Complete BH family",
                            "value": {"family": "complete", "procedure": "benjamini_hochberg"},
                            "consequence": "A later audit may run the bounded BH comparison.",
                        },
                        {
                            "answer_id": stable_id("answer-option", question_id, "single-primary"),
                            "label": "Single primary test",
                            "value": {"family": "single_primary", "procedure": "not_applicable"},
                            "consequence": "The BH check is not applicable to that decision.",
                        },
                        {
                            "answer_id": stable_id("answer-option", question_id, "retain-unknown"),
                            "label": "Retain unknown",
                            "value": {"family": "unknown", "procedure": "unknown"},
                            "consequence": "No multiple-testing conclusion is drawn.",
                        },
                    ],
                    "evidence_searched": [
                        {
                            "source": "selected report and explicitly referenced bounded tables",
                            "result": "The complete family or governing procedure remained unavailable.",
                        }
                    ],
                    "blocked_detector_ids": [],
                    "affected_claim_ids": [],
                    "linked_conditional_concern_ids": [],
                    "priority": "high",
                    "status": "open",
                    "answer_ids": [],
                    "created_at": created_at,
                    "provenance": controller_provenance(
                        "bounded_calculation_question_v1", created_at
                    ),
                    "extensions": {
                        "x-calculation-observation-ref": observation_ref,
                        "x-output-ceiling": "question_only",
                    },
                }
            )
        elif observation.applicability == "unsupported":
            disclosures.append(
                _disclosure(
                    record,
                    run_id,
                    created_at,
                    title="Declared bounded calculation could not be completed",
                    description=observation.limitations[0],
                    coverage_status="not_covered",
                    importance="important",
                )
            )
        elif observation.comparison_outcome == "nonconformant":
            operands = {item.name: item.value for item in observation.operands}
            check_id = module.check_manifest.check_id
            if check_id == "calculation-check:single-cell-replicate-sensitivity-v1":
                title = "Reported discoveries changed under replicate-level sensitivity analysis"
                description = (
                    f"Of {operands['reported_significant_testable']} explicitly declared, "
                    "matched, and testable reported discoveries, "
                    f"{operands['replicate_level_survivors']} remained significant in the "
                    "auditor-owned replicate-level sensitivity calculation. The recorded power "
                    "and producer limitations govern interpretation."
                )
            elif check_id == "calculation-check:effect-size-relevance-summary-v1":
                title = "Declared discoveries include effects below the relevance floor"
                description = (
                    f"Of {operands['significant_discoveries']} discoveries in the explicitly "
                    f"bound significant family, {operands['below_threshold_discoveries']} "
                    f"({operands['below_threshold_fraction']:.1%}) fall below the declared "
                    f"absolute {operands['effect_scale']} threshold of "
                    f"{operands['effect_threshold']}."
                )
            elif check_id == "calculation-check:tabular-design-integrity-v1":
                title = "Declared design contains exact structural incompatibilities"
                parts = []
                if operands["merged_aggregation_groups"]:
                    parts.append(
                        f"{operands['merged_aggregation_groups']} aggregation group(s) contain both contrast arms"
                    )
                if operands["missing_aggregation_rows"]:
                    parts.append(
                        f"{operands['missing_aggregation_rows']} row(s) have an incomplete aggregation identity"
                    )
                if operands["pairing_omitted"]:
                    parts.append(
                        f"{operands['complete_pairing_levels']} cross-arm pairing level(s) are present but the bound comparison is unpaired"
                    )
                if operands["paired_comparison_unusable"]:
                    parts.append("the bound paired comparison has no complete pair")
                if operands["required_adjustments_omitted"]:
                    parts.append(
                        "required adjustment fields are absent from the bound model: "
                        + ", ".join(operands["required_adjustments_omitted"])
                    )
                if operands["condition_aliased_with_required_adjustments"]:
                    parts.append(
                        "the condition indicator lies exactly in the categorical adjustment design span"
                    )
                description = "; ".join(parts) + "."
            elif check_id == "calculation-check:r-count-model-compatibility-v1":
                title = "Bound R producer method is incompatible with the declared response scale"
                description = (
                    f"The exact producer call {operands['producer_call']} belongs to "
                    f"{operands['observed_method_family']}, while the bound response scale is "
                    f"{operands['response_scale']} and the declared requirement is "
                    f"{operands['required_method_family']}."
                )
            elif check_id == "calculation-check:scanpy-selection-reuse-v1":
                title = "One expression object is reused for de-novo clustering and marker testing"
                description = (
                    f"The unique bounded Scanpy source shape clusters "
                    f"{operands['selection_object']} and then tests calibrated markers on "
                    f"{operands['test_object']} using group key {operands['groupby_key']}, with "
                    f"safeguard {operands['safeguard']}. This records the exact static reuse "
                    "pattern; its stated limitations govern interpretation."
                )
            elif check_id == "calculation-check:donor-eqtl-sign-v1":
                title = "Reported eQTL direction differs from the donor-level oriented slope"
                description = (
                    f"For {operands['target_feature']} at {operands['variant_id']}, the reported "
                    f"effect sign is {operands['reported_sign']} while the independently "
                    f"recomputed donor-level OLS sign is {operands['recomputed_sign']} after "
                    f"{operands['orientation_transform']} allele orientation."
                )
            elif check_id == "calculation-check:hic-loop-strength-v1":
                title = "Reported Hi-C loop-strength delta differs from independent recomputation"
                description = (
                    f"For target {operands['target_bin_i']}-{operands['target_bin_j']}, the "
                    f"reported delta is {operands['reported_delta']} and the independent bounded "
                    f"recomputation is {operands['recomputed_delta']}; absolute error "
                    f"{operands['absolute_error']} exceeds the declared tolerance "
                    f"{operands['reported_delta_tolerance']}."
                )
            else:
                title = "Declared BH outputs differ from bounded recomputation"
                description = (
                    "For the explicitly declared complete family, the table reports "
                    f"{operands['reported_discovery_count']} discovery calls while the "
                    f"exact-decimal BH recomputation yields {operands['recomputed_discovery_count']}."
                )
            disclosures.append(
                _disclosure(
                    record,
                    run_id,
                    created_at,
                    title=title,
                    description=description,
                    coverage_status="covered",
                    importance="important",
                )
            )
    return CalculationCompilation(tuple(observations), tuple(questions), tuple(disclosures))


def _disclosure(
    observation: dict[str, Any],
    run_id: str,
    created_at: str,
    *,
    title: str,
    description: str,
    coverage_status: str,
    importance: str,
) -> dict[str, Any]:
    observation_id = str(observation["deterministic_check_observation_id"])
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "disclosure",
        "disclosure_id": stable_id("disclosure-calculation-check", run_id, observation_id),
        "audit_run_id": run_id,
        "disclosure_kind": "other" if coverage_status == "covered" else "detector_gap",
        "title": title,
        "description": description,
        "importance": importance,
        "non_accusatory": True,
        "affected_refs": [
            typed_ref("deterministic_check_observation", observation_id),
            copy.deepcopy(observation["target_ref"]),
        ],
        "source_refs": copy.deepcopy(observation["source_refs"]),
        "coverage_status": coverage_status,
        "interpretive_consequence": (
            "This experimental calculation check can emit only a Disclosure. It does not establish "
            "workflow execution, publication use, scientific appropriateness, or a Finding."
        ),
        "created_at": created_at,
        "provenance": controller_provenance("bounded_calculation_disclosure_v1", created_at),
        "extensions": {
            "x-calculation-observation-ref": typed_ref(
                "deterministic_check_observation", observation_id
            ),
            "x-production-finding-permitted": False,
        },
    }
