from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee_evaluation.qualification_identity import (
    validate_case_author_session_identity_evidence,
    validate_certificate_reveal_evidence,
    validate_identity_registry,
)
from sc_referee_evaluation.selected_result_qualification_io import (
    QualificationIOError,
    RootedReader,
    RootedTreeRead,
)
from sc_referee_evaluation.selected_result_qualification_oracle import (
    ConstructionCertificate,
    FileCertificate,
    OracleState,
    PositiveBindingCertificate,
    SpanCertificate,
    verify_construction_certificate,
)
from sc_referee_evaluation.selected_result_semantic_review import (
    FROZEN_SEMANTIC_REVIEW_CONTRACT_DIGEST,
    revalidate_semantic_reconciliation,
)

QUALIFICATION_CONTROLLER_VERSION = "1.1.0-development"
PYTHON_STATIC_MARKED_REPORT_PROFILE = "selected-result-profile:python-static-marked-report-v1"
FROZEN_ASSIGNMENT_DIGEST = "sha256:d001ff86f8cb986b4623d0b0781f1d9e8c47c27fcfc15a46fbbd2ec79c211f1b"
_REASON_CODES_BY_STATE: dict[str, frozenset[str]] = {
    "V": frozenset(),
    "A": frozenset({"multiple_selected_result_bindings_rederived"}),
    "I": frozenset(
        {
            "selected_report_missing",
            "selected_report_empty",
            "selected_result_marker_missing",
            "selected_report_writer_not_rederived",
            "selected_report_source_operand_empty",
            "selected_report_source_operand_not_rederived",
            "selected_report_bytes_do_not_match_static_writer",
            "selected_report_source_operand_missing",
            "selected_report_subscript_out_of_range",
            "static_numeric_conversion_failed",
        }
    ),
    "U": frozenset(
        {
            "text_io_runtime_unsupported",
            "unsupported_selected_report_role",
            "selected_result_candidate_ceiling_exceeded",
            "unsupported_non_python_source_artifact",
            "python_source_absent",
            "python_source_byte_ceiling_exceeded",
            "python_source_parse_failed",
            "python_ast_node_ceiling_exceeded",
            "python_module_without_selected_report_writer",
            "unsupported_source_operand_role",
            "unclassified_case_artifact",
            "unsupported_possible_report_writer",
            "dynamic_or_unsupported_report_writer",
            "unsupported_selected_report_writer_signature",
            "conditional_or_nested_selected_report_writer",
            "selected_report_writer_value_type_unsupported",
            "selected_report_text_not_utf8_encodable",
            "selected_report_self_dependency",
            "opaque_or_unallowlisted_python_call",
            "python_module_statement_ceiling_exceeded",
            "non_straight_line_module_statement",
            "unsupported_python_import_binding",
            "reserved_python_binding_reassigned",
            "static_value_byte_ceiling_exceeded",
            "static_sequence_item_ceiling_exceeded",
            "static_integer_bit_ceiling_exceeded",
            "static_evaluation_step_ceiling_exceeded",
            "unsupported_selected_report_dependency_flow",
            "unsupported_formatted_selected_result",
            "unsupported_selected_report_addition",
            "unsupported_selected_report_subscript",
            "unsupported_static_source_read",
            "unsupported_selected_report_keyword_argument",
            "unsupported_selected_report_method",
            "unsupported_selected_report_call",
            "unsupported_selected_report_expression",
            "non_utf8_selected_result_evidence",
            "unsupported_python_encoding_declaration",
            "non_lf_normalized_text_evidence",
            "non_ascii_text_evidence",
            "selected_result_line_ceiling_exceeded",
        }
    ),
}


class SelectedResultVerifierQualificationError(ValueError):
    """Raised when a verifier-qualification artifact cannot replay exactly."""


def load_construction_certificate(path: Path) -> ConstructionCertificate:
    """Load the closed JSON representation authored outside the verifier package."""

    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SelectedResultVerifierQualificationError(
            "Construction certificate must be one JSON object."
        )
    return parse_construction_certificate(value)


def parse_construction_certificate(value: Mapping[str, Any]) -> ConstructionCertificate:
    """Parse certificate values already obtained through a trusted byte reader."""

    return _construction_certificate(value)


def _construction_certificate(value: Mapping[str, Any]) -> ConstructionCertificate:
    certificate = dict(value)
    _exact_keys(
        certificate,
        {
            "case_id",
            "expected_state",
            "files",
            "spans",
            "positive_binding",
            "reason_codes",
            "certificate_version",
            "certificate_digest",
        },
        "construction certificate",
    )
    files = tuple(
        FileCertificate(
            path=_text(item.get("path"), "file path"),
            size=_integer(item.get("size"), "file size"),
            sha256=_text(item.get("sha256"), "file sha256"),
        )
        for item in _object_sequence(certificate["files"], "files")
    )
    spans = tuple(
        SpanCertificate(
            span_id=_text(item.get("span_id"), "span_id"),
            path=_text(item.get("path"), "span path"),
            start=_integer(item.get("start"), "span start"),
            end=_integer(item.get("end"), "span end"),
            sha256=_text(item.get("sha256"), "span sha256"),
        )
        for item in _object_sequence(certificate["spans"], "spans")
    )
    raw_binding = certificate["positive_binding"]
    binding: PositiveBindingCertificate | None
    if raw_binding is None:
        binding = None
    elif isinstance(raw_binding, dict):
        _exact_keys(
            raw_binding,
            {"result_span_id", "producer_span_id", "operand_span_ids", "report_span_id"},
            "positive binding certificate",
        )
        binding = PositiveBindingCertificate(
            result_span_id=_text(raw_binding["result_span_id"], "result_span_id"),
            producer_span_id=_text(raw_binding["producer_span_id"], "producer_span_id"),
            operand_span_ids=tuple(
                _text(item, "operand_span_id")
                for item in _sequence(raw_binding["operand_span_ids"], "operand_span_ids")
            ),
            report_span_id=_text(raw_binding["report_span_id"], "report_span_id"),
        )
    else:
        raise SelectedResultVerifierQualificationError(
            "positive_binding must be an object or null."
        )
    expected_state = _text(certificate["expected_state"], "expected_state")
    if expected_state not in {"V", "A", "I", "U"}:
        raise SelectedResultVerifierQualificationError("Expected state must be V, A, I, or U.")
    return ConstructionCertificate(
        case_id=_text(certificate["case_id"], "case_id"),
        expected_state=cast(OracleState, expected_state),
        files=files,
        spans=spans,
        positive_binding=binding,
        reason_codes=tuple(
            _text(item, "reason_code")
            for item in _sequence(certificate["reason_codes"], "reason_codes")
        ),
        certificate_version=_text(certificate["certificate_version"], "certificate_version"),
        certificate_digest=_text(certificate["certificate_digest"], "certificate_digest"),
    )


def freeze_semantic_attestation(
    *,
    case_root: Path,
    certificate: ConstructionCertificate,
    target_packet: Mapping[str, Any],
    assignment_manifest: Mapping[str, Any],
    block: str,
    provider_slot: str,
    runner_freeze_digest: str,
    author_identity: Mapping[str, Any],
    validator_identity: Mapping[str, Any],
    semantic_conclusion: Mapping[str, Any],
    independence_declaration: Mapping[str, Any],
    review_evidence_digest: str,
    completed_at: str,
) -> dict[str, Any]:
    """Reject the invalidated single-stage attestation API.

    Experiment 0054 allowed the certificate to be present while a purportedly blind conclusion
    was first frozen.  Callers must now use ``freeze_blind_semantic_review`` from
    ``selected_result_semantic_review`` and subsequently create a separate reconciliation.
    """

    del (
        case_root,
        certificate,
        target_packet,
        assignment_manifest,
        block,
        provider_slot,
        runner_freeze_digest,
        author_identity,
        validator_identity,
        semantic_conclusion,
        independence_declaration,
        review_evidence_digest,
        completed_at,
    )
    raise SelectedResultVerifierQualificationError(
        "Single-stage semantic attestations are invalidated; freeze a certificate-blind review "
        "and a separate post-reveal reconciliation."
    )


