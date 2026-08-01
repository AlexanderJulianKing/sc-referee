from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from sc_referee.agent_protocol import load_audit_status
from sc_referee.core.ids import semantic_digest

_DIFF_FORMAT = "sc-referee-audit-diff-v1"


def build_audit_diff(before: Path, after: Path, schema_root: Path) -> dict[str, Any]:
    """Compare two integrity-verified audit bundles without treating absence as correctness."""

    before_status = load_audit_status(before, schema_root)
    after_status = load_audit_status(after, schema_root)
    before_bundle = _load_bundle(before)
    after_bundle = _load_bundle(after)
    after_lock = _load_lock(after)
    before_files = _file_identities(before_bundle)
    after_files = _file_identities(after_bundle)
    common = set(before_files) & set(after_files)
    added = sorted(set(after_files) - set(before_files))
    removed = sorted(set(before_files) - set(after_files))
    changed = sorted(path for path in common if before_files[path] != after_files[path])
    unchanged = sorted(path for path in common if before_files[path] == after_files[path])

    cache_summary = after_lock.get("cache_summary", {})
    if not isinstance(cache_summary, dict) or cache_summary.get("audit_run_id") != (
        after_status.audit_run_id
    ):
        cache_summary = {}
    hit_paths = _string_list(cache_summary.get("hit_paths", []))
    miss_paths = _string_list(cache_summary.get("miss_paths", []))
    invalidated_paths = _string_list(cache_summary.get("invalidated_paths", []))
    result: dict[str, Any] = {
        "diff_format": _DIFF_FORMAT,
        "before": {
            "audit_run_id": before_status.audit_run_id,
            "semantic_lock_digest": before_status.semantic_lock_digest,
            "snapshot_digest": _snapshot_digest(before_bundle),
        },
        "after": {
            "audit_run_id": after_status.audit_run_id,
            "semantic_lock_digest": after_status.semantic_lock_digest,
            "snapshot_digest": _snapshot_digest(after_bundle),
        },
        "paths": {
            "added": added,
            "removed": removed,
            "changed": changed,
            "unchanged": unchanged,
        },
        "cache": {
            "hits": len(hit_paths),
            "misses": len(miss_paths),
            "invalidations": len(invalidated_paths),
            "hit_paths": hit_paths,
            "miss_paths": miss_paths,
            "invalidated_paths": invalidated_paths,
            "scope": "after-run project-local parser cache only",
        },
        "assessment_count_delta": {
            key: len(after_bundle.get(field, [])) - len(before_bundle.get(field, []))
            for key, field in (
                ("findings", "findings"),
                ("conditional_concerns", "conditional_concerns"),
                ("material_questions", "material_questions"),
                ("disclosures", "disclosures"),
            )
        },
        "limitations": [
            "This diff reports identity and count changes; it is not a correctness comparison.",
            "Cache reuse is currently limited to exact Python and Markdown parser inputs.",
            "Changed descendants beyond the parser cache are recomputed and are not yet individually cache-addressed.",
        ],
    }
    result["audit_diff_digest"] = semantic_digest(result)
    return result


def verify_audit_diff(diff: dict[str, Any]) -> None:
    candidate = copy.deepcopy(diff)
    digest = candidate.pop("audit_diff_digest", None)
    if candidate.get("diff_format") != _DIFF_FORMAT or semantic_digest(candidate) != digest:
        raise ValueError("audit diff digest mismatch")


def _load_bundle(root: Path) -> dict[str, Any]:
    path = root.resolve() / "audit.bundle.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"audit bundle is not an object: {path}")
    return value


def _load_lock(root: Path) -> dict[str, Any]:
    path = root.resolve() / "semantic.lock.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"semantic lock is not an object: {path}")
    return value


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        return []
    return sorted(set(value))


def _snapshot_digest(bundle: dict[str, Any]) -> str:
    snapshots = bundle.get("repository_snapshots", [])
    if not isinstance(snapshots, list) or len(snapshots) != 1:
        raise ValueError("audit diff requires exactly one repository snapshot per bundle")
    digest = snapshots[0].get("snapshot_digest")
    if not isinstance(digest, str):
        raise ValueError("repository snapshot digest is unavailable")
    return digest


def _file_identities(bundle: dict[str, Any]) -> dict[str, str]:
    identity_by_file_id = {
        str(item.get("asset_ref", {}).get("record_id")): semantic_digest(
            {
                "tier": item.get("tier"),
                "identity_evidence": item.get("identity_evidence"),
                "limitations": item.get("limitations", []),
            }
        )
        for item in bundle.get("asset_identities", [])
        if item.get("asset_ref", {}).get("record_type") == "file_record"
    }
    result: dict[str, str] = {}
    for item in bundle.get("file_records", []):
        path = item.get("path")
        file_id = item.get("file_record_id")
        if not isinstance(file_id, str):
            file_id = item.get("file_id")
        if isinstance(path, str) and isinstance(file_id, str):
            result[path] = identity_by_file_id.get(file_id, semantic_digest(item))
    return result
