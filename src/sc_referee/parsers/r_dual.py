from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import tree_sitter_r
from tree_sitter import Language, Node, Parser

from sc_referee.core.ids import canonical_json, sha256_digest, stable_id
from sc_referee.version import SCHEMA_VERSION, __version__

R_TREE_SITTER_PARSER_ID = "parser:r-tree-sitter-inventory"
R_BASE_PARSER_ID = "parser:r-base-parse-data"
R_PARSER_VERSION = "0.1.0"
TREE_SITTER_R_VERSION = "1.3.0"
TREE_SITTER_R_COMMIT = "346d3707b8c9301f1051e8f6e32666e67529f7d2"
MAX_R_SOURCE_BYTES = 2_000_000
MAX_TREE_NODES = 200_000
MAX_CALLS = 10_000
MAX_HELPER_OUTPUT_BYTES = 32_000_000
BASE_R_TIMEOUT_SECONDS = 10.0
_TIMESTAMP = "2026-07-30T00:00:00Z"
_HELPER_PATH = Path(__file__).resolve().parents[1] / "resources" / "r-helper" / "base_parse_data.R"


@dataclass(frozen=True)
class _ParseRow:
    row_id: int
    parent: int
    line1: int
    col1: int
    line2: int
    col2: int
    terminal: bool
    token: str
    text: str


