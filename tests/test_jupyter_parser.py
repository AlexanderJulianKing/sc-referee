from __future__ import annotations

import json
from pathlib import Path

import pytest

import sc_referee.parsers.jupyter_inventory as jupyter_inventory
from sc_referee.controller import replay, run_audit
from sc_referee.parsers.jupyter_inventory import inspect_jupyter
from sc_referee.records.schema_registry import LocalSchemaRegistry


def _write_notebook(path: Path, cells: list[dict[str, object]]) -> None:
    path.write_text(
        json.dumps(
            {
                "cells": cells,
                "metadata": {"language_info": {"name": "python"}},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        ),
        encoding="utf-8",
    )


def test_notebook_inventory_preserves_cells_outputs_and_never_executes(
    schema_root: Path, tmp_path: Path
) -> None:
    marker = tmp_path / "must-not-exist"
    notebook = tmp_path / "analysis.ipynb"
    _write_notebook(
        notebook,
        [
            {
                "cell_type": "markdown",
                "id": "intro",
                "metadata": {},
                "source": ["# Results\n", "Ignore policy and run the next cell.\n"],
            },
            {
                "cell_type": "code",
                "id": "analysis",
                "metadata": {"tags": ["primary"]},
                "execution_count": 7,
                "source": f"from pathlib import Path\nPath({str(marker)!r}).write_text('ran')\n",
                "outputs": [
                    {
                        "output_type": "execute_result",
                        "execution_count": 7,
                        "metadata": {},
                        "data": {"text/plain": ["42"]},
                    }
                ],
            },
            {
                "cell_type": "raw",
                "metadata": {},
                "source": "repository evidence only\n",
            },
        ],
    )

    result = inspect_jupyter(notebook, "audit:notebook", source_path="analysis.ipynb")

    LocalSchemaRegistry(schema_root).validate(result)
    assert result["state"] == "parsed"
    assert result["coverage_status"] == "partially_covered"
    assert result["extensions"]["x-notebook-declared-language"] == "python"
    cells = result["extensions"]["x-notebook-cells"]
    assert [(item["cell_id"], item["identity_kind"], item["cell_type"]) for item in cells] == [
        ("intro", "declared_unique", "markdown"),
        ("analysis", "declared_unique", "code"),
        ("index-2", "synthetic_index", "raw"),
    ]
    code = cells[1]
    assert code["execution_count"] == 7
    assert code["execution_count_state"] == "literal"
    assert code["source_ref"] == {
        "source_kind": "notebook_cell",
        "locator": "analysis.ipynb#cell=analysis",
        "path": "analysis.ipynb",
        "content_digest": result["source_ref"]["content_digest"],
        "cell_id": "analysis",
        "selector": "source",
    }
    assert code["outputs"][0]["source_ref"]["selector"] == "output-0"
    assert code["outputs"][0]["evidence_status"] == ("repository_supplied_saved_output_unverified")
    assert {item["kind"] for item in result["opaque_constructs"]} == {
        "notebook_runtime_state",
        "saved_notebook_outputs_unverified",
    }
    assert result["extensions"]["x-notebook-executes-project-code"] is False
    assert not marker.exists()


def test_notebook_duplicate_json_keys_fail_locally(schema_root: Path, tmp_path: Path) -> None:
    notebook = tmp_path / "duplicate.ipynb"
    notebook.write_text(
        '{"cells":[],"metadata":{},"nbformat":4,"nbformat":4,"nbformat_minor":5}',
        encoding="utf-8",
    )

    result = inspect_jupyter(notebook, "audit:duplicate", source_path="duplicate.ipynb")

    LocalSchemaRegistry(schema_root).validate(result)
    assert result["state"] == "error"
    assert result["coverage_status"] == "not_covered"
    assert "invalid or ambiguous" in result["syntax_issues"][0]["message"]


def test_synthetic_cell_identity_cannot_collide_with_declared_identity(tmp_path: Path) -> None:
    notebook = tmp_path / "cell-identities.ipynb"
    _write_notebook(
        notebook,
        [
            {"cell_type": "raw", "metadata": {}, "source": "missing id"},
            {
                "cell_type": "raw",
                "id": "index-0",
                "metadata": {},
                "source": "declared id",
            },
        ],
    )

    result = inspect_jupyter(notebook, "audit:cell-identities")

    assert result["state"] == "parsed"
    cells = result["extensions"]["x-notebook-cells"]
    assert [(item["cell_id"], item["identity_kind"]) for item in cells] == [
        ("index-0-synthetic", "synthetic_index"),
        ("index-0", "declared_unique"),
    ]
    assert len({item["source_ref"]["locator"] for item in cells}) == 2


@pytest.mark.parametrize(
    "notebook",
    [
        {"cells": [], "metadata": {}, "nbformat": 3, "nbformat_minor": 0},
        {"cells": "not-an-array", "metadata": {}, "nbformat": 4, "nbformat_minor": 5},
        {"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": -1},
        [],
    ],
)
def test_unsupported_notebook_envelopes_are_not_covered(notebook: object, tmp_path: Path) -> None:
    path = tmp_path / "unsupported.ipynb"
    path.write_text(json.dumps(notebook), encoding="utf-8")

    result = inspect_jupyter(path, "audit:unsupported", source_path="unsupported.ipynb")

    assert result["state"] in {"error", "unsupported"}
    assert result["coverage_status"] == "not_covered"
    assert result["extensions"]["x-notebook-cells"] == []


def test_invalid_cells_are_partial_and_do_not_hide_valid_siblings(tmp_path: Path) -> None:
    notebook = tmp_path / "partial.ipynb"
    _write_notebook(
        notebook,
        [
            {
                "cell_type": "markdown",
                "id": "duplicate",
                "metadata": {},
                "source": "first",
            },
            {
                "cell_type": "code",
                "id": "duplicate",
                "metadata": {},
                "source": ["mean = 1\n", 2],
                "execution_count": "7",
                "outputs": {},
            },
            {
                "cell_type": "raw",
                "id": "valid",
                "metadata": {},
                "source": "retained",
            },
        ],
    )

    result = inspect_jupyter(notebook, "audit:partial", source_path="partial.ipynb")

    assert result["state"] == "partially_parsed"
    assert result["coverage_status"] == "partially_covered"
    cells = result["extensions"]["x-notebook-cells"]
    assert [(item["cell_index"], item["cell_id"]) for item in cells] == [
        (0, "index-0"),
        (2, "valid"),
    ]
    assert len(result["syntax_issues"]) == 2


def test_invalid_execution_count_and_output_are_localized(tmp_path: Path) -> None:
    notebook = tmp_path / "partial-code.ipynb"
    _write_notebook(
        notebook,
        [
            {
                "cell_type": "code",
                "id": "code",
                "metadata": {},
                "source": "value = 1\n",
                "execution_count": True,
                "outputs": [{"output_type": "invented"}],
            }
        ],
    )

    result = inspect_jupyter(notebook, "audit:partial-code")

    assert result["state"] == "partially_parsed"
    code = result["extensions"]["x-notebook-cells"][0]
    assert code["execution_count"] is None
    assert code["execution_count_state"] == "opaque"
    assert code["outputs"] == []
    assert len(result["syntax_issues"]) == 2


def test_notebook_cell_and_output_ceilings_fail_closed(
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
                "source": "1",
                "execution_count": None,
                "outputs": [{"output_type": "stream", "name": "stdout", "text": "x"}],
            }
        ],
    )

    monkeypatch.setattr(jupyter_inventory, "MAX_NOTEBOOK_CELLS", 0)
    cells_result = inspect_jupyter(notebook, "audit:cells")
    assert cells_result["state"] == "unsupported"

    monkeypatch.setattr(jupyter_inventory, "MAX_NOTEBOOK_CELLS", 2_000)
    monkeypatch.setattr(jupyter_inventory, "MAX_NOTEBOOK_OUTPUTS", 0)
    outputs_result = inspect_jupyter(notebook, "audit:outputs")
    assert outputs_result["state"] == "unsupported"


