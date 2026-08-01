from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

from sc_referee.core.errors import RecordValidationError
from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee.records.root_cause import root_cause_candidate_ref
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee_evaluation.root_cause import (
    RootCauseReconciliationError,
    validate_adjudicated_root_cause,
    validate_review_local_candidate,
)


class ReviewProtocolError(ValueError):
    """A blind-review packet, submission, or freeze violates the evaluation protocol."""


_STAGE1_BLINDNESS = {
    "answer_key_hidden": True,
    "benchmark_grade_hidden": True,
    "detector_identity_hidden": True,
    "other_reviews_hidden": True,
    "sc_referee_output_hidden": True,
}
_STAGE2_BLINDNESS = {
    "answer_key_hidden": False,
    "benchmark_grade_hidden": False,
    "detector_identity_hidden": True,
    "other_reviews_hidden": False,
    "sc_referee_output_hidden": True,
}
_REVIEWER_REQUIRED = {
    "provider",
    "agent_surface",
    "model_name",
    "model_id",
    "agent_version",
    "execution_context_id",
    "independent_context",
    "system_prompt_digest",
    "tool_policy_digest",
    "environment_digest",
}


def build_stage1_review_packet(
    case_id: str,
    workspace_manifest: dict[str, Any],
    reviewer_agent: dict[str, Any],
    prompt_text: str,
    *,
    created_at: str,
) -> dict[str, Any]:
    """Build one normalized, digest-bound packet containing only Stage-1-visible state."""

    if not case_id:
        raise ReviewProtocolError("Stage-1 case_id must be non-empty.")
    _validate_workspace_manifest(workspace_manifest)
    if _timestamp(created_at) < _timestamp(str(workspace_manifest["created_at"])):
        raise ReviewProtocolError("Stage-1 packet creation cannot precede its blind workspace.")
    missing = sorted(_REVIEWER_REQUIRED - set(reviewer_agent))
    if missing or reviewer_agent.get("independent_context") is not True:
        raise ReviewProtocolError(
            f"Stage-1 reviewer configuration is incomplete or not independent: {missing}"
        )
    normalized_prompt = _normalize_prompt(prompt_text)
    expected_reviewer = deepcopy(reviewer_agent)
    expected_reviewer["task_prompt_digest"] = sha256_digest(normalized_prompt)
    packet: dict[str, Any] = {
        "evaluation_protocol_version": "0.2.0",
        "packet_kind": "stage1_blind_scientific_review",
        "case_id": case_id,
        "stage": "stage1_blind",
        "created_at": created_at,
        "workspace": {
            "workspace_id": workspace_manifest["workspace_id"],
            "manifest_digest": workspace_manifest["manifest_digest"],
            "created_at": workspace_manifest["created_at"],
            "source_snapshot_ref": deepcopy(workspace_manifest["source_snapshot_ref"]),
            "source_snapshot_digest": workspace_manifest["source_snapshot_digest"],
            "files": deepcopy(workspace_manifest["files"]),
        },
        "blindness_required": deepcopy(_STAGE1_BLINDNESS),
        "hidden_categories": [
            "answer_key_and_benchmark_grade",
            "answer_side_adjudication_evidence",
            "detector_identity_and_sc_referee_output",
            "other_reviews_and_prior_labels",
        ],
        "prompt": {
            "normalized_text": normalized_prompt,
            "prompt_digest": sha256_digest(normalized_prompt),
        },
        "expected_reviewer_agent": expected_reviewer,
        "required_output": {
            "record_type": "agent_review",
            "stage": "stage1_blind",
            "confidence_used_for_labeling": False,
            "review_local_candidate_identity_required_for_demonstrated_issue": True,
            "cross_review_reconciliation_permitted": False,
            "packet_digest_extension": "x-review-packet-digest",
        },
    }
    packet["packet_digest"] = semantic_digest(packet)
    return packet


