from __future__ import annotations

import hashlib
import json
import os
import stat
import tempfile
import zipfile
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import IO, Any
from urllib.parse import urlsplit

from sc_referee.agent_protocol import load_audit_status
from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest, stable_id
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.reporting.html import render_report_bytes
from sc_referee.reporting.policy import validate_report_contract
from sc_referee.storage.atomic import fsync_directory
from sc_referee.storage.sqlite_index import record_identity
from sc_referee.version import SCHEMA_VERSION, __version__

RO_CRATE_CONTEXT = "https://w3id.org/ro/crate/1.3/context"
RO_CRATE_PROFILE = "https://w3id.org/ro/crate/1.3"
CONTENT_DIGEST_PROFILE = "canonical-json-file-inventory-excluding-ro-crate-export-v1"
METADATA_PATH = "ro-crate-metadata.json"
EXPORT_RECORD_PATH = "ro-crate-export.json"
NATIVE_ROOT = "native/"
_STORAGE_MANIFEST_PATH = "derived/storage-manifest.jsonl"
_MAX_ARCHIVE_MEMBERS = 100_000
_MAX_CONTROL_MEMBER_BYTES = 64 * 1024 * 1024
_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


class ROCrateValidationError(ValueError):
    """Raised when an archive violates the bounded sc-referee RO-Crate profile."""


def export_ro_crate(
    audit_root: Path,
    output: Path,
    schema_root: Path,
    *,
    author_name: str,
    license_uri: str,
    license_name: str,
    author_id: str = "#author",
) -> dict[str, Any]:
    """Create one deterministic, no-replace RO-Crate ZIP from an integrity-verified audit."""

    if output.suffix.lower() != ".zip":
        raise ValueError("RO-Crate output must use the .zip suffix")
    normalized_author_name = _declared_text(author_name, "author name")
    normalized_license_name = _declared_text(license_name, "license name")
    normalized_author_id = _uri_reference(author_id, "author identifier", absolute=False)
    normalized_license_uri = _uri_reference(license_uri, "license URI", absolute=True)
    if normalized_author_id in {
        "./",
        METADATA_PATH,
        EXPORT_RECORD_PATH,
        "#sc-referee",
        normalized_license_uri,
    }:
        raise ValueError("author identifier conflicts with a reserved RO-Crate entity")

    load_audit_status(audit_root, schema_root)
    resolved_root = audit_root.resolve()
    resolved_output = output.resolve(strict=False)
    try:
        resolved_output.relative_to(resolved_root)
    except ValueError:
        pass
    else:
        raise ValueError("RO-Crate output must be outside the source audit root")

    bundle = _read_json_object(resolved_root / "audit.bundle.json", "native audit bundle")
    source_files = _native_source_files(resolved_root, bundle)
    native_entries = [
        _source_file_entry(f"{NATIVE_ROOT}{relative}", path)
        for relative, path in source_files.items()
    ]
    metadata = _build_metadata(
        bundle,
        native_entries,
        author_id=normalized_author_id,
        author_name=normalized_author_name,
        license_uri=normalized_license_uri,
        license_name=normalized_license_name,
    )
    metadata_payload = _json_bytes(metadata)
    content_inventory = sorted(
        [
            {
                "path": METADATA_PATH,
                "digest": sha256_digest(metadata_payload),
                "size_bytes": len(metadata_payload),
            },
            *native_entries,
        ],
        key=lambda item: str(item["path"]),
    )
    content_digest = semantic_digest(content_inventory)
    export_record = _build_export_record(
        bundle,
        content_digest,
        author_id=normalized_author_id,
        author_name=normalized_author_name,
        license_uri=normalized_license_uri,
        license_name=normalized_license_name,
    )
    LocalSchemaRegistry(schema_root).validate(export_record)

    archive_members: dict[str, bytes | Path] = {
        METADATA_PATH: metadata_payload,
        EXPORT_RECORD_PATH: _json_bytes(export_record),
    }
    archive_members.update(
        {f"{NATIVE_ROOT}{relative}": path for relative, path in source_files.items()}
    )
    _publish_archive(output, archive_members, schema_root, export_record)
    return export_record


