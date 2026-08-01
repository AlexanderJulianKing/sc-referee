from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from sc_referee.core.errors import RecordValidationError
from sc_referee.records.schema_registry import LocalSchemaRegistry
from scripts.build_execution_schema_release import RELEASE_VERSION, SOURCE_ADRS, build_release


def _load(release: Path, name: str) -> dict[str, object]:
    value = json.loads((release / "examples" / name).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_committed_execution_release_is_accepted_exact_v0130(project_root: Path) -> None:
    release = project_root / "reference" / "schemas-v0.13.0"
    status = json.loads((release / "RELEASE_STATUS.json").read_text(encoding="utf-8"))
    assert status == {
        "accepted": True,
        "baseline_version": "0.12.0",
        "public_release": True,
        "release_version": "0.13.0",
        "source_adrs": SOURCE_ADRS,
    }
    assert RELEASE_VERSION == "0.13.0"
    assert LocalSchemaRegistry(release).validate_example_directory() == 70


def test_execution_release_manifest_binds_every_file(project_root: Path) -> None:
    release = project_root / "reference" / "schemas-v0.13.0"
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


def test_execution_release_builder_is_reproducible_and_preserves_v0120(
    project_root: Path, tmp_path: Path
) -> None:
    baseline_manifest = project_root / "reference" / "schemas-v0.12.0" / "MANIFEST.sha256"
    before = baseline_manifest.read_bytes()
    output = tmp_path / "schemas-v0.13.0"
    assert build_release(output) == 70
    committed = project_root / "reference" / "schemas-v0.13.0"
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


def test_authorization_scope_is_closed_and_network_denied(project_root: Path) -> None:
    release = project_root / "reference" / "schemas-v0.13.0"
    registry = LocalSchemaRegistry(release)
    authorization = _load(release, "project-execution-authorization.example.json")
    registry.validate(authorization)

    mutation = copy.deepcopy(authorization)
    mutation["network_policy"] = "allowed"
    with pytest.raises(RecordValidationError):
        registry.validate(mutation)

    mutation = copy.deepcopy(authorization)
    mutation["scope"]["allowed_output_paths"] = ["../escape"]  # type: ignore[index]
    with pytest.raises(RecordValidationError):
        registry.validate(mutation)

    mutation = copy.deepcopy(authorization)
    mutation["acknowledgements"]["project_code_is_untrusted"] = False  # type: ignore[index]
    with pytest.raises(RecordValidationError):
        registry.validate(mutation)


def test_supported_capability_requires_complete_effective_probe(project_root: Path) -> None:
    release = project_root / "reference" / "schemas-v0.13.0"
    registry = LocalSchemaRegistry(release)
    capability = _load(release, "sandbox-capability.example.json")
    registry.validate(capability)

    capability["capability_evidence_status"] = "legacy_probe_projection_unavailable"
    with pytest.raises(RecordValidationError):
        registry.validate(capability)

    capability = _load(release, "sandbox-capability.example.json")
    capability["capability_evidence"]["effective_controls"][  # type: ignore[index]
        "writable_bytes_enforced"
    ] = False
    with pytest.raises(RecordValidationError):
        registry.validate(capability)


def test_project_execution_requires_authorization_and_consumption(project_root: Path) -> None:
    release = project_root / "reference" / "schemas-v0.13.0"
    registry = LocalSchemaRegistry(release)
    execution = _load(release, "execution.project-workflow.example.json")
    registry.validate(execution)

    execution["project_execution"] = None
    with pytest.raises(RecordValidationError):
        registry.validate(execution)

    execution = _load(release, "execution.project-workflow.example.json")
    execution["project_execution"]["consumption"]["disposition"] = "claimed"  # type: ignore[index]
    with pytest.raises(RecordValidationError):
        registry.validate(execution)


def test_audit_bundle_requires_authorization_collection(project_root: Path) -> None:
    release = project_root / "reference" / "schemas-v0.13.0"
    registry = LocalSchemaRegistry(release)
    bundle = _load(release, "audit-bundle.example.json")
    registry.validate(bundle)
    bundle.pop("project_execution_authorizations")
    with pytest.raises(RecordValidationError):
        registry.validate(bundle)
