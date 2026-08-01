from __future__ import annotations

import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id
from sc_referee.records.normalization import write_normalized_json
from sc_referee.storage.atomic import atomic_write_bytes, fsync_directory
from sc_referee_evaluation.review_protocol import (
    ReviewProtocolError,
    validate_stage1_review_submission,
    validate_stage2_review_submission,
)
from sc_referee_evaluation.stage3 import Stage3ProtocolError, validate_stage3_review_submission


class ReviewCaptureError(ValueError):
    """A review capture is incomplete, mutable, or not bound to its exact packet."""


def capture_review_submission(
    review: dict[str, Any],
    packet: dict[str, Any],
    transcript_source: Path,
    schema_root: Path,
    *,
    captured_at: str,
    destination: Path,
) -> dict[str, Any]:
    """Capture one validated review, packet, and exact transcript in a fresh directory."""

    if destination.exists() or destination.is_symlink():
        raise ReviewCaptureError(f"Review capture destination already exists: {destination}")
    if transcript_source.is_symlink() or not transcript_source.is_file():
        raise ReviewCaptureError("Review transcript must be one non-symlink regular file.")
    transcript = transcript_source.read_bytes()
    transcript_digest = sha256_digest(transcript)
    if review.get("transcript_digest") != transcript_digest:
        raise ReviewCaptureError(
            "AgentReview transcript_digest does not match the supplied transcript bytes."
        )
    _validate_review_packet(review, packet, schema_root)
    if _timestamp(captured_at) < _timestamp(str(review["completed_at"])):
        raise ReviewCaptureError("Review capture cannot precede review completion.")

    packet_digest = str(packet["packet_digest"])
    review_digest = semantic_digest(review)
    review_type, review_id = _review_identity(review)
    capture: dict[str, Any] = {
        "evaluation_protocol_version": "0.2.0",
        "record_type": "evaluation_review_capture",
        "capture_id": stable_id(
            "review-capture",
            review_type,
            review_id,
            packet_digest,
            transcript_digest,
        ),
        "case_id": review["case_id"],
        "stage": review["stage"],
        "review_ref": {
            "record_type": review_type,
            "record_id": review_id,
        },
        "review_digest": review_digest,
        "packet_digest": packet_digest,
        "transcript_digest": transcript_digest,
        "captured_files": {
            "review": "review.json",
            "packet": "packet.json",
            "transcript": "transcript.bin",
        },
        "transcript_byte_size": len(transcript),
        "captured_at": captured_at,
        "model_invoked_by_capture": False,
        "project_code_executed": False,
        "reviewer_independence_verified": False,
        "transcript_authenticity_verified": False,
        "limitations": [
            "Capture proves byte identity and packet consistency, not who produced the transcript.",
            "Declared independent execution context is not cryptographically authenticated.",
        ],
    }
    capture["capture_digest"] = semantic_digest(capture)

    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent))
    try:
        write_normalized_json(staging / "review.json", review)
        write_normalized_json(staging / "packet.json", packet)
        atomic_write_bytes(staging / "transcript.bin", transcript)
        write_normalized_json(staging / "capture.manifest.json", capture)
        os.replace(staging, destination)
        fsync_directory(destination.parent)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return capture


def load_review_capture(
    destination: Path, schema_root: Path
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Verify and load one complete capture directory without trusting loose records."""

    if destination.is_symlink() or not destination.is_dir():
        raise ReviewCaptureError("Review capture must be one non-symlink directory.")
    expected_names = {
        "capture.manifest.json",
        "packet.json",
        "review.json",
        "transcript.bin",
    }
    actual_names = {path.name for path in destination.iterdir()}
    if actual_names != expected_names:
        raise ReviewCaptureError(
            "Review capture contains absent or unexpected files: "
            f"expected {sorted(expected_names)}, observed {sorted(actual_names)}"
        )
    paths = {name: destination / name for name in expected_names}
    if any(path.is_symlink() or not path.is_file() for path in paths.values()):
        raise ReviewCaptureError("Review capture entries must be non-symlink regular files.")
    manifest = _load_object(paths["capture.manifest.json"])
    digest_input = dict(manifest)
    capture_digest = digest_input.pop("capture_digest", None)
    if capture_digest != semantic_digest(digest_input):
        raise ReviewCaptureError("Review capture manifest digest is invalid.")
    if manifest.get("record_type") != "evaluation_review_capture":
        raise ReviewCaptureError("Review capture manifest record kind is invalid.")
    if manifest.get("captured_files") != {
        "review": "review.json",
        "packet": "packet.json",
        "transcript": "transcript.bin",
    }:
        raise ReviewCaptureError("Review capture manifest file map is invalid.")
    review = _load_object(paths["review.json"])
    packet = _load_object(paths["packet.json"])
    transcript = paths["transcript.bin"].read_bytes()
    transcript_digest = sha256_digest(transcript)
    if (
        manifest.get("review_digest") != semantic_digest(review)
        or manifest.get("packet_digest") != packet.get("packet_digest")
        or manifest.get("transcript_digest") != transcript_digest
        or manifest.get("transcript_byte_size") != len(transcript)
        or review.get("transcript_digest") != transcript_digest
        or manifest.get("case_id") != review.get("case_id")
        or manifest.get("stage") != review.get("stage")
        or manifest.get("review_ref")
        != {
            "record_type": _review_identity(review)[0],
            "record_id": _review_identity(review)[1],
        }
    ):
        raise ReviewCaptureError("Review capture content does not match its manifest.")
    _validate_review_packet(review, packet, schema_root)
    if _timestamp(str(manifest["captured_at"])) < _timestamp(str(review["completed_at"])):
        raise ReviewCaptureError("Review capture predates review completion.")
    return review, packet, manifest


def _validate_review_packet(
    review: dict[str, Any], packet: dict[str, Any], schema_root: Path
) -> None:
    packet_kind = packet.get("packet_kind")
    try:
        if packet_kind == "stage1_blind_scientific_review":
            validate_stage1_review_submission(review, packet, schema_root)
        elif packet_kind == "stage2_scientific_adjudication":
            validate_stage2_review_submission(review, packet, schema_root)
        elif packet_kind == "stage3_detector_comparison":
            validate_stage3_review_submission(review, packet, schema_root)
        else:
            raise ReviewCaptureError(f"Unsupported review packet kind {packet_kind!r}.")
    except (ReviewProtocolError, Stage3ProtocolError) as error:
        raise ReviewCaptureError(str(error)) from error


def _review_identity(review: dict[str, Any]) -> tuple[str, str]:
    record_type = review.get("record_type")
    if record_type == "agent_review" and isinstance(review.get("review_id"), str):
        return record_type, str(review["review_id"])
    if record_type == "stage3_comparison_review" and isinstance(
        review.get("comparison_review_id"), str
    ):
        return record_type, str(review["comparison_review_id"])
    raise ReviewCaptureError("Review capture has no supported public review identity.")


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ReviewCaptureError(f"Invalid review-capture timestamp {value!r}.") from error
    if parsed.tzinfo is None:
        raise ReviewCaptureError("Review-capture timestamps must include an offset.")
    return parsed


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as error:
        raise ReviewCaptureError(f"Cannot read review capture object {path.name!r}.") from error
    if not isinstance(value, dict):
        raise ReviewCaptureError(f"Review capture object {path.name!r} is not a JSON object.")
    return value
