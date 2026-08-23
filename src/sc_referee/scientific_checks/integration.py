from __future__ import annotations

import copy
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath
from typing import Any

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest, stable_id
from sc_referee.method_contracts import SCIENTIFIC_CONTRACT_DIMENSIONS
from sc_referee.parsers.cell_language_bridge import reextract_verified_cell_source
from sc_referee.records.observed import controller_provenance, typed_ref
from sc_referee.scientific_checks.core import (
    CheckManifest,
    FrozenBaseRecord,
    FrozenInspectionContext,
    FrozenMaterialInput,
    FrozenSourceLocation,
    InspectionDocument,
    NormalizedMethodObservation,
    RecordRef,
    ScientificCheckModule,
)
from sc_referee.scientific_checks.registry import RegistryEvaluation, ScientificCheckRegistry
from sc_referee.scientific_checks.scope_joins import build_static_scope_join_graph
from sc_referee.version import SCHEMA_VERSION, __version__

_MAX_ADAPTER_DOCUMENT_BYTES = 2_000_000
_MAX_INSPECTION_MATERIAL_INPUTS = 8
_MAX_INSPECTION_MATERIAL_INPUT_BYTES = 8 * 1024 * 1024
_MAX_INSPECTION_MATERIAL_TOTAL_BYTES = 64 * 1024 * 1024


@dataclass(frozen=True)
class ScientificCheckCompilation:
    contracts: tuple[dict[str, Any], ...]
    assertions: tuple[dict[str, Any], ...]
    questions: tuple[dict[str, Any], ...]
    disclosures: tuple[dict[str, Any], ...]


def build_frozen_inspection_context(
    *,
    snapshot_root: Path,
    snapshot_digest: str,
    file_records: list[dict[str, Any]],
    asset_identities: list[dict[str, Any]],
    parser_results: list[dict[str, Any]],
    operations: list[dict[str, Any]],
    artifacts: list[dict[str, Any]],
    publication_surface: dict[str, Any],
    repository_snapshot: dict[str, Any],
    executions: list[dict[str, Any]] | None = None,
    environments: list[dict[str, Any]] | None = None,
    scope_selections: dict[str, Any] | None = None,
    selection_evidence_records: list[dict[str, Any]] | None = None,
) -> FrozenInspectionContext | None:
    """Construct immutable adapter bytes without exposing filesystem or controller handles."""

    selected = publication_surface.get("selection", {}).get("selected_surface_refs", [])
    selected_surface_ref: RecordRef
    selected_artifact_ref: RecordRef
    if publication_surface.get("status") == "resolved" and len(selected) == 1:
        selected_artifact_id = selected[0].get("record_id")
        selected_artifacts = [
            item for item in artifacts if item.get("artifact_id") == selected_artifact_id
        ]
        if len(selected_artifacts) != 1:
            return None
        selected_surface_ref = RecordRef(
            "publication_surface", str(publication_surface["publication_surface_id"])
        )
        selected_artifact_ref = RecordRef("artifact", str(selected_artifact_id))
    else:
        analysis_files = [
            item
            for item in file_records
            if item.get("path") == "analysis.py"
            and item.get("entry_kind") == "regular_file"
            and isinstance(item.get("file_record_id"), str)
        ]
        if len(analysis_files) != 1:
            return None
        analysis_ref = RecordRef("file_record", str(analysis_files[0]["file_record_id"]))
        selected_surface_ref = analysis_ref
        selected_artifact_ref = analysis_ref
    base_values = [
        repository_snapshot,
        publication_surface,
        *file_records,
        *asset_identities,
        *parser_results,
        *operations,
        *artifacts,
        *(executions or []),
        *(environments or []),
        *(selection_evidence_records or []),
    ]
    base_records: list[FrozenBaseRecord] = []
    for value in base_values:
        ref = _record_ref(value)
        if ref is not None:
            base_records.append(FrozenBaseRecord.from_record(ref, value))
    base_records.sort(key=lambda item: item.ref)
    if len({item.ref for item in base_records}) != len(base_records):
        return None

    material_inputs = _frozen_material_inputs(
        resolved_root=snapshot_root.resolve(),
        repository_snapshot=repository_snapshot,
        file_records=file_records,
        asset_identities=asset_identities,
    )

    files_by_path = {
        str(item.get("path")): item
        for item in file_records
        if item.get("entry_kind") == "regular_file"
    }
    documents: list[InspectionDocument] = []
    resolved_root = snapshot_root.resolve()
    parser_results_by_id = {
        str(item["parser_result_id"]): item
        for item in parser_results
        if isinstance(item.get("parser_result_id"), str)
    }
    if len(parser_results_by_id) != len(parser_results):
        return None
    tree_sitter_r_scopes = {
        _parser_source_scope(item)
        for item in parser_results
        if item.get("parser_id") == "parser:r-tree-sitter-inventory"
    }
    for parser_result in sorted(
        parser_results,
        key=lambda item: (
            str(item.get("source_ref", {}).get("path", "")),
            str(item.get("parser_id", "")),
        ),
    ):
        source_ref = parser_result.get("source_ref", {})
        path_value = source_ref.get("path")
        if not isinstance(path_value, str):
            continue
        if (
            parser_result.get("parser_id") == "parser:r-base-parse-data"
            and _parser_source_scope(parser_result) in tree_sitter_r_scopes
        ):
            continue
        file_record = files_by_path.get(path_value)
        if file_record is None:
            continue
        document = (
            _whole_file_inspection_document(
                resolved_root=resolved_root,
                path_value=path_value,
                file_record=file_record,
                parser_result=parser_result,
            )
            if source_ref.get("source_kind") == "file_span"
            else _virtual_cell_inspection_document(
                resolved_root=resolved_root,
                path_value=path_value,
                file_record=file_record,
                parser_result=parser_result,
                parser_results_by_id=parser_results_by_id,
            )
        )
        if document is not None:
            documents.append(document)
    context = FrozenInspectionContext(
        snapshot_digest=snapshot_digest,
        selected_surface_ref=selected_surface_ref,
        selected_artifact_ref=selected_artifact_ref,
        documents=tuple(documents),
        base_records=tuple(base_records),
        material_inputs=material_inputs,
    )
    snapshot_ref = _record_ref(repository_snapshot)
    if snapshot_ref is None:
        return None
    graph = build_static_scope_join_graph(
        snapshot_digest=snapshot_digest,
        snapshot_ref=snapshot_ref,
        selected_surface_ref=context.selected_surface_ref,
        selected_artifact_ref=context.selected_artifact_ref,
        documents=context.documents,
        base_records=context.base_records,
        scope_selections=scope_selections,
    )
    return replace(context, scope_join_graph=graph)


