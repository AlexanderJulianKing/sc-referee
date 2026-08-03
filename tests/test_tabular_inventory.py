from __future__ import annotations

import gzip
from pathlib import Path

import pytest

from sc_referee.controller import replay, run_audit
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.snapshot.repository import AssetIdentityPolicy, capture_repository
from sc_referee.tabular_inventory import (
    MAX_DELIMITED_HEADER_BYTES,
    MAX_DELIMITED_LOGICAL_READ_BYTES,
    MAX_DELIMITED_READ_CHUNK_BYTES,
    inspect_delimited_inventory,
)


def test_exact_header_inventory_preserves_unknown_rows_types_and_role(
    schema_root: Path, tmp_path: Path
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "results.csv").write_text(
        "sample_id,effect,p_value\nsecret-row-value,1.5,0.01\n",
        encoding="utf-8",
    )
    snapshot = capture_repository(
        source,
        tmp_path / "snapshot",
        "run:test",
        captured_at="2026-07-29T20:00:00Z",
    )

    output = inspect_delimited_inventory(
        snapshot,
        [],
        [],
        "run:test",
        "2026-07-29T20:00:00Z",
    )

    assert output.inspected_paths == ("results.csv",)
    assert output.unavailable_paths == ()
    assert len(output.artifacts) == 1
    assert len(output.asset_identities) == 1
    assert len(output.data_assets) == 1
    data_asset = output.data_assets[0]
    assert data_asset["role"] == "unknown"
    assert data_asset["format"] == "csv"
    assert data_asset["structure_status"] == "partial"
    assert {record["observed_name"] for record in output.variables} == {
        "effect",
        "p_value",
        "sample_id",
    }
    assert {record["storage_type"] for record in output.variables} == {"unknown"}
    assert all("observed_level_count" not in record for record in output.variables)
    assert "secret-row-value" not in repr(output.data_assets)
    assert "secret-row-value" not in repr(output.variables)

    validator = LocalSchemaRegistry(schema_root)
    for record in [
        *output.artifacts,
        *output.asset_identities,
        *output.data_assets,
        *output.variables,
    ]:
        validator.validate(record)


def test_invalid_or_over_budget_delimited_files_fail_locally(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "duplicate.csv").write_text("value,value\n1,2\n", encoding="utf-8")
    (source / "large.tsv").write_bytes(b"name\tvalue\n" + b"x" * 500)
    snapshot = capture_repository(
        source,
        tmp_path / "snapshot",
        "run:test",
        captured_at="2026-07-29T20:00:00Z",
        identity_policy=AssetIdentityPolicy(
            full_digest_byte_budget=len((source / "duplicate.csv").read_bytes()),
            sampled_fingerprint_byte_budget=12,
            sample_chunk_bytes=4,
        ),
    )

    output = inspect_delimited_inventory(
        snapshot,
        [],
        [],
        "run:test",
        "2026-07-29T20:00:00Z",
    )

    assert output.inspected_paths == ("duplicate.csv",)
    assert output.unavailable_paths == ("large.tsv",)
    assert len(output.data_assets) == 1
    assert output.data_assets[0]["structure_status"] == "opaque"
    assert output.data_assets[0]["variable_refs"] == []
    assert output.variables == []


def test_non_utf8_wide_and_ambiguous_headers_never_invent_variables(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "binary.csv").write_bytes(b"name,\xff\nvalue,1\n")
    (source / "wide.csv").write_text(
        ",".join(f"column_{index}" for index in range(1025)) + "\n",
        encoding="utf-8",
    )
    (source / "ambiguous.csv").write_text("name,value\n", encoding="utf-8")
    snapshot = capture_repository(
        source,
        tmp_path / "snapshot",
        "run:test",
        captured_at="2026-07-29T20:00:00Z",
    )

    output = inspect_delimited_inventory(
        snapshot,
        [{"path": "ambiguous.csv"}, {"path": "ambiguous.csv"}],
        [],
        "run:test",
        "2026-07-29T20:00:00Z",
    )

    assert output.ambiguous_artifact_paths == ("ambiguous.csv",)
    assert output.inspected_paths == ("binary.csv", "wide.csv")
    by_path = {record["path"]: record for record in output.data_assets}
    assert by_path["binary.csv"]["structure_status"] == "opaque"
    assert by_path["wide.csv"]["structure_status"] == "partial"
    assert by_path["binary.csv"]["variable_refs"] == []
    assert by_path["wide.csv"]["variable_refs"] == []
    assert output.variables == []


