import json
import os
import sqlite3
from pathlib import Path

import pytest

from sc_referee.controller import run_demo
from sc_referee.records.normalization import write_normalized_json, write_normalized_json_once
from sc_referee.storage.integrity import (
    StorageIntegrityError,
    verify_sqlite_index,
    verify_storage_manifest,
)
from sc_referee.storage.jsonl import JsonlIntegrityError, JsonlRecordStore
from sc_referee.storage.layout import AuditLayout
from sc_referee.storage.sqlite_index import rebuild_sqlite, record_identity


def test_sqlite_is_rebuildable(tmp_path) -> None:
    records = [
        {"record_type": "claim", "claim_id": "claim:1", "value": 1},
        {"record_type": "finding", "finding_id": "finding:1", "value": 2},
    ]
    path = tmp_path / "audit.db"
    assert rebuild_sqlite(path, records) == 2
    first_connection = sqlite3.connect(path)
    first = first_connection.execute(
        "select record_type, record_id, digest from records order by record_type, record_id"
    ).fetchall()
    first_connection.close()
    path.unlink()
    assert rebuild_sqlite(path, records) == 2
    second_connection = sqlite3.connect(path)
    second = second_connection.execute(
        "select record_type, record_id, digest from records order by record_type, record_id"
    ).fetchall()
    second_connection.close()
    assert first == second
    assert [(row[0], row[1]) for row in first] == [
        ("claim", "claim:1"),
        ("finding", "finding:1"),
    ]


def test_sqlite_preserves_append_only_audit_run_states(tmp_path) -> None:
    records = [
        {"record_type": "audit_run", "audit_run_id": "audit:1", "state": "created"},
        {"record_type": "audit_run", "audit_run_id": "audit:1", "state": "complete"},
    ]
    path = tmp_path / "audit.db"
    assert rebuild_sqlite(path, records) == 2
    connection = sqlite3.connect(path)
    states = [
        json.loads(row[0])["state"]
        for row in connection.execute(
            "SELECT json_text FROM records WHERE record_type = 'audit_run' ORDER BY digest"
        ).fetchall()
    ]
    connection.close()
    assert sorted(states) == ["complete", "created"]
    verify_sqlite_index(path, records)


@pytest.mark.parametrize(
    ("record", "expected"),
    [
        (
            {
                "record_type": "parser_result",
                "parser_result_id": "parser-result:1",
                "parser_id": "parser:python",
                "audit_run_id": "audit:1",
            },
            ("parser_result", "parser-result:1"),
        ),
        (
            {
                "record_type": "detector_result",
                "result_id": "detector-result:1",
                "detector_id": "detector:1",
                "audit_run_id": "audit:1",
            },
            ("detector_result", "detector-result:1"),
        ),
        (
            {
                "record_type": "detector_qualification",
                "qualification_id": "qualification:1",
                "detector_id": "detector:1",
            },
            ("detector_qualification", "qualification:1"),
        ),
        (
            {
                "record_type": "agent_review",
                "review_id": "review:1",
                "case_id": "case:1",
            },
            ("agent_review", "review:1"),
        ),
        (
            {
                "record_type": "adjudicated_root_cause",
                "adjudicated_root_cause_id": "adjudicated-root-cause:1",
                "case_id": "case:1",
            },
            ("adjudicated_root_cause", "adjudicated-root-cause:1"),
        ),
        (
            {
                "record_type": "detector_evaluation_candidate",
                "evaluation_candidate_id": "detector-evaluation-candidate:1",
                "case_id": "case:1",
                "detector_id": "detector:1",
            },
            ("detector_evaluation_candidate", "detector-evaluation-candidate:1"),
        ),
        (
            {
                "record_type": "stage3_comparison_review",
                "comparison_review_id": "stage3-review:1",
                "case_id": "case:1",
            },
            ("stage3_comparison_review", "stage3-review:1"),
        ),
        (
            {
                "record_type": "detector_case_outcome",
                "case_outcome_id": "detector-case-outcome:1",
                "case_id": "case:1",
                "detector_id": "detector:1",
            },
            ("detector_case_outcome", "detector-case-outcome:1"),
        ),
        (
            {
                "record_type": "qualification_metric_set",
                "metric_set_id": "qualification-metric-set:1",
                "detector_id": "detector:1",
            },
            ("qualification_metric_set", "qualification-metric-set:1"),
        ),
    ],
)
def test_record_identity_never_selects_a_related_component_identifier(
    record: dict[str, str], expected: tuple[str, str]
) -> None:
    assert record_identity(record) == expected


