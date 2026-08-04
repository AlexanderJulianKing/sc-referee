from __future__ import annotations

import ast
import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pytest
import sc_referee_evaluation.prospective_selected_result_verifier as target


def _contract(project_root: Path) -> dict[str, Any]:
    path = (
        project_root
        / "evaluation"
        / "qualification"
        / "selected-result-verifier-v1.1.0-precase"
        / "semantic-review-contract.json"
    )
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _target_tree(project_root: Path) -> ast.Module:
    path = (
        project_root
        / "evaluation"
        / "src"
        / "sc_referee_evaluation"
        / "prospective_selected_result_verifier.py"
    )
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _literal_exception_reasons(tree: ast.AST, exception_name: str) -> set[str]:
    reasons: set[str] = set()
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == exception_name
    ]
    assert calls, f"No {exception_name} reason sites were found."
    for call in calls:
        assert len(call.args) == 1
        argument = call.args[0]
        assert isinstance(argument, ast.Constant)
        assert isinstance(argument.value, str)
        reasons.add(argument.value)
    return reasons


def _assigned_string(statement: ast.stmt, name: str) -> str | None:
    if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
        return None
    target_node = statement.targets[0]
    if not isinstance(target_node, ast.Name) or target_node.id != name:
        return None
    if not isinstance(statement.value, ast.Constant) or not isinstance(statement.value.value, str):
        return None
    return statement.value.value


def _assigned_string_list(statement: ast.stmt, name: str) -> list[str] | None:
    if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
        return None
    target_node = statement.targets[0]
    if not isinstance(target_node, ast.Name) or target_node.id != name:
        return None
    if not isinstance(statement.value, ast.List):
        return None
    values: list[str] = []
    for item in statement.value.elts:
        if not isinstance(item, ast.Constant) or not isinstance(item.value, str):
            return None
        values.append(item.value)
    return values


def _literal_reasons_for_status(tree: ast.AST, status: str) -> set[str]:
    matches: set[str] = set()
    for node in ast.walk(tree):
        for _, field in ast.iter_fields(node):
            if not isinstance(field, list) or not all(isinstance(item, ast.stmt) for item in field):
                continue
            statements = list(field)
            if status not in {
                assigned
                for statement in statements
                if (assigned := _assigned_string(statement, "status")) is not None
            }:
                continue
            for statement in statements:
                reason_values = _assigned_string_list(statement, "reasons")
                if reason_values is not None:
                    matches.update(reason_values)
    return matches


def _function_literal_sets(tree: ast.Module, function_name: str) -> dict[str, set[str]]:
    functions = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name
    ]
    assert len(functions) == 1
    result: dict[str, set[str]] = {}
    for node in ast.walk(functions[0]):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target_node = node.targets[0]
        if not isinstance(target_node, ast.Name) or not isinstance(node.value, ast.Set):
            continue
        values = {
            item.value
            for item in node.value.elts
            if isinstance(item, ast.Constant) and isinstance(item.value, str)
        }
        assert len(values) == len(node.value.elts)
        result[target_node.id] = values
    return result


def _dot_suffixes(value: str) -> set[str]:
    return set(re.findall(r"\.[a-z][a-z0-9]*", value))


def _derive_reason(
    *,
    selected_report: str,
    payloads: dict[str, bytes],
    executable_paths: Iterable[str] = (),
) -> str:
    with pytest.raises((target._Unsupported, target._Insufficient)) as raised:
        target._derive_python_static_marked_report_bindings(
            selected_report,
            payloads,
            set(executable_paths),
        )
    return raised.value.reason


def _operand_case(source_path: str, source_payload: bytes) -> dict[str, bytes]:
    report_payload = f"[selected-result] {len(source_payload)}\n".encode("ascii")
    python_payload = (
        "from pathlib import Path\n"
        f'raw = Path("{source_path}").read_bytes()\n'
        'rendered = "[selected-result] " + str(len(raw)) + "\\n"\n'
        'Path("report.txt").write_text(rendered)\n'
    ).encode("ascii")
    return {
        source_path: source_payload,
        "analysis.py": python_payload,
        "report.txt": report_payload,
    }


def test_target_reason_namespaces_exactly_equal_the_frozen_contract(project_root: Path) -> None:
    contract = _contract(project_root)
    tree = _target_tree(project_root)
    reason_codes = contract["reason_codes_by_state"]

    assert _literal_exception_reasons(tree, "_Unsupported") == set(reason_codes["U"])
    assert _literal_exception_reasons(tree, "_Insufficient") == set(reason_codes["I"])
    assert _literal_reasons_for_status(tree, "ambiguous_selected_result") == set(reason_codes["A"])


def test_target_limits_exactly_equal_the_frozen_contract(project_root: Path) -> None:
    budgets = _contract(project_root)["budgets"]
    observed = {
        "case_files": target.MAX_CASE_FILES,
        "case_directories": target.MAX_CASE_DIRECTORIES,
        "case_entries": target.MAX_CASE_ENTRIES,
        "case_depth": target.MAX_CASE_DEPTH,
        "file_bytes": target.MAX_FILE_BYTES,
        "total_bytes": target.MAX_TOTAL_BYTES,
        "candidate_bindings": target.MAX_CANDIDATE_BINDINGS,
        "text_lines": target.MAX_TEXT_LINES,
        "python_source_bytes": target.MAX_PYTHON_SOURCE_BYTES,
        "python_ast_nodes": target.MAX_PYTHON_AST_NODES,
        "module_statements": target.MAX_MODULE_STATEMENTS,
        "static_evaluation_steps": target.MAX_STATIC_EVALUATION_STEPS,
        "static_value_bytes": target.MAX_STATIC_VALUE_BYTES,
        "static_sequence_items": target.MAX_STATIC_SEQUENCE_ITEMS,
        "static_integer_bits": target.MAX_STATIC_INTEGER_BITS,
    }

    assert set(observed) == set(budgets)
    assert observed == {name: value["maximum_inclusive"] for name, value in budgets.items()}


