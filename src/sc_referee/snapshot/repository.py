from __future__ import annotations

import os
import stat as stat_module
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id
from sc_referee.snapshot.checksum_manifest import (
    CHECKSUM_MANIFEST_PROFILE,
    inspect_checksum_manifests,
    is_root_checksum_manifest,
)
from sc_referee.snapshot.identity import (
    AssetIdentityEvidence,
    build_asset_identity,
    full_digest_evidence,
    manifest_evidence,
    unidentified_evidence,
    weak_fingerprint_evidence,
)
from sc_referee.storage.atomic import atomic_write_bytes
from sc_referee.version import SCHEMA_VERSION, __version__

_EXCLUDED_DIRS = {
    ".git",
    ".sc-referee",
    ".scientific-audit",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}
_SAMPLE_PROFILE_PREFIX = "sc-referee-sparse-v1:sha256:framed-head-middle-tail"
MAX_MATERIAL_FULL_DIGEST_PATHS = 8


@dataclass(frozen=True)
class AssetIdentityPolicy:
    """Bound complete and sampled reads independently under the tiered identity policy."""

    full_digest_byte_budget: int = 5_000_000
    sampled_fingerprint_byte_budget: int = 1_000_000
    material_full_digest_byte_budget: int = 16 * 1024 * 1024
    sample_chunk_bytes: int = 4096

    def __post_init__(self) -> None:
        if (
            self.full_digest_byte_budget < 0
            or self.sampled_fingerprint_byte_budget < 0
            or self.material_full_digest_byte_budget < 0
        ):
            raise ValueError("asset identity byte budgets must be nonnegative")
        if self.sample_chunk_bytes <= 0:
            raise ValueError("sample chunk size must be positive")

    @property
    def sampled_fingerprint_profile(self) -> str:
        return f"{_SAMPLE_PROFILE_PREFIX}:chunk-{self.sample_chunk_bytes}"


@dataclass(frozen=True)
class SnapshotOutput:
    snapshot_record: dict[str, Any]
    file_records: list[dict[str, Any]]
    asset_identity_records: list[dict[str, Any]]
    materialized_root: Path
    identity_policy: AssetIdentityPolicy


@dataclass(frozen=True)
class _InventoryEntry:
    path: Path
    relative: str
    stat: os.stat_result
    kind: str


