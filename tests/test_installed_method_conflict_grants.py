from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from pathlib import Path

import pytest

from sc_referee.capability_matrix import (
    default_capability_manifest_root,
    generate_capability_matrix,
)
from sc_referee.controller import replay, run_audit
from sc_referee.core.ids import canonical_json
from sc_referee.detectors.method_conflict_grant_pins import (
    GRANT_PINS,
    installed_pin_matches_live_identity,
    load_method_conflict_grant_evidence,
)
from sc_referee.detectors.method_conflict_qualification import (
    resolve_method_conflict_qualification,
)
from sc_referee.qualification_grants import (
    QualificationGrantResourceError,
    default_qualification_grant_root,
    load_installed_qualification_grants,
)
from sc_referee.scientific_checks.profiles import scientific_check_release_registry
from scripts.build_method_conflict_grant_resources import build_grant_resources

_DEPENDENCE_BINDING_ID = (
    "method-conflict-binding:authorized-independent-unit-entry-into-row-independent-procedure-v1"
)
_COMPLETE_DOMAIN_BINDING_ID = "method-conflict-binding:complete-domain-exposure-denominator-v1"
_INSTALLED_FINDING_BINDINGS = {_COMPLETE_DOMAIN_BINDING_ID, _DEPENDENCE_BINDING_ID}
_LIVE_FINDING_BINDINGS = {_COMPLETE_DOMAIN_BINDING_ID, _DEPENDENCE_BINDING_ID}


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _detector_manifest(detector_id: str, detector_version: str) -> dict[str, object]:
    collection = _load(default_capability_manifest_root() / "detector-manifests.json")
    records = collection["records"]
    assert isinstance(records, list)
    return next(
        record
        for record in records
        if isinstance(record, dict)
        and record.get("detector_id") == detector_id
        and record.get("detector_version") == detector_version
    )


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_installed_resources_keep_both_exact_pins_live() -> None:
    evidence_by_binding = load_installed_qualification_grants()
    assert len(GRANT_PINS) == 2
    assert set(evidence_by_binding) == set(GRANT_PINS)
    assert set(GRANT_PINS) == _INSTALLED_FINDING_BINDINGS
    for binding_id, pin in GRANT_PINS.items():
        evidence = evidence_by_binding[binding_id]
        assert dict(evidence.grant)["qualification_digest"] == pin.qualification_digest
        assert dict(evidence.grant)["metric_set_digest"] == pin.metric_set_digest
        assert dict(evidence.grant)["required_roots"] == pin.required_roots
        assert dict(evidence.grant)["absolute_missed_roots"] == pin.absolute_missed_roots
        expected_live = binding_id in _LIVE_FINDING_BINDINGS
        assert installed_pin_matches_live_identity(pin) is expected_live
        assert (load_method_conflict_grant_evidence(pin) is not None) is expected_live


def test_only_live_installed_grant_resolves_and_all_stale_or_unpinned_bindings_refuse() -> None:
    registry = scientific_check_release_registry()
    installed = load_installed_qualification_grants()
    by_binding = {binding.binding_id: binding for binding in registry.method_conflict_bindings}
    assert len(by_binding) == 23
    resolved = []
    refused = []
    for binding_id, binding in sorted(by_binding.items()):
        pin = GRANT_PINS.get(binding_id)
        if pin is None:
            refused.append(binding_id)
            assert (
                resolve_method_conflict_qualification(
                    binding=binding,
                    detector_manifest={},
                    qualification={},
                    metric_set={},
                    pin=None,
                )
                is None
            )
            continue
        evidence = load_method_conflict_grant_evidence(pin)
        detector_manifest = _detector_manifest(binding.detector_id, binding.detector_version)
        if evidence is None:
            refused.append(binding_id)
            assert installed_pin_matches_live_identity(pin) is False
            raw = installed[binding_id]
            assert (
                resolve_method_conflict_qualification(
                    binding=binding,
                    detector_manifest=detector_manifest,
                    qualification=dict(raw.qualification),
                    metric_set=dict(raw.metric_set),
                    pin=pin,
                )
                is None
            )
            continue
        qualification, metric_set = evidence
        grant = resolve_method_conflict_qualification(
            binding=binding,
            detector_manifest=detector_manifest,
            qualification=qualification,
            metric_set=metric_set,
            pin=pin,
        )
        assert grant is not None
        assert grant.binding_id == binding_id
        resolved.append(binding_id)
    assert resolved == sorted(_LIVE_FINDING_BINDINGS)
    assert len(refused) == len(by_binding) - len(_LIVE_FINDING_BINDINGS)


