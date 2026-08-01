from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from sc_referee.core.errors import RecordValidationError
from sc_referee.records.schema_registry import LocalSchemaRegistry
from scripts.build_observed_schema_candidate import build_candidate


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.fixture(scope="module")
def candidate(tmp_path_factory: pytest.TempPathFactory) -> Path:
    output = tmp_path_factory.mktemp("observed-schema-candidate") / "v0.6.0"
    assert build_candidate("0.6.0", output) == 49
    return output


def test_candidate_is_explicitly_nonpublic_and_versioned(candidate: Path) -> None:
    status = _read(candidate / "PROPOSAL_STATUS.json")
    assert status["accepted"] is False
    assert status["public_release"] is False
    assert status["candidate_version"] == "0.6.0"
    assert (candidate / "VERSION").read_text(encoding="utf-8") == "0.6.0\n"


def test_candidate_schemas_and_all_examples_validate(candidate: Path) -> None:
    schema_dir = candidate / "schemas" / "v0.6.0"
    for path in sorted(schema_dir.glob("*.json")):
        Draft202012Validator.check_schema(_read(path))

    registry = LocalSchemaRegistry(candidate)
    assert registry.validate_example_directory() == 49


def test_candidate_updates_catalog_union_and_bundle_together(candidate: Path) -> None:
    catalog = _read(candidate / "schema-catalog.json")
    names = {item["name"] for item in catalog["schemas"]}
    assert {
        "audit_run",
        "stage_result",
        "file_record",
        "operation",
        "artifact",
        "observed_result",
    } <= names

    schema_dir = candidate / "schemas" / "v0.6.0"
    assert len(_read(schema_dir / "record-union.schema.json")["oneOf"]) == 40
    bundle = _read(schema_dir / "audit-bundle.schema.json")
    arrays = {
        "audit_runs",
        "stage_results",
        "file_records",
        "operations",
        "artifacts",
        "observed_results",
    }
    assert arrays <= set(bundle["required"])
    assert arrays <= set(bundle["properties"])


def test_candidate_rejects_lifecycle_fabrication(candidate: Path) -> None:
    registry = LocalSchemaRegistry(candidate)
    created = _read(candidate / "examples" / "audit-run.created.example.json")
    created["snapshot_ref"] = {
        "record_type": "repository_snapshot",
        "record_id": "snapshot:fabricated",
    }
    with pytest.raises(RecordValidationError):
        registry.validate(created)

    parsed = _read(candidate / "examples" / "audit-run.terminal.example.json")
    parsed["state"] = "parsed"
    parsed.pop("snapshot_ref")
    parsed.pop("terminal_reason")
    with pytest.raises(RecordValidationError):
        registry.validate(parsed)


def test_candidate_rejects_followed_symlink_and_untyped_edge(candidate: Path) -> None:
    registry = LocalSchemaRegistry(candidate)
    symlink = _read(candidate / "examples" / "file-record.symlink.example.json")
    symlink["symlink_followed"] = True
    with pytest.raises(RecordValidationError):
        registry.validate(symlink)

    operation = _read(candidate / "examples" / "operation.example.json")
    operation["input_refs"] = ["artifact:data"]
    with pytest.raises(RecordValidationError):
        registry.validate(operation)


def test_candidate_rejects_opaque_operation_reported_supported(candidate: Path) -> None:
    registry = LocalSchemaRegistry(candidate)
    operation = _read(candidate / "examples" / "operation.opaque.example.json")
    operation["inspection_status"] = "supported"
    with pytest.raises(RecordValidationError):
        registry.validate(operation)


def test_candidate_rejects_unknown_orientation_promoted_without_evidence(candidate: Path) -> None:
    registry = LocalSchemaRegistry(candidate)
    observed = _read(candidate / "examples" / "observed-result.unknown.example.json")
    observed["orientation"] = {
        "state": "known",
        "value": "treated_minus_control",
    }
    with pytest.raises(RecordValidationError):
        registry.validate(observed)


def test_complete_result_requires_producer_and_artifact_while_partial_preserves_gap(
    candidate: Path,
) -> None:
    registry = LocalSchemaRegistry(candidate)
    observed = _read(candidate / "examples" / "observed-result.scalar.example.json")
    observed.pop("producing_operation_ref")
    with pytest.raises(RecordValidationError):
        registry.validate(observed)

    observed["lineage_status"] = "partial"
    observed["lineage_limitations"] = ["Producing operation linkage was unavailable."]
    registry.validate(observed)


@pytest.mark.parametrize("version", ["0.5.1", "0.6.0"])
def test_builder_supports_both_unresolved_release_choices(tmp_path: Path, version: str) -> None:
    output = tmp_path / version
    build_candidate(version, output)
    common = _read(output / "schemas" / f"v{version}" / "common.schema.json")
    assert common["$defs"]["SchemaVersion"]["const"] == version


def test_builder_refuses_baseline_invalid_version_and_nonempty_output(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="immutable"):
        build_candidate("0.5.0", tmp_path / "baseline")
    with pytest.raises(ValueError, match="SemVer"):
        build_candidate("next", tmp_path / "invalid")

    output = tmp_path / "nonempty"
    output.mkdir()
    (output / "keep.txt").write_text("user-owned\n", encoding="utf-8")
    with pytest.raises(ValueError, match="absent or empty"):
        build_candidate("0.6.0", output)
    assert (output / "keep.txt").read_text(encoding="utf-8") == "user-owned\n"


def test_candidate_build_does_not_modify_baseline(project_root: Path, tmp_path: Path) -> None:
    baseline = project_root / "reference" / "schemas-v0.5.0" / "schema-catalog.json"
    before = copy.deepcopy(baseline.read_bytes())
    build_candidate("0.6.0", tmp_path / "candidate")
    assert baseline.read_bytes() == before