def capture_repository(
    source: Path,
    destination: Path,
    run_id: str,
    captured_at: str | None = None,
    *,
    identity_policy: AssetIdentityPolicy | None = None,
    preferred_full_digest_paths: tuple[str, ...] = (),
    material_full_digest_paths: tuple[str, ...] = (),
) -> SnapshotOutput:
    source = source.resolve()
    if not source.is_dir():
        raise ValueError(f"repository source is not a directory: {source}")
    resolved_destination = destination.resolve(strict=False)
    try:
        destination_relative = resolved_destination.relative_to(source)
    except ValueError:
        pass
    else:
        if not destination_relative.parts or not any(
            part in _EXCLUDED_DIRS for part in destination_relative.parts
        ):
            raise ValueError(
                "an in-repository snapshot destination must be inside an excluded audit directory"
            )
    policy = identity_policy or AssetIdentityPolicy()
    preferred_paths = _normalize_preferred_paths(preferred_full_digest_paths)
    material_paths = _normalize_material_paths(material_full_digest_paths)
    materialized = resolved_destination / "materialized"
    if materialized.exists() or materialized.is_symlink():
        raise ValueError(f"snapshot materialization target already exists: {materialized}")
    materialized.mkdir(parents=True)
    timestamp = captured_at or _timestamp_now()

    entries = _inventory_entries(source)
    identities_by_path: dict[str, AssetIdentityEvidence] = {}
    symlink_targets_by_path: dict[str, str] = {}
    payloads_by_path: dict[str, bytes] = {}
    full_digest_bytes_read = 0
    material_full_digest_bytes_read = 0
    sampled_fingerprint_bytes_read = 0

    regular_entries = [entry for entry in entries if entry.kind == "file"]
    regular_paths = {entry.relative for entry in regular_entries}
    unavailable_material_paths = sorted(material_paths - regular_paths)
    if unavailable_material_paths:
        raise ValueError(
            "material input paths must identify regular files: "
            + ", ".join(unavailable_material_paths)
        )
    regular_entries.sort(
        key=lambda entry: (
            entry.relative not in material_paths,
            entry.relative not in preferred_paths,
            _read_priority(entry.path, entry.relative),
            entry.relative,
        )
    )
    for entry in regular_entries:
        if entry.relative in material_paths:
            remaining_material_bytes = (
                policy.material_full_digest_byte_budget - material_full_digest_bytes_read
            )
            if entry.stat.st_size <= remaining_material_bytes:
                try:
                    payload = _read_stable_full_file(entry.path, entry.stat)
                except OSError:
                    identities_by_path[entry.relative] = unidentified_evidence(
                        "The selected material input could not be read safely during snapshot capture.",
                        reported_location=entry.relative,
                        limitations=("No content identity was established for this file.",),
                    )
                else:
                    material_full_digest_bytes_read += len(payload)
                    payloads_by_path[entry.relative] = payload
                    identities_by_path[entry.relative] = full_digest_evidence(
                        sha256_digest(payload)
                    )
                continue
        if entry.stat.st_size <= (policy.full_digest_byte_budget - full_digest_bytes_read):
            try:
                payload = _read_stable_full_file(entry.path, entry.stat)
            except OSError:
                identities_by_path[entry.relative] = unidentified_evidence(
                    "The file could not be read safely during snapshot capture.",
                    reported_location=entry.relative,
                    limitations=("No content identity was established for this file.",),
                )
            else:
                full_digest_bytes_read += len(payload)
                payloads_by_path[entry.relative] = payload
                identities_by_path[entry.relative] = full_digest_evidence(sha256_digest(payload))
            continue

        sample_budget = policy.sampled_fingerprint_byte_budget - (sampled_fingerprint_bytes_read)
        if sample_budget <= 0:
            identities_by_path[entry.relative] = unidentified_evidence(
                "The sampled-fingerprint byte budget was exhausted.",
                reported_location=entry.relative,
                limitations=("No content identity was established for this file.",),
            )
            continue
        try:
            fingerprint, bytes_read = _read_stable_sample(
                entry.path,
                entry.stat,
                max_bytes=sample_budget,
                chunk_bytes=policy.sample_chunk_bytes,
            )
        except OSError:
            identities_by_path[entry.relative] = unidentified_evidence(
                "The file could not be sampled safely during snapshot capture.",
                reported_location=entry.relative,
                limitations=("No content identity was established for this file.",),
            )
        else:
            sampled_fingerprint_bytes_read += bytes_read
            identities_by_path[entry.relative] = weak_fingerprint_evidence(
                entry.relative,
                entry.stat.st_size,
                fingerprint,
                modified_at=_timestamp_from_ns(entry.stat.st_mtime_ns),
                limitations=(
                    "The complete file body was not read; exact content identity is unavailable.",
                ),
                profile=policy.sampled_fingerprint_profile,
            )

    manifest_candidates = sorted(
        entry.relative for entry in regular_entries if is_root_checksum_manifest(entry.relative)
    )
    manifest_inspection = inspect_checksum_manifests(manifest_candidates, payloads_by_path)
    regular_by_path = {entry.relative: entry for entry in regular_entries}
    manifest_upgraded_targets: list[str] = []
    for target_path, declaration in sorted(manifest_inspection.declarations.items()):
        target_entry = regular_by_path.get(target_path)
        existing_identity = identities_by_path.get(target_path)
        if (
            target_entry is None
            or existing_identity is None
            or existing_identity.tier == "full_digest"
        ):
            continue
        identities_by_path[target_path] = manifest_evidence(
            declaration.source_ref,
            declaration.target_digest,
            limitations=(
                "The target file body was not fully read; this identity records a "
                "repository-supplied checksum declaration and does not verify the target bytes.",
            ),
            extensions={
                "x-checksum-manifest-profile": CHECKSUM_MANIFEST_PROFILE,
                "x-observed-file-state": {
                    "path": target_path,
                    "size_bytes": target_entry.stat.st_size,
                    "modified_at_ns": target_entry.stat.st_mtime_ns,
                },
            },
        )
        manifest_upgraded_targets.append(target_path)

    for entry in entries:
        if entry.kind == "symlink":
            try:
                target = os.readlink(entry.path)
            except OSError:
                identities_by_path[entry.relative] = unidentified_evidence(
                    "The symbolic-link target could not be read.",
                    reported_location=entry.relative,
                    limitations=("The symbolic link was not followed.",),
                )
            else:
                symlink_targets_by_path[entry.relative] = target
                identities_by_path[entry.relative] = weak_fingerprint_evidence(
                    entry.relative,
                    entry.stat.st_size,
                    sha256_digest(target.encode("utf-8", errors="surrogateescape")),
                    modified_at=_timestamp_from_ns(entry.stat.st_mtime_ns),
                    limitations=(
                        "The fingerprint identifies only the link target text; target content "
                        "was not read.",
                    ),
                    profile="sc-referee-symlink-target-v1:sha256",
                )
        elif entry.kind == "special":
            identities_by_path[entry.relative] = unidentified_evidence(
                "The path is an unsupported filesystem object and was not read.",
                reported_location=entry.relative,
                limitations=("No content identity was established for this path.",),
            )

    file_records: list[dict[str, Any]] = []
    asset_identity_records: list[dict[str, Any]] = []
    digest_manifest: list[dict[str, Any]] = []
    for entry in sorted(entries, key=lambda item: item.relative):
        evidence = identities_by_path[entry.relative]
        digest = (
            str(evidence.identity_evidence["digest"]) if evidence.tier == "full_digest" else None
        )
        file_id = stable_id(
            "file",
            entry.relative,
            evidence.tier,
            semantic_digest(evidence.identity_evidence),
        )
        record = {
            "record_type": "file_record",
            "file_id": file_id,
            "run_id": run_id,
            "path": entry.relative,
            "entry_kind": "regular_file" if entry.kind == "file" else entry.kind,
            "size_bytes": entry.stat.st_size,
            "language": _language_for(entry.path),
            "role": _role_for(entry.path, entry.kind),
            "digest": digest,
        }
        if entry.relative in symlink_targets_by_path:
            record["symlink_target"] = symlink_targets_by_path[entry.relative]
        identity_record = build_asset_identity(
            audit_run_id=run_id,
            asset_record_type="file_record",
            asset_record_id=file_id,
            evidence=evidence,
            created_at=timestamp,
        )
        file_records.append(record)
        asset_identity_records.append(identity_record)
        digest_manifest.append(
            {
                "path": entry.relative,
                "size_bytes": entry.stat.st_size,
                "role": record["role"],
                "tier": evidence.tier,
                "identity_evidence": evidence.identity_evidence,
                "limitations": list(evidence.limitations),
            }
        )
        materialized_payload = payloads_by_path.get(entry.relative)
        if materialized_payload is not None:
            atomic_write_bytes(materialized / entry.relative, materialized_payload)

    snapshot_digest = semantic_digest(digest_manifest)
    snapshot_id = stable_id("snapshot", snapshot_digest)
    snapshot_extensions: dict[str, Any] = {
        "x-preferred-full-digest-paths": sorted(preferred_paths),
        "x-asset-identity-policy": {
            "full_digest_byte_budget": policy.full_digest_byte_budget,
            "sampled_fingerprint_byte_budget": (policy.sampled_fingerprint_byte_budget),
            "sample_chunk_bytes": policy.sample_chunk_bytes,
        },
        "x-identity-byte-reads": {
            "full_digest": full_digest_bytes_read,
            "sampled_fingerprint": sampled_fingerprint_bytes_read,
        },
    }
    if manifest_candidates:
        snapshot_extensions["x-checksum-manifest-inspection"] = manifest_inspection.public_summary(
            upgraded_targets=manifest_upgraded_targets
        )
    if material_paths:
        snapshot_extensions.update(
            {
                "x-material-full-digest-paths": sorted(material_paths),
                "x-material-full-digest-byte-budget": (policy.material_full_digest_byte_budget),
                "x-material-full-digest-byte-reads": material_full_digest_bytes_read,
                "x-material-input-identities": [
                    {
                        "path": path,
                        "tier": identities_by_path[path].tier,
                    }
                    for path in sorted(material_paths)
                ],
            }
        )
    snapshot_record = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "repository_snapshot",
        "snapshot_id": snapshot_id,
        "audit_run_id": run_id,
        "project_root": str(source),
        "captured_at": timestamp,
        "strategy": "content_addressed_copy",
        "snapshot_digest": snapshot_digest,
        "immutability": True,
        "git_state": {"available": False, "worktree_state": "unknown"},
        "file_manifest_ref": "observed/files.jsonl",
        "included_roots": ["."],
        "excluded_paths": sorted(_EXCLUDED_DIRS),
        "large_asset_policy": "identity_record_unless_material_copy_authorized",
        "live_workspace_state": {"status": "not_monitored", "mix_live_content_into_run": False},
        "provenance": {
            "actor": {
                "actor_kind": "controller",
                "actor_id": "software:sc-referee-controller",
                "display_name": "sc-referee controller",
            },
            "method": "deterministic_controller",
            "created_at": timestamp,
            "tool": "sc-referee",
            "tool_version": __version__,
        },
        "extensions": snapshot_extensions,
    }
    return SnapshotOutput(
        snapshot_record,
        file_records,
        asset_identity_records,
        materialized,
        policy,
    )


