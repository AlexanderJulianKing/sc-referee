from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation.cli import main as evaluation_main
from sc_referee_evaluation.grader import ExactJsonGraderError, grade_exact_json_output

from sc_referee.core.ids import semantic_digest
from sc_referee.records.observed import build_file_records
from sc_referee.snapshot.repository import SnapshotOutput, capture_repository


def _example(project_root: Path, name: str) -> dict[str, Any]:
    return json.loads(
        (project_root / "reference" / "schemas-v0.21.0" / "examples" / name).read_text(
            encoding="utf-8"
        )
    )


def _grade_inputs(
    project_root: Path,
    tmp_path: Path,
    *,
    result_text: str | None = None,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    SnapshotOutput,
    list[dict[str, Any]],
    dict[str, Any],
]:
    source = tmp_path / "fixture-source"
    source.mkdir(parents=True)
    payload = result_text or (json.dumps({"effect": -0.42, "nested": {"a/b": [1, 2, 3]}}) + "\n")
    (source / "result.json").write_text(payload, encoding="utf-8")
    snapshot = capture_repository(
        source,
        tmp_path / "captured",
        "audit:json-grader",
        captured_at="2026-07-27T17:00:00Z",
    )
    file_records = build_file_records(
        snapshot.file_records,
        snapshot.asset_identity_records,
        str(snapshot.snapshot_record["snapshot_id"]),
        "2026-07-27T17:00:00Z",
    )
    fixture = _example(project_root, "benchmark-fixture.example.json")
    adjudication = _example(project_root, "benchmark-adjudication.example.json")
    fixture.update(
        {
            "fixture_id": "fixture:exact-json-grade",
            "fixture_kind": "positive_issue_fixture",
            "qualification_proof_status": "legacy_proof_projection_unavailable",
            "proof_evidence": None,
            "execution_evidence": "not_executed",
            "expected_issue_labels": ["claim_result_agreement"],
            "expected_root_cause_refs": deepcopy(adjudication["adjudicated_root_cause_refs"]),
            "snapshot_ref": {
                "record_type": "repository_snapshot",
                "record_id": snapshot.snapshot_record["snapshot_id"],
            },
            "adjudication_ref": {
                "record_type": "benchmark_adjudication",
                "record_id": adjudication["adjudication_id"],
            },
        }
    )
    fixture["proof_obligations"]["positive_root_cause_documented"] = True
    spec = {
        "case_id": adjudication["case_id"],
        "fixture_id": fixture["fixture_id"],
        "comparison_profile": "exact_canonical_json_v1",
        "actual": {"path": "result.json", "json_pointer": "/effect"},
        "expected_value": -0.42,
    }
    return fixture, adjudication, snapshot, file_records, spec


