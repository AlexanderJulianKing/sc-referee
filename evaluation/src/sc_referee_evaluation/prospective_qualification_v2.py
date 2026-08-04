from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any, Literal

from sc_referee.core.ids import semantic_digest
from sc_referee_evaluation.prospective_selected_result_verifier import (
    ProspectiveSelectedResultVerifierError,
    validate_selected_result_validation,
)

CASE_EVIDENCE_CONTRACT_VERSION = "2.0.0"
SCIENTIFIC_LABEL_VERSION = "2.0.0"

ScientificLabel = Literal[
    "issue_present",
    "issue_absent",
    "conditional_or_unknown",
    "insufficient_evidence",
    "unsupported",
    "review_disagreement",
]

_REVIEW_LABELS = {"issue_present", "issue_absent"}


class ProspectiveQualificationV2Error(ValueError):
    """Raised when v2 prospective case or label evidence is not closed and replayable."""


def freeze_case_evidence_contract(spec: Mapping[str, Any], *, frozen_at: str) -> dict[str, Any]:
    """Freeze an unverified author declaration that makes the selected result auditable."""

    value = deepcopy(dict(spec))
    _exact_keys(
        value,
        {
            "case_id",
            "envelope",
            "canonical_issue_class",
            "selected_result_binding",
            "authorship",
            "authored_at",
        },
        "case evidence contract",
    )
    case_id = _case_id(value["case_id"])
    envelope = _envelope(value["envelope"])
    issue_class = _issue_class(value["canonical_issue_class"])
    binding = _selected_result_binding(value["selected_result_binding"])
    authorship = _authorship(value["authorship"])
    authored_at = _timestamp(_text(value["authored_at"], "authored_at"))
    frozen = _timestamp(frozen_at)
    if authored_at > frozen:
        raise ProspectiveQualificationV2Error("Case evidence cannot be frozen before authorship.")

    record: dict[str, Any] = {
        "artifact_kind": "prospective_case_evidence_contract",
        "contract_version": CASE_EVIDENCE_CONTRACT_VERSION,
        "case_id": case_id,
        "envelope": envelope,
        "canonical_issue_class": issue_class,
        "selected_result_binding": binding,
        "selected_result_binding_digest": semantic_digest(binding),
        "authorship": authorship,
        "authored_at": _iso(authored_at),
        "frozen_at": _iso(frozen),
        "evidence_status": "unverified_author_declaration",
        "qualification_authority": "none_case_contract_only",
    }
    record["contract_digest"] = semantic_digest(record)
    return record


def freeze_stage2_scientific_label(
    spec: Mapping[str, Any],
    *,
    case_root: Path,
    case_contract: Mapping[str, Any],
    frozen_at: str,
) -> dict[str, Any]:
    """Freeze a canonical label without comparing free-text issue descriptions."""

    contract = validate_case_evidence_contract(case_contract)
    value = deepcopy(dict(spec))
    _exact_keys(
        value,
        {
            "case_id",
            "envelope_id",
            "case_contract_digest",
            "reviews",
            "independent_evidence_validation",
        },
        "stage-2 scientific label input",
    )
    if _case_id(value["case_id"]) != contract["case_id"]:
        raise ProspectiveQualificationV2Error("Label and case-contract identities differ.")
    if value["envelope_id"] != contract["envelope"]["envelope_id"]:
        raise ProspectiveQualificationV2Error("Label and envelope identities differ.")
    if value["case_contract_digest"] != contract["contract_digest"]:
        raise ProspectiveQualificationV2Error("Label does not bind the exact case contract.")

    reviews = tuple(_review(item) for item in _sequence(value["reviews"], "reviews"))
    if len(reviews) != 2:
        raise ProspectiveQualificationV2Error("Exactly two Stage-2 reviews are required.")
    if len({item["reviewer_id"] for item in reviews}) != 2:
        raise ProspectiveQualificationV2Error("Stage-2 reviewer identities must be distinct.")
    if len({item["provider"] for item in reviews}) != 2:
        raise ProspectiveQualificationV2Error("Stage-2 reviews must use two providers.")
    author = contract["authorship"]
    if any(
        item["reviewer_id"] == author["author_id"] or item["provider"] == author["provider"]
        for item in reviews
    ):
        raise ProspectiveQualificationV2Error(
            "Stage-2 reviewers must be independent of the case author."
        )

    validation = _evidence_validation(
        value["independent_evidence_validation"],
        case_root=case_root,
        case_contract=contract,
    )
    if validation["validator_id"] in {
        str(author["author_id"]),
        *(str(item["reviewer_id"]) for item in reviews),
    } or validation["provider"] in {
        str(author["provider"]),
        *(str(item["provider"]) for item in reviews),
    }:
        raise ProspectiveQualificationV2Error(
            "The evidence validator must be independent of the author and Stage-2 reviewers."
        )
    if validation["case_contract_digest"] != contract["contract_digest"]:
        raise ProspectiveQualificationV2Error(
            "Independent evidence validation does not bind the case contract."
        )
    binding_digest = contract["selected_result_binding_digest"]
    if validation["status"] == "verified_complete":
        if validation["selected_result_binding_digest"] != binding_digest:
            raise ProspectiveQualificationV2Error(
                "Verified evidence does not bind the exact selected-result declaration."
            )
    elif validation["selected_result_binding_digest"] is not None:
        raise ProspectiveQualificationV2Error(
            "Incomplete evidence validation cannot verify a selected-result binding."
        )

    frozen = _timestamp(frozen_at)
    completed_times = [_timestamp(str(item["completed_at"])) for item in reviews]
    completed_times.append(_timestamp(str(validation["completed_at"])))
    if any(completed > frozen for completed in completed_times):
        raise ProspectiveQualificationV2Error("Scientific label predates required review evidence.")

    label, issue_class = _resolve_label(
        reviews,
        validation_status=str(validation["status"]),
        canonical_issue_class=str(contract["canonical_issue_class"]),
        selected_result_binding_digest=str(binding_digest),
    )
    record: dict[str, Any] = {
        "artifact_kind": "prospective_stage2_scientific_label",
        "label_version": SCIENTIFIC_LABEL_VERSION,
        "case_id": contract["case_id"],
        "envelope_id": contract["envelope"]["envelope_id"],
        "case_contract_digest": contract["contract_digest"],
        "selected_result_binding_digest": binding_digest,
        "scientific_label": label,
        "canonical_issue_class": issue_class,
        "reviews": sorted(reviews, key=lambda item: str(item["reviewer_id"])),
        "independent_evidence_validation": validation,
        "frozen_at": _iso(frozen),
        "qualification_authority": "none_scientific_label_only",
        "free_text_used_for_label_resolution": False,
    }
    record["label_digest"] = semantic_digest(record)
    return record


