from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from sc_referee.core.errors import RecordValidationError
from sc_referee.records.schema_registry import LocalSchemaRegistry
from scripts.build_second_static_profile_schema_release import (
    METHOD_DETECTOR,
    METHOD_ENTRY,
    METHOD_KIND,
    RELEASE_VERSION,
    SOURCE_ADRS,
    build_release,
)


def _load(root: Path, name: str) -> dict[str, object]:
    return json.loads((root / "examples" / name).read_text(encoding="utf-8"))


def _release(tmp_path: Path) -> tuple[Path, LocalSchemaRegistry]:
    root = tmp_path / "schemas-v0.16.0"
    build_release(root)
    return root, LocalSchemaRegistry(root)


def _invalid(registry: LocalSchemaRegistry, value: dict[str, object]) -> None:
    with pytest.raises(RecordValidationError):
        registry.validate(value)


def test_committed_v016_release_is_accepted_and_complete(project_root: Path) -> None:
    release = project_root / "reference" / "schemas-v0.16.0"
    status = json.loads((release / "RELEASE_STATUS.json").read_text(encoding="utf-8"))
    assert status == {
        "accepted": True,
        "baseline_version": "0.15.0",
        "public_release": True,
        "release_version": "0.16.0",
        "source_adrs": SOURCE_ADRS,
    }
    assert RELEASE_VERSION == "0.16.0"
    assert LocalSchemaRegistry(release).validate_example_directory() == 78


def test_v016_manifest_binds_every_release_file(project_root: Path) -> None:
    release = project_root / "reference" / "schemas-v0.16.0"
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


def test_v016_builder_is_reproducible_and_preserves_v015(
    project_root: Path, tmp_path: Path
) -> None:
    baseline_manifest = project_root / "reference" / "schemas-v0.15.0" / "MANIFEST.sha256"
    before = baseline_manifest.read_bytes()
    output = tmp_path / "schemas-v0.16.0"
    assert build_release(output) == 78
    committed = project_root / "reference" / "schemas-v0.16.0"
    generated = {
        path.relative_to(output).as_posix(): path.read_bytes()
        for path in output.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }
    expected = {
        path.relative_to(committed).as_posix(): path.read_bytes()
        for path in committed.rglob("*")
        if path.is_file()
        and not any(part.startswith(".") or part == "__pycache__" for part in path.parts)
    }
    assert generated == expected
    assert baseline_manifest.read_bytes() == before


def test_method_profile_is_closed_and_cannot_cross_variants(tmp_path: Path) -> None:
    root, registry = _release(tmp_path)
    profile = _load(root, "static-qualification-profile.analysis-method.example.json")
    registry.validate(profile)
    assert profile["profile_kind"] == METHOD_KIND
    assert profile["target_detector"]["detector_id"] == METHOD_DETECTOR  # type: ignore[index]
    assert profile["verifier"]["entry_point"] == METHOD_ENTRY  # type: ignore[index]

    crossed = copy.deepcopy(profile)
    crossed["verifier"]["entry_point"] = (  # type: ignore[index]
        "sc_referee_evaluation.static_qualification:verify_bounded_direction_case"
    )
    _invalid(registry, crossed)


def test_method_proof_binds_review_authority_and_cannot_cross_fact_shape(
    tmp_path: Path,
) -> None:
    root, registry = _release(tmp_path)
    proof = _load(root, "static-qualification-proof.analysis-method.example.json")
    registry.validate(proof)
    facts = proof["derived_facts"]
    assert facts["governing_answer"]["record_ref"]["record_type"] == "answer"  # type: ignore[index]
    assert facts["governing_question"]["record_ref"]["record_type"] == (  # type: ignore[index]
        "material_question"
    )
    crossed = copy.deepcopy(proof)
    crossed["proof_profile_kind"] = "bounded_report_mean_direction_v1"
    _invalid(registry, crossed)


def test_method_static_fixture_requires_exact_review_input_collections(tmp_path: Path) -> None:
    root, registry = _release(tmp_path)
    fixture = _load(root, "benchmark-fixture.static-method-good.example.json")
    registry.validate(fixture)
    inputs = fixture["proof_evidence"]["public_inputs"]  # type: ignore[index]
    assert len(inputs["answers"]) == 1
    assert len(inputs["material_questions"]) == 1
    assert len(inputs["semantic_assertions"]) == 1
    for field in ("answers", "material_questions", "semantic_assertions"):
        invalid = copy.deepcopy(fixture)
        del invalid["proof_evidence"]["public_inputs"][field]  # type: ignore[index]
        _invalid(registry, invalid)
