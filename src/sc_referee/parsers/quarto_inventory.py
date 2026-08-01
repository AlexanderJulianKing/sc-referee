from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from typing import Any

from sc_referee.core.ids import sha256_digest, stable_id
from sc_referee.version import SCHEMA_VERSION, __version__

QUARTO_PARSER_ID = "parser:quarto-source-inventory"
QUARTO_PARSER_VERSION = "0.2.0"
MAX_QUARTO_BYTES = 2_000_000
MAX_QUARTO_LINES = 100_000
MAX_QUARTO_CELLS = 2_000
_TIMESTAMP = "2026-07-30T00:00:00Z"
_CELL_START = re.compile(r"^\s*```\{(?P<engine>[A-Za-z][A-Za-z0-9_+.-]{0,31})\}\s*$")
_FENCE_END = re.compile(r"^\s*```\s*$")
_OPTION = re.compile(r"^\s*#\|\s*(?P<key>[A-Za-z][A-Za-z0-9_-]{0,63})\s*:\s*(?P<value>.*)$")
_LABEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


def inspect_quarto(path: Path, run_id: str, *, source_path: str | None = None) -> dict[str, Any]:
    """Inventory one bounded Quarto source without rendering or executing it."""

    logical_path = _logical_path(path, source_path)
    bare_ref: dict[str, Any] = {
        "source_kind": "file_span",
        "locator": logical_path,
        "path": logical_path,
    }
    try:
        payload = path.read_bytes()
    except OSError as error:
        return _failure(
            run_id,
            bare_ref,
            "error",
            f"Quarto source could not be read: {type(error).__name__}.",
        )
    digest = sha256_digest(payload)
    source_ref = {**bare_ref, "content_digest": digest}
    if len(payload) > MAX_QUARTO_BYTES:
        return _failure(
            run_id,
            source_ref,
            "unsupported",
            f"Quarto source exceeds the {MAX_QUARTO_BYTES}-byte parser ceiling.",
        )
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        return _failure(run_id, source_ref, "error", "Quarto source is not valid UTF-8.")
    lines = text.splitlines()
    if len(lines) > MAX_QUARTO_LINES:
        return _failure(
            run_id,
            source_ref,
            "unsupported",
            f"Quarto source exceeds the {MAX_QUARTO_LINES}-line parser ceiling.",
        )
    line_count = max(1, len(lines))
    source_ref.update(
        {
            "locator": f"{logical_path}:1-{line_count}",
            "start_line": 1,
            "end_line": line_count,
        }
    )
    front_matter, content_start, front_issue = _front_matter(lines, source_ref)
    raw_cells, cell_lines, syntax_issues = _raw_cells(lines, content_start, source_ref)
    if front_issue is not None:
        syntax_issues.append(front_issue)
    if len(raw_cells) > MAX_QUARTO_CELLS:
        return _failure(
            run_id,
            source_ref,
            "unsupported",
            f"Quarto source exceeds the {MAX_QUARTO_CELLS}-cell parser ceiling.",
        )
    cells = _assign_cell_labels(raw_cells, syntax_issues)
    prose_spans = [
        {
            "start_line": index,
            "end_line": index,
            "start_column": len(line) - len(line.lstrip()) + 1,
            "end_column": len(line.rstrip()) + 1,
            "text": line.strip(),
        }
        for index, line in enumerate(lines, start=1)
        if index >= content_start
        and index not in cell_lines
        and line.strip()
        and not line.lstrip().startswith("#")
    ]
    state = "partially_parsed" if syntax_issues else "parsed"
    return _result(
        run_id,
        source_ref,
        state,
        syntax_issues,
        {
            "x-quarto-profile": "bounded-quarto-source-cell-inventory-v2",
            "x-quarto-front-matter-span": front_matter,
            "x-quarto-prose-spans": prose_spans,
            "x-quarto-cells": cells,
            "x-quarto-cell-count": len(cells),
            "x-quarto-executes-project-code": False,
        },
    )


def _front_matter(
    lines: list[str], source_ref: dict[str, Any]
) -> tuple[dict[str, int] | None, int, dict[str, Any] | None]:
    if not lines or lines[0].strip() != "---":
        return None, 1, None
    for index, line in enumerate(lines[1:], start=2):
        if line.strip() in {"---", "..."}:
            return {"start_line": 1, "end_line": index}, index + 1, None
    return None, 1, _issue("Quarto YAML front matter is not closed.", _line_ref(source_ref, 1))


