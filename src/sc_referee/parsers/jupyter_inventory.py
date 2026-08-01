from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

from sc_referee.core.ids import canonical_json, sha256_digest, stable_id
from sc_referee.version import SCHEMA_VERSION, __version__

JUPYTER_PARSER_ID = "parser:jupyter-notebook-inventory"
JUPYTER_PARSER_VERSION = "0.2.0"
MAX_NOTEBOOK_BYTES = 5_000_000
MAX_NOTEBOOK_CELLS = 2_000
MAX_NOTEBOOK_OUTPUTS = 10_000
MAX_JSON_NODES = 200_000
MAX_JSON_DEPTH = 100
_TIMESTAMP = "2026-07-30T00:00:00Z"
_CELL_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_CELL_TYPES = frozenset({"markdown", "code", "raw"})
_OUTPUT_TYPES = frozenset(
    {"stream", "display_data", "execute_result", "error", "update_display_data"}
)


class _DuplicateKeyError(ValueError):
    pass


def inspect_jupyter(path: Path, run_id: str, *, source_path: str | None = None) -> dict[str, Any]:
    """Inventory one bounded notebook without importing nbformat or starting a kernel."""

    logical_path = _logical_path(path, source_path)
    bare_ref: dict[str, Any] = {
        "source_kind": "file_span",
        "locator": logical_path,
        "path": logical_path,
    }
    try:
        payload = path.read_bytes()
    except OSError as error:
        return _failure_result(
            run_id,
            bare_ref,
            "error",
            f"Notebook source could not be read: {type(error).__name__}.",
        )
    digest = sha256_digest(payload)
    source_ref = {**bare_ref, "content_digest": digest}
    if len(payload) > MAX_NOTEBOOK_BYTES:
        return _failure_result(
            run_id,
            source_ref,
            "unsupported",
            f"Notebook source exceeds the {MAX_NOTEBOOK_BYTES}-byte parser ceiling.",
        )
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        return _failure_result(run_id, source_ref, "error", "Notebook source is not valid UTF-8.")
    try:
        notebook = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_nonfinite_constant,
        )
    except (json.JSONDecodeError, _DuplicateKeyError, RecursionError, ValueError) as error:
        return _failure_result(
            run_id,
            source_ref,
            "error",
            f"Notebook JSON is invalid or ambiguous: {type(error).__name__}.",
        )
    if not isinstance(notebook, dict):
        return _failure_result(
            run_id, source_ref, "unsupported", "Notebook JSON root is not an object."
        )
    if not _within_json_budget(notebook):
        return _failure_result(
            run_id,
            source_ref,
            "unsupported",
            "Notebook JSON exceeds the finite structure depth or node ceiling.",
        )
    nbformat = notebook.get("nbformat")
    nbformat_minor = notebook.get("nbformat_minor")
    if nbformat != 4 or not _is_nonnegative_int(nbformat_minor):
        return _failure_result(
            run_id,
            source_ref,
            "unsupported",
            "Only nbformat 4 with a nonnegative integer minor version is inventoried.",
        )
    cells_value = notebook.get("cells")
    if not isinstance(cells_value, list):
        return _failure_result(run_id, source_ref, "error", "Notebook cells is not an array.")
    if len(cells_value) > MAX_NOTEBOOK_CELLS:
        return _failure_result(
            run_id,
            source_ref,
            "unsupported",
            f"Notebook exceeds the {MAX_NOTEBOOK_CELLS}-cell parser ceiling.",
        )

    declared_ids: list[str] = []
    for cell in cells_value:
        if not isinstance(cell, dict):
            continue
        declared_id = cell.get("id")
        if isinstance(declared_id, str) and _CELL_ID.fullmatch(declared_id) is not None:
            declared_ids.append(declared_id)
    duplicate_ids = {value for value in declared_ids if declared_ids.count(value) > 1}
    unavailable_synthetic_ids = set(declared_ids)
    assigned_ids: set[str] = set()
    cells: list[dict[str, Any]] = []
    syntax_issues: list[dict[str, Any]] = []
    opaque_constructs: list[dict[str, Any]] = []
    output_count = 0
    for index, cell_value in enumerate(cells_value):
        index_ref = _cell_ref(logical_path, digest, f"index-{index}")
        if not isinstance(cell_value, dict):
            syntax_issues.append(_issue("Notebook cell is not an object.", index_ref))
            continue
        cell_type = cell_value.get("cell_type")
        if cell_type not in _CELL_TYPES:
            syntax_issues.append(_issue("Notebook cell type is unsupported.", index_ref))
            continue
        source_text = _cell_source(cell_value.get("source"))
        if source_text is None:
            syntax_issues.append(_issue("Notebook cell source is not a string array.", index_ref))
            continue
        metadata = cell_value.get("metadata")
        if not isinstance(metadata, dict):
            syntax_issues.append(_issue("Notebook cell metadata is not an object.", index_ref))
            continue

        declared_id = cell_value.get("id")
        if (
            isinstance(declared_id, str)
            and _CELL_ID.fullmatch(declared_id) is not None
            and declared_id not in duplicate_ids
        ):
            cell_id = declared_id
            identity_kind = "declared_unique"
        else:
            cell_id = _synthetic_cell_id(index, unavailable_synthetic_ids | assigned_ids)
            identity_kind = "synthetic_index"
            if declared_id is not None:
                syntax_issues.append(
                    _issue("Notebook cell id is invalid or duplicated.", index_ref)
                )
        assigned_ids.add(cell_id)
        cell_ref = _cell_ref(logical_path, digest, cell_id)
        execution_count = None
        execution_count_state = "not_applicable"
        outputs: list[dict[str, Any]] = []
        if cell_type == "code":
            raw_execution_count = cell_value.get("execution_count")
            if raw_execution_count is None or _is_nonnegative_int(raw_execution_count):
                execution_count = raw_execution_count
                execution_count_state = "literal"
            else:
                execution_count_state = "opaque"
                syntax_issues.append(
                    _issue(
                        "Code-cell execution_count is not null or nonnegative integer.", cell_ref
                    )
                )
            output_values = cell_value.get("outputs")
            if not isinstance(output_values, list):
                syntax_issues.append(_issue("Code-cell outputs is not an array.", cell_ref))
            else:
                if output_count + len(output_values) > MAX_NOTEBOOK_OUTPUTS:
                    return _failure_result(
                        run_id,
                        source_ref,
                        "unsupported",
                        f"Notebook exceeds the {MAX_NOTEBOOK_OUTPUTS}-output parser ceiling.",
                    )
                for output_index, output in enumerate(output_values):
                    output_count += 1
                    output_ref = _output_ref(logical_path, digest, cell_id, output_index)
                    if (
                        not isinstance(output, dict)
                        or output.get("output_type") not in _OUTPUT_TYPES
                    ):
                        syntax_issues.append(
                            _issue("Saved notebook output has an unsupported shape.", output_ref)
                        )
                        continue
                    outputs.append(
                        {
                            "output_index": output_index,
                            "output_type": output["output_type"],
                            "payload_digest": sha256_digest(canonical_json(output)),
                            "source_ref": output_ref,
                            "evidence_status": "repository_supplied_saved_output_unverified",
                        }
                    )
        cells.append(
            {
                "cell_index": index,
                "cell_id": cell_id,
                "identity_kind": identity_kind,
                "cell_type": cell_type,
                "source_digest": sha256_digest(source_text.encode("utf-8")),
                "source_byte_count": len(source_text.encode("utf-8")),
                "source_line_count": max(1, len(source_text.splitlines())),
                "metadata_digest": sha256_digest(canonical_json(metadata)),
                "execution_count": execution_count,
                "execution_count_state": execution_count_state,
                "source_ref": cell_ref,
                "outputs": outputs,
            }
        )

    metadata = notebook.get("metadata")
    if not isinstance(metadata, dict):
        syntax_issues.append(_issue("Notebook metadata is not an object.", source_ref))
        metadata = {}
    language_declaration = _language_declaration(metadata)
    if (
        any(item["cell_type"] == "code" for item in cells)
        and language_declaration["state"] != "recognized"
    ):
        opaque_constructs.append(
            {
                "kind": "notebook_cell_language_boundary",
                "reason": (
                    "Static cell-language parsing requires one unconflicted notebook language "
                    "declaration equal to Python or R."
                ),
                "source_ref": source_ref,
            }
        )
    opaque_constructs.append(
        {
            "kind": "notebook_runtime_state",
            "reason": (
                "Static notebook JSON does not establish cell execution, execution order, "
                "hidden kernel state, environment identity, or code-to-output provenance."
            ),
            "source_ref": source_ref,
        }
    )
    if output_count:
        opaque_constructs.append(
            {
                "kind": "saved_notebook_outputs_unverified",
                "reason": (
                    "Saved outputs are repository-supplied evidence and may be stale or edited."
                ),
                "source_ref": source_ref,
            }
        )
    state = "partially_parsed" if syntax_issues else "parsed"
    return _result(
        run_id,
        source_ref,
        state=state,
        syntax_issues=syntax_issues,
        opaque_constructs=opaque_constructs,
        extensions={
            "x-notebook-profile": "bounded-nbformat4-cell-output-inventory-v2",
            "x-notebook-format": {"major": nbformat, "minor": nbformat_minor},
            "x-notebook-metadata-digest": sha256_digest(canonical_json(metadata)),
            "x-notebook-declared-language": _declared_language(metadata),
            "x-notebook-language-declaration": language_declaration,
            "x-notebook-cells": cells,
            "x-notebook-cell-count": len(cells_value),
            "x-notebook-inventoried-cell-count": len(cells),
            "x-notebook-output-count": output_count,
            "x-notebook-inventory-complete": not syntax_issues,
            "x-notebook-executes-project-code": False,
        },
    )


