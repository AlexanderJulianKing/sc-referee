from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from sc_referee.core.errors import RecordValidationError
from sc_referee.records.schema_registry import LocalSchemaRegistry
from scripts.build_project_execution_work_item_schema_release import (
    RELEASE_VERSION,
    SOURCE_ADRS,
    build_release,
)


def _load(root: Path, name: str) -> dict[str, object]:
    return json.loads((root / "examples" / name).read_text(encoding="utf-8"))


def _release(tmp_path: Path) -> tuple[Path, LocalSchemaRegistry]:
    root = tmp_path / "schemas-v0.14.0"
    build_release(root)
    return root, LocalSchemaRegistry(root)


def _invalid(registry: LocalSchemaRegistry, value: dict[str, object]) -> None:
    with pytest.raises(RecordValidationError):
        registry.validate(value)


def test_committed_v014_release_is_accepted_and_complete(project_root: Path) -> None:
    release = project_root / "reference" / "schemas-v0.14.0"
    status = json.loads((release / "RELEASE_STATUS.json").read_text(encoding="utf-8"))
    assert status == {
        "accepted": True,
        "baseline_version": "0.13.0",
        "public_release": True,
        "release_version": "0.14.0",
        "source_adrs": SOURCE_ADRS,
    }
    assert RELEASE_VERSION == "0.14.0"
    assert LocalSchemaRegistry(release).validate_example_directory() == 71


def test_v014_manifest_binds_every_release_file(project_root: Path) -> None:
    release = project_root / "reference" / "schemas-v0.14.0"
    manifest = {}
    for line in (release / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", maxsplit=1)
        manifest[relative] = digest
    actual = {
        path.relative_to(release).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in release.rglob("*")
        if path.is_file()
        and path.name != "MANIFEST.sha256"
        and not any(part.startswith(".") or part == "__pycache__" for part in path.parts)
    }
    assert manifest == actual


def test_v014_builder_is_reproducible_and_preserves_v013(
    project_root: Path, tmp_path: Path
) -> None:
    baseline_manifest = project_root / "reference" / "schemas-v0.13.0" / "MANIFEST.sha256"
    before = baseline_manifest.read_bytes()
    output = tmp_path / "schemas-v0.14.0"
    assert build_release(output) == 71
    committed = project_root / "reference" / "schemas-v0.14.0"
    generated_files = {
        path.relative_to(output).as_posix(): path.read_bytes()
        for path in output.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }
    committed_files = {
        path.relative_to(committed).as_posix(): path.read_bytes()
        for path in committed.rglob("*")
        if path.is_file()
        and not any(part.startswith(".") or part == "__pycache__" for part in path.parts)
    }
    assert generated_files == committed_files
    assert baseline_manifest.read_bytes() == before


def test_project_execution_work_item_is_a_non_authorizing_controller_request(
    tmp_path: Path,
) -> None:
    root, registry = _release(tmp_path)
    item = _load(root, "work-item.project-execution.example.json")

    registry.validate(item)
    assert item["kind"] == "project_execution"
    assert item["status"] == "awaiting_authorization"
    assert item["scheduling"]["execution_privilege"] == "project_code_execution"  # type: ignore[index]
    assert item["packet"]["packet_kind"] == "project_execution_request_v1"  # type: ignore[index]
    assert item["packet"]["policy"]["launch_authorized"] is False  # type: ignore[index]


@pytest.mark.parametrize(
    ("mutation",),
    [
        (lambda item: item.update(status="ready"),),
        (
            lambda item: item["scheduling"].update(execution_privilege="safe_inspection"),  # type: ignore[union-attr]
        ),
        (lambda item: item["packet"].update(packet_kind="semantic_or_auditor_work_v1"),),  # type: ignore[union-attr]
        (lambda item: item["packet"].update(prompt_template_id="prompt:invented"),),  # type: ignore[union-attr]
        (lambda item: item["packet"].update(allowed_output_paths=["../escape.json"]),),  # type: ignore[union-attr]
        (lambda item: item["packet"]["policy"].update(launch_authorized=True),),  # type: ignore[index,union-attr]
    ],
)
def test_project_execution_work_item_rejects_contradictory_or_broadenable_state(
    tmp_path: Path, mutation: object
) -> None:
    root, registry = _release(tmp_path)
    item = _load(root, "work-item.project-execution.example.json")
    mutation(item)  # type: ignore[operator]
    _invalid(registry, item)


def test_semantic_work_item_cannot_use_project_execution_packet(tmp_path: Path) -> None:
    root, registry = _release(tmp_path)
    semantic = _load(root, "work-item.ready.example.json")
    execution = _load(root, "work-item.project-execution.example.json")
    semantic["packet"] = copy.deepcopy(execution["packet"])
    _invalid(registry, semantic)


def test_authorization_requires_explicit_work_item_binding_state_and_digest(
    tmp_path: Path,
) -> None:
    root, registry = _release(tmp_path)
    authorization = _load(root, "project-execution-authorization.example.json")
    registry.validate(authorization)

    missing = copy.deepcopy(authorization)
    del missing["scope"]["work_item_semantic_digest"]  # type: ignore[index]
    _invalid(registry, missing)

    legacy = copy.deepcopy(authorization)
    legacy["scope"]["work_item_binding_status"] = "legacy_work_item_semantics_unavailable"  # type: ignore[index]
    legacy["scope"]["work_item_semantic_digest"] = None  # type: ignore[index]
    legacy["scope"]["purpose"] = None  # type: ignore[index]
    legacy["scope"]["target_refs"] = None  # type: ignore[index]
    registry.validate(legacy)

    contradictory = copy.deepcopy(legacy)
    contradictory["scope"]["work_item_semantic_digest"] = "sha256:" + "9" * 64  # type: ignore[index]
    _invalid(registry, contradictory)
