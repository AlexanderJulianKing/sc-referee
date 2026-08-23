from __future__ import annotations

import json
import os
import shutil
from dataclasses import fields
from pathlib import Path
from typing import Any

import pytest
from conftest import H5AD_PATH, SOURCE_PATH, StaticWorld1Case
from sc_referee_evaluation.audit_ladder.slice_c.core import SliceCRequestV1, canonical_frame, sha256
from sc_referee_evaluation.audit_ladder.slice_c.fixture import (
    FixtureCaptureError,
    capture_world1_fixture_context_v1,
)
from sc_referee_evaluation.audit_ladder.slice_c.repository import (
    RepositoryAuthenticationError,
    authenticate_world1_context_v1,
)
from sc_referee_evaluation.audit_ladder.slice_c.transaction import render_slice_c_report_v1

from sc_referee.controller import FrozenFileManifestInput, ManifestBoundFrozenInspectionContext


def _unchecked_replace(value: object, **changes: object) -> Any:
    clone = object.__new__(type(value))
    for field in fields(value):
        object.__setattr__(clone, field.name, changes.get(field.name, getattr(value, field.name)))
    return clone


def _manifest(raw: bytes, original: FrozenFileManifestInput) -> FrozenFileManifestInput:
    return FrozenFileManifestInput(
        file_manifest_ref=original.file_manifest_ref,
        canonical_jsonl_bytes=raw,
        manifest_digest=sha256(raw),
    )


def _mutated_contexts(
    case: StaticWorld1Case,
) -> list[tuple[str, ManifestBoundFrozenInspectionContext]]:
    context = case.context
    assert isinstance(context, ManifestBoundFrozenInspectionContext)
    manifest = context.file_manifest_input
    assert manifest is not None
    lines = manifest.canonical_jsonl_bytes.rstrip(b"\n").split(b"\n")
    first = json.loads(lines[0])
    second = json.loads(lines[1])
    traversal = dict(first)
    traversal["path"] = "../analysis.py"
    symlink = dict(first)
    symlink["entry_kind"] = "symlink"
    special = dict(first)
    special["entry_kind"] = "special"
    mismatch = dict(first)
    mismatch["byte_size"] = 1_014
    extra = dict(second)
    extra["path"] = "scanpy.py"

    manifest_cases = {
        "manifest-omission": lines[0] + b"\n",
        "manifest-duplicate": lines[0] + b"\n" + lines[0] + b"\n",
        "manifest-reorder": lines[1] + b"\n" + lines[0] + b"\n",
        "manifest-mismatch": canonical_frame(mismatch) + lines[1] + b"\n",
        "manifest-traversal": canonical_frame(traversal) + lines[1] + b"\n",
        "manifest-symlink": canonical_frame(symlink) + lines[1] + b"\n",
        "manifest-special": canonical_frame(special) + lines[1] + b"\n",
        "growth14-extra-omitted": lines[0] + b"\n" + lines[1] + b"\n" + canonical_frame(extra),
    }
    result = [
        (
            name,
            _unchecked_replace(context, file_manifest_input=_manifest(raw, manifest)),
        )
        for name, raw in manifest_cases.items()
    ]
    records = context.base_records
    materials = context.material_inputs
    result.extend(
        [
            ("record-omission", _unchecked_replace(context, base_records=records[:-1])),
            ("record-addition", _unchecked_replace(context, base_records=(*records, records[-1]))),
            (
                "record-duplicate",
                _unchecked_replace(
                    context, base_records=(records[0], records[1], records[1], *records[3:])
                ),
            ),
            ("material-omission", _unchecked_replace(context, material_inputs=materials[:1])),
            (
                "material-addition",
                _unchecked_replace(context, material_inputs=(*materials, materials[-1])),
            ),
            (
                "material-reorder",
                _unchecked_replace(context, material_inputs=tuple(reversed(materials))),
            ),
            (
                "material-content-mismatch",
                _unchecked_replace(
                    context,
                    material_inputs=(
                        _unchecked_replace(
                            materials[0],
                            content=b"x" + materials[0].content[1:],
                        ),
                        materials[1],
                    ),
                ),
            ),
            (
                "material-stale-digest",
                _unchecked_replace(
                    context,
                    material_inputs=(
                        _unchecked_replace(materials[0], content_digest="sha256:" + "0" * 64),
                        materials[1],
                    ),
                ),
            ),
            (
                "material-mutable-buffer",
                _unchecked_replace(
                    context,
                    material_inputs=(
                        _unchecked_replace(materials[0], content=bytearray(materials[0].content)),
                        materials[1],
                    ),
                ),
            ),
            (
                "material-swap",
                _unchecked_replace(
                    context,
                    material_inputs=(
                        _unchecked_replace(materials[0], content=materials[1].content),
                        _unchecked_replace(materials[1], content=materials[0].content),
                    ),
                ),
            ),
            (
                "snapshot-stale-ref",
                _unchecked_replace(context, snapshot_digest="sha256:" + "0" * 64),
            ),
        ]
    )
    return result