def validate_ro_crate(archive_path: Path, schema_root: Path) -> dict[str, Any]:
    """Validate one attached ZIP against the bounded offline sc-referee RO-Crate 1.3 profile."""

    if archive_path.is_symlink() or not archive_path.is_file():
        raise ROCrateValidationError(f"RO-Crate archive is unavailable or unsafe: {archive_path}")
    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            infos = archive.infolist()
            _validate_archive_members(infos)
            metadata_payload = _read_control_member(archive, METADATA_PATH)
            export_payload = _read_control_member(archive, EXPORT_RECORD_PATH)
            metadata = _parse_canonical_object(metadata_payload, METADATA_PATH)
            export_record = _parse_canonical_object(export_payload, EXPORT_RECORD_PATH)
            if metadata.get("@context") != RO_CRATE_CONTEXT:
                raise ROCrateValidationError("RO-Crate 1.3 context is required")
            native_names, file_entities = _validate_metadata_and_members(metadata, infos)
            native_entries = [
                _archive_file_entry(archive, name, file_entities[name]) for name in native_names
            ]

            content_inventory = sorted(
                [
                    {
                        "path": METADATA_PATH,
                        "digest": sha256_digest(metadata_payload),
                        "size_bytes": len(metadata_payload),
                    },
                    *native_entries,
                ],
                key=lambda item: str(item["path"]),
            )
            content_digest = semantic_digest(content_inventory)
            if export_record.get("content_digest") != content_digest:
                raise ROCrateValidationError("RO-Crate content digest mismatch")

            bundle_payload = _read_control_member(archive, f"{NATIVE_ROOT}audit.bundle.json")
            bundle = _parse_canonical_object(bundle_payload, "native/audit.bundle.json")
            registry = LocalSchemaRegistry(schema_root)
            registry.validate(bundle)
            validate_report_contract(bundle)
            declared = _declared_metadata(metadata)
            expected_metadata = _build_metadata(
                bundle,
                native_entries,
                author_id=declared[0],
                author_name=declared[1],
                license_uri=declared[2],
                license_name=declared[3],
            )
            if metadata != expected_metadata:
                raise ROCrateValidationError("RO-Crate metadata does not match the export profile")
            report_payload = _read_control_member(archive, f"{NATIVE_ROOT}report.html")
            if report_payload != render_report_bytes(bundle):
                raise ROCrateValidationError(
                    "native report bytes do not match the deterministic bundle rendering"
                )
            entries_by_name = {str(entry["path"]): entry for entry in native_entries}
            _validate_native_audit(archive, bundle, native_names, entries_by_name)

            expected_export = _build_export_record(
                bundle,
                content_digest,
                author_id=declared[0],
                author_name=declared[1],
                license_uri=declared[2],
                license_name=declared[3],
            )
            registry.validate(export_record)
            if export_record != expected_export:
                raise ROCrateValidationError("ROCrateExport record does not match archive content")
            return export_record
    except zipfile.BadZipFile as error:
        raise ROCrateValidationError(f"invalid RO-Crate ZIP archive: {error}") from error