def _raw_cells(
    lines: list[str], content_start: int, source_ref: dict[str, Any]
) -> tuple[list[dict[str, Any]], set[int], list[dict[str, Any]]]:
    cells: list[dict[str, Any]] = []
    cell_lines: set[int] = set()
    issues: list[dict[str, Any]] = []
    index = max(0, content_start - 1)
    while index < len(lines):
        match = _CELL_START.fullmatch(lines[index])
        if match is None:
            index += 1
            continue
        fence_start = index + 1
        end_index = next(
            (
                candidate
                for candidate in range(index + 1, len(lines))
                if _FENCE_END.fullmatch(lines[candidate]) is not None
            ),
            None,
        )
        if end_index is None:
            issues.append(
                _issue("Quarto executable cell is not closed.", _line_ref(source_ref, fence_start))
            )
            cell_lines.update(range(fence_start, len(lines) + 1))
            break
        fence_end = end_index + 1
        cell_lines.update(range(fence_start, fence_end + 1))
        option_records: list[dict[str, str]] = []
        code_start_index = index + 1
        while code_start_index < end_index:
            option_match = _OPTION.fullmatch(lines[code_start_index])
            if option_match is None:
                break
            option_records.append(
                {"key": option_match.group("key"), "value": option_match.group("value")}
            )
            code_start_index += 1
        code_text = "\n".join(lines[code_start_index:end_index])
        if code_start_index < end_index:
            code_text += "\n"
        label_values = [item["value"] for item in option_records if item["key"] == "label"]
        declared_label = (
            label_values[0]
            if len(label_values) == 1 and _LABEL.fullmatch(label_values[0]) is not None
            else None
        )
        if label_values and declared_label is None:
            issues.append(
                _issue(
                    "Quarto cell label is invalid or repeated.", _line_ref(source_ref, fence_start)
                )
            )
        cells.append(
            {
                "cell_index": len(cells),
                "engine": match.group("engine"),
                "declared_label": declared_label,
                "options": option_records,
                "evaluation_state": _evaluation_state(option_records),
                "fence_start_line": fence_start,
                "code_start_line": min(code_start_index + 1, fence_end),
                "code_end_line": max(fence_start, fence_end - 1),
                "fence_end_line": fence_end,
                "code_digest": sha256_digest(code_text.encode("utf-8")),
                "_source_ref": source_ref,
            }
        )
        index = end_index + 1
    return cells, cell_lines, issues


