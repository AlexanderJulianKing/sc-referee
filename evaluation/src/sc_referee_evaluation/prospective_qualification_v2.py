from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any, Literal

from sc_referee.core.errors import RecordValidationError
from sc_referee.core.ids import semantic_digest
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee_evaluation.prospective_selected_result_verifier import (
    ProspectiveSelectedResultVerifierError,
    validate_selected_result_validation,
)

AUTHOR_DECLARATION_VERSION = "3.0.0"
CASE_EVIDENCE_CONTRACT_VERSION = "3.0.0"
SCIENTIFIC_LABEL_VERSION = "3.0.0"

ScientificLabel = Literal[
    "issue_present",
    "issue_absent",
    "conditional_or_unknown",
    "insufficient_evidence",
    "unsupported",
    "review_disagreement",
]

_REVIEW_LABELS = {"issue_present", "issue_absent"}
_DECLARATION_STATES = {
    "one_selected_result",
    "multiple_candidate_results",
    "unsupported_producer_surface",
}


class ProspectiveQualificationV2Error(ValueError):
    """Raised when prospective case or label evidence is not closed and replayable."""


def freeze_author_selected_result_declaration(
    spec: Mapping[str, Any], *, frozen_at: str
) -> dict[str, Any]:
    """Freeze only the result-selection facts visible to a prospective case author."""

    value = deepcopy(dict(spec))
    _exact_keys(
        value,
        {
            "case_id",
            "declaration_state",
            "selected_result_binding",
            "candidate_result_locators",
            "unsupported_producer_locators",
            "authorship",
            "authored_at",
        },
        "author selected-result declaration",
    )
    case_id = _case_id(value["case_id"])
    state = _text(value["declaration_state"], "declaration_state")
    if state not in _DECLARATION_STATES:
        raise ProspectiveQualificationV2Error("Unsupported author declaration state.")
    binding = (
        None
        if value["selected_result_binding"] is None
        else _selected_result_binding(value["selected_result_binding"])
    )
    candidates = sorted(
        (
            _locator(item, "candidate_result_locator")
            for item in _sequence(value["candidate_result_locators"], "candidate_result_locators")
        ),
        key=semantic_digest,
    )
    unsupported = sorted(
        (
            _locator(item, "unsupported_producer_locator")
            for item in _sequence(
                value["unsupported_producer_locators"], "unsupported_producer_locators"
            )
        ),
        key=semantic_digest,
    )
    if len({semantic_digest(item) for item in candidates}) != len(candidates):
        raise ProspectiveQualificationV2Error("Candidate result locators must be unique.")
    if len({semantic_digest(item) for item in unsupported}) != len(unsupported):
        raise ProspectiveQualificationV2Error("Unsupported producer locators must be unique.")
    if state == "one_selected_result":
        if binding is None or candidates or unsupported:
            raise ProspectiveQualificationV2Error(
                "One-result declarations require exactly one binding and no failure-state locators."
            )
    elif state == "multiple_candidate_results":
        if binding is not None or len(candidates) < 2 or unsupported:
            raise ProspectiveQualificationV2Error(
                "Multiple-result declarations require at least two candidate locators and no "
                "single binding."
            )
    elif binding is not None or candidates or not unsupported:
        raise ProspectiveQualificationV2Error(
            "Unsupported-producer declarations require producer evidence and no single binding."
        )

    authorship = _authorship(value["authorship"])
    authored_at = _timestamp(_text(value["authored_at"], "authored_at"))
    frozen = _timestamp(frozen_at)
    if authored_at > frozen:
        raise ProspectiveQualificationV2Error(
            "Author declaration cannot be frozen before authorship."
        )
    record: dict[str, Any] = {
        "artifact_kind": "prospective_author_selected_result_declaration",
        "declaration_version": AUTHOR_DECLARATION_VERSION,
        "case_id": case_id,
        "declaration_state": state,
        "selected_result_binding": binding,
        "selected_result_binding_digest": None if binding is None else semantic_digest(binding),
        "candidate_result_locators": candidates,
        "unsupported_producer_locators": unsupported,
        "authorship": authorship,
        "authored_at": _iso(authored_at),
        "frozen_at": _iso(frozen),
        "qualification_authority": "none_author_declaration_only",
    }
    record["declaration_digest"] = semantic_digest(record)
    return record


