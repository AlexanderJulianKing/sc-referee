from __future__ import annotations

import ast
import io
import tokenize
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from sc_referee.core.ids import sha256_digest, stable_id
from sc_referee.version import SCHEMA_VERSION, __version__

_TIMESTAMP = "2026-07-27T20:00:00Z"
_MAX_STATIC_RESULT_ALIAS_DEPTH = 8
_RENDER_WRAPPER_NAMES = frozenset({"repr", "str"})
PARSER_ID = "parser:python-ast-tokenize"
PARSER_VERSION = "0.15.1"


@dataclass(frozen=True)
class _StaticFormatter:
    definition_index: int
    function: ast.FunctionDef
    return_expression: ast.expr
    render_wrapper_names: frozenset[str]


@dataclass(frozen=True)
class _StaticFormatterAlias:
    assignment_index: int
    result_ref: str
    alias_depth: int
    assignment_count: int
    predecessor: str | None


def inspect_python(path: Path, run_id: str, *, source_path: str | None = None) -> dict[str, Any]:
    logical_path = _logical_path(path, source_path)
    try:
        payload = path.read_bytes()
    except OSError as error:
        return _read_error_result(path, run_id, logical_path, error)
    return _inspect_python_payload(payload, path, run_id, logical_path)


def inspect_python_source(
    payload: bytes,
    analysis_path: Path,
    run_id: str,
    *,
    source_path: str,
) -> dict[str, Any]:
    """Inspect controller-extracted Python bytes without writing or executing them."""

    logical_path = _logical_path(analysis_path, source_path)
    return _inspect_python_payload(payload, analysis_path, run_id, logical_path)


def _inspect_python_payload(
    payload: bytes,
    analysis_path: Path,
    run_id: str,
    logical_path: str,
) -> dict[str, Any]:
    digest = sha256_digest(payload)
    line_count = max(1, len(payload.decode("utf-8", errors="replace").splitlines()))
    source_ref = {
        "source_kind": "file_span",
        "locator": f"{logical_path}:1-{line_count}",
        "path": logical_path,
        "content_digest": digest,
        "start_line": 1,
        "end_line": line_count,
    }
    try:
        source_text = payload.decode("utf-8")
        tree = ast.parse(source_text, filename=str(analysis_path), type_comments=True)
        assert isinstance(tree, ast.Module)
        call_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        calls = [_call_record(node) for node in call_nodes]
        opaque_constructs = _opaque_constructs(tree, source_ref)
        operations, artifacts = _extract_graph_records(
            tree, source_text, analysis_path, logical_path, digest, run_id
        )
        state = "parsed"
        coverage_status = "partially_covered" if opaque_constructs else "covered"
        syntax_issues: list[dict[str, Any]] = []
    except (SyntaxError, UnicodeDecodeError) as exc:
        calls = []
        operations = []
        artifacts = []
        opaque_constructs = []
        state = "partially_parsed"
        coverage_status = "partially_covered"
        syntax_issues = [
            {
                "message": _bounded_syntax_message(exc),
                "source_ref": _syntax_issue_ref(source_ref, exc),
                "recoverable": True,
            }
        ]
    token_count = 0
    try:
        token_count = sum(1 for _ in tokenize.tokenize(io.BytesIO(payload).readline))
    except (tokenize.TokenError, SyntaxError) as error:
        coverage_status = "partially_covered"
        if not syntax_issues:
            syntax_issues.append(
                {
                    "message": f"Tokenization incomplete: {type(error).__name__}",
                    "source_ref": source_ref,
                    "recoverable": True,
                }
            )
    return {
        "record_type": "parser_result",
        "schema_version": SCHEMA_VERSION,
        "parser_result_id": stable_id("parser-result", logical_path, digest),
        "audit_run_id": run_id,
        "parser_id": PARSER_ID,
        "parser_version": PARSER_VERSION,
        "source_ref": source_ref,
        "state": state,
        "coverage_status": coverage_status,
        "emitted_record_refs": [
            {"record_type": record["record_type"], "record_id": _record_id(record)}
            for record in [*operations, *artifacts]
        ],
        "syntax_issues": syntax_issues,
        "opaque_constructs": opaque_constructs,
        "parser_disagreement": None,
        "started_at": _TIMESTAMP,
        "completed_at": _TIMESTAMP,
        "extensions": {
            "x-calls": calls,
            "x-token-count": token_count,
            "x-operations": operations,
            "x-artifacts": artifacts,
        },
        "provenance": {
            "actor": {"actor_kind": "parser", "actor_id": PARSER_ID},
            "method": "static_parse",
            "created_at": _TIMESTAMP,
            "tool": "sc-referee",
            "tool_version": __version__,
        },
    }


def _call_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Call):
        called = _call_name(node.func)
        return f"{called}()" if called else "<dynamic>"
    if isinstance(node, ast.Attribute):
        base = _call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return "<dynamic>"


def _call_record(node: ast.Call) -> dict[str, Any]:
    return {
        "name": _call_name(node.func),
        "start_line": node.lineno,
        "end_line": getattr(node, "end_lineno", node.lineno),
        "start_column": node.col_offset + 1,
        "end_column": getattr(node, "end_col_offset", node.col_offset + 1) + 1,
    }


def _opaque_constructs(tree: ast.AST, source_ref: dict[str, Any]) -> list[dict[str, Any]]:
    opaque: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        kind = None
        reason = None
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Call):
            kind = "dynamic_call_target"
            reason = (
                "The callable target is computed dynamically, so static operation identity is "
                "unresolved."
            )
        elif isinstance(node, ast.Call) and _call_name(node.func) in {"eval", "exec", "compile"}:
            kind = "runtime_code_generation"
            reason = (
                "Runtime-generated Python is not interpreted or executed during static inspection."
            )
        elif isinstance(node, ast.ImportFrom) and any(alias.name == "*" for alias in node.names):
            kind = "wildcard_import"
            reason = (
                "Wildcard import bindings cannot be resolved without importing project-authored "
                "code."
            )
        if kind is not None and reason is not None:
            opaque.append(
                {
                    "kind": kind,
                    "reason": reason,
                    "source_ref": _node_source_ref(source_ref, node),
                }
            )
    return sorted(
        opaque,
        key=lambda item: (
            item["source_ref"].get("start_line", 0),
            item["source_ref"].get("start_column", 0),
            item["kind"],
        ),
    )


def _node_source_ref(source_ref: dict[str, Any], node: ast.AST) -> dict[str, Any]:
    result = dict(source_ref)
    start_line = getattr(node, "lineno", 1)
    end_line = getattr(node, "end_lineno", start_line)
    result.update(
        {
            "locator": f"{source_ref['path']}:{start_line}-{end_line}",
            "start_line": start_line,
            "end_line": end_line,
            "start_column": getattr(node, "col_offset", 0) + 1,
            "end_column": getattr(node, "end_col_offset", 0) + 1,
        }
    )
    return result