def test_gzip_csv_and_tsv_headers_are_read_without_decompressing_the_body(tmp_path: Path) -> None:
    source = tmp_path / "compressed"
    source.mkdir()
    (source / "results.csv.gz").write_bytes(
        gzip.compress(b'"sample\nidentifier",effect\nsecret,1.5\n' + b"x" * 2_000_000, mtime=0)
    )
    (source / "metadata.tsv.gz").write_bytes(
        gzip.compress(b"sample_id\tcondition\ns1\tcontrol\n", mtime=0)
    )
    snapshot = capture_repository(
        source,
        tmp_path / "snapshot-compressed",
        "run:compressed",
        captured_at="2026-08-02T22:00:00Z",
    )

    output = inspect_delimited_inventory(
        snapshot,
        [],
        [],
        "run:compressed",
        "2026-08-02T22:00:00Z",
    )

    assert output.inspected_paths == ("metadata.tsv.gz", "results.csv.gz")
    assets = {item["path"]: item for item in output.data_assets}
    assert assets["results.csv.gz"]["format"] == "csv"
    assert assets["metadata.tsv.gz"]["format"] == "tsv"
    assert {item["observed_name"] for item in output.variables} == {
        "sample\nidentifier",
        "effect",
        "sample_id",
        "condition",
    }
    csv_ref = assets["results.csv.gz"]["source_refs"][0]
    assert csv_ref["end_line"] == 2
    assert csv_ref["quoted_text"] == '"sample\nidentifier",effect'
    receipts = {item.path: item for item in output.read_receipts}
    assert receipts["results.csv.gz"].content_encoding == "gzip"
    assert receipts["results.csv.gz"].logical_bytes_read < 100
    assert receipts["results.csv.gz"].raw_file_bytes < 10_000
    assert receipts["results.csv.gz"].chunk_byte_ceiling == MAX_DELIMITED_READ_CHUNK_BYTES
    assert any(
        "not decompressed or validated" in limitation
        for limitation in assets["results.csv.gz"]["limitations"]
    )


def test_compressed_header_bomb_and_malformed_gzip_are_localized(tmp_path: Path) -> None:
    source = tmp_path / "bad-compressed"
    source.mkdir()
    oversized_header = b"x" * (MAX_DELIMITED_HEADER_BYTES + 1) + b"\n"
    (source / "oversized.csv.gz").write_bytes(gzip.compress(oversized_header, mtime=0))
    (source / "malformed.tsv.gz").write_bytes(b"not-a-gzip-member")
    (source / "ignored.csv.zip").write_bytes(b"not supported")
    snapshot = capture_repository(
        source,
        tmp_path / "snapshot-bad-compressed",
        "run:bad-compressed",
        captured_at="2026-08-02T22:00:00Z",
    )

    output = inspect_delimited_inventory(
        snapshot,
        [],
        [],
        "run:bad-compressed",
        "2026-08-02T22:00:00Z",
    )

    assert output.inspected_paths == ("malformed.tsv.gz", "oversized.csv.gz")
    by_path = {item["path"]: item for item in output.data_assets}
    assert set(by_path) == {"malformed.tsv.gz", "oversized.csv.gz"}
    assert {item["structure_status"] for item in by_path.values()} == {"opaque"}
    assert output.variables == []
    receipts = {item.path: item for item in output.read_receipts}
    assert receipts["malformed.tsv.gz"].termination_reason == "invalid_compression"
    assert receipts["oversized.csv.gz"].termination_reason == "header_budget_exceeded"
    assert receipts["oversized.csv.gz"].logical_bytes_read <= MAX_DELIMITED_LOGICAL_READ_BYTES


def test_compressed_header_reader_propagates_cancellation_between_chunks(tmp_path: Path) -> None:
    source = tmp_path / "cancel-compressed"
    source.mkdir()
    header = b"x" * (MAX_DELIMITED_READ_CHUNK_BYTES + 10) + b",value\n"
    (source / "wide.csv.gz").write_bytes(gzip.compress(header, mtime=0))
    snapshot = capture_repository(
        source,
        tmp_path / "snapshot-cancel-compressed",
        "run:cancel-compressed",
        captured_at="2026-08-02T22:00:00Z",
    )
    calls = 0

    class _Cancelled(RuntimeError):
        pass

    def checkpoint() -> None:
        nonlocal calls
        calls += 1
        if calls == 3:
            raise _Cancelled("stop compressed read")

    with pytest.raises(_Cancelled, match="stop compressed read"):
        inspect_delimited_inventory(
            snapshot,
            [],
            [],
            "run:cancel-compressed",
            "2026-08-02T22:00:00Z",
            read_checkpoint=checkpoint,
        )
    assert calls == 3


def test_compressed_header_receipt_is_locked_and_replayed_without_project_execution(
    schema_root: Path,
    tmp_path: Path,
) -> None:
    source = tmp_path / "audit-compressed"
    source.mkdir()
    (source / "report.md").write_text("# Results\n\nNo scientific claim.\n", encoding="utf-8")
    (source / "results.csv.gz").write_bytes(gzip.compress(b"sample_id,effect\ns1,1.5\n", mtime=0))
    marker = source / "executed.txt"
    (source / "trap.py").write_text(
        "from pathlib import Path\nPath('executed.txt').write_text('bad')\n",
        encoding="utf-8",
    )
    audit_output = tmp_path / "audit-output"

    bundle = run_audit(
        source,
        audit_output,
        schema_root,
        report="report.md",
        material_inputs=("results.csv.gz",),
    )

    assert not marker.exists()
    assert bundle["findings"] == []
    receipts = bundle["repository_snapshots"][0]["extensions"]["x-delimited-read-receipts"]
    assert receipts[0]["path"] == "results.csv.gz"
    assert receipts[0]["status"] == "inspected"
    (source / "results.csv.gz").write_bytes(b"changed after semantic lock")
    replayed = replay(
        audit_output / "semantic.lock.json",
        tmp_path / "audit-replay",
        schema_root,
    )
    assert (
        replayed["repository_snapshots"][0]["extensions"]["x-delimited-read-receipts"] == receipts
    )
    assert not marker.exists()