def test_exact_json_grader_observes_match_and_mismatch_without_scientific_inference(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    fixture, adjudication, snapshot, file_records, spec = _grade_inputs(project_root, tmp_path)

    matched = grade_exact_json_output(
        fixture,
        adjudication,
        snapshot.snapshot_record,
        file_records,
        snapshot.asset_identity_records,
        snapshot.materialized_root,
        spec,
        schema_root,
        graded_at="2026-07-27T18:00:00Z",
        output=tmp_path / "match.json",
    )
    mismatched_spec = deepcopy(spec)
    mismatched_spec["expected_value"] = -0.41
    mismatched = grade_exact_json_output(
        fixture,
        adjudication,
        snapshot.snapshot_record,
        file_records,
        snapshot.asset_identity_records,
        snapshot.materialized_root,
        mismatched_spec,
        schema_root,
        graded_at="2026-07-27T18:00:00Z",
        output=tmp_path / "mismatch.json",
    )

    assert matched["grade_status"] == "exact_match"
    assert matched["exact_match"] is True
    assert mismatched["grade_status"] == "exact_mismatch"
    assert mismatched["exact_match"] is False
    assert matched["actual"]["value_digest"] != mismatched["expected_value_digest"]
    assert matched["metric_eligible"] is False
    assert matched["project_code_executed"] is False
    assert "expected_value" not in matched
    digest = matched.pop("grade_digest")
    assert digest == semantic_digest(matched)


def test_exact_json_grader_rejects_snapshot_digest_and_pointer_drift(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    fixture, adjudication, snapshot, file_records, spec = _grade_inputs(project_root, tmp_path)
    target = snapshot.materialized_root / "result.json"
    original = target.read_bytes()
    target.write_text('{"effect": -0.41}\n', encoding="utf-8")

    with pytest.raises(ExactJsonGraderError, match="drift"):
        grade_exact_json_output(
            fixture,
            adjudication,
            snapshot.snapshot_record,
            file_records,
            snapshot.asset_identity_records,
            snapshot.materialized_root,
            spec,
            schema_root,
            graded_at="2026-07-27T18:00:00Z",
            output=tmp_path / "drift.json",
        )

    target.write_bytes(original)
    missing_pointer = deepcopy(spec)
    missing_pointer["actual"]["json_pointer"] = "/absent"
    with pytest.raises(ExactJsonGraderError, match="does not exist"):
        grade_exact_json_output(
            fixture,
            adjudication,
            snapshot.snapshot_record,
            file_records,
            snapshot.asset_identity_records,
            snapshot.materialized_root,
            missing_pointer,
            schema_root,
            graded_at="2026-07-27T18:00:00Z",
            output=tmp_path / "pointer.json",
        )

    duplicate_inputs = _grade_inputs(
        project_root,
        tmp_path / "duplicate-case",
        result_text='{"effect": -0.42, "effect": -0.41}\n',
    )
    (
        duplicate_fixture,
        duplicate_adjudication,
        duplicate_snapshot,
        duplicate_files,
        duplicate_spec,
    ) = duplicate_inputs
    with pytest.raises(ExactJsonGraderError, match="duplicate key"):
        grade_exact_json_output(
            duplicate_fixture,
            duplicate_adjudication,
            duplicate_snapshot.snapshot_record,
            duplicate_files,
            duplicate_snapshot.asset_identity_records,
            duplicate_snapshot.materialized_root,
            duplicate_spec,
            schema_root,
            graded_at="2026-07-27T18:00:00Z",
            output=tmp_path / "duplicate.json",
        )


def test_exact_json_grader_cli_is_canonical_and_write_once(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    fixture, adjudication, snapshot, file_records, spec = _grade_inputs(project_root, tmp_path)
    inputs = {
        "fixture": fixture,
        "adjudication": adjudication,
        "snapshot": snapshot.snapshot_record,
        "grader-spec": spec,
    }
    paths: dict[str, Path] = {}
    for label, record in inputs.items():
        path = tmp_path / f"{label}.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        paths[label] = path
    file_records_path = tmp_path / "file-records.jsonl"
    identity_path = tmp_path / "asset-identities.jsonl"
    file_records_path.write_text(
        "".join(json.dumps(record) + "\n" for record in file_records),
        encoding="utf-8",
    )
    identity_path.write_text(
        "".join(json.dumps(record) + "\n" for record in snapshot.asset_identity_records),
        encoding="utf-8",
    )
    output = tmp_path / "grade.json"
    arguments = [
        "grade-json",
        "--fixture",
        str(paths["fixture"]),
        "--adjudication",
        str(paths["adjudication"]),
        "--snapshot",
        str(paths["snapshot"]),
        "--file-records-jsonl",
        str(file_records_path),
        "--asset-identities-jsonl",
        str(identity_path),
        "--materialized-root",
        str(snapshot.materialized_root),
        "--grader-spec",
        str(paths["grader-spec"]),
        "--schema-root",
        str(schema_root),
        "--graded-at",
        "2026-07-27T18:00:00Z",
        "--output",
        str(output),
    ]

    assert evaluation_main(arguments) == 0
    persisted = json.loads(output.read_text(encoding="utf-8"))
    digest = persisted.pop("grade_digest")
    assert digest == semantic_digest(persisted)
    original = output.read_bytes()
    assert evaluation_main(arguments) == 2
    assert output.read_bytes() == original
