from __future__ import annotations

import copy
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from sc_referee.core.ids import semantic_digest
from sc_referee.records.normalization import normalized_json_bytes, write_normalized_json

LedgerState = Literal[
    "active",
    "awaiting_scientist_response",
    "complete",
    "hard_deadline_exhausted",
]

LEDGER_FILENAME = "deadline-ledger.json"
_LEDGER_VERSION = "1.0.0"


class DeadlineLedgerError(ValueError):
    """Raised when durable deadline history is invalid or the current segment expires."""


def start_linked_segment(
    *,
    parent_ledger: dict[str, Any] | None,
    audit_run_id: str,
    parent_audit_run_id: str,
    mode: str,
    scheduling_cutoff_seconds: float,
    hard_seconds: float,
    started_at: str,
) -> dict[str, Any]:
    if scheduling_cutoff_seconds <= 0 or hard_seconds <= 0:
        raise DeadlineLedgerError("deadline limits must be positive")
    if scheduling_cutoff_seconds > hard_seconds:
        raise DeadlineLedgerError("scheduling cutoff cannot exceed the hard deadline")
    _parse_timestamp(started_at)
    segments: list[dict[str, Any]] = []
    if parent_ledger is not None:
        verify_deadline_ledger(parent_ledger)
        segments = copy.deepcopy(parent_ledger["segments"])
        if segments and segments[-1].get("state") not in {
            "complete",
            "hard_deadline_exhausted",
        }:
            raise DeadlineLedgerError("parent deadline segment is not terminal")
    segments.append(
        {
            "audit_run_id": audit_run_id,
            "parent_audit_run_id": parent_audit_run_id,
            "mode": mode,
            "scheduling_cutoff_seconds": float(scheduling_cutoff_seconds),
            "hard_seconds": float(hard_seconds),
            "started_at": started_at,
            "last_accounted_at": started_at,
            "state": "active",
            "user_visible_elapsed_seconds": 0.0,
            "paused_for_scientist_seconds": 0.0,
            "events": [
                {
                    "event": "segment_started",
                    "at": started_at,
                    "state": "active",
                    "user_visible_elapsed_seconds": 0.0,
                    "paused_for_scientist_seconds": 0.0,
                }
            ],
        }
    )
    return _with_digest({"ledger_version": _LEDGER_VERSION, "segments": segments})


def checkpoint_active(ledger: dict[str, Any], *, at: str, event: str) -> dict[str, Any]:
    return _advance(ledger, at=at, event=event, required_state="active")


def pause_for_scientist(
    ledger: dict[str, Any], *, at: str, event: str = "scientist_wait_started"
) -> dict[str, Any]:
    updated = _advance(ledger, at=at, event=event, required_state="active")
    segment = updated["segments"][-1]
    segment["state"] = "awaiting_scientist_response"
    segment["events"][-1]["state"] = "awaiting_scientist_response"
    return _refresh_digest(updated)


def resume_after_scientist(
    ledger: dict[str, Any], *, at: str, event: str = "scientist_answer_recorded"
) -> dict[str, Any]:
    updated = _advance(
        ledger,
        at=at,
        event=event,
        required_state="awaiting_scientist_response",
    )
    segment = updated["segments"][-1]
    segment["state"] = "active"
    segment["events"][-1]["state"] = "active"
    return _refresh_digest(updated)


def complete_segment(
    ledger: dict[str, Any], *, at: str, event: str = "segment_completed"
) -> dict[str, Any]:
    updated = _advance(ledger, at=at, event=event, required_state="active")
    segment = updated["segments"][-1]
    segment["state"] = "complete"
    segment["events"][-1]["state"] = "complete"
    return _refresh_digest(updated)


def current_segment(ledger: dict[str, Any]) -> dict[str, Any]:
    verify_deadline_ledger(ledger)
    return copy.deepcopy(ledger["segments"][-1])


def write_deadline_ledger(path: Path, ledger: dict[str, Any]) -> None:
    verify_deadline_ledger(ledger)
    write_normalized_json(path, ledger)


def load_deadline_ledger(path: Path, *, required: bool = True) -> dict[str, Any] | None:
    if not path.is_file() or path.is_symlink():
        if required:
            raise DeadlineLedgerError(f"deadline ledger is unavailable or unsafe: {path}")
        return None
    try:
        payload = path.read_bytes()
        value = json.loads(payload)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DeadlineLedgerError("deadline ledger could not be decoded") from error
    if not isinstance(value, dict) or normalized_json_bytes(value) != payload:
        raise DeadlineLedgerError("deadline ledger is not canonical JSON")
    verify_deadline_ledger(value)
    return value


