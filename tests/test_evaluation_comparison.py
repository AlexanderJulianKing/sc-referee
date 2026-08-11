from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation.cli import main as evaluation_main
from sc_referee_evaluation.comparison import (
    DetectorComparisonError,
    compare_detector_output,
)

from sc_referee.core.ids import semantic_digest


def _example(project_root: Path, name: str) -> dict[str, Any]:
    return json.loads(
        (project_root / "reference" / "schemas-v0.19.0" / "examples" / name).read_text(
            encoding="utf-8"
        )
    )


def _stage3_inputs(
    project_root: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    fixture = _example(project_root, "benchmark-fixture.example.json")
    adjudication = _example(project_root, "benchmark-adjudication.example.json")
    audit_bundle = _example(project_root, "audit-bundle.example.json")
    snapshot = _example(project_root, "repository-snapshot.example.json")
    audit_run = _example(project_root, "audit-run.terminal.example.json")
    audit_run.update(
        {
            "audit_run_id": audit_bundle["audit_run_id"],
            "state": "complete",
            "snapshot_ref": {
                "record_type": "repository_snapshot",
                "record_id": snapshot["snapshot_id"],
            },
        }
    )
    audit_run.pop("terminal_reason", None)
    audit_bundle["repository_snapshots"] = [snapshot]
    audit_bundle["audit_runs"] = [audit_run]
    fixture.update(
        {
            "fixture_id": "fixture:stage3-positive",
            "fixture_kind": "positive_issue_fixture",
            "qualification_proof_status": "legacy_proof_projection_unavailable",
            "proof_evidence": None,
            "execution_evidence": "not_executed",
            "expected_issue_labels": ["claim_result_disagreement"],
            "expected_root_cause_refs": deepcopy(adjudication["adjudicated_root_cause_refs"]),
            "scientific_contract_refs": [],
            "adjudication_ref": {
                "record_type": "benchmark_adjudication",
                "record_id": adjudication["adjudication_id"],
            },
            "snapshot_ref": {
                "record_type": "repository_snapshot",
                "record_id": snapshot["snapshot_id"],
            },
        }
    )
    fixture["declared_scope"] = {
        "claim_refs": [{"record_type": "claim", "record_id": "claim:1"}],
        "detector_ids": ["detector:claim-direction"],
        "issue_classes": ["claim_result_disagreement"],
        "operation_refs": [],
    }
    fixture["proof_obligations"]["positive_root_cause_documented"] = True
    label_freeze: dict[str, Any] = {
        "evaluation_protocol_version": "0.1.0",
        "record_type": "evaluation_scientific_label_freeze",
        "case_id": adjudication["case_id"],
        "stage1_freeze_digest": "sha256:" + "1" * 64,
        "stage2_reviews": [
            {"review_ref": deepcopy(review_ref)}
            for review_ref in adjudication["stage2_review_refs"]
        ],
        "adjudication_ref": {
            "record_type": "benchmark_adjudication",
            "record_id": adjudication["adjudication_id"],
        },
        "adjudication_digest": semantic_digest(adjudication),
        "adjudicated_root_causes": [
            {
                "root_cause_ref": deepcopy(root_ref),
                "root_cause_digest": "sha256:" + "2" * 64,
            }
            for root_ref in adjudication["adjudicated_root_cause_refs"]
        ],
        "label_status": adjudication["label_status"],
        "frozen_at": "2026-07-27T19:30:00Z",
        "detector_output_observed": False,
    }
    label_freeze["freeze_digest"] = semantic_digest(label_freeze)
    return fixture, adjudication, label_freeze, audit_bundle


def test_stage3_comparison_binds_post_freeze_detector_output_without_scoring(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    fixture, adjudication, label_freeze, audit_bundle = _stage3_inputs(project_root)

    comparison = compare_detector_output(
        fixture,
        adjudication,
        label_freeze,
        audit_bundle,
        "detector:claim-direction",
        schema_root,
        compared_at="2026-07-27T21:00:00Z",
        output=tmp_path / "stage3.json",
    )

    assert comparison["comparison_status"] == ("withheld_pending_independent_label_admission")
    assert comparison["metric_eligible"] is False
    assert comparison["detector_output_observed"] is True
    assert comparison["scientific_label"]["label_status"] == "positive_demonstrated"
    detector_output = comparison["detector_output"]
    assert detector_output["detector_result_state_counts"] == {"finding_candidate": 1}
    assert detector_output["exact_in_scope_finding_refs"] == [
        {"record_type": "finding", "record_id": "finding:claim-direction"}
    ]
    assert detector_output["exact_out_of_scope_finding_refs"] == []
    digest = comparison.pop("comparison_digest")
    assert digest == semantic_digest(comparison)
    assert label_freeze["detector_output_observed"] is False


def test_stage3_comparison_rejects_freeze_tampering_or_unresolved_result_refs(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    fixture, adjudication, label_freeze, audit_bundle = _stage3_inputs(project_root)
    tampered_freeze = deepcopy(label_freeze)
    tampered_freeze["label_status"] = "ambiguous_excluded"

    with pytest.raises(DetectorComparisonError, match="freeze digest"):
        compare_detector_output(
            fixture,
            adjudication,
            tampered_freeze,
            audit_bundle,
            "detector:claim-direction",
            schema_root,
            compared_at="2026-07-27T21:00:00Z",
            output=tmp_path / "tampered.json",
        )

    root_ref_drift = deepcopy(label_freeze)
    root_ref_drift["adjudicated_root_causes"][0]["root_cause_ref"]["record_id"] = (
        "adjudicated-root-cause:other"
    )
    root_ref_drift.pop("freeze_digest")
    root_ref_drift["freeze_digest"] = semantic_digest(root_ref_drift)
    with pytest.raises(DetectorComparisonError, match="root-cause refs"):
        compare_detector_output(
            fixture,
            adjudication,
            root_ref_drift,
            audit_bundle,
            "detector:claim-direction",
            schema_root,
            compared_at="2026-07-27T21:00:00Z",
            output=tmp_path / "root-ref-drift.json",
        )

    with pytest.raises(DetectorComparisonError, match="must occur after"):
        compare_detector_output(
            fixture,
            adjudication,
            label_freeze,
            audit_bundle,
            "detector:claim-direction",
            schema_root,
            compared_at="2026-07-27T19:30:00Z",
            output=tmp_path / "too-early.json",
        )

    wrong_snapshot_bundle = deepcopy(audit_bundle)
    wrong_snapshot_bundle["audit_runs"][0]["snapshot_ref"]["record_id"] = "snapshot:other"
    with pytest.raises(DetectorComparisonError, match="Fixture snapshot"):
        compare_detector_output(
            fixture,
            adjudication,
            label_freeze,
            wrong_snapshot_bundle,
            "detector:claim-direction",
            schema_root,
            compared_at="2026-07-27T21:00:00Z",
            output=tmp_path / "wrong-snapshot.json",
        )

    unresolved_bundle = deepcopy(audit_bundle)
    unresolved_bundle["findings"][0]["detector_result_ids"] = ["result:absent"]
    with pytest.raises(DetectorComparisonError, match="absent DetectorResult"):
        compare_detector_output(
            fixture,
            adjudication,
            label_freeze,
            unresolved_bundle,
            "detector:claim-direction",
            schema_root,
            compared_at="2026-07-27T21:00:00Z",
            output=tmp_path / "unresolved.json",
        )


def test_stage3_cli_persists_a_canonical_comparison(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    fixture, adjudication, label_freeze, audit_bundle = _stage3_inputs(project_root)
    inputs = {
        "fixture": fixture,
        "adjudication": adjudication,
        "label-freeze": label_freeze,
        "audit-bundle": audit_bundle,
    }
    paths: dict[str, Path] = {}
    for label, record in inputs.items():
        path = tmp_path / f"{label}.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        paths[label] = path
    output = tmp_path / "comparison.json"
    arguments = [
        "compare-stage3",
        "--fixture",
        str(paths["fixture"]),
        "--adjudication",
        str(paths["adjudication"]),
        "--label-freeze",
        str(paths["label-freeze"]),
        "--audit-bundle",
        str(paths["audit-bundle"]),
        "--detector-id",
        "detector:claim-direction",
        "--schema-root",
        str(schema_root),
        "--compared-at",
        "2026-07-27T21:00:00Z",
        "--output",
        str(output),
    ]

    assert evaluation_main(arguments) == 0
    persisted = json.loads(output.read_text(encoding="utf-8"))
    digest = persisted.pop("comparison_digest")
    assert digest == semantic_digest(persisted)
    original = output.read_bytes()
    assert evaluation_main(arguments) == 2
    assert output.read_bytes() == original
