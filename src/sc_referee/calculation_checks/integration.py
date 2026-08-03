from __future__ import annotations

import copy
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sc_referee.calculation_checks.core import (
    CalculationContext,
    CalculationRegistryEvaluation,
    FrozenCalculationInput,
    public_observation_record,
)
from sc_referee.calculation_checks.material_context import MaterialCalculationContext
from sc_referee.core.ids import sha256_digest, stable_id
from sc_referee.delimited_io import (
    BoundedDelimitedContent,
    DelimitedReadError,
    classify_delimited_path,
    read_bounded_delimited_content,
)
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
MAX_CONTEXT_GZIP_CONTENT_BYTES = 8 * 1024 * 1024
MAX_CONTEXT_GZIP_TOTAL_LOGICAL_BYTES = 64 * 1024 * 1024
MAX_CONTEXT_GZIP_CHUNK_BYTES = 64 * 1024


@dataclass(frozen=True)
class CalculationCompilation:
    observations: tuple[dict[str, Any], ...]
    questions: tuple[dict[str, Any], ...]
    disclosures: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class CalculationContextBuild:
    context: CalculationContext
    read_receipts: tuple[dict[str, Any], ...]


def build_calculation_context(
    *,
    snapshot: SnapshotOutput,
    scientific_context: FrozenInspectionContext,
    artifacts: list[dict[str, Any]],
    read_checkpoint: Callable[[], None] | None = None,
) -> CalculationContextBuild | None:
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

    decoded_by_identity: dict[tuple[str, str], BoundedDelimitedContent | None] = {}
    receipt_by_identity: dict[tuple[str, str], dict[str, Any]] = {}
    gzip_logical_bytes_read = 0

    def bounded_gzip_content(
        path: str,
        content: bytes,
        digest: str,
        raw_byte_ceiling: int,
    ) -> tuple[BoundedDelimitedContent | None, bool]:
        nonlocal gzip_logical_bytes_read
        file_format = classify_delimited_path(path)
        if file_format is None or file_format.content_encoding == "identity":
            return None, True
        key = (path, digest)
        if key in decoded_by_identity:
            decoded = decoded_by_identity[key]
            return decoded, decoded is not None
        remaining = MAX_CONTEXT_GZIP_TOTAL_LOGICAL_BYTES - gzip_logical_bytes_read
        if remaining <= 1:
            receipt_by_identity[key] = _calculation_read_receipt(
                path=path,
                digest=digest,
                status="unsupported",
                raw_file_bytes=len(content),
                logical_bytes_read=0,
                read_chunks=0,
                raw_byte_ceiling=raw_byte_ceiling,
                content_byte_ceiling=MAX_CONTEXT_GZIP_CONTENT_BYTES,
                logical_read_byte_ceiling=MAX_CONTEXT_GZIP_CONTENT_BYTES + 1,
                aggregate_logical_bytes_after_read=gzip_logical_bytes_read,
                termination_reason="aggregate_logical_budget_exhausted",
            )
            decoded_by_identity[key] = None
            return None, False
        content_ceiling = min(MAX_CONTEXT_GZIP_CONTENT_BYTES, remaining - 1)
        logical_ceiling = content_ceiling + 1
        try:
            decoded = read_bounded_delimited_content(
                content,
                path,
                raw_byte_ceiling=raw_byte_ceiling,
                content_byte_ceiling=content_ceiling,
                logical_read_byte_ceiling=logical_ceiling,
                chunk_byte_ceiling=MAX_CONTEXT_GZIP_CHUNK_BYTES,
                checkpoint=read_checkpoint,
            )
        except DelimitedReadError as error:
            gzip_logical_bytes_read += error.logical_bytes_read
            receipt_by_identity[key] = _calculation_read_receipt(
                path=path,
                digest=digest,
                status="unsupported",
                raw_file_bytes=len(content),
                logical_bytes_read=error.logical_bytes_read,
                read_chunks=error.read_chunks,
                raw_byte_ceiling=raw_byte_ceiling,
                content_byte_ceiling=content_ceiling,
                logical_read_byte_ceiling=logical_ceiling,
                aggregate_logical_bytes_after_read=gzip_logical_bytes_read,
                termination_reason=error.reason,
            )
            decoded_by_identity[key] = None
            return None, False
        gzip_logical_bytes_read += decoded.logical_bytes_read
        receipt_by_identity[key] = _calculation_read_receipt(
            path=path,
            digest=digest,
            status="inspected",
            raw_file_bytes=len(content),
            logical_bytes_read=decoded.logical_bytes_read,
            read_chunks=decoded.read_chunks,
            raw_byte_ceiling=raw_byte_ceiling,
            content_byte_ceiling=content_ceiling,
            logical_read_byte_ceiling=logical_ceiling,
            aggregate_logical_bytes_after_read=gzip_logical_bytes_read,
            termination_reason=None,
            logical_content_digest=sha256_digest(decoded.content),
        )
        decoded_by_identity[key] = decoded
        return decoded, True

    artifact_paths: dict[str, list[dict[str, Any]]] = {}
    for artifact in artifacts:
        path = artifact.get("path")
        if isinstance(path, str) and classify_delimited_path(path) is not None:
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
        file_format = classify_delimited_path(path)
        if (
            read_checkpoint is not None
            and file_format is not None
            and file_format.content_encoding == "gzip"
        ):
            read_checkpoint()
        try:
            content = materialized.read_bytes()
        except OSError:
            continue
        decoded_content, supported = bounded_gzip_content(
            path,
            content,
            digest,
            MAX_CONTEXT_TABLE_BYTES,
        )
        if not supported:
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
                decoded_delimited_content=decoded_content,
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
            file_format = classify_delimited_path(path)
            if (
                read_checkpoint is not None
                and file_format is not None
                and file_format.content_encoding == "gzip"
            ):
                read_checkpoint()
            try:
                content = materialized.read_bytes()
                decoded_content, supported = bounded_gzip_content(
                    path,
                    content,
                    digest,
                    snapshot.identity_policy.material_full_digest_byte_budget,
                )
                if not supported:
                    continue
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
                    decoded_delimited_content=decoded_content,
                )
            except (OSError, ValueError):
                continue
            material_inputs.append(material_input)
            material_total_bytes += size
    if material_inputs:
        context: CalculationContext = MaterialCalculationContext(
            snapshot_digest=scientific_context.snapshot_digest,
            selected_surface_ref=scientific_context.selected_surface_ref,
            selected_artifact_ref=scientific_context.selected_artifact_ref,
            selected_report=report_input,
            tabular_inputs=tuple(tables),
            material_inputs=tuple(material_inputs),
        )
    else:
        context = CalculationContext(
            snapshot_digest=scientific_context.snapshot_digest,
            selected_surface_ref=scientific_context.selected_surface_ref,
            selected_artifact_ref=scientific_context.selected_artifact_ref,
            selected_report=report_input,
            tabular_inputs=tuple(tables),
        )
    return CalculationContextBuild(
        context=context,
        read_receipts=tuple(receipt_by_identity[key] for key in sorted(receipt_by_identity)),
    )


