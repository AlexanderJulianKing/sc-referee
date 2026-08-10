from __future__ import annotations

from pathlib import Path

from sc_referee.scientific_checks.profiles import scientific_check_release_registry


def test_every_substantive_scientific_check_has_one_explicit_evaluation_binding() -> None:
    registry = scientific_check_release_registry()
    substantive = {
        module.manifest.check_id: module
        for module in registry.modules
        if module.manifest.check_id != "check:registry-conformance-token"
    }
    bindings = {binding.check_id: binding for binding in registry.method_conflict_bindings}

    assert len(substantive) == len(bindings) == 22
    assert set(bindings) == set(substantive)
    for check_id, module in substantive.items():
        binding = bindings[check_id]
        evidence_planes = tuple(
            sorted({adapter.evidence_plane for adapter in module.adapter_manifests})
        )
        assertion_roles = tuple(
            sorted(
                {
                    "reported" if plane == "reported_text" else "observed"
                    for plane in evidence_planes
                }
            )
        )
        assert binding.check_version == module.manifest.check_version
        assert binding.check_manifest_digest == module.manifest.manifest_digest
        assert binding.dimension == module.manifest.dimension
        assert binding.comparison_form == module.manifest.comparison_form
        assert binding.required_evidence_planes == evidence_planes
        assert binding.required_assertion_roles == assertion_roles
        assert binding.required_semantic_roles == module.manifest.semantic_roles
        assert binding.production_finding_permitted is False


def test_production_method_conflict_path_contains_no_benchmark_identity(
    project_root: Path,
) -> None:
    paths = [
        *sorted((project_root / "src" / "sc_referee").rglob("*.py")),
        project_root
        / "src"
        / "sc_referee"
        / "resources"
        / "capability-manifests-v1"
        / "detector-manifests.json",
        project_root
        / "src"
        / "sc_referee"
        / "resources"
        / "scientific-check-manifests-v1"
        / "registry.json",
        project_root / "scripts" / "build_capability_source_manifests.py",
    ]
    forbidden = (
        "genebench",
        "scienceagentbench",
        "structural-v2",
        "task-03",
        "task-04",
        "task-05",
        "task-06",
        "task-07",
        "task-08",
        "task-09",
        "task-10",
        "task-11",
        "task-12",
        "evaluation/genebench",
        "evaluation/cold",
    )

    for path in paths:
        payload = path.read_text(encoding="utf-8").casefold()
        assert not ({value for value in forbidden if value in payload}), path