def detect_workspace_divergence(
    source: Path,
    initial_file_records: list[dict[str, Any]],
    *,
    detected_at: str,
    initial_asset_identities: list[dict[str, Any]] | None = None,
    identity_policy: AssetIdentityPolicy | None = None,
) -> dict[str, Any]:
    """Compare a live workspace to the initial inventory without changing the snapshot."""

    source = source.resolve()
    policy = identity_policy or AssetIdentityPolicy()
    identities_by_file_id = {
        str(record["asset_ref"]["record_id"]): record
        for record in initial_asset_identities or []
        if record.get("asset_ref", {}).get("record_type") == "file_record"
    }
    initial = {
        str(record["path"]): _record_identity_tuple(
            record, identities_by_file_id.get(str(record["file_id"]))
        )
        for record in initial_file_records
    }
    current: dict[str, tuple[str, int, str | None]] = {}
    unreadable_paths: set[str] = set()
    for entry in _inventory_entries(source):
        initial_record = next(
            (record for record in initial_file_records if record["path"] == entry.relative),
            None,
        )
        try:
            if entry.kind == "symlink":
                fingerprint = sha256_digest(
                    os.readlink(entry.path).encode("utf-8", errors="surrogateescape")
                )
                current[entry.relative] = (
                    ("symlink:weak_fingerprint", entry.stat.st_size, fingerprint)
                    if identities_by_file_id
                    else ("symlink", entry.stat.st_size, None)
                )
            elif entry.kind == "special":
                current[entry.relative] = ("special:unidentified", entry.stat.st_size, None)
            elif initial_record is None:
                current[entry.relative] = ("file:unseen", entry.stat.st_size, None)
            else:
                identity = identities_by_file_id.get(str(initial_record["file_id"]))
                tier = identity.get("tier") if identity else None
                if identity is None:
                    expected_digest = initial_record.get("digest")
                    digest = None
                    if isinstance(expected_digest, str):
                        digest = sha256_digest(_read_stable_full_file(entry.path, entry.stat))
                    current[entry.relative] = ("file", entry.stat.st_size, digest)
                elif tier == "weak_fingerprint":
                    fingerprint, _ = _read_stable_sample(
                        entry.path,
                        entry.stat,
                        max_bytes=policy.sample_chunk_bytes * 3,
                        chunk_bytes=policy.sample_chunk_bytes,
                    )
                    current[entry.relative] = (
                        "file:weak_fingerprint",
                        entry.stat.st_size,
                        fingerprint,
                    )
                elif tier == "unidentified":
                    current[entry.relative] = ("file:unidentified", entry.stat.st_size, None)
                elif tier == "manifest":
                    current[entry.relative] = (
                        "file:manifest",
                        entry.stat.st_size,
                        _observed_file_state_digest(
                            entry.relative,
                            entry.stat.st_size,
                            entry.stat.st_mtime_ns,
                        ),
                    )
                else:
                    payload = _read_stable_full_file(entry.path, entry.stat)
                    current[entry.relative] = (
                        "file:full_digest",
                        entry.stat.st_size,
                        sha256_digest(payload),
                    )
        except OSError:
            unreadable_paths.add(entry.relative)

    changed_paths = sorted(
        {
            *unreadable_paths,
            *(set(initial) ^ set(current)),
            *(path for path in set(initial) & set(current) if initial[path] != current[path]),
        }
    )
    if not changed_paths:
        return {"status": "unchanged", "mix_live_content_into_run": False}
    return {
        "status": "workspace_diverged",
        "mix_live_content_into_run": False,
        "detected_at": detected_at,
        "changed_paths": changed_paths,
    }