def _frozen_material_inputs(
    *,
    resolved_root: Path,
    repository_snapshot: dict[str, Any],
    file_records: list[dict[str, Any]],
    asset_identities: list[dict[str, Any]],
) -> tuple[FrozenMaterialInput, ...]:
    """Freeze only intake-selected, full-digest material bytes under strict budgets."""

    selected = repository_snapshot.get("extensions", {}).get("x-material-full-digest-paths", [])
    if not isinstance(selected, list):
        return ()
    selected_paths = sorted({item for item in selected if isinstance(item, str)})
    if len(selected_paths) > _MAX_INSPECTION_MATERIAL_INPUTS:
        selected_paths = selected_paths[:_MAX_INSPECTION_MATERIAL_INPUTS]
    files_by_path: dict[str, list[dict[str, Any]]] = {}
    for record in file_records:
        path = record.get("path")
        if record.get("entry_kind") == "regular_file" and isinstance(path, str):
            files_by_path.setdefault(path, []).append(record)
    identities_by_id = {
        str(record["asset_identity_id"]): record
        for record in asset_identities
        if isinstance(record.get("asset_identity_id"), str)
    }
    frozen: list[FrozenMaterialInput] = []
    total_bytes = 0
    for path in selected_paths:
        matches = files_by_path.get(path, [])
        if len(matches) != 1:
            continue
        file_record = matches[0]
        file_ref = _record_ref(file_record)
        identity_ref_value = file_record.get("asset_identity_ref")
        if (
            file_ref is None
            or not isinstance(identity_ref_value, dict)
            or identity_ref_value.get("record_type") != "asset_identity"
            or not isinstance(identity_ref_value.get("record_id"), str)
        ):
            continue
        identity_ref = RecordRef("asset_identity", str(identity_ref_value["record_id"]))
        identity = identities_by_id.get(identity_ref.record_id)
        evidence = identity.get("identity_evidence") if isinstance(identity, dict) else None
        digest = evidence.get("digest") if isinstance(evidence, dict) else None
        if (
            not isinstance(identity, dict)
            or identity.get("tier") != "full_digest"
            or identity.get("asset_ref") != file_ref.to_dict()
            or not isinstance(evidence, dict)
            or evidence.get("kind") != "full_digest"
            or not isinstance(digest, str)
        ):
            continue
        source_path = _resolved_snapshot_file(resolved_root, path)
        if source_path is None:
            continue
        try:
            size = source_path.stat().st_size
        except OSError:
            continue
        if (
            size > _MAX_INSPECTION_MATERIAL_INPUT_BYTES
            or total_bytes + size > _MAX_INSPECTION_MATERIAL_TOTAL_BYTES
        ):
            continue
        try:
            content = source_path.read_bytes()
        except OSError:
            continue
        if len(content) != size or sha256_digest(content) != digest:
            continue
        try:
            material = FrozenMaterialInput(
                path=path,
                file_ref=file_ref,
                asset_identity_ref=identity_ref,
                content=content,
                content_digest=digest,
            )
        except ValueError:
            continue
        frozen.append(material)
        total_bytes += size
    return tuple(frozen)


