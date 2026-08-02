from __future__ import annotations

import json
from pathlib import Path

import pytest

import sc_referee.parsers.cell_language_bridge as cell_bridge
from sc_referee.controller import replay, run_audit
from sc_referee.parsers.cell_language_bridge import inspect_embedded_cell_sources
from sc_referee.parsers.jupyter_inventory import inspect_jupyter
from sc_referee.parsers.quarto_inventory import inspect_quarto
from sc_referee.records.schema_registry import LocalSchemaRegistry


def _write_notebook(
    path: Path,
    cells: list[dict[str, object]],
    *,
    metadata: dict[str, object],
) -> None:
    path.write_text(
        json.dumps(
            {
                "cells": cells,
                "metadata": metadata,
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        ),
        encoding="utf-8",
    )


def test_python_notebook_cells_reuse_static_parser_with_exact_cell_refs(
    schema_root: Path, tmp_path: Path
) -> None:
    marker = tmp_path / "must-not-exist"
    notebook = tmp_path / "analysis.ipynb"
    cells = [
        {
            "cell_type": "code",
            "id": cell_id,
            "metadata": {},
            "source": (
                "selected = [row for row in rows if row['group'] == 'treated']\n"
                f"open({str(marker)!r}, 'w').write('executed')\n"
            ),
            "execution_count": None,
            "outputs": [],
        }
        for cell_id in ("first", "second")
    ]
    _write_notebook(
        notebook,
        cells,
        metadata={
            "language_info": {"name": "Python"},
            "kernelspec": {"language": "python"},
        },
    )
    parent = inspect_jupyter(notebook, "audit:notebook", source_path="analysis.ipynb")

    children = inspect_embedded_cell_sources(notebook, parent, "audit:notebook")

    registry = LocalSchemaRegistry(schema_root)
    registry.validate(parent)
    for child in children:
        registry.validate(child)
    assert len(children) == 2
    assert len({item["parser_result_id"] for item in children}) == 2
    assert parent["extensions"]["x-cell-language-bridge"] == {
        "profile": "bounded-container-cell-static-language-bridge-v2",
        "bridge_version": "0.2.0",
        "state": "bridged",
        "eligible_cell_count": 2,
        "emitted_parser_result_count": 2,
        "unsupported_languages": [],
        "supported_languages": ["python", "r"],
        "cell_ceiling": 200,
        "executes_project_code": False,
    }
    assert {item["source_ref"]["cell_id"] for item in children} == {"first", "second"}
    assert all(item["source_ref"]["source_kind"] == "notebook_cell" for item in children)
    assert all(item["source_ref"]["path"] == "analysis.ipynb" for item in children)
    assert all(
        item["extensions"]["x-virtual-source"]["executes_project_code"] is False
        for item in children
    )
    operations = [
        operation for child in children for operation in child["extensions"]["x-operations"]
    ]
    filters = [item for item in operations if item["kind"] == "filter"]
    assert len(filters) == 2
    assert len({item["operation_id"] for item in filters}) == 2
    assert all(item["source_refs"][0]["source_kind"] == "notebook_cell" for item in filters)
    assert not marker.exists()


def test_conflicting_notebook_language_declarations_abstain_from_cell_parsing(
    tmp_path: Path,
) -> None:
    notebook = tmp_path / "conflict.ipynb"
    _write_notebook(
        notebook,
        [
            {
                "cell_type": "code",
                "id": "code",
                "metadata": {},
                "source": "value = 1\n",
                "execution_count": None,
                "outputs": [],
            }
        ],
        metadata={
            "language_info": {"name": "python"},
            "kernelspec": {"language": "R"},
        },
    )
    parent = inspect_jupyter(notebook, "audit:conflict", source_path="conflict.ipynb")

    children = inspect_embedded_cell_sources(notebook, parent, "audit:conflict")

    assert children == []
    assert parent["extensions"]["x-notebook-language-declaration"]["state"] == "ambiguous"
    assert parent["extensions"]["x-cell-language-bridge"]["state"] == "not_applicable"
    assert any(
        item["kind"] == "notebook_cell_language_boundary" for item in parent["opaque_constructs"]
    )


def test_quarto_python_and_r_cells_reuse_static_parsers_without_execution(
    schema_root: Path, tmp_path: Path
) -> None:
    marker = tmp_path / "must-not-exist"
    source = tmp_path / "analysis.qmd"
    source.write_text(
        "# Analysis\n\n"
        "```{python}\n"
        "#| label: python-cell\n"
        "selected = [row for row in rows if row['group'] == 'treated']\n"
        f"open({str(marker)!r}, 'w').write('executed')\n"
        "```\n\n"
        "```{r}\n"
        "#| label: r-cell\n"
        "fit <- edgeR::glmQLFit(y, design = design)\n"
        f"system('touch {marker.as_posix()}')\n"
        "```\n\n"
        "```{julia}\n"
        "value = 1\n"
        "```\n",
        encoding="utf-8",
    )
    parent = inspect_quarto(source, "audit:quarto", source_path="analysis.qmd")

    children = inspect_embedded_cell_sources(source, parent, "audit:quarto")

    registry = LocalSchemaRegistry(schema_root)
    registry.validate(parent)
    for child in children:
        registry.validate(child)
    assert [item["parser_id"] for item in children] == [
        "parser:python-ast-tokenize",
        "parser:r-tree-sitter-inventory",
        "parser:r-base-parse-data",
    ]
    python = children[0]
    assert python["source_ref"]["source_kind"] == "document_chunk"
    assert python["source_ref"]["chunk_label"] == "python-cell"
    assert python["source_ref"]["start_line"] == 5
    tree_r = children[1]
    first_call = tree_r["extensions"]["x-r-calls"][0]
    assert first_call["terminal_name"] == "glmQLFit"
    assert first_call["source_ref"]["chunk_label"] == "r-cell"
    assert first_call["source_ref"]["start_line"] == 11
    assert parent["extensions"]["x-cell-language-bridge"]["unsupported_languages"] == ["julia"]
    assert any(
        item["kind"] == "unsupported_quarto_cell_engine" for item in parent["opaque_constructs"]
    )
    assert not marker.exists()


def test_cell_language_bridge_ceiling_fails_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    notebook = tmp_path / "bounded.ipynb"
    _write_notebook(
        notebook,
        [
            {
                "cell_type": "code",
                "id": "code",
                "metadata": {},
                "source": "value = 1\n",
                "execution_count": None,
                "outputs": [],
            }
        ],
        metadata={"language_info": {"name": "python"}},
    )
    parent = inspect_jupyter(notebook, "audit:bounded", source_path="bounded.ipynb")
    monkeypatch.setattr(cell_bridge, "MAX_BRIDGED_CODE_CELLS", 0)

    assert inspect_embedded_cell_sources(notebook, parent, "audit:bounded") == []
    assert parent["extensions"]["x-cell-language-bridge"]["state"] == "unsupported"
    assert any(
        item["kind"] == "cell_language_bridge_ceiling" for item in parent["opaque_constructs"]
    )


def test_identical_notebook_cells_promote_and_cache_under_distinct_scopes(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "notebook-project"
    repository.mkdir()
    notebook = repository / "analysis.ipynb"
    _write_notebook(
        notebook,
        [
            {
                "cell_type": "code",
                "id": cell_id,
                "metadata": {},
                "source": "selected = [row for row in rows if row['group'] == 'treated']\n",
                "execution_count": None,
                "outputs": [],
            }
            for cell_id in ("first", "second")
        ],
        metadata={"language_info": {"name": "python"}},
    )

    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first = run_audit(repository, first_root, schema_root, report="analysis.ipynb")
    second = run_audit(repository, second_root, schema_root, report="analysis.ipynb")

    filters = [item for item in first["operations"] if item["kind"] == "filter"]
    assert len(filters) == 2
    assert len({item["operation_id"] for item in filters}) == 2
    assert {item["source_refs"][0]["cell_id"] for item in filters} == {"first", "second"}
    first_lock = json.loads((first_root / "semantic.lock.json").read_text(encoding="utf-8"))
    second_lock = json.loads((second_root / "semantic.lock.json").read_text(encoding="utf-8"))
    first_static = [
        key
        for key in first_lock["cache_summary"]["descendants"]["miss_keys"]
        if key.startswith("static_graph:")
    ]
    second_static = [
        key
        for key in second_lock["cache_summary"]["descendants"]["hit_keys"]
        if key.startswith("static_graph:")
    ]
    assert len(first_static) == 2
    assert len(set(first_static)) == 2
    assert second_static == first_static
    replayed = replay(first_root / "semantic.lock.json", tmp_path / "replay", schema_root)
    assert replayed["parser_results"] == first["parser_results"]
    assert replayed["operations"] == first["operations"]
    assert second["findings"] == []