def validate_case_evidence_contract(value: Mapping[str, Any]) -> dict[str, Any]:
    """Replay one frozen v2 case-evidence contract exactly."""

    contract = deepcopy(dict(value))
    expected_digest = contract.pop("contract_digest", None)
    if expected_digest != semantic_digest(contract):
        raise ProspectiveQualificationV2Error("Case-evidence contract digest does not replay.")
    if (
        contract.get("artifact_kind") != "prospective_case_evidence_contract"
        or contract.get("contract_version") != CASE_EVIDENCE_CONTRACT_VERSION
        or contract.get("evidence_status") != "unverified_author_declaration"
        or contract.get("qualification_authority") != "none_case_contract_only"
    ):
        raise ProspectiveQualificationV2Error("Unsupported case-evidence contract artifact.")
    replayed = freeze_case_evidence_contract(
        {
            key: contract[key]
            for key in (
                "case_id",
                "envelope",
                "canonical_issue_class",
                "selected_result_binding",
                "authorship",
                "authored_at",
            )
        },
        frozen_at=str(contract["frozen_at"]),
    )
    contract["contract_digest"] = expected_digest
    if replayed != contract:
        raise ProspectiveQualificationV2Error("Case-evidence contract semantics do not replay.")
    return contract


def _resolve_label(
    reviews: tuple[dict[str, Any], ...],
    *,
    validation_status: str,
    canonical_issue_class: str,
    selected_result_binding_digest: str,
) -> tuple[ScientificLabel, str | None]:
    if validation_status == "ambiguous_selected_result":
        return "conditional_or_unknown", None
    if validation_status == "insufficient_evidence":
        return "insufficient_evidence", None
    if validation_status == "unsupported_structure":
        return "unsupported", None

    labels = {str(item["scientific_label"]) for item in reviews}
    if len(labels) != 1:
        return "review_disagreement", None
    label = labels.pop()
    if any(
        item["selected_result_binding_digest"] != selected_result_binding_digest
        or item["selected_result_binding_status"] != "verified"
        or item["finite_counterevidence_status"] != "complete"
        for item in reviews
    ):
        return "insufficient_evidence", None
    if label == "issue_present":
        if any(item["issue_class_id"] != canonical_issue_class for item in reviews):
            raise ProspectiveQualificationV2Error(
                "Issue-present reviews must use the frozen canonical issue-class identifier."
            )
        return "issue_present", canonical_issue_class
    if any(item["issue_class_id"] is not None for item in reviews):
        raise ProspectiveQualificationV2Error(
            "Issue-absent reviews cannot carry an issue-class identifier."
        )
    return "issue_absent", None


