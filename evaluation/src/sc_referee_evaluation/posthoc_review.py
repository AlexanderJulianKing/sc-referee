from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest, stable_id
from sc_referee.posthoc_method_ledger import (
    POSTHOC_METHOD_LEDGER_PROFILE,
    POSTHOC_METHOD_LEDGER_VERSION,
    posthoc_form_allowed,
    project_posthoc_method_ledger,
    validate_posthoc_requirement,
)
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee_evaluation.source_method_probe import PROFILE_MANIFEST

_REVIEW_VERSION = "0.2.0"
_DIGEST_PREFIX = "sha256:"
_STRUCTURED_KEYS = {
    "answer_kind",
    "approval_statement_digest",
    "comparison_form",
    "dimension",
    "normalized_value",
    "profile_id",
    "respondent",
}
_UNKNOWN_KEYS = {
    "answer_kind",
    "approval_statement_digest",
    "comparison_form",
    "dimension",
    "normalized_value",
    "profile_id",
    "respondent",
}


class PosthocValidationReviewError(ValueError):
    """An evaluation-only post-hoc validation review failed closed."""


def build_posthoc_validation_review(
    source_probe: Mapping[str, Any],
    review_spec: Mapping[str, Any],
    *,
    reviewed_at: str,
    output: Path,
) -> dict[str, Any]:
    """Bind one scoped scientist Answer to one fixed static-probe result.

    This compiler is deliberately evaluation-only. It never promotes a public answer-side
    reference or an audit-time Answer into production intent, execution evidence, qualification,
    or a Finding.
    """

    if output.exists() or output.is_symlink():
        raise PosthocValidationReviewError(f"review output already exists: {output}")
    _timestamp(reviewed_at)
    _validate_probe(source_probe)
    case_id = _required_string(review_spec.get("case_id"), "case_id")
    allowed_spec_keys = {"case_id", "scientist_answer", "repository_self_declaration"}
    if (
        not {"case_id", "scientist_answer"} <= set(review_spec)
        or not set(review_spec) <= allowed_spec_keys
    ):
        raise PosthocValidationReviewError("review specification has unsupported fields")
    raw_answer = review_spec.get("scientist_answer")
    if not isinstance(raw_answer, Mapping):
        raise PosthocValidationReviewError("scientist_answer must be one object")
    reference = source_probe["answer_side_reference"]
    if (
        not isinstance(reference, Mapping)
        or reference.get("reference_id") != f"genebench-public:{case_id}:report-public"
    ):
        raise PosthocValidationReviewError("review case scope does not match the source probe")
    answer = _validate_answer(raw_answer, case_id)
    self_declaration = _validate_self_declaration(
        review_spec.get("repository_self_declaration"), answer
    )

    identity_parts = [
        _REVIEW_VERSION,
        reviewed_at,
        case_id,
        str(source_probe["diagnostic_digest"]),
        semantic_digest(answer),
    ]
    if self_declaration is not None:
        identity_parts.append(semantic_digest(self_declaration))
    review_id = stable_id(
        "evaluation-posthoc-validation-review",
        *identity_parts,
    )
    record: dict[str, Any] = {
        "evaluation_protocol_version": "0.2.0",
        "posthoc_validation_review_version": _REVIEW_VERSION,
        "record_type": "evaluation_posthoc_validation_review",
        "review_id": review_id,
        "case_id": case_id,
        "reviewed_at": reviewed_at,
        "source_probe_ref": {
            "record_type": str(source_probe["record_type"]),
            "record_id": str(source_probe["probe_id"]),
            "diagnostic_digest": str(source_probe["diagnostic_digest"]),
        },
        "source_binding": deepcopy(source_probe["source"]),
        "answer_side_reference": deepcopy(source_probe["answer_side_reference"]),
        "scientist_answer": answer,
        "project_code_executed": False,
        "model_invoked": False,
        "production_intent_authority": False,
        "historical_intent_established": False,
        "execution_established": False,
        "numeric_causality_established": False,
        "metric_eligible": False,
        "held_out_eligible": False,
        "promotion_evidence_eligible": False,
        "production_finding_eligible": False,
    }
    if answer["answer_kind"] == "unknown":
        record.update(_unknown_projection(source_probe))
    else:
        record.update(_structured_projection(source_probe, case_id, answer))
    if self_declaration is not None:
        record["repository_self_declaration"] = self_declaration
        record["self_compliance_check"] = {
            "state": (
                "contradicted_by_static_source_shape"
                if record["review_outcome"] == "exact_conflict_candidate"
                else "compatible_with_static_source_shape"
            ),
            "declaration_establishes_execution": False,
            "declaration_overrides_static_source": False,
        }
    record["non_inferences"] = [
        "This evaluation-scoped Answer does not establish historical or universal scientific intent.",
        "Static source inspection does not establish that the inspected source executed.",
        "An exact conflict candidate is not a production Finding or proof of numeric causality.",
        "A covered compatibility result is not a scientific correctness certificate.",
    ]
    record["review_digest"] = semantic_digest(record)
    write_normalized_json_once(output, record)
    return record


