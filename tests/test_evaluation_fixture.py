from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation.cli import main as evaluation_main
from sc_referee_evaluation.fixture import FixtureGenerationError, generate_ambiguous_fixture

from sc_referee.records.observed import build_file_records
from sc_referee.snapshot.repository import SnapshotOutput, capture_repository


def _example(project_root: Path, name: str) -> dict[str, Any]:
    return json.loads(
        (project_root / "reference" / "schemas-v0.21.0" / "examples" / name).read_text(
            encoding="utf-8"
        )
    )


def _ambiguous_inputs(
    project_root: Path, tmp_path: Path
) -> tuple[dict[str, Any], SnapshotOutput, list[dict[str, Any]], dict[str, Any]]:
    source = tmp_path / "case-source"
    source.mkdir()
    (source / "workflow.txt").write_text("Unresolved scientific workflow.\n", encoding="utf-8")
    snapshot = capture_repository(
        source,
        tmp_path / "captured",
        "audit:ambiguous-fixture",
        captured_at="2026-07-27T17:00:00Z",
    )
    file_records = build_file_records(
        snapshot.file_records,
        snapshot.asset_identity_records,
        str(snapshot.snapshot_record["snapshot_id"]),
        "2026-07-27T17:00:00Z",
    )
    adjudication = _example(project_root, "benchmark-adjudication.example.json")
    adjudication.update(
        {
            "label_status": "ambiguous_excluded",
            "adjudicated_root_cause_refs": [],
            "root_cause_reconciliation_status": "unresolved",
            "exclusion_reason": "A material scientific interpretation remains unresolved.",
            "adjudicated_at": "2026-07-27T19:00:00Z",
        }
    )
    adjudication["agreement"].update(
        {"cross_provider_support": False, "material_disagreement": True}
    )
    for key in adjudication["deterministic_checks"]:
        adjudication["deterministic_checks"][key] = False
    fixture_spec = {
        "problem_id": "problem:ambiguous-1",
        "declared_scope": {
            "claim_refs": [],
            "detector_ids": ["detector:claim-direction"],
            "issue_classes": ["claim_result_disagreement"],
            "operation_refs": [],
        },
        "scientific_contract_refs": [],
        "limitations": ["The intended contrast orientation remains unresolved."],
    }
    return adjudication, snapshot, file_records, fixture_spec


def test_ambiguous_fixture_generator_emits_only_an_excluded_nonexecuted_fixture(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    adjudication, snapshot, file_records, fixture_spec = _ambiguous_inputs(project_root, tmp_path)

    fixture = generate_ambiguous_fixture(
        adjudication,
        snapshot.snapshot_record,
        file_records,
        snapshot.asset_identity_records,
        fixture_spec,
        schema_root,
        created_at="2026-07-27T20:00:00Z",
        output=tmp_path / "fixture.json",
    )

    assert fixture["fixture_kind"] == "ambiguous_fixture"
    assert fixture["expected_issue_labels"] == []
    assert fixture["execution_evidence"] == "not_executed"
    assert fixture["global_correctness_claim_allowed"] is False
    assert not any(fixture["proof_obligations"].values())
    assert fixture["snapshot_ref"]["record_id"] == snapshot.snapshot_record["snapshot_id"]
    assert fixture["adjudication_ref"]["record_id"] == adjudication["adjudication_id"]


def test_ambiguous_fixture_generator_rejects_eligible_labels_or_snapshot_drift(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    adjudication, snapshot, file_records, fixture_spec = _ambiguous_inputs(project_root, tmp_path)
    eligible = deepcopy(adjudication)
    eligible.update(
        {
            "label_status": "positive_demonstrated",
            "adjudicated_root_cause_refs": [
                {
                    "record_type": "adjudicated_root_cause",
                    "record_id": "adjudicated-root-cause:fixture-test",
                }
            ],
            "root_cause_reconciliation_status": "verified",
            "exclusion_reason": None,
        }
    )
    eligible["agreement"].update({"cross_provider_support": True, "material_disagreement": False})
    for key in eligible["deterministic_checks"]:
        eligible["deterministic_checks"][key] = True
    with pytest.raises(FixtureGenerationError, match="only excluded ambiguous"):
        generate_ambiguous_fixture(
            eligible,
            snapshot.snapshot_record,
            file_records,
            snapshot.asset_identity_records,
            fixture_spec,
            schema_root,
            created_at="2026-07-27T20:00:00Z",
            output=tmp_path / "eligible.json",
        )

    drifted_snapshot = deepcopy(snapshot.snapshot_record)
    drifted_snapshot["snapshot_digest"] = "sha256:" + "0" * 64
    with pytest.raises(FixtureGenerationError, match="RepositorySnapshot digest"):
        generate_ambiguous_fixture(
            adjudication,
            drifted_snapshot,
            file_records,
            snapshot.asset_identity_records,
            fixture_spec,
            schema_root,
            created_at="2026-07-27T20:00:00Z",
            output=tmp_path / "drifted.json",
        )


def test_ambiguous_fixture_cli_is_canonical_and_write_once(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    adjudication, snapshot, file_records, fixture_spec = _ambiguous_inputs(project_root, tmp_path)
    records = {
        "adjudication": adjudication,
        "snapshot": snapshot.snapshot_record,
        "fixture-spec": fixture_spec,
    }
    paths: dict[str, Path] = {}
    for label, record in records.items():
        path = tmp_path / f"{label}.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        paths[label] = path
    file_records_path = tmp_path / "file-records.jsonl"
    identities_path = tmp_path / "asset-identities.jsonl"
    file_records_path.write_text(
        "".join(json.dumps(record) + "\n" for record in file_records),
        encoding="utf-8",
    )
    identities_path.write_text(
        "".join(json.dumps(record) + "\n" for record in snapshot.asset_identity_records),
        encoding="utf-8",
    )
    output = tmp_path / "fixture.json"
    arguments = [
        "generate-ambiguous-fixture",
        "--adjudication",
        str(paths["adjudication"]),
        "--snapshot",
        str(paths["snapshot"]),
        "--file-records-jsonl",
        str(file_records_path),
        "--asset-identities-jsonl",
        str(identities_path),
        "--fixture-spec",
        str(paths["fixture-spec"]),
        "--schema-root",
        str(schema_root),
        "--created-at",
        "2026-07-27T20:00:00Z",
        "--output",
        str(output),
    ]

    assert evaluation_main(arguments) == 0
    persisted = json.loads(output.read_text(encoding="utf-8"))
    assert persisted["record_type"] == "benchmark_fixture"
    original = output.read_bytes()
    assert evaluation_main(arguments) == 2
    assert output.read_bytes() == original
