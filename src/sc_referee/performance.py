from __future__ import annotations

from typing import Any

from sc_referee.core.ids import stable_id
from sc_referee.records.observed import controller_provenance
from sc_referee.version import SCHEMA_VERSION


def build_semantic_lock_performance_record(
    *,
    audit_run_id: str,
    recorded_at: str,
    user_visible_elapsed_seconds: float,
    paused_for_scientist_seconds: float,
    snapshot_record: dict[str, Any],
    cache_summary: dict[str, Any] | None = None,
    deadline_ledger_digest: str | None = None,
) -> dict[str, Any]:
    """Project canonical measurements at the semantic-lock boundary without claiming run-final time."""

    identity_reads = snapshot_record.get("extensions", {}).get("x-identity-byte-reads", {})
    source_bytes = int(identity_reads.get("full_digest", 0))
    sampled_large_asset_bytes = int(identity_reads.get("sampled_fingerprint", 0))
    summary = cache_summary or {}
    if summary.get("audit_run_id") != audit_run_id:
        summary = {}
    extensions: dict[str, Any] = {
        "x-measurement-boundary": "semantic_lock",
        "x-postlock-elapsed-included": False,
        "x-io-measurement-scope": "snapshot_identity_reads_only",
        "x-cache-scope": "current_audit_run_parser_cache_only",
        "x-model-usage-scope": "controller_initiated_provider_calls_only",
    }
    if deadline_ledger_digest is not None:
        extensions["x-deadline-ledger-digest"] = deadline_ledger_digest
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "performance_record",
        "performance_record_id": stable_id("performance", audit_run_id, "semantic-lock-boundary"),
        "audit_run_id": audit_run_id,
        "recorded_at": recorded_at,
        "user_visible_elapsed_seconds": max(0.0, user_visible_elapsed_seconds),
        "paused_for_scientist_seconds": max(0.0, paused_for_scientist_seconds),
        "active_cpu_seconds": None,
        "peak_memory_bytes": None,
        "model_usage": {
            "calls": 0,
            "input_tokens": None,
            "output_tokens": None,
            "host_limit_reached": False,
        },
        "io_usage": {
            "source_bytes_read": source_bytes,
            "large_asset_bytes_read": sampled_large_asset_bytes,
            "network_bytes_received": None,
        },
        "cache_usage": {
            "hits": int(summary.get("hits", 0)),
            "misses": int(summary.get("misses", 0)),
            "invalidations": int(summary.get("invalidations", 0)),
        },
        "stage_timings": [
            {
                "stage": "through_semantic_lock",
                "elapsed_seconds": max(0.0, user_visible_elapsed_seconds),
                "state": "complete",
            }
        ],
        "termination": {
            "state": "partial",
            "reason": "other",
            "detail": (
                "Measurement ends at semantic lock so it can replay deterministically; "
                "post-lock elapsed time is excluded and run termination is recorded separately."
            ),
        },
        "provenance": controller_provenance(
            "canonical_semantic_lock_performance_projection", recorded_at
        ),
        "extensions": extensions,
    }