def freeze_oracle_proof(
    *,
    case_root: Path,
    certificate: ConstructionCertificate,
    target_packet: Mapping[str, Any],
    oracle_identity: Mapping[str, Any],
    completed_at: str,
    assignment_manifest: Mapping[str, Any] | None = None,
    block: str = "",
    provider_slot: str = "",
    runner_freeze_digest: str = "",
    author_identity: Mapping[str, Any] | None = None,
    author_identity_evidence: Mapping[str, Any] | None = None,
    semantic_contract: Mapping[str, Any] | None = None,
    identity_registry: Mapping[str, Any] | None = None,
    frozen_identity_registry_digest: str,
    semantic_reconciliations: Sequence[Mapping[str, Any]] = (),
    certificate_reveal_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Freeze a certificate-backed oracle proof before target output is available."""

    packet = _target_packet(target_packet)
    assignment_binding = _assignment_binding(
        assignment_manifest,
        packet=packet,
        block=block,
        provider_slot=provider_slot,
    )
    runner_digest = _digest(runner_freeze_digest, "runner_freeze_digest")
    if packet["case_id"] != certificate.case_id:
        raise SelectedResultVerifierQualificationError(
            "Target packet and certificate case identities differ."
        )
    if author_identity is None:
        raise SelectedResultVerifierQualificationError(
            "Case-author identity is required for semantic independence."
        )
    author = _identity(author_identity, "case author")
    if author_identity_evidence is None:
        raise SelectedResultVerifierQualificationError(
            "Registrar-authenticated case-author session evidence is required."
        )
    if semantic_contract is None:
        raise SelectedResultVerifierQualificationError(
            "The frozen semantic review contract is required."
        )
    contract = _semantic_review_contract(semantic_contract)
    if identity_registry is None:
        raise SelectedResultVerifierQualificationError("The frozen identity registry is required.")
    registry = _qualification_identity_registry(identity_registry)
    expected_registry_digest = _digest(
        frozen_identity_registry_digest,
        "frozen_identity_registry_digest",
    )
    if registry["identity_registry_digest"] != expected_registry_digest:
        raise SelectedResultVerifierQualificationError(
            "Qualification identity registry does not match the frozen runner binding."
        )
    case_inventory = _immutable_case_inventory(case_root)
    _require_certificate_inventory(certificate, case_inventory)
    author_evidence = _validated_case_author_evidence(
        author_identity_evidence,
        registry=registry,
        author_identity=author,
        certificate=certificate,
        packet=packet,
        assignment=assignment_binding,
        runner_freeze_digest=runner_digest,
        semantic_contract=contract,
        case_inventory=case_inventory,
    )
    author_completed = _provider_completion_time(author_evidence, "case-author session")
    result = verify_construction_certificate(certificate, case_root)
    identity = _identity(oracle_identity, "oracle")
    proof_completed = _timestamp(completed_at)
    if author_completed >= proof_completed:
        raise SelectedResultVerifierQualificationError(
            "Case-author completion must predate the oracle proof."
        )
    reconciliations = _validated_reconciliation_panel(
        semantic_reconciliations,
        case_root=case_root,
        certificate=certificate,
        packet=packet,
        assignment=assignment_binding,
        runner_freeze_digest=runner_digest,
        author_identity=author,
        author_completed_at=author_completed,
        semantic_contract=contract,
        identity_registry=registry,
    )
    reveal_evidence = _validated_certificate_reveal(
        certificate_reveal_evidence,
        reconciliations=reconciliations,
        registry=registry,
        certificate=certificate,
        assignment=assignment_binding,
        runner_freeze_digest=runner_digest,
        author_completed_at=author_completed,
    )
    if any(_timestamp(str(item["reconciled_at"])) > proof_completed for item in reconciliations):
        raise SelectedResultVerifierQualificationError(
            "Oracle proof predates a required semantic reconciliation."
        )
    record: dict[str, Any] = {
        "artifact_kind": "selected_result_verifier_oracle_proof",
        "qualification_controller_version": QUALIFICATION_CONTROLLER_VERSION,
        "case_id": result.case_id,
        "target_packet": packet,
        "assignment_binding": assignment_binding,
        "runner_freeze_digest": runner_digest,
        "author_identity": author,
        "author_identity_evidence": author_evidence,
        "case_inventory": case_inventory,
        "case_inventory_digest": semantic_digest(case_inventory),
        "semantic_contract": contract,
        "identity_registry": registry,
        "frozen_identity_registry_digest": expected_registry_digest,
        "semantic_reconciliations": reconciliations,
        "certificate_reveal_evidence": reveal_evidence,
        "oracle_identity": identity,
        "construction_certificate": asdict(certificate),
        "oracle_result": asdict(result),
        "oracle_implementation": _module_lock(
            Path(__file__).with_name("selected_result_qualification_oracle.py")
        ),
        "completed_at": _iso(proof_completed),
        "target_output_available": False,
        "qualification_authority": "none_oracle_proof_only",
    }
    record["oracle_proof_digest"] = semantic_digest(record)
    return record


def freeze_target_output(
    *,
    case_root: Path,
    target_packet: Mapping[str, Any],
    validator_identity: Mapping[str, Any],
    derived_at: str,
    frozen_at: str,
    assignment_manifest: Mapping[str, Any] | None = None,
    block: str = "",
    provider_slot: str = "",
    runner_freeze_digest: str = "",
) -> dict[str, Any]:
    """Run and freeze the target without accepting any oracle or certificate input."""

    from sc_referee_evaluation.prospective_selected_result_verifier import (
        freeze_independent_selected_result_derivation,
        revalidate_independent_selected_result_derivation,
    )

    packet = _target_packet(target_packet)
    assignment_binding = _assignment_binding(
        assignment_manifest,
        packet=packet,
        block=block,
        provider_slot=provider_slot,
    )
    runner_digest = _digest(runner_freeze_digest, "runner_freeze_digest")
    derivation = freeze_independent_selected_result_derivation(
        case_root,
        {
            "case_id": packet["case_id"],
            "validator_identity": _target_validator_identity(validator_identity),
            "profile_id": packet["profile_id"],
            "selected_report_path": packet["selected_report_path"],
            "derived_at": derived_at,
        },
        frozen_at=frozen_at,
    )
    replayed = revalidate_independent_selected_result_derivation(derivation, case_root)
    record: dict[str, Any] = {
        "artifact_kind": "selected_result_verifier_qualification_target_output",
        "qualification_controller_version": QUALIFICATION_CONTROLLER_VERSION,
        "case_id": packet["case_id"],
        "target_packet": packet,
        "assignment_binding": assignment_binding,
        "runner_freeze_digest": runner_digest,
        "target_derivation": replayed,
        "qualification_authority": "none_qualification_target_output_only",
    }
    record["qualification_target_output_digest"] = semantic_digest(record)
    return record


def freeze_qualification_validation(
    *,
    case_root: Path,
    case_contract: Mapping[str, Any],
    qualification_target_output: Mapping[str, Any],
    assignment_manifest: Mapping[str, Any],
    validation_identity: Mapping[str, Any],
    declaration_revealed_at: str,
    compared_at: str,
) -> dict[str, Any]:
    """Run and bind the validation wrapper after blind derivation is frozen."""

    from sc_referee_evaluation.prospective_selected_result_verifier import (
        freeze_selected_result_validation,
        validate_selected_result_validation,
    )

    target_record = _revalidate_qualification_target_output(
        qualification_target_output,
        case_root,
        assignment_manifest=assignment_manifest,
    )
    derivation = _mapping(target_record["target_derivation"], "target_derivation")
    validation = freeze_selected_result_validation(
        case_root,
        case_contract,
        derivation,
        declaration_revealed_at=declaration_revealed_at,
        compared_at=compared_at,
    )
    replayed = validate_selected_result_validation(
        validation,
        case_root=case_root,
        case_contract=case_contract,
    )
    record: dict[str, Any] = {
        "artifact_kind": "selected_result_verifier_qualification_validation",
        "qualification_controller_version": QUALIFICATION_CONTROLLER_VERSION,
        "case_id": target_record["case_id"],
        "assignment_binding": target_record["assignment_binding"],
        "runner_freeze_digest": target_record["runner_freeze_digest"],
        "qualification_target_output_digest": target_record["qualification_target_output_digest"],
        "validation_identity": _identity(validation_identity, "validation runner"),
        "case_contract_digest": replayed["case_contract_digest"],
        "case_contract": dict(case_contract),
        "target_validation": replayed,
        "qualification_authority": "none_qualification_validation_only",
    }
    record["qualification_validation_digest"] = semantic_digest(record)
    return record


def freeze_verifier_comparison(
    *,
    case_root: Path,
    oracle_proof: Mapping[str, Any],
    target_derivation: Mapping[str, Any],
    target_validation: Mapping[str, Any],
    comparison_identity: Mapping[str, Any],
    compared_at: str,
    frozen_identity_registry_digest: str,
    assignment_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare only after both independently frozen inputs exist."""

    proof = _revalidate_oracle_proof(
        oracle_proof,
        case_root,
        assignment_manifest=assignment_manifest,
        frozen_identity_registry_digest=frozen_identity_registry_digest,
    )
    target_record = _revalidate_qualification_target_output(
        target_derivation, case_root, assignment_manifest=assignment_manifest
    )
    target = _mapping(target_record["target_derivation"], "target_derivation")
    validation_record = _revalidate_qualification_validation(
        target_validation,
        case_root,
        assignment_manifest=assignment_manifest,
    )
    validation = _mapping(validation_record["target_validation"], "target_validation")
    comparison_actor = _identity(comparison_identity, "comparison runner")
    _require_phase_identity_separation(
        proof=proof,
        target=target,
        validation_record=validation_record,
        comparison_identity=comparison_actor,
    )
    if proof.get("target_output_available") is not False:
        raise SelectedResultVerifierQualificationError(
            "Oracle proof was not frozen before target-output reveal."
        )
    if proof.get("case_id") != target.get("case_id"):
        raise SelectedResultVerifierQualificationError(
            "Oracle proof and target derivation case identities differ."
        )
    if proof.get("assignment_binding") != target_record.get("assignment_binding"):
        raise SelectedResultVerifierQualificationError(
            "Oracle proof and target output have different assignment bindings."
        )
    if proof.get("runner_freeze_digest") != target_record.get("runner_freeze_digest"):
        raise SelectedResultVerifierQualificationError(
            "Oracle proof and target output have different runner freezes."
        )
    if (
        validation_record.get("assignment_binding") != proof.get("assignment_binding")
        or validation_record.get("runner_freeze_digest") != proof.get("runner_freeze_digest")
        or validation_record.get("qualification_target_output_digest")
        != target_record.get("qualification_target_output_digest")
        or validation.get("derivation_digest") != target.get("derivation_digest")
    ):
        raise SelectedResultVerifierQualificationError(
            "Validation wrapper does not bind the same frozen target opportunity."
        )
    packet = _target_packet(_mapping(proof.get("target_packet"), "target_packet"))
    if (
        target.get("case_id") != packet["case_id"]
        or target.get("profile_id") != packet["profile_id"]
        or target.get("selected_report_path") != packet["selected_report_path"]
    ):
        raise SelectedResultVerifierQualificationError(
            "Target derivation does not match the frozen target packet."
        )
    oracle_completed = _timestamp(str(proof.get("completed_at", "")))
    target_derived = _timestamp(str(target.get("derived_at", "")))
    target_frozen = _timestamp(str(target.get("frozen_at", "")))
    validation_completed = _timestamp(str(validation.get("completed_at", "")))
    comparison_time = _timestamp(str(compared_at))
    if target_derived < oracle_completed:
        raise SelectedResultVerifierQualificationError(
            "Target derivation predates the frozen oracle proof."
        )
    if comparison_time < target_frozen:
        raise SelectedResultVerifierQualificationError(
            "Comparison predates the frozen target output."
        )
    if comparison_time < validation_completed:
        raise SelectedResultVerifierQualificationError(
            "Comparison predates the frozen validation-wrapper output."
        )
    raw_oracle = proof.get("oracle_result")
    if not isinstance(raw_oracle, dict):
        raise SelectedResultVerifierQualificationError("Oracle result is absent.")
    expected_state = _text(raw_oracle.get("expected_state"), "oracle expected_state")
    observed_state = _target_state(target.get("derivation_status"))
    state_matches = expected_state == observed_state
    expected_reasons = _expected_target_reasons(expected_state, raw_oracle.get("reason_codes"))
    observed_reasons = tuple(
        _text(item, "target reason_code")
        for item in _sequence(target.get("reason_codes"), "target reason_codes")
    )
    reasons_match = expected_reasons == observed_reasons
    expected_validation_status, expected_validation_reasons = _expected_validation_outcome(
        expected_state, expected_reasons
    )
    observed_validation_status = _text(validation.get("status"), "target validation status")
    observed_validation_reasons = tuple(
        _text(item, "target validation reason_code")
        for item in _sequence(validation.get("reason_codes"), "target validation reason_codes")
    )
    validation_matches = (
        observed_validation_status == expected_validation_status
        and observed_validation_reasons == expected_validation_reasons
    )
    binding_matches = False
    if expected_state == "V" and observed_state == "V":
        binding_matches = _positive_binding_matches(case_root, raw_oracle, target)
    elif expected_state == "A" and observed_state == "A":
        candidates = target.get("candidate_bindings")
        binding_matches = isinstance(candidates, list) and len(candidates) > 1
    elif expected_state in {"I", "U"} and observed_state in {"I", "U"}:
        binding_matches = not target.get("candidate_bindings")

    if observed_state == "V" and expected_state != "V":
        outcome = "false_complete"
    elif observed_validation_status == "verified_complete" and expected_state != "V":
        outcome = "false_complete"
    elif expected_state == "V" and observed_state != "V":
        outcome = "false_incomplete"
    elif expected_state == "V" and not binding_matches:
        outcome = "binding_mismatch"
    elif not state_matches or not reasons_match or not validation_matches:
        outcome = "state_or_reason_mismatch"
    elif not binding_matches:
        outcome = "binding_mismatch"
    else:
        outcome = "exact_match"
    record: dict[str, Any] = {
        "artifact_kind": "selected_result_verifier_qualification_comparison",
        "qualification_controller_version": QUALIFICATION_CONTROLLER_VERSION,
        "case_id": target["case_id"],
        "oracle_proof_digest": proof["oracle_proof_digest"],
        "target_derivation_digest": target["derivation_digest"],
        "qualification_target_output_digest": target_record["qualification_target_output_digest"],
        "qualification_validation_digest": validation_record["qualification_validation_digest"],
        "assignment_binding": proof["assignment_binding"],
        "runner_freeze_digest": proof["runner_freeze_digest"],
        "comparison_identity": comparison_actor,
        "expected_state": expected_state,
        "observed_state": observed_state,
        "expected_reason_codes": list(expected_reasons),
        "observed_reason_codes": list(observed_reasons),
        "expected_validation_status": expected_validation_status,
        "observed_validation_status": observed_validation_status,
        "expected_validation_reason_codes": list(expected_validation_reasons),
        "observed_validation_reason_codes": list(observed_validation_reasons),
        "state_matches": state_matches,
        "reason_codes_match": reasons_match,
        "validation_matches": validation_matches,
        "binding_matches": binding_matches,
        "comparison_outcome": outcome,
        "compared_at": _iso(comparison_time),
        "qualification_authority": "none_case_comparison_only",
    }
    record["comparison_digest"] = semantic_digest(record)
    return record


def _positive_binding_matches(
    case_root: Path, oracle_result: Mapping[str, Any], target: Mapping[str, Any]
) -> bool:
    raw_binding = oracle_result.get("positive_binding")
    candidates = target.get("candidate_bindings")
    if (
        not isinstance(raw_binding, dict)
        or not isinstance(candidates, list)
        or len(candidates) != 1
    ):
        return False
    candidate = candidates[0]
    if not isinstance(candidate, dict):
        return False
    try:
        with RootedReader(case_root) as reader:
            case_tree = reader.read_case_tree()
        expected_report = _exact_span_locator(case_tree, raw_binding["report"], role="report")
        expected_result = _exact_span_locator(case_tree, raw_binding["result"], role="result")
        expected_producer = _exact_span_locator(case_tree, raw_binding["producer"], role="producer")
        raw_operands = raw_binding["operands"]
        if not isinstance(raw_operands, (list, tuple)):
            return False
        expected_operands = sorted(
            (_exact_span_locator(case_tree, item, role="operand") for item in raw_operands),
            key=lambda item: (str(item["path"]), int(item["start_line"])),
        )
        actual_operands = candidate.get("source_operands")
        if not isinstance(actual_operands, list):
            return False
        actual_operand_locators = sorted(
            (item["source_locator"] for item in actual_operands if isinstance(item, dict)),
            key=lambda item: (str(item["path"]), int(item["start_line"])),
        )
    except (KeyError, TypeError, ValueError, OSError, QualificationIOError):
        return False
    expected = (expected_report, expected_result, expected_producer, *expected_operands)
    return (
        candidate.get("report_locator") == _locator_projection(expected_report)
        and candidate.get("result_locator") == _locator_projection(expected_result)
        and candidate.get("producer_locator") == _locator_projection(expected_producer)
        and actual_operand_locators == [_locator_projection(item) for item in expected_operands]
        and candidate.get("alternative_producer_locators") == []
        and all(_target_receipt_matches(target, item) for item in expected)
    )


def _revalidate_oracle_proof(
    value: Mapping[str, Any],
    case_root: Path,
    *,
    assignment_manifest: Mapping[str, Any] | None,
    frozen_identity_registry_digest: str,
) -> dict[str, Any]:
    proof = _self_digested(value, "oracle_proof_digest")
    required = {
        "artifact_kind",
        "qualification_controller_version",
        "case_id",
        "target_packet",
        "assignment_binding",
        "runner_freeze_digest",
        "author_identity",
        "author_identity_evidence",
        "case_inventory",
        "case_inventory_digest",
        "semantic_contract",
        "identity_registry",
        "frozen_identity_registry_digest",
        "semantic_reconciliations",
        "certificate_reveal_evidence",
        "oracle_identity",
        "construction_certificate",
        "oracle_result",
        "oracle_implementation",
        "completed_at",
        "target_output_available",
        "qualification_authority",
        "oracle_proof_digest",
    }
    _exact_keys(proof, required, "oracle proof")
    if (
        proof["artifact_kind"] != "selected_result_verifier_oracle_proof"
        or proof["qualification_controller_version"] != QUALIFICATION_CONTROLLER_VERSION
        or proof["target_output_available"] is not False
        or proof["qualification_authority"] != "none_oracle_proof_only"
        or proof["oracle_implementation"]
        != _module_lock(Path(__file__).with_name("selected_result_qualification_oracle.py"))
    ):
        raise SelectedResultVerifierQualificationError("Oracle proof identity has drifted.")
    packet = _target_packet(_mapping(proof["target_packet"], "target_packet"))
    _digest(proof["runner_freeze_digest"], "runner_freeze_digest")
    assignment = _validate_assignment_binding(
        _mapping(proof["assignment_binding"], "assignment_binding"), packet=packet
    )
    expected_assignment = _assignment_binding(
        assignment_manifest,
        packet=packet,
        block=str(assignment["block"]),
        provider_slot=str(assignment["provider_slot"]),
    )
    author = _identity(_mapping(proof["author_identity"], "author_identity"), "case author")
    _identity(_mapping(proof["oracle_identity"], "oracle_identity"), "oracle")
    contract = _semantic_review_contract(_mapping(proof["semantic_contract"], "semantic_contract"))
    registry = _qualification_identity_registry(
        _mapping(proof["identity_registry"], "identity_registry")
    )
    expected_registry_digest = _digest(
        frozen_identity_registry_digest,
        "frozen_identity_registry_digest",
    )
    if (
        proof["frozen_identity_registry_digest"] != expected_registry_digest
        or registry["identity_registry_digest"] != expected_registry_digest
    ):
        raise SelectedResultVerifierQualificationError(
            "Oracle proof identity registry does not match the frozen runner binding."
        )
    certificate = _construction_certificate(
        _mapping(proof["construction_certificate"], "construction_certificate")
    )
    case_inventory = _immutable_case_inventory(case_root)
    _require_certificate_inventory(certificate, case_inventory)
    author_evidence = _validated_case_author_evidence(
        _mapping(proof["author_identity_evidence"], "author_identity_evidence"),
        registry=registry,
        author_identity=author,
        certificate=certificate,
        packet=packet,
        assignment=assignment,
        runner_freeze_digest=str(proof["runner_freeze_digest"]),
        semantic_contract=contract,
        case_inventory=case_inventory,
    )
    author_completed = _provider_completion_time(author_evidence, "case-author session")
    result = verify_construction_certificate(certificate, case_root)
    proof_completed = _timestamp(_text(proof["completed_at"], "completed_at"))
    if author_completed >= proof_completed:
        raise SelectedResultVerifierQualificationError(
            "Case-author completion must predate the oracle proof."
        )
    reconciliations = _validated_reconciliation_panel(
        _object_sequence(proof["semantic_reconciliations"], "semantic_reconciliations"),
        case_root=case_root,
        certificate=certificate,
        packet=packet,
        assignment=assignment,
        runner_freeze_digest=str(proof["runner_freeze_digest"]),
        author_identity=author,
        author_completed_at=author_completed,
        semantic_contract=contract,
        identity_registry=registry,
    )
    reveal_evidence = _validated_certificate_reveal(
        _mapping(proof["certificate_reveal_evidence"], "certificate_reveal_evidence"),
        reconciliations=reconciliations,
        registry=registry,
        certificate=certificate,
        assignment=assignment,
        runner_freeze_digest=str(proof["runner_freeze_digest"]),
        author_completed_at=author_completed,
    )
    if any(_timestamp(str(item["reconciled_at"])) > proof_completed for item in reconciliations):
        raise SelectedResultVerifierQualificationError(
            "Oracle proof predates a required semantic reconciliation."
        )
    if (
        proof["case_id"] != certificate.case_id
        or packet["case_id"] != certificate.case_id
        or assignment["case_id"] != certificate.case_id
        or assignment != expected_assignment
        or proof["oracle_result"] != asdict(result)
        or proof["author_identity_evidence"] != author_evidence
        or proof["case_inventory"] != case_inventory
        or proof["case_inventory_digest"] != semantic_digest(case_inventory)
        or proof["semantic_contract"] != contract
        or proof["identity_registry"] != registry
        or proof["semantic_reconciliations"] != reconciliations
        or proof["certificate_reveal_evidence"] != reveal_evidence
    ):
        raise SelectedResultVerifierQualificationError(
            "Oracle proof does not replay from its certificate and case bytes."
        )
    return proof


def _revalidate_qualification_target_output(
    value: Mapping[str, Any],
    case_root: Path,
    *,
    assignment_manifest: Mapping[str, Any] | None,
) -> dict[str, Any]:
    from sc_referee_evaluation.prospective_selected_result_verifier import (
        revalidate_independent_selected_result_derivation,
    )

    record = _self_digested(value, "qualification_target_output_digest")
    common_keys = {
        "artifact_kind",
        "case_id",
        "target_packet",
        "assignment_binding",
        "runner_freeze_digest",
        "target_derivation",
        "qualification_authority",
        "qualification_target_output_digest",
    }
    controller_keys = common_keys | {"qualification_controller_version"}
    worker_keys = common_keys | {
        "target_worker_version",
        "release_gate_digest",
        "target_authorization_digest",
    }
    if set(record) == controller_keys:
        if record["qualification_controller_version"] != QUALIFICATION_CONTROLLER_VERSION:
            raise SelectedResultVerifierQualificationError(
                "Qualification target-output controller version has drifted."
            )
    elif set(record) == worker_keys:
        from sc_referee_evaluation.selected_result_qualification_target_worker import (
            TARGET_WORKER_VERSION,
        )

        if record["target_worker_version"] != TARGET_WORKER_VERSION:
            raise SelectedResultVerifierQualificationError(
                "Qualification target-output worker version has drifted."
            )
        _digest(record["release_gate_digest"], "release_gate_digest")
        _digest(record["target_authorization_digest"], "target_authorization_digest")
    else:
        raise SelectedResultVerifierQualificationError(
            "Qualification target output has an unsupported shape."
        )
    if (
        record["artifact_kind"] != "selected_result_verifier_qualification_target_output"
        or record["qualification_authority"] != "none_qualification_target_output_only"
    ):
        raise SelectedResultVerifierQualificationError(
            "Qualification target-output identity has drifted."
        )
    packet = _target_packet(_mapping(record["target_packet"], "target_packet"))
    _digest(record["runner_freeze_digest"], "runner_freeze_digest")
    assignment = _validate_assignment_binding(
        _mapping(record["assignment_binding"], "assignment_binding"), packet=packet
    )
    expected_assignment = _assignment_binding(
        assignment_manifest,
        packet=packet,
        block=str(assignment["block"]),
        provider_slot=str(assignment["provider_slot"]),
    )
    derivation = revalidate_independent_selected_result_derivation(
        _mapping(record["target_derivation"], "target_derivation"), case_root
    )
    if (
        record["case_id"] != packet["case_id"]
        or assignment["case_id"] != packet["case_id"]
        or assignment != expected_assignment
        or derivation["case_id"] != packet["case_id"]
        or derivation["profile_id"] != packet["profile_id"]
        or derivation["selected_report_path"] != packet["selected_report_path"]
    ):
        raise SelectedResultVerifierQualificationError(
            "Qualification target output does not replay from its assignment packet."
        )
    return record


def _revalidate_qualification_validation(
    value: Mapping[str, Any],
    case_root: Path,
    *,
    assignment_manifest: Mapping[str, Any] | None,
) -> dict[str, Any]:
    from sc_referee_evaluation.prospective_selected_result_verifier import (
        validate_selected_result_validation,
    )

    record = _self_digested(value, "qualification_validation_digest")
    _exact_keys(
        record,
        {
            "artifact_kind",
            "qualification_controller_version",
            "case_id",
            "assignment_binding",
            "runner_freeze_digest",
            "qualification_target_output_digest",
            "validation_identity",
            "case_contract_digest",
            "case_contract",
            "target_validation",
            "qualification_authority",
            "qualification_validation_digest",
        },
        "qualification validation",
    )
    if (
        record["artifact_kind"] != "selected_result_verifier_qualification_validation"
        or record["qualification_controller_version"] != QUALIFICATION_CONTROLLER_VERSION
        or record["qualification_authority"] != "none_qualification_validation_only"
    ):
        raise SelectedResultVerifierQualificationError(
            "Qualification validation identity has drifted."
        )
    binding = _mapping(record["assignment_binding"], "assignment_binding")
    packet = _target_packet(_mapping(binding.get("target_packet"), "target_packet"))
    assignment = _validate_assignment_binding(binding, packet=packet)
    expected_assignment = _assignment_binding(
        assignment_manifest,
        packet=packet,
        block=str(assignment["block"]),
        provider_slot=str(assignment["provider_slot"]),
    )
    case_contract = _mapping(record["case_contract"], "case_contract")
    _identity(
        _mapping(record["validation_identity"], "validation_identity"),
        "validation runner",
    )
    validation = validate_selected_result_validation(
        _mapping(record["target_validation"], "target_validation"),
        case_root=case_root,
        case_contract=case_contract,
    )
    if (
        assignment != expected_assignment
        or record["case_id"] != packet["case_id"]
        or case_contract.get("case_id") != packet["case_id"]
        or validation["case_contract_digest"] != record["case_contract_digest"]
        or validation["case_contract_digest"] != case_contract.get("contract_digest")
    ):
        raise SelectedResultVerifierQualificationError(
            "Qualification validation does not replay from its assignment and contract."
        )
    _digest(record["runner_freeze_digest"], "runner_freeze_digest")
    _digest(
        record["qualification_target_output_digest"],
        "qualification_target_output_digest",
    )
    return record


def _exact_span_locator(case_tree: RootedTreeRead, value: Any, *, role: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SelectedResultVerifierQualificationError("Oracle byte span is malformed.")
    path = _text(value.get("path"), "oracle span path")
    start = _integer(value.get("start"), "oracle span start")
    end = _integer(value.get("end"), "oracle span end")
    payload = case_tree.read_bytes(path)
    if start < 0 or end <= start or end > len(payload):
        raise SelectedResultVerifierQualificationError("Oracle byte span exceeds its file.")
    supplied_digest = _text(value.get("sha256"), "oracle span sha256")
    normalized_span_digest = (
        supplied_digest if supplied_digest.startswith("sha256:") else f"sha256:{supplied_digest}"
    )
    if normalized_span_digest != sha256_digest(payload[start:end]):
        raise SelectedResultVerifierQualificationError("Oracle byte-span digest has drifted.")
    lines = payload.splitlines(keepends=True)
    if not lines:
        raise SelectedResultVerifierQualificationError("Oracle byte span targets an empty file.")
    line_bounds: list[tuple[int, int]] = []
    cursor = 0
    for line in lines:
        next_cursor = cursor + len(line)
        line_bounds.append((cursor, next_cursor))
        cursor = next_cursor
    try:
        start_index = next(index for index, bounds in enumerate(line_bounds) if bounds[0] == start)
        end_index = next(index for index, bounds in enumerate(line_bounds) if bounds[1] == end)
    except StopIteration as error:
        raise SelectedResultVerifierQualificationError(
            "Oracle evidence spans must cover complete retained lines."
        ) from error
    if end_index < start_index:
        raise SelectedResultVerifierQualificationError(
            "Oracle evidence span has reversed line boundaries."
        )
    if role in {"report", "operand"} and (start != 0 or end != len(payload)):
        raise SelectedResultVerifierQualificationError(
            f"Oracle {role} span must cover the complete retained file."
        )
    return {
        "path": path,
        "content_digest": sha256_digest(payload),
        "start_line": start_index + 1,
        "end_line": end_index + 1,
        "span_digest": normalized_span_digest,
    }


def _locator_projection(value: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value[key] for key in ("path", "content_digest", "start_line", "end_line")}


def _target_receipt_matches(target: Mapping[str, Any], expected: Mapping[str, Any]) -> bool:
    locator = _locator_projection(expected)
    locator_digest = semantic_digest(locator)
    receipts = target.get("locator_receipts")
    if not isinstance(receipts, list):
        return False
    matching = [
        item
        for item in receipts
        if isinstance(item, dict) and item.get("locator_digest") == locator_digest
    ]
    return len(matching) == 1 and matching[0].get("span_digest") == expected.get("span_digest")


def _expected_target_reasons(expected_state: str, value: Any) -> tuple[str, ...]:
    if expected_state == "V":
        return ("one_selected_result_binding_rederived",)
    return tuple(_text(item, "oracle reason_code") for item in _sequence(value, "reason_codes"))


def _expected_validation_outcome(
    expected_state: str, target_reasons: tuple[str, ...]
) -> tuple[str, tuple[str, ...]]:
    if expected_state == "V":
        return "verified_complete", ("exact_independent_binding_match",)
    statuses = {
        "A": "ambiguous_selected_result",
        "I": "insufficient_evidence",
        "U": "unsupported_structure",
    }
    try:
        return statuses[expected_state], target_reasons
    except KeyError as error:
        raise SelectedResultVerifierQualificationError(
            "Oracle state has no validation-wrapper mapping."
        ) from error


def _target_state(value: Any) -> str:
    mapping = {
        "one_selected_result_rederived": "V",
        "ambiguous_selected_result": "A",
        "insufficient_evidence": "I",
        "unsupported_structure": "U",
    }
    status = _text(value, "target derivation_status")
    try:
        return mapping[status]
    except KeyError as error:
        raise SelectedResultVerifierQualificationError(
            "Target derivation has an unknown closed status."
        ) from error


def _target_packet(value: Mapping[str, Any]) -> dict[str, str]:
    packet = dict(value)
    _exact_keys(packet, {"case_id", "profile_id", "selected_report_path"}, "target packet")
    result = {key: _text(packet[key], key) for key in packet}
    if result["profile_id"] != PYTHON_STATIC_MARKED_REPORT_PROFILE:
        raise SelectedResultVerifierQualificationError("Target packet profile has drifted.")
    return result


def _semantic_conclusion(value: Mapping[str, Any]) -> dict[str, Any]:
    conclusion = dict(value)
    _exact_keys(
        conclusion,
        {"expected_state", "reason_codes", "positive_binding_digest"},
        "semantic conclusion",
    )
    state = _text(conclusion["expected_state"], "semantic expected_state")
    if state not in _REASON_CODES_BY_STATE:
        raise SelectedResultVerifierQualificationError(
            "Semantic conclusion state must be V, A, I, or U."
        )
    reasons = [
        _text(item, "semantic reason_code")
        for item in _sequence(conclusion["reason_codes"], "semantic reason_codes")
    ]
    if state == "V":
        if reasons or conclusion["positive_binding_digest"] is None:
            raise SelectedResultVerifierQualificationError(
                "V requires one exact positive-binding digest and no reason code."
            )
        binding_digest: str | None = _digest(
            conclusion["positive_binding_digest"], "positive_binding_digest"
        )
    else:
        if (
            len(reasons) != 1
            or reasons[0] not in _REASON_CODES_BY_STATE[state]
            or conclusion["positive_binding_digest"] is not None
        ):
            raise SelectedResultVerifierQualificationError(
                "Non-V semantic conclusions require one registered reason and no binding."
            )
        binding_digest = None
    return {
        "expected_state": state,
        "reason_codes": reasons,
        "positive_binding_digest": binding_digest,
    }


def _independence_declaration(value: Mapping[str, Any]) -> dict[str, bool]:
    declaration = dict(value)
    required = {
        "case_bytes_inspected",
        "reason_taxonomy_inspected",
        "target_source_seen",
        "target_tests_seen",
        "target_output_seen",
        "other_attestation_seen",
    }
    _exact_keys(declaration, required, "semantic-review independence declaration")
    if not all(isinstance(item, bool) for item in declaration.values()):
        raise SelectedResultVerifierQualificationError(
            "Semantic-review independence declarations must be Boolean."
        )
    expected = {
        "case_bytes_inspected": True,
        "reason_taxonomy_inspected": True,
        "target_source_seen": False,
        "target_tests_seen": False,
        "target_output_seen": False,
        "other_attestation_seen": False,
    }
    if declaration != expected:
        raise SelectedResultVerifierQualificationError(
            "Semantic review was not blind and independent."
        )
    return cast(dict[str, bool], declaration)


def _revalidate_semantic_attestation(
    value: Mapping[str, Any],
    *,
    case_root: Path,
    certificate: ConstructionCertificate,
    packet: Mapping[str, str],
    assignment: Mapping[str, Any],
    runner_freeze_digest: str,
    author_identity: Mapping[str, str],
) -> dict[str, Any]:
    attestation = _self_digested(value, "semantic_attestation_digest")
    _exact_keys(
        attestation,
        {
            "artifact_kind",
            "attestation_version",
            "case_id",
            "target_packet",
            "assignment_binding",
            "runner_freeze_digest",
            "certificate_digest",
            "case_inventory_digest",
            "semantic_conclusion",
            "agrees_with_construction_certificate",
            "author_identity",
            "validator_identity",
            "independence_declaration",
            "review_evidence_digest",
            "completed_at",
            "target_output_available",
            "qualification_authority",
            "semantic_attestation_digest",
        },
        "semantic attestation",
    )
    if (
        attestation["artifact_kind"] != "selected_result_verifier_semantic_attestation"
        or attestation["attestation_version"] != "1.0.0-development"
        or attestation["qualification_authority"] != "none_semantic_attestation_only"
        or attestation["target_output_available"] is not False
        or attestation["case_id"] != certificate.case_id
        or attestation["target_packet"] != dict(packet)
        or attestation["assignment_binding"] != dict(assignment)
        or attestation["runner_freeze_digest"] != runner_freeze_digest
        or attestation["certificate_digest"] != certificate.certificate_digest
        or attestation["author_identity"] != dict(author_identity)
    ):
        raise SelectedResultVerifierQualificationError(
            "Semantic attestation identity or study binding has drifted."
        )
    result = verify_construction_certificate(certificate, case_root)
    if attestation["case_inventory_digest"] != result.inventory_digest:
        raise SelectedResultVerifierQualificationError(
            "Semantic attestation case inventory has drifted."
        )
    conclusion = _semantic_conclusion(
        _mapping(attestation["semantic_conclusion"], "semantic_conclusion")
    )
    validator = _identity(
        _mapping(attestation["validator_identity"], "validator_identity"),
        "semantic validator",
    )
    if (
        validator["actor_id"] == author_identity["actor_id"]
        or validator["execution_context_id"] == author_identity["execution_context_id"]
        or validator["provider"] == author_identity["provider"]
    ):
        raise SelectedResultVerifierQualificationError(
            "Semantic validator is not cross-provider independent of the case author."
        )
    _independence_declaration(
        _mapping(attestation["independence_declaration"], "independence_declaration")
    )
    _digest(attestation["review_evidence_digest"], "review_evidence_digest")
    _timestamp(_text(attestation["completed_at"], "semantic attestation completed_at"))
    expected_binding_digest = (
        semantic_digest(asdict(result.positive_binding))
        if result.positive_binding is not None
        else None
    )
    expected_conclusion = {
        "expected_state": result.expected_state,
        "reason_codes": list(result.reason_codes),
        "positive_binding_digest": expected_binding_digest,
    }
    agreement = conclusion == expected_conclusion
    if attestation["agrees_with_construction_certificate"] is not agreement:
        raise SelectedResultVerifierQualificationError(
            "Semantic attestation agreement flag does not replay."
        )
    return attestation


def _validated_attestation_panel(
    values: Sequence[Mapping[str, Any]],
    *,
    case_root: Path,
    certificate: ConstructionCertificate,
    packet: Mapping[str, str],
    assignment: Mapping[str, Any],
    runner_freeze_digest: str,
    author_identity: Mapping[str, str],
) -> list[dict[str, Any]]:
    if len(values) != 2:
        raise SelectedResultVerifierQualificationError(
            "Exactly two independent semantic attestations are required."
        )
    attestations = [
        _revalidate_semantic_attestation(
            item,
            case_root=case_root,
            certificate=certificate,
            packet=packet,
            assignment=assignment,
            runner_freeze_digest=runner_freeze_digest,
            author_identity=author_identity,
        )
        for item in values
    ]
    attestations.sort(key=lambda item: str(item["semantic_attestation_digest"]))
    identities = [
        _mapping(item["validator_identity"], "validator_identity") for item in attestations
    ]
    if (
        len({str(item["actor_id"]) for item in identities}) != 2
        or len({str(item["execution_context_id"]) for item in identities}) != 2
        or len({str(item["review_evidence_digest"]) for item in attestations}) != 2
        or not all(item["agrees_with_construction_certificate"] is True for item in attestations)
        or attestations[0]["semantic_conclusion"] != attestations[1]["semantic_conclusion"]
    ):
        raise SelectedResultVerifierQualificationError(
            "Semantic attestation panel is not independent and unanimous."
        )
    return attestations


def _semantic_review_contract(value: Mapping[str, Any]) -> dict[str, Any]:
    contract = _self_digested(value, "contract_digest")
    if (
        contract.get("artifact_kind") != "selected_result_verifier_semantic_review_contract"
        or contract.get("contract_version") != "1.1.0"
        or contract.get("contract_digest") != FROZEN_SEMANTIC_REVIEW_CONTRACT_DIGEST
        or contract.get("qualification_authority") != "none_semantic_review_contract_only"
    ):
        raise SelectedResultVerifierQualificationError("Unsupported semantic review contract.")
    taxonomy = contract.get("reason_codes_by_state")
    expected = {state: sorted(reasons) for state, reasons in _REASON_CODES_BY_STATE.items()}
    if (
        not isinstance(taxonomy, Mapping)
        or {
            state: sorted(_sequence(taxonomy.get(state), f"{state} reason taxonomy"))
            for state in ("V", "A", "I", "U")
        }
        != expected
    ):
        raise SelectedResultVerifierQualificationError(
            "Semantic review contract reason taxonomy has drifted."
        )
    return contract


def _qualification_identity_registry(value: Mapping[str, Any]) -> dict[str, Any]:
    try:
        return validate_identity_registry(value)
    except ValueError as error:
        raise SelectedResultVerifierQualificationError(
            "Qualification identity registry does not replay."
        ) from error


def _immutable_case_inventory(case_root: Path) -> list[dict[str, Any]]:
    try:
        with RootedReader(case_root) as reader:
            case_tree = reader.read_case_tree()
    except QualificationIOError as error:
        raise SelectedResultVerifierQualificationError(
            "Case-author evidence requires one immutable descriptor-rooted case inventory."
        ) from error
    return [
        {
            "path": item.relative_path,
            "size": item.byte_length,
            "sha256": item.content_digest,
            "mode": item.mode,
        }
        for item in case_tree.files
    ]


def _require_certificate_inventory(
    certificate: ConstructionCertificate, case_inventory: Sequence[Mapping[str, Any]]
) -> None:
    certified = [
        {
            "path": item.path,
            "size": item.size,
            "sha256": f"sha256:{item.sha256}",
        }
        for item in certificate.files
    ]
    observed = [
        {
            "path": item.get("path"),
            "size": item.get("size"),
            "sha256": item.get("sha256"),
        }
        for item in case_inventory
    ]
    if certified != observed:
        raise SelectedResultVerifierQualificationError(
            "Construction certificate does not bind the immutable case-author inventory."
        )


def _validated_case_author_evidence(
    value: Mapping[str, Any],
    *,
    registry: Mapping[str, Any],
    author_identity: Mapping[str, str],
    certificate: ConstructionCertificate,
    packet: Mapping[str, Any],
    assignment: Mapping[str, Any],
    runner_freeze_digest: str,
    semantic_contract: Mapping[str, Any],
    case_inventory: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    try:
        return validate_case_author_session_identity_evidence(
            value,
            registry=registry,
            identity=author_identity,
            case_id=certificate.case_id,
            target_packet=packet,
            assignment_binding=assignment,
            runner_freeze_digest=runner_freeze_digest,
            semantic_contract_digest=str(semantic_contract["contract_digest"]),
            case_inventory=case_inventory,
            construction_certificate=asdict(certificate),
        )
    except ValueError as error:
        raise SelectedResultVerifierQualificationError(
            f"Case-author identity and retained session evidence do not replay: {error}"
        ) from error


def _validated_reconciliation_panel(
    values: Sequence[Mapping[str, Any]],
    *,
    case_root: Path,
    certificate: ConstructionCertificate,
    packet: Mapping[str, str],
    assignment: Mapping[str, Any],
    runner_freeze_digest: str,
    author_identity: Mapping[str, str],
    author_completed_at: datetime,
    semantic_contract: Mapping[str, Any],
    identity_registry: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if len(values) != 2:
        raise SelectedResultVerifierQualificationError(
            "Exactly two independent semantic reconciliations are required."
        )
    reconciliations = [
        revalidate_semantic_reconciliation(
            item,
            case_root=case_root,
            certificate=certificate,
            target_packet=packet,
            assignment_binding=assignment,
            runner_freeze_digest=runner_freeze_digest,
            semantic_contract=semantic_contract,
            identity_registry=identity_registry,
            author_identity=author_identity,
        )
        for item in values
    ]
    reconciliations.sort(key=lambda item: str(item["semantic_reconciliation_digest"]))
    blind_reviews = [_mapping(item["blind_review"], "blind_review") for item in reconciliations]
    identities = [
        _mapping(item["validator_identity"], "validator_identity") for item in blind_reviews
    ]
    evidence = [
        _mapping(item["validator_identity_evidence"], "validator_identity_evidence")
        for item in blind_reviews
    ]
    launches = [_mapping(item["launch_receipt"], "launch_receipt") for item in evidence]
    completions = [_mapping(item["completion_receipt"], "completion_receipt") for item in evidence]
    if any(
        _timestamp(_text(item.get("issued_at"), "reviewer launch issued_at")) <= author_completed_at
        for item in launches
    ):
        raise SelectedResultVerifierQualificationError(
            "Case-author completion must predate every independent reviewer launch."
        )
    if (
        len({str(item["actor_id"]) for item in identities}) != 2
        or len({str(item["execution_context_id"]) for item in identities}) != 2
        or len({str(item["provider"]) for item in identities}) != 2
        or len({str(item["session_nonce"]) for item in launches}) != 2
        or len({str(item["provider_request_id"]) for item in completions}) != 2
        or len({str(item["provider_response_digest"]) for item in completions}) != 2
        or len({str(item["raw_transcript_digest"]) for item in completions}) != 2
        or not all(item["agrees_with_construction_certificate"] is True for item in reconciliations)
        or blind_reviews[0]["semantic_conclusion"] != blind_reviews[1]["semantic_conclusion"]
    ):
        raise SelectedResultVerifierQualificationError(
            "Semantic reconciliation panel is not independent, evidenced, and unanimous."
        )
    return reconciliations


def _provider_completion_time(value: Mapping[str, Any], label: str) -> datetime:
    completion = _mapping(value.get("completion_receipt"), f"{label} completion receipt")
    return _timestamp(_text(completion.get("issued_at"), f"{label} completion issued_at"))


def _validated_certificate_reveal(
    value: Mapping[str, Any] | None,
    *,
    reconciliations: Sequence[Mapping[str, Any]],
    registry: Mapping[str, Any],
    certificate: ConstructionCertificate,
    assignment: Mapping[str, Any],
    runner_freeze_digest: str,
    author_completed_at: datetime,
) -> dict[str, Any]:
    if value is None:
        raise SelectedResultVerifierQualificationError(
            "Registrar-signed certificate reveal evidence is required."
        )
    blind_reviews = [_mapping(item["blind_review"], "blind_review") for item in reconciliations]
    completion_receipts = [
        _mapping(
            _mapping(review["validator_identity_evidence"], "validator_identity_evidence")[
                "completion_receipt"
            ],
            "completion_receipt",
        )
        for review in blind_reviews
    ]
    try:
        evidence = validate_certificate_reveal_evidence(
            value,
            registry=registry,
            case_id=certificate.case_id,
            assignment_digest=str(assignment["assignment_digest"]),
            runner_freeze_digest=runner_freeze_digest,
            certificate_digest=certificate.certificate_digest,
            blind_review_digests=[str(review["blind_review_digest"]) for review in blind_reviews],
            completion_receipts=completion_receipts,
        )
    except ValueError as error:
        raise SelectedResultVerifierQualificationError(
            "Certificate reveal evidence does not replay."
        ) from error
    event = _mapping(evidence["reveal_event"], "certificate reveal event")
    reveal_at = _timestamp(_text(event.get("issued_at"), "certificate reveal event issued_at"))
    if author_completed_at >= reveal_at:
        raise SelectedResultVerifierQualificationError(
            "Case-author completion must predate certificate reveal."
        )
    if any(
        item.get("certificate_revealed_at") != event.get("issued_at") for item in reconciliations
    ):
        raise SelectedResultVerifierQualificationError(
            "Reconciliation reveal timestamps do not equal the signed reveal event."
        )
    return evidence


def _assignment_binding(
    manifest: Mapping[str, Any] | None,
    *,
    packet: Mapping[str, str],
    block: str,
    provider_slot: str,
) -> dict[str, Any]:
    if manifest is None:
        raise SelectedResultVerifierQualificationError(
            "A frozen assignment manifest is required for qualification execution."
        )
    assignments = _self_digested(manifest, "assignment_digest")
    if (
        assignments["assignment_digest"] != FROZEN_ASSIGNMENT_DIGEST
        or assignments.get("artifact_kind") != "selected_result_verifier_opaque_assignments"
        or assignments.get("case_replacement_permitted") is not False
        or assignments.get("case_bytes_present") is not False
        or assignments.get("target_outputs_present") is not False
        or assignments.get("case_count") != 96
    ):
        raise SelectedResultVerifierQualificationError(
            "Qualification assignment manifest is not the frozen study assignment."
        )
    blocks = assignments.get("blocks")
    if not isinstance(blocks, list):
        raise SelectedResultVerifierQualificationError("Assignment blocks are absent.")
    matches: list[dict[str, Any]] = []
    for block_record in blocks:
        if not isinstance(block_record, dict) or block_record.get("block") != block:
            continue
        records = block_record.get("assignments")
        if not isinstance(records, list):
            continue
        for raw in records:
            if (
                isinstance(raw, dict)
                and raw.get("provider_slot") == provider_slot
                and raw.get("target_packet") == dict(packet)
            ):
                matches.append(raw)
    if len(matches) != 1:
        raise SelectedResultVerifierQualificationError(
            "Target packet is not uniquely present in the frozen assignment."
        )
    selected = matches[0]
    if (
        selected.get("case_id") != packet["case_id"]
        or selected.get("case_replacement_permitted") is not False
        or not isinstance(selected.get("assignment_position"), int)
        or isinstance(selected.get("assignment_position"), bool)
    ):
        raise SelectedResultVerifierQualificationError(
            "Frozen qualification assignment entry is malformed."
        )
    return {
        "assignment_digest": assignments["assignment_digest"],
        "block": block,
        "provider_slot": provider_slot,
        "assignment_position": selected["assignment_position"],
        "case_id": packet["case_id"],
        "target_packet": dict(packet),
    }


def _validate_assignment_binding(
    value: Mapping[str, Any], *, packet: Mapping[str, str]
) -> dict[str, Any]:
    binding = dict(value)
    _exact_keys(
        binding,
        {
            "assignment_digest",
            "block",
            "provider_slot",
            "assignment_position",
            "case_id",
            "target_packet",
        },
        "assignment binding",
    )
    if (
        binding["assignment_digest"] != FROZEN_ASSIGNMENT_DIGEST
        or binding["case_id"] != packet["case_id"]
        or binding["target_packet"] != dict(packet)
        or binding["block"] not in {"pilot", "held_out"}
        or binding["provider_slot"] not in {"provider-family-1", "provider-family-2"}
        or not isinstance(binding["assignment_position"], int)
        or isinstance(binding["assignment_position"], bool)
        or not 1 <= binding["assignment_position"] <= 48
    ):
        raise SelectedResultVerifierQualificationError(
            "Qualification assignment binding has drifted."
        )
    return binding


def _target_validator_identity(value: Mapping[str, Any]) -> dict[str, str]:
    identity = _identity(value, "target validator")
    return {
        "validator_id": identity["actor_id"],
        "provider": identity["provider"],
        "execution_context_id": identity["execution_context_id"],
        "identity_evidence_digest": identity["identity_evidence_digest"],
    }


def _require_phase_identity_separation(
    *,
    proof: Mapping[str, Any],
    target: Mapping[str, Any],
    validation_record: Mapping[str, Any],
    comparison_identity: Mapping[str, str],
) -> None:
    author = _identity(_mapping(proof["author_identity"], "author_identity"), "case author")
    oracle = _identity(_mapping(proof["oracle_identity"], "oracle_identity"), "oracle runner")
    reviews = [
        _mapping(item, "semantic reconciliation")
        for item in _sequence(proof["semantic_reconciliations"], "semantic_reconciliations")
    ]
    reviewers = [
        _identity(
            _mapping(
                _mapping(item["blind_review"], "blind_review")["validator_identity"],
                "validator_identity",
            ),
            "semantic validator",
        )
        for item in reviews
    ]
    target_raw = _mapping(target["validator_identity"], "target validator identity")
    target_identity = {
        "actor_id": _text(target_raw["validator_id"], "target validator_id"),
        "provider": _text(target_raw["provider"], "target provider"),
        "execution_context_id": _text(
            target_raw["execution_context_id"], "target execution_context_id"
        ),
        "identity_evidence_digest": _digest(
            target_raw["identity_evidence_digest"], "target identity_evidence_digest"
        ),
    }
    validation_identity = _identity(
        _mapping(validation_record["validation_identity"], "validation_identity"),
        "validation runner",
    )
    identities = [
        author,
        *reviewers,
        oracle,
        target_identity,
        validation_identity,
        dict(comparison_identity),
    ]
    if (
        len({item["actor_id"] for item in identities}) != len(identities)
        or len({item["execution_context_id"] for item in identities}) != len(identities)
        or len({item["identity_evidence_digest"] for item in identities}) != len(identities)
    ):
        raise SelectedResultVerifierQualificationError(
            "Qualification roles reuse an actor, execution context, or identity receipt."
        )


def _identity(value: Mapping[str, Any], label: str) -> dict[str, str]:
    identity = dict(value)
    _exact_keys(
        identity,
        {"actor_id", "provider", "execution_context_id", "identity_evidence_digest"},
        f"{label} identity",
    )
    return {key: _text(identity[key], f"{label} {key}") for key in identity}


def _module_lock(path: Path) -> dict[str, str]:
    return {
        "path": path.name,
        "content_digest": sha256_digest(path.read_bytes()),
    }


def _self_digested(value: Mapping[str, Any], digest_field: str) -> dict[str, Any]:
    result = dict(value)
    supplied = result.pop(digest_field, None)
    if supplied != semantic_digest(result):
        raise SelectedResultVerifierQualificationError(f"{digest_field} does not replay.")
    result[digest_field] = supplied
    return result


def _object_sequence(value: Any, label: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in _sequence(value, label):
        if not isinstance(item, Mapping):
            raise SelectedResultVerifierQualificationError(f"{label} entries must be objects.")
        result.append(dict(item))
    return result


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SelectedResultVerifierQualificationError(f"{label} must be an object.")
    return value


def _sequence(value: Any, label: str) -> Sequence[Any]:
    if not isinstance(value, (list, tuple)):
        raise SelectedResultVerifierQualificationError(f"{label} must be a list.")
    return value


def _exact_keys(value: Mapping[str, Any], keys: set[str], label: str) -> None:
    if set(value) != keys:
        raise SelectedResultVerifierQualificationError(f"{label} has an unsupported shape.")


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or "\n" in value or "\r" in value:
        raise SelectedResultVerifierQualificationError(
            f"{label} must be non-empty single-line text."
        )
    return value


def _integer(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise SelectedResultVerifierQualificationError(f"{label} must be an integer.")
    return value


def _digest(value: Any, label: str) -> str:
    digest = _text(value, label)
    if not digest.startswith("sha256:") or len(digest) != 71:
        raise SelectedResultVerifierQualificationError(f"{label} must be a SHA-256 digest.")
    try:
        int(digest.removeprefix("sha256:"), 16)
    except ValueError as error:
        raise SelectedResultVerifierQualificationError(
            f"{label} must be a SHA-256 digest."
        ) from error
    return digest


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise SelectedResultVerifierQualificationError(
            "Invalid qualification timestamp."
        ) from error
    if parsed.tzinfo is None:
        raise SelectedResultVerifierQualificationError(
            "Qualification timestamps require timezones."
        )
    return parsed.astimezone(UTC)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
