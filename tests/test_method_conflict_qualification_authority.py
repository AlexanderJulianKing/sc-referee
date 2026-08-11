from __future__ import annotations

import copy
import json
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import pytest

import sc_referee.detectors.method_conflict_grant_pins as grant_pins
from sc_referee.controller import _evaluate_general_detectors
from sc_referee.core.ids import semantic_digest, stable_id
from sc_referee.detectors.method_conflict_grant_pins import GrantPin, live_adapter_identity
from sc_referee.detectors.method_conflict_qualification import (
    project_qualified_method_conflict_candidate,
    resolve_method_conflict_qualification,
)
from sc_referee.detectors.method_conflict_registry import (
    MethodConflictEvaluation,
    evaluate_registered_method_conflicts,
)
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.reporting.policy import ReportContractError, _validate_detector_projection
from sc_referee.scientific_checks.profiles import scientific_check_release_registry
from scripts.build_method_promotion_schema_candidate import build_candidate
from tests.method_conflict_matrix_support import TARGET_RELATIONS, method_conflict_case


def _detector_manifest(project_root: Path) -> dict[str, Any]:
    collection = json.loads(
        (
            project_root
            / "src"
            / "sc_referee"
            / "resources"
            / "capability-manifests-v1"
            / "detector-manifests.json"
        ).read_text(encoding="utf-8")
    )
    return next(
        item
        for item in collection["records"]
        if item["detector_id"] == "detector:bounded-analysis-method-conflict"
    )


def _policy() -> dict[str, Any]:
    value: dict[str, Any] = {
        "policy_kind": "pilot_informed_binding_thresholds_v1",
        "policy_id": "threshold-policy:synthetic-test-only",
        "policy_version": "1.0.0",
        "decision_adr_ref": "docs/implementation/ADR-9999-SYNTHETIC-TEST-ONLY.md",
        "pilot_evidence_refs": ["pilot:synthetic-test-only"],
        "frozen_at": "2026-08-03T12:00:00Z",
        "held_out_labels_observed_before_freeze": False,
        "minimum_counts": {
            "workflows": 1,
            "problem_clusters": 2,
            "adjudicated_roots": 1,
            "control_cases": 1,
        },
        "require_estimable_intervals": False,
        "metric_requirements": [
            {
                "metric_name": "completed_opportunity_false_positive_rate",
                "statistic": "estimate",
                "operator": "at_most",
                "threshold": 0.1,
            },
            {
                "metric_name": "adjudicated_root_recall",
                "statistic": "estimate",
                "operator": "at_least",
                "threshold": 0.9,
            },
        ],
    }
    value["policy_semantic_digest"] = semantic_digest(value)
    return value