def validate_stage1_review_submission(
    review: dict[str, Any], packet: dict[str, Any], schema_root: Path
) -> None:
    """Validate one public AgentReview against the exact packet and reviewer context."""

    _validate_packet_digest(packet)
    try:
        LocalSchemaRegistry(schema_root).validate(review)
    except RecordValidationError as error:
        raise ReviewProtocolError(str(error)) from error
    try:
        validate_review_local_candidate(review)
    except RootCauseReconciliationError as error:
        raise ReviewProtocolError(str(error)) from error
    if review.get("stage") != "stage1_blind" or review.get("case_id") != packet.get("case_id"):
        raise ReviewProtocolError(
            "Stage-1 review stage or case identity does not match its packet."
        )
    blindness = review.get("blindness", {})
    if any(
        blindness.get(key) is not value for key, value in _STAGE1_BLINDNESS.items()
    ) or blindness.get("exceptions"):
        raise ReviewProtocolError("Stage-1 review does not preserve the required blindness state.")
    if review.get("reviewer_agent") != packet.get("expected_reviewer_agent"):
        raise ReviewProtocolError("Stage-1 reviewer configuration drifted from its packet.")
    if _timestamp(str(review["completed_at"])) < _timestamp(str(packet["created_at"])):
        raise ReviewProtocolError("Stage-1 review completion predates packet creation.")
    extension_digest = review.get("extensions", {}).get("x-review-packet-digest")
    if extension_digest != packet.get("packet_digest"):
        raise ReviewProtocolError("Stage-1 review packet digest does not match its submission.")


def build_stage2_review_packet(
    stage1_freeze: dict[str, Any],
    stage1_reviews: list[dict[str, Any]],
    reviewer_agent: dict[str, Any],
    prompt_text: str,
    *,
    created_at: str,
    answer_side_evidence_refs: list[dict[str, str]],
    reference_analysis_refs: list[dict[str, str]],
    execution_comparison_refs: list[dict[str, str]],
) -> dict[str, Any]:
    """Build a Stage-2 packet from frozen Stage-1 records without detector output."""

    _validate_stage1_freeze(stage1_freeze)
    if _timestamp(created_at) < _timestamp(str(stage1_freeze["frozen_at"])):
        raise ReviewProtocolError("Stage-2 packet creation cannot precede the Stage-1 freeze.")
    stage1_projection = _frozen_stage1_projection(stage1_freeze, stage1_reviews)
    missing = sorted(_REVIEWER_REQUIRED - set(reviewer_agent))
    if missing or reviewer_agent.get("independent_context") is not True:
        raise ReviewProtocolError(
            f"Stage-2 reviewer configuration is incomplete or not independent: {missing}"
        )
    normalized_prompt = _normalize_prompt(prompt_text)
    expected_reviewer = deepcopy(reviewer_agent)
    expected_reviewer["task_prompt_digest"] = sha256_digest(normalized_prompt)
    packet: dict[str, Any] = {
        "evaluation_protocol_version": "0.2.0",
        "packet_kind": "stage2_scientific_adjudication",
        "case_id": stage1_freeze["case_id"],
        "stage": "stage2_scientific_adjudication",
        "created_at": created_at,
        "stage1_freeze_digest": stage1_freeze["freeze_digest"],
        "frozen_stage1_reviews": stage1_projection,
        "answer_side_evidence_refs": deepcopy(answer_side_evidence_refs),
        "reference_analysis_refs": deepcopy(reference_analysis_refs),
        "execution_comparison_refs": deepcopy(execution_comparison_refs),
        "blindness_required": deepcopy(_STAGE2_BLINDNESS),
        "prompt": {
            "normalized_text": normalized_prompt,
            "prompt_digest": sha256_digest(normalized_prompt),
        },
        "expected_reviewer_agent": expected_reviewer,
        "required_output": {
            "record_type": "agent_review",
            "stage": "stage2_scientific_adjudication",
            "confidence_used_for_labeling": False,
            "falsification_attempt_required": True,
            "review_local_candidate_identity_required_for_demonstrated_issue": True,
            "exact_stage1_candidate_reconciliation_required_for_demonstrated_issue": True,
            "packet_digest_extension": "x-review-packet-digest",
            "stage1_freeze_extension": "x-stage1-freeze-digest",
        },
    }
    packet["packet_digest"] = semantic_digest(packet)
    return packet


