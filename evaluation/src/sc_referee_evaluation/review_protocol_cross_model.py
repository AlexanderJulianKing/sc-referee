"""Cross-model Stage-1 panel freezing under ADR-0066.

This is the versioned code path authorized by ADR-0066 for panels whose four
blind Stage-1 reviews come from one provider but two distinct model families.
The digest-bound ``review_protocol`` module is intentionally untouched: its
``freeze_stage1_panel`` requires two provider families and remains the default
for cross-provider panels. This module generalizes only the family axis, from
provider to the (provider, model family) pair, and records the single-provider
composition explicitly in the frozen record. Provider fields stay truthful.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest
from sc_referee.records.normalization import write_normalized_json_once

from .review_protocol import (
    ReviewProtocolError,
    _capture_index,
    _timestamp,
    _validate_capture_manifest,
    _validate_packet_digest,
    validate_stage1_review_submission,
)

ADR_REFERENCE = "ADR-0066-CROSS-MODEL-SINGLE-PROVIDER-REVIEW-PANEL.md"


def _reviewer_family(review: dict[str, Any]) -> str:
    agent = review["reviewer_agent"]
    return f"{agent['provider']}:{agent['model_name']}"


def _collect_entries(
    reviews: list[dict[str, Any]],
    packets: list[dict[str, Any]],
    capture_manifests: list[dict[str, Any]],
    schema_root: Path,
) -> tuple[list[dict[str, Any]], Counter[str], Counter[str], set[str]]:
    packets_by_digest: dict[str, dict[str, Any]] = {}
    for packet in packets:
        _validate_packet_digest(packet)
        packet_digest = str(packet["packet_digest"])
        if packet_digest in packets_by_digest:
            raise ReviewProtocolError(f"Duplicate Stage-1 packet digest {packet_digest!r}.")
        packets_by_digest[packet_digest] = packet
    captures_by_review = _capture_index(capture_manifests, "stage1_blind")

    review_ids: set[str] = set()
    contexts: set[str] = set()
    providers: Counter[str] = Counter()
    families: Counter[str] = Counter()
    case_ids: set[str] = set()
    entries: list[dict[str, Any]] = []
    for review in reviews:
        packet_digest = str(review.get("extensions", {}).get("x-review-packet-digest", ""))
        matched_packet = packets_by_digest.get(packet_digest)
        if matched_packet is None:
            raise ReviewProtocolError("Stage-1 review has no exact supplied packet digest.")
        validate_stage1_review_submission(review, matched_packet, schema_root)
        review_id = str(review["review_id"])
        capture = captures_by_review.get(review_id)
        if capture is None:
            raise ReviewProtocolError("Stage-1 review has no exact supplied capture manifest.")
        _validate_capture_manifest(capture, review, matched_packet)
        context = str(review["reviewer_agent"]["execution_context_id"])
        if review_id in review_ids:
            raise ReviewProtocolError(f"Duplicate Stage-1 review identity {review_id!r}.")
        if context in contexts:
            raise ReviewProtocolError(f"Reused Stage-1 execution context {context!r}.")
        review_ids.add(review_id)
        contexts.add(context)
        provider = str(review["reviewer_agent"]["provider"])
        providers[provider] += 1
        families[_reviewer_family(review)] += 1
        case_ids.add(str(review["case_id"]))
        entries.append(
            {
                "review_ref": {"record_type": "agent_review", "record_id": review_id},
                "review_digest": semantic_digest(review),
                "packet_digest": packet_digest,
                "capture_id": capture["capture_id"],
                "capture_digest": capture["capture_digest"],
                "transcript_digest": capture["transcript_digest"],
                "captured_at": capture["captured_at"],
                "provider": provider,
                "reviewer_family": _reviewer_family(review),
                "execution_context_id": context,
                "completed_at": review["completed_at"],
            }
        )
    if set(packets_by_digest) != {
        str(review.get("extensions", {}).get("x-review-packet-digest", "")) for review in reviews
    }:
        raise ReviewProtocolError("Every supplied Stage-1 packet must have exactly one review.")
    if set(captures_by_review) != review_ids:
        raise ReviewProtocolError("Every supplied Stage-1 capture must have exactly one review.")
    if len(case_ids) != 1:
        raise ReviewProtocolError("A Stage-1 freeze must contain exactly one case identity.")
    if len(families) != 2 or any(count < 2 for count in families.values()):
        raise ReviewProtocolError(
            "A cross-model Stage-1 freeze requires two independent reviews from each of two "
            "reviewer families."
        )
    return entries, providers, families, case_ids


def freeze_stage1_cross_model_panel(
    reviews: list[dict[str, Any]],
    packets: list[dict[str, Any]],
    capture_manifests: list[dict[str, Any]],
    schema_root: Path,
    *,
    frozen_at: str,
    output: Path,
) -> dict[str, Any]:
    """Freeze a complete 2x2 cross-model panel before Stage-2 evidence may be exposed."""

    if output.exists() or output.is_symlink():
        raise ReviewProtocolError(f"Stage-1 freeze output already exists: {output}")
    entries, providers, families, case_ids = _collect_entries(
        reviews, packets, capture_manifests, schema_root
    )
    frozen_time = _timestamp(frozen_at)
    if any(_timestamp(str(capture["captured_at"])) > frozen_time for capture in capture_manifests):
        raise ReviewProtocolError("Stage-1 frozen_at cannot precede a review capture.")

    frozen: dict[str, Any] = {
        "evaluation_protocol_version": "0.2.0",
        "record_type": "evaluation_stage1_freeze",
        "freeze_variant": "cross_model_single_provider_v1",
        "adr_reference": ADR_REFERENCE,
        "case_id": next(iter(case_ids)),
        "frozen_at": frozen_at,
        "reviews": sorted(entries, key=lambda item: str(item["review_ref"]["record_id"])),
        "provider_participation": dict(sorted(providers.items())),
        "reviewer_family_participation": dict(sorted(families.items())),
        "single_provider_cross_model_panel": len(providers) == 1,
        "detector_output_observed": False,
        "answer_side_evidence_observed": False,
    }
    frozen["freeze_digest"] = semantic_digest(frozen)
    write_normalized_json_once(output, frozen)
    return frozen


def validate_stage1_cross_model_freeze_evidence(
    frozen: dict[str, Any],
    reviews: list[dict[str, Any]],
    packets: list[dict[str, Any]],
    capture_manifests: list[dict[str, Any]],
    schema_root: Path,
) -> None:
    """Re-resolve one cross-model Stage-1 freeze against its exact inputs."""

    supplied = dict(frozen)
    digest = supplied.pop("freeze_digest", None)
    if digest != semantic_digest(supplied):
        raise ReviewProtocolError("Cross-model Stage-1 freeze digest does not replay.")
    if (
        frozen.get("record_type") != "evaluation_stage1_freeze"
        or frozen.get("freeze_variant") != "cross_model_single_provider_v1"
        or frozen.get("adr_reference") != ADR_REFERENCE
        or frozen.get("detector_output_observed") is not False
        or frozen.get("answer_side_evidence_observed") is not False
    ):
        raise ReviewProtocolError("Cross-model Stage-1 freeze metadata is invalid.")
    entries, providers, families, case_ids = _collect_entries(
        reviews, packets, capture_manifests, schema_root
    )
    if any(
        _timestamp(str(capture["captured_at"])) > _timestamp(str(frozen["frozen_at"]))
        for capture in capture_manifests
    ):
        raise ReviewProtocolError("Cross-model Stage-1 freeze replay predates a capture.")
    if (
        frozen.get("case_id") != next(iter(case_ids))
        or frozen.get("provider_participation") != dict(sorted(providers.items()))
        or frozen.get("reviewer_family_participation") != dict(sorted(families.items()))
        or frozen.get("reviews")
        != sorted(entries, key=lambda item: str(item["review_ref"]["record_id"]))
    ):
        raise ReviewProtocolError(
            "Cross-model Stage-1 freeze projection has drifted from exact capture inputs."
        )


_EVALUATION_ADJUDICATION_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "record_type": {"const": "evaluation_benchmark_adjudication"},
        "adr_reference": {"const": ADR_REFERENCE},
        "public_benchmark_adjudication_deferred_reason": {"type": "string", "minLength": 1},
        "adjudication_id": {"type": "string", "minLength": 1},
        "case_id": {"type": "string", "minLength": 1},
        "provider_families": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
            "minItems": 1,
            "uniqueItems": True,
        },
        "model_families": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
            "minItems": 2,
            "uniqueItems": True,
        },
        "provider_participation": {"type": "array", "minItems": 1},
        "label_status": {
            "enum": [
                "positive_demonstrated",
                "verified_good_eligible",
                "hard_negative_eligible",
                "ambiguous_excluded",
                "insufficient_evidence",
                "adjudication_failed",
            ]
        },
        "agreement": {
            "type": "object",
            "properties": {
                "cross_provider_support": {"const": False},
                "cross_model_support": {"const": True},
                "material_disagreement": {"type": "boolean"},
                "unresolved_dissent_excluded": {"const": True},
                "notes": {"type": ["string", "null"]},
            },
            "required": [
                "cross_provider_support",
                "cross_model_support",
                "material_disagreement",
                "unresolved_dissent_excluded",
            ],
            "additionalProperties": False,
        },
        "majority_vote_permitted": {"const": False},
        "agent_only_disclosure": {"type": "string", "minLength": 1},
        "adjudicated_at": {"type": "string", "minLength": 1},
        "stage1_review_refs": {"type": "array", "minItems": 4, "maxItems": 4},
        "stage2_review_refs": {"type": "array", "minItems": 2, "maxItems": 2},
        "adjudicated_root_cause_refs": {"type": "array"},
        "root_cause_reconciliation_status": {"enum": ["verified", "not_applicable", "unresolved"]},
    },
    "required": [
        "record_type",
        "adr_reference",
        "public_benchmark_adjudication_deferred_reason",
        "adjudication_id",
        "case_id",
        "provider_families",
        "model_families",
        "provider_participation",
        "label_status",
        "agreement",
        "majority_vote_permitted",
        "agent_only_disclosure",
        "adjudicated_at",
        "stage1_review_refs",
        "stage2_review_refs",
        "adjudicated_root_cause_refs",
        "root_cause_reconciliation_status",
    ],
}


def freeze_scientific_label_cross_model(
    adjudication: dict[str, Any],
    stage1_freeze: dict[str, Any],
    stage2_reviews: list[dict[str, Any]],
    stage2_packets: list[dict[str, Any]],
    stage2_capture_manifests: list[dict[str, Any]],
    schema_root: Path,
    *,
    frozen_at: str,
    output: Path,
    stage1_reviews: list[dict[str, Any]] | None = None,
    adjudicated_root_causes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Freeze one evaluation-private scientific label under ADR-0066.

    Identical to ``review_protocol.freeze_scientific_label`` except that the
    adjudication is an evaluation-private record validated against a strict
    local schema, because the immutable public BenchmarkAdjudication schema
    requires a cross-provider panel that ADR-0066 explicitly replaces for this
    envelope. Public adjudication issuance is deferred and disclosed.
    """

    from collections import Counter

    from jsonschema import Draft202012Validator

    from .review_protocol import (
        _capture_index,
        _validate_adjudication_participation,
        _validate_capture_manifest,
        _validate_stage1_freeze,
        _validate_stage1_reviews_against_freeze,
        validate_stage2_review_submission,
    )
    from .root_cause import RootCauseReconciliationError

    if output.exists() or output.is_symlink():
        raise ReviewProtocolError(f"Scientific-label freeze output already exists: {output}")
    _validate_stage1_freeze(stage1_freeze)
    packets_by_digest = {str(packet.get("packet_digest")): packet for packet in stage2_packets}
    if len(packets_by_digest) != len(stage2_packets):
        raise ReviewProtocolError("Stage-2 packets must have unique exact digests.")
    captures_by_review = _capture_index(stage2_capture_manifests, "stage2_scientific_adjudication")
    stage1_contexts = {str(item["execution_context_id"]) for item in stage1_freeze["reviews"]}
    stage2_contexts: set[str] = set()
    stage2_providers: Counter[str] = Counter()
    stage2_entries: list[dict[str, Any]] = []
    for review in stage2_reviews:
        packet_digest = str(review.get("extensions", {}).get("x-review-packet-digest", ""))
        packet = packets_by_digest.get(packet_digest)
        if packet is None:
            raise ReviewProtocolError("Stage-2 review has no exact supplied packet digest.")
        validate_stage2_review_submission(review, packet, schema_root)
        context = str(review["reviewer_agent"]["execution_context_id"])
        review_id = str(review["review_id"])
        capture = captures_by_review.get(review_id)
        if capture is None:
            raise ReviewProtocolError("Stage-2 review has no exact supplied capture manifest.")
        _validate_capture_manifest(capture, review, packet)
        if context in stage1_contexts:
            raise ReviewProtocolError("Stage-2 review reuses a Stage-1 execution context.")
        if context in stage2_contexts:
            raise ReviewProtocolError("Stage-2 reviews reuse an execution context.")
        stage2_contexts.add(context)
        provider = str(review["reviewer_agent"]["provider"])
        stage2_providers[provider] += 1
        stage2_entries.append(
            {
                "review_ref": {
                    "record_type": "agent_review",
                    "record_id": review["review_id"],
                },
                "review_digest": semantic_digest(review),
                "packet_digest": packet_digest,
                "capture_id": capture["capture_id"],
                "capture_digest": capture["capture_digest"],
                "transcript_digest": capture["transcript_digest"],
                "captured_at": capture["captured_at"],
                "provider": provider,
                "reviewer_family": _reviewer_family(review),
                "execution_context_id": context,
                "completed_at": review["completed_at"],
            }
        )
    if set(packets_by_digest) != {
        str(review.get("extensions", {}).get("x-review-packet-digest", ""))
        for review in stage2_reviews
    }:
        raise ReviewProtocolError("Every supplied Stage-2 packet must have exactly one review.")
    if set(captures_by_review) != {str(review["review_id"]) for review in stage2_reviews}:
        raise ReviewProtocolError("Every supplied Stage-2 capture must have exactly one review.")
    stage1_providers = {str(provider) for provider in stage1_freeze["provider_participation"]}
    if set(stage2_providers) != stage1_providers or any(
        count < 1 for count in stage2_providers.values()
    ):
        raise ReviewProtocolError(
            "Stage-2 freeze requires at least one fresh review from each Stage-1 provider family."
        )
    stage2_families = {_reviewer_family(review) for review in stage2_reviews}
    if len(stage2_families) != 2:
        raise ReviewProtocolError(
            "A cross-model Stage-2 freeze requires two distinct reviewer families."
        )

    try:
        Draft202012Validator(_EVALUATION_ADJUDICATION_SCHEMA).validate(adjudication)
    except Exception as error:
        raise ReviewProtocolError(
            f"evaluation_benchmark_adjudication failed validation: {error}"
        ) from error
    if adjudication.get("case_id") != stage1_freeze.get("case_id"):
        raise ReviewProtocolError("Adjudication case does not match the frozen panel.")
    if sorted(str(value) for value in adjudication["model_families"]) != sorted(
        str(value) for value in stage1_freeze["reviewer_family_participation"]
    ):
        raise ReviewProtocolError("Adjudication model families do not match the frozen panel.")
    expected_stage1_refs = {
        (str(item["review_ref"]["record_type"]), str(item["review_ref"]["record_id"]))
        for item in stage1_freeze["reviews"]
    }
    actual_stage1_refs = {
        (str(item.get("record_type")), str(item.get("record_id")))
        for item in adjudication["stage1_review_refs"]
    }
    expected_stage2_refs = {("agent_review", str(review["review_id"])) for review in stage2_reviews}
    actual_stage2_refs = {
        (str(item.get("record_type")), str(item.get("record_id")))
        for item in adjudication["stage2_review_refs"]
    }
    if actual_stage1_refs != expected_stage1_refs or actual_stage2_refs != expected_stage2_refs:
        raise ReviewProtocolError("Adjudication review refs do not match the frozen panels.")
    _validate_adjudication_participation(adjudication, stage1_freeze, stage2_providers)
    roots = adjudicated_root_causes or []
    actual_root_refs = {
        ("adjudicated_root_cause", str(root["adjudicated_root_cause_id"])) for root in roots
    }
    declared_root_refs = {
        (str(ref.get("record_type")), str(ref.get("record_id")))
        for ref in adjudication["adjudicated_root_cause_refs"]
    }
    if actual_root_refs != declared_root_refs:
        raise ReviewProtocolError(
            "Adjudication root-cause refs do not match the supplied canonical records."
        )
    if roots:
        if stage1_reviews is None:
            raise ReviewProtocolError(
                "Canonical root-cause validation requires the exact frozen Stage-1 reviews."
            )
        _validate_stage1_reviews_against_freeze(stage1_reviews, stage1_freeze)
        if len(roots) != 1:
            raise ReviewProtocolError(
                "This first reconciliation slice requires exactly one adjudicated root cause."
            )
        try:
            validate_adjudicated_root_cause_cross_model(
                roots[0], stage1_reviews, stage2_reviews, schema_root
            )
        except RootCauseReconciliationError as error:
            raise ReviewProtocolError(str(error)) from error
        if roots[0]["adjudicated_at"] != adjudication["adjudicated_at"]:
            raise ReviewProtocolError(
                "Root-cause and benchmark adjudication timestamps must match exactly."
            )

    stage1_frozen_at = _timestamp(str(stage1_freeze["frozen_at"]))
    if any(_timestamp(str(review["completed_at"])) < stage1_frozen_at for review in stage2_reviews):
        raise ReviewProtocolError("A Stage-2 review cannot complete before the Stage-1 freeze.")
    last_stage2_capture = max(
        _timestamp(str(capture["captured_at"])) for capture in stage2_capture_manifests
    )
    adjudicated_at = _timestamp(str(adjudication["adjudicated_at"]))
    frozen_time = _timestamp(frozen_at)
    if adjudicated_at < last_stage2_capture or frozen_time < adjudicated_at:
        raise ReviewProtocolError(
            "Scientific adjudication and label freeze must follow the completed Stage-2 panel."
        )

    frozen: dict[str, Any] = {
        "evaluation_protocol_version": "0.2.0",
        "record_type": "evaluation_scientific_label_freeze",
        "freeze_variant": "cross_model_single_provider_v1",
        "adr_reference": ADR_REFERENCE,
        "case_id": adjudication["case_id"],
        "stage1_freeze_digest": stage1_freeze["freeze_digest"],
        "stage2_reviews": sorted(
            stage2_entries, key=lambda item: str(item["review_ref"]["record_id"])
        ),
        "adjudication_ref": {
            "record_type": "evaluation_benchmark_adjudication",
            "record_id": adjudication["adjudication_id"],
        },
        "adjudication_digest": semantic_digest(adjudication),
        "adjudicated_root_causes": sorted(
            [
                {
                    "root_cause_ref": {
                        "record_type": "adjudicated_root_cause",
                        "record_id": root["adjudicated_root_cause_id"],
                    },
                    "root_cause_digest": semantic_digest(root),
                }
                for root in roots
            ],
            key=lambda item: str(item["root_cause_ref"]["record_id"]),
        ),
        "label_status": adjudication["label_status"],
        "frozen_at": frozen_at,
        "detector_output_observed": False,
    }
    frozen["freeze_digest"] = semantic_digest(frozen)
    write_normalized_json_once(output, frozen)
    return frozen


