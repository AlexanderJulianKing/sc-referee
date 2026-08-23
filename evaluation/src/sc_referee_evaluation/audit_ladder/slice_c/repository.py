"""Growth-14-style manifest and immutable-material authentication for Slice C."""

from __future__ import annotations

import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, NoReturn, cast

from sc_referee.controller import FrozenFileManifestInput, ManifestBoundFrozenInspectionContext
from sc_referee.scientific_checks.core import FrozenBaseRecord, FrozenMaterialInput, RecordRef
from sc_referee_evaluation.audit_ladder.slice_c.core import (
    SliceCRequestV1,
    canonical_json_bytes,
    sha256,
    validate_slice_c_request,
)

_PROTOCOL_NAME: Final = "audit-report-ladder-slice-c-worker-protocol-v1.json"
_RENDERER_NAME: Final = "audit-report-ladder-slice-c-renderer-registry-v2.json"
_ROOT_SEAL_NAME: Final = "audit-report-ladder-slice-c-runtime-root-seal-v1.json"
_PROTOCOL_IDENTITY: Final = (
    16_110,
    "sha256:9446a9c727342487ff78dc1907b588ebcab9ce51a144054baeb2fd4c8df8641b",
)
_RENDERER_IDENTITY: Final = (
    1_801,
    "sha256:13d55e0ce00a7a916f7d5797fd80f4d66993b2ac0f87b51d2e76829967488945",
)
_ROOT_SEAL_IDENTITY: Final = (
    960,
    "sha256:07dd8873f3b5ce4b94ca4b536bb2cbaeafc7f9be42dad2f16b1be495d4fba4e6",
)
_SNAPSHOT_REF: Final = "snapshot:c92d684f49901b6a1e6a"
_SNAPSHOT_DIGEST: Final = "sha256:c92d684f49901b6a1e6ad534061f9e0a000f75738d39307abfe6e55c5eaedb5c"
_SOURCE_PATH: Final = "analysis.py"
_H5AD_PATH: Final = "sc_reads.h5ad"
_SOURCE_DIGEST: Final = "sha256:c5f3bb51457ace3e4b979b69739f212b9d0c7a12baba62033859d31f5b2ade18"
_H5AD_DIGEST: Final = "sha256:f94ddd1bc2c7d1d690d5c054caf924a2c531a0e7d191da9ca7a7b786fee0e887"


class RepositoryAuthenticationError(RuntimeError):
    """The frozen capability is not the exact world-1 repository transaction."""


@dataclass(frozen=True, slots=True)
class RegistryBundleV1:
    protocol_bytes: bytes
    protocol: dict[str, Any]
    renderer_bytes: bytes
    renderer: dict[str, Any]
    root_seal_bytes: bytes
    root_seal: dict[str, Any]


@dataclass(frozen=True, slots=True)
class CapturedWorld1MaterialsV1:
    """The exact selected bytes and independently reconstructed repository request."""

    source_bytes: bytes
    h5ad_bytes: bytes
    source_digest: str
    h5ad_digest: str
    snapshot_ref: str
    snapshot_digest: str
    source_file_ref: str
    h5ad_file_ref: str
    repository_request: dict[str, Any]


def _fail(message: str) -> NoReturn:
    raise RepositoryAuthenticationError(message)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("duplicate JSON member")
        result[key] = value
    return result


