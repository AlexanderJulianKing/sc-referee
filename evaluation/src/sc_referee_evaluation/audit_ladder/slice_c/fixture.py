"""Descriptor-relative constructor for the exact two-entry development fixture."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any, NoReturn, cast

from sc_referee.controller import FrozenFileManifestInput, ManifestBoundFrozenInspectionContext
from sc_referee.scientific_checks.core import FrozenBaseRecord, FrozenMaterialInput, RecordRef
from sc_referee_evaluation.audit_ladder.slice_c.core import sha256
from sc_referee_evaluation.audit_ladder.slice_c.repository import (
    load_registry_bundle_v1,
    world1_snapshot_record_v1,
)


class FixtureCaptureError(RuntimeError):
    """The live development fixture is not the exact reviewed two-entry repository."""


def _fail(message: str) -> NoReturn:
    raise FixtureCaptureError(message)


def _read_once(root_fd: int, name: str) -> bytes:
    before = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
    if not stat.S_ISREG(before.st_mode):
        _fail("fixture entry is not one regular file")
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=root_fd)
    try:
        opened = os.fstat(fd)
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            _fail("fixture entry changed during descriptor acquisition")
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
            _fail("fixture entry changed during capture")
        return b"".join(chunks)
    finally:
        os.close(fd)


def capture_world1_fixture_context_v1(root: Path) -> ManifestBoundFrozenInspectionContext:
    """Enumerate and capture exactly ``analysis.py`` and ``sc_reads.h5ad`` once."""

    if not isinstance(root, Path):
        _fail("fixture root has the wrong type")
    root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        root_before = os.fstat(root_fd)
        names = sorted(os.listdir(root_fd))
        if names != ["analysis.py", "sc_reads.h5ad"]:
            _fail("fixture inventory has an omission, addition, or reordering")
        source = _read_once(root_fd, names[0])
        h5ad = _read_once(root_fd, names[1])
        root_after = os.fstat(root_fd)
        if sorted(os.listdir(root_fd)) != names or (
            root_after.st_dev,
            root_after.st_ino,
            root_after.st_mtime_ns,
            root_after.st_ctime_ns,
        ) != (
            root_before.st_dev,
            root_before.st_ino,
            root_before.st_mtime_ns,
            root_before.st_ctime_ns,
        ):
            _fail("fixture inventory changed during capture")
    finally:
        os.close(root_fd)
    if (
        len(source) != 1_015
        or sha256(source)
        != "sha256:c5f3bb51457ace3e4b979b69739f212b9d0c7a12baba62033859d31f5b2ade18"
        or len(h5ad) != 330_008
        or sha256(h5ad) != "sha256:f94ddd1bc2c7d1d690d5c054caf924a2c531a0e7d191da9ca7a7b786fee0e887"
    ):
        _fail("fixture byte identity differs")
    registry = load_registry_bundle_v1()
    world = registry.protocol.get("world1_repository")
    if type(world) is not dict:
        _fail("world-1 repository registry is unavailable")
    file_wrappers = world.get("file_record_preimages")
    asset_wrappers = world.get("asset_identity_preimages")
    if type(file_wrappers) is not list or type(asset_wrappers) is not list:
        _fail("world-1 record preimages are unavailable")
    try:
        files = [json.loads(cast(dict[str, Any], wrapper)["utf8"]) for wrapper in file_wrappers]
        assets = [json.loads(cast(dict[str, Any], wrapper)["utf8"]) for wrapper in asset_wrappers]
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise FixtureCaptureError("world-1 record preimage parsing failed") from error
    snapshot_ref = RecordRef("repository_snapshot", cast(str, world["snapshot_ref"]))
    records = [FrozenBaseRecord.from_record(snapshot_ref, world1_snapshot_record_v1())]
    materials: list[FrozenMaterialInput] = []
    for file_value, asset_value, content in zip(files, assets, (source, h5ad), strict=True):
        file_ref = RecordRef("file_record", cast(str, file_value["file_record_id"]))
        asset_ref = RecordRef("asset_identity", cast(str, asset_value["asset_identity_id"]))
        records.extend(
            (
                FrozenBaseRecord.from_record(file_ref, file_value),
                FrozenBaseRecord.from_record(asset_ref, asset_value),
            )
        )
        materials.append(
            FrozenMaterialInput(
                path=cast(str, file_value["path"]),
                file_ref=file_ref,
                asset_identity_ref=asset_ref,
                content=content,
                content_digest=cast(str, asset_value["identity_evidence"]["digest"]),
            )
        )
    manifest = cast(dict[str, Any], world["file_manifest"])
    return ManifestBoundFrozenInspectionContext(
        snapshot_digest=cast(str, cast(dict[str, Any], world["snapshot_identity"])["sha256"]),
        selected_surface_ref=snapshot_ref,
        selected_artifact_ref=snapshot_ref,
        documents=(),
        base_records=tuple(records),
        material_inputs=tuple(materials),
        file_manifest_input=FrozenFileManifestInput(
            file_manifest_ref=cast(str, manifest["file_manifest_ref"]),
            canonical_jsonl_bytes=cast(str, manifest["utf8"]).encode("utf-8", "strict"),
            manifest_digest=cast(str, manifest["sha256"]),
        ),
    )


__all__ = ["FixtureCaptureError", "capture_world1_fixture_context_v1"]