def _calculation_read_receipt(
    *,
    path: str,
    digest: str,
    status: str,
    raw_file_bytes: int,
    logical_bytes_read: int,
    read_chunks: int,
    raw_byte_ceiling: int,
    content_byte_ceiling: int,
    logical_read_byte_ceiling: int,
    aggregate_logical_bytes_after_read: int,
    termination_reason: str | None,
    logical_content_digest: str | None = None,
) -> dict[str, Any]:
    return {
        "path": path,
        "content_digest": digest,
        "content_encoding": "gzip",
        "status": status,
        "raw_file_bytes": raw_file_bytes,
        "logical_bytes_read": logical_bytes_read,
        "read_chunks": read_chunks,
        "raw_byte_ceiling": raw_byte_ceiling,
        "content_byte_ceiling": content_byte_ceiling,
        "logical_read_byte_ceiling": logical_read_byte_ceiling,
        "chunk_byte_ceiling": MAX_CONTEXT_GZIP_CHUNK_BYTES,
        "aggregate_logical_bytes_after_read": aggregate_logical_bytes_after_read,
        "aggregate_logical_byte_ceiling": MAX_CONTEXT_GZIP_TOTAL_LOGICAL_BYTES,
        "termination_reason": termination_reason,
        "logical_content_digest": logical_content_digest,
    }


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
