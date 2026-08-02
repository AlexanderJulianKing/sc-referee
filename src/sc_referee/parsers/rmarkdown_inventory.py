from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from typing import Any

from sc_referee.core.ids import sha256_digest, stable_id
from sc_referee.version import SCHEMA_VERSION, __version__

_TIMESTAMP = "2026-07-29T20:00:00Z"
RMARKDOWN_PARSER_ID = "parser:rmarkdown-selected-report-inventory"
RMARKDOWN_PARSER_VERSION = "0.2.0"
MAX_RMARKDOWN_BYTES = 2_000_000
MAX_RMARKDOWN_LINES = 100_000
MAX_RMARKDOWN_CHUNKS = 1_000
_R_CHUNK_START = re.compile(r"^\s*```\{[rR](?P<header>[^}]*)\}\s*$")
_FENCE_END = re.compile(r"^\s*```\s*$")
_INLINE_R = re.compile(r"`r\s+[^`]+`")
_LABEL = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]*$")


def inspect_rmarkdown(path: Path, run_id: str, *, source_path: str | None = None) -> dict[str, Any]:
    """Inventory one R Markdown source without invoking R, knitr, or project code."""

    logical_path = _logical_path(path, source_path)
    try:
        payload = path.read_bytes()
    except OSError as error:
        return _error_result(
            run_id,
            {"source_kind": "file_span", "locator": logical_path, "path": logical_path},
            stable_id("parser-result", logical_path, type(error).__name__),
            f"R Markdown source could not be read: {type(error).__name__}",
        )
    digest = sha256_digest(payload)
    source_ref: dict[str, Any] = {
        "source_kind": "file_span",
        "locator": logical_path,
        "path": logical_path,
        "content_digest": digest,
    }
    if len(payload) > MAX_RMARKDOWN_BYTES:
        return _unsupported_result(
            run_id,
            source_ref,
            stable_id("parser-result", logical_path, digest),
            "R Markdown source exceeds the bounded byte ceiling.",
        )
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        return _error_result(
            run_id,
            source_ref,
            stable_id("parser-result", logical_path, digest),
            "R Markdown source is not valid UTF-8.",
        )

    lines = text.splitlines()
    if len(lines) > MAX_RMARKDOWN_LINES:
        return _unsupported_result(
            run_id,
            source_ref,
            stable_id("parser-result", logical_path, digest),
            "R Markdown source exceeds the bounded line ceiling.",
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
    raw_chunks, chunk_lines, syntax_issues = _chunks(lines, content_start, source_ref)
    if len(raw_chunks) > MAX_RMARKDOWN_CHUNKS:
        return _unsupported_result(
            run_id,
            source_ref,
            stable_id("parser-result", logical_path, digest),
            "R Markdown source exceeds the bounded chunk ceiling.",
        )
    chunks = _assign_chunk_labels(raw_chunks, syntax_issues)
    if front_issue is not None:
        syntax_issues.append(front_issue)
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
        and index not in chunk_lines
        and line.strip()
        and not line.lstrip().startswith("#")
    ]
    inline_r = [
        {
            "kind": "inline_r_expression",
            "reason": "Inline R is inventoried but not interpreted or executed.",
            "source_ref": {
                **source_ref,
                "locator": f"{logical_path}:{index}",
                "start_line": index,
                "end_line": index,
            },
        }
        for index, line in enumerate(lines, start=1)
        if index not in chunk_lines and _INLINE_R.search(line) is not None
    ]
    state = "partially_parsed" if syntax_issues else "parsed"
    return {
        "record_type": "parser_result",
        "schema_version": SCHEMA_VERSION,
        "parser_result_id": stable_id("parser-result", logical_path, digest),
        "audit_run_id": run_id,
        "parser_id": RMARKDOWN_PARSER_ID,
        "parser_version": RMARKDOWN_PARSER_VERSION,
        "source_ref": source_ref,
        "state": state,
        "coverage_status": "partially_covered",
        "emitted_record_refs": [],
        "syntax_issues": syntax_issues,
        "opaque_constructs": [
            *inline_r,
            {
                "kind": "rendered_rmarkdown_semantics",
                "reason": (
                    "Chunk inventory does not establish knitr execution, rendered output, "
                    "package behavior, or general R semantics."
                ),
                "source_ref": source_ref,
            },
        ],
        "parser_disagreement": None,
        "started_at": _TIMESTAMP,
        "completed_at": _TIMESTAMP,
        "extensions": {
            "x-rmarkdown-profile": "bounded-rmarkdown-source-chunk-inventory-v2",
            "x-rmarkdown-front-matter-span": front_matter,
            "x-rmarkdown-prose-spans": prose_spans,
            "x-rmarkdown-chunks": chunks,
            "x-rmarkdown-chunk-count": len(chunks),
            "x-rmarkdown-executes-project-code": False,
        },
        "provenance": {
            "actor": {"actor_kind": "parser", "actor_id": RMARKDOWN_PARSER_ID},
            "method": "static_rmarkdown_chunk_inventory",
            "created_at": _TIMESTAMP,
            "tool": "sc-referee",
            "tool_version": __version__,
        },
    }


