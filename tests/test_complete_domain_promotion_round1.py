from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation.complete_domain_promotion import (
    BINDING_DIGEST,
    DETECTOR_MANIFEST_DIGEST,
    HELDOUT_LEDGER_DIGEST,
    CompleteDomainPromotionError,
    build_round1_records,
    project_heldout_detector_case_outcomes,
)

from sc_referee.capability_matrix import (
    default_capability_manifest_root,
    generate_capability_matrix,
)
from sc_referee.core.ids import canonical_json, semantic_digest
from sc_referee.detectors.method_conflict_qualification import (
    resolve_method_conflict_qualification,
)
from sc_referee.scientific_checks.profiles import scientific_check_release_registry

LANE = Path("evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane-v2")
LEDGER = LANE / "heldout-v207-seven-case/detector-run/DETECTOR_RUN_LEDGER.json"
PROMOTION = LANE / "promotion"
CAPABILITY_MATRIX_DIGEST_BEFORE_ROUND1 = (
    "sha256:4a3f3a74f295e899aace905c493c137a50e5545ac2be7b4e437ff2bedc19b968"
)
EMPTY_QUALIFICATION_MANIFEST = (
    b'{"manifest_kind":"detector_qualification_manifest_collection",'
    b'"manifest_version":"1.0.0","records":[]}\n'
)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_frozen_ledger_projects_seven_complete_heldout_outcomes(project_root: Path) -> None:
    outcomes = project_heldout_detector_case_outcomes(project_root / LEDGER)

    assert len(outcomes) == 7
    assert len({outcome["problem_id"] for outcome in outcomes}) == 7
    assert all(outcome["corpus_partition"] == "held_out" for outcome in outcomes)
    assert all(outcome["promotion_evidence_eligible"] is True for outcome in outcomes)
    assert sum(bool(outcome["candidate_refs"]) for outcome in outcomes) == 2
    assert sum(bool(outcome["root_cause_refs"]) for outcome in outcomes) == 2
    assert (
        sum(outcome["qualification_proof_family"] == "static_closed_scope" for outcome in outcomes)
        == 5
    )


def test_projector_refuses_ledger_byte_or_self_digest_drift(
    project_root: Path, tmp_path: Path
) -> None:
    ledger = _load(project_root / LEDGER)
    ledger["entries"][0]["finding_candidate_count"] = 1
    drifted = tmp_path / "DETECTOR_RUN_LEDGER.json"
    drifted.write_text(canonical_json(ledger) + "\n", encoding="utf-8")

    with pytest.raises(CompleteDomainPromotionError, match="digest"):
        project_heldout_detector_case_outcomes(drifted)

    ledger["ledger_digest"] = semantic_digest(
        {key: value for key, value in ledger.items() if key != "ledger_digest"}
    )
    drifted.write_text(canonical_json(ledger) + "\n", encoding="utf-8")
    assert ledger["ledger_digest"] != HELDOUT_LEDGER_DIGEST
    with pytest.raises(CompleteDomainPromotionError, match="seal"):
        project_heldout_detector_case_outcomes(drifted)


def test_round1_private_records_rederive_and_resolve_exact_grant(project_root: Path) -> None:
    metric_set = _load(project_root / PROMOTION / "QUALIFICATION_METRIC_SET.json")
    qualification = _load(project_root / PROMOTION / "DETECTOR_QUALIFICATION.json")
    expected_metric_set, expected_qualification = build_round1_records(
        project_root / LEDGER, recorded_at=str(qualification["decided_at"])
    )
    assert metric_set == expected_metric_set
    assert qualification == expected_qualification

    manifest_collection = _load(
        project_root / "src/sc_referee/resources/capability-manifests-v1/detector-manifests.json"
    )
    detector_manifest = next(
        record
        for record in manifest_collection["records"]
        if record["detector_id"] == "detector:bounded-analysis-method-conflict"
    )
    binding = next(
        item
        for item in scientific_check_release_registry().method_conflict_bindings
        if item.binding_id == "method-conflict-binding:complete-domain-exposure-denominator-v1"
    )

    grant = resolve_method_conflict_qualification(
        binding=binding,
        detector_manifest=detector_manifest,
        qualification=qualification,
        metric_set=metric_set,
    )

    assert grant is not None
    assert grant.qualification_id == qualification["qualification_id"]
    assert grant.metric_set_id == metric_set["metric_set_id"]
    assert grant.binding_digest == BINDING_DIGEST
    assert grant.detector_manifest_digest == DETECTOR_MANIFEST_DIGEST
    assert grant.maturity == "validated"
    assert metric_set["counts"] == {
        "abstentions": 1,
        "adjudicated_roots": 2,
        "applicable_covered_opportunities": 5,
        "bounded_root_matches": 2,
        "boundedly_localized_roots": 2,
        "detector_errors": 0,
        "evaluation_candidates": 2,
        "false_root_localizations": 0,
        "localized_but_overstated_roots": 0,
        "missed_roots": 0,
        "opportunities": 7,
        "overstated_root_matches": 0,
        "problem_clusters": 7,
        "unresolved_comparisons": 0,
        "unsupported_opportunities": 1,
        "workflows": 7,
    }
    assert qualification["safety_gates"] == {
        "cluster_aware_uncertainty_reported": True,
        "conditional_never_promoted": True,
        "decisive_counterevidence_included": True,
        "no_known_high_or_critical_false_accusations": True,
        "proof_families_stratified": True,
        "public_development_cases_not_used_for_qualification": True,
        "qualification_report_public": True,
        "regression_fixture_for_every_discovered_false_accusation": True,
        "unresolved_disagreement_excluded": True,
        "verified_good_and_hard_negative_included": True,
    }


def test_round1_does_not_install_authority_or_change_capability_matrix(
    project_root: Path,
) -> None:
    qualification_manifest = (
        project_root
        / "src/sc_referee/resources/capability-manifests-v1/qualification-manifests.json"
    )
    assert qualification_manifest.read_bytes() == EMPTY_QUALIFICATION_MANIFEST
    assert _load(qualification_manifest)["records"] == []

    matrix = generate_capability_matrix(
        default_capability_manifest_root(), project_root / "reference/schemas-v0.18.0"
    )
    assert semantic_digest(matrix) == CAPABILITY_MATRIX_DIGEST_BEFORE_ROUND1
    method_entry = next(
        item
        for item in matrix["entries"]
        if item["entry_id"] == "capability:bounded-analysis-method-conflict-v1"
    )
    assert method_entry["detectors"][0]["maturity"] == "experimental"
    assert method_entry["detectors"][0]["qualification_ref"] is None
    assert method_entry["detectors"][0]["strongest_output_type"] == "disclosure"