def validate_stage2_review_submission(
    review: dict[str, Any], packet: dict[str, Any], schema_root: Path
) -> None:
    """Validate one fresh Stage-2 adjudication against its frozen inputs."""

    _validate_packet_digest(packet)
    if packet.get("packet_kind") != "stage2_scientific_adjudication":
        raise ReviewProtocolError("Stage-2 submission packet has the wrong kind.")
    try:
        LocalSchemaRegistry(schema_root).validate(review)
    except RecordValidationError as error:
        raise ReviewProtocolError(str(error)) from error
    try:
        validate_review_local_candidate(review)
    except RootCauseReconciliationError as error:
        raise ReviewProtocolError(str(error)) from error
    if review.get("stage") != "stage2_scientific_adjudication" or review.get(
        "case_id"
    ) != packet.get("case_id"):
        raise ReviewProtocolError(
            "Stage-2 review stage or case identity does not match its packet."
        )
    blindness = review.get("blindness", {})
    if any(blindness.get(key) is not value for key, value in _STAGE2_BLINDNESS.items()):
        raise ReviewProtocolError("Stage-2 review does not preserve the required blindness state.")
    if review.get("reviewer_agent") != packet.get("expected_reviewer_agent"):
        raise ReviewProtocolError("Stage-2 reviewer configuration drifted from its packet.")
    if _timestamp(str(review["completed_at"])) < _timestamp(str(packet["created_at"])):
        raise ReviewProtocolError("Stage-2 review completion predates packet creation.")
    extensions = review.get("extensions", {})
    if extensions.get("x-review-packet-digest") != packet.get("packet_digest"):
        raise ReviewProtocolError("Stage-2 review packet digest does not match its submission.")
    if extensions.get("x-stage1-freeze-digest") != packet.get("stage1_freeze_digest"):
        raise ReviewProtocolError("Stage-2 review does not bind the frozen Stage-1 panel.")
    if review.get("verdict") == "demonstrated_issue":
        available = {
            str(item["root_cause_identity"]["candidate_root_cause_id"]): {
                "review_ref": deepcopy(item["review_ref"]),
                "candidate_root_cause_id": item["root_cause_identity"]["candidate_root_cause_id"],
            }
            for item in packet.get("frozen_stage1_reviews", [])
            if isinstance(item.get("root_cause_identity"), dict)
        }
        selected = review["root_cause_identity"]["reconciled_stage1_candidates"]
        for candidate_ref in selected:
            candidate_id = str(candidate_ref["candidate_root_cause_id"])
            if available.get(candidate_id) != candidate_ref:
                raise ReviewProtocolError(
                    "Stage-2 reconciliation cites a candidate outside the frozen Stage-1 panel."
                )


def validate_scientific_review_capture_evidence(
    review: dict[str, Any],
    packet: dict[str, Any],
    capture_manifest: dict[str, Any],
    schema_root: Path,
    *,
    expected_stage: str,
) -> None:
    """Validate one scientific-panel review, packet, and capture projection exactly."""

    if expected_stage == "stage1_blind":
        validate_stage1_review_submission(review, packet, schema_root)
    elif expected_stage == "stage2_scientific_adjudication":
        validate_stage2_review_submission(review, packet, schema_root)
    else:
        raise ReviewProtocolError(f"Unsupported scientific review stage {expected_stage!r}.")
    if review.get("stage") != expected_stage:
        raise ReviewProtocolError("Scientific review capture has the wrong stage.")
    _validate_capture_manifest(capture_manifest, review, packet)