def _whole_file_inspection_document(
    *,
    resolved_root: Path,
    path_value: str,
    file_record: dict[str, Any],
    parser_result: dict[str, Any],
) -> InspectionDocument | None:
    content_digest = parser_result.get("source_ref", {}).get("content_digest")
    if not isinstance(content_digest, str):
        return None
    source_path = _resolved_snapshot_file(resolved_root, path_value)
    if source_path is None:
        return None
    try:
        if source_path.stat().st_size > _MAX_ADAPTER_DOCUMENT_BYTES:
            return None
        content = source_path.read_bytes()
    except OSError:
        return None
    if sha256_digest(content) != content_digest:
        return None
    return _inspection_document(
        path_value=path_value,
        file_record=file_record,
        parser_result=parser_result,
        content=content,
        content_digest=content_digest,
        media_type=_media_type(path_value),
    )


def _virtual_cell_inspection_document(
    *,
    resolved_root: Path,
    path_value: str,
    file_record: dict[str, Any],
    parser_result: dict[str, Any],
    parser_results_by_id: dict[str, dict[str, Any]],
) -> InspectionDocument | None:
    source_ref = parser_result.get("source_ref", {})
    if source_ref.get("source_kind") not in {"notebook_cell", "document_chunk"}:
        return None
    extension = parser_result.get("extensions", {}).get("x-virtual-source")
    if not isinstance(extension, dict):
        return None
    parent_id = extension.get("container_parser_result_id")
    if not isinstance(parent_id, str):
        return None
    parent = parser_results_by_id.get(parent_id)
    if parent is None:
        return None
    parent_ref = parent.get("source_ref", {})
    if (
        parent_ref.get("source_kind") != "file_span"
        or parent_ref.get("path") != path_value
        or parent_ref.get("content_digest") != source_ref.get("content_digest")
    ):
        return None
    source_path = _resolved_snapshot_file(resolved_root, path_value)
    if source_path is None:
        return None
    try:
        verified = reextract_verified_cell_source(source_path, parent, parser_result)
        if len(verified.content) > _MAX_ADAPTER_DOCUMENT_BYTES:
            return None
        source_location = FrozenSourceLocation(
            canonical_payload=verified.source_ref_payload,
            payload_digest=sha256_digest(verified.source_ref_payload),
        )
    except (OSError, UnicodeError, ValueError):
        return None
    return _inspection_document(
        path_value=path_value,
        file_record=file_record,
        parser_result=parser_result,
        content=verified.content,
        content_digest=verified.content_digest,
        media_type={"python": "text/x-python", "r": "text/x-r"}[verified.language],
        source_location=source_location,
        line_offset=verified.line_offset,
    )


def _inspection_document(
    *,
    path_value: str,
    file_record: dict[str, Any],
    parser_result: dict[str, Any],
    content: bytes,
    content_digest: str,
    media_type: str,
    source_location: FrozenSourceLocation | None = None,
    line_offset: int = 0,
) -> InspectionDocument | None:
    parser_payload = canonical_json(parser_result).encode("utf-8")
    parser_ref = _record_ref(parser_result)
    file_ref = _record_ref(file_record)
    if parser_ref is None or file_ref is None:
        return None
    return InspectionDocument(
        path=path_value,
        file_ref=file_ref,
        content=content,
        content_digest=content_digest,
        media_type=media_type,
        parser_result_ref=parser_ref,
        parser_result_payload=parser_payload,
        parser_result_digest=sha256_digest(parser_payload),
        source_location=source_location,
        line_offset=line_offset,
    )