def _validate_probe(source_probe: Mapping[str, Any]) -> None:
    expected_digest = source_probe.get("diagnostic_digest")
    if not _digest(expected_digest):
        raise PosthocValidationReviewError("source probe diagnostic digest is unavailable")
    unsigned = deepcopy(dict(source_probe))
    unsigned.pop("diagnostic_digest", None)
    if semantic_digest(unsigned) != expected_digest:
        raise PosthocValidationReviewError("source probe diagnostic digest does not verify")
    required = {
        "record_type": "evaluation_python_source_method_probe",
        "source_method_probe_version": "0.2.0",
        "production_finding_eligible": False,
        "promotion_evidence_eligible": False,
        "project_code_executed_by_probe": False,
        "model_invoked_by_probe": False,
    }
    if any(source_probe.get(key) != value for key, value in required.items()):
        raise PosthocValidationReviewError("source probe crosses the evaluation safety boundary")
    if not isinstance(source_probe.get("source"), Mapping):
        raise PosthocValidationReviewError("source probe has no exact source binding")
    reference = source_probe.get("answer_side_reference")
    if (
        not isinstance(reference, Mapping)
        or reference.get("production_intent_authority") is not False
    ):
        raise PosthocValidationReviewError("answer-side reference must remain non-authoritative")
    results = source_probe.get("results")
    if not isinstance(results, Sequence) or isinstance(results, (str, bytes)) or not results:
        raise PosthocValidationReviewError("source probe has no closed profile results")


def _validate_answer(raw: Mapping[str, Any], case_id: str) -> dict[str, Any]:
    kind = raw.get("answer_kind")
    expected_keys = _UNKNOWN_KEYS if kind == "unknown" else _STRUCTURED_KEYS
    if set(raw) != expected_keys:
        raise PosthocValidationReviewError("scientist Answer has unsupported or missing fields")
    approval_digest = raw.get("approval_statement_digest")
    if not _digest(approval_digest):
        raise PosthocValidationReviewError("scientist Answer requires an approval statement digest")
    respondent = raw.get("respondent")
    if (
        not isinstance(respondent, Mapping)
        or set(respondent) != {"actor_kind", "actor_id"}
        or respondent.get("actor_kind") != "human"
        or not isinstance(respondent.get("actor_id"), str)
        or not respondent.get("actor_id")
    ):
        raise PosthocValidationReviewError("scientist Answer requires one identified human")
    normalized = deepcopy(dict(raw))
    normalized["authority_scope"] = {
        "case_id": case_id,
        "review_only": True,
        "historical_intent": False,
    }
    if kind == "unknown":
        if any(
            raw.get(key) is not None
            for key in ("comparison_form", "dimension", "normalized_value", "profile_id")
        ):
            raise PosthocValidationReviewError(
                "unknown Answer must not invent a profile, dimension, form, or value"
            )
        normalized["answer_digest"] = semantic_digest(normalized)
        return normalized
    if kind != "structured":
        raise PosthocValidationReviewError("unsupported scientist Answer kind")
    profile_id = _required_string(raw.get("profile_id"), "profile_id")
    dimension = _required_string(raw.get("dimension"), "dimension")
    comparison_form = _required_string(raw.get("comparison_form"), "comparison_form")
    if profile_id not in PROFILE_MANIFEST:
        raise PosthocValidationReviewError("scientist Answer names an unsupported probe profile")
    if not posthoc_form_allowed(dimension, comparison_form):
        raise PosthocValidationReviewError("comparison form is not allowed for this dimension")
    value = validate_posthoc_requirement(dimension, comparison_form, raw.get("normalized_value"))
    if value != PROFILE_MANIFEST[profile_id]["expected_form"]:
        raise PosthocValidationReviewError(
            "scientist Answer does not equal the selected profile's closed expected form"
        )
    normalized["normalized_value"] = value
    normalized["authority_scope"]["scientific_contract_dimension"] = dimension
    normalized["answer_digest"] = semantic_digest(normalized)
    return normalized