def merge_workspace_state(
    existing: Mapping[str, Any], observed: Mapping[str, Any]
) -> dict[str, Any]:
    """Retain the first divergence and accumulate paths across stage-boundary checks."""

    if existing.get("status") != "workspace_diverged":
        return dict(observed)
    if observed.get("status") != "workspace_diverged":
        return dict(existing)
    return {
        "status": "workspace_diverged",
        "mix_live_content_into_run": False,
        "detected_at": existing["detected_at"],
        "changed_paths": sorted(
            {
                *existing.get("changed_paths", []),
                *observed.get("changed_paths", []),
            }
        ),
    }


def _inventory_entries(source: Path) -> list[_InventoryEntry]:
    entries: list[_InventoryEntry] = []
    for path in sorted(source.rglob("*")):
        relative_path = path.relative_to(source)
        if any(part in _EXCLUDED_DIRS for part in relative_path.parts):
            continue
        try:
            path_stat = path.lstat()
        except OSError:
            continue
        mode = path_stat.st_mode
        if stat_module.S_ISLNK(mode):
            kind = "symlink"
        elif stat_module.S_ISREG(mode):
            kind = "file"
        elif stat_module.S_ISDIR(mode):
            continue
        else:
            kind = "special"
        entries.append(_InventoryEntry(path, relative_path.as_posix(), path_stat, kind))
    return entries


