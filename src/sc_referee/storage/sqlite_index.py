from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path
from typing import Any

from sc_referee.core.ids import canonical_json, sha256_digest

_ID_FIELDS = {
    "adjudication": "adjudication_id",
    "agent_review": "review_id",
    "adjudicated_root_cause": "adjudicated_root_cause_id",
    "audit_run": "audit_run_id",
    "benchmark_adjudication": "adjudication_id",
    "benchmark_fixture": "fixture_id",
    "capability_matrix": "matrix_id",
    "claim": "claim_id",
    "scientific_contract": "contract_id",
    "detector_manifest": "detector_id",
    "detector_evaluation_candidate": "evaluation_candidate_id",
    "detector_case_outcome": "case_outcome_id",
    "detector_qualification": "qualification_id",
    "detector_result": "result_id",
    "finding": "finding_id",
    "material_question": "question_id",
    "conditional_concern": "concern_id",
    "disclosure": "disclosure_id",
    "repository_snapshot": "snapshot_id",
    "parser_manifest": "parser_id",
    "parser_result": "parser_result_id",
    "qualification_metric_set": "metric_set_id",
    "ro_crate_export": "export_id",
    "stage3_comparison_review": "comparison_review_id",
    "static_qualification_profile": "profile_id",
    "static_qualification_proof": "proof_id",
}


def record_identity(record: Mapping[str, Any]) -> tuple[str, str]:
    record_type = str(record["record_type"])
    field = _ID_FIELDS.get(record_type)
    if field and field in record:
        return record_type, str(record[field])
    preferred = f"{record_type}_id"
    if preferred in record:
        return record_type, str(record[preferred])
    candidates = [key for key in record if key.endswith("_id") and key != "audit_run_id"]
    if len(candidates) != 1:
        raise ValueError(f"Cannot determine one identity for {record_type}")
    return record_type, str(record[candidates[0]])


def rebuild_sqlite(path: Path, records: Iterable[Mapping[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    connection = sqlite3.connect(path)
    try:
        connection.executescript(
            """
            PRAGMA journal_mode = WAL;
            CREATE TABLE records (
                record_type TEXT NOT NULL,
                record_id TEXT NOT NULL,
                json_text TEXT NOT NULL,
                digest TEXT NOT NULL,
                PRIMARY KEY (record_type, record_id, digest)
            );
            CREATE INDEX records_by_type ON records(record_type);
            CREATE TABLE record_edges (
                source_type TEXT NOT NULL,
                source_id TEXT NOT NULL,
                relationship TEXT NOT NULL,
                target_type TEXT NOT NULL,
                target_id TEXT NOT NULL,
                PRIMARY KEY (source_type, source_id, relationship, target_type, target_id)
            );
            CREATE INDEX record_edges_by_source
                ON record_edges(source_type, source_id, relationship);
            CREATE INDEX record_edges_by_target
                ON record_edges(target_type, target_id, relationship);
            CREATE TABLE source_locations (
                record_type TEXT NOT NULL,
                record_id TEXT NOT NULL,
                relationship TEXT NOT NULL,
                source_kind TEXT NOT NULL,
                locator TEXT NOT NULL,
                file_path TEXT,
                content_digest TEXT,
                start_line INTEGER,
                end_line INTEGER,
                PRIMARY KEY (record_type, record_id, relationship, locator)
            );
            CREATE INDEX source_locations_by_record
                ON source_locations(record_type, record_id);
            CREATE INDEX source_locations_by_file_span
                ON source_locations(file_path, start_line, end_line);
            CREATE INDEX source_locations_by_digest
                ON source_locations(content_digest);
            """
        )
        count = 0
        for record in records:
            record_type, record_id = record_identity(record)
            text = canonical_json(dict(record))
            connection.execute(
                "INSERT INTO records(record_type, record_id, json_text, digest) VALUES (?, ?, ?, ?)",
                (record_type, record_id, text, sha256_digest(text)),
            )
            for relationship, target_type, target_id in _record_refs(record):
                connection.execute(
                    """
                    INSERT OR IGNORE INTO record_edges(
                        source_type, source_id, relationship, target_type, target_id
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (record_type, record_id, relationship, target_type, target_id),
                )
            for relationship, source_ref in _source_refs(record):
                connection.execute(
                    """
                    INSERT OR IGNORE INTO source_locations(
                        record_type, record_id, relationship, source_kind, locator,
                        file_path, content_digest, start_line, end_line
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record_type,
                        record_id,
                        relationship,
                        source_ref["source_kind"],
                        source_ref["locator"],
                        source_ref.get("path"),
                        source_ref.get("content_digest"),
                        source_ref.get("start_line"),
                        source_ref.get("end_line"),
                    ),
                )
            count += 1
        connection.commit()
        return count
    finally:
        connection.close()


def _record_refs(value: Any, pointer: str = "") -> Iterator[tuple[str, str, str]]:
    if isinstance(value, Mapping):
        record_type = value.get("record_type")
        record_id = value.get("record_id")
        if isinstance(record_type, str) and isinstance(record_id, str):
            yield pointer or "/", record_type, record_id
            return
        for key in sorted(value):
            yield from _record_refs(value[key], f"{pointer}/{_pointer_token(str(key))}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _record_refs(item, f"{pointer}/{index}")


def _source_refs(value: Any, pointer: str = "") -> Iterator[tuple[str, Mapping[str, Any]]]:
    if isinstance(value, Mapping):
        if isinstance(value.get("source_kind"), str) and isinstance(value.get("locator"), str):
            yield pointer or "/", value
            return
        for key in sorted(value):
            yield from _source_refs(value[key], f"{pointer}/{_pointer_token(str(key))}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _source_refs(item, f"{pointer}/{index}")


def _pointer_token(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")