def freeze_case_evidence_contract(spec: Mapping[str, Any], *, frozen_at: str) -> dict[str, Any]:
    """Coordinator-bind a blinded author declaration to one scientific envelope."""

    value = deepcopy(dict(spec))
    _exact_keys(
        value,
        {
            "case_id",
            "envelope",
            "canonical_issue_class",
            "author_declaration",
            "coordinated_at",
        },
        "case evidence contract",
    )
    case_id = _case_id(value["case_id"])
    envelope = _envelope(value["envelope"])
    issue_class = _issue_class(value["canonical_issue_class"])
    declaration = validate_author_selected_result_declaration(value["author_declaration"])
    if declaration["case_id"] != case_id:
        raise ProspectiveQualificationV2Error(
            "Author declaration and coordinator case identities differ."
        )
    coordinated_at = _timestamp(_text(value["coordinated_at"], "coordinated_at"))
    frozen = _timestamp(frozen_at)
    if _timestamp(str(declaration["frozen_at"])) > coordinated_at or coordinated_at > frozen:
        raise ProspectiveQualificationV2Error(
            "Coordinator binding must follow the author-only freeze and precede contract freeze."
        )

    record: dict[str, Any] = {
        "artifact_kind": "prospective_case_evidence_contract",
        "contract_version": CASE_EVIDENCE_CONTRACT_VERSION,
        "case_id": case_id,
        "envelope": envelope,
        "canonical_issue_class": issue_class,
        "author_declaration": declaration,
        "author_declaration_digest": declaration["declaration_digest"],
        "declaration_state": declaration["declaration_state"],
        "selected_result_binding": declaration["selected_result_binding"],
        "selected_result_binding_digest": declaration["selected_result_binding_digest"],
        "authorship": declaration["authorship"],
        "authored_at": declaration["authored_at"],
        "coordinated_at": _iso(coordinated_at),
        "frozen_at": _iso(frozen),
        "evidence_status": "coordinator_bound_unverified_author_declaration",
        "qualification_authority": "none_case_contract_only",
    }
    record["contract_digest"] = semantic_digest(record)
    return record


