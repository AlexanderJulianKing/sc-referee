from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee_evaluation.prospective_selected_result_verifier import (
    PYTHON_STATIC_MARKED_REPORT_PROFILE,
    freeze_independent_selected_result_derivation,
    revalidate_independent_selected_result_derivation,
)
from sc_referee_evaluation.selected_result_qualification_oracle import (
    ConstructionCertificate,
    FileCertificate,
    OracleState,
    PositiveBindingCertificate,
    SpanCertificate,
    verify_construction_certificate,
)

QUALIFICATION_CONTROLLER_VERSION = "1.0.0"


class SelectedResultVerifierQualificationError(ValueError):
    """Raised when a verifier-qualification artifact cannot replay exactly."""


def load_construction_certificate(path: Path) -> ConstructionCertificate:
    """Load the closed JSON representation authored outside the verifier package."""

    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SelectedResultVerifierQualificationError(
            "Construction certificate must be one JSON object."
        )
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


def freeze_oracle_proof(
    *,
    case_root: Path,
    certificate: ConstructionCertificate,
    target_packet: Mapping[str, Any],
    oracle_identity: Mapping[str, Any],
    completed_at: str,
) -> dict[str, Any]:
    """Freeze a certificate-backed oracle proof before target output is available."""

    packet = _target_packet(target_packet)
    if packet["case_id"] != certificate.case_id:
        raise SelectedResultVerifierQualificationError(
            "Target packet and certificate case identities differ."
        )
    result = verify_construction_certificate(certificate, case_root)
    identity = _identity(oracle_identity, "oracle")
    record: dict[str, Any] = {
        "artifact_kind": "selected_result_verifier_oracle_proof",
        "qualification_controller_version": QUALIFICATION_CONTROLLER_VERSION,
        "case_id": result.case_id,
        "target_packet": packet,
        "oracle_identity": identity,
        "construction_certificate": asdict(certificate),
        "oracle_result": asdict(result),
        "oracle_implementation": _module_lock(
            Path(__file__).with_name("selected_result_qualification_oracle.py")
        ),
        "completed_at": _iso(_timestamp(completed_at)),
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
) -> dict[str, Any]:
    """Run and freeze the target without accepting any oracle or certificate input."""

    packet = _target_packet(target_packet)
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
    return revalidate_independent_selected_result_derivation(derivation, case_root)


def freeze_verifier_comparison(
    *,
    case_root: Path,
    oracle_proof: Mapping[str, Any],
    target_derivation: Mapping[str, Any],
    compared_at: str,
) -> dict[str, Any]:
    """Compare only after both independently frozen inputs exist."""

    proof = _revalidate_oracle_proof(oracle_proof, case_root)
    target = revalidate_independent_selected_result_derivation(target_derivation, case_root)
    if proof.get("target_output_available") is not False:
        raise SelectedResultVerifierQualificationError(
            "Oracle proof was not frozen before target-output reveal."
        )
    if proof.get("case_id") != target.get("case_id"):
        raise SelectedResultVerifierQualificationError(
            "Oracle proof and target derivation case identities differ."
        )
    oracle_completed = _timestamp(str(proof.get("completed_at", "")))
    target_derived = _timestamp(str(target.get("derived_at", "")))
    target_frozen = _timestamp(str(target.get("frozen_at", "")))
    comparison_time = _timestamp(str(compared_at))
    if target_derived < oracle_completed:
        raise SelectedResultVerifierQualificationError(
            "Target derivation predates the frozen oracle proof."
        )
    if comparison_time < target_frozen:
        raise SelectedResultVerifierQualificationError(
            "Comparison predates the frozen target output."
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
    elif expected_state == "V" and observed_state != "V":
        outcome = "false_incomplete"
    elif expected_state == "V" and not binding_matches:
        outcome = "binding_mismatch"
    elif not state_matches or not reasons_match:
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
        "expected_state": expected_state,
        "observed_state": observed_state,
        "expected_reason_codes": list(expected_reasons),
        "observed_reason_codes": list(observed_reasons),
        "state_matches": state_matches,
        "reason_codes_match": reasons_match,
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
        expected_report = _span_locator(case_root, raw_binding["report"])
        expected_result = _span_locator(case_root, raw_binding["result"])
        expected_producer = _span_locator(case_root, raw_binding["producer"])
        raw_operands = raw_binding["operands"]
        if not isinstance(raw_operands, (list, tuple)):
            return False
        expected_operands = sorted(
            (_span_locator(case_root, item) for item in raw_operands),
            key=lambda item: (str(item["path"]), int(item["start_line"])),
        )
        actual_operands = candidate.get("source_operands")
        if not isinstance(actual_operands, list):
            return False
        actual_operand_locators = sorted(
            (item["source_locator"] for item in actual_operands if isinstance(item, dict)),
            key=lambda item: (str(item["path"]), int(item["start_line"])),
        )
    except (KeyError, TypeError, ValueError, OSError):
        return False
    return (
        candidate.get("report_locator") == expected_report
        and candidate.get("result_locator") == expected_result
        and candidate.get("producer_locator") == expected_producer
        and actual_operand_locators == expected_operands
        and candidate.get("alternative_producer_locators") == []
    )


def _revalidate_oracle_proof(value: Mapping[str, Any], case_root: Path) -> dict[str, Any]:
    proof = _self_digested(value, "oracle_proof_digest")
    required = {
        "artifact_kind",
        "qualification_controller_version",
        "case_id",
        "target_packet",
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
    _identity(_mapping(proof["oracle_identity"], "oracle_identity"), "oracle")
    certificate = _construction_certificate(
        _mapping(proof["construction_certificate"], "construction_certificate")
    )
    result = verify_construction_certificate(certificate, case_root)
    if (
        proof["case_id"] != certificate.case_id
        or packet["case_id"] != certificate.case_id
        or proof["oracle_result"] != asdict(result)
    ):
        raise SelectedResultVerifierQualificationError(
            "Oracle proof does not replay from its certificate and case bytes."
        )
    _timestamp(_text(proof["completed_at"], "completed_at"))
    return proof


def _span_locator(case_root: Path, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SelectedResultVerifierQualificationError("Oracle byte span is malformed.")
    path = _text(value.get("path"), "oracle span path")
    start = _integer(value.get("start"), "oracle span start")
    end = _integer(value.get("end"), "oracle span end")
    payload = (case_root / path).read_bytes()
    if start < 0 or end <= start or end > len(payload):
        raise SelectedResultVerifierQualificationError("Oracle byte span exceeds its file.")
    start_line = payload.count(b"\n", 0, start) + 1
    end_line = payload.count(b"\n", 0, end - 1) + 1
    return {
        "path": path,
        "content_digest": sha256_digest(payload),
        "start_line": start_line,
        "end_line": end_line,
    }


def _expected_target_reasons(expected_state: str, value: Any) -> tuple[str, ...]:
    if expected_state == "V":
        return ("one_selected_result_binding_rederived",)
    return tuple(_text(item, "oracle reason_code") for item in _sequence(value, "reason_codes"))


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


def _target_validator_identity(value: Mapping[str, Any]) -> dict[str, str]:
    identity = _identity(value, "target validator")
    return {
        "validator_id": identity["actor_id"],
        "provider": identity["provider"],
        "execution_context_id": identity["execution_context_id"],
        "identity_evidence_digest": identity["identity_evidence_digest"],
    }


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
