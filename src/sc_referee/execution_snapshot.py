from __future__ import annotations

import os
import stat
from pathlib import Path, PurePosixPath
from typing import Any

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.storage.atomic import atomic_create_bytes, fsync_directory


def _mapping(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} is malformed")
    return value


def _safe_relative(value: object) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise ValueError("snapshot FileRecord path is unavailable")
    relative = PurePosixPath(value)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise ValueError(f"snapshot FileRecord path is unsafe: {value!r}")
    return relative


def _read_stable_regular_file(path: Path) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    flags |= getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError(f"snapshot materialization contains a non-regular file: {path}")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise ValueError(f"snapshot materialization changed while being verified: {path}")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _expected_materialized_files(
    source_lock: dict[str, Any],
    authorization: dict[str, Any],
    schema_root: Path,
) -> dict[str, tuple[str, int | None]]:
    scope = _mapping(authorization.get("scope"), "authorization scope")
    snapshot_binding = _mapping(scope.get("snapshot"), "authorization snapshot binding")
    snapshot_ref = _mapping(snapshot_binding.get("record_ref"), "authorization snapshot reference")
    snapshot = _mapping(source_lock.get("repository_snapshot"), "source RepositorySnapshot")
    if (
        snapshot.get("record_type") != "repository_snapshot"
        or snapshot.get("snapshot_id") != snapshot_ref.get("record_id")
        or semantic_digest(snapshot) != snapshot_binding.get("semantic_digest")
    ):
        raise ValueError("registered source lock does not match the authorized snapshot")

    validator = LocalSchemaRegistry(schema_root)
    validator.validate(snapshot)
    file_records = source_lock.get("file_records", [])
    identities = source_lock.get("asset_identities", [])
    if not isinstance(file_records, list) or not isinstance(identities, list):
        raise ValueError("source lock snapshot inventory is malformed")
    identity_by_id: dict[str, dict[str, Any]] = {}
    for identity in identities:
        if not isinstance(identity, dict):
            raise ValueError("source lock AssetIdentity is malformed")
        validator.validate(identity)
        identity_id = identity.get("asset_identity_id")
        if not isinstance(identity_id, str) or identity_id in identity_by_id:
            raise ValueError("source lock AssetIdentity identity is missing or duplicated")
        identity_by_id[identity_id] = identity

    expected: dict[str, tuple[str, int | None]] = {}
    unavailable_paths: set[str] = set()
    for record in file_records:
        if not isinstance(record, dict):
            raise ValueError("source lock FileRecord is malformed")
        validator.validate(record)
        if record.get("snapshot_ref") != snapshot_ref:
            raise ValueError("source lock FileRecord is bound to a different snapshot")
        relative = _safe_relative(record.get("path")).as_posix()
        if relative in expected or relative in unavailable_paths:
            raise ValueError("source lock snapshot paths are duplicated")
        identity_ref = record.get("asset_identity_ref")
        identity = None
        if isinstance(identity_ref, dict) and isinstance(identity_ref.get("record_id"), str):
            identity = identity_by_id.get(str(identity_ref["record_id"]))
        if record.get("identity_disposition") == "recorded" and identity is None:
            raise ValueError("source lock FileRecord lacks its recorded AssetIdentity")
        if identity is not None and identity.get("asset_ref") != {
            "record_type": "file_record",
            "record_id": record.get("file_record_id"),
        }:
            raise ValueError("source lock FileRecord and AssetIdentity disagree")
        evidence = identity.get("identity_evidence") if identity is not None else None
        if (
            record.get("entry_kind") == "regular_file"
            and identity is not None
            and identity.get("tier") == "full_digest"
            and isinstance(evidence, dict)
            and evidence.get("kind") == "full_digest"
            and isinstance(evidence.get("digest"), str)
        ):
            size = record.get("byte_size")
            expected[relative] = (
                str(evidence["digest"]),
                size if isinstance(size, int) and not isinstance(size, bool) else None,
            )
        else:
            unavailable_paths.add(relative)
    if set(expected) & unavailable_paths:
        raise ValueError("source lock snapshot materialization policy is contradictory")
    return expected


def _inventory_materialization(root: Path) -> tuple[dict[str, Path], set[str]]:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("bound snapshot materialization is unavailable or unsafe")
    files: dict[str, Path] = {}
    directories: set[str] = set()
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        path_stat = path.lstat()
        if stat.S_ISLNK(path_stat.st_mode):
            raise ValueError(f"snapshot materialization contains a symbolic link: {relative}")
        if stat.S_ISREG(path_stat.st_mode):
            files[relative] = path
        elif stat.S_ISDIR(path_stat.st_mode):
            directories.add(relative)
        else:
            raise ValueError(f"snapshot materialization contains a special file: {relative}")
    return files, directories


def stage_verified_snapshot(
    source_lock: dict[str, Any],
    authorization: dict[str, Any],
    source_materialization: Path,
    staged_root: Path,
    schema_root: Path,
) -> Path:
    """Verify exact captured bytes and stage the only directory eligible for `/project`."""

    expected = _expected_materialized_files(source_lock, authorization, schema_root)
    files, directories = _inventory_materialization(source_materialization)
    expected_directories = {
        parent.as_posix()
        for relative in expected
        for parent in PurePosixPath(relative).parents
        if parent != PurePosixPath(".")
    }
    if set(files) != set(expected):
        missing = sorted(set(expected) - set(files))
        unexpected = sorted(set(files) - set(expected))
        raise ValueError(
            f"snapshot materialization drifted (missing={missing}, unexpected={unexpected})"
        )
    if directories != expected_directories:
        raise ValueError("snapshot materialization directory topology drifted")

    verified: dict[str, bytes] = {}
    for relative, path in files.items():
        payload = _read_stable_regular_file(path)
        expected_digest, expected_size = expected[relative]
        if sha256_digest(payload) != expected_digest or (
            expected_size is not None and len(payload) != expected_size
        ):
            raise ValueError(f"snapshot materialization bytes drifted: {relative}")
        verified[relative] = payload

    if staged_root.exists() or staged_root.is_symlink():
        staged_files, staged_directories = _inventory_materialization(staged_root)
        if set(staged_files) != set(expected) or staged_directories != expected_directories:
            raise ValueError("existing staged execution snapshot does not match authorization")
        for relative, path in staged_files.items():
            payload = _read_stable_regular_file(path)
            if payload != verified[relative]:
                raise ValueError("existing staged execution snapshot bytes drifted")
        return staged_root

    staged_root.mkdir(parents=True, exist_ok=False, mode=0o700)
    for relative in sorted(verified):
        logical = _safe_relative(relative)
        target = staged_root.joinpath(*logical.parts)
        atomic_create_bytes(target, verified[relative])
    fsync_directory(staged_root)
    return staged_root