def test_sqlite_derives_record_edges_and_source_location_indices(tmp_path) -> None:
    records = [
        {
            "record_type": "claim",
            "claim_id": "claim:1",
            "report_ref": {"record_type": "artifact", "record_id": "artifact:report"},
            "source_refs": [
                {
                    "source_kind": "file_span",
                    "locator": "report.md:3",
                    "path": "report.md",
                    "content_digest": "sha256:" + "1" * 64,
                    "start_line": 3,
                    "end_line": 3,
                }
            ],
        }
    ]
    path = tmp_path / "audit.db"
    rebuild_sqlite(path, records)
    connection = sqlite3.connect(path)
    edge = connection.execute(
        "SELECT relationship, target_type, target_id FROM record_edges"
    ).fetchone()
    location = connection.execute(
        "SELECT relationship, file_path, start_line, end_line FROM source_locations"
    ).fetchone()
    indices = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index'"
        ).fetchall()
    }
    connection.close()
    assert edge == ("/report_ref", "artifact", "artifact:report")
    assert location == ("/source_refs/0", "report.md", 3, 3)
    assert {
        "record_edges_by_source",
        "record_edges_by_target",
        "source_locations_by_record",
        "source_locations_by_file_span",
        "source_locations_by_digest",
    } <= indices


def test_storage_manifest_verifies_complete_audit(project_root, schema_root, tmp_path) -> None:
    output = tmp_path / "audit"
    bundle = run_demo(project_root / "examples" / "walking-skeleton", output, schema_root)
    assert len(bundle["storage_manifests"]) == 1
    manifest = bundle["storage_manifests"][0]
    verify_storage_manifest(AuditLayout(output), manifest)
    records = [record for value in bundle.values() if isinstance(value, list) for record in value]
    verify_sqlite_index(output / "audit.db", records)


def test_storage_manifest_detects_canonical_file_tampering(
    project_root, schema_root, tmp_path
) -> None:
    output = tmp_path / "audit"
    bundle = run_demo(project_root / "examples" / "walking-skeleton", output, schema_root)
    finding_path = output / "derived" / "finding.jsonl"
    finding_path.write_bytes(finding_path.read_bytes() + b" ")
    with pytest.raises(StorageIntegrityError, match="digest mismatch"):
        verify_storage_manifest(AuditLayout(output), bundle["storage_manifests"][0])


