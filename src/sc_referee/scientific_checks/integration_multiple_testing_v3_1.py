"""Development-only compilation overlay for multiple-testing 3.1.

The scientific-contract projection is the byte-for-byte 3.0 algorithm applied to the versioned
3.1 observation.  Correction-scope questions are compiled separately after the frozen source
result has been selected; this module never changes a source classification.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id
from sc_referee.method_contracts import SCIENTIFIC_CONTRACT_DIMENSIONS
from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v3 import _authority
from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v3_1 import (
    MULTIPLE_TESTING_CODE_CHECK_ID,
    MultipleTestingCodeEvidenceProjection,
    MultipleTestingCodeObservation,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_1 import (
    select_code_source_envelope,
)
from sc_referee.scientific_checks.core import FrozenInspectionContext, RecordRef
from sc_referee.scientific_checks.integration import (
    ScientificCheckCompilation,
    compile_scientific_check_records,
)
from sc_referee.scientific_checks.multiple_testing_scope_questions_v1 import (
    ScopeQuestionRecords,
    build_scope_question_records,
    locate_correction_scope_witness,
)
from sc_referee.scientific_checks.registry import RegistryEvaluation, ScientificCheckRegistry

MULTIPLE_TESTING_INTEGRATION_IMPLEMENTATION_DIGEST = sha256_digest(Path(__file__).read_bytes())


@dataclass(frozen=True)
class MultipleTestingScopeQuestionCompilation:
    records: ScopeQuestionRecords
    analysis_content: bytes
    outcome_columns: tuple[str, ...]


def compile_multiple_testing_development_records(
    *,
    registry: ScientificCheckRegistry,
    evaluation: RegistryEvaluation,
    context: FrozenInspectionContext,
    run_id: str,
    created_at: str,
) -> ScientificCheckCompilation:
    """Compile the development registry and overlay only an applicable MT observation."""

    compiled = compile_scientific_check_records(
        registry=registry,
        evaluation=evaluation,
        context=context,
        run_id=run_id,
        created_at=created_at,
    )
    if evaluation.lane != "development":
        return compiled
    matching_modules = [
        item for item in evaluation.modules if item.check_id == MULTIPLE_TESTING_CODE_CHECK_ID
    ]
    if len(matching_modules) != 1:
        return compiled
    if matching_modules[0].state == "unsupported":
        return _compile_scope_question_contract(
            compiled=compiled,
            registry=registry,
            module_evaluation=matching_modules[0],
            context=context,
            run_id=run_id,
            created_at=created_at,
        )
    if matching_modules[0].state != "applicable":
        return compiled
    observations = [
        item
        for item in matching_modules[0].observations
        if item.applicability == "applicable"
        and isinstance(item, MultipleTestingCodeObservation)
        and isinstance(item.multiple_testing_evidence, MultipleTestingCodeEvidenceProjection)
        and item.method_target_ref is not None
    ]
    if len(observations) != 1:
        return compiled
    observation = observations[0]
    projection = observation.multiple_testing_evidence
    if not isinstance(projection, MultipleTestingCodeEvidenceProjection):
        return compiled
    analysis_ref = observation.method_target_ref
    if not isinstance(analysis_ref, RecordRef) or analysis_ref.record_type != "file_record":
        return compiled
    fact = projection.to_dict()
    subject_ref = analysis_ref.to_dict()

    assertions = [deepcopy(item) for item in compiled.assertions]
    assertion_matches = [
        item
        for item in assertions
        if item.get("extensions", {}).get("x-scientific-check-id") == MULTIPLE_TESTING_CODE_CHECK_ID
    ]
    contracts = [deepcopy(item) for item in compiled.contracts]
    contract_matches = [
        item
        for item in contracts
        if item.get("extensions", {}).get("x-scientific-check-id") == MULTIPLE_TESTING_CODE_CHECK_ID
    ]
    questions = [deepcopy(item) for item in compiled.questions]
    question_matches = [
        item
        for item in questions
        if item.get("extensions", {}).get("x-scientific-check-id") == MULTIPLE_TESTING_CODE_CHECK_ID
    ]
    if not (
        len(assertion_matches) == 1 and len(contract_matches) == 1 and len(question_matches) == 1
    ):
        return compiled

    assertion_extensions: dict[str, Any] = assertion_matches[0]["extensions"]
    assertion_extensions["x-code-csv-multiple-testing-evidence"] = fact
    assertion_extensions["x-code-csv-multiple-testing-evidence-digest"] = semantic_digest(fact)
    contract_matches[0]["scope"]["subject_refs"] = [subject_ref]
    question_matches[0]["extensions"]["x-analysis-subject-ref"] = subject_ref
    return ScientificCheckCompilation(
        contracts=tuple(contracts),
        assertions=tuple(assertions),
        questions=tuple(questions),
        disclosures=compiled.disclosures,
    )


def _compile_scope_question_contract(
    *,
    compiled: ScientificCheckCompilation,
    registry: ScientificCheckRegistry,
    module_evaluation: Any,
    context: FrozenInspectionContext,
    run_id: str,
    created_at: str,
) -> ScientificCheckCompilation:
    """Add one analysis contract only when the closed question witness exists.

    An unsupported source observation has no operand and therefore cannot be passed through the
    ordinary applicable-observation compiler.  This contract is deliberately assertion-free: it
    supplies the public analysis/authority subject for the additive question without inventing an
    applicable observation or changing the frozen source result.
    """

    if len(module_evaluation.observations) != 1:
        return compiled
    observation = module_evaluation.observations[0]
    reason = observation.abstention_reason
    if reason is None:
        return compiled
    registry_modules = [
        item
        for item in registry.modules_for_lane("development")
        if item.manifest.check_id == MULTIPLE_TESTING_CODE_CHECK_ID
    ]
    if len(registry_modules) != 1:
        return compiled
    manifest = registry_modules[0].manifest
    authority = _authority(context.shared_derivations, manifest)
    if authority is None:
        return compiled
    envelope = select_code_source_envelope(
        base_records=context.base_records,
        documents=context.documents,
    )
    if envelope.reason is not None or envelope.analysis is None:
        return compiled
    analysis = envelope.analysis
    witness = locate_correction_scope_witness(
        analysis.content,
        qualifying_reason=reason,
        authorized_count=len(authority.outcome_columns),
        outcome_columns=authority.outcome_columns,
    )
    if witness is None:
        return compiled
    if any(
        item.get("extensions", {}).get("x-scientific-check-id") == MULTIPLE_TESTING_CODE_CHECK_ID
        for item in compiled.contracts
    ):
        return compiled

    subject_ref = analysis.file_ref.to_dict()
    scope_identity = {
        "profile": "multiple_testing_correction_scope_contract_v1",
        "analysis_ref": subject_ref,
        "analysis_content_digest": analysis.content_digest,
        "authority_binding_digest": authority.binding_digest,
        "question_witness_digest": semantic_digest(witness.to_dict()),
    }
    scope_digest = semantic_digest(scope_identity)
    contract_id = stable_id(
        "contract-analysis-multiple-testing-correction-scope",
        run_id,
        manifest.check_id,
        manifest.manifest_digest,
        scope_digest,
    )
    source_ref = {
        "source_kind": "file_span",
        "locator": analysis.path,
        "path": analysis.path,
        "content_digest": analysis.content_digest,
        "external": False,
    }
    unknown_reason = (
        "The frozen authority declares the family, but the source analyzer did not establish "
        "complete correction scope for this analysis."
    )
    contract = {
        "schema_version": "0.21.0",
        "record_type": "scientific_contract",
        "contract_id": contract_id,
        "audit_run_id": run_id,
        "title": "Analysis-scoped multiple-testing correction-scope contract",
        "status": "draft",
        "scope": {"level": "analysis", "subject_refs": [subject_ref]},
        "dimensions": {
            dimension: {
                "state": "unknown",
                "reason": unknown_reason,
                "searched_source_refs": [deepcopy(source_ref)],
            }
            for dimension in SCIENTIFIC_CONTRACT_DIMENSIONS
        },
        "source_refs": [deepcopy(source_ref)],
        "created_at": created_at,
        "notes": (
            "Question-only contract shell. It records no observed operand and does not change "
            "the unsupported source classification or establish complete correction."
        ),
        "extensions": {
            "x-scientific-check-id": manifest.check_id,
            "x-scientific-check-manifest-digest": manifest.manifest_digest,
            "x-scientific-check-scope-join-digest": scope_digest,
            "x-authority-binding-digest": authority.binding_digest,
            "x-question-purpose": "multiple_testing_correction_scope",
        },
    }
    return ScientificCheckCompilation(
        contracts=(*compiled.contracts, contract),
        assertions=compiled.assertions,
        questions=compiled.questions,
        disclosures=compiled.disclosures,
    )


def compile_multiple_testing_scope_question(
    *,
    registry: ScientificCheckRegistry,
    evaluation: RegistryEvaluation,
    context: FrozenInspectionContext,
    run_id: str,
    created_at: str,
    source_snapshot_digest: str,
    contract_ref: dict[str, str],
    detector_manifest_digest: str,
) -> MultipleTestingScopeQuestionCompilation | None:
    """Compile one additive question only after the exact 3.0 source reason is frozen."""

    if evaluation.lane != "development":
        return None
    modules = [
        item for item in evaluation.modules if item.check_id == MULTIPLE_TESTING_CODE_CHECK_ID
    ]
    registry_modules = [
        item
        for item in registry.modules_for_lane("development")
        if item.manifest.check_id == MULTIPLE_TESTING_CODE_CHECK_ID
    ]
    if len(modules) != 1 or len(registry_modules) != 1 or len(modules[0].observations) != 1:
        return None
    observation = modules[0].observations[0]
    reason = observation.abstention_reason
    if modules[0].state != "unsupported" or reason is None:
        return None
    authority = _authority(context.shared_derivations, registry_modules[0].manifest)
    if authority is None:
        return None
    envelope = select_code_source_envelope(
        base_records=context.base_records,
        documents=context.documents,
    )
    if envelope.reason is not None or envelope.analysis is None:
        return None
    analysis = envelope.analysis
    witness = locate_correction_scope_witness(
        analysis.content,
        qualifying_reason=reason,
        authorized_count=len(authority.outcome_columns),
        outcome_columns=authority.outcome_columns,
    )
    if witness is None:
        return None
    records = build_scope_question_records(
        witness,
        run_id=run_id,
        created_at=created_at,
        source_snapshot_digest=source_snapshot_digest,
        authority_binding_digest=authority.binding_digest,
        analysis_ref=analysis.file_ref.to_dict(),
        contract_ref=contract_ref,
        detector_manifest_digest=detector_manifest_digest,
    )
    return MultipleTestingScopeQuestionCompilation(
        records=records,
        analysis_content=analysis.content,
        outcome_columns=authority.outcome_columns,
    )


__all__ = [
    "MULTIPLE_TESTING_INTEGRATION_IMPLEMENTATION_DIGEST",
    "MultipleTestingScopeQuestionCompilation",
    "compile_multiple_testing_development_records",
    "compile_multiple_testing_scope_question",
]