def inspect_r(
    path: Path,
    run_id: str,
    *,
    source_path: str | None = None,
    r_executable: str | None = None,
    helper_path: Path | None = None,
    timeout_seconds: float = BASE_R_TIMEOUT_SECONDS,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Parse one immutable R source twice without sourcing or evaluating it."""

    logical_path = _logical_path(path, source_path)
    bare_ref: dict[str, Any] = {
        "source_kind": "file_span",
        "locator": logical_path,
        "path": logical_path,
    }
    try:
        payload = path.read_bytes()
    except OSError as error:
        reason = f"R source could not be read: {type(error).__name__}."
        return (
            _failure_result(R_TREE_SITTER_PARSER_ID, run_id, bare_ref, "error", reason),
            _failure_result(R_BASE_PARSER_ID, run_id, bare_ref, "error", reason),
        )

    return _inspect_r_payload(
        payload,
        path,
        run_id,
        logical_path,
        r_executable=r_executable,
        helper_path=helper_path,
        timeout_seconds=timeout_seconds,
    )


def inspect_r_source(
    payload: bytes,
    analysis_path: Path,
    run_id: str,
    *,
    source_path: str,
    r_executable: str | None = None,
    helper_path: Path | None = None,
    timeout_seconds: float = BASE_R_TIMEOUT_SECONDS,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Inspect controller-extracted R bytes without sourcing or evaluating them."""

    logical_path = _logical_path(analysis_path, source_path)
    return _inspect_r_payload(
        payload,
        analysis_path,
        run_id,
        logical_path,
        r_executable=r_executable,
        helper_path=helper_path,
        timeout_seconds=timeout_seconds,
    )


def _inspect_r_payload(
    payload: bytes,
    analysis_path: Path,
    run_id: str,
    logical_path: str,
    *,
    r_executable: str | None,
    helper_path: Path | None,
    timeout_seconds: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    bare_ref: dict[str, Any] = {
        "source_kind": "file_span",
        "locator": logical_path,
        "path": logical_path,
    }

    digest = sha256_digest(payload)
    source_ref = {**bare_ref, "content_digest": digest}
    if len(payload) > MAX_R_SOURCE_BYTES:
        reason = f"R source exceeds the {MAX_R_SOURCE_BYTES}-byte parser ceiling."
        return (
            _failure_result(R_TREE_SITTER_PARSER_ID, run_id, source_ref, "unsupported", reason),
            _failure_result(R_BASE_PARSER_ID, run_id, source_ref, "unsupported", reason),
        )
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        reason = "R source is not valid UTF-8."
        return (
            _failure_result(R_TREE_SITTER_PARSER_ID, run_id, source_ref, "error", reason),
            _failure_result(R_BASE_PARSER_ID, run_id, source_ref, "error", reason),
        )

    line_count = max(1, len(text.splitlines()))
    complete_ref = {
        **source_ref,
        "locator": f"{logical_path}:1-{line_count}",
        "start_line": 1,
        "end_line": line_count,
    }
    tree_result = _tree_sitter_result(payload, text, logical_path, complete_ref, run_id)
    selected_r = shutil.which("R") if r_executable is None else r_executable
    base_result = _base_r_result(
        analysis_path,
        text,
        logical_path,
        complete_ref,
        run_id,
        r_executable=selected_r,
        helper_path=helper_path or _HELPER_PATH,
        timeout_seconds=timeout_seconds,
    )
    _record_comparison(tree_result, base_result)
    return tree_result, base_result


def _tree_sitter_result(
    payload: bytes,
    text: str,
    logical_path: str,
    source_ref: dict[str, Any],
    run_id: str,
) -> dict[str, Any]:
    language = Language(tree_sitter_r.language())
    tree = Parser(language).parse(payload)
    calls: list[dict[str, Any]] = []
    syntax_issues: list[dict[str, Any]] = []
    dynamic_spans: list[dict[str, Any]] = []
    stack = [tree.root_node]
    node_count = 0
    ceiling_exceeded = False
    while stack:
        node = stack.pop()
        node_count += 1
        if node_count > MAX_TREE_NODES:
            ceiling_exceeded = True
            break
        if node.is_error or node.is_missing:
            syntax_issues.append(
                {
                    "message": (
                        "Tree-sitter-R reported a missing token."
                        if node.is_missing
                        else "Tree-sitter-R reported a syntax error node."
                    ),
                    "source_ref": _node_source_ref(node, payload, logical_path, source_ref),
                    "recoverable": True,
                }
            )
        if node.type == "call":
            if len(calls) >= MAX_CALLS:
                ceiling_exceeded = True
                break
            call = _tree_call(node, payload, text, logical_path, source_ref)
            calls.append(call)
            if call["target_kind"] == "dynamic":
                dynamic_spans.append(call["source_ref"])
        stack.extend(reversed(node.children))

    opaque: list[dict[str, Any]] = [
        {
            "kind": "r_runtime_semantics",
            "reason": (
                "Static R syntax does not establish evaluation, dispatch, package behavior, "
                "tidy evaluation, generated formulas, dataflow, or scientific meaning."
            ),
            "source_ref": source_ref,
        }
    ]
    opaque.extend(
        {
            "kind": "dynamic_r_call_target",
            "reason": "The call target is not one direct identifier or literal namespace target.",
            "source_ref": span,
        }
        for span in dynamic_spans
    )
    if ceiling_exceeded:
        opaque.append(
            {
                "kind": "r_tree_inventory_ceiling",
                "reason": "Tree-sitter-R node or call inventory exceeded its finite ceiling.",
                "source_ref": source_ref,
            }
        )
    state = "partially_parsed" if syntax_issues or ceiling_exceeded else "parsed"
    return _parser_result(
        parser_id=R_TREE_SITTER_PARSER_ID,
        run_id=run_id,
        source_ref=source_ref,
        state=state,
        syntax_issues=syntax_issues,
        opaque_constructs=opaque,
        extensions={
            "x-r-backend": "tree-sitter-r",
            "x-r-backend-version": TREE_SITTER_R_VERSION,
            "x-r-backend-commit": TREE_SITTER_R_COMMIT,
            "x-r-tree-language-abi": language.abi_version,
            "x-r-tree-node-count": node_count,
            "x-r-calls": _indexed_calls(calls),
            "x-r-inventory-complete": not ceiling_exceeded,
        },
    )


def _tree_call(
    node: Node,
    payload: bytes,
    text: str,
    logical_path: str,
    source_ref: dict[str, Any],
) -> dict[str, Any]:
    function = node.child_by_field_name("function")
    namespace: str | None = None
    namespace_operator: str | None = None
    terminal_name: str | None = None
    target_kind = "dynamic"
    if function is not None and function.type == "identifier":
        terminal_name = _node_text(function, payload)
        target_kind = "direct"
    elif function is not None and function.type == "namespace_operator":
        named = function.named_children
        operators = [item for item in function.children if item.type in {"::", ":::"}]
        if (
            len(named) == 2
            and all(item.type == "identifier" for item in named)
            and len(operators) == 1
        ):
            namespace = _node_text(named[0], payload)
            terminal_name = _node_text(named[1], payload)
            namespace_operator = operators[0].type
            target_kind = "namespaced"
    arguments = node.child_by_field_name("arguments")
    argument_names = sorted(
        {
            _node_text(name, payload)
            for argument in (() if arguments is None else arguments.named_children)
            if argument.type == "argument"
            for name in [argument.child_by_field_name("name")]
            if name is not None and name.type == "identifier"
        }
    )
    span = _node_source_ref(node, payload, logical_path, source_ref)
    snippet = _slice_text_span(
        text,
        int(span["start_line"]),
        int(span["start_column"]),
        int(span["end_line"]),
        int(span["end_column"]),
    )
    return {
        "target_kind": target_kind,
        "terminal_name": terminal_name,
        "namespace": namespace,
        "namespace_operator": namespace_operator,
        "argument_names": argument_names,
        "source_ref": span,
        "source_text_digest": sha256_digest(snippet.encode("utf-8")),
    }


def _base_r_result(
    path: Path,
    text: str,
    logical_path: str,
    source_ref: dict[str, Any],
    run_id: str,
    *,
    r_executable: str | None,
    helper_path: Path,
    timeout_seconds: float,
) -> dict[str, Any]:
    if not r_executable:
        return _failure_result(
            R_BASE_PARSER_ID,
            run_id,
            source_ref,
            "parser_unavailable",
            "A base-R executable was not available; Tree-sitter-R coverage remains independent.",
        )
    if not helper_path.is_file() or helper_path.is_symlink():
        return _failure_result(
            R_BASE_PARSER_ID,
            run_id,
            source_ref,
            "parser_unavailable",
            "The packaged non-evaluating base-R helper was unavailable.",
        )
    try:
        with tempfile.TemporaryDirectory(prefix="sc-referee-r-parse-") as temporary:
            isolated_source = Path(temporary) / "source.R"
            isolated_source.write_bytes(text.encode("utf-8"))
            environment = {
                "HOME": temporary,
                "R_USER": temporary,
                "R_ENVIRON_USER": str(Path(temporary) / "absent-Renviron"),
                "R_PROFILE_USER": str(Path(temporary) / "absent-Rprofile"),
                "TMPDIR": temporary,
                "PATH": os.environ.get("PATH", ""),
                "LC_ALL": "C",
            }
            completed = subprocess.run(
                [
                    r_executable,
                    "--vanilla",
                    "--slave",
                    "-f",
                    str(helper_path),
                    "--args",
                    str(isolated_source),
                ],
                cwd=temporary,
                env=environment,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                check=False,
                timeout=timeout_seconds,
            )
    except subprocess.TimeoutExpired:
        return _failure_result(
            R_BASE_PARSER_ID,
            run_id,
            source_ref,
            "parser_unavailable",
            "The non-evaluating base-R parse helper timed out.",
        )
    except OSError as error:
        return _failure_result(
            R_BASE_PARSER_ID,
            run_id,
            source_ref,
            "parser_unavailable",
            f"The non-evaluating base-R parse helper could not start: {type(error).__name__}.",
        )
    if completed.returncode != 0:
        return _failure_result(
            R_BASE_PARSER_ID,
            run_id,
            source_ref,
            "error",
            "The non-evaluating base-R parse helper exited unsuccessfully.",
        )
    if len(completed.stdout) > MAX_HELPER_OUTPUT_BYTES:
        return _failure_result(
            R_BASE_PARSER_ID,
            run_id,
            source_ref,
            "unsupported",
            "The non-evaluating base-R parse-data output exceeded its finite byte ceiling.",
        )
    try:
        outcome = _parse_helper_output(completed.stdout)
    except ValueError as error:
        return _failure_result(
            R_BASE_PARSER_ID,
            run_id,
            source_ref,
            "error",
            f"The non-evaluating base-R helper returned invalid output: {error}.",
        )
    if outcome["status"] == "parse_error":
        return _parser_result(
            parser_id=R_BASE_PARSER_ID,
            run_id=run_id,
            source_ref=source_ref,
            state="error",
            syntax_issues=[
                {
                    "message": f"Base R rejected the source syntax: {outcome['message']}",
                    "source_ref": source_ref,
                    "recoverable": True,
                }
            ],
            opaque_constructs=[],
            extensions={
                "x-r-backend": "base-r-parse-data",
                "x-r-runtime-version": outcome["r_version"],
                "x-r-calls": [],
                "x-r-parse-data-row-count": 0,
                "x-r-helper-profile": "parse-keep-source-get-parse-data-v1",
                "x-r-helper-executes-project-code": False,
            },
        )
    if outcome["status"] == "over_budget":
        result = _failure_result(
            R_BASE_PARSER_ID,
            run_id,
            source_ref,
            "unsupported",
            "Base-R parse data exceeded the 100000-row finite ceiling.",
        )
        result["extensions"].update(
            {
                "x-r-runtime-version": outcome["r_version"],
                "x-r-parse-data-row-count": outcome["row_count"],
            }
        )
        return result
    rows = outcome["rows"]
    assert isinstance(rows, list)
    calls = _base_calls(rows, text, logical_path, source_ref)
    return _parser_result(
        parser_id=R_BASE_PARSER_ID,
        run_id=run_id,
        source_ref=source_ref,
        state="parsed",
        syntax_issues=[],
        opaque_constructs=[
            {
                "kind": "r_runtime_semantics",
                "reason": (
                    "Base-R parse data does not source or evaluate code and does not establish "
                    "dispatch, package behavior, dataflow, execution, or scientific meaning."
                ),
                "source_ref": source_ref,
            }
        ],
        extensions={
            "x-r-backend": "base-r-parse-data",
            "x-r-runtime-version": outcome["r_version"],
            "x-r-calls": _indexed_calls(calls),
            "x-r-parse-data-row-count": outcome["row_count"],
            "x-r-parse-data-digest": sha256_digest(
                canonical_json([_row_projection(item) for item in rows])
            ),
            "x-r-helper-profile": "parse-keep-source-get-parse-data-v1",
            "x-r-helper-executes-project-code": False,
        },
    )


def _parse_helper_output(payload: bytes) -> dict[str, Any]:
    try:
        lines = payload.decode("ascii").splitlines()
    except UnicodeDecodeError as error:
        raise ValueError("output was not ASCII-safe") from error
    if not lines:
        raise ValueError("output was empty")
    header = lines[0].split("\t")
    if header[0] == "PARSE_ERROR" and len(header) == 4:
        return {
            "status": "parse_error",
            "error_class": _decode_hex(header[1]),
            "message": _decode_hex(header[2]),
            "r_version": _decode_hex(header[3]),
        }
    if header[0] == "OVER_BUDGET" and len(header) == 3:
        return {
            "status": "over_budget",
            "row_count": _nonnegative_int(header[1]),
            "r_version": _decode_hex(header[2]),
        }
    if header[0] != "OK" or len(header) != 3:
        raise ValueError("header did not match the closed helper protocol")
    expected_count = _nonnegative_int(header[2])
    rows: list[_ParseRow] = []
    for line in lines[1:]:
        fields = line.split("\t")
        if len(fields) != 10 or fields[0] != "ROW":
            raise ValueError("row did not match the closed helper protocol")
        row = _ParseRow(
            row_id=_nonnegative_int(fields[1]),
            parent=_nonnegative_int(fields[2]),
            line1=_positive_int(fields[3]),
            col1=_positive_int(fields[4]),
            line2=_positive_int(fields[5]),
            col2=_positive_int(fields[6]),
            terminal=fields[7] == "1",
            token=_decode_hex(fields[8]),
            text=_decode_hex(fields[9]),
        )
        if fields[7] not in {"0", "1"} or row.line2 < row.line1:
            raise ValueError("row coordinates or terminal flag were invalid")
        rows.append(row)
    if len(rows) != expected_count or len({item.row_id for item in rows}) != len(rows):
        raise ValueError("row count or identity was inconsistent")
    return {
        "status": "ok",
        "r_version": _decode_hex(header[1]),
        "row_count": expected_count,
        "rows": rows,
    }


def _base_calls(
    rows: list[_ParseRow],
    text: str,
    logical_path: str,
    source_ref: dict[str, Any],
) -> list[dict[str, Any]]:
    by_id = {item.row_id: item for item in rows}
    children: dict[int, list[_ParseRow]] = {}
    for row in rows:
        children.setdefault(row.parent, []).append(row)
    calls: list[dict[str, Any]] = []
    for target in rows:
        if target.token != "SYMBOL_FUNCTION_CALL":
            continue
        namespace: str | None = None
        namespace_operator: str | None = None
        target_kind = "direct"
        siblings = children.get(target.parent, [])
        packages = [item for item in siblings if item.token == "SYMBOL_PACKAGE"]
        operators = [item for item in siblings if item.token in {"NS_GET", "NS_GET_INT"}]
        if len(packages) == 1 and len(operators) == 1:
            namespace = packages[0].text
            namespace_operator = "::" if operators[0].token == "NS_GET" else ":::"
            target_kind = "namespaced"
        call_row = _base_call_ancestor(target, by_id, children)
        argument_names = sorted(
            {
                item.text
                for item in children.get(call_row.row_id, [])
                if item.token == "SYMBOL_SUB" and item.text
            }
        )
        span = _row_source_ref(call_row, logical_path, source_ref)
        snippet = _slice_text_span(
            text,
            call_row.line1,
            call_row.col1,
            call_row.line2,
            call_row.col2 + 1,
        )
        calls.append(
            {
                "target_kind": target_kind,
                "terminal_name": target.text,
                "namespace": namespace,
                "namespace_operator": namespace_operator,
                "argument_names": argument_names,
                "source_ref": span,
                "source_text_digest": sha256_digest(snippet.encode("utf-8")),
            }
        )
    return calls


def _base_call_ancestor(
    target: _ParseRow,
    by_id: dict[int, _ParseRow],
    children: dict[int, list[_ParseRow]],
) -> _ParseRow:
    current = target
    seen: set[int] = set()
    while current.parent and current.parent not in seen:
        seen.add(current.parent)
        parent = by_id.get(current.parent)
        if parent is None:
            break
        child_tokens = {item.token for item in children.get(parent.row_id, [])}
        if "'('" in child_tokens and "')'" in child_tokens:
            return parent
        current = parent
    return target


def _record_comparison(tree_result: dict[str, Any], base_result: dict[str, Any]) -> None:
    tree_id = str(tree_result["parser_result_id"])
    base_id = str(base_result["parser_result_id"])
    comparable = tree_result["state"] in {"parsed", "partially_parsed"} and base_result[
        "state"
    ] in {"parsed", "partially_parsed"}
    tree_projection = _call_comparison_projection(tree_result)
    base_projection = _call_comparison_projection(base_result)
    if not comparable:
        status = "unavailable"
        disagreement = None
    elif tree_projection == base_projection:
        status = "exact_call_inventory_agreement"
        disagreement = None
    else:
        status = "call_inventory_disagreement"
        disagreement = (
            "Tree-sitter-R and base-R parse data disagree on the bounded direct/namespaced "
            "call-span inventory."
        )
        if tree_result["state"] == "parsed":
            tree_result["state"] = "partially_parsed"
        if base_result["state"] == "parsed":
            base_result["state"] = "partially_parsed"
    comparison_digest = sha256_digest(
        canonical_json({"tree_sitter": tree_projection, "base_r": base_projection})
    )
    tree_result["parser_disagreement"] = disagreement
    base_result["parser_disagreement"] = disagreement
    tree_result["extensions"]["x-r-cross-parser-comparison"] = {
        "status": status,
        "counterpart_parser_result_id": base_id,
        "comparison_digest": comparison_digest,
    }
    base_result["extensions"]["x-r-cross-parser-comparison"] = {
        "status": status,
        "counterpart_parser_result_id": tree_id,
        "comparison_digest": comparison_digest,
    }


def _call_comparison_projection(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "target_kind": item["target_kind"],
            "terminal_name": item["terminal_name"],
            "namespace": item["namespace"],
            "namespace_operator": item["namespace_operator"],
            "start_line": item["source_ref"]["start_line"],
            "start_column": item["source_ref"]["start_column"],
            "end_line": item["source_ref"]["end_line"],
            "end_column": item["source_ref"]["end_column"],
        }
        for item in result.get("extensions", {}).get("x-r-calls", [])
        if item.get("target_kind") in {"direct", "namespaced"}
    ]


def _parser_result(
    *,
    parser_id: str,
    run_id: str,
    source_ref: dict[str, Any],
    state: str,
    syntax_issues: list[dict[str, Any]],
    opaque_constructs: list[dict[str, Any]],
    extensions: dict[str, Any],
) -> dict[str, Any]:
    return {
        "record_type": "parser_result",
        "schema_version": SCHEMA_VERSION,
        "parser_result_id": stable_id(
            "parser-result",
            parser_id,
            str(source_ref.get("path")),
            str(source_ref.get("content_digest")),
        ),
        "audit_run_id": run_id,
        "parser_id": parser_id,
        "parser_version": R_PARSER_VERSION,
        "source_ref": source_ref,
        "state": state,
        "coverage_status": "not_covered"
        if state in {"error", "parser_unavailable", "unsupported"}
        else "partially_covered",
        "emitted_record_refs": [],
        "syntax_issues": syntax_issues,
        "opaque_constructs": opaque_constructs,
        "parser_disagreement": None,
        "started_at": _TIMESTAMP,
        "completed_at": _TIMESTAMP,
        "extensions": extensions,
        "provenance": {
            "actor": {"actor_kind": "parser", "actor_id": parser_id},
            "method": "static_non_evaluating_r_inventory",
            "created_at": _TIMESTAMP,
            "tool": "sc-referee",
            "tool_version": __version__,
        },
    }


def _failure_result(
    parser_id: str,
    run_id: str,
    source_ref: dict[str, Any],
    state: str,
    reason: str,
) -> dict[str, Any]:
    syntax_issues = (
        []
        if state in {"unsupported", "parser_unavailable"}
        else [{"message": reason, "source_ref": source_ref, "recoverable": True}]
    )
    return _parser_result(
        parser_id=parser_id,
        run_id=run_id,
        source_ref=source_ref,
        state=state,
        syntax_issues=syntax_issues,
        opaque_constructs=[
            {"kind": "r_parser_boundary", "reason": reason, "source_ref": source_ref}
        ],
        extensions={
            "x-r-backend": (
                "tree-sitter-r" if parser_id == R_TREE_SITTER_PARSER_ID else "base-r-parse-data"
            ),
            "x-r-calls": [],
            "x-r-inventory-complete": False,
        },
    )


def _indexed_calls(calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(
        calls,
        key=lambda item: (
            item["source_ref"]["start_line"],
            item["source_ref"]["start_column"],
            item["source_ref"]["end_line"],
            item["source_ref"]["end_column"],
            str(item["terminal_name"]),
        ),
    )
    return [{"call_index": index, **item} for index, item in enumerate(ordered)]


def _node_source_ref(
    node: Node,
    payload: bytes,
    logical_path: str,
    source_ref: dict[str, Any],
) -> dict[str, Any]:
    start_line = node.start_point.row + 1
    end_line = node.end_point.row + 1
    return {
        **source_ref,
        "locator": f"{logical_path}:{start_line}-{end_line}",
        "start_line": start_line,
        "end_line": end_line,
        "start_column": _character_column(payload, node.start_byte) + 1,
        "end_column": _character_column(payload, node.end_byte) + 1,
    }


def _row_source_ref(
    row: _ParseRow,
    logical_path: str,
    source_ref: dict[str, Any],
) -> dict[str, Any]:
    return {
        **source_ref,
        "locator": f"{logical_path}:{row.line1}-{row.line2}",
        "start_line": row.line1,
        "end_line": row.line2,
        "start_column": row.col1,
        "end_column": row.col2 + 1,
    }


def _character_column(payload: bytes, byte_offset: int) -> int:
    line_start = payload.rfind(b"\n", 0, byte_offset) + 1
    return len(payload[line_start:byte_offset].decode("utf-8"))


def _slice_text_span(
    text: str,
    start_line: int,
    start_column: int,
    end_line: int,
    end_column: int,
) -> str:
    lines = text.splitlines(keepends=True) or [""]
    if start_line == end_line:
        return lines[start_line - 1][start_column - 1 : max(start_column - 1, end_column - 1)]
    selected = [lines[start_line - 1][start_column - 1 :]]
    selected.extend(lines[start_line : end_line - 1])
    selected.append(lines[end_line - 1][: max(0, end_column - 1)])
    return "".join(selected)


def _node_text(node: Node, payload: bytes) -> str:
    return payload[node.start_byte : node.end_byte].decode("utf-8")


def _row_projection(row: _ParseRow) -> dict[str, Any]:
    return {
        "id": row.row_id,
        "parent": row.parent,
        "line1": row.line1,
        "col1": row.col1,
        "line2": row.line2,
        "col2": row.col2,
        "terminal": row.terminal,
        "token": row.token,
        "text": row.text,
    }


def _decode_hex(value: str) -> str:
    try:
        return bytes.fromhex(value).decode("utf-8")
    except (ValueError, UnicodeDecodeError) as error:
        raise ValueError("hex field was invalid UTF-8") from error


def _positive_int(value: str) -> int:
    parsed = _nonnegative_int(value)
    if parsed == 0:
        raise ValueError("integer field must be positive")
    return parsed


def _nonnegative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise ValueError("integer field was invalid") from error
    if parsed < 0 or str(parsed) != value:
        raise ValueError("integer field was not canonical and nonnegative")
    return parsed


def _logical_path(path: Path, source_path: str | None) -> str:
    value = source_path or path.name
    candidate = PurePosixPath(value)
    if not value or candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError("source_path must be a safe repository-relative POSIX path")
    return candidate.as_posix()
