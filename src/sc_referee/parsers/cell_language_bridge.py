from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sc_referee.core.ids import canonical_json, sha256_digest, stable_id
from sc_referee.parsers.jupyter_inventory import (
    JUPYTER_PARSER_ID,
    extract_jupyter_code_cells,
)
from sc_referee.parsers.python_ast import inspect_python_source
from sc_referee.parsers.quarto_inventory import (
    QUARTO_PARSER_ID,
    extract_quarto_code_cells,
)
from sc_referee.parsers.r_dual import inspect_r_source
from sc_referee.parsers.rmarkdown_inventory import (
    RMARKDOWN_PARSER_ID,
    extract_rmarkdown_code_chunks,
)

CELL_LANGUAGE_BRIDGE_VERSION = "0.2.0"
CELL_LANGUAGE_BRIDGE_PROFILE = "bounded-container-cell-static-language-bridge-v2"
SUPPORTED_CELL_LANGUAGE_BRIDGE_IDENTITIES = frozenset(
    {
        ("bounded-container-cell-static-language-bridge-v1", "0.1.0"),
        (CELL_LANGUAGE_BRIDGE_PROFILE, CELL_LANGUAGE_BRIDGE_VERSION),
    }
)
MAX_BRIDGED_CODE_CELLS = 200
_SUPPORTED_LANGUAGES = frozenset({"python", "r"})
_BRIDGE_OPAQUE_KINDS = frozenset(
    {
        "cell_language_bridge_ceiling",
        "cell_language_bridge_extraction_failure",
        "cell_language_bridge_scope",
        "unsupported_quarto_cell_engine",
    }
)


@dataclass(frozen=True)
class VerifiedCellSource:
    """Re-extracted immutable cell bytes and their container-bound public identity."""

    content: bytes
    content_digest: str
    source_ref_payload: bytes
    language: str
    line_offset: int

    @property
    def source_ref(self) -> dict[str, Any]:
        value = json.loads(self.source_ref_payload)
        assert isinstance(value, dict)
        return value


def inspect_embedded_cell_sources(
    container_path: Path,
    parent_result: dict[str, Any],
    run_id: str,
) -> list[dict[str, Any]]:
    """Parse recognized cell bytes statically while preserving their container locations."""

    parser_id = parent_result.get("parser_id")
    parent_result["opaque_constructs"] = [
        item
        for item in parent_result.get("opaque_constructs", [])
        if isinstance(item, dict) and item.get("kind") not in _BRIDGE_OPAQUE_KINDS
    ]
    try:
        if parser_id == JUPYTER_PARSER_ID:
            cells = _jupyter_cells(container_path, parent_result)
        elif parser_id == QUARTO_PARSER_ID:
            cells = _quarto_cells(container_path, parent_result)
        elif parser_id == RMARKDOWN_PARSER_ID:
            cells = _rmarkdown_cells(container_path, parent_result)
        else:
            return []
    except (OSError, UnicodeError, ValueError) as error:
        _append_parent_opaque(
            parent_result,
            "cell_language_bridge_extraction_failure",
            f"Cell source could not be reverified: {type(error).__name__}.",
        )
        _set_bridge_summary(parent_result, "unsupported", 0, 0, [])
        return []

    supported = [item for item in cells if item["language"] in _SUPPORTED_LANGUAGES]
    unsupported = [item for item in cells if item["language"] not in _SUPPORTED_LANGUAGES]
    for item in unsupported:
        if parser_id == QUARTO_PARSER_ID:
            _append_parent_opaque(
                parent_result,
                "unsupported_quarto_cell_engine",
                f"Quarto cell engine {item['language']!r} has no static language bridge.",
                item["cell_ref"],
            )
    if len(supported) > MAX_BRIDGED_CODE_CELLS:
        _append_parent_opaque(
            parent_result,
            "cell_language_bridge_ceiling",
            (
                f"Recognized code-cell count exceeds the {MAX_BRIDGED_CODE_CELLS}-cell "
                "static bridge ceiling."
            ),
        )
        _set_bridge_summary(
            parent_result,
            "unsupported",
            len(supported),
            0,
            sorted({str(item["language"]) for item in unsupported}),
        )
        return []

    children: list[dict[str, Any]] = []
    for item in supported:
        raw_results = _inspect_cell(container_path, parent_result, item, run_id)
        children.extend(_bind_virtual_results(raw_results, parent_result, item))
    if children:
        _append_parent_opaque(
            parent_result,
            "cell_language_bridge_scope",
            (
                "Each recognized cell is parsed independently. Cross-cell state, execution "
                "order, runtime behavior, and code-to-output provenance remain unknown."
            ),
        )
    state = "bridged" if children else ("not_applicable" if not supported else "unsupported")
    _set_bridge_summary(
        parent_result,
        state,
        len(supported),
        len(children),
        sorted({str(item["language"]) for item in unsupported}),
    )
    return children