def _normalize_preferred_paths(values: tuple[str, ...]) -> frozenset[str]:
    normalized: set[str] = set()
    for value in values:
        candidate = PurePosixPath(value)
        if not value or candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError("preferred full-digest paths must be repository-relative POSIX paths")
        normalized.add(candidate.as_posix())
    return frozenset(normalized)


def _normalize_material_paths(values: tuple[str, ...]) -> frozenset[str]:
    if len(values) > MAX_MATERIAL_FULL_DIGEST_PATHS:
        raise ValueError(
            f"at most {MAX_MATERIAL_FULL_DIGEST_PATHS} material input paths may be selected"
        )
    normalized: set[str] = set()
    for value in values:
        candidate = PurePosixPath(value)
        if not value or candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError("material input paths must be safe repository-relative POSIX paths")
        normalized.add(candidate.as_posix())
    return frozenset(normalized)


def _read_stable_full_file(path: Path, expected: os.stat_result) -> bytes:
    descriptor = _open_stable_regular_file(path, expected)
    try:
        chunks: list[bytes] = []
        remaining = expected.st_size
        while remaining:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            if not chunk:
                raise OSError("file ended before its inventoried size")
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1):
            raise OSError("file grew during snapshot capture")
        _require_same_stat(os.fstat(descriptor), expected)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _read_stable_sample(
    path: Path,
    expected: os.stat_result,
    *,
    max_bytes: int,
    chunk_bytes: int,
) -> tuple[str, int]:
    descriptor = _open_stable_regular_file(path, expected)
    try:
        region_count = min(3, max_bytes)
        if region_count <= 0:
            raise OSError("sample byte budget is exhausted")
        read_size = min(chunk_bytes, max(1, max_bytes // region_count), expected.st_size)
        offsets = _sample_offsets(expected.st_size, read_size)
        framed = bytearray(b"sc-referee-sparse-v1\0")
        framed.extend(expected.st_size.to_bytes(8, "big"))
        bytes_read = 0
        for offset in offsets:
            os.lseek(descriptor, offset, os.SEEK_SET)
            chunk = os.read(descriptor, read_size)
            if len(chunk) != read_size:
                raise OSError("sample region changed during snapshot capture")
            framed.extend(offset.to_bytes(8, "big"))
            framed.extend(len(chunk).to_bytes(8, "big"))
            framed.extend(chunk)
            bytes_read += len(chunk)
        _require_same_stat(os.fstat(descriptor), expected)
        return sha256_digest(bytes(framed)), bytes_read
    finally:
        os.close(descriptor)


def _sample_offsets(size_bytes: int, read_size: int) -> list[int]:
    if read_size == 0:
        return [0]
    offsets = {
        0,
        max(0, (size_bytes - read_size) // 2),
        max(0, size_bytes - read_size),
    }
    return sorted(offsets)


def _open_stable_regular_file(path: Path, expected: os.stat_result) -> int:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    flags |= getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(path, flags)
    try:
        _require_same_stat(os.fstat(descriptor), expected)
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


def _require_same_stat(observed: os.stat_result, expected: os.stat_result) -> None:
    if not stat_module.S_ISREG(observed.st_mode) or (
        observed.st_dev,
        observed.st_ino,
        observed.st_size,
        observed.st_mtime_ns,
    ) != (
        expected.st_dev,
        expected.st_ino,
        expected.st_size,
        expected.st_mtime_ns,
    ):
        raise OSError("path identity changed during snapshot capture")


def _record_identity_tuple(
    record: Mapping[str, Any], identity: Mapping[str, Any] | None
) -> tuple[str, int, str | None]:
    role = record.get("role")
    kind = (
        "symlink"
        if role == "symlink_not_followed"
        else "special"
        if (role == "unsupported_special_file")
        else "file"
    )
    if identity is None:
        digest = record.get("digest")
        return kind, int(record["size_bytes"]), digest if isinstance(digest, str) else None
    tier = str(identity["tier"])
    evidence = identity.get("identity_evidence", {})
    digest = evidence.get("digest") or evidence.get("sampled_fingerprint")
    if tier == "manifest":
        digest = _manifest_observed_state_digest(identity)
    return (
        f"{kind}:{tier}",
        int(record["size_bytes"]),
        (str(digest) if isinstance(digest, str) else None),
    )


def _manifest_observed_state_digest(identity: Mapping[str, Any]) -> str | None:
    extensions = identity.get("extensions")
    if not isinstance(extensions, Mapping):
        return None
    state = extensions.get("x-observed-file-state")
    if not isinstance(state, Mapping):
        return None
    path = state.get("path")
    size_bytes = state.get("size_bytes")
    modified_at_ns = state.get("modified_at_ns")
    if (
        not isinstance(path, str)
        or not path
        or not isinstance(size_bytes, int)
        or isinstance(size_bytes, bool)
        or size_bytes < 0
        or not isinstance(modified_at_ns, int)
        or isinstance(modified_at_ns, bool)
        or modified_at_ns < 0
    ):
        return None
    return _observed_file_state_digest(path, size_bytes, modified_at_ns)


def _observed_file_state_digest(path: str, size_bytes: int, modified_at_ns: int) -> str:
    return semantic_digest(
        {"path": path, "size_bytes": size_bytes, "modified_at_ns": modified_at_ns}
    )


def _read_priority(path: Path, relative: str) -> int:
    role = _role_for(path, "file")
    if role in {"analysis_source", "report_candidate"}:
        return 0
    if is_root_checksum_manifest(relative):
        return 1
    if role == "data_or_result":
        return 3
    return 2


def _timestamp_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _timestamp_from_ns(value: int) -> str:
    return datetime.fromtimestamp(value / 1_000_000_000, UTC).isoformat().replace("+00:00", "Z")


def _language_for(path: Path) -> str:
    return {
        ".py": "python",
        ".md": "markdown",
        ".qmd": "quarto",
        ".rmd": "r_markdown",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".csv": "csv",
        ".sh": "shell",
    }.get(path.suffix.lower(), "unknown")


def _role_for(path: Path, kind: str) -> str:
    if kind == "symlink":
        return "symlink_not_followed"
    if kind == "special":
        return "unsupported_special_file"
    name = path.name.lower()
    if "report" in name or "manuscript" in name:
        return "report_candidate"
    if path.suffix.lower() in {".py", ".r", ".sh"}:
        return "analysis_source"
    if path.suffix.lower() in {".csv", ".tsv", ".parquet"}:
        return "data_or_result"
    return "other"