def _result(
    run_id: str,
    source_ref: dict[str, Any],
    *,
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
            JUPYTER_PARSER_ID,
            str(source_ref.get("path")),
            str(source_ref.get("content_digest")),
        ),
        "audit_run_id": run_id,
        "parser_id": JUPYTER_PARSER_ID,
        "parser_version": JUPYTER_PARSER_VERSION,
        "source_ref": source_ref,
        "state": state,
        "coverage_status": (
            "not_covered"
            if state in {"error", "unsupported", "parser_unavailable"}
            else "partially_covered"
        ),
        "emitted_record_refs": [],
        "syntax_issues": syntax_issues,
        "opaque_constructs": opaque_constructs,
        "parser_disagreement": None,
        "started_at": _TIMESTAMP,
        "completed_at": _TIMESTAMP,
        "extensions": extensions,
        "provenance": {
            "actor": {"actor_kind": "parser", "actor_id": JUPYTER_PARSER_ID},
            "method": "static_non_executing_jupyter_json_inventory",
            "created_at": _TIMESTAMP,
            "tool": "sc-referee",
            "tool_version": __version__,
        },
    }


def _failure_result(
    run_id: str,
    source_ref: dict[str, Any],
    state: str,
    reason: str,
) -> dict[str, Any]:
    return _result(
        run_id,
        source_ref,
        state=state,
        syntax_issues=([_issue(reason, source_ref)] if state == "error" else []),
        opaque_constructs=[
            {"kind": "jupyter_parser_boundary", "reason": reason, "source_ref": source_ref}
        ],
        extensions={
            "x-notebook-profile": "bounded-nbformat4-cell-output-inventory-v2",
            "x-notebook-language-declaration": {
                "state": "absent",
                "language": None,
                "sources": [],
            },
            "x-notebook-cells": [],
            "x-notebook-cell-count": 0,
            "x-notebook-inventoried-cell-count": 0,
            "x-notebook-output-count": 0,
            "x-notebook-inventory-complete": False,
            "x-notebook-executes-project-code": False,
        },
    )


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _reject_nonfinite_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def _within_json_budget(value: object) -> bool:
    stack: list[tuple[object, int]] = [(value, 1)]
    nodes = 0
    while stack:
        current, depth = stack.pop()
        nodes += 1
        if nodes > MAX_JSON_NODES or depth > MAX_JSON_DEPTH:
            return False
        if isinstance(current, dict):
            stack.extend((item, depth + 1) for item in current.values())
        elif isinstance(current, list):
            stack.extend((item, depth + 1) for item in current)
    return True


