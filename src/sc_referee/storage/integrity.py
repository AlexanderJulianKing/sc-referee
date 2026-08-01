from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.version import SCHEMA_VERSION, __version__

from .layout import AuditLayout
from .sqlite_index import record_identity

INTEGRITY_PROFILE = "x-sc-referee-m0-canonical-files-v1"
_MANIFEST_PATH = "derived/storage-manifest.jsonl"
_BUNDLE_PATH = "audit.bundle.json"
_MATERIALIZED_PARTS = ("observed", "snapshot", "materialized")


class StorageIntegrityError(ValueError):
    """Raised when canonical files or their generated index fail verification."""


def build_storage_manifest(
    layout: AuditLayout, audit_run_id: str, created_at: str
) -> dict[str, Any]:
    """Build a public StorageManifest using the Milestone 0 integrity profile."""

    (layout.root / "objects").mkdir(parents=True, exist_ok=True)
    entries = [_file_entry(layout.root, path) for path in _canonical_paths(layout)]
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "storage_manifest",
        "storage_manifest_id": f"storage-manifest:{audit_run_id}",
        "audit_run_id": audit_run_id,
        "canonical_record_formats": ["json", "jsonl"],
        "scientist_editable_formats": ["yaml", "json"],
        "canonical_record_roots": ["semantic.lock.json", "observed/", "derived/"],
        "content_addressed_object_store": {
            "root": "objects/",
            "digest_algorithm": "sha256",
        },
        "generated_query_index": {
            "engine": "sqlite",
            "path": "audit.db",
            "canonical": False,
            "disposable": True,
            "rebuildable_from_canonical_records": True,
        },
        "canonical_manifest_digest": semantic_digest(entries),
        "created_at": created_at,
        "provenance": {
            "actor": {
                "actor_kind": "controller",
                "actor_id": "software:sc-referee-controller",
                "display_name": "sc-referee controller",
            },
            "method": "deterministic_controller",
            "created_at": created_at,
            "tool": "sc-referee",
            "tool_version": __version__,
        },
        "extensions": {
            "x-integrity-profile": INTEGRITY_PROFILE,
            "x-canonical-files": entries,
            "x-self-excluded-path": _MANIFEST_PATH,
            "x-aggregate-excluded-path": _BUNDLE_PATH,
            "x-profile-status": "proposed_milestone_0_extension",
        },
    }


def verify_storage_manifest(layout: AuditLayout, manifest: Mapping[str, Any]) -> None:
    """Verify the exact canonical-file binding set and every recorded digest."""

    extensions = manifest.get("extensions")
    if not isinstance(extensions, Mapping) or extensions.get("x-integrity-profile") != (
        INTEGRITY_PROFILE
    ):
        raise StorageIntegrityError("unsupported or missing storage integrity profile")
    entries = extensions.get("x-canonical-files")
    if not isinstance(entries, list):
        raise StorageIntegrityError("storage manifest file entries are missing")

    expected_paths = [path.relative_to(layout.root).as_posix() for path in _canonical_paths(layout)]
    recorded_paths: list[str] = []
    normalized_entries: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise StorageIntegrityError("storage manifest contains a malformed file entry")
        relative = entry.get("path")
        digest = entry.get("digest")
        size_bytes = entry.get("size_bytes")
        if (
            not isinstance(relative, str)
            or not isinstance(digest, str)
            or not isinstance(size_bytes, int)
        ):
            raise StorageIntegrityError("storage manifest contains a malformed file entry")
        path = _resolve_manifest_path(layout.root, relative)
        actual = _file_entry(layout.root, path)
        normalized = {"path": relative, "digest": digest, "size_bytes": size_bytes}
        if normalized != actual:
            raise StorageIntegrityError(f"canonical file digest mismatch: {relative}")
        recorded_paths.append(relative)
        normalized_entries.append(normalized)

    if recorded_paths != sorted(recorded_paths) or len(set(recorded_paths)) != len(recorded_paths):
        raise StorageIntegrityError("storage manifest paths are not sorted and unique")
    if recorded_paths != expected_paths:
        raise StorageIntegrityError("storage manifest canonical file set is incomplete")
    if manifest.get("canonical_manifest_digest") != semantic_digest(normalized_entries):
        raise StorageIntegrityError("canonical manifest digest mismatch")


def verify_sqlite_index(path: Path, records: Iterable[Mapping[str, Any]]) -> None:
    """Verify that SQLite is an exact disposable projection of normalized records."""

    expected: dict[tuple[str, str, str], str] = {}
    for record in records:
        record_type, record_id = record_identity(record)
        text = canonical_json(dict(record))
        digest = sha256_digest(text)
        expected[(record_type, record_id, digest)] = text

    try:
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    except sqlite3.Error as error:
        raise StorageIntegrityError(f"SQLite index is unavailable: {error}") from error
    try:
        rows = connection.execute(
            "SELECT record_type, record_id, json_text, digest FROM records"
        ).fetchall()
    except sqlite3.Error as error:
        raise StorageIntegrityError(f"SQLite index cannot be read: {error}") from error
    finally:
        connection.close()

    actual = {(row[0], row[1], row[3]): row[2] for row in rows}
    if actual != expected:
        raise StorageIntegrityError("SQLite index does not match canonical bundle records")


def _canonical_paths(layout: AuditLayout) -> list[Path]:
    paths: list[Path] = []
    if layout.lock_path.is_file() and not layout.lock_path.is_symlink():
        paths.append(layout.lock_path)
    for root in (layout.observed, layout.derived):
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.is_symlink() or path.suffix not in {".json", ".jsonl"}:
                continue
            relative_parts = path.relative_to(layout.root).parts
            if relative_parts[: len(_MATERIALIZED_PARTS)] == _MATERIALIZED_PARTS:
                continue
            if path.relative_to(layout.root).as_posix() == _MANIFEST_PATH:
                continue
            paths.append(path)
    return sorted(paths, key=lambda item: item.relative_to(layout.root).as_posix())


def _file_entry(root: Path, path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise StorageIntegrityError(f"canonical path is unavailable or unsafe: {path}")
    payload = path.read_bytes()
    resolved_root = root.resolve()
    resolved_path = path.resolve()
    try:
        relative = resolved_path.relative_to(resolved_root)
    except ValueError as error:
        raise StorageIntegrityError(f"canonical path escapes audit root: {path}") from error
    return {
        "path": relative.as_posix(),
        "digest": sha256_digest(payload),
        "size_bytes": len(payload),
    }


def _resolve_manifest_path(root: Path, relative: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise StorageIntegrityError(f"unsafe canonical path in manifest: {relative}")
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as error:
        raise StorageIntegrityError(f"canonical path escapes audit root: {relative}") from error
    return resolved
