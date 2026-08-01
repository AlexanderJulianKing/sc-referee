from __future__ import annotations

import os
import shutil
import tempfile
import unicodedata
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

from sc_referee.core.ids import canonical_json, semantic_digest, stable_id
from sc_referee.records.normalization import write_normalized_json
from sc_referee.storage.atomic import atomic_write_bytes, fsync_directory
from sc_referee_evaluation.snapshot_evidence import (
    SnapshotEvidenceError,
    read_full_digest_snapshot_file,
    validate_content_addressed_snapshot,
)


class BlindWorkspaceError(ValueError):
    """The requested blind workspace would violate its explicit isolation contract."""


_ALLOWED_ROLES = {
    "scientific_task",
    "data_description",
    "staged_data",
    "workflow_source",
    "report",
    "generated_output",
    "execution_evidence",
}


def build_blind_workspace(
    source_root: Path,
    destination: Path,
    manifest_path: Path,
    files: list[dict[str, str]],
    *,
    snapshot: dict[str, Any],
    file_records: list[dict[str, Any]],
    asset_identities: list[dict[str, Any]],
    created_at: str,
    forbidden_source_paths: set[str] | None = None,
    forbidden_markers: set[str] | None = None,
    forbidden_digests: set[str] | None = None,
) -> dict[str, Any]:
    """Copy exact immutable-snapshot files after bounded answer-leak checks."""

    if not source_root.is_dir() or source_root.is_symlink():
        raise BlindWorkspaceError("Source root must be one real directory.")
    if destination.exists():
        raise BlindWorkspaceError("Blind workspace destination must not already exist.")
    if manifest_path.exists():
        raise BlindWorkspaceError("Blind workspace manifest must not already exist.")
    if manifest_path == destination or manifest_path.is_relative_to(destination):
        raise BlindWorkspaceError("Runner-side manifest must remain outside the blind workspace.")
    if not files:
        raise BlindWorkspaceError("Blind workspace requires at least one allowlisted file.")
    try:
        snapshot_index = validate_content_addressed_snapshot(
            snapshot, file_records, asset_identities
        )
    except SnapshotEvidenceError as error:
        raise BlindWorkspaceError(str(error)) from error
    if _timestamp(created_at) < _timestamp(str(snapshot.get("captured_at", ""))):
        raise BlindWorkspaceError("Blind workspace creation cannot precede snapshot capture.")

    forbidden_paths = {
        _safe_relative_path(value).as_posix() for value in (forbidden_source_paths or set())
    }
    markers = sorted(value for value in (forbidden_markers or set()) if value)
    marker_bytes = [encoded for value in markers for encoded in _encoded_text_variants(value)]
    forbidden_payloads, forbidden_texts, unresolved_forbidden_paths = (
        _load_forbidden_source_content(source_root, forbidden_paths)
    )
    forbidden_digest_values = forbidden_digests or set()
    selected: list[tuple[PurePosixPath, str, bytes, str, dict[str, Any], dict[str, Any]]] = []
    seen_paths: set[str] = set()
    for item in files:
        relative = _safe_relative_path(item.get("path", ""))
        path_value = relative.as_posix()
        role = item.get("role")
        if role not in _ALLOWED_ROLES:
            raise BlindWorkspaceError(f"Unsupported blind-workspace role {role!r}.")
        if path_value in seen_paths:
            raise BlindWorkspaceError(f"Duplicate blind-workspace path {path_value!r}.")
        seen_paths.add(path_value)
        if path_value in forbidden_paths:
            raise BlindWorkspaceError(f"Selected forbidden answer-side path {path_value!r}.")
        try:
            file_record, identity, payload, digest = read_full_digest_snapshot_file(
                snapshot_index, source_root, path_value
            )
        except SnapshotEvidenceError as error:
            raise BlindWorkspaceError(str(error)) from error
        if digest in forbidden_digest_values:
            raise BlindWorkspaceError(
                f"Selected path {path_value!r} matches a forbidden answer-side digest."
            )
        if any(marker in payload for marker in marker_bytes):
            raise BlindWorkspaceError(
                f"Selected path {path_value!r} contains a forbidden literal marker."
            )
        if any(forbidden_payload in payload for forbidden_payload in forbidden_payloads):
            raise BlindWorkspaceError(
                f"Selected path {path_value!r} embeds declared forbidden source content."
            )
        candidate_texts = _decoded_text_variants(payload)
        if any(
            forbidden_text in candidate_text
            for forbidden_text in forbidden_texts
            for candidate_text in candidate_texts
        ):
            raise BlindWorkspaceError(
                f"Selected path {path_value!r} embeds normalized forbidden source text."
            )
        selected.append((relative, str(role), payload, digest, file_record, identity))

    file_entries = [
        {
            "path": relative.as_posix(),
            "role": role,
            "content_digest": digest,
            "byte_size": len(payload),
            "file_record_ref": {
                "record_type": "file_record",
                "record_id": file_record["file_record_id"],
            },
            "asset_identity_ref": {
                "record_type": "asset_identity",
                "record_id": identity["asset_identity_id"],
            },
        }
        for relative, role, payload, digest, file_record, identity in sorted(
            selected, key=lambda item: item[0].as_posix()
        )
    ]
    workspace_id = stable_id(
        "blind-workspace",
        str(snapshot["snapshot_id"]),
        semantic_digest(snapshot),
        created_at,
        *(canonical_json(entry) for entry in file_entries),
    )
    manifest: dict[str, Any] = {
        "evaluation_protocol_version": "0.2.0",
        "record_type": "evaluation_blind_workspace_manifest",
        "workspace_id": workspace_id,
        "source_snapshot_ref": {
            "record_type": "repository_snapshot",
            "record_id": snapshot["snapshot_id"],
        },
        "source_snapshot_digest": semantic_digest(snapshot),
        "created_at": created_at,
        "files": file_entries,
        "answer_side_content_copied": False,
        "project_code_executed": False,
        "scanner": {
            "method": "exact_path_digest_multiencoding_marker_and_forbidden_content_v2",
            "forbidden_path_count": len(forbidden_paths),
            "forbidden_source_content_variant_count": len(forbidden_payloads),
            "unresolved_forbidden_source_path_count": len(unresolved_forbidden_paths),
            "forbidden_digest_count": len(forbidden_digest_values),
            "forbidden_marker_count": len(markers),
            "limitations": [
                "The bounded scanner does not detect paraphrases, partial transformations, compression, encryption, or undisclosed answer-side content.",
                "Only exact bytes and UTF-8/UTF-16 text variants with Unicode and newline normalization are checked.",
            ],
        },
    }
    manifest["manifest_digest"] = semantic_digest(manifest)

    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent))
    try:
        for relative, _role, payload, _digest, _file_record, _identity in selected:
            atomic_write_bytes(staging.joinpath(*relative.parts), payload)
        os.replace(staging, destination)
        fsync_directory(destination.parent)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    write_normalized_json(manifest_path, manifest)
    return manifest