def freeze_stage2_scientific_label(
    spec: Mapping[str, Any],
    *,
    case_root: Path,
    case_contract: Mapping[str, Any],
    schema_root: Path,
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
            "scientific_panel_freeze",
            "full_stage2_reviews",
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

    panel_freeze = _scientific_panel_freeze(
        value["scientific_panel_freeze"], case_id=str(contract["case_id"])
    )
    reviews = tuple(
        _stage2_review(item, case_id=str(contract["case_id"]), schema_root=schema_root)
        for item in _sequence(value["full_stage2_reviews"], "full_stage2_reviews")
    )
    if len(reviews) != 2:
        raise ProspectiveQualificationV2Error("Exactly two Stage-2 reviews are required.")
    if len({item["reviewer_id"] for item in reviews}) != 2:
        raise ProspectiveQualificationV2Error("Stage-2 reviewer identities must be distinct.")
    if len({item["provider"] for item in reviews}) != 2:
        raise ProspectiveQualificationV2Error("Stage-2 reviews must use two providers.")
    if len({item["execution_context_id"] for item in reviews}) != 2:
        raise ProspectiveQualificationV2Error("Stage-2 execution contexts must be distinct.")
    author = contract["authorship"]
    if any(
        item["reviewer_id"] == author["author_id"]
        or item["execution_context_id"] == author["execution_context_id"]
        for item in reviews
    ):
        raise ProspectiveQualificationV2Error(
            "Stage-2 reviewer identities and contexts must be independent of the case author."
        )
    _match_stage2_reviews_to_panel(reviews, panel_freeze)

    validation = _evidence_validation(
        value["independent_evidence_validation"],
        case_root=case_root,
        case_contract=contract,
    )
    if validation["validator_id"] in {
        str(author["author_id"]),
        *(str(item["reviewer_id"]) for item in reviews),
    } or validation["execution_context_id"] in {
        str(author["execution_context_id"]),
        *(str(item["execution_context_id"]) for item in reviews),
    }:
        raise ProspectiveQualificationV2Error(
            "The evidence-validator identity and context must be independent of the author and "
            "Stage-2 reviewers."
        )
    if validation["case_contract_digest"] != contract["contract_digest"]:
        raise ProspectiveQualificationV2Error(
            "Independent evidence validation does not bind the case contract."
        )
    binding_digest = contract["selected_result_binding_digest"]
    if validation["status"] == "verified_complete":
        if binding_digest is None or validation["selected_result_binding_digest"] != binding_digest:
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
    completed_times.append(_timestamp(str(panel_freeze["frozen_at"])))
    if any(completed > frozen for completed in completed_times):
        raise ProspectiveQualificationV2Error("Scientific label predates required review evidence.")

    label, issue_class = _resolve_label(
        reviews,
        validation_status=str(validation["status"]),
        canonical_issue_class=str(contract["canonical_issue_class"]),
        selected_result_binding_digest=binding_digest,
    )
    record: dict[str, Any] = {
        "artifact_kind": "prospective_stage2_scientific_label",
        "label_version": SCIENTIFIC_LABEL_VERSION,
        "case_id": contract["case_id"],
        "envelope_id": contract["envelope"]["envelope_id"],
        "case_contract_digest": contract["contract_digest"],
        "scientific_panel_freeze_digest": panel_freeze["freeze_digest"],
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
        or contract.get("evidence_status") != "coordinator_bound_unverified_author_declaration"
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
                "author_declaration",
                "coordinated_at",
            )
        },
        frozen_at=str(contract["frozen_at"]),
    )
    contract["contract_digest"] = expected_digest
    if replayed != contract:
        raise ProspectiveQualificationV2Error("Case-evidence contract semantics do not replay.")
    return contract


def validate_author_selected_result_declaration(value: Mapping[str, Any]) -> dict[str, Any]:
    """Replay one author-only declaration without introducing coordinator-only fields."""

    declaration = deepcopy(dict(value))
    expected_digest = declaration.pop("declaration_digest", None)
    if expected_digest != semantic_digest(declaration):
        raise ProspectiveQualificationV2Error("Author declaration digest does not replay.")
    if (
        declaration.get("artifact_kind") != "prospective_author_selected_result_declaration"
        or declaration.get("declaration_version") != AUTHOR_DECLARATION_VERSION
        or declaration.get("qualification_authority") != "none_author_declaration_only"
    ):
        raise ProspectiveQualificationV2Error("Unsupported author declaration artifact.")
    replayed = freeze_author_selected_result_declaration(
        {
            key: declaration[key]
            for key in (
                "case_id",
                "declaration_state",
                "selected_result_binding",
                "candidate_result_locators",
                "unsupported_producer_locators",
                "authorship",
                "authored_at",
            )
        },
        frozen_at=str(declaration["frozen_at"]),
    )
    declaration["declaration_digest"] = expected_digest
    if replayed != declaration:
        raise ProspectiveQualificationV2Error("Author declaration semantics do not replay.")
    return declaration


def _resolve_label(
    reviews: tuple[dict[str, Any], ...],
    *,
    validation_status: str,
    canonical_issue_class: str,
    selected_result_binding_digest: str | None,
) -> tuple[ScientificLabel, str | None]:
    if validation_status == "ambiguous_selected_result":
        return "conditional_or_unknown", None
    if validation_status == "insufficient_evidence":
        return "insufficient_evidence", None
    if validation_status == "unsupported_structure":
        return "unsupported", None
    if any(item["material_dissent"] is True for item in reviews):
        return "review_disagreement", None

    labels = {str(item["scientific_label"]) for item in reviews}
    if not labels.issubset(_REVIEW_LABELS):
        return "insufficient_evidence", None
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