def _validate_reconciliation_panel_cross_model(
    stage1_reviews: list[dict[str, Any]], stage2_reviews: list[dict[str, Any]]
) -> tuple[str, str, list[dict[str, Any]]]:
    """Family-axis copy of ``root_cause._validate_reconciliation_panel`` under ADR-0066."""

    from sc_referee.records.root_cause import (
        canonical_candidate_refs,
        root_cause_candidate_ref,
    )

    from .root_cause import RootCauseReconciliationError, validate_review_local_candidate

    if len(stage1_reviews) < 2 or len(stage2_reviews) < 2:
        raise RootCauseReconciliationError(
            "Reconciliation requires at least two Stage-1 and two Stage-2 reviews."
        )
    reviews = [*stage1_reviews, *stage2_reviews]
    if any(review.get("verdict") != "demonstrated_issue" for review in reviews):
        raise RootCauseReconciliationError(
            "Canonical positive reconciliation requires demonstrated-issue reviews only."
        )
    if any(review.get("stage") != "stage1_blind" for review in stage1_reviews) or any(
        review.get("stage") != "stage2_scientific_adjudication" for review in stage2_reviews
    ):
        raise RootCauseReconciliationError("Root-cause reviews are assigned to the wrong stage.")
    case_ids = {str(review.get("case_id")) for review in reviews}
    issue_classes = {str(review.get("issue_class")) for review in reviews}
    if len(case_ids) != 1 or len(issue_classes) != 1:
        raise RootCauseReconciliationError(
            "Every reconciled review must share one case and issue class."
        )
    for review in reviews:
        validate_review_local_candidate(review)
    for review in stage1_reviews:
        identity = review["root_cause_identity"]
        if identity["reconciled_stage1_candidates"] or identity["equivalence_evidence"]:
            raise RootCauseReconciliationError(
                "Stage-1 local candidates cannot contain cross-review reconciliation."
            )
    stage1_by_id = {str(review["review_id"]): review for review in stage1_reviews}
    if len(stage1_by_id) != len(stage1_reviews):
        raise RootCauseReconciliationError("Stage-1 review identities are not unique.")
    stage2_by_id = {str(review["review_id"]): review for review in stage2_reviews}
    if len(stage2_by_id) != len(stage2_reviews):
        raise RootCauseReconciliationError("Stage-2 review identities are not unique.")
    stage1_families = {_reviewer_family(review) for review in stage1_reviews}
    stage2_families = {_reviewer_family(review) for review in stage2_reviews}
    if len(stage1_families) < 2 or stage2_families != stage1_families:
        raise RootCauseReconciliationError(
            "Cross-model Stage-2 reconciliation requires every Stage-1 reviewer family."
        )

    selections: list[list[dict[str, Any]]] = []
    for review in stage2_reviews:
        falsification = review.get("falsification_attempt", {})
        if (
            review.get("unresolved_material_questions")
            or falsification.get("material_dissent") is not False
            or falsification.get("outcome") != "root_cause_survived"
        ):
            raise RootCauseReconciliationError(
                "Stage-2 reconciliation retains material dissent, an unresolved question, "
                "or failed falsification."
            )
        selection = canonical_candidate_refs(
            list(review["root_cause_identity"]["reconciled_stage1_candidates"])
        )
        for candidate_ref in selection:
            review_id = str(candidate_ref["review_ref"]["record_id"])
            stage1_review = stage1_by_id.get(review_id)
            if stage1_review is None:
                raise RootCauseReconciliationError(
                    "A Stage-2 candidate reference does not resolve to the frozen Stage-1 panel."
                )
            if candidate_ref != root_cause_candidate_ref(stage1_review):
                raise RootCauseReconciliationError(
                    "A Stage-2 candidate reference does not match exact Stage-1 content."
                )
        selected_families = {
            _reviewer_family(stage1_by_id[str(item["review_ref"]["record_id"])])
            for item in selection
        }
        if selected_families != stage1_families:
            raise RootCauseReconciliationError(
                "A Stage-2 candidate set must include every required reviewer family."
            )
        selections.append(selection)
    candidate_refs = selections[0]
    if any(selection != candidate_refs for selection in selections[1:]):
        raise RootCauseReconciliationError(
            "Fresh Stage-2 reviewers did not select the identical Stage-1 candidate set."
        )
    return next(iter(case_ids)), next(iter(issue_classes)), candidate_refs


