from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation.complete_domain_promotion import (
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
from sc_referee.detectors.method_conflict_grant_pins import (
    GRANT_PINS,
    GrantPin,
    installed_pin_matches_live_identity,
    live_adapter_identity,
)
from sc_referee.detectors.method_conflict_qualification import (
    resolve_method_conflict_qualification,
)
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.scientific_checks.profiles import scientific_check_release_registry

LANE = Path("evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane-v2")
LEDGER = LANE / "heldout-v207-seven-case/detector-run/DETECTOR_RUN_LEDGER.json"
AUTHORING = LANE / "heldout-v207-seven-case/authoring/AUTHORING_PROTOCOL.json"
PROMOTION = LANE / "promotion"
PROMOTION_ROUND2_V021 = LANE / "promotion-round2-v021"
OPENING = LANE / "heldout-v207-seven-case/HELDOUT_OPENING.json"
FROZEN_DETECTOR_MANIFESTS = (
    LANE / "heldout-v207-seven-case/detector-run/runs/0e8a84e424013c876694/"
    "audit/derived/detector-manifest.jsonl"
)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


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


def test_round1_private_records_rederive_but_require_v019_restamp(
    project_root: Path,
) -> None:
    metric_set = _load(project_root / PROMOTION / "QUALIFICATION_METRIC_SET.json")
    qualification = _load(project_root / PROMOTION / "DETECTOR_QUALIFICATION.json")
    expected_metric_set, expected_qualification = build_round1_records(
        project_root / LEDGER, recorded_at=str(qualification["decided_at"])
    )
    assert metric_set == expected_metric_set
    assert qualification == expected_qualification

    current_manifest_collection = _load(
        project_root / "src/sc_referee/resources/capability-manifests-v1/detector-manifests.json"
    )
    current_detector_manifest = next(
        record
        for record in current_manifest_collection["records"]
        if record["detector_id"] == "detector:bounded-analysis-method-conflict"
    )
    current_binding = next(
        item
        for item in scientific_check_release_registry().method_conflict_bindings
        if item.binding_id == "method-conflict-binding:complete-domain-exposure-denominator-v1"
    )
    frozen_detector_manifest = next(
        json.loads(line)
        for line in (project_root / FROZEN_DETECTOR_MANIFESTS).read_text().splitlines()
        if json.loads(line).get("detector_id") == "detector:bounded-analysis-method-conflict"
    )
    frozen_binding = replace(
        current_binding,
        detector_manifest_digest=DETECTOR_MANIFEST_DIGEST,
    )

    grant = resolve_method_conflict_qualification(
        binding=frozen_binding,
        detector_manifest=frozen_detector_manifest,
        qualification=qualification,
        metric_set=metric_set,
        pin=_pin(frozen_binding, metric_set, qualification),
    )

    assert grant is None
    assert (
        resolve_method_conflict_qualification(
            binding=current_binding,
            detector_manifest=current_detector_manifest,
            qualification=qualification,
            metric_set=metric_set,
            pin=_pin(frozen_binding, metric_set, qualification),
        )
        is None
    )
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


def test_v021_round2_records_resolve_the_installed_complete_domain_grant(
    project_root: Path,
) -> None:
    metric_set = _load(project_root / PROMOTION_ROUND2_V021 / "QUALIFICATION_METRIC_SET.json")
    qualification = _load(project_root / PROMOTION_ROUND2_V021 / "DETECTOR_QUALIFICATION.json")
    registry = LocalSchemaRegistry(project_root / "reference/schemas-v0.21.0")
    registry.validate(metric_set)
    registry.validate(qualification)

    detector_manifest = next(
        record
        for record in _load(
            project_root
            / "src/sc_referee/resources/capability-manifests-v1/detector-manifests.json"
        )["records"]
        if record["detector_id"] == "detector:bounded-analysis-method-conflict"
    )
    bindings = scientific_check_release_registry().method_conflict_bindings
    binding = next(
        item
        for item in bindings
        if item.binding_id == "method-conflict-binding:complete-domain-exposure-denominator-v1"
    )
    pin = GRANT_PINS[binding.binding_id]
    assert installed_pin_matches_live_identity(pin) is True
    assert semantic_digest(metric_set) == pin.metric_set_digest
    assert semantic_digest(qualification) == pin.qualification_digest
    grant = resolve_method_conflict_qualification(
        binding=binding,
        detector_manifest=detector_manifest,
        qualification=qualification,
        metric_set=metric_set,
        pin=pin,
    )
    assert grant is not None
    assert grant.qualification_id == qualification["qualification_id"]
    assert qualification["author_actor_ids"] == [
        "actor:heldout-claude-04",
        "actor:heldout-claude-05",
        "actor:heldout-claude-06",
        "actor:heldout-codex-04",
        "actor:heldout-codex-05",
        "actor:heldout-codex-06",
    ]
    assert qualification["agent_adjudication_refs"] == []
    assert qualification["evaluation_refs"]
    assert qualification["qualification_proof_families"] == ["static_closed_scope"]
    assert qualification["static_scope_disclosure"]["stage3_comparison_artifact_exists"] is False

    for sibling in bindings:
        if sibling.binding_id != binding.binding_id:
            assert (
                resolve_method_conflict_qualification(
                    binding=sibling,
                    detector_manifest=detector_manifest,
                    qualification=qualification,
                    metric_set=metric_set,
                    pin=pin,
                )
                is None
            )

    adr = (
        project_root
        / "docs/implementation/ADR-0076-CONTRACT-BOUND-REPORT-CSV-PSEUDOREPLICATION-FINDING.md"
    ).read_text(encoding="utf-8")
    assert "Accepted v0.20.0 schema and Envelope 5 installation amendment" in adr


def test_round1_policy_derives_the_frozen_sensitivity_bar_from_heldout_opening(
    project_root: Path,
) -> None:
    opening = _load(project_root / OPENING)
    metric_set = _load(project_root / PROMOTION / "QUALIFICATION_METRIC_SET.json")
    bar = opening["adr_reference"]["sensitivity_bar"]
    prefix = "at_least_"
    suffix = "_positives"
    assert isinstance(bar, str) and bar.startswith(prefix) and bar.endswith(suffix)
    numerator_word, denominator_word = bar[len(prefix) : -len(suffix)].split("_of_")
    word_counts = {"one": 1, "two": 2}
    expected_numerator = word_counts[numerator_word]
    expected_denominator = word_counts[denominator_word]
    recall_requirement = next(
        requirement
        for requirement in metric_set["numeric_threshold_policy"]["metric_requirements"]
        if requirement["metric_name"] == "adjudicated_root_recall"
    )
    achieved_recall = next(
        metric
        for metric in metric_set["metrics"]
        if metric["metric_name"] == "adjudicated_root_recall"
    )

    assert recall_requirement["threshold"] == expected_numerator / expected_denominator
    assert (
        metric_set["numeric_threshold_policy"]["minimum_counts"]["adjudicated_roots"]
        == expected_denominator
    )
    assert achieved_recall["estimate"] == 1.0


def test_round2_installs_exact_binding_authority_while_detector_stays_experimental(
    project_root: Path,
) -> None:
    qualification_manifest = (
        project_root
        / "src/sc_referee/resources/capability-manifests-v1/qualification-manifests.json"
    )
    records = _load(qualification_manifest)["records"]
    assert {record["qualification_id"] for record in records} == {
        "qualification:authorized-independent-unit-entry-v310-code-csv-envelope9",
        "qualification:complete-domain-exposure-denominator-v207-round2",
    }

    matrix = generate_capability_matrix(
        default_capability_manifest_root(), project_root / "reference/schemas-v0.21.0"
    )
    method_entry = next(
        item
        for item in matrix["entries"]
        if item["entry_id"] == "capability:bounded-analysis-method-conflict-v1"
    )
    assert method_entry["detectors"][0]["maturity"] == "experimental"
    assert method_entry["detectors"][0]["qualification_ref"] is None
    assert method_entry["detectors"][0]["strongest_output_type"] == "disclosure"
    grants = method_entry["detectors"][0]["binding_grants"]
    assert len(grants) == 1
    assert {grant["binding_id"] for grant in grants} == {
        "method-conflict-binding:complete-domain-exposure-denominator-v1"
    }
