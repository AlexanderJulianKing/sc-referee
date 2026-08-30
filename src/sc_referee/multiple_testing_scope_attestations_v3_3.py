"""Versioned AP-aware wrapper around the frozen asymmetric attestation implementation."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, cast

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.multiple_testing_scope_attestations_v1 import (
    CLOSED_ATTESTATION_ERROR_CATEGORIES,
    COMPLETE_OPTION,
    INCOMPLETE_OPTION,
    UNKNOWN_OPTION,
    AttestationApplication,
    LoadedAttestation,
    MultipleTestingAttestationError,
    load_attestation_file,
)
from sc_referee.multiple_testing_scope_attestations_v1 import (
    apply_attestation as frozen_apply_attestation,
)
from sc_referee.scientific_checks.multiple_testing_scope_questions_v1 import (
    GuidedCoverageProof,
    SourceSpan,
)
from sc_referee.scientific_checks.multiple_testing_scope_questions_v3_3 import (
    APGuidedRecheckContext,
    existing_complete_coverage_recheck,
)

MULTIPLE_TESTING_SCOPE_ATTESTATIONS_V3_3_IMPLEMENTATION_DIGEST = sha256_digest(
    Path(__file__).read_bytes()
)


def _span(value: dict[str, Any]) -> SourceSpan:
    return SourceSpan(
        int(value["start_line"]),
        int(value["start_column"]),
        int(value["end_line"]),
        int(value["end_column"]),
    )


def _proofs_are_answer_removal_equivalent(
    guided: GuidedCoverageProof,
    answer_removed: GuidedCoverageProof,
) -> bool:
    return (
        guided.status == answer_removed.status
        and guided.corrected_positions == answer_removed.corrected_positions
        and guided.proof_digest == answer_removed.proof_digest
    )


def _with_answer_removal_equivalence(
    application: AttestationApplication,
    *,
    equivalent: bool,
) -> AttestationApplication:
    receipt = copy.deepcopy(application.lock_receipt)
    guided_receipt = receipt.get("guided_proof")
    if not isinstance(guided_receipt, dict):
        return application
    guided_receipt["answer_removal_equivalent"] = equivalent
    receipt.pop("receipt_digest", None)
    receipt["receipt_digest"] = semantic_digest(receipt)
    return AttestationApplication(
        application.question,
        application.concern,
        application.answer,
        application.disclosure,
        application.guided_proof,
        receipt,
    )


def apply_attestation(
    loaded: LoadedAttestation,
    *,
    question: dict[str, Any],
    initial_concern: dict[str, Any],
    analysis_content: bytes,
    outcome_columns: tuple[str, ...],
    created_at: str,
    ap_context: APGuidedRecheckContext | None = None,
) -> AttestationApplication:
    """Apply frozen trust rules, then allow only an answer-independent AP complete proof."""

    frozen = frozen_apply_attestation(
        loaded,
        question=question,
        initial_concern=initial_concern,
        analysis_content=analysis_content,
        outcome_columns=outcome_columns,
        created_at=created_at,
    )
    entry = cast(dict[str, Any], loaded.value["answers"][0])
    if (
        entry.get("answer") != COMPLETE_OPTION
        or ap_context is None
        or (frozen.guided_proof is not None and frozen.guided_proof.status == "complete")
    ):
        return frozen
    claimed = entry.get("claimed_correction")
    if not isinstance(claimed, dict) or not isinstance(claimed.get("source_span"), dict):
        return frozen
    extensions = question.get("extensions")
    if not isinstance(extensions, dict) or not isinstance(extensions.get("x-source-span"), dict):
        return frozen
    proof = existing_complete_coverage_recheck(
        analysis_content,
        source_span=_span(cast(dict[str, Any], claimed["source_span"])),
        authorized_count=len(outcome_columns),
        outcome_columns=outcome_columns,
        ap_context=ap_context,
    )
    answer_removed = existing_complete_coverage_recheck(
        analysis_content,
        source_span=_span(cast(dict[str, Any], extensions["x-source-span"])),
        authorized_count=len(outcome_columns),
        outcome_columns=outcome_columns,
        ap_context=ap_context,
    )
    equivalent = _proofs_are_answer_removal_equivalent(proof, answer_removed)
    if proof.status != "complete" or not equivalent:
        return _with_answer_removal_equivalence(frozen, equivalent=equivalent)
    updated_question = copy.deepcopy(frozen.question)
    updated_question["status"] = "answered"
    updated_question["linked_conditional_concern_ids"] = []
    receipt = copy.deepcopy(frozen.lock_receipt)
    receipt["guided_proof"] = {
        "status": proof.status,
        "corrected_positions": list(proof.corrected_positions),
        "proof_root_span": proof.proof_root_span.to_dict(),
        "proof_digest": proof.proof_digest,
        "failure_code": proof.failure_code,
        "answer_removal_equivalent": equivalent,
    }
    receipt.pop("receipt_digest", None)
    receipt["receipt_digest"] = semantic_digest(receipt)
    return AttestationApplication(
        updated_question,
        None,
        frozen.answer,
        None,
        proof,
        receipt,
    )


__all__ = [
    "CLOSED_ATTESTATION_ERROR_CATEGORIES",
    "COMPLETE_OPTION",
    "INCOMPLETE_OPTION",
    "MULTIPLE_TESTING_SCOPE_ATTESTATIONS_V3_3_IMPLEMENTATION_DIGEST",
    "UNKNOWN_OPTION",
    "AttestationApplication",
    "LoadedAttestation",
    "MultipleTestingAttestationError",
    "apply_attestation",
    "load_attestation_file",
]