def _build_metadata(
    bundle: Mapping[str, Any],
    native_entries: list[dict[str, Any]],
    *,
    author_id: str,
    author_name: str,
    license_uri: str,
    license_name: str,
) -> dict[str, Any]:
    audit_run_id = str(bundle["audit_run_id"])
    generated_at = str(bundle["generated_at"])
    file_entities = [
        {
            "@id": str(entry["path"]),
            "@type": "File",
            "name": str(entry["path"]).removeprefix(NATIVE_ROOT),
            "description": _file_description(str(entry["path"])),
            "encodingFormat": _media_type(str(entry["path"])),
            "contentSize": str(entry["size_bytes"]),
            "identifier": str(entry["digest"]),
        }
        for entry in native_entries
    ]
    return {
        "@context": RO_CRATE_CONTEXT,
        "@graph": [
            {
                "@id": METADATA_PATH,
                "@type": "CreativeWork",
                "about": {"@id": "./"},
                "conformsTo": {"@id": RO_CRATE_PROFILE},
                "description": "RO-Crate Metadata Descriptor (this file)",
            },
            {
                "@id": "./",
                "@type": "Dataset",
                "name": f"sc-referee audit {audit_run_id}",
                "description": (
                    "Integrity-verified native sc-referee audit records and report. "
                    "The native records remain canonical."
                ),
                "datePublished": generated_at,
                "author": {"@id": author_id},
                "creator": {"@id": "#sc-referee"},
                "license": {"@id": license_uri},
                "hasPart": [{"@id": str(entry["path"])} for entry in native_entries],
            },
            {"@id": author_id, "@type": "Person", "name": author_name},
            {"@id": license_uri, "@type": "CreativeWork", "name": license_name},
            {
                "@id": "#sc-referee",
                "@type": "SoftwareApplication",
                "name": "sc-referee",
                "softwareVersion": __version__,
            },
            *file_entities,
        ],
    }


def _build_export_record(
    bundle: Mapping[str, Any],
    content_digest: str,
    *,
    author_id: str,
    author_name: str,
    license_uri: str,
    license_name: str,
) -> dict[str, Any]:
    bundle_ref = {"record_type": "audit_bundle", "record_id": str(bundle["bundle_id"])}
    generated_at = str(bundle["generated_at"])
    export_id = stable_id(
        "rocrate",
        str(bundle["bundle_id"]),
        content_digest,
        author_id,
        author_name,
        license_uri,
        license_name,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "ro_crate_export",
        "export_id": export_id,
        "audit_bundle_ref": bundle_ref,
        "ro_crate_version": "1.3",
        "native_records_included": True,
        "crate_metadata_path": METADATA_PATH,
        "entity_refs": _bundle_entity_refs(bundle),
        "validation_status": "valid",
        "validation_messages": [],
        "content_digest": content_digest,
        "generated_at": generated_at,
        "provenance": {
            "actor": {
                "actor_kind": "controller",
                "actor_id": "software:sc-referee-controller",
                "display_name": "sc-referee controller",
            },
            "method": "deterministic_ro_crate_1_3_export",
            "created_at": generated_at,
            "tool": "sc-referee",
            "tool_version": __version__,
        },
        "extensions": {
            "x-authorship-declared-not-authenticated": True,
            "x-content-digest-profile": CONTENT_DIGEST_PROFILE,
            "x-content-digest-self-excluded-path": EXPORT_RECORD_PATH,
            "x-native-audit-root": NATIVE_ROOT,
            "x-third-party-ro-crate-validation": "not_performed",
        },
    }


def _native_source_files(root: Path, bundle: Mapping[str, Any]) -> dict[str, Path]:
    manifests = bundle.get("storage_manifests")
    if not isinstance(manifests, list) or len(manifests) != 1:
        raise ValueError("exactly one native storage manifest is required")
    manifest = manifests[0]
    if not isinstance(manifest, Mapping):
        raise ValueError("native storage manifest is malformed")
    extensions = manifest.get("extensions")
    entries = extensions.get("x-canonical-files") if isinstance(extensions, Mapping) else None
    if not isinstance(entries, list):
        raise ValueError("native storage manifest file inventory is missing")
    relative_paths = ["audit.bundle.json", "report.html", _STORAGE_MANIFEST_PATH]
    for entry in entries:
        if not isinstance(entry, Mapping) or not isinstance(entry.get("path"), str):
            raise ValueError("native storage manifest contains a malformed file entry")
        relative_paths.append(str(entry["path"]))
    if len(set(relative_paths)) != len(relative_paths):
        raise ValueError("native export file inventory is not unique")
    source_files = {
        relative: _safe_source_path(root, relative) for relative in sorted(relative_paths)
    }
    expected_manifest = _json_bytes(dict(manifest))
    if source_files[_STORAGE_MANIFEST_PATH].read_bytes() != expected_manifest:
        raise ValueError("native storage manifest JSONL does not match the audit bundle")
    return source_files