def verify_deadline_ledger(ledger: dict[str, Any]) -> None:
    candidate = copy.deepcopy(ledger)
    digest = candidate.pop("ledger_digest", None)
    if candidate.get("ledger_version") != _LEDGER_VERSION:
        raise DeadlineLedgerError("unsupported deadline ledger version")
    segments = candidate.get("segments")
    if not isinstance(segments, list) or not segments:
        raise DeadlineLedgerError("deadline ledger has no run segments")
    if semantic_digest(candidate) != digest:
        raise DeadlineLedgerError("deadline ledger digest mismatch")
    prior_ids: set[str] = set()
    for segment in segments:
        if not isinstance(segment, dict):
            raise DeadlineLedgerError("deadline ledger segment is malformed")
        run_id = segment.get("audit_run_id")
        parent_id = segment.get("parent_audit_run_id")
        if not isinstance(run_id, str) or not isinstance(parent_id, str):
            raise DeadlineLedgerError("deadline ledger segment linkage is malformed")
        if run_id in prior_ids:
            raise DeadlineLedgerError("deadline ledger repeats a run segment")
        if prior_ids and parent_id not in prior_ids:
            raise DeadlineLedgerError("deadline ledger segment does not link to prior history")
        prior_ids.add(run_id)
        _validate_segment(segment)


def _advance(
    ledger: dict[str, Any], *, at: str, event: str, required_state: LedgerState
) -> dict[str, Any]:
    verify_deadline_ledger(ledger)
    if not event:
        raise DeadlineLedgerError("deadline event must be named")
    updated = copy.deepcopy(ledger)
    updated.pop("ledger_digest", None)
    segment = updated["segments"][-1]
    if segment["state"] != required_state:
        raise DeadlineLedgerError(
            f"deadline event requires {required_state}, not {segment['state']}"
        )
    last = _parse_timestamp(str(segment["last_accounted_at"]))
    current = _parse_timestamp(at)
    delta = (current - last).total_seconds()
    if delta < 0:
        raise DeadlineLedgerError("deadline timestamps must be nondecreasing")
    if required_state == "awaiting_scientist_response":
        segment["paused_for_scientist_seconds"] = _seconds(
            float(segment["paused_for_scientist_seconds"]) + delta
        )
    else:
        segment["user_visible_elapsed_seconds"] = _seconds(
            float(segment["user_visible_elapsed_seconds"]) + delta
        )
    segment["last_accounted_at"] = at
    elapsed = float(segment["user_visible_elapsed_seconds"])
    if elapsed >= float(segment["hard_seconds"]):
        segment["state"] = "hard_deadline_exhausted"
    segment["events"].append(
        {
            "event": event,
            "at": at,
            "state": segment["state"],
            "user_visible_elapsed_seconds": elapsed,
            "paused_for_scientist_seconds": float(segment["paused_for_scientist_seconds"]),
        }
    )
    result = _with_digest(updated)
    if segment["state"] == "hard_deadline_exhausted":
        raise _ExhaustedDeadlineLedger(result)
    return result


class _ExhaustedDeadlineLedger(DeadlineLedgerError):
    def __init__(self, ledger: dict[str, Any]) -> None:
        super().__init__("user-visible hard deadline exhausted")
        self.ledger = ledger


def advance_or_exhaust(
    ledger: dict[str, Any], *, at: str, event: str
) -> tuple[dict[str, Any], bool]:
    """Advance active time and return durable exhausted state instead of losing it."""

    try:
        return checkpoint_active(ledger, at=at, event=event), False
    except _ExhaustedDeadlineLedger as error:
        return error.ledger, True


def _validate_segment(segment: dict[str, Any]) -> None:
    state = segment.get("state")
    if state not in {
        "active",
        "awaiting_scientist_response",
        "complete",
        "hard_deadline_exhausted",
    }:
        raise DeadlineLedgerError("deadline ledger segment state is invalid")
    cutoff = segment.get("scheduling_cutoff_seconds")
    hard = segment.get("hard_seconds")
    elapsed = segment.get("user_visible_elapsed_seconds")
    paused = segment.get("paused_for_scientist_seconds")
    if (
        not isinstance(cutoff, (int, float))
        or not isinstance(hard, (int, float))
        or not isinstance(elapsed, (int, float))
        or not isinstance(paused, (int, float))
    ):
        raise DeadlineLedgerError("deadline ledger durations are malformed")
    cutoff_value = float(cutoff)
    hard_value = float(hard)
    elapsed_value = float(elapsed)
    paused_value = float(paused)
    if (
        cutoff_value <= 0
        or hard_value <= 0
        or cutoff_value > hard_value
        or elapsed_value < 0
        or paused_value < 0
    ):
        raise DeadlineLedgerError("deadline ledger durations are invalid")
    started = _parse_timestamp(str(segment.get("started_at")))
    last = _parse_timestamp(str(segment.get("last_accounted_at")))
    if last < started:
        raise DeadlineLedgerError("deadline ledger last timestamp predates its segment")
    events = segment.get("events")
    if not isinstance(events, list) or not events:
        raise DeadlineLedgerError("deadline ledger segment has no events")


def _parse_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise DeadlineLedgerError(f"invalid deadline timestamp: {value!r}") from error
    if parsed.tzinfo is None:
        raise DeadlineLedgerError("deadline timestamp must include a timezone")
    return parsed.astimezone(UTC)


def _seconds(value: float) -> float:
    return round(value, 6)


def _with_digest(value: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result.pop("ledger_digest", None)
    result["ledger_digest"] = semantic_digest(result)
    return result


def _refresh_digest(value: dict[str, Any]) -> dict[str, Any]:
    value.pop("ledger_digest", None)
    value["ledger_digest"] = semantic_digest(value)
    return value