def freeze_stage1_panel(
    reviews: list[dict[str, Any]],
    packets: list[dict[str, Any]],
    capture_manifests: list[dict[str, Any]],
    schema_root: Path,
    *,
    frozen_at: str,
    output: Path,
) -> dict[str, Any]:
    """Freeze a complete 2x2 provider panel before Stage-2 evidence may be exposed."""

    if output.exists() or output.is_symlink():
        raise ReviewProtocolError(f"Stage-1 freeze output already exists: {output}")
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
    case_ids: set[str] = set()
    review_entries: list[dict[str, Any]] = []
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
        case_ids.add(str(review["case_id"]))
        review_entries.append(
            {
                "review_ref": {"record_type": "agent_review", "record_id": review_id},
                "review_digest": semantic_digest(review),
                "packet_digest": packet_digest,
                "capture_id": capture["capture_id"],
                "capture_digest": capture["capture_digest"],
                "transcript_digest": capture["transcript_digest"],
                "captured_at": capture["captured_at"],
                "provider": provider,
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
    if len(providers) != 2 or any(count < 2 for count in providers.values()):
        raise ReviewProtocolError(
            "Stage-1 freeze requires two independent reviews from each of two provider families."
        )
    frozen_time = _timestamp(frozen_at)
    if any(_timestamp(str(capture["captured_at"])) > frozen_time for capture in capture_manifests):
        raise ReviewProtocolError("Stage-1 frozen_at cannot precede a review capture.")

    frozen: dict[str, Any] = {
        "evaluation_protocol_version": "0.2.0",
        "record_type": "evaluation_stage1_freeze",
        "case_id": next(iter(case_ids)),
        "frozen_at": frozen_at,
        "reviews": sorted(review_entries, key=lambda item: str(item["review_ref"]["record_id"])),
        "provider_participation": dict(sorted(providers.items())),
        "detector_output_observed": False,
        "answer_side_evidence_observed": False,
    }
    frozen["freeze_digest"] = semantic_digest(frozen)
    write_normalized_json_once(output, frozen)
    return frozen


def validate_stage1_freeze_evidence(
    frozen: dict[str, Any],
    reviews: list[dict[str, Any]],
    packets: list[dict[str, Any]],
    capture_manifests: list[dict[str, Any]],
    schema_root: Path,
) -> None:
    """Re-resolve one Stage-1 freeze against its exact packets and captures."""

    _validate_stage1_freeze(frozen)
    packets_by_digest: dict[str, dict[str, Any]] = {}
    for packet in packets:
        _validate_packet_digest(packet)
        packet_digest = str(packet["packet_digest"])
        if packet_digest in packets_by_digest:
            raise ReviewProtocolError("Stage-1 freeze replay has duplicate packet digests.")
        packets_by_digest[packet_digest] = packet
    captures_by_review = _capture_index(capture_manifests, "stage1_blind")
    entries: list[dict[str, Any]] = []
    providers: Counter[str] = Counter()
    review_ids: set[str] = set()
    case_ids: set[str] = set()
    contexts: set[str] = set()
    for review in reviews:
        review_id = str(review["review_id"])
        packet_digest = str(review.get("extensions", {}).get("x-review-packet-digest", ""))
        matched_packet = packets_by_digest.get(packet_digest)
        capture = captures_by_review.get(review_id)
        if matched_packet is None or capture is None:
            raise ReviewProtocolError("Stage-1 freeze replay has an unresolved packet or capture.")
        validate_stage1_review_submission(review, matched_packet, schema_root)
        _validate_capture_manifest(capture, review, matched_packet)
        context = str(review["reviewer_agent"]["execution_context_id"])
        if review_id in review_ids or context in contexts:
            raise ReviewProtocolError("Stage-1 freeze replay has duplicate identity or context.")
        review_ids.add(review_id)
        contexts.add(context)
        provider = str(review["reviewer_agent"]["provider"])
        providers[provider] += 1
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
                "execution_context_id": context,
                "completed_at": review["completed_at"],
            }
        )
    if (
        set(packets_by_digest)
        != {
            str(review.get("extensions", {}).get("x-review-packet-digest", ""))
            for review in reviews
        }
        or set(captures_by_review) != review_ids
        or len(case_ids) != 1
        or len(providers) != 2
        or any(count < 2 for count in providers.values())
    ):
        raise ReviewProtocolError("Stage-1 freeze replay does not contain one complete 2x2 panel.")
    if any(
        _timestamp(str(capture["captured_at"])) > _timestamp(str(frozen["frozen_at"]))
        for capture in capture_manifests
    ):
        raise ReviewProtocolError("Stage-1 freeze replay predates a capture.")
    if (
        frozen.get("case_id") != next(iter(case_ids))
        or frozen.get("provider_participation") != dict(sorted(providers.items()))
        or frozen.get("reviews")
        != sorted(entries, key=lambda item: str(item["review_ref"]["record_id"]))
    ):
        raise ReviewProtocolError(
            "Stage-1 freeze projection has drifted from exact capture inputs."
        )