def test_target_allowlists_and_suffixes_exactly_equal_the_frozen_contract(
    project_root: Path,
) -> None:
    contract = _contract(project_root)
    source_profile = contract["source_artifact_profile"]
    runtime_profile = contract["runtime_and_text_profile"]
    python_grammar = contract["python_module_grammar"]
    call_allowlist = _function_literal_sets(
        _target_tree(project_root),
        "_validate_closed_python_calls",
    )

    assert target._NON_PYTHON_SOURCE_SUFFIXES == set(
        source_profile["forbidden_suffixes_case_insensitive"]
    )
    assert target._NON_PYTHON_SOURCE_NAMES == set(
        source_profile["forbidden_names_case_insensitive"]
    )
    assert target._SOURCE_OPERAND_SUFFIXES == _dot_suffixes(runtime_profile["operand_role"])
    assert target._SELECTED_REPORT_SUFFIXES == _dot_suffixes(runtime_profile["report_role"])
    assert {".py"} == _dot_suffixes(runtime_profile["python_paths"])
    assert target._RESERVED_PYTHON_BINDINGS == set(python_grammar["reserved_names"])
    assert call_allowlist == {
        "allowed_names": set(python_grammar["whole_module_call_allowlist"]["names"]),
        "allowed_attributes": set(python_grammar["whole_module_call_allowlist"]["attributes"]),
    }
    assert target._SELECTED_RESULT_PREFIX in runtime_profile["marker"]
    cookie_pattern = target._PYTHON_ENCODING_COOKIE.pattern.decode("ascii").replace(r"\#", "#")
    assert cookie_pattern in runtime_profile["python_encoding"]


def test_suspicious_output_method_registry_is_frozen_by_the_contract(
    project_root: Path,
) -> None:
    python_grammar = _contract(project_root)["python_module_grammar"]

    assert python_grammar.get("potential_output_methods") == sorted(
        target._POTENTIAL_OUTPUT_METHODS
    )


@pytest.mark.parametrize(
    ("selected_report", "report_payload", "executable", "expected_reason"),
    [
        ("report.csv", b"[selected-result] x\n", False, "unsupported_selected_report_role"),
        ("report.txt", b"[selected-result] x\n", True, "unsupported_selected_report_role"),
        (
            "report.txt",
            b"#!ignored\n[selected-result] x\n",
            False,
            "unsupported_selected_report_role",
        ),
        ("report.txt", b"[selected-result] x\x00\n", False, "unsupported_selected_report_role"),
        ("report.txt", b"[selected-result] x\r\n", False, "non_lf_normalized_text_evidence"),
        ("report.txt", "[selected-result] café\n".encode(), False, "non_ascii_text_evidence"),
    ],
)
def test_selected_report_role_matches_the_frozen_contract(
    selected_report: str,
    report_payload: bytes,
    executable: bool,
    expected_reason: str,
) -> None:
    assert (
        _derive_reason(
            selected_report=selected_report,
            payloads={selected_report: report_payload},
            executable_paths={selected_report} if executable else set(),
        )
        == expected_reason
    )


@pytest.mark.parametrize(
    ("source_path", "source_payload", "executable", "expected_reason"),
    [
        ("data.bin", b"x", False, "unsupported_source_operand_role"),
        ("data.csv", b"x", True, "unsupported_source_operand_role"),
        ("data.csv", b"#!ignored\n", False, "unsupported_source_operand_role"),
        ("data.csv", b"x\x00", False, "unsupported_source_operand_role"),
        ("data.csv", b"x\r\n", False, "non_lf_normalized_text_evidence"),
        ("data.csv", "café\n".encode(), False, "non_ascii_text_evidence"),
    ],
)
def test_source_operand_role_matches_the_frozen_contract(
    source_path: str,
    source_payload: bytes,
    executable: bool,
    expected_reason: str,
) -> None:
    assert (
        _derive_reason(
            selected_report="report.txt",
            payloads=_operand_case(source_path, source_payload),
            executable_paths={source_path} if executable else set(),
        )
        == expected_reason
    )


def test_python_cr_bytes_follow_the_frozen_non_lf_reason(project_root: Path) -> None:
    contract = _contract(project_root)
    predicate = contract["reason_predicates"]["non_lf_normalized_text_evidence"]
    assert "Python, report, or operand payload contains a CR byte" in predicate
    payload = b"[selected-result] x\n"
    python_payload = (
        b"from pathlib import Path\r\n"
        b'data = Path("data.csv").read_text()\r\n'
        b'Path("report.txt").write_text(data)\r\n'
    )

    assert (
        _derive_reason(
            selected_report="report.txt",
            payloads={
                "analysis.py": python_payload,
                "data.csv": payload,
                "report.txt": payload,
            },
        )
        == "non_lf_normalized_text_evidence"
    )
