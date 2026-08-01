from __future__ import annotations

import csv
from dataclasses import dataclass
from typing import Any

from sc_referee.core.ids import canonical_json, sha256_digest, stable_id
from sc_referee.records.observed import controller_provenance, typed_ref
from sc_referee.snapshot.repository import SnapshotOutput
from sc_referee.version import SCHEMA_VERSION, __version__

NEXTFLOW_TRACE_PATH = "trace.txt"
NEXTFLOW_TRACE_PROFILE = "nextflow-default-trace-v1"
NEXTFLOW_TRACE_PARSER_ID = "parser:nextflow-default-trace"
MAX_NEXTFLOW_TRACE_BYTES = 2_000_000
MAX_NEXTFLOW_TRACE_ROWS = 4096
MAX_NEXTFLOW_TRACE_FIELD_CHARS = 4096
MAX_NEXTFLOW_TRACE_OPAQUE_ROWS = 128

_HEADER = (
    "task_id",
    "hash",
    "native_id",
    "name",
    "status",
    "exit",
    "submit",
    "duration",
    "realtime",
    "%cpu",
    "peak_rss",
    "peak_vmem",
    "rchar",
    "wchar",
)


@dataclass(frozen=True)
class NextflowTraceOutput:
    parser_result: dict[str, Any] | None
    environments: list[dict[str, Any]]
    executions: list[dict[str, Any]]
    candidate_path: str | None


def inspect_nextflow_trace(
    snapshot: SnapshotOutput,
    run_id: str,
    created_at: str,
) -> NextflowTraceOutput:
    """Import terminal rows from the default Nextflow trace without trusting their claims."""

    file_record = next(
        (
            record
            for record in snapshot.file_records
            if record.get("path") == NEXTFLOW_TRACE_PATH
            and record.get("entry_kind") == "regular_file"
        ),
        None,
    )
    if file_record is None:
        return NextflowTraceOutput(None, [], [], None)

    generic_ref: dict[str, Any] = {
        "source_kind": "artifact",
        "locator": NEXTFLOW_TRACE_PATH,
        "path": NEXTFLOW_TRACE_PATH,
    }
    identity = next(
        (
            record
            for record in snapshot.asset_identity_records
            if record.get("asset_ref") == typed_ref("file_record", str(file_record["file_id"]))
        ),
        None,
    )
    materialized = snapshot.materialized_root / NEXTFLOW_TRACE_PATH
    if (
        identity is None
        or identity.get("tier") != "full_digest"
        or not materialized.is_file()
        or materialized.is_symlink()
    ):
        return NextflowTraceOutput(
            _unavailable_parser_result(
                run_id,
                created_at,
                generic_ref,
                "The default Nextflow trace was not fully captured under full-digest identity.",
            ),
            [],
            [],
            NEXTFLOW_TRACE_PATH,
        )

    digest = identity.get("identity_evidence", {}).get("digest")
    if not isinstance(digest, str):
        return NextflowTraceOutput(
            _unavailable_parser_result(
                run_id,
                created_at,
                generic_ref,
                "The default Nextflow trace lacks a usable full content digest.",
            ),
            [],
            [],
            NEXTFLOW_TRACE_PATH,
        )
    generic_ref["content_digest"] = digest
    try:
        payload = materialized.read_bytes()
    except OSError:
        return NextflowTraceOutput(
            _unavailable_parser_result(
                run_id,
                created_at,
                generic_ref,
                "The captured default Nextflow trace could not be read safely.",
            ),
            [],
            [],
            NEXTFLOW_TRACE_PATH,
        )
    if sha256_digest(payload) != digest:
        return NextflowTraceOutput(
            _unavailable_parser_result(
                run_id,
                created_at,
                generic_ref,
                "The captured default Nextflow trace no longer matches its immutable identity.",
            ),
            [],
            [],
            NEXTFLOW_TRACE_PATH,
        )
    if len(payload) > MAX_NEXTFLOW_TRACE_BYTES:
        return NextflowTraceOutput(
            _unsupported_parser_result(
                run_id,
                created_at,
                generic_ref,
                f"The trace exceeds the {MAX_NEXTFLOW_TRACE_BYTES}-byte inspection ceiling.",
            ),
            [],
            [],
            NEXTFLOW_TRACE_PATH,
        )
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return NextflowTraceOutput(
            _unsupported_parser_result(
                run_id,
                created_at,
                generic_ref,
                "The trace is not strict UTF-8.",
            ),
            [],
            [],
            NEXTFLOW_TRACE_PATH,
        )

    lines = text.splitlines()
    if not lines or tuple(lines[0].split("\t")) != _HEADER:
        return NextflowTraceOutput(
            _unsupported_parser_result(
                run_id,
                created_at,
                generic_ref,
                "The trace does not have the exact default Nextflow trace header.",
            ),
            [],
            [],
            NEXTFLOW_TRACE_PATH,
        )

    header_ref = _line_ref(digest, 1, lines[0])
    environment = _imported_environment(run_id, created_at, digest, header_ref)
    executions: list[dict[str, Any]] = []
    opaque_constructs: list[dict[str, Any]] = []
    rows = lines[1:]
    inspected_rows = min(len(rows), MAX_NEXTFLOW_TRACE_ROWS)
    for line_number, line in enumerate(rows[:MAX_NEXTFLOW_TRACE_ROWS], start=2):
        source_ref = _line_ref(digest, line_number, line)
        parsed, reason = _parse_terminal_row(line)
        if parsed is None:
            _append_opaque(opaque_constructs, source_ref, reason)
            continue
        executions.append(
            _imported_execution(
                parsed,
                source_ref,
                environment,
                digest,
                line_number,
                run_id,
                created_at,
            )
        )
    if len(rows) > MAX_NEXTFLOW_TRACE_ROWS:
        source_ref = {
            "source_kind": "file_span",
            "locator": f"{NEXTFLOW_TRACE_PATH}:{MAX_NEXTFLOW_TRACE_ROWS + 2}",
            "path": NEXTFLOW_TRACE_PATH,
            "content_digest": digest,
            "start_line": MAX_NEXTFLOW_TRACE_ROWS + 2,
            "end_line": MAX_NEXTFLOW_TRACE_ROWS + 2,
        }
        _append_opaque(
            opaque_constructs,
            source_ref,
            f"Trace rows above the {MAX_NEXTFLOW_TRACE_ROWS}-row ceiling were not inspected.",
        )

    emitted_refs = [typed_ref("environment", str(environment["environment_id"]))]
    emitted_refs.extend(
        typed_ref("execution", str(record["execution_id"])) for record in executions
    )
    parser_result = _base_parser_result(
        run_id,
        created_at,
        generic_ref,
        state="partially_parsed" if opaque_constructs else "parsed",
        coverage_status="partially_covered",
        emitted_record_refs=emitted_refs,
        opaque_constructs=opaque_constructs,
        extensions={
            "x-profile": NEXTFLOW_TRACE_PROFILE,
            "x-imported-execution-count": len(executions),
            "x-rows-inspected": inspected_rows,
            "x-row-ceiling": MAX_NEXTFLOW_TRACE_ROWS,
            "x-imported-records-are-not-observed-execution": True,
        },
    )
    return NextflowTraceOutput(
        parser_result,
        [environment],
        sorted(executions, key=lambda item: str(item["execution_id"])),
        NEXTFLOW_TRACE_PATH,
    )


