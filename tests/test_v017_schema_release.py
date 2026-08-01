from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
from sc_referee_evaluation.founder_orientation_adapter import (
    FounderOrientationQualificationAdapter,
    founder_orientation_dependency_closure,
)

from sc_referee.core.errors import RecordValidationError
from sc_referee.core.ids import semantic_digest
from sc_referee.records.schema_registry import LocalSchemaRegistry
from scripts.build_modular_method_schema_release import (
    METHOD_DETECTOR,
    METHOD_ENTRY,
    METHOD_KIND,
    RELEASE_VERSION,
    SOURCE_ADRS,
    build_release,
)


def _load(root: Path, name: str) -> dict[str, object]:
    return json.loads((root / "examples" / name).read_text(encoding="utf-8"))


def _invalid(registry: LocalSchemaRegistry, value: dict[str, object]) -> None:
    with pytest.raises(RecordValidationError):
        registry.validate(value)


def test_committed_v017_release_is_accepted_and_complete(project_root: Path) -> None:
    release = project_root / "reference" / "schemas-v0.17.0"
    status = json.loads((release / "RELEASE_STATUS.json").read_text(encoding="utf-8"))
    assert status == {
        "accepted": True,
        "baseline_version": "0.16.0",
        "public_release": True,
        "release_version": "0.17.0",
        "source_adrs": SOURCE_ADRS,
    }
    assert RELEASE_VERSION == "0.17.0"
    assert LocalSchemaRegistry(release).validate_example_directory() == 78


def test_v017_manifest_binds_every_release_file(project_root: Path) -> None:
    release = project_root / "reference" / "schemas-v0.17.0"
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


def test_v017_builder_is_reproducible_and_preserves_v016(
    project_root: Path, tmp_path: Path
) -> None:
    baseline_manifest = project_root / "reference" / "schemas-v0.16.0" / "MANIFEST.sha256"
    before = baseline_manifest.read_bytes()
    output = tmp_path / "schemas-v0.17.0"
    assert build_release(output) == 78
    committed = project_root / "reference" / "schemas-v0.17.0"
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


def test_typed_method_profile_is_digest_bound_and_cannot_cross_variants(
    project_root: Path,
) -> None:
    root = project_root / "reference" / "schemas-v0.17.0"
    registry = LocalSchemaRegistry(root)
    profile = _load(root, "static-qualification-profile.analysis-method.example.json")
    registry.validate(profile)
    assert profile["profile_kind"] == METHOD_KIND
    assert profile["target_detector"]["detector_id"] == METHOD_DETECTOR  # type: ignore[index]
    assert profile["verifier"]["entry_point"] == METHOD_ENTRY  # type: ignore[index]
    assert profile["method_binding"]["production_finding_permitted"] is False  # type: ignore[index]
    binding = copy.deepcopy(profile["method_binding"])
    supplied_digest = binding.pop("binding_digest")
    assert supplied_digest == semantic_digest(binding)
    adapter = FounderOrientationQualificationAdapter()
    assert (
        binding["qualification_adapter"][  # type: ignore[index]
            "implementation_digest"
        ]
        == adapter.implementation_digest
    )
    assert binding["qualification_adapter"]["dependency_closure"] == list(  # type: ignore[index]
        founder_orientation_dependency_closure()
    )

    crossed = copy.deepcopy(profile)
    crossed["method_binding"]["qualification_adapter"]["adapter_id"] = "adapter:production"  # type: ignore[index]
    _invalid(registry, crossed)


def test_typed_method_proof_rejects_relation_kind_and_duplicate_plane(
    project_root: Path,
) -> None:
    root = project_root / "reference" / "schemas-v0.17.0"
    registry = LocalSchemaRegistry(root)
    proof = _load(root, "static-qualification-proof.analysis-method.example.json")
    registry.validate(proof)
    assert proof["proof_profile_kind"] == METHOD_KIND

    mixed = copy.deepcopy(proof)
    mixed["derived_facts"]["comparison_form"] = "set_relation"  # type: ignore[index]
    _invalid(registry, mixed)

    report_only_profile = _load(root, "static-qualification-profile.analysis-method.example.json")
    report_only_profile["method_binding"]["required_evidence_planes"] = [  # type: ignore[index]
        "reported_text"
    ]
    report_only_profile["method_binding"]["required_assertion_roles"] = [  # type: ignore[index]
        "reported"
    ]
    registry.validate(report_only_profile)

    report_only = copy.deepcopy(proof)
    report_only["derived_facts"]["observations"] = report_only["derived_facts"][  # type: ignore[index]
        "observations"
    ][:1]
    report_only["derived_facts"]["candidate_paths"] = ["report.md"]  # type: ignore[index]
    registry.validate(report_only)

    duplicate = copy.deepcopy(proof)
    duplicate["derived_facts"]["observations"][1] = copy.deepcopy(  # type: ignore[index]
        duplicate["derived_facts"]["observations"][0]  # type: ignore[index]
    )
    _invalid(registry, duplicate)
