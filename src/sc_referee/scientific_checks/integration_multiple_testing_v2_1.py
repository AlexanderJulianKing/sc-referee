"""Development-only compilation overlay for the multiple-testing code slice.

The shared scientific-check integration module is a frozen dependency of qualified checks.  This
overlay delegates to that exact compiler, then adds only the new development check's analysis-file
subject and closed evidence projection.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v2_1 import (
    MULTIPLE_TESTING_CODE_CHECK_ID,
    MultipleTestingCodeEvidenceProjection,
    MultipleTestingCodeObservation,
)
from sc_referee.scientific_checks.core import FrozenInspectionContext, RecordRef
from sc_referee.scientific_checks.integration import (
    ScientificCheckCompilation,
    compile_scientific_check_records,
)
from sc_referee.scientific_checks.registry import RegistryEvaluation, ScientificCheckRegistry

MULTIPLE_TESTING_INTEGRATION_IMPLEMENTATION_DIGEST = sha256_digest(Path(__file__).read_bytes())


def compile_multiple_testing_development_records(
    *,
    registry: ScientificCheckRegistry,
    evaluation: RegistryEvaluation,
    context: FrozenInspectionContext,
    run_id: str,
    created_at: str,
) -> ScientificCheckCompilation:
    """Compile the development registry and overlay only one exact multiple-testing observation."""

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
    if len(matching_modules) != 1 or matching_modules[0].state != "applicable":
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