def parser_scope_key(parser_result: dict[str, Any]) -> str:
    """Return a collision-free cache scope for files and container-bound cells."""

    source_ref = parser_result.get("source_ref", {})
    path = str(source_ref.get("path", "unknown"))
    if source_ref.get("source_kind") == "file_span":
        return path
    return str(source_ref.get("locator") or parser_result.get("parser_result_id") or path)


def reextract_verified_cell_source(
    container_path: Path,
    parent_result: dict[str, Any],
    child_result: dict[str, Any],
) -> VerifiedCellSource:
    """Reproduce one bridge child's exact cell bytes or reject the linkage."""

    extension = child_result.get("extensions", {}).get("x-virtual-source")
    if not isinstance(extension, dict):
        raise ValueError("parser result has no virtual-source contract")
    bridge_identity = (extension.get("profile"), extension.get("bridge_version"))
    if (
        bridge_identity not in SUPPORTED_CELL_LANGUAGE_BRIDGE_IDENTITIES
        or extension.get("executes_project_code") is not False
        or extension.get("container_parser_result_id") != parent_result.get("parser_result_id")
    ):
        raise ValueError("virtual-source bridge identity is invalid")
    summary = parent_result.get("extensions", {}).get("x-cell-language-bridge")
    if not isinstance(summary, dict) or (
        (summary.get("profile"), summary.get("bridge_version")) != bridge_identity
        or summary.get("state") != "bridged"
        or summary.get("executes_project_code") is not False
        or summary.get("cell_ceiling") != MAX_BRIDGED_CODE_CELLS
    ):
        raise ValueError("parent bridge summary is unavailable or inconsistent")

    parser_id = parent_result.get("parser_id")
    if parser_id == JUPYTER_PARSER_ID:
        cells = _jupyter_cells(container_path, parent_result)
    elif parser_id == QUARTO_PARSER_ID:
        cells = _quarto_cells(container_path, parent_result)
    elif parser_id == RMARKDOWN_PARSER_ID:
        cells = _rmarkdown_cells(container_path, parent_result)
    else:
        raise ValueError("virtual-source parent parser is unsupported")
    supported = [item for item in cells if item["language"] in _SUPPORTED_LANGUAGES]
    if len(supported) > MAX_BRIDGED_CODE_CELLS or summary.get("eligible_cell_count") != len(
        supported
    ):
        raise ValueError("virtual-source parent exceeds or contradicts the bridge ceiling")

    declared_ref = extension.get("source_ref")
    language = extension.get("language")
    source_digest = extension.get("source_digest")
    if (
        not isinstance(declared_ref, dict)
        or language not in _SUPPORTED_LANGUAGES
        or not isinstance(source_digest, str)
    ):
        raise ValueError("virtual-source cell identity is incomplete")
    matches = [
        item
        for item in supported
        if item["language"] == language
        and item["source_digest"] == source_digest
        and canonical_json(item["cell_ref"]) == canonical_json(declared_ref)
    ]
    if len(matches) != 1:
        raise ValueError("virtual-source cell cannot be uniquely re-extracted")
    item = matches[0]
    content = str(item["source_text"]).encode("utf-8")
    if sha256_digest(content) != source_digest:
        raise ValueError("virtual-source inspected bytes have the wrong digest")

    expected_parsers = {
        "python": {"parser:python-ast-tokenize"},
        "r": {"parser:r-tree-sitter-inventory", "parser:r-base-parse-data"},
    }
    if child_result.get("parser_id") not in expected_parsers[str(language)]:
        raise ValueError("virtual-source language and parser identities disagree")
    child_ref = child_result.get("source_ref")
    identity_fields = ["source_kind", "path", "content_digest"]
    identity_fields.extend(
        ["cell_id", "selector"]
        if declared_ref.get("source_kind") == "notebook_cell"
        else ["chunk_label"]
    )
    if not isinstance(child_ref, dict) or any(
        child_ref.get(field) != declared_ref.get(field) for field in identity_fields
    ):
        raise ValueError("virtual-source child location disagrees with its bridge declaration")
    return VerifiedCellSource(
        content=content,
        content_digest=source_digest,
        source_ref_payload=canonical_json(declared_ref).encode("utf-8"),
        language=str(language),
        line_offset=int(item["line_offset"]),
    )