def _resolved_snapshot_file(resolved_root: Path, path_value: str) -> Path | None:
    relative = PurePosixPath(path_value)
    if relative.is_absolute() or ".." in relative.parts:
        return None
    unresolved_path = resolved_root / relative.as_posix()
    if unresolved_path.is_symlink():
        return None
    source_path = unresolved_path.resolve()
    try:
        source_path.relative_to(resolved_root)
    except ValueError:
        return None
    return source_path if source_path.is_file() else None


def _parser_source_scope(parser_result: dict[str, Any]) -> str:
    virtual = parser_result.get("extensions", {}).get("x-virtual-source")
    if isinstance(virtual, dict) and isinstance(virtual.get("source_ref"), dict):
        return canonical_json(virtual["source_ref"])
    source_ref = parser_result.get("source_ref", {})
    return canonical_json(
        {
            "source_kind": source_ref.get("source_kind"),
            "path": source_ref.get("path"),
            "content_digest": source_ref.get("content_digest"),
        }
    )


def compile_scientific_check_records(
    *,
    registry: ScientificCheckRegistry,
    evaluation: RegistryEvaluation,
    context: FrozenInspectionContext,
    run_id: str,
    created_at: str,
) -> ScientificCheckCompilation:
    """Compile module-local results into existing v0.14 question and evidence records."""

    selected_modules = registry.modules_for_lane(evaluation.lane)
    modules = {module.manifest.check_id: module for module in selected_modules}
    manifests = {
        **{module.manifest.check_id: module.manifest for module in selected_modules},
        **{manifest.check_id: manifest for manifest in registry.unavailable_manifests},
    }
    contracts: list[dict[str, Any]] = []
    assertions: list[dict[str, Any]] = []
    questions: list[dict[str, Any]] = []
    disclosures: list[dict[str, Any]] = []
    for result in evaluation.modules:
        module = modules.get(result.check_id)
        manifest = manifests[result.check_id]
        applicable = [
            observation
            for observation in result.observations
            if observation.applicability == "applicable"
        ]
        scope_path = _canonical_scope_join_path(applicable)
        can_compile = (
            module is not None
            and result.state == "applicable"
            and scope_path is not None
            and bool(applicable)
        )
        if can_compile:
            assert module is not None
            assert scope_path is not None
            contract, module_assertions, question = _compile_applicable_module(
                module,
                applicable,
                context,
                run_id,
                created_at,
                scope_path,
            )
            contracts.append(contract)
            assertions.extend(module_assertions)
            questions.append(question)
        disclosures.append(
            _coverage_disclosure(
                manifest,
                result.state if can_compile else "unsupported" if applicable else result.state,
                result.basis,
                context,
                run_id,
                created_at,
            )
        )
    return ScientificCheckCompilation(
        contracts=tuple(contracts),
        assertions=tuple(assertions),
        questions=tuple(questions),
        disclosures=tuple(disclosures),
    )