def test_parent_inventory_mutations_refuse_without_worker(
    static_world1_case: StaticWorld1Case,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    launches = 0

    def forbidden_launch(**_kwargs: object) -> object:
        nonlocal launches
        launches += 1
        raise AssertionError("inventory refusal reached worker launch")

    monkeypatch.setattr(
        "sc_referee_evaluation.audit_ladder.slice_c.transaction.run_isolated_worker_v1",
        forbidden_launch,
    )
    cases = _mutated_contexts(static_world1_case)
    for _name, context in cases:
        with pytest.raises(RepositoryAuthenticationError):
            authenticate_world1_context_v1(
                context,
                static_world1_case.request,
                static_world1_case.registry,
            )
        assert render_slice_c_report_v1(context, static_world1_case.request) == b""
    assert len(cases) == 19
    assert launches == 0


def _copy_fixture(root: Path) -> None:
    root.mkdir()
    shutil.copyfile(SOURCE_PATH, root / "analysis.py")
    shutil.copyfile(H5AD_PATH, root / "sc_reads.h5ad")


@pytest.mark.parametrize(
    ("candidate", "kind"),
    [
        ("scanpy.py", "file"),
        ("scanpy.pyc", "file"),
        ("scanpy.cpython-311-darwin.so", "file"),
        ("scanpy.abi3.so", "file"),
        ("scanpy.so", "file"),
        ("scanpy", "directory"),
        ("scanpy", "symlink"),
        ("scanpy", "special"),
    ],
)
def test_adjacent_import_candidates_and_nonregular_entries_refuse(
    tmp_path: Path,
    candidate: str,
    kind: str,
) -> None:
    root = tmp_path / "repository"
    _copy_fixture(root)
    target = root / candidate
    if kind == "file":
        target.write_bytes(b"candidate")
    elif kind == "directory":
        target.mkdir()
    elif kind == "symlink":
        target.symlink_to(root / "analysis.py")
    else:
        os.mkfifo(target)
    with pytest.raises(FixtureCaptureError):
        capture_world1_fixture_context_v1(root)


@pytest.mark.parametrize("selected", ["analysis.py", "sc_reads.h5ad"])
@pytest.mark.parametrize("kind", ["symlink", "directory", "special"])
def test_selected_fixture_nonregular_entries_refuse(
    tmp_path: Path,
    selected: str,
    kind: str,
) -> None:
    root = tmp_path / "repository"
    _copy_fixture(root)
    target = root / selected
    target.unlink()
    if kind == "symlink":
        target.symlink_to(root / ("sc_reads.h5ad" if selected == "analysis.py" else "analysis.py"))
    elif kind == "directory":
        target.mkdir()
    else:
        os.mkfifo(target)
    with pytest.raises(FixtureCaptureError):
        capture_world1_fixture_context_v1(root)


@pytest.mark.parametrize("omitted", ["analysis.py", "sc_reads.h5ad"])
def test_fixture_omission_refuses(tmp_path: Path, omitted: str) -> None:
    root = tmp_path / "repository"
    _copy_fixture(root)
    (root / omitted).unlink()
    with pytest.raises(FixtureCaptureError):
        capture_world1_fixture_context_v1(root)


def test_valid_but_stale_private_paths_refuse_without_worker(
    static_world1_case: StaticWorld1Case,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "sc_referee_evaluation.audit_ladder.slice_c.transaction.run_isolated_worker_v1",
        lambda **_kwargs: pytest.fail("stale request reached worker"),
    )
    request = SliceCRequestV1(
        source_path="old-analysis.py",
        h5ad_path="old-reads.h5ad",
        obs_column="animal_id",
    )
    assert render_slice_c_report_v1(static_world1_case.context, request) == b""