def build_adjudicated_root_cause_cross_model(
    stage1_reviews: list[dict[str, Any]],
    stage2_reviews: list[dict[str, Any]],
    schema_root: Path,
    *,
    adjudicated_at: str,
    statement_source_review_id: str,
    required_scientific_premises: list[str],
    stronger_claims_excluded: list[str],
    output: Path | None = None,
) -> dict[str, Any]:
    """Family-axis copy of ``root_cause.build_adjudicated_root_cause`` under ADR-0066."""

    from sc_referee.core.errors import RecordValidationError
    from sc_referee.records.root_cause import (
        ADJUDICATED_IDENTITY_PROFILE,
        adjudicated_root_cause_id,
    )
    from sc_referee.records.schema_registry import LocalSchemaRegistry
    from sc_referee.version import SCHEMA_VERSION

    from .root_cause import RootCauseReconciliationError, _canonical_objects, _timestamp

    if output is not None and (output.exists() or output.is_symlink()):
        raise RootCauseReconciliationError(f"AdjudicatedRootCause output already exists: {output}")
    registry = LocalSchemaRegistry(schema_root)
    try:
        for review in [*stage1_reviews, *stage2_reviews]:
            registry.validate(review)
    except RecordValidationError as error:
        raise RootCauseReconciliationError(str(error)) from error
    case_id, issue_class, candidate_refs = _validate_reconciliation_panel_cross_model(
        stage1_reviews, stage2_reviews
    )
    stage2_by_id = {str(review["review_id"]): review for review in stage2_reviews}
    statement_source = stage2_by_id.get(statement_source_review_id)
    if statement_source is None:
        raise RootCauseReconciliationError(
            "The statement source must name one of the supporting Stage-2 reviews."
        )
    if not stronger_claims_excluded or any(not item for item in stronger_claims_excluded):
        raise RootCauseReconciliationError(
            "At least one explicit nonempty stronger-claim exclusion is required."
        )
    if any(not item for item in required_scientific_premises):
        raise RootCauseReconciliationError(
            "Required scientific premises must be nonempty when supplied."
        )
    last_stage2 = max(_timestamp(str(review["completed_at"])) for review in stage2_reviews)
    if _timestamp(adjudicated_at) <= last_stage2:
        raise RootCauseReconciliationError(
            "Root-cause adjudication must follow every supporting Stage-2 review."
        )

    evidence = _canonical_objects(
        [
            evidence_item
            for review in stage2_reviews
            for evidence_item in review["root_cause_identity"]["equivalence_evidence"]
        ]
    )
    affected_record_refs = _canonical_objects(
        [
            record_ref
            for review in [*stage1_reviews, *stage2_reviews]
            for record_ref in review.get("affected_record_refs", [])
        ]
    )
    root_cause: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "adjudicated_root_cause",
        "adjudicated_root_cause_id": adjudicated_root_cause_id(
            case_id, issue_class, candidate_refs
        ),
        "case_id": case_id,
        "identity_profile": ADJUDICATED_IDENTITY_PROFILE,
        "stage1_candidate_refs": candidate_refs,
        "stage2_review_refs": sorted(
            [
                {"record_type": "agent_review", "record_id": review["review_id"]}
                for review in stage2_reviews
            ],
            key=lambda item: str(item["record_id"]),
        ),
        "statement_source_review_ref": {
            "record_type": "agent_review",
            "record_id": statement_source_review_id,
        },
        "bounded_statement": statement_source["bounded_statement"],
        "issue_class": issue_class,
        "evidence": evidence,
        "affected_record_refs": affected_record_refs,
        "required_scientific_premises": sorted(set(required_scientific_premises)),
        "stronger_claims_excluded": sorted(set(stronger_claims_excluded)),
        "material_dissent": False,
        "confidence_used_for_identity": False,
        "adjudicated_at": adjudicated_at,
        "provenance": {
            "actor": {
                "actor_kind": "controller",
                "actor_id": "software:sc-referee-eval",
                "display_name": "sc-referee evaluation controller",
            },
            "method": "deterministic_root_cause_reconciliation",
            "created_at": adjudicated_at,
            "tool": "sc-referee-eval",
            "tool_version": "0.1.0",
        },
    }
    try:
        registry.validate(root_cause)
    except RecordValidationError as error:
        raise RootCauseReconciliationError(str(error)) from error
    if output is not None:
        write_normalized_json_once(output, root_cause)
    return root_cause


def validate_adjudicated_root_cause_cross_model(
    root_cause: dict[str, Any],
    stage1_reviews: list[dict[str, Any]],
    stage2_reviews: list[dict[str, Any]],
    schema_root: Path,
) -> None:
    """Require a root record to equal the deterministic cross-model construction."""

    from sc_referee.core.errors import RecordValidationError
    from sc_referee.records.schema_registry import LocalSchemaRegistry

    from .root_cause import RootCauseReconciliationError

    try:
        LocalSchemaRegistry(schema_root).validate(root_cause)
    except RecordValidationError as error:
        raise RootCauseReconciliationError(str(error)) from error
    expected = build_adjudicated_root_cause_cross_model(
        stage1_reviews,
        stage2_reviews,
        schema_root,
        adjudicated_at=str(root_cause["adjudicated_at"]),
        statement_source_review_id=str(root_cause["statement_source_review_ref"]["record_id"]),
        required_scientific_premises=list(root_cause["required_scientific_premises"]),
        stronger_claims_excluded=list(root_cause["stronger_claims_excluded"]),
    )
    if root_cause != expected:
        raise RootCauseReconciliationError(
            "AdjudicatedRootCause does not equal the deterministic reconciliation record."
        )
