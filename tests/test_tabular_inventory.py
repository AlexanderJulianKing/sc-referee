from __future__ import annotations

from pathlib import Path

from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.snapshot.repository import AssetIdentityPolicy, capture_repository
from sc_referee.tabular_inventory import inspect_delimited_inventory


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
    (source / "binary.csv").write_bytes(b"name,value\n\xff,1\n")
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