def _parse_terminal_row(line: str) -> tuple[dict[str, str] | None, str]:
    try:
        row = next(csv.reader([line], delimiter="\t", strict=True))
    except (csv.Error, StopIteration):
        return None, "The trace row could not be parsed as one tab-delimited record."
    if len(row) != len(_HEADER):
        return None, f"The trace row has {len(row)} fields; {len(_HEADER)} were required."
    if any(len(field) > MAX_NEXTFLOW_TRACE_FIELD_CHARS for field in row):
        return None, (
            f"A trace field exceeds the {MAX_NEXTFLOW_TRACE_FIELD_CHARS}-character ceiling."
        )
    parsed = dict(zip(_HEADER, row, strict=True))
    if not parsed["task_id"] or not parsed["hash"] or not parsed["name"]:
        return None, "The trace row lacks a task identifier, task hash, or task name."
    try:
        exit_code = int(parsed["exit"])
    except ValueError:
        return None, "The trace row does not declare an integer terminal exit code."
    if parsed["status"] == "COMPLETED" and exit_code == 0:
        return parsed, ""
    if parsed["status"] == "FAILED" and exit_code != 0:
        return parsed, ""
    return None, (
        "Only internally consistent COMPLETED/0 and FAILED/nonzero terminal rows are imported."
    )


def _imported_environment(
    run_id: str,
    created_at: str,
    digest: str,
    source_ref: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "environment",
        "environment_id": stable_id("environment-imported-nextflow", run_id, digest),
        "audit_run_id": run_id,
        "environment_kind": "imported_runtime",
        "identity_status": "partial",
        "runtime": {"name": "Nextflow"},
        "platform": {},
        "dependency_refs": [],
        "source_refs": [source_ref],
        "limitations": [
            "The exact default trace header identifies a Nextflow trace profile, but no runtime "
            "version, platform, dependencies, containers, modules, or scheduler environment were "
            "established."
        ],
        "provenance": controller_provenance("bounded_nextflow_trace_import", created_at),
    }