def test_installed_grant_binding_digests_match_live_registry_and_matrix_builds(
    project_root: Path,
) -> None:
    """Any shared detector-manifest change must repin every installed binding."""

    registry = scientific_check_release_registry()
    live_by_id = {binding.binding_id: binding for binding in registry.method_conflict_bindings}
    assert set(GRANT_PINS) <= set(live_by_id)
    for binding_id in _LIVE_FINDING_BINDINGS:
        pin = GRANT_PINS[binding_id]
        binding = live_by_id[binding_id]
        assert pin.binding_digest == binding.binding_digest
        assert pin.detector_manifest_digest == binding.detector_manifest_digest
    matrix = generate_capability_matrix(
        default_capability_manifest_root(), project_root / "reference/schemas-v0.21.0"
    )
    published = {
        grant["binding_id"]
        for entry in matrix["entries"]
        for detector in entry["detectors"]
        for grant in detector.get("binding_grants", [])
        if grant.get("strongest_output_type") == "finding"
    }
    assert published == _LIVE_FINDING_BINDINGS


def test_capability_matrix_exposes_finding_for_exactly_the_live_grant_binding(
    project_root: Path,
) -> None:
    matrix = generate_capability_matrix(
        default_capability_manifest_root(), project_root / "reference/schemas-v0.21.0"
    )
    grants = [
        grant
        for entry in matrix["entries"]
        for detector in entry["detectors"]
        for grant in detector.get("binding_grants", [])
    ]
    assert {grant["binding_id"] for grant in grants} == _LIVE_FINDING_BINDINGS
    assert all(grant["strongest_output_type"] == "finding" for grant in grants)
    method_detector = next(
        detector
        for entry in matrix["entries"]
        for detector in entry["detectors"]
        if detector["detector_id"] == "detector:bounded-analysis-method-conflict"
    )
    assert method_detector["maturity"] == "experimental"
    assert method_detector["strongest_output_type"] == "disclosure"
    code_detector = next(
        detector
        for entry in matrix["entries"]
        for detector in entry["detectors"]
        if detector["detector_id"] == "detector:bounded-code-csv-dependence-conflict"
    )
    assert code_detector["maturity"] == "experimental"
    assert code_detector["strongest_output_type"] == "disclosure"
    assert {item["binding_id"] for item in code_detector["binding_grants"]} == {
        _DEPENDENCE_BINDING_ID
    }


def test_grant_builder_reproduces_the_installed_resource(tmp_path: Path) -> None:
    output = tmp_path / "qualification-grants-v1"
    descriptor, metric_sets = build_grant_resources(output)
    assert len(descriptor["grants"]) == 2
    assert len(metric_sets["records"]) == 2
    assert _tree_bytes(output) == _tree_bytes(default_qualification_grant_root())
    with pytest.raises(RuntimeError, match="absent or empty"):
        build_grant_resources(output)


def test_grant_loader_refuses_digest_drift(project_root: Path, tmp_path: Path) -> None:
    root = tmp_path / "grants"
    shutil.copytree(default_qualification_grant_root(), root)
    metric_sets = _load(root / "metric-sets.json")
    records = metric_sets["records"]
    assert isinstance(records, list)
    first = records[0]
    assert isinstance(first, dict)
    first["counts"]["missed_roots"] = 1
    (root / "metric-sets.json").write_text(canonical_json(metric_sets) + "\n", encoding="utf-8")
    with pytest.raises(QualificationGrantResourceError, match="digest mismatch"):
        load_installed_qualification_grants(
            grant_root=root,
            qualification_manifest_path=(
                project_root
                / "src/sc_referee/resources/capability-manifests-v1/qualification-manifests.json"
            ),
            schema_root=project_root / "reference/schemas-v0.21.0",
        )


def test_grant_descriptor_payload_equals_the_frozen_pin_fields() -> None:
    evidence = load_installed_qualification_grants()
    for binding_id, pin in GRANT_PINS.items():
        expected = asdict(pin)
        expected["exam_adapter_identity"] = [asdict(item) for item in pin.exam_adapter_identity]
        if expected["finding_profile_id"] is None:
            expected.pop("finding_profile_id")
            expected.pop("finding_profile_digest")
        assert dict(evidence[binding_id].grant) == expected


def test_complete_domain_installed_grant_admits_one_finding_through_audit_and_replay(
    schema_root: Path, tmp_path: Path
) -> None:
    from tests.test_generic_exposure_denominator_relation import (
        CONFLICT_REPORTS,
        _contract,
        _result,
        _write_project,
    )

    repository = tmp_path / "complete-domain-production"
    _write_project(repository, CONFLICT_REPORTS[0][1])
    contract_lock = _contract(repository, tmp_path / "contract", schema_root)
    output = tmp_path / "audit"
    bundle = run_audit(
        repository,
        output,
        schema_root,
        report="report.md",
        method_contract_lock=contract_lock,
    )
    result = _result(bundle)
    assert result is not None
    assert result["state"] == "finding_candidate"
    assert result["extensions"]["x-production-finding-permitted"] is True
    pin = GRANT_PINS["method-conflict-binding:complete-domain-exposure-denominator-v1"]
    assert result["extensions"]["x-detector-qualification-digest"] == pin.qualification_digest
    assert result["extensions"]["x-qualification-metric-set-digest"] == pin.metric_set_digest
    assert len(bundle["findings"]) == 1

    replayed = replay(output / "semantic.lock.json", tmp_path / "replay", schema_root)
    assert replayed["detector_results"] == bundle["detector_results"]
    assert replayed["findings"] == bundle["findings"]
