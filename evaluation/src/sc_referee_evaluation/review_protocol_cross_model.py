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