def _front_matter(
    lines: list[str], source_ref: dict[str, Any]
) -> tuple[dict[str, int] | None, int, dict[str, Any] | None]:
    if not lines or lines[0].strip() != "---":
        return None, 1, None
    for index, line in enumerate(lines[1:], start=2):
        if line.strip() in {"---", "..."}:
            return {"start_line": 1, "end_line": index}, index + 1, None
    issue_ref = {**source_ref, "locator": f"{source_ref['path']}:1", "start_line": 1, "end_line": 1}
    return (
        None,
        1,
        {
            "message": "R Markdown YAML front matter is not closed.",
            "source_ref": issue_ref,
            "recoverable": True,
        },
    )


def _chunks(
    lines: list[str], content_start: int, source_ref: dict[str, Any]
) -> tuple[list[dict[str, Any]], set[int], list[dict[str, Any]]]:
    chunks: list[dict[str, Any]] = []
    chunk_lines: set[int] = set()
    issues: list[dict[str, Any]] = []
    index = max(0, content_start - 1)
    while index < len(lines):
        match = _R_CHUNK_START.fullmatch(lines[index])
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
                {
                    "message": "R Markdown R code chunk is not closed.",
                    "source_ref": {
                        **source_ref,
                        "locator": f"{source_ref['path']}:{fence_start}",
                        "start_line": fence_start,
                        "end_line": fence_start,
                    },
                    "recoverable": True,
                }
            )
            chunk_lines.update(range(fence_start, len(lines) + 1))
            break
        fence_end = end_index + 1
        chunk_lines.update(range(fence_start, fence_end + 1))
        declared_label, options = _chunk_header(match.group("header"))
        code_text = "\n".join(lines[index + 1 : end_index])
        if index + 1 < end_index:
            code_text += "\n"
        if declared_label is not None and _LABEL.fullmatch(declared_label) is None:
            issues.append(
                {
                    "message": "R Markdown chunk label is invalid.",
                    "source_ref": {
                        **source_ref,
                        "locator": f"{source_ref['path']}:{fence_start}",
                        "start_line": fence_start,
                        "end_line": fence_start,
                    },
                    "recoverable": True,
                }
            )
            declared_label = None
        chunks.append(
            {
                "chunk_index": len(chunks),
                "declared_label": declared_label,
                "options": options,
                "evaluation_state": _evaluation_state(options),
                "fence_start_line": fence_start,
                "code_start_line": fence_start + 1,
                "code_end_line": max(fence_start, fence_end - 1),
                "fence_end_line": fence_end,
                "code_digest": sha256_digest(code_text.encode("utf-8")),
                "_source_ref": source_ref,
            }
        )
        index = end_index + 1
    return chunks, chunk_lines, issues


