from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation.dependence_promotion import (
    ADAPTER_ID,
    ADAPTER_IMPLEMENTATION_DIGEST,
    ADAPTER_MANIFEST_DIGEST,
    ADAPTER_VERSION,
    AUTHORING_PROTOCOL_DIGEST,
    BINDING_DIGEST,
    BINDING_ID,
    CHECK_ID,
    CHECK_MANIFEST_DIGEST,
    DETECTOR_MANIFEST_DIGEST,
    DETECTOR_TUPLE_DIGEST,
    HELDOUT_LEDGER_DIGEST,
    HELDOUT_OPENING_DIGEST,
    RECOGNITION_GRAMMAR_DIGEST,
    REGISTRY_CONTENT_DIGEST,
    DependencePromotionError,
    build_round1_records,
    numeric_threshold_policy,
    project_heldout_detector_case_outcomes,
    verify_absolute_missed_root_gate,
)

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.detectors.method_conflict_qualification import (
    resolve_method_conflict_qualification,
)
from sc_referee.scientific_checks.profiles import scientific_check_release_registry

LANE = Path(
    "evaluation/qualification/authorized-independent-unit-entry-into-row-independent-"
    "procedure-v1.1.0-direct-lane"
)
EXAM = LANE / "heldout-seven-case"
LEDGER = EXAM / "detector-run/DETECTOR_RUN_LEDGER.json"
OPENING = EXAM / "opening/DEPENDENCE_HELDOUT_OPENING.json"
AUTHORING = EXAM / "authoring/AUTHORING_PROTOCOL.json"
PROMOTION = LANE / "promotion"
FROZEN_DETECTOR_MANIFESTS = (
    EXAM / "detector-run/runs/8a68d6ae147ce49e2a11/audit/derived/detector-manifest.jsonl"
)
REGISTRY = Path("src/sc_referee/resources/scientific-check-manifests-v1/registry.json")
DETECTOR_MANIFESTS = Path(
    "src/sc_referee/resources/capability-manifests-v1/detector-manifests.json"
)
QUALIFICATION_MANIFESTS = Path(
    "src/sc_referee/resources/capability-manifests-v1/qualification-manifests.json"
)
REPORT = LANE / "QUALIFICATION_REPORT.md"
ADR = Path("docs/implementation/ADR-0073-DEPENDENCE-ENVELOPE-PROMOTION.md")
THRESHOLD_AUTHORING = LANE / "threshold-rehearsal/authoring/AUTHORING_PROTOCOL.json"
EMPTY_QUALIFICATION_MANIFEST = (
    b'{"manifest_kind":"detector_qualification_manifest_collection",'
    b'"manifest_version":"1.0.0","records":[]}\n'
)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _detector_manifest(collection: dict[str, Any]) -> dict[str, Any]:
    return next(
        record
        for record in collection["records"]
        if record["detector_id"] == "detector:bounded-analysis-method-conflict"
    )


def test_frozen_dependence_ledger_projects_seven_complete_outcomes(
    project_root: Path,
) -> None:
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
    states = {
        outcome["case_id"]: outcome["detector_result_outcomes"][0]["state"] for outcome in outcomes
    }
    assert states == {
        "case:6f1702f1e1ff3855d34f": "no_issue_detected_within_coverage",
        "case:75bb533785f478cbdd8d": "insufficient_semantics",
        "case:8a68d6ae147ce49e2a11": "evaluation_finding_candidate",
        "case:a516621a9cc0c4f6854d": "no_issue_detected_within_coverage",
        "case:c37ea6f502dc593de820": "evaluation_finding_candidate",
        "case:c41c53bc6fedd68b0ccc": "unsupported_path",
        "case:e9e6bf9e80c9287dabe5": "no_issue_detected_within_coverage",
    }


def test_projector_refuses_ledger_byte_or_self_digest_drift(
    project_root: Path, tmp_path: Path
) -> None:
    ledger = _load(project_root / LEDGER)
    ledger["entries"][0]["finding_candidate_count"] = 1
    drifted = tmp_path / "DETECTOR_RUN_LEDGER.json"
    drifted.write_text(canonical_json(ledger) + "\n", encoding="utf-8")

    with pytest.raises(DependencePromotionError, match="digest"):
        project_heldout_detector_case_outcomes(drifted)

    ledger["ledger_digest"] = semantic_digest(
        {key: value for key, value in ledger.items() if key != "ledger_digest"}
    )
    drifted.write_text(canonical_json(ledger) + "\n", encoding="utf-8")
    assert ledger["ledger_digest"] != HELDOUT_LEDGER_DIGEST
    with pytest.raises(DependencePromotionError, match="seal"):
        project_heldout_detector_case_outcomes(drifted)