def _safe_source_path(root: Path, relative: str) -> Path:
    candidate = PurePosixPath(relative)
    if candidate.is_absolute() or not candidate.parts or ".." in candidate.parts:
        raise ValueError(f"unsafe native audit path: {relative}")
    path = root.joinpath(*candidate.parts)
    current = root
    for part in candidate.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"native audit path contains a symlink: {relative}")
    if not path.is_file():
        raise ValueError(f"native audit file is unavailable: {relative}")
    try:
        path.resolve().relative_to(root)
    except ValueError as error:
        raise ValueError(f"native audit path escapes the audit root: {relative}") from error
    return path


def _publish_archive(
    output: Path,
    members: Mapping[str, bytes | Path],
    schema_root: Path,
    expected_record: Mapping[str, Any],
) -> None:
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"RO-Crate output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=output.parent,
        prefix=f".{output.name}.",
        suffix=".tmp",
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        _write_archive(temporary, members)
        with temporary.open("rb") as handle:
            os.fsync(handle.fileno())
        validated = validate_ro_crate(temporary, schema_root)
        if validated != dict(expected_record):
            raise ROCrateValidationError("generated RO-Crate record changed during validation")
        os.link(temporary, output, follow_symlinks=False)
        temporary.unlink()
        fsync_directory(output.parent)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _write_archive(path: Path, members: Mapping[str, bytes | Path]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
        for name in sorted(members):
            info = zipfile.ZipInfo(name, date_time=_ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            source = members[name]
            if isinstance(source, bytes):
                archive.writestr(info, source)
                continue
            with (
                source.open("rb") as input_handle,
                archive.open(info, "w", force_zip64=True) as output_handle,
            ):
                _copy_stream(input_handle, output_handle)


def _copy_stream(source: IO[bytes], destination: IO[bytes]) -> None:
    while True:
        chunk = source.read(1024 * 1024)
        if not chunk:
            return
        destination.write(chunk)


def _validate_archive_members(infos: list[zipfile.ZipInfo]) -> None:
    if not infos or len(infos) > _MAX_ARCHIVE_MEMBERS:
        raise ROCrateValidationError("RO-Crate archive member count is invalid")
    names = [info.filename for info in infos]
    if names != sorted(names) or len(names) != len(set(names)):
        raise ROCrateValidationError("RO-Crate archive members must be sorted and unique")
    for info in infos:
        candidate = PurePosixPath(info.filename)
        mode = info.external_attr >> 16
        if (
            candidate.is_absolute()
            or not candidate.parts
            or ".." in candidate.parts
            or "\\" in info.filename
            or info.is_dir()
        ):
            raise ROCrateValidationError(f"unsafe RO-Crate archive member: {info.filename}")
        if info.compress_type != zipfile.ZIP_STORED:
            raise ROCrateValidationError("RO-Crate profile requires stored, uncompressed members")
        if mode and (stat.S_ISLNK(mode) or not stat.S_ISREG(mode)):
            raise ROCrateValidationError(f"non-regular RO-Crate archive member: {info.filename}")
    required = {METADATA_PATH, EXPORT_RECORD_PATH, f"{NATIVE_ROOT}audit.bundle.json"}
    missing = required - set(names)
    if missing:
        raise ROCrateValidationError(
            f"RO-Crate archive is missing required members: {sorted(missing)}"
        )


def _validate_metadata_and_members(
    metadata: Mapping[str, Any], infos: list[zipfile.ZipInfo]
) -> tuple[list[str], dict[str, Mapping[str, Any]]]:
    graph = metadata.get("@graph")
    if not isinstance(graph, list) or not graph:
        raise ROCrateValidationError("RO-Crate metadata graph is missing")
    entities: dict[str, Mapping[str, Any]] = {}
    for item in graph:
        if not isinstance(item, Mapping) or not isinstance(item.get("@id"), str):
            raise ROCrateValidationError("RO-Crate metadata contains a malformed entity")
        identifier = str(item["@id"])
        if identifier in entities:
            raise ROCrateValidationError("RO-Crate metadata entity identifiers are not unique")
        entities[identifier] = item
    descriptor = entities.get(METADATA_PATH)
    if descriptor != {
        "@id": METADATA_PATH,
        "@type": "CreativeWork",
        "about": {"@id": "./"},
        "conformsTo": {"@id": RO_CRATE_PROFILE},
        "description": "RO-Crate Metadata Descriptor (this file)",
    }:
        raise ROCrateValidationError("RO-Crate metadata descriptor is invalid")
    root = entities.get("./")
    if not isinstance(root, Mapping) or root.get("@type") != "Dataset":
        raise ROCrateValidationError("RO-Crate root Dataset is invalid")
    has_part = root.get("hasPart")
    if not isinstance(has_part, list) or not has_part:
        raise ROCrateValidationError("RO-Crate root hasPart inventory is missing")
    native_names: list[str] = []
    for reference in has_part:
        if not isinstance(reference, Mapping) or set(reference) != {"@id"}:
            raise ROCrateValidationError("RO-Crate root hasPart reference is malformed")
        name = reference.get("@id")
        if not isinstance(name, str) or not name.startswith(NATIVE_ROOT):
            raise ROCrateValidationError("RO-Crate payload must remain under native/")
        native_names.append(name)
    if native_names != sorted(native_names) or len(set(native_names)) != len(native_names):
        raise ROCrateValidationError("RO-Crate native payload references must be sorted and unique")
    expected_names = {METADATA_PATH, EXPORT_RECORD_PATH, *native_names}
    actual_names = {info.filename for info in infos}
    if actual_names != expected_names:
        raise ROCrateValidationError("RO-Crate archive member set does not match root hasPart")
    file_entities = {
        identifier: entity
        for identifier, entity in entities.items()
        if entity.get("@type") == "File"
    }
    if set(file_entities) != set(native_names):
        raise ROCrateValidationError("RO-Crate File entities do not match root hasPart")
    return native_names, file_entities


def _declared_metadata(metadata: Mapping[str, Any]) -> tuple[str, str, str, str]:
    graph = metadata.get("@graph")
    if not isinstance(graph, list):
        raise ROCrateValidationError("RO-Crate metadata graph is missing")
    entities = {
        str(item["@id"]): item
        for item in graph
        if isinstance(item, Mapping) and isinstance(item.get("@id"), str)
    }
    root = entities.get("./")
    if not isinstance(root, Mapping):
        raise ROCrateValidationError("RO-Crate root Dataset is missing")
    author_id = _reference_id(root.get("author"), "author")
    license_uri = _reference_id(root.get("license"), "license")
    author = entities.get(author_id)
    license_entity = entities.get(license_uri)
    if (
        not isinstance(author, Mapping)
        or author.get("@type") != "Person"
        or not isinstance(author.get("name"), str)
    ):
        raise ROCrateValidationError("RO-Crate declared author entity is invalid")
    if (
        not isinstance(license_entity, Mapping)
        or license_entity.get("@type") != "CreativeWork"
        or not isinstance(license_entity.get("name"), str)
    ):
        raise ROCrateValidationError("RO-Crate declared license entity is invalid")
    try:
        safe_author_id = _uri_reference(author_id, "author identifier", absolute=False)
        safe_author_name = _declared_text(str(author["name"]), "author name")
        safe_license_uri = _uri_reference(license_uri, "license URI", absolute=True)
        safe_license_name = _declared_text(str(license_entity["name"]), "license name")
    except ValueError as error:
        raise ROCrateValidationError(str(error)) from error
    return safe_author_id, safe_author_name, safe_license_uri, safe_license_name


def _reference_id(value: object, label: str) -> str:
    if (
        not isinstance(value, Mapping)
        or set(value) != {"@id"}
        or not isinstance(value.get("@id"), str)
    ):
        raise ROCrateValidationError(f"RO-Crate {label} reference is invalid")
    return str(value["@id"])


def _validate_native_audit(
    archive: zipfile.ZipFile,
    bundle: Mapping[str, Any],
    native_names: list[str],
    entries_by_name: Mapping[str, Mapping[str, Any]],
) -> None:
    manifests = bundle.get("storage_manifests")
    if (
        not isinstance(manifests, list)
        or len(manifests) != 1
        or not isinstance(manifests[0], Mapping)
    ):
        raise ROCrateValidationError("native audit requires exactly one storage manifest")
    manifest = manifests[0]
    extensions = manifest.get("extensions")
    entries = extensions.get("x-canonical-files") if isinstance(extensions, Mapping) else None
    if not isinstance(entries, list):
        raise ROCrateValidationError("native storage manifest inventory is missing")
    canonical_paths: list[str] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise ROCrateValidationError("native storage manifest entry is malformed")
        relative = entry.get("path")
        digest = entry.get("digest")
        size_bytes = entry.get("size_bytes")
        if (
            not isinstance(relative, str)
            or not isinstance(digest, str)
            or not isinstance(size_bytes, int)
        ):
            raise ROCrateValidationError("native storage manifest entry is malformed")
        name = f"{NATIVE_ROOT}{relative}"
        actual = entries_by_name.get(name)
        if not isinstance(actual, Mapping):
            raise ROCrateValidationError(f"native file is missing: {name}")
        if actual["digest"] != digest or actual["size_bytes"] != size_bytes:
            raise ROCrateValidationError(f"native file digest mismatch: {name}")
        canonical_paths.append(name)
    expected_native = {
        f"{NATIVE_ROOT}audit.bundle.json",
        f"{NATIVE_ROOT}report.html",
        f"{NATIVE_ROOT}{_STORAGE_MANIFEST_PATH}",
        *canonical_paths,
    }
    if set(native_names) != expected_native:
        raise ROCrateValidationError("native audit file set is incomplete or contains extras")
    manifest_payload = _read_control_member(archive, f"{NATIVE_ROOT}{_STORAGE_MANIFEST_PATH}")
    if manifest_payload != _json_bytes(dict(manifest)):
        raise ROCrateValidationError("native storage manifest JSONL does not match the bundle")

    lock_payload = _read_control_member(archive, f"{NATIVE_ROOT}semantic.lock.json")
    locked = _parse_canonical_object(lock_payload, "native/semantic.lock.json")
    lock_digest = locked.get("semantic_lock_digest")
    digest_input = dict(locked)
    digest_input.pop("semantic_lock_digest", None)
    if not isinstance(lock_digest, str) or semantic_digest(digest_input) != lock_digest:
        raise ROCrateValidationError("native semantic lock digest mismatch")
    if bundle.get("semantic_lock_digest") != lock_digest:
        raise ROCrateValidationError("native bundle does not bind the semantic lock")
    if bundle.get("audit_run_id") != locked.get("audit_run_id"):
        raise ROCrateValidationError("native bundle and semantic lock audit runs differ")

    expected_refs = _bundle_entity_refs(bundle)
    export_record = _parse_canonical_object(
        _read_control_member(archive, EXPORT_RECORD_PATH), EXPORT_RECORD_PATH
    )
    if export_record.get("entity_refs") != expected_refs:
        raise ROCrateValidationError("ROCrateExport entity references are incomplete")
    if export_record.get("audit_bundle_ref") != {
        "record_type": "audit_bundle",
        "record_id": bundle.get("bundle_id"),
    }:
        raise ROCrateValidationError("ROCrateExport does not reference the native bundle")


def _bundle_entity_refs(bundle: Mapping[str, Any]) -> list[dict[str, str]]:
    refs: set[tuple[str, str]] = {("audit_bundle", str(bundle["bundle_id"]))}
    for value in bundle.values():
        if not isinstance(value, list):
            continue
        for item in value:
            if not isinstance(item, Mapping) or not isinstance(item.get("record_type"), str):
                continue
            refs.add(record_identity(item))
    return [
        {"record_type": record_type, "record_id": record_id}
        for record_type, record_id in sorted(refs)
    ]


def _archive_file_entry(
    archive: zipfile.ZipFile, name: str, file_entity: Mapping[str, Any]
) -> dict[str, Any]:
    try:
        info = archive.getinfo(name)
    except KeyError as error:
        raise ROCrateValidationError(f"native file is missing: {name}") from error
    digest = hashlib.sha256()
    size_bytes = 0
    with archive.open(info, "r") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            size_bytes += len(chunk)
    entry = {"path": name, "digest": f"sha256:{digest.hexdigest()}", "size_bytes": size_bytes}
    if file_entity.get("identifier") != entry["digest"] or file_entity.get("contentSize") != str(
        size_bytes
    ):
        raise ROCrateValidationError(f"native file digest metadata mismatch: {name}")
    return entry


def _source_file_entry(name: str, path: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    size_bytes = 0
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            size_bytes += len(chunk)
    return {"path": name, "digest": f"sha256:{digest.hexdigest()}", "size_bytes": size_bytes}


def _read_control_member(archive: zipfile.ZipFile, name: str) -> bytes:
    try:
        info = archive.getinfo(name)
    except KeyError as error:
        raise ROCrateValidationError(f"RO-Crate archive member is missing: {name}") from error
    if info.file_size > _MAX_CONTROL_MEMBER_BYTES:
        raise ROCrateValidationError(f"RO-Crate control member exceeds the size limit: {name}")
    return archive.read(info)


def _parse_canonical_object(payload: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ROCrateValidationError(f"{label} is not valid UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise ROCrateValidationError(f"{label} must contain one JSON object")
    if payload != _json_bytes(value):
        raise ROCrateValidationError(f"{label} is not canonical JSON")
    return value


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} is unavailable or unsafe")
    try:
        value = json.loads(path.read_bytes())
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{label} is not valid UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise ValueError(f"{label} must contain one JSON object")
    return value


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (canonical_json(dict(value)) + "\n").encode("utf-8")


def _declared_text(value: str, label: str) -> str:
    normalized = value.strip()
    if (
        not normalized
        or len(normalized) > 512
        or any(ord(character) < 32 for character in normalized)
    ):
        raise ValueError(f"declared {label} is empty or unsafe")
    return normalized


def _uri_reference(value: str, label: str, *, absolute: bool) -> str:
    normalized = value.strip()
    if not normalized or any(character.isspace() for character in normalized):
        raise ValueError(f"declared {label} is not a safe URI reference")
    parsed = urlsplit(normalized)
    if absolute and not parsed.scheme:
        raise ValueError(f"declared {label} must be an absolute URI")
    if parsed.scheme and parsed.scheme.lower() not in {"http", "https", "urn"}:
        raise ValueError(f"declared {label} uses an unsupported URI scheme")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError(f"declared {label} must not contain credentials")
    if not absolute and not (parsed.scheme or normalized.startswith("#")):
        raise ValueError(f"declared {label} must be an absolute URI or fragment identifier")
    return normalized


def _reference_name(path: str) -> str:
    return path.removeprefix(NATIVE_ROOT)


def _file_description(path: str) -> str:
    relative = _reference_name(path)
    descriptions = {
        "audit.bundle.json": "Unchanged native sc-referee audit bundle.",
        "report.html": "Unchanged self-contained sc-referee HTML report.",
        "semantic.lock.json": "Unchanged native semantic lock.",
        _STORAGE_MANIFEST_PATH: "Unchanged native sc-referee storage manifest record.",
    }
    return descriptions.get(relative, "Unchanged native sc-referee canonical record file.")


def _media_type(path: str) -> str:
    if path.endswith(".jsonl"):
        return "application/x-ndjson"
    if path.endswith(".json"):
        return "application/json"
    if path.endswith(".html"):
        return "text/html"
    return "application/octet-stream"
