from __future__ import annotations

from pathlib import Path

from sc_referee.nextflow_trace import (
    MAX_NEXTFLOW_TRACE_BYTES,
    inspect_nextflow_trace,
)
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.snapshot.repository import AssetIdentityPolicy, capture_repository

HEADER = (
    "task_id\thash\tnative_id\tname\tstatus\texit\tsubmit\tduration\trealtime\t%cpu\t"
    "peak_rss\tpeak_vmem\trchar\twchar\n"
)


def test_default_nextflow_trace_import_is_weak_and_lineage_free(
    schema_root: Path, tmp_path: Path
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "trace.txt").write_text(
        HEADER + "19\t45/ab752a\t2032\tblast (1)\tCOMPLETED\t0\t"
        "2026-07-29 16:33:16.288\t1m\t5s\t0.0%\t29.8 MB\t354 MB\t33.3 MB\t0\n"
        + "20\t72/db873d\t2033\tblast (2)\tFAILED\t137\t"
        "2026-07-29 16:34:17.211\t30s\t10s\t35.7%\t152.8 MB\t428.1 MB\t"
        "192.7 MB\t1 MB\n",
        encoding="utf-8",
    )
    snapshot = capture_repository(
        source,
        tmp_path / "snapshot",
        "run:test",
        captured_at="2026-07-29T20:00:00Z",
    )

    output = inspect_nextflow_trace(
        snapshot,
        "run:test",
        "2026-07-29T20:00:00Z",
    )

    assert output.candidate_path == "trace.txt"
    assert output.parser_result is not None
    assert output.parser_result["coverage_status"] == "partially_covered"
    assert len(output.environments) == 1
    assert len(output.executions) == 2
    assert {record["exit"]["state"] for record in output.executions} == {
        "failed",
        "succeeded",
    }
    assert {record["identity_strength"] for record in output.executions} == {"imported_weak"}
    assert {record["actor"] for record in output.executions} == {"external_import"}
    assert {record["execution_kind"] for record in output.executions} == {"imported"}
    assert {record["authorization_evidence_status"] for record in output.executions} == {"imported"}
    assert all(record["input_refs"] == [] for record in output.executions)
    assert all(record["output_refs"] == [] for record in output.executions)
    assert all(record["timing"] == {"state": "unavailable"} for record in output.executions)
    assert all(record["project_execution"] is None for record in output.executions)
    assert output.environments[0]["environment_kind"] == "imported_runtime"
    assert output.environments[0]["identity_status"] == "partial"
    assert output.environments[0]["runtime"] == {"name": "Nextflow"}

    validator = LocalSchemaRegistry(schema_root)
    validator.validate(output.parser_result)
    for record in [*output.environments, *output.executions]:
        validator.validate(record)


def test_malformed_and_nonterminal_trace_rows_are_localized(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "trace.txt").write_text(
        HEADER + "19\t45/ab752a\t2032\tblast (1)\tCOMPLETED\t0\t"
        "2026-07-29 16:33:16.288\t1m\t5s\t0.0%\t29.8 MB\t354 MB\t33.3 MB\t0\n"
        + "20\t72/db873d\t2033\tblast (2)\tRUNNING\t-\t"
        "2026-07-29 16:34:17.211\t-\t-\t-\t-\t-\t-\t-\n" + "not\ta\tcomplete\trow\n",
        encoding="utf-8",
    )
    snapshot = capture_repository(
        source,
        tmp_path / "snapshot",
        "run:test",
        captured_at="2026-07-29T20:00:00Z",
    )

    output = inspect_nextflow_trace(
        snapshot,
        "run:test",
        "2026-07-29T20:00:00Z",
    )

    assert len(output.executions) == 1
    assert output.parser_result is not None
    assert output.parser_result["state"] == "partially_parsed"
    assert len(output.parser_result["opaque_constructs"]) == 2


def test_wrong_header_over_budget_and_mutated_trace_never_emit_execution(
    tmp_path: Path,
) -> None:
    wrong_source = tmp_path / "wrong-source"
    wrong_source.mkdir()
    (wrong_source / "trace.txt").write_text("task\tstatus\n1\tCOMPLETED\n", encoding="utf-8")
    wrong_snapshot = capture_repository(
        wrong_source,
        tmp_path / "wrong-snapshot",
        "run:wrong",
        captured_at="2026-07-29T20:00:00Z",
    )
    wrong = inspect_nextflow_trace(
        wrong_snapshot,
        "run:wrong",
        "2026-07-29T20:00:00Z",
    )
    assert wrong.executions == []
    assert wrong.environments == []
    assert wrong.parser_result is not None
    assert wrong.parser_result["state"] == "unsupported"

    large_source = tmp_path / "large-source"
    large_source.mkdir()
    (large_source / "trace.txt").write_bytes(
        HEADER.encode("utf-8") + b"x" * MAX_NEXTFLOW_TRACE_BYTES
    )
    large_snapshot = capture_repository(
        large_source,
        tmp_path / "large-snapshot",
        "run:large",
        captured_at="2026-07-29T20:00:00Z",
        identity_policy=AssetIdentityPolicy(
            full_digest_byte_budget=MAX_NEXTFLOW_TRACE_BYTES + len(HEADER),
            sampled_fingerprint_byte_budget=12,
            sample_chunk_bytes=4,
        ),
    )
    large = inspect_nextflow_trace(
        large_snapshot,
        "run:large",
        "2026-07-29T20:00:00Z",
    )
    assert large.executions == []
    assert large.parser_result is not None
    assert large.parser_result["state"] == "unsupported"

    mutation_source = tmp_path / "mutation-source"
    mutation_source.mkdir()
    (mutation_source / "trace.txt").write_text(
        HEADER + "19\t45/ab752a\t2032\tblast\tCOMPLETED\t0\t2026-07-29 16:33:16.288\t"
        "1m\t5s\t0.0%\t29.8 MB\t354 MB\t33.3 MB\t0\n",
        encoding="utf-8",
    )
    mutation_snapshot = capture_repository(
        mutation_source,
        tmp_path / "mutation-snapshot",
        "run:mutation",
        captured_at="2026-07-29T20:00:00Z",
    )
    (mutation_snapshot.materialized_root / "trace.txt").write_text(
        "mutated after capture\n", encoding="utf-8"
    )
    mutated = inspect_nextflow_trace(
        mutation_snapshot,
        "run:mutation",
        "2026-07-29T20:00:00Z",
    )
    assert mutated.executions == []
    assert mutated.environments == []
    assert mutated.parser_result is not None
    assert mutated.parser_result["state"] == "parser_unavailable"