def _records(
    project_root: Path, candidate: Path
) -> tuple[Any, dict[str, Any], dict[str, Any], dict[str, Any]]:
    registry = scientific_check_release_registry()
    binding = next(
        item
        for item in registry.method_conflict_bindings
        if item.check_id == "check:founder-orientation-before-hmm-emission"
    )
    manifest = _detector_manifest(project_root)
    policy = _policy()
    scope = {
        "scope_kind": "method_conflict_binding_v1",
        "binding_id": binding.binding_id,
        "production_binding_digest": binding.binding_digest,
        "check_id": binding.check_id,
        "check_version": binding.check_version,
        "check_manifest_digest": binding.check_manifest_digest,
        "detector_id": binding.detector_id,
        "detector_version": binding.detector_version,
        "detector_manifest_digest": binding.detector_manifest_digest,
        "static_qualification_profile_ref": {
            "record_type": "static_qualification_profile",
            "record_id": "static-profile:synthetic-v03-test-only",
        },
        "static_qualification_profile_digest": "sha256:" + "3" * 64,
        "qualification_adapter": {
            "adapter_id": "qualification-adapter:synthetic-test-only",
            "adapter_version": "1.0.0",
            "implementation_digest": "sha256:" + "4" * 64,
        },
    }
    metric_set = json.loads(
        (candidate / "examples" / "qualification-metric-set.example.json").read_text()
    )
    metric_set.update(
        {
            "metric_set_id": "qualification-metric-set:synthetic-v03-test-only",
            "detector_id": binding.detector_id,
            "detector_version": binding.detector_version,
            "detector_manifest_digest": binding.detector_manifest_digest,
            "binding_scope": copy.deepcopy(scope),
            "numeric_threshold_policy": copy.deepcopy(policy),
            "promotion_evidence_eligible": True,
            "promotion_permitted": True,
            "corpus_partitions": ["held_out"],
            "excluded_case_outcomes": [],
        }
    )
    metric_set["counts"].update(
        {
            "workflows": 2,
            "problem_clusters": 2,
            "adjudicated_roots": 2,
            "missed_roots": 0,
        }
    )
    metric_set["control_family_strata"][2]["case_count"] = 1

    qualification = json.loads(
        (candidate / "examples" / "detector-qualification.example.json").read_text()
    )
    qualification.update(
        {
            "qualification_id": "qualification:synthetic-v03-test-only",
            "detector_id": binding.detector_id,
            "detector_version": binding.detector_version,
            "outcome": "promoted",
            "effective_maturity": "validated",
            "requested_maturity": "validated",
            "binding_scope": copy.deepcopy(scope),
            "numeric_threshold_policy": copy.deepcopy(policy),
            "qualification_proof_families": ["static_closed_scope"],
            "quantitative_metrics": {
                "metric_profile": "root-cause-clustered-metrics-v1",
                "metric_set_refs": [
                    {
                        "record_type": "qualification_metric_set",
                        "record_id": metric_set["metric_set_id"],
                    }
                ],
            },
            "static_scope_disclosure": {
                "profile_refs": [copy.deepcopy(scope["static_qualification_profile_ref"])],
                "scope_statement": "Synthetic schema and resolver test only.",
                "execution_claimed": False,
                "global_correctness_claimed": False,
            },
        }
    )
    qualification["safety_gates"]["proof_families_stratified"] = True
    LocalSchemaRegistry(candidate).validate(metric_set)
    LocalSchemaRegistry(candidate).validate(qualification)
    return binding, manifest, metric_set, qualification


def _pin(binding: Any, metric_set: dict[str, Any], qualification: dict[str, Any]) -> GrantPin:
    adapters = live_adapter_identity(binding)
    assert adapters is not None
    return GrantPin(
        binding_id=binding.binding_id,
        binding_digest=binding.binding_digest,
        check_id=binding.check_id,
        check_version=binding.check_version,
        check_manifest_digest=binding.check_manifest_digest,
        detector_id=binding.detector_id,
        detector_version=binding.detector_version,
        detector_manifest_digest=binding.detector_manifest_digest,
        qualification_id=qualification["qualification_id"],
        qualification_digest=semantic_digest(qualification),
        metric_set_id=metric_set["metric_set_id"],
        metric_set_digest=semantic_digest(metric_set),
        threshold_policy_digest=metric_set["numeric_threshold_policy"]["policy_semantic_digest"],
        exam_adapter_identity=adapters,
        absolute_missed_roots=0,
        required_roots=2,
    )


def _locked_candidate_case(manifest: dict[str, Any], binding: Any) -> dict[str, Any]:
    relation = TARGET_RELATIONS[0]
    locked, question = method_conflict_case(
        relation,
        required_candidate_id=relation.required_candidate_id,
        observed_candidate_id=relation.conflicting_candidate_id,
        namespace="round2-production-wiring",
    )
    locked["material_questions"] = [question]
    locked["detector_manifests"] = [copy.deepcopy(manifest)]
    registry = scientific_check_release_registry()
    locked["scientific_check_registry"] = {
        "enabled_modules": [
            {
                "manifest": {"check_id": item.check_id},
                "manifest_digest": item.check_manifest_digest,
            }
            for item in registry.method_conflict_bindings
        ],
        "method_conflict_bindings": [asdict(item) for item in registry.method_conflict_bindings],
    }
    return locked


@pytest.fixture
def candidate(tmp_path: Path) -> Path:
    output = tmp_path / "candidate"
    build_candidate(output)
    return output