def _syntax_issue_ref(
    source_ref: dict[str, Any], error: SyntaxError | UnicodeDecodeError
) -> dict[str, Any]:
    if not isinstance(error, SyntaxError) or error.lineno is None:
        return source_ref
    result = dict(source_ref)
    result.update(
        {
            "locator": f"{source_ref['path']}:{error.lineno}",
            "start_line": error.lineno,
            "end_line": error.lineno,
        }
    )
    if error.offset is not None and error.offset > 0:
        result["start_column"] = error.offset
        result["end_column"] = error.offset
    return result


def _bounded_syntax_message(error: SyntaxError | UnicodeDecodeError) -> str:
    if isinstance(error, SyntaxError):
        return f"Python syntax could not be parsed: {error.msg}"
    return "Python source is not valid UTF-8."


def _read_error_result(
    path: Path, run_id: str, logical_path: str, error: OSError
) -> dict[str, Any]:
    source_ref = {"source_kind": "file_span", "locator": logical_path, "path": logical_path}
    return {
        "record_type": "parser_result",
        "schema_version": SCHEMA_VERSION,
        "parser_result_id": stable_id("parser-result", logical_path, type(error).__name__),
        "audit_run_id": run_id,
        "parser_id": PARSER_ID,
        "parser_version": PARSER_VERSION,
        "source_ref": source_ref,
        "state": "error",
        "coverage_status": "not_covered",
        "emitted_record_refs": [],
        "syntax_issues": [
            {
                "message": f"Python source could not be read: {type(error).__name__}",
                "source_ref": source_ref,
                "recoverable": True,
            }
        ],
        "opaque_constructs": [],
        "parser_disagreement": None,
        "started_at": _TIMESTAMP,
        "completed_at": _TIMESTAMP,
        "extensions": {
            "x-calls": [],
            "x-token-count": 0,
            "x-operations": [],
            "x-artifacts": [],
        },
        "provenance": {
            "actor": {"actor_kind": "parser", "actor_id": PARSER_ID},
            "method": "static_parse",
            "created_at": _TIMESTAMP,
            "tool": "sc-referee",
            "tool_version": __version__,
        },
    }