def _stage2_review(value: Any, *, case_id: str, schema_root: Path) -> dict[str, Any]:
    full_review = deepcopy(_mapping(value, "full Stage-2 AgentReview"))
    try:
        LocalSchemaRegistry(schema_root).validate(full_review)
    except RecordValidationError as error:
        raise ProspectiveQualificationV2Error(str(error)) from error
    if full_review.get("record_type") != "agent_review" or full_review.get("stage") != (
        "stage2_scientific_adjudication"
    ):
        raise ProspectiveQualificationV2Error(
            "V3 labels require complete Stage-2 AgentReview records."
        )
    if full_review.get("case_id") != case_id:
        raise ProspectiveQualificationV2Error(
            "Full Stage-2 review and case-contract identities differ."
        )
    agent = _mapping(full_review["reviewer_agent"], "reviewer_agent")
    extensions = _mapping(full_review.get("extensions"), "Stage-2 review extensions")
    required_extensions = {
        "x-reviewer-actor-id",
        "x-selected-result-binding-digest",
        "x-selected-result-binding-status",
        "x-finite-counterevidence-status",
    }
    if not required_extensions.issubset(extensions):
        raise ProspectiveQualificationV2Error(
            "Full Stage-2 review lacks required v3 binding extensions."
        )
    reviewer_id = _text(extensions["x-reviewer-actor-id"], "x-reviewer-actor-id")
    binding_digest = extensions["x-selected-result-binding-digest"]
    if binding_digest is not None:
        _digest(binding_digest, "x-selected-result-binding-digest")
    binding_status = extensions["x-selected-result-binding-status"]
    if binding_status not in {"verified", "unverified"}:
        raise ProspectiveQualificationV2Error("Unsupported selected-result binding status.")
    counterevidence_status = extensions["x-finite-counterevidence-status"]
    if counterevidence_status not in {"complete", "incomplete"}:
        raise ProspectiveQualificationV2Error("Unsupported finite-counterevidence status.")
    verdict = str(full_review["verdict"])
    label_by_verdict = {
        "demonstrated_issue": "issue_present",
        "no_demonstrated_issue_within_scope": "issue_absent",
        "conditional_or_unknown": "conditional_or_unknown",
        "insufficient_evidence": "insufficient_evidence",
        "review_failure": "unsupported",
    }
    issue_class = full_review.get("issue_class")
    if issue_class is not None:
        _issue_class(issue_class)
    bounded_statement = full_review.get("bounded_statement")
    if bounded_statement is not None:
        _text(bounded_statement, "bounded_statement")
    falsification = _mapping(full_review["falsification_attempt"], "falsification_attempt")
    return {
        "reviewer_id": reviewer_id,
        "provider": _text(agent["provider"], "reviewer provider"),
        "execution_context_id": _text(
            agent["execution_context_id"], "reviewer execution_context_id"
        ),
        "full_review_ref": {
            "record_type": "agent_review",
            "record_id": _text(full_review["review_id"], "review_id"),
        },
        "full_review_digest": semantic_digest(full_review),
        "completed_at": _text(full_review["completed_at"], "completed_at"),
        "scientific_label": label_by_verdict[verdict],
        "issue_class_id": issue_class,
        "selected_result_binding_digest": binding_digest,
        "selected_result_binding_status": binding_status,
        "finite_counterevidence_status": counterevidence_status,
        "bounded_description": bounded_statement,
        "material_dissent": falsification["material_dissent"],
    }