def _safe_relative_path(value: str) -> PurePosixPath:
    candidate = PurePosixPath(value)
    if not value or candidate.is_absolute() or ".." in candidate.parts or "." in candidate.parts:
        raise BlindWorkspaceError(f"Unsafe repository-relative path {value!r}.")
    return candidate


def _path_contains_symlink(root: Path, relative: PurePosixPath) -> bool:
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def _load_forbidden_source_content(
    source_root: Path, forbidden_paths: set[str]
) -> tuple[list[bytes], list[str], list[str]]:
    payloads: list[bytes] = []
    texts: list[str] = []
    unresolved: list[str] = []
    for path_value in sorted(forbidden_paths):
        relative = PurePosixPath(path_value)
        source = source_root.joinpath(*relative.parts)
        if not source.exists():
            unresolved.append(path_value)
            continue
        if _path_contains_symlink(source_root, relative) or not source.is_file():
            raise BlindWorkspaceError(
                f"Declared forbidden source path {path_value!r} is non-regular or crosses a symbolic link."
            )
        payload = source.read_bytes()
        if payload:
            payloads.extend(_payload_variants(payload))
            texts.extend(_decoded_text_variants(payload))
    return sorted(set(payloads)), sorted(set(texts)), unresolved


def _payload_variants(payload: bytes) -> list[bytes]:
    variants = [payload]
    for text in _decoded_text_variants(payload):
        variants.extend(_encoded_text_variants(text))
    return variants


def _encoded_text_variants(value: str) -> list[bytes]:
    normalized = _normalize_text(value)
    return [
        normalized.encode("utf-8"),
        normalized.encode("utf-16-le"),
        normalized.encode("utf-16-be"),
    ]


def _decoded_text_variants(payload: bytes) -> list[str]:
    variants: list[str] = []
    encodings = ["utf-8-sig"]
    if payload.startswith((b"\xff\xfe", b"\xfe\xff")) or b"\x00" in payload:
        encodings.extend(["utf-16", "utf-16-le", "utf-16-be"])
    for encoding in encodings:
        try:
            text = _normalize_text(payload.decode(encoding))
        except UnicodeDecodeError:
            continue
        if text:
            variants.append(text)
    return sorted(set(variants))


def _normalize_text(value: str) -> str:
    return unicodedata.normalize("NFC", value).replace("\r\n", "\n").replace("\r", "\n")


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise BlindWorkspaceError(f"Invalid blind-workspace timestamp {value!r}.") from error
    if parsed.tzinfo is None:
        raise BlindWorkspaceError("Blind-workspace timestamps must include an offset.")
    return parsed