def _imported_execution(
    row: dict[str, str],
    source_ref: dict[str, Any],
    environment: dict[str, Any],
    digest: str,
    line_number: int,
    run_id: str,
    created_at: str,
) -> dict[str, Any]:
    exit_code = int(row["exit"])
    command_payload = {
        "profile": NEXTFLOW_TRACE_PROFILE,
        "trace_digest": digest,
        "line": line_number,
        "task_id": row["task_id"],
        "task_hash": row["hash"],
        "task_name": row["name"],
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "execution",
        "execution_id": stable_id("execution-imported-nextflow", canonical_json(command_payload)),
        "audit_run_id": run_id,
        "execution_kind": "imported",
        "actor": "external_import",
        "method": "bounded_nextflow_terminal_task_trace_import",
        "command": {
            "display": f"Nextflow task label: {row['name']}",
            "normalized_digest": sha256_digest(canonical_json(command_payload)),
        },
        "input_refs": [],
        "output_refs": [],
        "environment_ref": typed_ref("environment", str(environment["environment_id"])),
        "timing": {"state": "unavailable"},
        "exit": {
            "state": "succeeded" if row["status"] == "COMPLETED" else "failed",
            "code": exit_code,
        },
        "sandbox": {
            "project_code_executed": True,
            "authorization_status": "unknown",
            "network_policy": "unknown",
        },
        "identity_strength": "imported_weak",
        "source_refs": [source_ref],
        "limitations": [
            "This is a repository-supplied trace assertion, not controller-observed execution or "
            "independent proof that the task ran.",
            "The trace task label is not a captured command, script, or normalized argv.",
            "No task inputs, outputs, start or finish times, environment version, sandbox, network "
            "policy, or scientific meaning were established.",
            "This imported record is not a Finding premise, clean-control execution, or evidence "
            "that any output is correct.",
        ],
        "provenance": controller_provenance("bounded_nextflow_trace_import", created_at),
        "authorization_evidence_status": "imported",
        "project_execution": None,
    }


def _line_ref(digest: str, line_number: int, line: str) -> dict[str, Any]:
    return {
        "source_kind": "file_span",
        "locator": f"{NEXTFLOW_TRACE_PATH}:{line_number}",
        "path": NEXTFLOW_TRACE_PATH,
        "content_digest": digest,
        "start_line": line_number,
        "end_line": line_number,
        "quoted_text": line,
    }


def _append_opaque(
    opaque_constructs: list[dict[str, Any]],
    source_ref: dict[str, Any],
    reason: str,
) -> None:
    if len(opaque_constructs) >= MAX_NEXTFLOW_TRACE_OPAQUE_ROWS:
        return
    opaque_constructs.append(
        {
            "kind": "unsupported_nextflow_trace_row",
            "reason": reason,
            "source_ref": source_ref,
        }
    )


def _base_parser_result(
    run_id: str,
    created_at: str,
    source_ref: dict[str, Any],
    *,
    state: str,
    coverage_status: str,
    emitted_record_refs: list[dict[str, str]],
    opaque_constructs: list[dict[str, Any]],
    syntax_issues: list[dict[str, Any]] | None = None,
    extensions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    identity_seed = source_ref.get("content_digest", source_ref["locator"])
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "parser_result",
        "parser_result_id": stable_id("parser-result-nextflow-trace", identity_seed, state),
        "audit_run_id": run_id,
        "parser_id": NEXTFLOW_TRACE_PARSER_ID,
        "parser_version": "0.1.0",
        "source_ref": source_ref,
        "state": state,
        "coverage_status": coverage_status,
        "emitted_record_refs": emitted_record_refs,
        "syntax_issues": syntax_issues or [],
        "opaque_constructs": opaque_constructs,
        "parser_disagreement": None,
        "started_at": created_at,
        "completed_at": created_at,
        "extensions": extensions or {"x-profile": NEXTFLOW_TRACE_PROFILE},
        "provenance": {
            "actor": {"actor_kind": "parser", "actor_id": NEXTFLOW_TRACE_PARSER_ID},
            "method": "bounded_static_trace_import",
            "created_at": created_at,
            "tool": "sc-referee",
            "tool_version": __version__,
        },
    }


def _unavailable_parser_result(
    run_id: str,
    created_at: str,
    source_ref: dict[str, Any],
    message: str,
) -> dict[str, Any]:
    return _base_parser_result(
        run_id,
        created_at,
        source_ref,
        state="parser_unavailable",
        coverage_status="not_covered",
        emitted_record_refs=[],
        opaque_constructs=[],
        syntax_issues=[{"message": message, "recoverable": True, "source_ref": source_ref}],
    )


def _unsupported_parser_result(
    run_id: str,
    created_at: str,
    source_ref: dict[str, Any],
    message: str,
) -> dict[str, Any]:
    return _base_parser_result(
        run_id,
        created_at,
        source_ref,
        state="unsupported",
        coverage_status="not_covered",
        emitted_record_refs=[],
        opaque_constructs=[
            {
                "kind": "unsupported_nextflow_trace_profile",
                "reason": message,
                "source_ref": source_ref,
            }
        ],
    )