def test_exact_records_resolve_one_binding_grant_and_project_candidate(
    project_root: Path, candidate: Path
) -> None:
    binding, manifest, metric_set, qualification = _records(project_root, candidate)
    grant = resolve_method_conflict_qualification(
        binding=binding,
        detector_manifest=manifest,
        qualification=qualification,
        metric_set=metric_set,
        pin=_pin(binding, metric_set, qualification),
    )
    assert grant is not None
    assert grant.binding_digest == binding.binding_digest
    assert grant.maturity == "validated"

    work_packet = {
        "profile": "bounded_analysis_method_conflict_work_packet_v1",
        "audit_run_id": "audit:synthetic-binding-test",
        "detector_id": binding.detector_id,
        "detector_version": binding.detector_version,
        "detector_manifest_digest": binding.detector_manifest_digest,
        "target_question": {
            "record_type": "material_question",
            "question_id": "question:synthetic-binding-test",
            "status": "answered",
            "extensions": {"x-scientific-check-id": binding.check_id},
        },
        "scientific_contracts": [],
        "semantic_assertions": [],
        "answers": [],
        "file_records": [],
        "asset_identities": [],
        "operations": [],
        "artifacts": [],
        "publication_surfaces": [],
    }
    input_digest = semantic_digest(work_packet)
    result = {
        "record_type": "detector_result",
        "result_id": stable_id(
            "detector-result",
            binding.detector_id,
            binding.detector_version,
            "question:synthetic-binding-test",
            input_digest,
        ),
        "audit_run_id": "audit:synthetic-binding-test",
        "state": "evaluation_finding_candidate",
        "detector_maturity": "experimental",
        "detector_id": binding.detector_id,
        "detector_version": binding.detector_version,
        "detector_manifest_digest": binding.detector_manifest_digest,
        "deterministic_input_digest": input_digest,
        "candidate": {"assessment_type": "finding"},
        "extensions": {
            "x-evaluation-only": True,
            "x-production-finding-permitted": False,
            "x-review-case-digest": "sha256:" + "5" * 64,
        },
    }
    promoted = project_qualified_method_conflict_candidate(
        result, binding, grant, work_packet=work_packet
    )
    assert promoted is not None
    assert promoted["state"] == "finding_candidate"
    assert promoted["detector_maturity"] == "validated"
    assert promoted["extensions"]["x-method-conflict-binding-digest"] == binding.binding_digest


def test_resolver_uses_evaluation_refs_not_typed_agent_refs(
    project_root: Path, candidate: Path
) -> None:
    binding, manifest, metric_set, qualification = _records(project_root, candidate)
    qualification["agent_adjudication_refs"] = []
    assert (
        resolve_method_conflict_qualification(
            binding=binding,
            detector_manifest=manifest,
            qualification=qualification,
            metric_set=metric_set,
            pin=_pin(binding, metric_set, qualification),
        )
        is not None
    )

    qualification["evaluation_refs"] = []
    assert (
        resolve_method_conflict_qualification(
            binding=binding,
            detector_manifest=manifest,
            qualification=qualification,
            metric_set=metric_set,
            pin=_pin(binding, metric_set, qualification),
        )
        is None
    )

    qualification["evaluation_refs"] = [1]
    assert (
        resolve_method_conflict_qualification(
            binding=binding,
            detector_manifest=manifest,
            qualification=qualification,
            metric_set=metric_set,
            pin=_pin(binding, metric_set, qualification),
        )
        is None
    )


def test_registry_exposes_exact_work_packet_and_ungranted_binding_keeps_candidate(
    project_root: Path, candidate: Path
) -> None:
    binding, manifest, metric_set, qualification = _records(project_root, candidate)
    del metric_set, qualification
    locked = _locked_candidate_case(manifest, binding)

    registered = evaluate_registered_method_conflicts(locked)
    assert len(registered) == 1
    assert isinstance(registered[0], MethodConflictEvaluation)
    assert registered[0].result["deterministic_input_digest"] == semantic_digest(
        registered[0].work_packet
    )
    assert registered[0].binding.binding_id == binding.binding_id

    evaluation = _evaluate_general_detectors(locked)

    assert len(grant_pins.GRANT_PINS) == 2
    assert binding.binding_id not in grant_pins.GRANT_PINS
    assert len(evaluation.results) == 1
    assert evaluation.results[0]["state"] == "evaluation_finding_candidate"
    assert evaluation.findings == ()