def _compile_applicable_module(
    module: ScientificCheckModule,
    observations: list[NormalizedMethodObservation],
    context: FrozenInspectionContext,
    run_id: str,
    created_at: str,
    scope_path: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    manifest = module.manifest
    scope_digest = semantic_digest(scope_path)
    source_refs = _source_refs(context, observations)
    code_dependence_subjects = {
        item.method_target_ref
        for item in observations
        if manifest.check_id
        == "check:authorized-independent-unit-entry-into-row-independent-procedure"
        and manifest.check_version in {"2.1.0", "2.3.0", "3.0.0", "3.1.0"}
        and item.evidence_plane == "static_source"
        and item.method_target_ref is not None
    }
    subject_ref = (
        next(iter(code_dependence_subjects)).to_dict()
        if len(code_dependence_subjects) == 1
        else context.selected_surface_ref.to_dict()
    )
    contract_id = stable_id(
        "contract-analysis-scientific-check",
        run_id,
        manifest.check_id,
        manifest.manifest_digest,
        scope_digest,
    )
    unknown_reason = (
        "The installed check verified one observed operand, but no authority has established "
        "which candidate requirement governs this review."
    )
    contract = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "scientific_contract",
        "contract_id": contract_id,
        "audit_run_id": run_id,
        "title": f"Analysis-scoped requirement for {manifest.check_id}",
        "status": "draft",
        "scope": {"level": "analysis", "subject_refs": [subject_ref]},
        "dimensions": {
            dimension: {
                "state": "unknown",
                "reason": unknown_reason,
                "searched_source_refs": copy.deepcopy(source_refs),
            }
            for dimension in SCIENTIFIC_CONTRACT_DIMENSIONS
        },
        "source_refs": copy.deepcopy(source_refs),
        "created_at": created_at,
        "notes": (
            "Experimental question-only check. Observed wording or source shape does not "
            "establish intended method, execution, numeric causality, or scientific correctness."
        ),
        "extensions": {
            "x-scientific-check-id": manifest.check_id,
            "x-scientific-check-manifest-digest": manifest.manifest_digest,
            "x-scientific-check-scope-join-digest": scope_digest,
        },
    }
    equivalent_groups: dict[str, list[NormalizedMethodObservation]] = {}
    for observation in observations:
        equivalent_groups.setdefault(observation.equivalence_key, []).append(observation)
    module_assertions = []
    for key in sorted(equivalent_groups):
        group = sorted(equivalent_groups[key], key=lambda item: item.adapter_id)
        module_assertions.append(
            _observation_assertion(
                module,
                group[0],
                context,
                run_id,
                created_at,
                scope_digest,
                equivalent_observations=group,
            )
        )
    observed_ids = [str(item["assertion_id"]) for item in module_assertions]
    question_id = stable_id(
        "question-analysis-scientific-check",
        run_id,
        contract_id,
        manifest.dimension,
        *observed_ids,
    )
    question = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "material_question",
        "question_id": question_id,
        "audit_run_id": run_id,
        "question": manifest.permitted_wording,
        "unknown_semantic_dimension": "scientific_contract",
        "why_it_matters": (
            "The exact observed operand can be checked for review-scoped compatibility only "
            "after the scientist identifies the governing requirement or retains it as unknown."
        ),
        "candidate_answers": [
            {
                "answer_id": stable_id("answer-option", question_id, "provide-structured-intent"),
                "label": "Select a listed requirement",
                "value": {"action": "provide_structured_intent"},
                "consequence": (
                    "Only the scientist-selected listed operand governs this review; it does "
                    "not establish historical intent or universal correctness."
                ),
            },
            {
                "answer_id": stable_id("answer-option", question_id, "retain-unknown"),
                "label": "Retain unresolved",
                "value": {"action": "retain_unknown"},
                "consequence": "No method-compatibility conclusion is drawn.",
            },
        ],
        "evidence_searched": [
            {
                "source": "installed scientific-check adapters over immutable selected evidence",
                "result": (
                    f"{len(observations)} exact observation(s) completed finite checks; the "
                    "governing scientific requirement remains unresolved."
                ),
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
            "deterministic_analysis_scientific_check_question_v1", created_at
        ),
        "extensions": {
            "x-contract-ref": typed_ref("scientific_contract", contract_id),
            "x-unresolved-dimensions": [manifest.dimension],
            "x-answer-shape": "one-listed-scientific-check-requirement",
            "x-analysis-subject-ref": subject_ref,
            "x-posthoc-ledger-profile": "posthoc_method_ledger_v1",
            "x-posthoc-comparison-forms": {manifest.dimension: manifest.comparison_form},
            "x-posthoc-reported-assertion-ids": {manifest.dimension: observed_ids},
            "x-scientific-check-id": manifest.check_id,
            "x-scientific-check-version": manifest.check_version,
            "x-scientific-check-manifest-digest": manifest.manifest_digest,
            "x-scientific-check-requirement-candidates": [
                candidate.to_dict() for candidate in manifest.requirement_candidates
            ],
            "x-scientific-check-adapter-bindings": [
                {
                    "adapter_id": observation.adapter_id,
                    "adapter_manifest_digest": observation.adapter_manifest_digest,
                    "observation_digest": observation.observation_digest,
                }
                for observation in observations
            ],
            "x-scientific-check-scope-join-path": scope_path,
            "x-scientific-check-scope-join-digest": scope_digest,
            "x-output-ceiling": "question_only",
        },
    }
    return contract, module_assertions, question


