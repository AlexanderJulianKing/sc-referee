from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id


class SnapshotEvidenceError(ValueError):
    """Public snapshot records or materialized bytes fail exact identity verification."""


@dataclass(frozen=True)
class SnapshotEvidenceIndex:
    snapshot_id: str
    files_by_path: dict[str, dict[str, Any]]
    identities_by_id: dict[str, dict[str, Any]]


def validate_content_addressed_snapshot(
    snapshot: dict[str, Any],
    file_records: list[dict[str, Any]],
    asset_identities: list[dict[str, Any]],
) -> SnapshotEvidenceIndex:
    """Reconstruct one content-addressed snapshot manifest from public records."""

    if snapshot.get("strategy") != "content_addressed_copy":
        raise SnapshotEvidenceError(
            "Only the content_addressed_copy snapshot profile is independently verifiable."
        )
    if snapshot.get("immutability") is not True:
        raise SnapshotEvidenceError("RepositorySnapshot is not marked immutable.")
    snapshot_id = str(snapshot["snapshot_id"])
    audit_run_id = snapshot.get("audit_run_id")
    files_by_path: dict[str, dict[str, Any]] = {}
    identities_by_id: dict[str, dict[str, Any]] = {}
    for identity_record in asset_identities:
        identity_id = str(identity_record["asset_identity_id"])
        if identity_id in identities_by_id:
            raise SnapshotEvidenceError(f"Duplicate AssetIdentity {identity_id!r}.")
        identities_by_id[identity_id] = identity_record

    linked_identity_ids: set[str] = set()
    digest_manifest: list[dict[str, Any]] = []
    for file_record in sorted(file_records, key=lambda item: str(item["path"])):
        if file_record.get("snapshot_ref") != {
            "record_type": "repository_snapshot",
            "record_id": snapshot_id,
        }:
            raise SnapshotEvidenceError("Every FileRecord must bind the fixture snapshot.")
        path = str(file_record["path"])
        if path in files_by_path:
            raise SnapshotEvidenceError(f"Duplicate FileRecord path {path!r}.")
        files_by_path[path] = file_record
        identity_id = str(file_record.get("asset_identity_ref", {}).get("record_id", ""))
        identity = identities_by_id.get(identity_id)
        if identity is None:
            raise SnapshotEvidenceError(
                f"FileRecord {file_record['file_record_id']!r} has no supplied AssetIdentity."
            )
        linked_identity_ids.add(identity_id)
        evidence = identity["identity_evidence"]
        tier = str(identity["tier"])
        expected_file_id = stable_id("file", path, tier, semantic_digest(evidence))
        expected_identity_id = stable_id(
            "asset-identity",
            str(audit_run_id),
            "file_record",
            expected_file_id,
            tier,
            semantic_digest(evidence),
        )
        if (
            file_record.get("audit_run_id") != audit_run_id
            or file_record.get("file_record_id") != expected_file_id
            or identity.get("audit_run_id") != audit_run_id
            or identity.get("asset_identity_id") != expected_identity_id
            or identity.get("asset_ref")
            != {"record_type": "file_record", "record_id": expected_file_id}
        ):
            raise SnapshotEvidenceError(
                f"Snapshot identity chain is invalid for FileRecord path {path!r}."
            )
        digest_manifest.append(
            {
                "path": path,
                "size_bytes": file_record["byte_size"],
                "role": _snapshot_role(file_record),
                "tier": tier,
                "identity_evidence": evidence,
                "limitations": identity["limitations"],
            }
        )
    if linked_identity_ids != set(identities_by_id):
        raise SnapshotEvidenceError(
            "Supplied AssetIdentities are not exactly the fixture snapshot file identities."
        )
    manifest_digest = semantic_digest(digest_manifest)
    if snapshot.get("snapshot_digest") != manifest_digest or snapshot_id != stable_id(
        "snapshot", manifest_digest
    ):
        raise SnapshotEvidenceError(
            "RepositorySnapshot digest does not match the supplied file identity manifest."
        )
    return SnapshotEvidenceIndex(snapshot_id, files_by_path, identities_by_id)


def read_full_digest_snapshot_file(
    index: SnapshotEvidenceIndex,
    materialized_root: Path,
    path_value: str,
) -> tuple[dict[str, Any], dict[str, Any], bytes, str]:
    """Read one safe materialized file and verify its exact public identity chain."""

    relative = _safe_relative_path(path_value)
    file_record = index.files_by_path.get(relative.as_posix())
    if file_record is None or file_record.get("entry_kind") != "regular_file":
        raise SnapshotEvidenceError(
            f"Path {path_value!r} does not resolve to one regular-file FileRecord."
        )
    identity_id = str(file_record.get("asset_identity_ref", {}).get("record_id", ""))
    identity = index.identities_by_id.get(identity_id)
    if (
        identity is None
        or identity.get("tier") != "full_digest"
        or identity.get("identity_evidence", {}).get("kind") != "full_digest"
    ):
        raise SnapshotEvidenceError(f"Path {path_value!r} lacks an exact full-digest identity.")
    if materialized_root.is_symlink():
        raise SnapshotEvidenceError("Materialized snapshot root must not be a symbolic link.")
    resolved_root = materialized_root.resolve()
    if not resolved_root.is_dir():
        raise SnapshotEvidenceError("Materialized snapshot root must be one directory.")
    target = resolved_root.joinpath(*relative.parts)
    if _path_contains_symlink(resolved_root, relative) or not target.is_file():
        raise SnapshotEvidenceError(f"Path {path_value!r} is absent or crosses a symbolic link.")
    payload = target.read_bytes()
    if len(payload) != file_record["byte_size"]:
        raise SnapshotEvidenceError(f"Path {path_value!r} has byte-size drift.")
    content_digest = sha256_digest(payload)
    if identity["identity_evidence"].get("digest") != content_digest:
        raise SnapshotEvidenceError(f"Path {path_value!r} has snapshot digest drift.")
    return file_record, identity, payload, content_digest


def _snapshot_role(file_record: dict[str, Any]) -> str:
    entry_kind = file_record.get("entry_kind")
    if entry_kind == "symlink":
        return "symlink_not_followed"
    if entry_kind == "special":
        return "unsupported_special_file"
    classification = file_record.get("classification")
    roles = {
        "analysis_source": "analysis_source",
        "report_candidate": "report_candidate",
        "other": "other",
        "unknown": "data_or_result",
    }
    role = roles.get(str(classification))
    if role is None:
        raise SnapshotEvidenceError(
            f"FileRecord classification {classification!r} is outside the snapshot profile."
        )
    return role


def _safe_relative_path(value: str) -> PurePosixPath:
    candidate = PurePosixPath(value)
    if not value or candidate.is_absolute() or ".." in candidate.parts or "." in candidate.parts:
        raise SnapshotEvidenceError(f"Unsafe repository-relative path {value!r}.")
    return candidate


def _path_contains_symlink(root: Path, relative: PurePosixPath) -> bool:
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return True
    return False