def _cell_source(value: object) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return "".join(value)
    return None


def _synthetic_cell_id(index: int, unavailable: set[str]) -> str:
    candidate = f"index-{index}"
    if candidate not in unavailable:
        return candidate
    candidate = f"index-{index}-synthetic"
    suffix = 2
    while candidate in unavailable:
        candidate = f"index-{index}-synthetic-{suffix}"
        suffix += 1
    return candidate


def _cell_ref(logical_path: str, digest: str, cell_id: str) -> dict[str, Any]:
    return {
        "source_kind": "notebook_cell",
        "locator": f"{logical_path}#cell={cell_id}",
        "path": logical_path,
        "content_digest": digest,
        "cell_id": cell_id,
        "selector": "source",
    }


def _output_ref(logical_path: str, digest: str, cell_id: str, output_index: int) -> dict[str, Any]:
    return {
        "source_kind": "notebook_cell",
        "locator": f"{logical_path}#cell={cell_id}&output={output_index}",
        "path": logical_path,
        "content_digest": digest,
        "cell_id": cell_id,
        "selector": f"output-{output_index}",
    }


def _issue(message: str, source_ref: dict[str, Any]) -> dict[str, Any]:
    return {"message": message, "source_ref": source_ref, "recoverable": True}


def _declared_language(metadata: dict[str, Any]) -> str | None:
    language_info = metadata.get("language_info")
    if not isinstance(language_info, dict):
        return None
    name = language_info.get("name")
    return name if isinstance(name, str) and name else None