def test_test_local_pin_admits_one_finding_through_full_controller_bundle(
    project_root: Path,
    schema_root: Path,
    candidate: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tests.test_evaluation_control_fixture import _lock_method_authority

    binding, manifest, metric_set, qualification = _records(project_root, candidate)
    del manifest
    pin = _pin(binding, metric_set, qualification)
    installed_pins = dict(grant_pins.GRANT_PINS)
    installed_loader = grant_pins.load_method_conflict_grant_evidence
    monkeypatch.setattr(
        grant_pins,
        "GRANT_PINS",
        {**installed_pins, binding.binding_id: pin},
    )
    monkeypatch.setattr(
        grant_pins,
        "load_method_conflict_grant_evidence",
        lambda installed: (
            (qualification, metric_set) if installed == pin else installed_loader(installed)
        ),
    )
    repository = tmp_path / "round2-controller-project"
    repository.mkdir()
    (repository / "analysis.py").write_text(
        "import csv\n"
        "import math\n"
        "from pathlib import Path\n"
        "ROOT = Path(__file__).resolve().parent\n"
        "def emission_matrix(observed, founder_state, error):\n"
        "    return observed == founder_state\n"
        "def fit(sample, observed):\n"
        "    return emission_matrix(observed, sample.founder_alleles[0], 0.01)\n"
        "def main():\n"
        "    (ROOT / 'report.md').write_text(\n"
        "        'The parental marker panel as supplied and the progeny calls were compared marker by marker: 372 of the 480 markers agree.\\n\\nThe emission model used a per-marker agreement rate of 0.225.\\n'\n"
        "    )\n"
        "if __name__ == '__main__':\n"
        "    main()\n"
        "rows = list(csv.DictReader((ROOT / 'markers.csv').open()))\n"
        "panel = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
        "LIKELIHOOD = math.prod(\n"
        "    0.99 if int(row['call']) == int(row['founder']) else 0.01 for row in panel\n"
        ")\n"
        "(ROOT / 'likelihood.txt').write_text(str(LIKELIHOOD))\n",
        encoding="utf-8",
    )
    (repository / "markers.csv").write_text("call,founder\n0,0\n1,1\n", encoding="utf-8")
    (repository / "report.md").write_text(
        "The parental marker panel as supplied and the progeny calls were compared marker "
        "by marker: 372 of the 480 markers agree.\n\n"
        "The emission model used a per-marker agreement rate of 0.225.\n",
        encoding="utf-8",
    )

    bundle = _lock_method_authority(repository, schema_root, tmp_path)

    promoted = [
        result for result in bundle["detector_results"] if result["state"] == "finding_candidate"
    ]
    assert len(promoted) == 1
    assert len(bundle["findings"]) == 1
    assert bundle["coverage_records"][0]["assessment_counts"]["findings"] == 1


def test_test_local_exact_pin_admits_one_finding_and_replaces_result(
    project_root: Path,
    candidate: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    binding, manifest, metric_set, qualification = _records(project_root, candidate)
    pin = _pin(binding, metric_set, qualification)
    locked = _locked_candidate_case(manifest, binding)
    monkeypatch.setattr(grant_pins, "GRANT_PINS", {binding.binding_id: pin})
    monkeypatch.setattr(
        grant_pins,
        "load_method_conflict_grant_evidence",
        lambda installed: (qualification, metric_set) if installed == pin else None,
    )

    evaluation = _evaluate_general_detectors(locked)

    assert len(evaluation.results) == 1
    assert evaluation.results[0]["state"] == "finding_candidate"
    assert len(evaluation.findings) == 1
    assert evaluation.findings[0]["detector_result_ids"] == [evaluation.results[0]["result_id"]]
    assert len({item["result_id"] for item in evaluation.results}) == 1
    _validate_detector_projection(
        {
            "detector_manifests": [manifest],
            "detector_results": list(evaluation.results),
            "findings": list(evaluation.findings),
        }
    )


def test_policy_rejects_forged_validated_method_result_without_grant_linkage(
    project_root: Path, candidate: Path
) -> None:
    binding, manifest, metric_set, qualification = _records(project_root, candidate)
    del metric_set, qualification
    result = _evaluate_general_detectors(_locked_candidate_case(manifest, binding)).results[0]
    forged = copy.deepcopy(result)
    forged["state"] = "finding_candidate"
    forged["detector_maturity"] = "validated"
    forged["extensions"]["x-production-finding-permitted"] = True
    forged["extensions"]["x-evaluation-only"] = False

    with pytest.raises(ReportContractError, match="installed exact grant"):
        _validate_detector_projection(
            {
                "detector_manifests": [manifest],
                "detector_results": [forged],
                "findings": [],
            }
        )


def test_policy_rejects_duplicate_method_result_identity(
    project_root: Path, candidate: Path
) -> None:
    binding, manifest, metric_set, qualification = _records(project_root, candidate)
    del metric_set, qualification
    result = _evaluate_general_detectors(_locked_candidate_case(manifest, binding)).results[0]

    with pytest.raises(ReportContractError, match="duplicated"):
        _validate_detector_projection(
            {
                "detector_manifests": [manifest],
                "detector_results": [result, copy.deepcopy(result)],
                "findings": [],
            }
        )


def test_sibling_binding_grant_cannot_promote_result_for_another_question(
    project_root: Path, candidate: Path
) -> None:
    binding, manifest, metric_set, qualification = _records(project_root, candidate)
    grant = resolve_method_conflict_qualification(
        binding=binding,
        detector_manifest=manifest,
        qualification=qualification,
        metric_set=metric_set,
        pin=_pin(binding, metric_set, qualification),
    )
    assert grant is not None
    sibling = next(
        item
        for item in scientific_check_release_registry().method_conflict_bindings
        if item.check_id != binding.check_id
    )
    sibling_grant = replace(
        grant,
        binding_id=sibling.binding_id,
        binding_digest=sibling.binding_digest,
    )
    work_packet = {
        "profile": "bounded_analysis_method_conflict_work_packet_v1",
        "audit_run_id": "audit:sibling-binding-test",
        "detector_id": binding.detector_id,
        "detector_version": binding.detector_version,
        "detector_manifest_digest": binding.detector_manifest_digest,
        "target_question": {
            "record_type": "material_question",
            "question_id": "question:founder-binding-test",
            "status": "answered",
            "extensions": {"x-scientific-check-id": binding.check_id},
        },
    }
    input_digest = semantic_digest(work_packet)
    result = {
        "record_type": "detector_result",
        "result_id": stable_id(
            "detector-result",
            binding.detector_id,
            binding.detector_version,
            "question:founder-binding-test",
            input_digest,
        ),
        "audit_run_id": "audit:sibling-binding-test",
        "state": "evaluation_finding_candidate",
        "detector_maturity": "experimental",
        "detector_id": binding.detector_id,
        "detector_version": binding.detector_version,
        "detector_manifest_digest": binding.detector_manifest_digest,
        "deterministic_input_digest": input_digest,
        "candidate": {"assessment_type": "finding"},
        "extensions": {"x-review-case-digest": "sha256:" + "5" * 64},
    }
    assert (
        project_qualified_method_conflict_candidate(
            result,
            sibling,
            sibling_grant,
            work_packet=work_packet,
        )
        is None
    )


@pytest.mark.parametrize(
    ("target", "mutation"),
    [
        ("qualification", lambda value: value.update(outcome="deferred")),
        ("qualification", lambda value: value.update(binding_scope=None)),
        (
            "qualification",
            lambda value: value["safety_gates"].update(
                no_known_high_or_critical_false_accusations=False
            ),
        ),
        ("metric", lambda value: value.update(promotion_evidence_eligible=False)),
        ("metric", lambda value: value.update(corpus_partitions=["public_development"])),
        (
            "metric",
            lambda value: next(
                item
                for item in value["metrics"]
                if item["metric_name"] == "adjudicated_root_recall"
            ).update(estimate=0.5),
        ),
        (
            "metric",
            lambda value: value["numeric_threshold_policy"].update(
                policy_semantic_digest="sha256:" + "0" * 64
            ),
        ),
    ],
)
def test_missing_drifted_or_failed_evidence_never_resolves_a_grant(
    project_root: Path,
    candidate: Path,
    target: str,
    mutation: Any,
) -> None:
    binding, manifest, metric_set, qualification = _records(project_root, candidate)
    pin = _pin(binding, metric_set, qualification)
    mutation(qualification if target == "qualification" else metric_set)
    assert (
        resolve_method_conflict_qualification(
            binding=binding,
            detector_manifest=manifest,
            qualification=qualification,
            metric_set=metric_set,
            pin=pin,
        )
        is None
    )


def test_resolver_refuses_absent_or_drifted_external_pin_and_absolute_counts(
    project_root: Path, candidate: Path
) -> None:
    binding, manifest, metric_set, qualification = _records(project_root, candidate)
    pin = _pin(binding, metric_set, qualification)
    arguments = {
        "binding": binding,
        "detector_manifest": manifest,
        "qualification": qualification,
        "metric_set": metric_set,
    }
    assert resolve_method_conflict_qualification(**arguments, pin=None) is None
    assert (
        resolve_method_conflict_qualification(
            **arguments,
            pin=replace(pin, threshold_policy_digest="sha256:" + "0" * 64),
        )
        is None
    )
    drifted_adapter = replace(
        pin.exam_adapter_identity[0], implementation_digest="sha256:" + "0" * 64
    )
    assert (
        resolve_method_conflict_qualification(
            **arguments,
            pin=replace(
                pin,
                exam_adapter_identity=(drifted_adapter, *pin.exam_adapter_identity[1:]),
            ),
        )
        is None
    )
    missed = copy.deepcopy(metric_set)
    missed["counts"]["missed_roots"] = 1
    assert (
        resolve_method_conflict_qualification(
            binding=binding,
            detector_manifest=manifest,
            qualification=qualification,
            metric_set=missed,
            pin=pin,
        )
        is None
    )
    wrong_root_count = copy.deepcopy(metric_set)
    wrong_root_count["counts"]["adjudicated_roots"] = 3
    assert (
        resolve_method_conflict_qualification(
            binding=binding,
            detector_manifest=manifest,
            qualification=qualification,
            metric_set=wrong_root_count,
            pin=pin,
        )
        is None
    )


def test_absolute_missed_roots_gate_is_driven_by_the_installed_pin(
    project_root: Path, candidate: Path
) -> None:
    binding, manifest, metric_set, qualification = _records(project_root, candidate)
    pin = replace(
        _pin(binding, metric_set, qualification),
        absolute_missed_roots=1,
    )

    assert (
        resolve_method_conflict_qualification(
            binding=binding,
            detector_manifest=manifest,
            qualification=qualification,
            metric_set=metric_set,
            pin=pin,
        )
        is not None
    )


def test_required_roots_gate_is_driven_by_the_installed_pin(
    project_root: Path, candidate: Path
) -> None:
    binding, manifest, metric_set, qualification = _records(project_root, candidate)
    metric_set["counts"]["adjudicated_roots"] = 3
    pin = replace(
        _pin(binding, metric_set, qualification),
        required_roots=3,
    )

    assert (
        resolve_method_conflict_qualification(
            binding=binding,
            detector_manifest=manifest,
            qualification=qualification,
            metric_set=metric_set,
            pin=pin,
        )
        is not None
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("absolute_missed_roots", -1),
        ("absolute_missed_roots", True),
        ("required_roots", 0),
        ("required_roots", False),
    ],
)
def test_invalid_absolute_count_pin_fields_fail_closed(
    project_root: Path,
    candidate: Path,
    field: str,
    value: object,
) -> None:
    binding, manifest, metric_set, qualification = _records(project_root, candidate)
    pin = replace(_pin(binding, metric_set, qualification), **{field: value})

    assert (
        resolve_method_conflict_qualification(
            binding=binding,
            detector_manifest=manifest,
            qualification=qualification,
            metric_set=metric_set,
            pin=pin,
        )
        is None
    )