def _structured_projection(
    source_probe: Mapping[str, Any], case_id: str, answer: Mapping[str, Any]
) -> dict[str, Any]:
    profile_id = str(answer["profile_id"])
    dimension = str(answer["dimension"])
    comparison_form = str(answer["comparison_form"])
    profile_result = _one_profile_result(source_probe, profile_id)
    observed = profile_result.get("observed_form")
    if profile_result.get("state") not in {"exact_static_conflict", "covered_negative"}:
        raise PosthocValidationReviewError(
            "structured validation requires one exact conflict or covered source shape"
        )
    if not isinstance(observed, str) or not observed:
        raise PosthocValidationReviewError("profile result has no canonical observed form")
    evidence = _evidence(profile_result)
    answer_source = {
        "source_kind": "evaluation_scientist_answer",
        "locator": str(answer["approval_statement_digest"]),
        "content_digest": str(answer["approval_statement_digest"]),
    }
    claim_id = stable_id("evaluation-claim", case_id, str(source_probe["diagnostic_digest"]))
    contract_id = stable_id("evaluation-contract", claim_id, dimension)
    requirement_id = stable_id(
        "evaluation-semantic-assertion",
        claim_id,
        f"verified_intended_{dimension}",
        str(answer["answer_digest"]),
    )
    observed_id = stable_id(
        "evaluation-semantic-assertion",
        claim_id,
        f"reported_{dimension}",
        semantic_digest(profile_result),
    )
    claim = {"claim_id": claim_id, "scientific_contract_id": contract_id}
    contract = {
        "contract_id": contract_id,
        "scope": {
            "level": "claim",
            "subject_refs": [{"record_type": "claim", "record_id": claim_id}],
        },
        "dimensions": {
            dimension: {
                "state": "known",
                "assertion_ids": [requirement_id],
                "accepted_assertion_ids": [requirement_id],
            }
        },
        "source_refs": [answer_source],
    }
    requirement = {
        "assertion_id": requirement_id,
        "subject_ref": {"record_type": "claim", "record_id": claim_id},
        "predicate": f"verified_intended_{dimension}",
        "object": deepcopy(answer["normalized_value"]),
        "semantic_role": "intended",
        "assertion_class": "deterministic_derivation",
        "epistemic_status": "accepted",
        "authority_scope": "scientific_intent",
        "independently_checkable": True,
        "finding_eligibility": "eligible",
        "verification": {"status": "verified", "method": "deterministic_comparison"},
        "source_refs": [answer_source],
        "provenance": {"actor": {"actor_kind": "controller"}},
        "extensions": {
            "x-answer-ref": {
                "record_type": "answer",
                "record_id": stable_id("evaluation-answer", case_id, str(answer["answer_digest"])),
            },
            "x-answer-digest": str(answer["answer_digest"]),
        },
    }
    reported = {
        "assertion_id": observed_id,
        "subject_ref": {"record_type": "claim", "record_id": claim_id},
        "predicate": f"reported_{dimension}",
        "object": observed,
        "semantic_role": "reported",
        "assertion_class": "explicit_text_extraction",
        "epistemic_status": "accepted",
        "authority_scope": "reported_wording",
        "independently_checkable": True,
        "finding_eligibility": "eligible",
        "verification": {"status": "verified", "method": "structural_parser"},
        "source_refs": evidence,
        "provenance": {"actor": {"actor_kind": "parser"}},
    }
    ledger = project_posthoc_method_ledger(
        claim=claim,
        contract=contract,
        assertions=[requirement, reported],
        dimension=dimension,
        comparison_form=comparison_form,
    )
    expected_outcome = {
        "exact_static_conflict": "exact_conflict_candidate",
        "covered_negative": "covered_negative",
    }[str(profile_result["state"])]
    if ledger.get("outcome") != expected_outcome:
        raise PosthocValidationReviewError("source probe and post-hoc ledger outcomes disagree")
    return {
        "profile_result": deepcopy(profile_result),
        "ledger_profile": POSTHOC_METHOD_LEDGER_PROFILE,
        "ledger_profile_version": POSTHOC_METHOD_LEDGER_VERSION,
        "ledger": ledger,
        "review_outcome": str(ledger["outcome"]),
        "coverage_status": (
            "covered" if ledger["outcome"] == "covered_negative" else "exact_conflict_candidate"
        ),
        "bounded_summary": (
            "The exact static source form is compatible with the scientist-specified requirement "
            "for this review."
            if ledger["outcome"] == "covered_negative"
            else "The exact static source form conflicts with the scientist-specified requirement "
            "for this review."
        ),
    }