def _language_declaration(metadata: dict[str, Any]) -> dict[str, Any]:
    declarations: list[dict[str, str]] = []
    for container_name, field in (("language_info", "name"), ("kernelspec", "language")):
        container = metadata.get(container_name)
        value = container.get(field) if isinstance(container, dict) else None
        if isinstance(value, str) and value.strip():
            declarations.append(
                {
                    "field": f"metadata.{container_name}.{field}",
                    "value": value,
                    "normalized_value": value.strip().casefold(),
                }
            )
    normalized = {item["normalized_value"] for item in declarations}
    if not declarations:
        state = "absent"
        language = None
    elif len(normalized) != 1:
        state = "ambiguous"
        language = None
    else:
        candidate = next(iter(normalized))
        state = "recognized" if candidate in {"python", "r"} else "unsupported"
        language = candidate if state == "recognized" else None
    return {"state": state, "language": language, "sources": declarations}


def extract_jupyter_code_cells(path: Path, parser_result: dict[str, Any]) -> list[dict[str, Any]]:
    """Re-extract inventoried code-cell bytes and verify them against the parent record."""

    payload = path.read_bytes()
    expected_digest = parser_result.get("source_ref", {}).get("content_digest")
    if sha256_digest(payload) != expected_digest or len(payload) > MAX_NOTEBOOK_BYTES:
        raise ValueError("notebook bytes no longer match the inventoried parent")
    notebook = json.loads(
        payload.decode("utf-8"),
        object_pairs_hook=_unique_object,
        parse_constant=_reject_nonfinite_constant,
    )
    if not isinstance(notebook, dict) or not _within_json_budget(notebook):
        raise ValueError("notebook structure no longer matches the inventoried parent")
    raw_cells = notebook.get("cells")
    if not isinstance(raw_cells, list) or len(raw_cells) > MAX_NOTEBOOK_CELLS:
        raise ValueError("notebook cells no longer match the inventoried parent")
    result: list[dict[str, Any]] = []
    for cell in parser_result.get("extensions", {}).get("x-notebook-cells", []):
        if not isinstance(cell, dict) or cell.get("cell_type") != "code":
            continue
        index = cell.get("cell_index")
        if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(raw_cells):
            raise ValueError("inventoried notebook cell index is invalid")
        raw_cell = raw_cells[index]
        if not isinstance(raw_cell, dict):
            raise ValueError("inventoried notebook cell is no longer an object")
        source_text = _cell_source(raw_cell.get("source"))
        if source_text is None or sha256_digest(source_text.encode("utf-8")) != cell.get(
            "source_digest"
        ):
            raise ValueError("notebook cell source no longer matches its inventory digest")
        result.append({"cell": cell, "source_text": source_text})
    return result


def _is_nonnegative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _logical_path(path: Path, source_path: str | None) -> str:
    value = source_path or path.name
    candidate = PurePosixPath(value)
    if not value or candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError("source_path must be a safe repository-relative POSIX path")
    return candidate.as_posix()