def _assign_chunk_labels(
    raw_chunks: list[dict[str, Any]], syntax_issues: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    declared = [str(item["declared_label"]) for item in raw_chunks if item["declared_label"]]
    duplicates = {value for value in declared if declared.count(value) > 1}
    unavailable = set(declared)
    assigned: set[str] = set()
    chunks: list[dict[str, Any]] = []
    for item in raw_chunks:
        source_ref = item.pop("_source_ref")
        declared_label = item.pop("declared_label")
        if isinstance(declared_label, str) and declared_label not in duplicates:
            label = declared_label
            identity_kind = "declared_unique"
        else:
            label = _synthetic_label(int(item["chunk_index"]), unavailable | assigned)
            identity_kind = "synthetic_index"
            if declared_label in duplicates:
                syntax_issues.append(
                    {
                        "message": "R Markdown chunk label is duplicated.",
                        "source_ref": {
                            **source_ref,
                            "locator": f"{source_ref['path']}:{item['fence_start_line']}",
                            "start_line": item["fence_start_line"],
                            "end_line": item["fence_start_line"],
                        },
                        "recoverable": True,
                    }
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
        chunks.append(item)
    return chunks


def _chunk_header(header: str) -> tuple[str | None, list[str]]:
    values = [item.strip() for item in header.strip().lstrip(",").split(",") if item.strip()]
    if not values:
        return None, []
    first = values[0]
    if "=" in first:
        return None, values
    return first, values[1:]


def _evaluation_state(options: list[str]) -> str:
    normalized = {item.replace(" ", "").lower() for item in options}
    if "eval=false" in normalized or "eval=f" in normalized:
        return "disabled_declared"
    if "eval=true" in normalized or "eval=t" in normalized:
        return "enabled_declared"
    return "unspecified"


def _synthetic_label(index: int, unavailable: set[str]) -> str:
    candidate = f"chunk-{index}"
    suffix = 2
    while candidate in unavailable:
        candidate = f"chunk-{index}-synthetic-{suffix}"
        suffix += 1
    return candidate


def _logical_path(path: Path, source_path: str | None) -> str:
    value = source_path or path.name
    candidate = PurePosixPath(value)
    if not value or candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError("source_path must be a safe repository-relative POSIX path")
    return candidate.as_posix()


def _error_result(
    run_id: str,
    source_ref: dict[str, Any],
    result_id: str,
    message: str,
) -> dict[str, Any]:
    return {
        "record_type": "parser_result",
        "schema_version": SCHEMA_VERSION,
        "parser_result_id": result_id,
        "audit_run_id": run_id,
        "parser_id": RMARKDOWN_PARSER_ID,
        "parser_version": RMARKDOWN_PARSER_VERSION,
        "source_ref": source_ref,
        "state": "error",
        "coverage_status": "not_covered",
        "emitted_record_refs": [],
        "syntax_issues": [{"message": message, "source_ref": source_ref, "recoverable": True}],
        "opaque_constructs": [],
        "parser_disagreement": None,
        "started_at": _TIMESTAMP,
        "completed_at": _TIMESTAMP,
        "extensions": {
            "x-rmarkdown-profile": "bounded-rmarkdown-source-chunk-inventory-v2",
            "x-rmarkdown-front-matter-span": None,
            "x-rmarkdown-prose-spans": [],
            "x-rmarkdown-chunks": [],
            "x-rmarkdown-chunk-count": 0,
            "x-rmarkdown-executes-project-code": False,
        },
        "provenance": {
            "actor": {"actor_kind": "parser", "actor_id": RMARKDOWN_PARSER_ID},
            "method": "static_rmarkdown_chunk_inventory",
            "created_at": _TIMESTAMP,
            "tool": "sc-referee",
            "tool_version": __version__,
        },
    }


def _unsupported_result(
    run_id: str, source_ref: dict[str, Any], result_id: str, reason: str
) -> dict[str, Any]:
    result = _error_result(run_id, source_ref, result_id, reason)
    result["state"] = "unsupported"
    result["coverage_status"] = "not_covered"
    result["syntax_issues"] = []
    result["opaque_constructs"] = [
        {"kind": "rmarkdown_inventory_ceiling", "reason": reason, "source_ref": source_ref}
    ]
    return result


def extract_rmarkdown_code_chunks(
    path: Path, parser_result: dict[str, Any]
) -> list[dict[str, Any]]:
    """Re-extract inventoried R chunk bytes and verify them against the parent record."""

    payload = path.read_bytes()
    expected_digest = parser_result.get("source_ref", {}).get("content_digest")
    if sha256_digest(payload) != expected_digest or len(payload) > MAX_RMARKDOWN_BYTES:
        raise ValueError("R Markdown bytes no longer match the inventoried parent")
    lines = payload.decode("utf-8").splitlines()
    if len(lines) > MAX_RMARKDOWN_LINES:
        raise ValueError("R Markdown lines exceed the inventoried parent ceiling")
    chunks = parser_result.get("extensions", {}).get("x-rmarkdown-chunks", [])
    if not isinstance(chunks, list) or len(chunks) > MAX_RMARKDOWN_CHUNKS:
        raise ValueError("R Markdown chunks exceed the inventoried parent ceiling")
    result: list[dict[str, Any]] = []
    for chunk in chunks:
        if not isinstance(chunk, dict):
            raise ValueError("inventoried R Markdown chunk is invalid")
        start = chunk.get("code_start_line")
        end = chunk.get("code_end_line")
        if not isinstance(start, int) or not isinstance(end, int) or start < 1:
            raise ValueError("inventoried R Markdown chunk coordinates are invalid")
        if start > end:
            source_text = ""
        elif end > len(lines):
            raise ValueError("inventoried R Markdown chunk exceeds the source")
        else:
            source_text = "\n".join(lines[start - 1 : end]) + "\n"
        if sha256_digest(source_text.encode("utf-8")) != chunk.get("code_digest"):
            raise ValueError("R Markdown chunk source no longer matches its inventory digest")
        result.append({"chunk": chunk, "source_text": source_text})
    return result


__all__ = [
    "MAX_RMARKDOWN_BYTES",
    "MAX_RMARKDOWN_CHUNKS",
    "MAX_RMARKDOWN_LINES",
    "RMARKDOWN_PARSER_ID",
    "RMARKDOWN_PARSER_VERSION",
    "extract_rmarkdown_code_chunks",
    "inspect_rmarkdown",
]