def _parse_canonical_object(raw: bytes, *, terminal_lf: bool) -> dict[str, Any]:
    content = raw[:-1] if terminal_lf and raw.endswith(b"\n") else raw
    if terminal_lf and (not raw.endswith(b"\n") or raw.endswith(b"\n\n") or b"\r" in raw):
        _fail("resource terminal framing differs")
    try:
        value = json.loads(content, object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise RepositoryAuthenticationError("resource JSON parsing failed") from error
    if type(value) is not dict or canonical_json_bytes(value) != content:
        _fail("resource is not one canonical object")
    return cast(dict[str, Any], value)


def _resource_root() -> Path:
    return (
        Path(__file__).resolve().parents[5]
        / "evaluation"
        / "development"
        / "audit-report-ladder"
        / "world1"
        / "resources"
    )


def _read_resource(name: str, identity: tuple[int, str]) -> tuple[bytes, dict[str, Any]]:
    path = _resource_root() / name
    before = os.stat(path, follow_symlinks=False)
    if not stat.S_ISREG(before.st_mode):
        _fail("development resource is not one regular file")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        opened = os.fstat(fd)
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            _fail("development resource changed during descriptor acquisition")
        chunks: list[bytes] = []
        while True:
            block = os.read(fd, 1_048_576)
            if not block:
                break
            chunks.append(block)
        after = os.fstat(fd)
        if (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ) != (
            opened.st_dev,
            opened.st_ino,
            opened.st_size,
            opened.st_mtime_ns,
            opened.st_ctime_ns,
        ):
            _fail("development resource changed during authentication")
    finally:
        os.close(fd)
    raw = b"".join(chunks)
    if len(raw) != identity[0] or sha256(raw) != identity[1]:
        _fail("development resource identity differs")
    return raw, _parse_canonical_object(raw, terminal_lf=True)


def load_registry_bundle_v1() -> RegistryBundleV1:
    """Authenticate all three copied authority resources before use."""

    protocol_bytes, protocol = _read_resource(_PROTOCOL_NAME, _PROTOCOL_IDENTITY)
    renderer_bytes, renderer = _read_resource(_RENDERER_NAME, _RENDERER_IDENTITY)
    root_seal_bytes, root_seal = _read_resource(_ROOT_SEAL_NAME, _ROOT_SEAL_IDENTITY)
    if (
        protocol.get("schema") != "slice-c-worker-protocol-registry-v1"
        or renderer.get("schema") != "slice-c-renderer-registry-v2"
        or root_seal.get("schema") != "slice-c-runtime-root-seal-v1"
    ):
        _fail("development resource schema differs")
    return RegistryBundleV1(
        protocol_bytes=protocol_bytes,
        protocol=protocol,
        renderer_bytes=renderer_bytes,
        renderer=renderer,
        root_seal_bytes=root_seal_bytes,
        root_seal=root_seal,
    )


def world1_snapshot_record_v1() -> dict[str, Any]:
    """Return the closed snapshot base-record used by the fixture constructor."""

    return {
        "extensions": {
            "x-material-full-digest-paths": [_SOURCE_PATH, _H5AD_PATH],
            "x-material-input-identities": [
                {"path": _SOURCE_PATH, "tier": "full_digest"},
                {"path": _H5AD_PATH, "tier": "full_digest"},
            ],
        },
        "file_manifest_ref": "observed/files.jsonl",
        "immutability": True,
        "record_type": "repository_snapshot",
        "snapshot_digest": _SNAPSHOT_DIGEST,
        "snapshot_id": _SNAPSHOT_REF,
    }


def _parse_base_record(record: FrozenBaseRecord) -> dict[str, Any]:
    if (
        type(record) is not FrozenBaseRecord
        or sha256(record.canonical_payload) != record.payload_digest
    ):
        _fail("frozen base-record identity differs")
    value = _parse_canonical_object(record.canonical_payload, terminal_lf=False)
    expected_ref = {"record_id": record.ref.record_id, "record_type": record.ref.record_type}
    identity_member = {
        "repository_snapshot": "snapshot_id",
        "file_record": "file_record_id",
        "asset_identity": "asset_identity_id",
    }.get(record.ref.record_type)
    if identity_member is None or value.get(identity_member) != expected_ref["record_id"]:
        _fail("base-record reference does not bind its payload")
    return value


def _exact_text_object(value: object) -> tuple[bytes, dict[str, Any]]:
    if type(value) is not dict or set(value) != {"byte_size", "sha256", "utf8"}:
        _fail("preimage wrapper member set differs")
    text = value.get("utf8")
    if type(text) is not str:
        _fail("preimage wrapper text type differs")
    raw = text.encode("utf-8", "strict")
    if value.get("byte_size") != len(raw) or value.get("sha256") != sha256(raw):
        _fail("preimage wrapper claims differ")
    return raw, _parse_canonical_object(raw, terminal_lf=False)


def _record_ref(value: str, record_type: str) -> RecordRef:
    return RecordRef(record_type, value)


def _require_context_shell(context: ManifestBoundFrozenInspectionContext) -> None:
    if type(context) is not ManifestBoundFrozenInspectionContext:
        _fail("context is not the exact manifest-bound capability type")
    snapshot_ref = _record_ref(_SNAPSHOT_REF, "repository_snapshot")
    if (
        context.snapshot_digest != _SNAPSHOT_DIGEST
        or context.selected_surface_ref != snapshot_ref
        or context.selected_artifact_ref != snapshot_ref
        or type(context.documents) is not tuple
        or context.documents
        or type(context.shared_derivations) is not tuple
        or context.shared_derivations
        or context.scope_join_graph is not None
    ):
        _fail("context shell differs from the closed fixture capability")


def authenticate_world1_context_v1(
    context: ManifestBoundFrozenInspectionContext,
    request: SliceCRequestV1,
    registry: RegistryBundleV1,
) -> CapturedWorld1MaterialsV1:
    """Authenticate the complete inventory/record/material bijection and capture bytes."""

    validate_slice_c_request(request)
    _require_context_shell(context)
    world = registry.protocol.get("world1_repository")
    if type(world) is not dict:
        _fail("protocol registry lacks the world-1 repository")
    manifest = context.file_manifest_input
    expected_manifest = world.get("file_manifest")
    if type(manifest) is not FrozenFileManifestInput or type(expected_manifest) is not dict:
        _fail("frozen file manifest is unavailable")
    expected_manifest_raw = expected_manifest.get("utf8")
    if type(expected_manifest_raw) is not str:
        _fail("registry manifest preimage is unavailable")
    manifest_raw = expected_manifest_raw.encode("utf-8", "strict")
    if (
        manifest.file_manifest_ref != expected_manifest.get("file_manifest_ref")
        or manifest.canonical_jsonl_bytes != manifest_raw
        or manifest.manifest_digest != expected_manifest.get("sha256")
        or expected_manifest.get("byte_size") != len(manifest_raw)
        or expected_manifest.get("entry_count") != 2
        or sha256(manifest_raw) != expected_manifest.get("sha256")
    ):
        _fail("file manifest identity differs")
    if not manifest_raw.endswith(b"\n") or manifest_raw.endswith(b"\n\n") or b"\r" in manifest_raw:
        _fail("file manifest framing differs")
    manifest_lines = manifest_raw[:-1].split(b"\n")
    if len(manifest_lines) != 2:
        _fail("file manifest inventory count differs")
    manifest_values = [_parse_canonical_object(line, terminal_lf=False) for line in manifest_lines]
    if [value.get("path") for value in manifest_values] != [_SOURCE_PATH, _H5AD_PATH]:
        _fail("file manifest ordering or inventory differs")

    base_records = context.base_records
    if type(base_records) is not tuple or len(base_records) != 5:
        _fail("base-record inventory count differs")
    parsed: dict[RecordRef, tuple[FrozenBaseRecord, dict[str, Any]]] = {}
    for record in base_records:
        if record.ref in parsed:
            _fail("duplicate base-record reference")
        parsed[record.ref] = (record, _parse_base_record(record))
    snapshot_ref = _record_ref(_SNAPSHOT_REF, "repository_snapshot")
    snapshot_pair = parsed.get(snapshot_ref)
    if snapshot_pair is None or snapshot_pair[1] != world1_snapshot_record_v1():
        _fail("snapshot record differs")

    record_wrappers = world.get("file_record_preimages")
    asset_wrappers = world.get("asset_identity_preimages")
    frozen_wrappers = world.get("frozen_material_preimages")
    selected_refs = world.get("selected_material_refs")
    if (
        type(record_wrappers) is not list
        or len(record_wrappers) != 2
        or type(asset_wrappers) is not list
        or len(asset_wrappers) != 2
        or type(frozen_wrappers) is not list
        or len(frozen_wrappers) != 2
        or type(selected_refs) is not dict
    ):
        _fail("world-1 preimage registry shape differs")
    expected_file_values: list[dict[str, Any]] = []
    expected_asset_values: list[dict[str, Any]] = []
    expected_frozen_values: list[dict[str, Any]] = []
    for wrapper in record_wrappers:
        _raw, value = _exact_text_object(wrapper)
        expected_file_values.append(value)
    for wrapper in asset_wrappers:
        _raw, value = _exact_text_object(wrapper)
        expected_asset_values.append(value)
    for wrapper in frozen_wrappers:
        _raw, value = _exact_text_object(wrapper)
        expected_frozen_values.append(value)
    if expected_file_values != manifest_values:
        _fail("manifest and file-record preimages are not bijective")

    expected_refs: set[RecordRef] = {snapshot_ref}
    for file_value, asset_value in zip(expected_file_values, expected_asset_values, strict=True):
        file_ref = _record_ref(cast(str, file_value["file_record_id"]), "file_record")
        asset_ref = _record_ref(cast(str, asset_value["asset_identity_id"]), "asset_identity")
        expected_refs.update({file_ref, asset_ref})
        if parsed.get(file_ref, (None, None))[1] != file_value:
            _fail("file-record payload differs")
        if parsed.get(asset_ref, (None, None))[1] != asset_value:
            _fail("asset-identity payload differs")
        if (
            file_value.get("asset_identity_ref") != asset_ref.to_dict()
            or asset_value.get("asset_ref") != file_ref.to_dict()
            or file_value.get("snapshot_ref") != snapshot_ref.to_dict()
        ):
            _fail("file/asset/snapshot join differs")
    if set(parsed) != expected_refs:
        _fail("base-record set has an omission or addition")

    materials = context.material_inputs
    if type(materials) is not tuple or len(materials) != 2:
        _fail("selected-material inventory differs")
    if [material.path for material in materials] != [_SOURCE_PATH, _H5AD_PATH]:
        _fail("selected-material ordering differs")
    captured: list[bytes] = []
    for index, material in enumerate(materials):
        if type(material) is not FrozenMaterialInput or type(material.content) is not bytes:
            _fail("selected material has the wrong type")
        expected_file = expected_file_values[index]
        expected_asset = expected_asset_values[index]
        expected_frozen = expected_frozen_values[index]
        content = material.content
        digest = sha256(content)
        if (
            material.path != expected_frozen.get("path")
            or material.file_ref.to_dict() != expected_frozen.get("file_ref")
            or material.asset_identity_ref.to_dict() != expected_frozen.get("asset_identity_ref")
            or len(content) != expected_frozen.get("byte_size")
            or digest != expected_frozen.get("sha256")
            or material.content_digest != digest
            or expected_file.get("byte_size") != len(content)
            or expected_asset.get("identity_evidence", {}).get("digest") != digest
        ):
            _fail("selected immutable material join differs")
        frozen_preimage = canonical_json_bytes(expected_frozen)
        material_ref = "material:" + sha256(frozen_preimage)[7:27]
        role = "source" if index == 0 else "h5ad"
        if selected_refs.get(role) != material_ref:
            _fail("selected material reference formula differs")
        captured.append(content)

    snapshot_wrapper = world.get("snapshot_identity")
    snapshot_raw, snapshot_identity = _exact_text_object(snapshot_wrapper)
    derived_identity = {
        "files": [
            {
                "byte_size": len(captured[0]),
                "path": _SOURCE_PATH,
                "schema": "slice-c-material-identity-v1",
                "sha256": sha256(captured[0]),
            },
            {
                "byte_size": len(captured[1]),
                "path": _H5AD_PATH,
                "schema": "slice-c-material-identity-v1",
                "sha256": sha256(captured[1]),
            },
        ],
        "schema": "slice-c-snapshot-identity-v1",
    }
    if (
        snapshot_identity != derived_identity
        or sha256(snapshot_raw) != _SNAPSHOT_DIGEST
        or world.get("snapshot_ref") != _SNAPSHOT_REF
        or "snapshot:" + sha256(snapshot_raw)[7:27] != _SNAPSHOT_REF
    ):
        _fail("snapshot identity preimage or reference differs")
    source_file_ref = cast(str, expected_file_values[0]["file_record_id"])
    h5ad_file_ref = cast(str, expected_file_values[1]["file_record_id"])
    for index, (file_value, material) in enumerate(
        zip(expected_file_values, materials, strict=True)
    ):
        identity_preimage = canonical_json_bytes(derived_identity["files"][index])
        expected_ref = "file:" + sha256(identity_preimage)[7:27]
        if (
            file_value.get("file_record_id") != expected_ref
            or material.file_ref.record_id != expected_ref
        ):
            _fail("file reference formula differs")

    repository_request = {
        "file_manifest": expected_manifest,
        "file_records": record_wrappers,
        "selected_materials": {
            "h5ad": {
                "asset_identity": asset_wrappers[1],
                "frozen_material": frozen_wrappers[1],
                "material_ref": selected_refs["h5ad"],
            },
            "source": {
                "asset_identity": asset_wrappers[0],
                "frozen_material": frozen_wrappers[0],
                "material_ref": selected_refs["source"],
            },
        },
        "snapshot_identity": snapshot_wrapper,
        "snapshot_ref": _SNAPSHOT_REF,
    }
    if set(repository_request) != set(registry.protocol["request"]["repository_members"]):
        _fail("repository worker-request member set differs")
    if request.source_path not in {_SOURCE_PATH} or request.h5ad_path not in {_H5AD_PATH}:
        _fail("requested selected paths are unavailable")
    return CapturedWorld1MaterialsV1(
        source_bytes=captured[0],
        h5ad_bytes=captured[1],
        source_digest=_SOURCE_DIGEST,
        h5ad_digest=_H5AD_DIGEST,
        snapshot_ref=_SNAPSHOT_REF,
        snapshot_digest=_SNAPSHOT_DIGEST,
        source_file_ref=source_file_ref,
        h5ad_file_ref=h5ad_file_ref,
        repository_request=repository_request,
    )


__all__ = [
    "CapturedWorld1MaterialsV1",
    "RegistryBundleV1",
    "RepositoryAuthenticationError",
    "authenticate_world1_context_v1",
    "load_registry_bundle_v1",
    "world1_snapshot_record_v1",
]