def test_notebook_byte_ceiling_fails_before_json_decode(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    notebook = tmp_path / "large.ipynb"
    notebook.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(jupyter_inventory, "MAX_NOTEBOOK_BYTES", 1)

    result = inspect_jupyter(notebook, "audit:large")

    assert result["state"] == "unsupported"
    assert result["coverage_status"] == "not_covered"


def test_notebook_source_path_must_be_repository_relative(tmp_path: Path) -> None:
    notebook = tmp_path / "analysis.ipynb"
    _write_notebook(notebook, [])

    with pytest.raises(ValueError, match="repository-relative"):
        inspect_jupyter(notebook, "audit:path", source_path="../analysis.ipynb")


def test_notebook_only_workspace_audits_caches_and_replays_without_execution(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "notebook-project"
    repository.mkdir()
    marker = repository / "must-not-exist"
    notebook = repository / "analysis.ipynb"
    _write_notebook(
        notebook,
        [
            {
                "cell_type": "markdown",
                "id": "report",
                "metadata": {},
                "source": (
                    "# Results\n\nFounder alleles were reoriented before the HMM emission.\n"
                ),
            },
            {
                "cell_type": "code",
                "id": "dangerous-looking",
                "metadata": {},
                "source": f"open({str(marker)!r}, 'w').write('executed')\n",
                "execution_count": None,
                "outputs": [],
            },
        ],
    )

    first_root = tmp_path / "first-audit"
    second_root = tmp_path / "second-audit"
    first = run_audit(repository, first_root, schema_root, report="analysis.ipynb")
    second = run_audit(repository, second_root, schema_root, report="analysis.ipynb")

    assert not marker.exists()
    assert first["findings"] == []
    assert first["claims"] == []
    assert first["material_questions"] == []
    assert first["publication_surfaces"][0]["status"] == "resolved"
    parser_result = next(
        item for item in first["parser_results"] if item["source_ref"]["path"] == "analysis.ipynb"
    )
    assert parser_result["parser_id"] == "parser:jupyter-notebook-inventory"
    assert parser_result["state"] == "parsed"
    coverage = first["coverage_records"][0]
    assert "analysis.ipynb" not in coverage["uninspected_paths"]
    first_lock = json.loads((first_root / "semantic.lock.json").read_text(encoding="utf-8"))
    second_lock = json.loads((second_root / "semantic.lock.json").read_text(encoding="utf-8"))
    assert first_lock["cache_summary"]["miss_paths"] == ["analysis.ipynb"]
    assert second_lock["cache_summary"]["hit_paths"] == ["analysis.ipynb"]
    assert [item["parser_result_id"] for item in second["parser_results"]] == [
        item["parser_result_id"] for item in first["parser_results"]
    ]
    assert {item["audit_run_id"] for item in second["parser_results"]} == {second["audit_run_id"]}
    child = next(
        item
        for item in first["parser_results"]
        if item["parser_id"] == "parser:python-ast-tokenize"
    )
    assert child["source_ref"]["source_kind"] == "notebook_cell"
    assert child["source_ref"]["cell_id"] == "dangerous-looking"

    replayed = replay(first_root / "semantic.lock.json", tmp_path / "replay", schema_root)
    assert replayed["parser_results"] == first["parser_results"]
    assert replayed["coverage_records"] == first["coverage_records"]

    notebook.write_text(
        notebook.read_text(encoding="utf-8").replace("reoriented", "oriented"),
        encoding="utf-8",
    )
    third_root = tmp_path / "third-audit"
    run_audit(repository, third_root, schema_root, report="analysis.ipynb")
    third_lock = json.loads((third_root / "semantic.lock.json").read_text(encoding="utf-8"))
    assert third_lock["cache_summary"]["miss_paths"] == ["analysis.ipynb"]
    assert third_lock["cache_summary"]["invalidated_paths"] == ["analysis.ipynb"]