def _selected_result_binding(value: Any) -> dict[str, Any]:
    binding = deepcopy(_mapping(value, "selected_result_binding"))
    _exact_keys(
        binding,
        {
            "binding_profile",
            "selection_status",
            "report_locator",
            "result_locator",
            "producer_locator",
            "source_operands",
            "alternative_producer_locators",
            "declared_dynamic_selection",
        },
        "selected_result_binding",
    )
    if binding["binding_profile"] != "exact_selected_report_result_static_producer_v1":
        raise ProspectiveQualificationV2Error("Unsupported selected-result binding profile.")
    if binding["selection_status"] != "one_selected_result":
        raise ProspectiveQualificationV2Error("One selected result must be declared exactly.")
    if binding["declared_dynamic_selection"] is not False:
        raise ProspectiveQualificationV2Error("Dynamic selected-result paths are unsupported.")
    report = _locator(binding["report_locator"], "report_locator")
    result = _locator(binding["result_locator"], "result_locator")
    producer = _locator(binding["producer_locator"], "producer_locator")
    if report["path"] != result["path"] or report["content_digest"] != result["content_digest"]:
        raise ProspectiveQualificationV2Error(
            "Selected result must be localized inside the exact selected report bytes."
        )
    if int(result["start_line"]) < int(report["start_line"]) or int(result["end_line"]) > int(
        report["end_line"]
    ):
        raise ProspectiveQualificationV2Error(
            "Selected result must be contained inside the selected report span."
        )
    operands = [
        _source_operand(item) for item in _sequence(binding["source_operands"], "source_operands")
    ]
    if not operands:
        raise ProspectiveQualificationV2Error("Selected result requires source operands.")
    if len({str(item["operand_id"]) for item in operands}) != len(operands):
        raise ProspectiveQualificationV2Error("Source operand identities must be unique.")
    alternatives = [
        _locator(item, "alternative_producer_locator")
        for item in _sequence(
            binding["alternative_producer_locators"], "alternative_producer_locators"
        )
    ]
    if any(item == producer for item in alternatives):
        raise ProspectiveQualificationV2Error(
            "Selected producer cannot also be an alternative producer."
        )
    if len({semantic_digest(item) for item in alternatives}) != len(alternatives):
        raise ProspectiveQualificationV2Error("Alternative producer locators must be unique.")
    binding.update(
        {
            "report_locator": report,
            "result_locator": result,
            "producer_locator": producer,
            "source_operands": sorted(operands, key=lambda item: str(item["operand_id"])),
            "alternative_producer_locators": sorted(
                alternatives,
                key=lambda item: (
                    str(item["path"]),
                    int(item["start_line"]),
                    int(item["end_line"]),
                    str(item["content_digest"]),
                ),
            ),
        }
    )
    return binding


def _review(value: Any) -> dict[str, Any]:
    review = deepcopy(_mapping(value, "stage-2 review"))
    _exact_keys(
        review,
        {
            "reviewer_id",
            "provider",
            "completed_at",
            "scientific_label",
            "issue_class_id",
            "selected_result_binding_digest",
            "selected_result_binding_status",
            "finite_counterevidence_status",
            "bounded_description",
            "review_digest",
        },
        "stage-2 review",
    )
    expected = review.pop("review_digest")
    if expected != semantic_digest(review):
        raise ProspectiveQualificationV2Error("Stage-2 review digest does not replay.")
    review["review_digest"] = expected
    _text(review["reviewer_id"], "reviewer_id")
    _text(review["provider"], "provider")
    _timestamp(_text(review["completed_at"], "completed_at"))
    if review["scientific_label"] not in _REVIEW_LABELS:
        raise ProspectiveQualificationV2Error("Unsupported Stage-2 scientific label.")
    if review["issue_class_id"] is not None:
        _issue_class(review["issue_class_id"])
    _digest(review["selected_result_binding_digest"], "selected_result_binding_digest")
    if review["selected_result_binding_status"] not in {"verified", "unverified"}:
        raise ProspectiveQualificationV2Error("Unsupported selected-result binding status.")
    if review["finite_counterevidence_status"] not in {"complete", "incomplete"}:
        raise ProspectiveQualificationV2Error("Unsupported finite-counterevidence status.")
    _text(review["bounded_description"], "bounded_description")
    return review


def _evidence_validation(
    value: Any, *, case_root: Path, case_contract: Mapping[str, Any]
) -> dict[str, Any]:
    try:
        return validate_selected_result_validation(
            _mapping(value, "independent_evidence_validation"),
            case_root=case_root,
            case_contract=case_contract,
        )
    except ProspectiveSelectedResultVerifierError as error:
        raise ProspectiveQualificationV2Error(str(error)) from error


