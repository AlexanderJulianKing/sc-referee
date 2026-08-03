from __future__ import annotations

import copy
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from sc_referee.core.ids import semantic_digest, stable_id
from sc_referee.detectors.method_conflict_qualification import (
    project_qualified_method_conflict_candidate,
    resolve_method_conflict_qualification,
)
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.scientific_checks.profiles import scientific_check_release_registry
from scripts.build_method_promotion_schema_candidate import build_candidate


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
    metric_set["counts"].update({"workflows": 2, "problem_clusters": 2, "adjudicated_roots": 1})
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


def test_sibling_binding_grant_cannot_promote_result_for_another_question(
    project_root: Path, candidate: Path
) -> None:
    binding, manifest, metric_set, qualification = _records(project_root, candidate)
    grant = resolve_method_conflict_qualification(
        binding=binding,
        detector_manifest=manifest,
        qualification=qualification,
        metric_set=metric_set,
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
    mutation(qualification if target == "qualification" else metric_set)
    assert (
        resolve_method_conflict_qualification(
            binding=binding,
            detector_manifest=manifest,
            qualification=qualification,
            metric_set=metric_set,
        )
        is None
    )