def _extract_graph_records(
    tree: ast.Module,
    source_text: str,
    path: Path,
    logical_path: str,
    digest: str,
    run_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    function_kinds = {
        node.name: _function_operation_kind(node)
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    module_binding_counts = _module_binding_counts(tree)
    supported_functions_by_name: dict[
        str, list[tuple[int, ast.FunctionDef | ast.AsyncFunctionDef]]
    ] = {}
    for index, statement in enumerate(tree.body):
        if (
            isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
            and _function_operation_kind(statement) is not None
        ):
            supported_functions_by_name.setdefault(statement.name, []).append((index, statement))
    unique_supported_function_outputs = {
        name: (nodes[0][0], stable_id("artifact", logical_path, digest, name, "return"))
        for name, nodes in supported_functions_by_name.items()
        if len(nodes) == 1 and module_binding_counts.get(name) == 1
    }
    module_result_aliases = _module_level_supported_result_aliases(
        tree, unique_supported_function_outputs
    )
    static_formatters = _static_formatter_functions(tree, module_binding_counts)
    static_formatter_aliases = _module_level_static_formatter_aliases(
        tree,
        static_formatters,
        unique_supported_function_outputs,
        module_result_aliases,
        module_binding_counts,
    )
    module_render_wrappers = {
        name for name in _RENDER_WRAPPER_NAMES if module_binding_counts.get(name, 0) == 0
    }
    module_write_indices = {
        id(statement.value): index
        for index, statement in enumerate(tree.body)
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call)
    }
    function_local_write_flows = _function_local_supported_result_write_flows(
        tree,
        unique_supported_function_outputs,
        module_result_aliases,
        module_binding_counts,
    )
    bound_write_paths = {call_id: flow[2] for call_id, flow in function_local_write_flows.items()}
    static_write_paths = _static_write_output_paths(
        tree,
        module_binding_counts=module_binding_counts,
        bound_write_paths=bound_write_paths,
    )
    path_artifacts, artifact_ids = _path_artifacts(
        tree,
        parents,
        path,
        logical_path,
        run_id,
        static_write_paths=static_write_paths,
    )
    operations: list[dict[str, Any]] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            kind = function_kinds[node.name]
            if kind is None:
                continue
            literal_parameters = _mean_difference_literal_parameters(node)
            operation_id = stable_id(
                "operation",
                logical_path,
                digest,
                str(node.lineno),
                str(getattr(node, "end_lineno", node.lineno)),
                kind,
            )
            function_input_refs = sorted(
                {
                    artifact_ids[literal]
                    for call in ast.walk(tree)
                    if isinstance(call, ast.Call) and _call_name(call.func) == node.name
                    for literal in _literal_path_arguments(call)
                    if literal in artifact_ids
                }
            )
            output_ref = stable_id("artifact", logical_path, digest, node.name, "return")
            operations.append(
                _operation_record(
                    operation_id=operation_id,
                    run_id=run_id,
                    kind=kind,
                    implementation=f"python.function:{node.name}",
                    node=node,
                    source_text=source_text,
                    logical_path=logical_path,
                    digest=digest,
                    input_refs=function_input_refs,
                    output_refs=[output_ref],
                    inspection_status="supported",
                    literal_parameters=literal_parameters,
                )
            )
            path_artifacts.append(
                {
                    "record_type": "artifact",
                    "artifact_id": output_ref,
                    "run_id": run_id,
                    "kind": "computed_scalar",
                    "identity": f"derived-from:{operation_id}",
                    "producer_operation_ids": [operation_id],
                }
            )
        elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            literal_parameters = _comprehension_filter_literal_parameters(node)
            operation_id = stable_id(
                "operation",
                logical_path,
                digest,
                str(node.lineno),
                str(node.col_offset),
                "filter",
            )
            operations.append(
                _operation_record(
                    operation_id=operation_id,
                    run_id=run_id,
                    kind="filter",
                    implementation=_comprehension_implementation(node),
                    node=node,
                    source_text=source_text,
                    logical_path=logical_path,
                    digest=digest,
                    input_refs=[],
                    output_refs=[],
                    inspection_status="supported",
                    literal_parameters=literal_parameters,
                )
            )
        elif isinstance(node, ast.Subscript):
            predicates = _boolean_subscription_predicates(node)
            if predicates is None:
                continue
            literal_parameters = _packed_filter_literal_parameters(predicates)
            operation_id = stable_id(
                "operation",
                logical_path,
                digest,
                str(node.lineno),
                str(node.col_offset),
                "filter",
            )
            operations.append(
                _operation_record(
                    operation_id=operation_id,
                    run_id=run_id,
                    kind="filter",
                    implementation="python.boolean_subscription",
                    node=node,
                    source_text=source_text,
                    logical_path=logical_path,
                    digest=digest,
                    input_refs=[],
                    output_refs=[],
                    inspection_status="supported",
                    literal_parameters=literal_parameters,
                )
            )
        elif isinstance(node, ast.Call):
            name = _call_name(node.func)
            kind = _call_operation_kind(name, function_kinds)
            operation_id = stable_id(
                "operation",
                logical_path,
                digest,
                str(node.lineno),
                str(node.col_offset),
                kind,
                name,
            )
            literal_paths = _literal_path_arguments(node)
            call_input_refs: list[str] = []
            call_output_refs: list[str] = []
            call_literal_parameters: dict[str, Any] | None = None
            if name.endswith((".write_text", ".write_bytes")):
                literal = static_write_paths.get(id(node))
                if literal in artifact_ids:
                    call_output_refs.append(artifact_ids[literal])
                static_result_inputs, flow_basis = _supported_result_artifact_inputs(
                    node,
                    unique_supported_function_outputs,
                    module_result_aliases,
                    module_write_indices.get(id(node)),
                    render_wrapper_names=module_render_wrappers,
                    static_formatters=static_formatters,
                    static_formatter_aliases=static_formatter_aliases,
                )
                if not static_result_inputs:
                    local_flow = function_local_write_flows.get(id(node))
                    if local_flow is not None:
                        static_result_inputs, flow_basis = local_flow[:2]
                if static_result_inputs:
                    call_input_refs.extend(static_result_inputs)
                    call_literal_parameters = {"static_result_artifact_flow": flow_basis}
            elif name in function_kinds:
                call_input_refs.extend(
                    artifact_ids[literal] for literal in literal_paths if literal in artifact_ids
                )
            operations.append(
                _operation_record(
                    operation_id=operation_id,
                    run_id=run_id,
                    kind=kind,
                    implementation=f"python.call:{name}",
                    node=node,
                    source_text=source_text,
                    logical_path=logical_path,
                    digest=digest,
                    input_refs=call_input_refs,
                    output_refs=call_output_refs,
                    inspection_status="opaque" if kind == "opaque_operation" else "supported",
                    literal_parameters=call_literal_parameters,
                )
            )

    operations.sort(
        key=lambda record: (
            record["source_refs"][0]["start_line"],
            record["source_refs"][0].get("start_column", 0),
            record["operation_id"],
        )
    )
    producers_by_artifact: dict[str, set[str]] = {}
    for operation in operations:
        for artifact_id in operation.get("output_refs", []):
            producers_by_artifact.setdefault(artifact_id, set()).add(operation["operation_id"])
    for artifact in path_artifacts:
        declared = {str(value) for value in artifact.get("producer_operation_ids", [])}
        observed = producers_by_artifact.get(str(artifact["artifact_id"]), set())
        artifact["producer_operation_ids"] = sorted(declared | observed)
    path_artifacts.sort(key=lambda record: record["artifact_id"])
    return operations, path_artifacts


def _operation_record(
    *,
    operation_id: str,
    run_id: str,
    kind: str,
    implementation: str,
    node: ast.AST,
    source_text: str,
    logical_path: str,
    digest: str,
    input_refs: list[str],
    output_refs: list[str],
    inspection_status: str,
    literal_parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "record_type": "operation",
        "operation_id": operation_id,
        "run_id": run_id,
        "kind": kind,
        "implementation": implementation,
        "source_refs": [_ast_node_source_ref(logical_path, digest, source_text, node)],
        "input_refs": input_refs,
        "output_refs": output_refs,
        "inspection_status": inspection_status,
        "literal_parameters": literal_parameters or {},
    }


def _ast_node_source_ref(
    logical_path: str, digest: str, source_text: str, node: ast.AST
) -> dict[str, Any]:
    start_line = getattr(node, "lineno", 1)
    end_line = getattr(node, "end_lineno", start_line)
    result: dict[str, Any] = {
        "source_kind": "file_span",
        "locator": f"{logical_path}:{start_line}-{end_line}",
        "path": logical_path,
        "start_line": start_line,
        "end_line": end_line,
        "start_column": getattr(node, "col_offset", 0) + 1,
        "end_column": getattr(node, "end_col_offset", 0) + 1,
        "content_digest": digest,
    }
    quoted = ast.get_source_segment(source_text, node)
    if quoted:
        result["quoted_text"] = quoted
    return result


def _function_operation_kind(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    return "estimate" if _mean_difference_literal_parameters(node) is not None else None


def _is_mean_expression(node: ast.expr) -> bool:
    if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Div):
        return False
    return (
        isinstance(node.left, ast.Call)
        and _call_name(node.left.func) == "sum"
        and isinstance(node.right, ast.Call)
        and _call_name(node.right.func) == "len"
    )


def _mean_difference_literal_parameters(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> dict[str, str] | None:
    vectors: dict[str, tuple[str, str]] = {}
    for child in node.body:
        if (
            not isinstance(child, ast.Assign)
            or len(child.targets) != 1
            or not isinstance(child.targets[0], ast.Name)
        ):
            continue
        selected = _selected_vector_literals(child.value)
        if selected is not None:
            vectors[child.targets[0].id] = selected
    for child in node.body:
        if not isinstance(child, ast.Return) or not isinstance(child.value, ast.BinOp):
            continue
        if not isinstance(child.value.op, ast.Sub):
            continue
        left = _mean_variable_name(child.value.left)
        right = _mean_variable_name(child.value.right)
        if left not in vectors or right not in vectors:
            continue
        left_column, left_group = vectors[left]
        right_column, right_group = vectors[right]
        if left_column != right_column:
            continue
        return {
            "outcome_column": left_column,
            "left_group": left_group,
            "right_group": right_group,
        }
    return None


def _selected_vector_literals(node: ast.expr) -> tuple[str, str] | None:
    if not isinstance(node, ast.ListComp) or len(node.generators) != 1:
        return None
    generator = node.generators[0]
    if (
        not isinstance(generator.target, ast.Name)
        or len(generator.ifs) != 1
        or not isinstance(node.elt, ast.Call)
        or _call_name(node.elt.func) != "float"
        or len(node.elt.args) != 1
    ):
        return None
    outcome_column = _row_literal_column(node.elt.args[0], generator.target.id)
    condition = generator.ifs[0]
    if (
        outcome_column is None
        or not isinstance(condition, ast.Compare)
        or len(condition.ops) != 1
        or not isinstance(condition.ops[0], ast.Eq)
        or len(condition.comparators) != 1
    ):
        return None
    group_column = _row_literal_column(condition.left, generator.target.id)
    group_value = condition.comparators[0]
    if (
        group_column is None
        or not isinstance(group_value, ast.Constant)
        or not isinstance(group_value.value, str)
    ):
        return None
    return outcome_column, group_value.value


def _comprehension_implementation(
    node: ast.ListComp | ast.SetComp | ast.DictComp | ast.GeneratorExp,
) -> str:
    return {
        ast.ListComp: "python.list_comprehension",
        ast.SetComp: "python.set_comprehension",
        ast.DictComp: "python.dict_comprehension",
        ast.GeneratorExp: "python.generator_expression",
    }[type(node)]


def _comprehension_filter_literal_parameters(
    node: ast.ListComp | ast.SetComp | ast.DictComp | ast.GeneratorExp,
) -> dict[str, Any] | None:
    if len(node.generators) != 1:
        return None
    generator = node.generators[0]
    if not generator.ifs:
        return None
    comparisons: list[ast.Compare] = []
    for condition in generator.ifs:
        flattened = _and_comparisons(condition, allow_bitwise=False)
        if flattened is None:
            return None
        comparisons.extend(flattened)
    predicates: list[tuple[ast.Compare, str]] = []
    for condition in comparisons:
        field: str | None = None
        if isinstance(generator.target, ast.Name):
            field = _row_literal_column(condition.left, generator.target.id)
        if field is None and isinstance(condition.left, ast.Name):
            field = condition.left.id
        if field is None:
            return None
        predicates.append((condition, field))
    return _packed_filter_literal_parameters(predicates)


def _comparison_filter_literal_parameters(
    condition: ast.Compare, field: str | None
) -> dict[str, Any] | None:
    if len(condition.ops) != 1 or len(condition.comparators) != 1:
        return None
    comparator = condition.comparators[0]
    if not isinstance(comparator, ast.Constant) or not isinstance(
        comparator.value, (str, int, float, bool, type(None))
    ):
        return None
    operator = {
        ast.Eq: "equal",
        ast.NotEq: "not_equal",
        ast.Lt: "less_than",
        ast.LtE: "less_than_or_equal",
        ast.Gt: "greater_than",
        ast.GtE: "greater_than_or_equal",
        ast.In: "in",
        ast.NotIn: "not_in",
    }.get(type(condition.ops[0]))
    if field is None or operator is None:
        return None
    return {
        "filter_field": field,
        "filter_operator": operator,
        "filter_value": comparator.value,
    }


def _boolean_subscription_predicates(
    node: ast.Subscript,
) -> list[tuple[ast.Compare, str]] | None:
    comparisons = _and_comparisons(node.slice, allow_bitwise=True)
    if comparisons is None:
        return None
    predicates: list[tuple[ast.Compare, str]] = []
    for condition in comparisons:
        field = _same_base_literal_field(node, condition)
        if field is None:
            return None
        predicates.append((condition, field))
    return predicates


def _and_comparisons(node: ast.expr, *, allow_bitwise: bool) -> list[ast.Compare] | None:
    if isinstance(node, ast.Compare):
        return [node]
    children: list[ast.expr]
    if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
        children = list(node.values)
    elif allow_bitwise and isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitAnd):
        children = [node.left, node.right]
    else:
        return None
    flattened: list[ast.Compare] = []
    for child in children:
        comparisons = _and_comparisons(child, allow_bitwise=allow_bitwise)
        if comparisons is None:
            return None
        flattened.extend(comparisons)
    return flattened


def _packed_filter_literal_parameters(
    predicates: list[tuple[ast.Compare, str]],
) -> dict[str, Any] | None:
    values: list[dict[str, Any]] = []
    for condition, field in predicates:
        parameters = _comparison_filter_literal_parameters(condition, field)
        if parameters is None:
            return None
        values.append(parameters)
    if len(values) == 1:
        return values[0]
    return {
        "filter_fields": [value["filter_field"] for value in values],
        "filter_operators": [value["filter_operator"] for value in values],
        "filter_values": [value["filter_value"] for value in values],
        "filter_logical_operator": "and",
    }


def _same_base_literal_field(node: ast.Subscript, condition: ast.Compare) -> str | None:
    if not isinstance(condition.left, ast.Subscript):
        return None
    predicate_base = _static_expression_name(condition.left.value)
    selection_expression: ast.expr = node.value
    if isinstance(selection_expression, ast.Attribute) and selection_expression.attr == "loc":
        selection_expression = selection_expression.value
    selection_base = _static_expression_name(selection_expression)
    if not selection_base or predicate_base != selection_base:
        return None
    if isinstance(condition.left.slice, ast.Constant) and isinstance(
        condition.left.slice.value, str
    ):
        return condition.left.slice.value
    return None


def _static_expression_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _static_expression_name(node.value)
        return f"{parent}.{node.attr}" if parent else None
    return None


def _row_literal_column(node: ast.expr, row_name: str) -> str | None:
    if not isinstance(node, ast.Subscript) or not isinstance(node.value, ast.Name):
        return None
    if node.value.id != row_name:
        return None
    if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
        return node.slice.value
    return None


def _mean_variable_name(node: ast.expr) -> str | None:
    if not _is_mean_expression(node):
        return None
    assert isinstance(node, ast.BinOp)
    assert isinstance(node.left, ast.Call)
    assert isinstance(node.right, ast.Call)
    if len(node.left.args) != 1 or len(node.right.args) != 1:
        return None
    left = node.left.args[0]
    right = node.right.args[0]
    if not isinstance(left, ast.Name) or not isinstance(right, ast.Name) or left.id != right.id:
        return None
    return left.id


def _call_operation_kind(name: str, function_kinds: dict[str, str | None]) -> str:
    if name in function_kinds and function_kinds[name] is not None:
        return str(function_kinds[name])
    suffix = name.rsplit(".", 1)[-1]
    return {
        "open": "read",
        "DictReader": "parse",
        "write_text": "write",
        "write_bytes": "write",
        "sum": "aggregate",
        "len": "aggregate",
        "float": "transform",
        "list": "transform",
        "Path": "parse",
        "dumps": "render",
    }.get(suffix, "opaque_operation")


def _module_binding_counts(tree: ast.Module) -> dict[str, int]:
    counts: dict[str, int] = {}

    def add(name: str) -> None:
        counts[name] = counts.get(name, 0) + 1

    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            add(node.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            add(node.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                add(alias.asname or alias.name.split(".", maxsplit=1)[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name != "*":
                    add(alias.asname or alias.name)
        elif isinstance(node, ast.ExceptHandler) and isinstance(node.name, str):
            add(node.name)
    return counts


def _module_level_supported_result_aliases(
    tree: ast.Module, supported_outputs: dict[str, tuple[int, str]]
) -> dict[str, tuple[int, str, int]]:
    binding_counts = _module_binding_counts(tree)
    render_wrapper_names = {
        name for name in _RENDER_WRAPPER_NAMES if binding_counts.get(name, 0) == 0
    }
    aliases: dict[str, tuple[int, str, int]] = {}
    for index, statement in enumerate(tree.body):
        if (
            not isinstance(statement, ast.Assign)
            or len(statement.targets) != 1
            or not isinstance(statement.targets[0], ast.Name)
        ):
            continue
        name = statement.targets[0].id
        flow = _supported_result_calls_in_render_expression(
            statement.value,
            supported_outputs,
            aliases=aliases,
            statement_index=index,
            render_wrapper_names=render_wrapper_names,
        )
        if (
            flow is None
            or flow[1] >= _MAX_STATIC_RESULT_ALIAS_DEPTH
            or len(flow[0]) != 1
            or binding_counts.get(name) != 1
        ):
            continue
        aliases[name] = (index, next(iter(flow[0])), flow[1] + 1)
    return aliases


def _supported_result_artifact_inputs(
    write_call: ast.Call,
    supported_outputs: dict[str, tuple[int, str]],
    aliases: dict[str, tuple[int, str, int]],
    statement_index: int | None,
    *,
    render_wrapper_names: set[str] | frozenset[str] = _RENDER_WRAPPER_NAMES,
    literal_names: set[str] | frozenset[str] = frozenset(),
    static_formatters: dict[str, _StaticFormatter] | None = None,
    static_formatter_aliases: dict[str, _StaticFormatterAlias] | None = None,
) -> tuple[list[str], str | None]:
    if len(write_call.args) != 1 or statement_index is None:
        return [], None
    if isinstance(write_call.args[0], ast.Name):
        formatter_alias = (static_formatter_aliases or {}).get(write_call.args[0].id)
        if formatter_alias is not None and formatter_alias.assignment_index < statement_index:
            basis = (
                "single_static_formatter_assignment"
                if formatter_alias.assignment_count == 1
                else "static_formatter_assignment_chain"
            )
            return [formatter_alias.result_ref], basis
    formatter_flow = _direct_static_formatter_inputs(
        write_call.args[0],
        supported_outputs,
        aliases,
        statement_index,
        render_wrapper_names=render_wrapper_names,
        static_formatters=static_formatters or {},
    )
    if formatter_flow is not None:
        return formatter_flow
    result = _supported_result_calls_in_render_expression(
        write_call.args[0],
        supported_outputs,
        aliases=aliases,
        statement_index=statement_index,
        render_wrapper_names=render_wrapper_names,
        literal_names=literal_names,
    )
    if result is None or not result[0]:
        return [], None
    if result[1] > 1:
        basis = "single_assignment_alias_chain"
    elif result[1] == 1:
        basis = "single_assignment_alias"
    else:
        basis = "direct_supported_call"
    return sorted(result[0]), basis


def _supported_result_calls_in_render_expression(
    node: ast.expr,
    supported_outputs: dict[str, tuple[int, str]],
    *,
    aliases: dict[str, tuple[int, str, int]],
    statement_index: int | None,
    render_wrapper_names: set[str] | frozenset[str],
    literal_names: set[str] | frozenset[str] = frozenset(),
) -> tuple[set[str], int] | None:
    if isinstance(node, ast.Constant):
        return set(), 0
    if isinstance(node, ast.Name):
        alias = aliases.get(node.id)
        if alias is not None and statement_index is not None and alias[0] < statement_index:
            return {alias[1]}, alias[2]
        if node.id in literal_names:
            return set(), 0
        return None
    if isinstance(node, ast.JoinedStr):
        combined: set[str] = set()
        alias_depth = 0
        for value in node.values:
            if isinstance(value, ast.Constant):
                continue
            if not isinstance(value, ast.FormattedValue) or value.format_spec is not None:
                return None
            nested = _supported_result_calls_in_render_expression(
                value.value,
                supported_outputs,
                aliases=aliases,
                statement_index=statement_index,
                render_wrapper_names=render_wrapper_names,
                literal_names=literal_names,
            )
            if nested is None:
                return None
            combined.update(nested[0])
            alias_depth = max(alias_depth, nested[1])
        return combined, alias_depth
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _supported_result_calls_in_render_expression(
            node.left,
            supported_outputs,
            aliases=aliases,
            statement_index=statement_index,
            render_wrapper_names=render_wrapper_names,
            literal_names=literal_names,
        )
        right = _supported_result_calls_in_render_expression(
            node.right,
            supported_outputs,
            aliases=aliases,
            statement_index=statement_index,
            render_wrapper_names=render_wrapper_names,
            literal_names=literal_names,
        )
        if left is None or right is None:
            return None
        return left[0] | right[0], max(left[1], right[1])
    if isinstance(node, ast.Call):
        name = _call_name(node.func)
        supported = supported_outputs.get(name)
        if supported is not None and statement_index is not None and supported[0] < statement_index:
            return {supported[1]}, 0
        if name in render_wrapper_names and len(node.args) == 1 and not node.keywords:
            return _supported_result_calls_in_render_expression(
                node.args[0],
                supported_outputs,
                aliases=aliases,
                statement_index=statement_index,
                render_wrapper_names=render_wrapper_names,
                literal_names=literal_names,
            )
    return None


def _function_local_supported_result_write_flows(
    tree: ast.Module,
    supported_outputs: dict[str, tuple[int, str]],
    module_aliases: dict[str, tuple[int, str, int]],
    module_binding_counts: dict[str, int],
) -> dict[int, tuple[list[str], str, str]]:
    flows: dict[int, tuple[list[str], str, str]] = {}
    for module_index, statement in enumerate(tree.body):
        if not isinstance(statement, ast.FunctionDef):
            continue
        if statement.decorator_list or module_binding_counts.get(statement.name) != 1:
            continue
        local_binding_counts = _scope_binding_counts(statement.body)
        if local_binding_counts.get("Path", 0) != 0:
            continue
        render_wrapper_names = {
            name
            for name in _RENDER_WRAPPER_NAMES
            if module_binding_counts.get(name, 0) == 0 and local_binding_counts.get(name, 0) == 0
        }
        local_supported_outputs: dict[str, tuple[int, str]] = {}
        aliases: dict[str, tuple[int, str, int]] = {}
        parameter_bound = False
        keyword_bound = False
        literal_parameter_names: set[str] = set()
        literal_path_parameters: dict[str, str] = {}
        if _function_has_no_parameters(statement):
            local_supported_outputs = {
                name: (-1, output_ref)
                for name, (definition_index, output_ref) in supported_outputs.items()
                if definition_index < module_index and local_binding_counts.get(name, 0) == 0
            }
            if not local_supported_outputs:
                continue
        else:
            parameters = _required_positional_parameters(statement)
            call = _single_direct_module_renderer_call(tree, statement, module_index)
            if (
                parameters is None
                or call is None
                or "Path" in parameters
                or any(local_binding_counts.get(parameter, 0) != 0 for parameter in parameters)
            ):
                continue
            render_wrapper_names.difference_update(parameters)
            call_index, bound_arguments, keyword_bound = call
            module_render_wrapper_names = {
                name for name in _RENDER_WRAPPER_NAMES if module_binding_counts.get(name, 0) == 0
            }
            result_parameter: tuple[str, str, int] | None = None
            valid_arguments = True
            for parameter, argument in bound_arguments:
                incoming = _supported_result_calls_in_render_expression(
                    argument,
                    supported_outputs,
                    aliases=module_aliases,
                    statement_index=call_index,
                    render_wrapper_names=module_render_wrapper_names,
                )
                if incoming is None or incoming[1] >= _MAX_STATIC_RESULT_ALIAS_DEPTH:
                    valid_arguments = False
                    break
                if not incoming[0]:
                    literal_parameter_names.add(parameter)
                    literal_path = _safe_literal_output_path_argument(argument)
                    if literal_path is not None:
                        literal_path_parameters[parameter] = literal_path
                    continue
                if len(incoming[0]) != 1 or result_parameter is not None:
                    valid_arguments = False
                    break
                result_parameter = (parameter, next(iter(incoming[0])), incoming[1])
            if not valid_arguments or result_parameter is None:
                continue
            parameter, result_ref, incoming_depth = result_parameter
            aliases[parameter] = (-1, result_ref, incoming_depth + 1)
            parameter_bound = True
        candidate_flows: dict[int, tuple[list[str], str, str]] = {}
        valid = True
        parameter_bound_output_count = 0
        for local_index, local_statement in enumerate(statement.body):
            if (
                local_index == 0
                and isinstance(local_statement, ast.Expr)
                and isinstance(local_statement.value, ast.Constant)
                and isinstance(local_statement.value.value, str)
            ):
                continue
            if (
                isinstance(local_statement, ast.Assign)
                and len(local_statement.targets) == 1
                and isinstance(local_statement.targets[0], ast.Name)
            ):
                name = local_statement.targets[0].id
                flow = _supported_result_calls_in_render_expression(
                    local_statement.value,
                    local_supported_outputs,
                    aliases=aliases,
                    statement_index=local_index,
                    render_wrapper_names=render_wrapper_names,
                    literal_names=literal_parameter_names,
                )
                if (
                    flow is None
                    or flow[1] >= _MAX_STATIC_RESULT_ALIAS_DEPTH
                    or len(flow[0]) != 1
                    or local_binding_counts.get(name) != 1
                ):
                    valid = False
                    break
                aliases[name] = (local_index, next(iter(flow[0])), flow[1] + 1)
                continue
            resolved_output_path = None
            if isinstance(local_statement, ast.Expr) and isinstance(
                local_statement.value, ast.Call
            ):
                resolved_output_path = _resolved_write_output_path(
                    local_statement.value, literal_path_parameters
                )
            if (
                isinstance(local_statement, ast.Expr)
                and isinstance(local_statement.value, ast.Call)
                and resolved_output_path is not None
                and _call_name(local_statement.value.func).endswith((".write_text", ".write_bytes"))
            ):
                inputs, basis = _supported_result_artifact_inputs(
                    local_statement.value,
                    local_supported_outputs,
                    aliases,
                    local_index,
                    render_wrapper_names=render_wrapper_names,
                    literal_names=literal_parameter_names,
                )
                if not inputs or basis is None:
                    valid = False
                    break
                output_path_parameter_bound = _literal_receiver_path(local_statement.value) is None
                if output_path_parameter_bound:
                    parameter_bound_output_count += 1
                    if parameter_bound_output_count > 1:
                        valid = False
                        break
                candidate_flows[id(local_statement.value)] = (
                    inputs,
                    _function_flow_basis(
                        basis,
                        parameter_bound=parameter_bound,
                        literal_parameter_bound=bool(literal_parameter_names),
                        output_path_parameter_bound=output_path_parameter_bound,
                        keyword_bound=keyword_bound,
                    ),
                    resolved_output_path,
                )
                continue
            valid = False
            break
        if valid:
            flows.update(candidate_flows)
    return flows


def _function_flow_basis(
    basis: str,
    *,
    parameter_bound: bool,
    literal_parameter_bound: bool,
    output_path_parameter_bound: bool,
    keyword_bound: bool,
) -> str:
    if not parameter_bound:
        return f"function_local_{basis}"
    if keyword_bound:
        if basis == "single_assignment_alias":
            return "function_keyword_bound_result_flow_direct"
        return "function_keyword_bound_result_flow_alias_chain"
    if output_path_parameter_bound:
        if basis == "single_assignment_alias":
            return "function_result_literal_path_parameters_bound_direct"
        return "function_result_literal_path_parameters_bound_alias_chain"
    if literal_parameter_bound:
        if basis == "single_assignment_alias":
            return "function_result_literal_parameters_bound_direct"
        return "function_result_literal_parameters_bound_alias_chain"
    if basis == "single_assignment_alias":
        return "function_parameter_bound_direct"
    return "function_parameter_bound_alias_chain"


def _required_positional_parameters(node: ast.FunctionDef) -> list[str] | None:
    arguments = node.args
    positional = [*arguments.posonlyargs, *arguments.args]
    if (
        not positional
        or arguments.defaults
        or arguments.vararg is not None
        or arguments.kwonlyargs
        or arguments.kwarg is not None
        or any(default is not None for default in arguments.kw_defaults)
    ):
        return None
    return [parameter.arg for parameter in positional]


def _single_direct_module_renderer_call(
    tree: ast.Module,
    renderer: ast.FunctionDef,
    definition_index: int,
) -> tuple[int, list[tuple[str, ast.expr]], bool] | None:
    direct_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == renderer.name
    ]
    if len(direct_calls) != 1:
        return None
    target = direct_calls[0]
    for index, statement in enumerate(tree.body):
        if (
            index > definition_index
            and isinstance(statement, ast.Expr)
            and statement.value is target
        ):
            bound = _bind_required_renderer_arguments(renderer, target)
            if bound is not None:
                return index, bound, bool(target.keywords)
    return None


def _bind_required_renderer_arguments(
    renderer: ast.FunctionDef, call: ast.Call
) -> list[tuple[str, ast.expr]] | None:
    parameters = _required_positional_parameters(renderer)
    if parameters is None or len(call.args) > len(parameters):
        return None
    positional_only = {argument.arg for argument in renderer.args.posonlyargs}
    bound: dict[str, ast.expr] = dict(zip(parameters, call.args, strict=False))
    for keyword in call.keywords:
        name = keyword.arg
        if name is None or name not in parameters or name in positional_only or name in bound:
            return None
        bound[name] = keyword.value
    if set(bound) != set(parameters):
        return None
    return [(parameter, bound[parameter]) for parameter in parameters]


def _static_formatter_functions(
    tree: ast.Module, module_binding_counts: dict[str, int]
) -> dict[str, _StaticFormatter]:
    formatters: dict[str, _StaticFormatter] = {}
    for definition_index, statement in enumerate(tree.body):
        if (
            not isinstance(statement, ast.FunctionDef)
            or statement.decorator_list
            or statement.returns is not None
            or statement.type_comment is not None
            or module_binding_counts.get(statement.name) != 1
            or _required_positional_parameters(statement) is None
            or any(argument.annotation is not None for argument in statement.args.posonlyargs)
            or any(argument.annotation is not None for argument in statement.args.args)
        ):
            continue
        body = list(statement.body)
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            body = body[1:]
        if len(body) != 1 or not isinstance(body[0], ast.Return) or body[0].value is None:
            continue
        if _scope_binding_counts(statement.body):
            continue
        call_count = sum(
            1
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == statement.name
        )
        if call_count != 1:
            continue
        render_wrapper_names = frozenset(
            name
            for name in _RENDER_WRAPPER_NAMES
            if module_binding_counts.get(name, 0) == 0
            and name not in (_required_positional_parameters(statement) or [])
        )
        formatters[statement.name] = _StaticFormatter(
            definition_index=definition_index,
            function=statement,
            return_expression=body[0].value,
            render_wrapper_names=render_wrapper_names,
        )
    return formatters


def _direct_static_formatter_inputs(
    expression: ast.expr,
    supported_outputs: dict[str, tuple[int, str]],
    aliases: dict[str, tuple[int, str, int]],
    statement_index: int,
    *,
    render_wrapper_names: set[str] | frozenset[str],
    static_formatters: dict[str, _StaticFormatter],
) -> tuple[list[str], str] | None:
    result = _static_formatter_expression_result(
        expression,
        supported_outputs,
        aliases,
        statement_index,
        render_wrapper_names=render_wrapper_names,
        static_formatters=static_formatters,
    )
    if result is None:
        return None
    return [result[0]], "direct_static_formatter_call"


def _static_formatter_expression_result(
    expression: ast.expr,
    supported_outputs: dict[str, tuple[int, str]],
    aliases: dict[str, tuple[int, str, int]],
    statement_index: int,
    *,
    render_wrapper_names: set[str] | frozenset[str],
    static_formatters: dict[str, _StaticFormatter],
) -> tuple[str, int] | None:
    if not isinstance(expression, ast.Call) or not isinstance(expression.func, ast.Name):
        return None
    formatter = static_formatters.get(expression.func.id)
    if formatter is None or formatter.definition_index >= statement_index:
        return None
    bound_arguments = _bind_required_renderer_arguments(formatter.function, expression)
    if bound_arguments is None:
        return None
    result_parameter: tuple[str, str, int] | None = None
    literal_parameters: set[str] = set()
    for parameter, argument in bound_arguments:
        incoming = _supported_result_calls_in_render_expression(
            argument,
            supported_outputs,
            aliases=aliases,
            statement_index=statement_index,
            render_wrapper_names=render_wrapper_names,
        )
        if incoming is None or incoming[1] >= _MAX_STATIC_RESULT_ALIAS_DEPTH:
            return None
        if not incoming[0]:
            literal_parameters.add(parameter)
            continue
        if len(incoming[0]) != 1 or result_parameter is not None:
            return None
        result_parameter = (parameter, next(iter(incoming[0])), incoming[1])
    if result_parameter is None:
        return None
    parameter, result_ref, incoming_depth = result_parameter
    formatter_aliases = {parameter: (-1, result_ref, incoming_depth + 1)}
    returned = _supported_result_calls_in_render_expression(
        formatter.return_expression,
        {},
        aliases=formatter_aliases,
        statement_index=0,
        render_wrapper_names=formatter.render_wrapper_names,
        literal_names=literal_parameters,
    )
    if (
        returned is None
        or returned[0] != {result_ref}
        or returned[1] > _MAX_STATIC_RESULT_ALIAS_DEPTH
    ):
        return None
    return result_ref, returned[1]


def _module_level_static_formatter_aliases(
    tree: ast.Module,
    static_formatters: dict[str, _StaticFormatter],
    supported_outputs: dict[str, tuple[int, str]],
    result_aliases: dict[str, tuple[int, str, int]],
    module_binding_counts: dict[str, int],
) -> dict[str, _StaticFormatterAlias]:
    candidates: dict[str, _StaticFormatterAlias] = {}
    render_wrapper_names = {
        name for name in _RENDER_WRAPPER_NAMES if module_binding_counts.get(name, 0) == 0
    }
    for assignment_index, statement in enumerate(tree.body):
        if (
            not isinstance(statement, ast.Assign)
            or len(statement.targets) != 1
            or not isinstance(statement.targets[0], ast.Name)
        ):
            continue
        name = statement.targets[0].id
        if module_binding_counts.get(name) != 1:
            continue
        formatter_result = _static_formatter_expression_result(
            statement.value,
            supported_outputs,
            result_aliases,
            assignment_index,
            render_wrapper_names=render_wrapper_names,
            static_formatters=static_formatters,
        )
        predecessor: str | None = None
        assignment_count = 1
        if formatter_result is None:
            referenced_aliases = [
                node.id
                for node in ast.walk(statement.value)
                if isinstance(node, ast.Name)
                and isinstance(node.ctx, ast.Load)
                and node.id in candidates
            ]
            if len(referenced_aliases) != 1:
                continue
            predecessor = referenced_aliases[0]
            predecessor_alias = candidates[predecessor]
            flow = _supported_result_calls_in_render_expression(
                statement.value,
                {},
                aliases={
                    alias_name: (
                        alias.assignment_index,
                        alias.result_ref,
                        alias.alias_depth,
                    )
                    for alias_name, alias in candidates.items()
                },
                statement_index=assignment_index,
                render_wrapper_names=render_wrapper_names,
            )
            if flow is None or flow[0] != {predecessor_alias.result_ref}:
                continue
            formatter_result = (predecessor_alias.result_ref, flow[1])
            assignment_count = predecessor_alias.assignment_count + 1
        if formatter_result[1] >= _MAX_STATIC_RESULT_ALIAS_DEPTH:
            continue
        candidates[name] = _StaticFormatterAlias(
            assignment_index=assignment_index,
            result_ref=formatter_result[0],
            alias_depth=formatter_result[1] + 1,
            assignment_count=assignment_count,
            predecessor=predecessor,
        )

    load_counts = {
        name: sum(
            1
            for node in ast.walk(tree)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id == name
        )
        for name in candidates
    }
    successors: dict[str, list[str]] = {name: [] for name in candidates}
    for name, alias in candidates.items():
        if alias.predecessor is not None:
            successors[alias.predecessor].append(name)
    writer_consumers: dict[str, list[int]] = {name: [] for name in candidates}
    for index, statement in enumerate(tree.body):
        if (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Call)
            and _call_name(statement.value.func).endswith((".write_text", ".write_bytes"))
            and _literal_receiver_path(statement.value) is not None
            and len(statement.value.args) == 1
            and isinstance(statement.value.args[0], ast.Name)
            and statement.value.args[0].id in candidates
        ):
            writer_consumers[statement.value.args[0].id].append(index)

    valid: dict[str, _StaticFormatterAlias] = {}
    terminals = [
        name
        for name, consumers in writer_consumers.items()
        if len(consumers) == 1
        and consumers[0] > candidates[name].assignment_index
        and not successors[name]
    ]
    for terminal in terminals:
        chain: list[str] = []
        current: str | None = terminal
        chain_valid = True
        while current is not None:
            alias = candidates[current]
            chain.append(current)
            if load_counts[current] != 1:
                chain_valid = False
                break
            if current == terminal:
                if len(writer_consumers[current]) != 1:
                    chain_valid = False
                    break
            elif len(successors[current]) != 1 or writer_consumers[current]:
                chain_valid = False
                break
            current = alias.predecessor
        if chain_valid:
            valid.update({name: candidates[name] for name in chain})
    return valid


def _function_has_no_parameters(node: ast.FunctionDef) -> bool:
    arguments = node.args
    return not (
        arguments.posonlyargs
        or arguments.args
        or arguments.vararg is not None
        or arguments.kwonlyargs
        or arguments.kwarg is not None
        or arguments.defaults
        or any(default is not None for default in arguments.kw_defaults)
    )


def _scope_binding_counts(nodes: list[ast.stmt]) -> dict[str, int]:
    counts: dict[str, int] = {}

    def add(name: str) -> None:
        counts[name] = counts.get(name, 0) + 1

    for root in nodes:
        for node in ast.walk(root):
            if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
                add(node.id)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                add(node.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    add(alias.asname or alias.name.split(".", maxsplit=1)[0])
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name != "*":
                        add(alias.asname or alias.name)
            elif isinstance(node, ast.ExceptHandler) and isinstance(node.name, str):
                add(node.name)
    return counts


def _path_artifacts(
    tree: ast.AST,
    parents: dict[ast.AST, ast.AST],
    analysis_path: Path,
    logical_analysis_path: str,
    run_id: str,
    *,
    static_write_paths: dict[int, str],
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    records: dict[str, dict[str, Any]] = {}
    literal_ids: dict[str, str] = {}
    logical_parent = PurePosixPath(logical_analysis_path).parent

    def add_record(literal: str, *, is_output: bool) -> None:
        candidate = analysis_path.parent / literal
        logical_artifact_path = (logical_parent / PurePosixPath(literal)).as_posix()
        identity = f"unavailable:path:{logical_artifact_path}"
        if candidate.is_file() and not candidate.is_symlink():
            try:
                identity = sha256_digest(candidate.read_bytes())
            except OSError:
                pass
        artifact_id = stable_id("artifact", logical_artifact_path, identity)
        literal_ids[literal] = artifact_id
        existing = records.get(literal)
        kind = "output_file" if is_output else "input_file"
        if existing is None or kind == "output_file":
            records[literal] = {
                "record_type": "artifact",
                "artifact_id": artifact_id,
                "run_id": run_id,
                "kind": kind,
                "path": logical_artifact_path,
                "identity": identity,
                "producer_operation_ids": [],
            }

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or _call_name(node.func) != "Path":
            continue
        literal = _single_string_argument(node)
        if literal is None or not _safe_relative_output_path(literal):
            continue
        parent = parents.get(node)
        is_output = isinstance(parent, ast.Attribute) and parent.attr in {
            "write_text",
            "write_bytes",
        }
        add_record(literal, is_output=is_output)
    for literal in static_write_paths.values():
        add_record(literal, is_output=True)
    return list(records.values()), literal_ids


def _static_write_output_paths(
    tree: ast.Module,
    *,
    module_binding_counts: dict[str, int],
    bound_write_paths: dict[int, str],
) -> dict[int, str]:
    """Resolve only literal writes rooted at the source file's exact parent directory."""

    root_aliases = _source_parent_aliases(tree, module_binding_counts)
    result: dict[int, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not _call_name(node.func).endswith(
            (".write_text", ".write_bytes")
        ):
            continue
        literal = _literal_receiver_path(node) or bound_write_paths.get(id(node))
        if literal is None and isinstance(node.func, ast.Attribute):
            resolved = _source_parent_relative_path(node.func.value, root_aliases)
            literal = resolved.as_posix() if resolved is not None else None
        if literal is not None and _safe_relative_output_path(literal):
            result[id(node)] = literal
    return result


def _source_parent_aliases(
    tree: ast.Module, module_binding_counts: dict[str, int]
) -> frozenset[str]:
    if module_binding_counts.get("Path") != 1 or not any(
        isinstance(statement, ast.ImportFrom)
        and statement.module == "pathlib"
        and any(alias.name == "Path" and alias.asname is None for alias in statement.names)
        for statement in tree.body
    ):
        return frozenset()
    aliases: set[str] = set()
    for statement in tree.body:
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and module_binding_counts.get(statement.targets[0].id) == 1
            and _is_exact_source_parent(statement.value)
        ):
            aliases.add(statement.targets[0].id)
    return frozenset(aliases)


def _is_exact_source_parent(node: ast.expr) -> bool:
    if not isinstance(node, ast.Attribute) or node.attr != "parent":
        return False
    value = node.value
    if isinstance(value, ast.Call):
        if value.args or value.keywords or not isinstance(value.func, ast.Attribute):
            return False
        if value.func.attr != "resolve":
            return False
        value = value.func.value
    return (
        isinstance(value, ast.Call)
        and _call_name(value.func) == "Path"
        and len(value.args) == 1
        and not value.keywords
        and isinstance(value.args[0], ast.Name)
        and value.args[0].id == "__file__"
    )


def _source_parent_relative_path(
    node: ast.expr, root_aliases: frozenset[str]
) -> PurePosixPath | None:
    if isinstance(node, ast.Name) and node.id in root_aliases:
        return PurePosixPath(".")
    if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Div):
        return None
    parent = _source_parent_relative_path(node.left, root_aliases)
    if (
        parent is None
        or not isinstance(node.right, ast.Constant)
        or not isinstance(node.right.value, str)
        or not _safe_relative_output_path(node.right.value)
    ):
        return None
    return parent / PurePosixPath(node.right.value)


def _safe_relative_output_path(value: str) -> bool:
    candidate = PurePosixPath(value)
    return bool(
        value
        and "\\" not in value
        and not candidate.is_absolute()
        and candidate.as_posix() == value
        and all(part not in {"", ".", ".."} for part in candidate.parts)
    )


def _logical_path(path: Path, source_path: str | None) -> str:
    value = source_path or path.name
    candidate = PurePosixPath(value)
    if not value or candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError("source_path must be a safe repository-relative POSIX path")
    return candidate.as_posix()


def _literal_path_arguments(node: ast.Call) -> list[str]:
    return [
        literal
        for argument in node.args
        if isinstance(argument, ast.Call) and _call_name(argument.func) == "Path"
        if (literal := _single_string_argument(argument)) is not None
    ]


def _literal_receiver_path(node: ast.Call) -> str | None:
    if not isinstance(node.func, ast.Attribute) or not isinstance(node.func.value, ast.Call):
        return None
    if _call_name(node.func.value.func) != "Path":
        return None
    return _single_string_argument(node.func.value)


def _resolved_write_output_path(
    node: ast.Call, literal_path_parameters: dict[str, str]
) -> str | None:
    literal = _literal_receiver_path(node)
    if literal is not None:
        return literal
    if not isinstance(node.func, ast.Attribute) or not isinstance(node.func.value, ast.Call):
        return None
    receiver = node.func.value
    if _call_name(receiver.func) != "Path" or len(receiver.args) != 1:
        return None
    parameter = receiver.args[0]
    if not isinstance(parameter, ast.Name):
        return None
    return literal_path_parameters.get(parameter.id)


def _safe_literal_output_path_argument(node: ast.expr) -> str | None:
    if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
        return None
    value = node.value
    candidate = PurePosixPath(value)
    if (
        not value
        or "\\" in value
        or candidate.is_absolute()
        or candidate.as_posix() != value
        or any(part in {"", ".", ".."} for part in candidate.parts)
    ):
        return None
    return value


def _single_string_argument(node: ast.Call) -> str | None:
    if len(node.args) != 1 or not isinstance(node.args[0], ast.Constant):
        return None
    return node.args[0].value if isinstance(node.args[0].value, str) else None


def _record_id(record: dict[str, Any]) -> str:
    if record["record_type"] == "operation":
        return str(record["operation_id"])
    return str(record["artifact_id"])