def _assign_cell_labels(
    raw_cells: list[dict[str, Any]], syntax_issues: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    declared = [str(item["declared_label"]) for item in raw_cells if item["declared_label"]]
    duplicates = {value for value in declared if declared.count(value) > 1}
    unavailable = set(declared)
    assigned: set[str] = set()
    cells: list[dict[str, Any]] = []
    for item in raw_cells:
        source_ref = item.pop("_source_ref")
        declared_label = item.pop("declared_label")
        if isinstance(declared_label, str) and declared_label not in duplicates:
            label = declared_label
            identity_kind = "declared_unique"
        else:
            label = _synthetic_label(int(item["cell_index"]), unavailable | assigned)
            identity_kind = "synthetic_index"
            if declared_label in duplicates:
                syntax_issues.append(
                    _issue(
                        "Quarto cell label is duplicated.",
                        _line_ref(source_ref, int(item["fence_start_line"])),
                    )
                )
        assigned.add(label)
        item.update(
            {
                "label": label,
                "identity_kind": identity_kind,
                "source_ref": {
                    "source_kind": "document_chunk",
                    "locator": f"{source_ref['path']}#cell={label}",
                    "path": source_ref["path"],
                    "content_digest": source_ref["content_digest"],
                    "chunk_label": label,
                    "start_line": item["fence_start_line"],
                    "end_line": item["fence_end_line"],
                },
            }
        )
        cells.append(item)
    return cells


def _evaluation_state(options: list[dict[str, str]]) -> str:
    values = [item["value"].strip().lower() for item in options if item["key"] == "eval"]
    if values == ["false"]:
        return "disabled_declared"
    if values == ["true"]:
        return "enabled_declared"
    return "unknown"


def _synthetic_label(index: int, unavailable: set[str]) -> str:
    candidate = f"cell-{index}"
    suffix = 2
    while candidate in unavailable:
        candidate = f"cell-{index}-synthetic-{suffix}"
        suffix += 1
    return candidate


def _result(
    run_id: str,
    source_ref: dict[str, Any],
    state: str,
    syntax_issues: list[dict[str, Any]],
    extensions: dict[str, Any],
) -> dict[str, Any]:
    return {
        "record_type": "parser_result",
        "schema_version": SCHEMA_VERSION,
        "parser_result_id": stable_id(
            "parser-result",
            QUARTO_PARSER_ID,
            str(source_ref.get("path")),
            str(source_ref.get("content_digest")),
        ),
        "audit_run_id": run_id,
        "parser_id": QUARTO_PARSER_ID,
        "parser_version": QUARTO_PARSER_VERSION,
        "source_ref": source_ref,
        "state": state,
        "coverage_status": "partially_covered",
        "emitted_record_refs": [],
        "syntax_issues": syntax_issues,
        "opaque_constructs": [
            {
                "kind": "quarto_render_and_runtime_semantics",
                "reason": (
                    "Source inventory does not establish Quarto rendering, executable-cell runs, "
                    "extensions, filters, environments, artifacts, or scientific meaning."
                ),
                "source_ref": source_ref,
            }
        ],
        "parser_disagreement": None,
        "started_at": _TIMESTAMP,
        "completed_at": _TIMESTAMP,
        "extensions": extensions,
        "provenance": {
            "actor": {"actor_kind": "parser", "actor_id": QUARTO_PARSER_ID},
            "method": "static_non_rendering_quarto_source_inventory",
            "created_at": _TIMESTAMP,
            "tool": "sc-referee",
            "tool_version": __version__,
        },
    }


def _failure(run_id: str, source_ref: dict[str, Any], state: str, reason: str) -> dict[str, Any]:
    result = _result(
        run_id,
        source_ref,
        state,
        [_issue(reason, source_ref)] if state == "error" else [],
        {
            "x-quarto-profile": "bounded-quarto-source-cell-inventory-v2",
            "x-quarto-front-matter-span": None,
            "x-quarto-prose-spans": [],
            "x-quarto-cells": [],
            "x-quarto-cell-count": 0,
            "x-quarto-executes-project-code": False,
        },
    )
    result["coverage_status"] = "not_covered"
    result["opaque_constructs"] = [
        {"kind": "quarto_parser_boundary", "reason": reason, "source_ref": source_ref}
    ]
    return result


def _issue(message: str, source_ref: dict[str, Any]) -> dict[str, Any]:
    return {"message": message, "source_ref": source_ref, "recoverable": True}


def _line_ref(source_ref: dict[str, Any], line: int) -> dict[str, Any]:
    return {
        **source_ref,
        "locator": f"{source_ref['path']}:{line}",
        "start_line": line,
        "end_line": line,
    }


def _logical_path(path: Path, source_path: str | None) -> str:
    value = source_path or path.name
    candidate = PurePosixPath(value)
    if not value or candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError("source_path must be a safe repository-relative POSIX path")
    return candidate.as_posix()


def extract_quarto_code_cells(path: Path, parser_result: dict[str, Any]) -> list[dict[str, Any]]:
    """Re-extract inventoried cell bytes and verify them against the parent record."""

    payload = path.read_bytes()
    expected_digest = parser_result.get("source_ref", {}).get("content_digest")
    if sha256_digest(payload) != expected_digest or len(payload) > MAX_QUARTO_BYTES:
        raise ValueError("Quarto bytes no longer match the inventoried parent")
    lines = payload.decode("utf-8").splitlines()
    if len(lines) > MAX_QUARTO_LINES:
        raise ValueError("Quarto lines exceed the inventoried parent ceiling")
    result: list[dict[str, Any]] = []
    for cell in parser_result.get("extensions", {}).get("x-quarto-cells", []):
        if not isinstance(cell, dict):
            continue
        start = cell.get("code_start_line")
        end = cell.get("code_end_line")
        if not isinstance(start, int) or not isinstance(end, int) or start < 1:
            raise ValueError("inventoried Quarto cell coordinates are invalid")
        if start > end:
            source_text = ""
        elif end > len(lines):
            raise ValueError("inventoried Quarto cell exceeds the source")
        else:
            source_text = "\n".join(lines[start - 1 : end]) + "\n"
        if sha256_digest(source_text.encode("utf-8")) != cell.get("code_digest"):
            raise ValueError("Quarto cell source no longer matches its inventory digest")
        result.append({"cell": cell, "source_text": source_text})
    return result