def test_exam_time_detector_tuple_matches_live_registry_and_manifest(
    project_root: Path,
) -> None:
    authoring = _load(project_root / AUTHORING)
    detector_tuple = authoring["detector_tuple"]
    registry = _load(project_root / REGISTRY)
    current_module = next(item for item in registry["modules"] if item["check_id"] == CHECK_ID)
    current_binding = next(
        item for item in registry["method_conflict_bindings"] if item["binding_id"] == BINDING_ID
    )
    current_detector = _detector_manifest(_load(project_root / DETECTOR_MANIFESTS))
    frozen_detector = next(
        json.loads(line)
        for line in (project_root / FROZEN_DETECTOR_MANIFESTS).read_text().splitlines()
        if json.loads(line).get("detector_id") == "detector:bounded-analysis-method-conflict"
    )

    assert authoring["protocol_digest"] == AUTHORING_PROTOCOL_DIGEST
    assert authoring["detector_tuple_digest"] == DETECTOR_TUPLE_DIGEST
    assert detector_tuple["check_manifest_digest"] == CHECK_MANIFEST_DIGEST
    assert detector_tuple["method_conflict_binding_digest"] == BINDING_DIGEST
    assert detector_tuple["registry_content_digest"] == REGISTRY_CONTENT_DIGEST
    assert sha256_digest((project_root / REGISTRY).read_bytes()) == REGISTRY_CONTENT_DIGEST
    assert current_module["manifest_digest"] == CHECK_MANIFEST_DIGEST
    assert current_module["adapters"] == [
        {
            "adapter_id": ADAPTER_ID,
            "adapter_version": ADAPTER_VERSION,
            "implementation_digest": ADAPTER_IMPLEMENTATION_DIGEST,
            "manifest_digest": ADAPTER_MANIFEST_DIGEST,
            "recognition_grammar_digest": RECOGNITION_GRAMMAR_DIGEST,
        }
    ]
    assert detector_tuple["adapters"] == current_module["adapters"]
    assert current_binding["detector_manifest_digest"] == DETECTOR_MANIFEST_DIGEST
    assert semantic_digest(current_binding) == BINDING_DIGEST
    assert frozen_detector == current_detector
    assert semantic_digest(current_detector) == DETECTOR_MANIFEST_DIGEST


def test_round1_private_records_rederive_and_resolve_live_exact_grant(
    project_root: Path,
) -> None:
    metric_set = _load(project_root / PROMOTION / "QUALIFICATION_METRIC_SET.json")
    qualification = _load(project_root / PROMOTION / "DETECTOR_QUALIFICATION.json")
    expected_metric_set, expected_qualification = build_round1_records(
        project_root / LEDGER, recorded_at=str(qualification["decided_at"])
    )
    assert metric_set == expected_metric_set
    assert qualification == expected_qualification

    detector_manifest = _detector_manifest(_load(project_root / DETECTOR_MANIFESTS))
    bindings = scientific_check_release_registry().method_conflict_bindings
    binding = next(item for item in bindings if item.binding_id == BINDING_ID)
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


def test_sibling_bindings_and_simulated_current_drift_defeat_grant(
    project_root: Path,
) -> None:
    metric_set = _load(project_root / PROMOTION / "QUALIFICATION_METRIC_SET.json")
    qualification = _load(project_root / PROMOTION / "DETECTOR_QUALIFICATION.json")
    detector_manifest = _detector_manifest(_load(project_root / DETECTOR_MANIFESTS))
    bindings = scientific_check_release_registry().method_conflict_bindings
    target = next(item for item in bindings if item.binding_id == BINDING_ID)

    for sibling in bindings:
        if sibling.binding_id != BINDING_ID:
            assert (
                resolve_method_conflict_qualification(
                    binding=sibling,
                    detector_manifest=detector_manifest,
                    qualification=qualification,
                    metric_set=metric_set,
                )
                is None
            )

    drifted = replace(target, check_manifest_digest="sha256:" + "0" * 64)
    assert drifted.binding_digest != BINDING_DIGEST
    assert (
        resolve_method_conflict_qualification(
            binding=drifted,
            detector_manifest=detector_manifest,
            qualification=qualification,
            metric_set=metric_set,
        )
        is None
    )