def _canonical_scope_join_path(
    observations: list[NormalizedMethodObservation],
) -> list[dict[str, Any]] | None:
    """Choose one complete path when every shorter observation path is its exact suffix."""

    paths = [
        [edge.to_dict() for edge in observation.scope_join_path] for observation in observations
    ]
    if not paths or any(not path for path in paths):
        return None
    canonical = max(paths, key=lambda path: (len(path), canonical_json(path)))
    if any(path != canonical[-len(path) :] for path in paths):
        return None
    return canonical


def _observation_assertion(
    module: ScientificCheckModule,
    observation: Any,
    context: FrozenInspectionContext,
    run_id: str,
    created_at: str,
    scope_digest: str,
    *,
    equivalent_observations: list[NormalizedMethodObservation] | None = None,
) -> dict[str, Any]:
    manifest = module.manifest
    equivalent = equivalent_observations or [observation]
    source_refs = _source_refs(context, equivalent)
    is_static = observation.evidence_plane == "static_source"
    assertion_id = stable_id(
        "assertion-scientific-check-observation",
        run_id,
        *(item.observation_digest for item in equivalent),
    )
    assertion = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "semantic_assertion",
        "assertion_id": assertion_id,
        "audit_run_id": run_id,
        "subject_ref": observation.method_target_ref.to_dict(),
        "predicate": (
            f"statically_observed_{manifest.dimension}"
            if is_static
            else f"reported_{manifest.dimension}"
        ),
        "object": copy.deepcopy(observation.observed_operand.value),
        "semantic_role": "observed" if is_static else "reported",
        "assertion_class": "deterministic_derivation" if is_static else "explicit_text_extraction",
        "epistemic_status": "accepted",
        "authority_scope": "none" if is_static else "reported_wording",
        "independently_checkable": True,
        "finding_eligibility": "ineligible",
        "verification": {
            "status": "verified",
            "method": "structural_parser" if is_static else "exact_quote_match",
            "validator_id": observation.adapter_id,
            "verified_at": created_at,
        },
        "certainty": {
            "level": "explicit",
            "basis": "The manifest-bound adapter reproduced one exact normalized operand.",
        },
        "rationale": (
            "This assertion records only the exact statically inspected source shape."
            if is_static
            else "This assertion records only the selected report's exact supported wording."
        ),
        "source_refs": source_refs,
        "provenance": {
            "actor": {"actor_kind": "controller", "actor_id": "controller:sc-referee"},
            "method": "deterministic_scientific_check_observation_v1",
            "created_at": created_at,
            "source_refs": copy.deepcopy(source_refs),
            "tool": "sc-referee",
            "tool_version": __version__,
        },
        "extensions": {
            "x-scientific-check-id": manifest.check_id,
            "x-scientific-check-manifest-digest": manifest.manifest_digest,
            "x-scientific-check-adapter-id": observation.adapter_id,
            "x-scientific-check-adapter-manifest-digest": (observation.adapter_manifest_digest),
            "x-normalized-observation-digest": observation.observation_digest,
            "x-equivalent-normalized-observation-digests": [
                item.observation_digest for item in equivalent
            ],
            "x-equivalent-scientific-check-adapters": [
                {
                    "adapter_id": item.adapter_id,
                    "adapter_manifest_digest": item.adapter_manifest_digest,
                }
                for item in equivalent
            ],
            "x-scientific-check-scope-join-digest": scope_digest,
            "x-posthoc-comparison-form": manifest.comparison_form,
            "x-authority-limitation": (
                "No execution, historical intent, numerical causality, or scientific correctness "
                "is established."
            ),
        },
    }
    row_entry = getattr(observation, "row_entry_evidence", None)
    if row_entry is not None:
        projection = row_entry.to_dict()
        if projection.get("profile") == "code_csv_row_entry_evidence_v1":
            assertion["extensions"]["x-code-csv-row-entry-evidence"] = projection
            assertion["extensions"]["x-code-csv-row-entry-evidence-digest"] = semantic_digest(
                projection
            )
        elif projection.get("profile") == "report_csv_row_entry_evidence_v1":
            assertion["extensions"]["x-report-csv-row-entry-evidence"] = projection
            assertion["extensions"]["x-report-csv-row-entry-evidence-digest"] = semantic_digest(
                projection
            )
    return assertion


