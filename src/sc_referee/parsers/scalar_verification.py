from __future__ import annotations

import ast
import csv
import math
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from sc_referee.core.ids import sha256_digest, stable_id


class UnsupportedScalarVerification(ValueError):
    """Raised when source does not match the bounded auditor-owned verification profile."""


@dataclass(frozen=True)
class _SelectedVector:
    variable: str
    value_column: str
    group_column: str
    group_value: str


def verify_mean_difference(
    path: Path, run_id: str, *, source_path: str | None = None
) -> dict[str, Any]:
    """Verify one literal filtered mean difference without executing project-authored code."""

    logical_path = _logical_path(path, source_path)
    payload = path.read_bytes()
    source_text = payload.decode("utf-8", errors="strict")
    source_digest = sha256_digest(payload)
    tree = ast.parse(source_text, filename=str(path), type_comments=True)
    function, left, right, return_node = _find_supported_function(tree)
    input_relative = _find_literal_input_path(tree, function.name)
    input_path = _safe_local_path(path.parent, input_relative)
    data_payload = input_path.read_bytes()
    data_digest = sha256_digest(data_payload)
    logical_input_path = (PurePosixPath(logical_path).parent / input_relative).as_posix()
    rows = list(csv.DictReader(data_payload.decode("utf-8", errors="strict").splitlines()))
    if not rows:
        raise UnsupportedScalarVerification("the selected input table has no rows")
    left_values = _selected_values(rows, left)
    right_values = _selected_values(rows, right)
    value = sum(left_values) / len(left_values) - sum(right_values) / len(right_values)
    if not math.isfinite(value):
        raise UnsupportedScalarVerification("the verified scalar is not finite")

    orientation = _orientation(left.group_value, right.group_value)
    return_ref = _source_ref(logical_path, source_digest, source_text, return_node)
    data_lines = data_payload.decode("utf-8", errors="strict").splitlines()
    data_ref = {
        "source_kind": "file_span",
        "locator": f"{logical_input_path}:1-{max(1, len(data_lines))}",
        "path": logical_input_path,
        "content_digest": data_digest,
        "start_line": 1,
        "end_line": max(1, len(data_lines)),
        "quoted_text": "\n".join(data_lines),
    }
    return {
        "record_type": "observed_result",
        "result_id": stable_id(
            "observed-result",
            source_digest,
            data_digest,
            str(return_node.lineno),
            left.group_value,
            right.group_value,
        ),
        "run_id": run_id,
        "value": value,
        "comparison": f"{left.group_value} versus {right.group_value}",
        "orientation": orientation,
        "scale": left.value_column,
        "source_refs": [return_ref, data_ref],
        "lineage_status": "complete",
        "analysis_path": logical_path,
        "input_path": logical_input_path,
        "producer_operation_id": stable_id(
            "operation",
            logical_path,
            source_digest,
            str(function.lineno),
            str(getattr(function, "end_lineno", function.lineno)),
            "estimate",
        ),
        "artifact_id": stable_id("artifact", logical_path, source_digest, function.name, "return"),
        "input_artifact_id": stable_id("artifact", logical_input_path, data_digest),
    }


def _find_supported_function(
    tree: ast.Module,
) -> tuple[ast.FunctionDef, _SelectedVector, _SelectedVector, ast.Return]:
    matches: list[tuple[ast.FunctionDef, _SelectedVector, _SelectedVector, ast.Return]] = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        vectors = {
            assignment.targets[0].id: vector
            for assignment in node.body
            if isinstance(assignment, ast.Assign)
            and len(assignment.targets) == 1
            and isinstance(assignment.targets[0], ast.Name)
            and (vector := _selected_vector(assignment.targets[0].id, assignment.value)) is not None
        }
        for child in node.body:
            names = _mean_difference_names(child)
            if names is None or names[0] not in vectors or names[1] not in vectors:
                continue
            left = vectors[names[0]]
            right = vectors[names[1]]
            if left.value_column != right.value_column or left.group_column != right.group_column:
                continue
            if not isinstance(child, ast.Return):
                continue
            matches.append((node, left, right, child))
    if len(matches) != 1:
        raise UnsupportedScalarVerification(
            "expected exactly one statically supported filtered mean-difference function"
        )
    return matches[0]


def _selected_vector(variable: str, value: ast.expr) -> _SelectedVector | None:
    if not isinstance(value, ast.ListComp) or len(value.generators) != 1:
        return None
    generator = value.generators[0]
    if (
        not isinstance(generator.target, ast.Name)
        or len(generator.ifs) != 1
        or not isinstance(value.elt, ast.Call)
        or _call_name(value.elt.func) != "float"
        or len(value.elt.args) != 1
    ):
        return None
    value_column = _row_column(value.elt.args[0], generator.target.id)
    condition = generator.ifs[0]
    if (
        value_column is None
        or not isinstance(condition, ast.Compare)
        or len(condition.ops) != 1
        or not isinstance(condition.ops[0], ast.Eq)
        or len(condition.comparators) != 1
    ):
        return None
    group_column = _row_column(condition.left, generator.target.id)
    comparator = condition.comparators[0]
    if (
        group_column is None
        or not isinstance(comparator, ast.Constant)
        or not isinstance(comparator.value, str)
    ):
        return None
    return _SelectedVector(variable, value_column, group_column, comparator.value)