def _scientific_panel_freeze(value: Any, *, case_id: str) -> dict[str, Any]:
    panel = deepcopy(_mapping(value, "scientific_panel_freeze"))
    expected_digest = panel.pop("freeze_digest", None)
    _digest(expected_digest, "scientific_panel_freeze freeze_digest")
    if expected_digest != semantic_digest(panel):
        raise ProspectiveQualificationV2Error("Scientific-panel freeze digest does not replay.")
    panel["freeze_digest"] = expected_digest
    if panel.get("record_type") != "evaluation_scientific_label_freeze":
        raise ProspectiveQualificationV2Error("Scientific-panel freeze record kind is invalid.")
    if panel.get("case_id") != case_id:
        raise ProspectiveQualificationV2Error(
            "Scientific-panel freeze and case-contract identities differ."
        )
    if panel.get("detector_output_observed") is not False:
        raise ProspectiveQualificationV2Error(
            "Scientific-panel freeze must precede detector-output observation."
        )
    _digest(panel.get("stage1_freeze_digest"), "stage1_freeze_digest")
    _timestamp(_text(panel.get("frozen_at"), "scientific_panel_freeze frozen_at"))
    entries = [
        _scientific_panel_stage2_entry(item)
        for item in _sequence(panel.get("stage2_reviews"), "scientific_panel_freeze stage2_reviews")
    ]
    if len(entries) != 2:
        raise ProspectiveQualificationV2Error(
            "Scientific-panel freeze must contain exactly two Stage-2 review entries."
        )
    if len({item["review_ref"]["record_id"] for item in entries}) != 2:
        raise ProspectiveQualificationV2Error(
            "Scientific-panel Stage-2 review identities must be distinct."
        )
    if len({item["provider"] for item in entries}) != 2:
        raise ProspectiveQualificationV2Error(
            "Scientific-panel Stage-2 reviews must use two providers."
        )
    if len({item["execution_context_id"] for item in entries}) != 2:
        raise ProspectiveQualificationV2Error(
            "Scientific-panel Stage-2 execution contexts must be distinct."
        )
    return panel


def _scientific_panel_stage2_entry(value: Any) -> dict[str, Any]:
    entry = _mapping(value, "scientific-panel Stage-2 entry")
    review_ref = _mapping(entry.get("review_ref"), "scientific-panel Stage-2 review_ref")
    _exact_keys(
        review_ref,
        {"record_type", "record_id"},
        "scientific-panel Stage-2 review_ref",
    )
    if review_ref["record_type"] != "agent_review":
        raise ProspectiveQualificationV2Error(
            "Scientific-panel Stage-2 entries must reference AgentReview records."
        )
    _text(review_ref["record_id"], "scientific-panel Stage-2 review ID")
    _digest(entry.get("review_digest"), "scientific-panel Stage-2 review_digest")
    _text(entry.get("provider"), "scientific-panel Stage-2 provider")
    _text(
        entry.get("execution_context_id"),
        "scientific-panel Stage-2 execution_context_id",
    )
    _timestamp(_text(entry.get("completed_at"), "scientific-panel Stage-2 completed_at"))
    return entry


def _match_stage2_reviews_to_panel(
    reviews: tuple[dict[str, Any], ...], panel: Mapping[str, Any]
) -> None:
    entries = {
        str(entry["review_ref"]["record_id"]): entry
        for entry in (
            _scientific_panel_stage2_entry(item)
            for item in _sequence(panel["stage2_reviews"], "scientific_panel_freeze stage2_reviews")
        )
    }
    if {str(review["full_review_ref"]["record_id"]) for review in reviews} != set(entries):
        raise ProspectiveQualificationV2Error(
            "V2 Stage-2 summaries do not reference the exact frozen Stage-2 review set."
        )
    for review in reviews:
        review_id = str(review["full_review_ref"]["record_id"])
        entry = entries[review_id]
        if (
            review["full_review_digest"] != entry["review_digest"]
            or review["provider"] != entry["provider"]
            or review["execution_context_id"] != entry["execution_context_id"]
            or review["completed_at"] != entry.get("completed_at")
        ):
            raise ProspectiveQualificationV2Error(
                "V2 Stage-2 summary identity does not match its frozen full review."
            )


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