def test_storage_manifest_detects_unlisted_canonical_file(
    project_root, schema_root, tmp_path
) -> None:
    output = tmp_path / "audit"
    bundle = run_demo(project_root / "examples" / "walking-skeleton", output, schema_root)
    (output / "observed" / "unlisted.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(StorageIntegrityError, match="file set is incomplete"):
        verify_storage_manifest(AuditLayout(output), bundle["storage_manifests"][0])


def test_sqlite_integrity_detects_index_tampering(project_root, schema_root, tmp_path) -> None:
    output = tmp_path / "audit"
    bundle = run_demo(project_root / "examples" / "walking-skeleton", output, schema_root)
    connection = sqlite3.connect(output / "audit.db")
    connection.execute("UPDATE records SET json_text = '{}' WHERE record_type = 'finding'")
    connection.commit()
    connection.close()
    records = [record for value in bundle.values() if isinstance(value, list) for record in value]
    with pytest.raises(StorageIntegrityError, match="does not match"):
        verify_sqlite_index(output / "audit.db", records)


def test_storage_manifest_is_schema_valid_json(project_root, schema_root, tmp_path) -> None:
    output = tmp_path / "audit"
    run_demo(project_root / "examples" / "walking-skeleton", output, schema_root)
    stored = json.loads((output / "derived" / "storage-manifest.jsonl").read_text())
    assert stored["extensions"]["x-profile-status"] == "proposed_milestone_0_extension"


def test_normalized_json_replace_failure_preserves_previous_file(tmp_path, monkeypatch) -> None:
    path = tmp_path / "record.json"
    write_normalized_json(path, {"version": 1})

    def fail_replace(source, destination) -> None:
        del source, destination
        raise OSError("injected replace failure")

    monkeypatch.setattr("sc_referee.storage.atomic.os.replace", fail_replace)
    with pytest.raises(OSError, match="injected replace failure"):
        write_normalized_json(path, {"version": 2})
    assert json.loads(path.read_text(encoding="utf-8")) == {"version": 1}
    assert list(tmp_path.glob(".record.json.*.tmp")) == []


def test_normalized_json_once_is_canonical_and_refuses_existing_paths(tmp_path) -> None:
    path = tmp_path / "record.json"
    write_normalized_json_once(path, {"version": 1, "name": "fixture"})

    assert path.read_bytes() == b'{"name":"fixture","version":1}\n'
    with pytest.raises(FileExistsError):
        write_normalized_json_once(path, {"version": 2})
    assert path.read_bytes() == b'{"name":"fixture","version":1}\n'

    target = tmp_path / "missing-target.json"
    symlink = tmp_path / "broken-or-live-link.json"
    symlink.symlink_to(target)
    with pytest.raises(FileExistsError):
        write_normalized_json_once(symlink, {"version": 3})
    assert symlink.is_symlink()
    assert not target.exists()


def test_normalized_json_once_loses_race_without_overwriting_winner(tmp_path, monkeypatch) -> None:
    path = tmp_path / "record.json"
    real_link = os.link

    def competing_link(source, destination, *, follow_symlinks=True) -> None:
        Path(destination).write_bytes(b"race-winner\n")
        real_link(source, destination, follow_symlinks=follow_symlinks)

    monkeypatch.setattr("sc_referee.storage.atomic.os.link", competing_link)
    with pytest.raises(FileExistsError):
        write_normalized_json_once(path, {"version": 1})

    assert path.read_bytes() == b"race-winner\n"
    assert list(tmp_path.glob(".record.json.*.tmp")) == []


def test_jsonl_append_is_canonical_and_integrity_checked(tmp_path) -> None:
    store = JsonlRecordStore(tmp_path / "records")
    store.append({"value": 1, "record_type": "claim", "claim_id": "claim:1"})
    path = tmp_path / "records" / "claim.jsonl"
    assert path.read_text(encoding="utf-8") == (
        '{"claim_id":"claim:1","record_type":"claim","value":1}\n'
    )
    assert store.verify_integrity() == 1


def test_adjudicated_root_cause_round_trips_through_jsonl_and_sqlite(tmp_path) -> None:
    record = {
        "record_type": "adjudicated_root_cause",
        "adjudicated_root_cause_id": "adjudicated-root-cause:1",
        "case_id": "case:1",
    }
    store = JsonlRecordStore(tmp_path / "records")
    store.append(record)
    assert list(store.iter_records("adjudicated_root_cause")) == [record]
    assert (tmp_path / "records" / "adjudicated-root-cause.jsonl").is_file()

    sqlite_path = tmp_path / "audit.db"
    assert rebuild_sqlite(sqlite_path, [record]) == 1
    connection = sqlite3.connect(sqlite_path)
    stored = connection.execute("SELECT record_type, record_id, json_text FROM records").fetchone()
    connection.close()
    assert stored == (
        "adjudicated_root_cause",
        "adjudicated-root-cause:1",
        '{"adjudicated_root_cause_id":"adjudicated-root-cause:1","case_id":"case:1","record_type":"adjudicated_root_cause"}',
    )


def test_stage3_records_round_trip_through_jsonl_and_disposable_sqlite(tmp_path) -> None:
    records = [
        {
            "record_type": "detector_evaluation_candidate",
            "evaluation_candidate_id": "detector-evaluation-candidate:1",
            "case_id": "case:1",
            "detector_id": "detector:1",
        },
        {
            "record_type": "stage3_comparison_review",
            "comparison_review_id": "stage3-review:1",
            "case_id": "case:1",
        },
        {
            "record_type": "detector_case_outcome",
            "case_outcome_id": "detector-case-outcome:1",
            "case_id": "case:1",
            "detector_id": "detector:1",
            "detector_result_outcomes": [
                {
                    "detector_result_ref": {
                        "record_type": "detector_result",
                        "record_id": "detector-result:1",
                    },
                    "detector_result_digest": "sha256:" + "11" * 32,
                    "evaluation_candidate_refs": [
                        {
                            "record_type": "detector_evaluation_candidate",
                            "record_id": "detector-evaluation-candidate:1",
                        }
                    ],
                }
            ],
        },
        {
            "record_type": "qualification_metric_set",
            "metric_set_id": "qualification-metric-set:1",
            "detector_id": "detector:1",
            "case_outcome_inputs": [
                {
                    "case_outcome_ref": {
                        "record_type": "detector_case_outcome",
                        "record_id": "detector-case-outcome:1",
                    },
                    "case_outcome_digest": "sha256:" + "22" * 32,
                }
            ],
        },
    ]
    store = JsonlRecordStore(tmp_path / "records")
    for record in records:
        store.append(record)
    assert list(store.iter_records()) == sorted(records, key=lambda value: value["record_type"])

    sqlite_path = tmp_path / "audit.db"
    assert rebuild_sqlite(sqlite_path, records) == 4
    verify_sqlite_index(sqlite_path, records)
    connection = sqlite3.connect(sqlite_path)
    edges = set(
        connection.execute(
            "SELECT source_type, relationship, target_type, target_id FROM record_edges"
        ).fetchall()
    )
    connection.close()
    assert (
        "detector_case_outcome",
        "/detector_result_outcomes/0/detector_result_ref",
        "detector_result",
        "detector-result:1",
    ) in edges
    assert (
        "qualification_metric_set",
        "/case_outcome_inputs/0/case_outcome_ref",
        "detector_case_outcome",
        "detector-case-outcome:1",
    ) in edges


def test_torn_jsonl_write_is_detected_and_blocks_future_append(tmp_path, monkeypatch) -> None:
    store = JsonlRecordStore(tmp_path / "records")
    real_write = os.write

    def crash_after_partial_write(descriptor: int, payload: bytes) -> int:
        real_write(descriptor, payload[: max(1, len(payload) // 2)])
        raise OSError("injected crash")

    monkeypatch.setattr("sc_referee.storage.jsonl.os.write", crash_after_partial_write)
    with pytest.raises(OSError, match="injected crash"):
        store.append({"record_type": "claim", "claim_id": "claim:1"})
    monkeypatch.setattr("sc_referee.storage.jsonl.os.write", real_write)
    with pytest.raises(JsonlIntegrityError, match="torn JSONL tail"):
        list(store.iter_records())
    with pytest.raises(JsonlIntegrityError, match="refusing to append"):
        store.append({"record_type": "claim", "claim_id": "claim:2"})


def test_noncanonical_or_misfiled_jsonl_is_rejected(tmp_path) -> None:
    root = tmp_path / "records"
    root.mkdir()
    (root / "claim.jsonl").write_text(
        '{"record_type": "claim", "claim_id": "claim:1"}\n', encoding="utf-8"
    )
    with pytest.raises(JsonlIntegrityError, match="noncanonical"):
        list(JsonlRecordStore(root).iter_records())

    (root / "claim.jsonl").write_text(
        '{"finding_id":"finding:1","record_type":"finding"}\n', encoding="utf-8"
    )
    with pytest.raises(JsonlIntegrityError, match="does not match"):
        list(JsonlRecordStore(root).iter_records())