def freeze_scientific_label(
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
    expected_freeze: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Freeze the scientific adjudication before any Stage-3 detector comparison."""

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

    try:
        LocalSchemaRegistry(schema_root).validate(adjudication)
    except RecordValidationError as error:
        raise ReviewProtocolError(str(error)) from error
    if adjudication.get("case_id") != stage1_freeze.get("case_id"):
        raise ReviewProtocolError("BenchmarkAdjudication case does not match the frozen panel.")
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
        raise ReviewProtocolError(
            "BenchmarkAdjudication review refs do not match the frozen panels."
        )
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
            "BenchmarkAdjudication root-cause refs do not match the supplied canonical records."
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
            validate_adjudicated_root_cause(roots[0], stage1_reviews, stage2_reviews, schema_root)
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
        "case_id": adjudication["case_id"],
        "stage1_freeze_digest": stage1_freeze["freeze_digest"],
        "stage2_reviews": sorted(
            stage2_entries, key=lambda item: str(item["review_ref"]["record_id"])
        ),
        "adjudication_ref": {
            "record_type": "benchmark_adjudication",
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
    if expected_freeze is not None and frozen != expected_freeze:
        raise ReviewProtocolError(
            "Model-free scientific-label replay does not equal the source freeze."
        )
    write_normalized_json_once(output, frozen)
    return frozen


def _validate_stage1_freeze(frozen: dict[str, Any]) -> None:
    expected = frozen.get("freeze_digest")
    digest_input = dict(frozen)
    digest_input.pop("freeze_digest", None)
    if expected != semantic_digest(digest_input):
        raise ReviewProtocolError("Stage-1 freeze digest is invalid.")
    if frozen.get("record_type") != "evaluation_stage1_freeze":
        raise ReviewProtocolError("Stage-1 freeze record kind is invalid.")
    if (
        frozen.get("detector_output_observed") is not False
        or frozen.get("answer_side_evidence_observed") is not False
    ):
        raise ReviewProtocolError("Stage-1 freeze contains evidence hidden from blind review.")


def _frozen_stage1_projection(
    frozen: dict[str, Any], reviews: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    reviews_by_id = {str(review["review_id"]): review for review in reviews}
    if len(reviews_by_id) != len(reviews):
        raise ReviewProtocolError("Stage-1 review identities are not unique.")
    projections: list[dict[str, Any]] = []
    for entry in frozen["reviews"]:
        review_id = str(entry["review_ref"]["record_id"])
        review = reviews_by_id.get(review_id)
        if review is None or semantic_digest(review) != entry.get("review_digest"):
            raise ReviewProtocolError(f"Frozen Stage-1 review {review_id!r} is absent or changed.")
        projections.append(
            {
                "review_ref": deepcopy(entry["review_ref"]),
                "review_digest": entry["review_digest"],
                "provider": entry["provider"],
                "case_id": review["case_id"],
                "verdict": review["verdict"],
                "bounded_statement": review.get("bounded_statement"),
                "root_cause": review.get("root_cause"),
                "root_cause_identity": deepcopy(review.get("root_cause_identity")),
                "issue_class": review.get("issue_class"),
                "scope": deepcopy(review["scope"]),
                "evidence": deepcopy(review.get("evidence", [])),
                "counterevidence_considered": deepcopy(
                    review.get("counterevidence_considered", [])
                ),
                "unresolved_material_questions": deepcopy(
                    review.get("unresolved_material_questions", [])
                ),
            }
        )
    if set(reviews_by_id) != {str(entry["review_ref"]["record_id"]) for entry in frozen["reviews"]}:
        raise ReviewProtocolError("Stage-2 packet received reviews outside the Stage-1 freeze.")
    return sorted(projections, key=lambda item: str(item["review_ref"]["record_id"]))


def _validate_stage1_reviews_against_freeze(
    reviews: list[dict[str, Any]], frozen: dict[str, Any]
) -> None:
    reviews_by_id = {str(review["review_id"]): review for review in reviews}
    if len(reviews_by_id) != len(reviews):
        raise ReviewProtocolError("Stage-1 review identities are not unique.")
    expected_ids: set[str] = set()
    for entry in frozen["reviews"]:
        review_id = str(entry["review_ref"]["record_id"])
        expected_ids.add(review_id)
        review = reviews_by_id.get(review_id)
        if review is None or semantic_digest(review) != entry["review_digest"]:
            raise ReviewProtocolError(f"Frozen Stage-1 review {review_id!r} is absent or changed.")
        if (
            root_cause_candidate_ref(review)["candidate_root_cause_id"]
            != review["root_cause_identity"]["candidate_root_cause_id"]
        ):
            raise ReviewProtocolError(
                f"Frozen Stage-1 review {review_id!r} has an invalid candidate identity."
            )
    if set(reviews_by_id) != expected_ids:
        raise ReviewProtocolError("Supplied Stage-1 reviews do not equal the frozen panel.")


def _validate_adjudication_participation(
    adjudication: dict[str, Any],
    stage1_freeze: dict[str, Any],
    stage2_providers: Counter[str],
) -> None:
    stage1_counts = {
        str(provider): int(count)
        for provider, count in stage1_freeze["provider_participation"].items()
    }
    expected_providers = set(stage1_counts)
    if set(str(value) for value in adjudication["provider_families"]) != expected_providers:
        raise ReviewProtocolError("Adjudication provider families do not match the frozen panels.")
    declared = {
        str(item["provider_family"]): item for item in adjudication["provider_participation"]
    }
    if set(declared) != expected_providers:
        raise ReviewProtocolError("Adjudication participation rows do not match the frozen panels.")
    for provider in expected_providers:
        row = declared[provider]
        stage1_count = stage1_counts[provider]
        stage2_count = stage2_providers[provider]
        if (
            row["stage1_review_count"] != stage1_count
            or row["stage2_review_count"] != stage2_count
            or row["distinct_execution_context_count"] != stage1_count + stage2_count
        ):
            raise ReviewProtocolError(
                f"Adjudication provider participation does not reconcile for {provider!r}."
            )


def _validate_workspace_manifest(manifest: dict[str, Any]) -> None:
    expected = manifest.get("manifest_digest")
    digest_input = dict(manifest)
    digest_input.pop("manifest_digest", None)
    if expected != semantic_digest(digest_input):
        raise ReviewProtocolError("Blind-workspace manifest digest is invalid.")
    if manifest.get("record_type") != "evaluation_blind_workspace_manifest":
        raise ReviewProtocolError("Blind-workspace manifest record kind is invalid.")
    if manifest.get("source_snapshot_ref", {}).get("record_type") != "repository_snapshot":
        raise ReviewProtocolError("Blind workspace has no exact source-snapshot reference.")
    if not isinstance(manifest.get("source_snapshot_digest"), str):
        raise ReviewProtocolError("Blind workspace has no exact source-snapshot digest.")
    _timestamp(str(manifest.get("created_at", "")))
    if manifest.get("answer_side_content_copied") is not False:
        raise ReviewProtocolError("Blind workspace does not deny copied answer-side content.")
    if manifest.get("project_code_executed") is not False:
        raise ReviewProtocolError("Blind workspace does not deny project code execution.")


def _validate_packet_digest(packet: dict[str, Any]) -> None:
    digest = packet.get("packet_digest")
    digest_input = dict(packet)
    digest_input.pop("packet_digest", None)
    if digest != semantic_digest(digest_input):
        raise ReviewProtocolError("Review packet digest is invalid.")
    _timestamp(str(packet.get("created_at", "")))


def _capture_index(
    manifests: list[dict[str, Any]], expected_stage: str
) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    capture_ids: set[str] = set()
    for manifest in manifests:
        if manifest.get("record_type") != "evaluation_review_capture":
            raise ReviewProtocolError("Review capture manifest record kind is invalid.")
        if manifest.get("stage") != expected_stage:
            raise ReviewProtocolError("Review capture stage does not match the requested freeze.")
        review_ref = manifest.get("review_ref", {})
        if review_ref.get("record_type") != "agent_review":
            raise ReviewProtocolError("Scientific-panel capture does not reference an AgentReview.")
        review_id = str(review_ref.get("record_id", ""))
        capture_id = str(manifest.get("capture_id", ""))
        if not review_id or review_id in index:
            raise ReviewProtocolError("Review capture manifests have duplicate review identities.")
        if not capture_id or capture_id in capture_ids:
            raise ReviewProtocolError("Review capture manifests have duplicate capture identities.")
        index[review_id] = manifest
        capture_ids.add(capture_id)
    return index


def _validate_capture_manifest(
    manifest: dict[str, Any], review: dict[str, Any], packet: dict[str, Any]
) -> None:
    digest_input = dict(manifest)
    capture_digest = digest_input.pop("capture_digest", None)
    if capture_digest != semantic_digest(digest_input):
        raise ReviewProtocolError("Review capture manifest digest is invalid.")
    review_ref = {"record_type": "agent_review", "record_id": review["review_id"]}
    if (
        manifest.get("review_ref") != review_ref
        or manifest.get("review_digest") != semantic_digest(review)
        or manifest.get("packet_digest") != packet.get("packet_digest")
        or manifest.get("case_id") != review.get("case_id")
        or manifest.get("stage") != review.get("stage")
        or manifest.get("transcript_digest") != review.get("transcript_digest")
    ):
        raise ReviewProtocolError("Review capture does not bind its exact review and packet.")
    if _timestamp(str(manifest["captured_at"])) < _timestamp(str(review["completed_at"])):
        raise ReviewProtocolError("Review capture predates review completion.")


def _normalize_prompt(value: str) -> str:
    normalized = "\n".join(line.rstrip() for line in value.replace("\r\n", "\n").split("\n"))
    normalized = normalized.strip()
    if not normalized:
        raise ReviewProtocolError("Stage-1 prompt must be non-empty.")
    return normalized


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ReviewProtocolError(f"Invalid review protocol timestamp {value!r}.") from error
    if parsed.tzinfo is None:
        raise ReviewProtocolError("Review protocol timestamps must include an offset.")
    return parsed