def test_frozen_bars_and_absolute_missed_root_gate_are_enforced(
    project_root: Path,
) -> None:
    metric_set = _load(project_root / PROMOTION / "QUALIFICATION_METRIC_SET.json")
    policy = numeric_threshold_policy(project_root / OPENING)
    requirements = {item["metric_name"]: item for item in policy["metric_requirements"]}

    assert policy == metric_set["numeric_threshold_policy"]
    assert requirements["adjudicated_root_recall"] == {
        "metric_name": "adjudicated_root_recall",
        "statistic": "estimate",
        "operator": "at_least",
        "threshold": 1.0,
    }
    assert requirements["completed_opportunity_false_positive_rate"] == {
        "metric_name": "completed_opportunity_false_positive_rate",
        "statistic": "estimate",
        "operator": "at_most",
        "threshold": 0.0,
    }
    assert policy["minimum_counts"]["adjudicated_roots"] == 2
    assert policy["minimum_counts"]["control_cases"] == 5
    assert policy["absolute_count_requirements"] == [
        {"count_name": "missed_roots", "operator": "equals", "threshold": 0}
    ]
    threshold_authoring = _load(project_root / THRESHOLD_AUTHORING)
    exam_authoring = _load(project_root / AUTHORING)
    assert (
        datetime.fromisoformat(policy["frozen_at"].replace("Z", "+00:00"))
        < datetime.fromisoformat(threshold_authoring["frozen_at"].replace("Z", "+00:00"))
        < datetime.fromisoformat(exam_authoring["frozen_at"].replace("Z", "+00:00"))
    )

    missed = json.loads(json.dumps(metric_set))
    missed["counts"]["missed_roots"] = 1
    with pytest.raises(DependencePromotionError, match="missed-root"):
        verify_absolute_missed_root_gate(missed)

    malformed = json.loads(json.dumps(metric_set))
    malformed["numeric_threshold_policy"]["absolute_count_requirements"] = []
    with pytest.raises(DependencePromotionError, match="missed-root"):
        verify_absolute_missed_root_gate(malformed)


def test_opening_digest_or_bar_drift_refuses_policy(project_root: Path, tmp_path: Path) -> None:
    opening = _load(project_root / OPENING)
    opening["adr_reference"]["sensitivity_bar"] = "one_of_two_positives"
    opening["semantic_digest"] = semantic_digest(
        {key: value for key, value in opening.items() if key != "semantic_digest"}
    )
    drifted = tmp_path / "DEPENDENCE_HELDOUT_OPENING.json"
    drifted.write_text(canonical_json(opening) + "\n", encoding="utf-8")
    assert opening["semantic_digest"] != HELDOUT_OPENING_DIGEST
    with pytest.raises(DependencePromotionError, match="seal"):
        numeric_threshold_policy(drifted)


def test_round1_records_do_not_install_or_generalize_authority(project_root: Path) -> None:
    assert (project_root / QUALIFICATION_MANIFESTS).read_bytes() == EMPTY_QUALIFICATION_MANIFEST
    assert _load(project_root / QUALIFICATION_MANIFESTS)["records"] == []
    registry = _load(project_root / REGISTRY)
    target = next(
        item for item in registry["method_conflict_bindings"] if item["binding_id"] == BINDING_ID
    )
    detector = _detector_manifest(_load(project_root / DETECTOR_MANIFESTS))
    assert target["production_finding_permitted"] is False
    assert detector["maturity"] == "experimental"
    assert detector["validation"]["qualification_record_ref"] is None


def test_public_report_retains_required_dependence_disclosures(project_root: Path) -> None:
    report = (project_root / REPORT).read_text(encoding="utf-8")
    required = (
        "Role-derived authority",
        "requirements.txt",
        "k1 namespace",
        "one-directional effect",
        "unblinded orchestrator",
        "Agent-only review",
        "Single-provider composition",
        "Acceptance before rehearsal",
        "sha256:8599661c954459daad710f61462ee3666dab8d9659f94e94714824ee6ad67c61",
        "sha256:7beb928087f8073f543636e0231e7fc57c1f9a843ea182107bf0b121a2e3d9d5",
    )
    assert all(item in report for item in required)


def test_adr_records_maintainer_quote_track_movement_and_resolved_digests(
    project_root: Path,
) -> None:
    adr = (project_root / ADR).read_text(encoding="utf-8")
    metric_set = _load(project_root / PROMOTION / "QUALIFICATION_METRIC_SET.json")
    qualification = _load(project_root / PROMOTION / "DETECTOR_QUALIFICATION.json")

    assert '"go ahead with the qualification report and promotion"' in adr
    assert "Track 1 remains **1/10 promoted**, unchanged" in adr
    assert "first capability family qualified and promoted" in adr
    assert semantic_digest(metric_set) in adr
    assert semantic_digest(qualification) in adr
    assert metric_set["numeric_threshold_policy"]["policy_semantic_digest"] in adr