def _validate_self_declaration(raw: object, answer: Mapping[str, Any]) -> dict[str, Any] | None:
    if raw is None:
        return None
    if answer.get("answer_kind") != "structured":
        raise PosthocValidationReviewError(
            "repository self-declaration cannot resolve an unknown scientist Answer"
        )
    if not isinstance(raw, Mapping) or set(raw) != {
        "dimension",
        "normalized_value",
        "source_ref",
    }:
        raise PosthocValidationReviewError("repository self-declaration has an unsupported shape")
    if raw.get("dimension") != answer.get("dimension") or raw.get("normalized_value") != answer.get(
        "normalized_value"
    ):
        raise PosthocValidationReviewError(
            "repository self-declaration must exactly claim the scoped required value"
        )
    source_ref = raw.get("source_ref")
    if (
        not isinstance(source_ref, Mapping)
        or source_ref.get("source_kind") != "file_span"
        or not isinstance(source_ref.get("path"), str)
        or not source_ref.get("path")
        or not isinstance(source_ref.get("locator"), str)
        or not source_ref.get("locator")
        or not _digest(source_ref.get("content_digest"))
    ):
        raise PosthocValidationReviewError(
            "repository self-declaration requires one exact file-span source"
        )
    return deepcopy(dict(raw))


def _unknown_projection(source_probe: Mapping[str, Any]) -> dict[str, Any]:
    results = source_probe.get("results")
    assert isinstance(results, Sequence)
    return {
        "profile_result": None,
        "ledger_profile": POSTHOC_METHOD_LEDGER_PROFILE,
        "ledger_profile_version": POSTHOC_METHOD_LEDGER_VERSION,
        "ledger": None,
        "review_outcome": "unresolved_obligation",
        "coverage_status": "unknown",
        "bounded_summary": (
            "The scientist retained the governing method as unknown; no profile, contract "
            "dimension, reported assertion, conflict, or Finding was manufactured."
        ),
        "unmapped_probe_results": deepcopy(list(results)),
    }


def _one_profile_result(source_probe: Mapping[str, Any], profile_id: str) -> dict[str, Any]:
    results = source_probe.get("results")
    assert isinstance(results, Sequence)
    selected = [
        item
        for item in results
        if isinstance(item, Mapping) and item.get("profile_id") == profile_id
    ]
    if len(selected) != 1:
        raise PosthocValidationReviewError("selected profile does not resolve to one probe result")
    result = deepcopy(dict(selected[0]))
    manifest = PROFILE_MANIFEST[profile_id]
    if (
        result.get("expected_form") != manifest["expected_form"]
        or result.get("issue_class") != manifest["issue_class"]
    ):
        raise PosthocValidationReviewError(
            "selected probe result does not match its closed manifest"
        )
    return result


def _evidence(profile_result: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw = profile_result.get("evidence")
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise PosthocValidationReviewError("profile evidence is malformed")
    values = [deepcopy(dict(item)) for item in raw if isinstance(item, Mapping)]
    if len(values) != len(raw) or not values:
        raise PosthocValidationReviewError("exact profile result requires source evidence")
    return values


def _required_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise PosthocValidationReviewError(f"{label} must be a non-empty string")
    return value


def _digest(value: object) -> bool:
    return (
        isinstance(value, str)
        and value.startswith(_DIGEST_PREFIX)
        and len(value) == len(_DIGEST_PREFIX) + 64
        and all(character in "0123456789abcdef" for character in value[len(_DIGEST_PREFIX) :])
    )


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise PosthocValidationReviewError(f"invalid timestamp: {value!r}") from error
    if parsed.tzinfo is None:
        raise PosthocValidationReviewError("timestamps must include a timezone")
    return parsed


__all__ = ["PosthocValidationReviewError", "build_posthoc_validation_review"]
