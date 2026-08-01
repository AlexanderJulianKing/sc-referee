from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from sc_referee.core.errors import RecordValidationError
from sc_referee.records.schema_registry import LocalSchemaRegistry
from scripts.build_static_qualification_schema_release import (
    RELEASE_VERSION,
    SOURCE_ADRS,
    build_release,
)


def _load(root: Path, name: str) -> dict[str, object]:
    return json.loads((root / "examples" / name).read_text(encoding="utf-8"))


def _release(tmp_path: Path) -> tuple[Path, LocalSchemaRegistry]:
    root = tmp_path / "schemas-v0.15.0"
    build_release(root)
    return root, LocalSchemaRegistry(root)


def _invalid(registry: LocalSchemaRegistry, value: dict[str, object]) -> None:
    with pytest.raises(RecordValidationError):
        registry.validate(value)


def test_committed_v015_release_is_accepted_and_complete(project_root: Path) -> None:
    release = project_root / "reference" / "schemas-v0.15.0"
    status = json.loads((release / "RELEASE_STATUS.json").read_text(encoding="utf-8"))
    assert status == {
        "accepted": True,
        "baseline_version": "0.14.0",
        "public_release": True,
        "release_version": "0.15.0",
        "source_adrs": SOURCE_ADRS,
    }
    assert RELEASE_VERSION == "0.15.0"
    assert LocalSchemaRegistry(release).validate_example_directory() == 75


def test_v015_manifest_binds_every_release_file(project_root: Path) -> None:
    release = project_root / "reference" / "schemas-v0.15.0"
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


def test_v015_builder_is_reproducible_and_preserves_v014(
    project_root: Path, tmp_path: Path
) -> None:
    baseline_manifest = project_root / "reference" / "schemas-v0.14.0" / "MANIFEST.sha256"
    before = baseline_manifest.read_bytes()
    output = tmp_path / "schemas-v0.15.0"
    assert build_release(output) == 75
    committed = project_root / "reference" / "schemas-v0.15.0"
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


@pytest.mark.parametrize(
    "name",
    ["benchmark-fixture.static-good.example.json", "benchmark-fixture.static-hard.example.json"],
)
def test_static_control_is_nonexecuting_and_has_one_bound_proof(tmp_path: Path, name: str) -> None:
    root, registry = _release(tmp_path)
    fixture = _load(root, name)
    registry.validate(fixture)
    assert fixture["execution_evidence"] == "not_executed"
    inputs = fixture["proof_evidence"]["public_inputs"]  # type: ignore[index]
    assert inputs["environments"] == []
    assert inputs["executions"] == []
    assert inputs["sandbox_capabilities"] == []
    assert len(inputs["static_qualification_proofs"]) == 1

    for claimed in ("clean_environment_executed", "documented_external_execution"):
        invalid = copy.deepcopy(fixture)
        invalid["execution_evidence"] = claimed
        _invalid(registry, invalid)


def test_static_and_legacy_fixture_proof_branches_do_not_cross(tmp_path: Path) -> None:
    root, registry = _release(tmp_path)
    static = _load(root, "benchmark-fixture.static-good.example.json")
    legacy = _load(root, "benchmark-fixture.example.json")

    crossed_static = copy.deepcopy(static)
    crossed_static["proof_evidence"] = copy.deepcopy(legacy["proof_evidence"])
    _invalid(registry, crossed_static)

    crossed_legacy = copy.deepcopy(legacy)
    crossed_legacy["proof_evidence"] = copy.deepcopy(static["proof_evidence"])
    _invalid(registry, crossed_legacy)


def test_static_hard_negative_requires_both_decisive_evidence_lists(tmp_path: Path) -> None:
    root, registry = _release(tmp_path)
    fixture = _load(root, "benchmark-fixture.static-hard.example.json")
    for field in ("suspicious_pattern", "decisive_innocent_explanation"):
        invalid = copy.deepcopy(fixture)
        invalid["proof_evidence"]["hard_negative_evidence"][field] = []  # type: ignore[index]
        _invalid(registry, invalid)


def test_static_proof_graph_has_no_authoritative_production_or_execution_node(
    tmp_path: Path,
) -> None:
    root, registry = _release(tmp_path)
    proof = _load(root, "static-qualification-proof.example.json")
    registry.validate(proof)
    for forbidden in (
        "detector_result",
        "finding",
        "execution",
        "project_execution_authorization",
        "sandbox_capability",
        "work_item",
        "parser_result",
        "claim",
        "observed_result",
        "operation",
        "artifact",
    ):
        invalid = copy.deepcopy(proof)
        invalid["dependency_graph"]["nodes"][0]["node_kind"] = forbidden  # type: ignore[index]
        _invalid(registry, invalid)


def test_metrics_and_qualification_cannot_hide_static_family(tmp_path: Path) -> None:
    root, registry = _release(tmp_path)
    metrics = _load(root, "qualification-metric-set.example.json")
    metrics["control_family_strata"] = [  # type: ignore[index]
        item
        for item in metrics["control_family_strata"]  # type: ignore[union-attr]
        if item["proof_family"] != "static_closed_scope"
    ]
    _invalid(registry, metrics)

    qualification = _load(root, "detector-qualification.example.json")
    qualification["qualification_proof_families"] = ["static_closed_scope"]
    qualification["static_scope_disclosure"] = None
    _invalid(registry, qualification)