def _jupyter_cells(container_path: Path, parent_result: dict[str, Any]) -> list[dict[str, Any]]:
    declaration = parent_result.get("extensions", {}).get("x-notebook-language-declaration", {})
    language = declaration.get("language") if declaration.get("state") == "recognized" else None
    if language not in _SUPPORTED_LANGUAGES:
        return []
    result: list[dict[str, Any]] = []
    for extracted in extract_jupyter_code_cells(container_path, parent_result):
        cell = extracted["cell"]
        source_text = str(extracted["source_text"])
        line_count = max(1, len(source_text.splitlines()))
        cell_ref = deepcopy(cell["source_ref"])
        cell_ref.update(
            {
                "locator": f"{cell_ref['locator']}:source:1-{line_count}",
                "start_line": 1,
                "end_line": line_count,
            }
        )
        result.append(
            {
                "language": language,
                "identity": str(cell["cell_id"]),
                "source_text": source_text,
                "source_digest": str(cell["source_digest"]),
                "cell_ref": cell_ref,
                "line_offset": 0,
                "execution_declaration": {
                    "kind": "saved_execution_count",
                    "state": cell.get("execution_count_state"),
                    "value": cell.get("execution_count"),
                    "establishes_execution": False,
                },
            }
        )
    return result


def _quarto_cells(container_path: Path, parent_result: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for extracted in extract_quarto_code_cells(container_path, parent_result):
        cell = extracted["cell"]
        source_text = str(extracted["source_text"])
        language = str(cell.get("engine", "")).strip().casefold()
        start = int(cell["code_start_line"])
        end = max(start, int(cell["code_end_line"]))
        cell_ref = deepcopy(cell["source_ref"])
        cell_ref.update(
            {
                "locator": f"{cell_ref['locator']}:code:{start}-{end}",
                "start_line": start,
                "end_line": end,
            }
        )
        result.append(
            {
                "language": language,
                "identity": str(cell["label"]),
                "source_text": source_text,
                "source_digest": str(cell["code_digest"]),
                "cell_ref": cell_ref,
                "line_offset": start - 1,
                "execution_declaration": {
                    "kind": "quarto_eval_option",
                    "state": cell.get("evaluation_state"),
                    "establishes_execution": False,
                },
            }
        )
    return result


def _rmarkdown_cells(container_path: Path, parent_result: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for extracted in extract_rmarkdown_code_chunks(container_path, parent_result):
        chunk = extracted["chunk"]
        source_text = str(extracted["source_text"])
        start = int(chunk["code_start_line"])
        end = max(start, int(chunk["code_end_line"]))
        cell_ref = deepcopy(chunk["source_ref"])
        cell_ref.update(
            {
                "locator": f"{cell_ref['locator']}:code:{start}-{end}",
                "start_line": start,
                "end_line": end,
            }
        )
        result.append(
            {
                "language": "r",
                "identity": str(chunk["label"]),
                "source_text": source_text,
                "source_digest": str(chunk["code_digest"]),
                "cell_ref": cell_ref,
                "line_offset": start - 1,
                "execution_declaration": {
                    "kind": "rmarkdown_eval_option",
                    "state": chunk.get("evaluation_state"),
                    "establishes_execution": False,
                },
            }
        )
    return result


def _inspect_cell(
    container_path: Path,
    parent_result: dict[str, Any],
    item: dict[str, Any],
    run_id: str,
) -> tuple[dict[str, Any], ...]:
    parent_path = str(parent_result["source_ref"]["path"])
    virtual_path = f"{parent_path}#cell={item['identity']}"
    payload = str(item["source_text"]).encode("utf-8")
    if item["language"] == "python":
        return (
            inspect_python_source(
                payload,
                container_path,
                run_id,
                source_path=virtual_path,
            ),
        )
    return inspect_r_source(
        payload,
        container_path,
        run_id,
        source_path=virtual_path,
    )


def _bind_virtual_results(
    results: tuple[dict[str, Any], ...],
    parent_result: dict[str, Any],
    item: dict[str, Any],
) -> list[dict[str, Any]]:
    bound: list[dict[str, Any]] = []
    for raw in results:
        result = _replace_source_refs(
            raw,
            item["cell_ref"],
            int(item["line_offset"]),
        )
        assert isinstance(result, dict)
        result["parser_result_id"] = stable_id(
            "parser-result",
            str(result["parser_id"]),
            str(parent_result["source_ref"]["path"]),
            str(parent_result["source_ref"]["content_digest"]),
            str(item["cell_ref"]["locator"]),
            str(item["source_digest"]),
        )
        result["extensions"]["x-virtual-source"] = {
            "profile": CELL_LANGUAGE_BRIDGE_PROFILE,
            "bridge_version": CELL_LANGUAGE_BRIDGE_VERSION,
            "container_parser_result_id": parent_result["parser_result_id"],
            "language": item["language"],
            "source_digest": item["source_digest"],
            "source_ref": deepcopy(item["cell_ref"]),
            "execution_declaration": deepcopy(item["execution_declaration"]),
            "executes_project_code": False,
        }
        bound.append(result)
    ids = {str(result["parser_id"]): str(result["parser_result_id"]) for result in bound}
    for result in bound:
        comparison = result.get("extensions", {}).get("x-r-cross-parser-comparison")
        if isinstance(comparison, dict):
            counterpart = (
                "parser:r-base-parse-data"
                if result["parser_id"] == "parser:r-tree-sitter-inventory"
                else "parser:r-tree-sitter-inventory"
            )
            if counterpart in ids:
                comparison["counterpart_parser_result_id"] = ids[counterpart]
    return bound


def _replace_source_refs(value: Any, base_ref: dict[str, Any], line_offset: int) -> Any:
    if isinstance(value, dict):
        if isinstance(value.get("source_kind"), str) and isinstance(value.get("locator"), str):
            result = deepcopy(base_ref)
            start = value.get("start_line")
            end = value.get("end_line")
            if isinstance(start, int) and isinstance(end, int):
                absolute_start = start + line_offset
                absolute_end = end + line_offset
                result["start_line"] = absolute_start
                result["end_line"] = absolute_end
                result["locator"] = f"{base_ref['locator']}:span:{absolute_start}-{absolute_end}"
                for key in ("start_column", "end_column", "quoted_text"):
                    if key in value:
                        result[key] = value[key]
            return result
        return {
            key: _replace_source_refs(item, base_ref, line_offset) for key, item in value.items()
        }
    if isinstance(value, list):
        return [_replace_source_refs(item, base_ref, line_offset) for item in value]
    return value


def _append_parent_opaque(
    parent_result: dict[str, Any],
    kind: str,
    reason: str,
    source_ref: dict[str, Any] | None = None,
) -> None:
    parent_result.setdefault("opaque_constructs", []).append(
        {
            "kind": kind,
            "reason": reason,
            "source_ref": deepcopy(source_ref or parent_result["source_ref"]),
        }
    )


def _set_bridge_summary(
    parent_result: dict[str, Any],
    state: str,
    eligible_cell_count: int,
    emitted_parser_result_count: int,
    unsupported_languages: list[str],
) -> None:
    parent_result.setdefault("extensions", {})["x-cell-language-bridge"] = {
        "profile": CELL_LANGUAGE_BRIDGE_PROFILE,
        "bridge_version": CELL_LANGUAGE_BRIDGE_VERSION,
        "state": state,
        "eligible_cell_count": eligible_cell_count,
        "emitted_parser_result_count": emitted_parser_result_count,
        "unsupported_languages": unsupported_languages,
        "supported_languages": sorted(_SUPPORTED_LANGUAGES),
        "cell_ceiling": MAX_BRIDGED_CODE_CELLS,
        "executes_project_code": False,
    }