def _coverage_disclosure(
    manifest: CheckManifest,
    state: str,
    basis: str,
    context: FrozenInspectionContext,
    run_id: str,
    created_at: str,
) -> dict[str, Any]:
    coverage = {
        "applicable": "covered",
        "not_applicable": "not_applicable",
        "ambiguous": "unknown",
        "unsupported": "not_covered",
        "not_installed": "not_covered",
    }.get(state, "not_covered")
    title = {
        "applicable": "Scientific check awaits a review-scoped requirement",
        "not_applicable": "Scientific check is not applicable",
        "ambiguous": "Scientific check remains ambiguous",
        "unsupported": "Scientific check representation is unsupported",
        "not_installed": "Scientific check is not installed",
    }.get(state, "Scientific check did not complete")
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "disclosure",
        "disclosure_id": stable_id(
            "disclosure-scientific-check-coverage",
            run_id,
            manifest.check_id,
            manifest.manifest_digest,
            state,
        ),
        "audit_run_id": run_id,
        "disclosure_kind": "detector_gap" if state != "applicable" else "other",
        "title": title,
        "description": f"{manifest.check_id}: {basis}",
        "importance": "important" if state in {"ambiguous", "unsupported"} else "informational",
        "non_accusatory": True,
        "affected_refs": [context.selected_surface_ref.to_dict()],
        "source_refs": [],
        "coverage_status": coverage,
        "interpretive_consequence": (
            "This experimental question-only check cannot emit a Finding. Unavailable or "
            "unchecked representations remain explicit."
        ),
        "created_at": created_at,
        "provenance": controller_provenance(
            "deterministic_scientific_check_coverage_v1", created_at
        ),
        "extensions": {
            "x-scientific-check-id": manifest.check_id,
            "x-scientific-check-manifest-digest": manifest.manifest_digest,
            "x-scientific-check-state": state,
            "x-output-ceiling": "question_only",
        },
    }


def _source_refs(
    context: FrozenInspectionContext,
    observations: list[NormalizedMethodObservation],
) -> list[dict[str, Any]]:
    values: dict[str, dict[str, Any]] = {}
    documents = {
        item.parser_result_ref: item
        for item in context.documents
        if item.parser_result_ref is not None
    }
    for observation in observations:
        for span in observation.evidence_spans:
            document = documents.get(span.parser_result_ref)
            if (
                document is None
                or document.file_ref != span.file_ref
                or document.path != span.path
                or document.source_location is None
                or document.source_location.content_digest != span.content_digest
            ):
                continue
            value = document.evidence_source_ref(span)
            values[canonical_json(value)] = value
        row_entry = getattr(observation, "row_entry_evidence", None)
        if row_entry is not None:
            material = [
                item
                for item in context.material_inputs
                if item.path == row_entry.material_input_path
                and item.content_digest == row_entry.material_input_content_digest
                and item.file_ref == row_entry.material_file_ref
            ]
            if len(material) == 1:
                value = {
                    "source_kind": "file_span",
                    "locator": row_entry.material_input_path,
                    "path": row_entry.material_input_path,
                    "content_digest": row_entry.material_input_content_digest,
                    "external": False,
                }
                values[canonical_json(value)] = value
    return [values[key] for key in sorted(values)]


def _record_ref(value: dict[str, Any]) -> RecordRef | None:
    record_type = value.get("record_type")
    field = {
        "artifact": "artifact_id",
        "asset_identity": "asset_identity_id",
        "file_record": "file_record_id",
        "operation": "operation_id",
        "parser_result": "parser_result_id",
        "publication_surface": "publication_surface_id",
        "repository_snapshot": "snapshot_id",
        "execution": "execution_id",
        "environment": "environment_id",
        "material_question": "question_id",
        "answer": "answer_id",
    }.get(str(record_type))
    record_id = value.get(field) if field is not None else None
    if not isinstance(record_type, str) or not isinstance(record_id, str):
        return None
    return RecordRef(record_type, record_id)


def _media_type(path: str) -> str:
    suffix = PurePosixPath(path).suffix.lower()
    return {
        ".md": "text/markdown",
        ".markdown": "text/markdown",
        ".rmd": "text/x-r-markdown",
        ".r": "text/x-r",
        ".ipynb": "application/x-ipynb+json",
        ".py": "text/x-python",
        ".qmd": "text/x-quarto",
    }.get(suffix, "application/octet-stream")