def _mean_difference_names(node: ast.stmt) -> tuple[str, str] | None:
    if not isinstance(node, ast.Return) or not isinstance(node.value, ast.BinOp):
        return None
    if not isinstance(node.value.op, ast.Sub):
        return None
    left = _mean_variable(node.value.left)
    right = _mean_variable(node.value.right)
    return (left, right) if left is not None and right is not None else None


def _mean_variable(node: ast.expr) -> str | None:
    if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Div):
        return None
    if not isinstance(node.left, ast.Call) or not isinstance(node.right, ast.Call):
        return None
    if _call_name(node.left.func) != "sum" or _call_name(node.right.func) != "len":
        return None
    if len(node.left.args) != 1 or len(node.right.args) != 1:
        return None
    if not isinstance(node.left.args[0], ast.Name) or not isinstance(node.right.args[0], ast.Name):
        return None
    if node.left.args[0].id != node.right.args[0].id:
        return None
    return node.left.args[0].id


def _find_literal_input_path(tree: ast.Module, function_name: str) -> str:
    paths: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or _call_name(node.func) != function_name:
            continue
        if len(node.args) != 1 or not isinstance(node.args[0], ast.Call):
            continue
        path_call = node.args[0]
        if _call_name(path_call.func) != "Path" or len(path_call.args) != 1:
            continue
        literal = path_call.args[0]
        if isinstance(literal, ast.Constant) and isinstance(literal.value, str):
            paths.add(literal.value)
    if len(paths) != 1:
        raise UnsupportedScalarVerification(
            "expected one literal local input path for the supported function"
        )
    return next(iter(paths))


def _safe_local_path(root: Path, relative: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise UnsupportedScalarVerification("the input path is outside the snapshot root")
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as error:
        raise UnsupportedScalarVerification("the input path escapes the snapshot root") from error
    if not resolved.is_file() or resolved.is_symlink():
        raise UnsupportedScalarVerification("the input path is unavailable or unsafe")
    return resolved


def _logical_path(path: Path, source_path: str | None) -> str:
    value = source_path or path.name
    candidate = PurePosixPath(value)
    if not value or candidate.is_absolute() or ".." in candidate.parts:
        raise UnsupportedScalarVerification(
            "source_path must be a safe repository-relative POSIX path"
        )
    return candidate.as_posix()


def _selected_values(rows: list[dict[str, str]], vector: _SelectedVector) -> list[float]:
    values: list[float] = []
    for row in rows:
        if vector.group_column not in row or vector.value_column not in row:
            raise UnsupportedScalarVerification("the selected table columns are unavailable")
        if row[vector.group_column] != vector.group_value:
            continue
        try:
            value = float(row[vector.value_column])
        except (TypeError, ValueError) as error:
            raise UnsupportedScalarVerification("a selected value is not numeric") from error
        if not math.isfinite(value):
            raise UnsupportedScalarVerification("a selected value is not finite")
        values.append(value)
    if not values:
        raise UnsupportedScalarVerification("a selected group has no rows")
    return values


def _row_column(node: ast.expr, row_name: str) -> str | None:
    if not isinstance(node, ast.Subscript) or not isinstance(node.value, ast.Name):
        return None
    if node.value.id != row_name:
        return None
    if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
        return node.slice.value
    return None


def _orientation(left: str, right: str) -> str:
    pair = (left.casefold(), right.casefold())
    if pair == ("treated", "control"):
        return "treated_minus_control"
    if pair == ("control", "treated"):
        return "control_minus_treated"
    return "unknown"


def _source_ref(path: str, digest: str, source_text: str, node: ast.AST) -> dict[str, Any]:
    start_line = getattr(node, "lineno", 1)
    end_line = getattr(node, "end_lineno", start_line)
    result: dict[str, Any] = {
        "source_kind": "file_span",
        "locator": f"{path}:{start_line}-{end_line}",
        "path": path,
        "content_digest": digest,
        "start_line": start_line,
        "end_line": end_line,
        "start_column": getattr(node, "col_offset", 0) + 1,
        "end_column": getattr(node, "end_col_offset", 0) + 1,
    }
    quoted = ast.get_source_segment(source_text, node)
    if quoted:
        result["quoted_text"] = quoted
    return result


def _call_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return "<dynamic>"