def _envelope(value: Any) -> dict[str, Any]:
    envelope = deepcopy(_mapping(value, "envelope"))
    _exact_keys(
        envelope,
        {"envelope_id", "check_id", "candidate_id", "binding_digest"},
        "envelope",
    )
    for key in ("envelope_id", "check_id", "candidate_id"):
        _text(envelope[key], key)
    _digest(envelope["binding_digest"], "binding_digest")
    return envelope


def _authorship(value: Any) -> dict[str, Any]:
    authorship = deepcopy(_mapping(value, "authorship"))
    _exact_keys(
        authorship,
        {"author_id", "provider", "execution_context_id", "identity_evidence_digest"},
        "authorship",
    )
    for key in ("author_id", "provider", "execution_context_id"):
        _text(authorship[key], key)
    _digest(authorship["identity_evidence_digest"], "identity_evidence_digest")
    return authorship


def _source_operand(value: Any) -> dict[str, Any]:
    operand = deepcopy(_mapping(value, "source operand"))
    _exact_keys(
        operand,
        {"operand_id", "record_ref", "source_locator"},
        "source operand",
    )
    _text(operand["operand_id"], "operand_id")
    record_ref = deepcopy(_mapping(operand["record_ref"], "source operand record_ref"))
    _exact_keys(record_ref, {"record_type", "record_id"}, "source operand record_ref")
    _text(record_ref["record_type"], "source operand record_type")
    _text(record_ref["record_id"], "source operand record_id")
    operand["record_ref"] = record_ref
    operand["source_locator"] = _locator(operand["source_locator"], "source operand locator")
    return operand


def _locator(value: Any, label: str) -> dict[str, Any]:
    locator = deepcopy(_mapping(value, label))
    _exact_keys(locator, {"path", "content_digest", "start_line", "end_line"}, label)
    path = _relative_path(locator["path"], f"{label} path")
    _digest(locator["content_digest"], f"{label} content_digest")
    start = locator["start_line"]
    end = locator["end_line"]
    if not isinstance(start, int) or isinstance(start, bool) or start < 1:
        raise ProspectiveQualificationV2Error(f"{label} start_line is invalid.")
    if not isinstance(end, int) or isinstance(end, bool) or end < start:
        raise ProspectiveQualificationV2Error(f"{label} end_line is invalid.")
    locator["path"] = path
    return locator


def _case_id(value: Any) -> str:
    case_id = _text(value, "case_id")
    if not case_id.startswith("case:") or len(case_id) != 25:
        raise ProspectiveQualificationV2Error("case_id must be one opaque 20-hex identity.")
    try:
        int(case_id.removeprefix("case:"), 16)
    except ValueError as error:
        raise ProspectiveQualificationV2Error(
            "case_id must be one opaque 20-hex identity."
        ) from error
    return case_id


def _issue_class(value: Any) -> str:
    issue_class = _text(value, "canonical_issue_class")
    if not issue_class.startswith("issue-class:") or any(
        character.isspace() for character in issue_class
    ):
        raise ProspectiveQualificationV2Error(
            "canonical issue classes must use one registered issue-class identifier."
        )
    return issue_class


def _relative_path(value: Any, label: str) -> str:
    path = _text(value, label)
    parsed = PurePosixPath(path)
    if (
        parsed.is_absolute()
        or not parsed.parts
        or path == "."
        or ".." in parsed.parts
        or path != parsed.as_posix()
    ):
        raise ProspectiveQualificationV2Error(f"{label} must be a normalized relative path.")
    return path


def _digest(value: Any, label: str) -> str:
    digest = _text(value, label)
    if not digest.startswith("sha256:") or len(digest) != 71:
        raise ProspectiveQualificationV2Error(f"{label} must be one full sha256 digest.")
    try:
        int(digest.removeprefix("sha256:"), 16)
    except ValueError as error:
        raise ProspectiveQualificationV2Error(f"{label} must be one full sha256 digest.") from error
    return digest


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ProspectiveQualificationV2Error("Timestamp must use ISO 8601.") from error
    if parsed.tzinfo is None:
        raise ProspectiveQualificationV2Error("Timestamp must include a timezone.")
    return parsed.astimezone(UTC)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ProspectiveQualificationV2Error(f"{label} must be an object.")
    return dict(value)


def _sequence(value: Any, label: str) -> list[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ProspectiveQualificationV2Error(f"{label} must be an array.")
    return list(value)


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ProspectiveQualificationV2Error(f"{label} must be nonempty text.")
    return value


def _exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise ProspectiveQualificationV2Error(
            f"{label} has unexpected fields; expected={sorted(expected)}, received={sorted(value)}."
        )
