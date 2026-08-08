from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from sc_referee.controller import replay, run_audit
from sc_referee.core.ids import sha256_digest
from sc_referee.scientific_checks import (
    FrozenSourceLocation,
    ScientificCheckContractError,
)
from sc_referee.scientific_checks.integration import build_frozen_inspection_context
from sc_referee.scientific_checks.profiles import default_scientific_check_registry

# The founder-orientation check became a single reported-text plane at check
# v2.0.0 (ADR-0069). Cell-level static-source evidence is exercised here by the
# LD-whitening check, whose Python static-source adapter still reads a cell.
STATIC_CHECK = "check:ld-covariance-whitening-before-robust-fit"
DIRECT_SOURCE = """from numpy.linalg import cholesky as factor_covariance
from numpy.linalg import solve as triangular_solve
from statsmodels.api import RLM as robust_fit
from statsmodels.robust.norms import TukeyBiweight as redescending_norm

factor = factor_covariance(ld_covariance)
y_white = triangular_solve(factor, outcome_innovations)
x_white = triangular_solve(factor, exposure_innovations)
fit = robust_fit(y_white, x_white, M=redescending_norm())
"""


def _write_notebook(path: Path, cells: list[tuple[str, str]]) -> None:
    path.write_text(
        json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "id": cell_id,
                        "metadata": {},
                        "source": source,
                        "execution_count": None,
                        "outputs": [],
                    }
                    for cell_id, source in cells
                ],
                "metadata": {
                    "language_info": {"name": "python"},
                    "kernelspec": {"language": "python"},
                },
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        ),
        encoding="utf-8",
    )


def _context(
    repository: Path,
    output: Path,
    bundle: dict[str, Any],
    *,
    parser_results: list[dict[str, Any]] | None = None,
):
    context = build_frozen_inspection_context(
        snapshot_root=output / "observed" / "snapshot" / "materialized",
        snapshot_digest=bundle["repository_snapshots"][0]["snapshot_digest"],
        file_records=bundle["file_records"],
        asset_identities=bundle["asset_identities"],
        parser_results=parser_results or bundle["parser_results"],
        operations=bundle["operations"],
        artifacts=bundle["artifacts"],
        publication_surface=bundle["publication_surfaces"][0],
        repository_snapshot=bundle["repository_snapshots"][0],
    )
    assert context is not None
    assert repository.is_dir()
    return context


def _static_source_observation(context):
    evaluation = default_scientific_check_registry().evaluate(context)
    module = next(item for item in evaluation.modules if item.check_id == STATIC_CHECK)
    observation = next(
        item
        for item in module.observations
        if item.evidence_plane == "static_source"
        and item.adapter_id.endswith("python-static-source-v1")
    )
    return module, observation


def test_notebook_cells_are_distinct_scientific_documents_but_remain_unscoped(
    tmp_path: Path, schema_root: Path
) -> None:
    marker = tmp_path / "must-not-exist"
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "report.md").write_text("A descriptive analysis summary.\n", encoding="utf-8")
    notebook = repository / "analysis.ipynb"
    _write_notebook(
        notebook,
        [
            ("whitening-model", DIRECT_SOURCE),
            ("inert-marker", f"open({str(marker)!r}, 'w').write('executed')\n"),
        ],
    )
    output = tmp_path / "audit"

    bundle = run_audit(repository, output, schema_root, report="report.md")
    context = _context(repository, output, bundle)
    cells = [
        item
        for item in context.documents
        if item.source_location is not None and item.source_location.source_kind == "notebook_cell"
    ]

    assert len(cells) == 2
    assert len({item.document_identity for item in cells}) == 2
    assert {item.path for item in cells} == {"analysis.ipynb"}
    assert {item.source_location.to_dict()["cell_id"] for item in cells} == {
        "whitening-model",
        "inert-marker",
    }
    module, observation = _static_source_observation(context)
    assert module.state == "unsupported"
    assert observation.applicability == "unsupported"
    assert observation.observed_operand is not None
    assert observation.scope_join_path == ()
    assert not any(
        item.get("extensions", {}).get("x-scientific-check-id") == STATIC_CHECK
        for item in bundle["material_questions"]
    )
    assert not marker.exists()

    span = observation.evidence_spans[0]
    document = next(item for item in cells if item.parser_result_ref == span.parser_result_ref)
    source_ref = document.evidence_source_ref(span)
    assert source_ref["source_kind"] == "notebook_cell"
    assert source_ref["cell_id"] == "whitening-model"
    assert source_ref["selector"] == "source"
    assert source_ref["content_digest"] == sha256_digest(notebook.read_bytes())
    assert "triangular_solve" in source_ref["quoted_text"]

    replayed = replay(output / "semantic.lock.json", tmp_path / "replay", schema_root)
    assert replayed["parser_results"] == bundle["parser_results"]
    assert replayed["material_questions"] == bundle["material_questions"]


def test_selected_quarto_cell_can_create_question_with_absolute_document_lines(
    tmp_path: Path, schema_root: Path
) -> None:
    marker = tmp_path / "must-not-exist"
    repository = tmp_path / "repository"
    repository.mkdir()
    quarto = repository / "analysis.qmd"
    quarto.write_text(
        "# Analysis\n\n"
        "This document contains one static model fragment.\n\n"
        "```{python}\n"
        "#| label: whitening-model\n"
        f"{DIRECT_SOURCE}"
        f"# open({str(marker)!r}, 'w').write('executed')\n"
        "```\n",
        encoding="utf-8",
    )
    output = tmp_path / "audit"

    bundle = run_audit(repository, output, schema_root, report="analysis.qmd")
    context = _context(repository, output, bundle)
    module, observation = _static_source_observation(context)

    assert module.state == "applicable"
    assert observation.applicability == "applicable"
    assert [item.relation for item in observation.scope_join_path] == [
        "contained_in_selected_source_artifact",
        "selected_by_publication_surface",
    ]
    span = observation.evidence_spans[0]
    document = next(
        item for item in context.documents if item.parser_result_ref == span.parser_result_ref
    )
    source_ref = document.evidence_source_ref(span)
    assert document.line_offset == 6
    assert source_ref["source_kind"] == "document_chunk"
    assert source_ref["chunk_label"] == "whitening-model"
    assert source_ref["start_line"] >= 7
    assert source_ref["content_digest"] == sha256_digest(quarto.read_bytes())
    assert "triangular_solve" in source_ref["quoted_text"]
    questions = [
        item
        for item in bundle["material_questions"]
        if item.get("extensions", {}).get("x-scientific-check-id") == STATIC_CHECK
    ]
    assertions = [
        item
        for item in bundle["semantic_assertions"]
        if item.get("extensions", {}).get("x-scientific-check-id") == STATIC_CHECK
    ]
    assert len(questions) == 1
    assert len(assertions) == 1
    assert assertions[0]["semantic_role"] == "observed"
    assert assertions[0]["finding_eligibility"] == "ineligible"
    assert assertions[0]["source_refs"][0]["source_kind"] == "document_chunk"
    assert assertions[0]["source_refs"][0]["chunk_label"] == "whitening-model"
    assert not marker.exists()
    assert bundle["findings"] == []


def test_selected_notebook_cell_can_create_question_without_claiming_execution(
    tmp_path: Path, schema_root: Path
) -> None:
    marker = tmp_path / "must-not-exist"
    repository = tmp_path / "repository"
    repository.mkdir()
    notebook = repository / "analysis.ipynb"
    _write_notebook(
        notebook,
        [
            ("whitening-model", DIRECT_SOURCE),
            ("inert-marker", f"open({str(marker)!r}, 'w').write('executed')\n"),
        ],
    )
    output = tmp_path / "audit"

    bundle = run_audit(repository, output, schema_root, report="analysis.ipynb")
    context = _context(repository, output, bundle)
    module, observation = _static_source_observation(context)

    assert module.state == "applicable"
    assert observation.applicability == "applicable"
    assert [item.relation for item in observation.scope_join_path] == [
        "contained_in_selected_source_artifact",
        "selected_by_publication_surface",
    ]
    questions = [
        item
        for item in bundle["material_questions"]
        if item.get("extensions", {}).get("x-scientific-check-id") == STATIC_CHECK
    ]
    assertions = [
        item
        for item in bundle["semantic_assertions"]
        if item.get("extensions", {}).get("x-scientific-check-id") == STATIC_CHECK
    ]
    assert len(questions) == 1
    assert assertions[0]["source_refs"][0]["source_kind"] == "notebook_cell"
    assert assertions[0]["source_refs"][0]["cell_id"] == "whitening-model"
    assert "execution" in observation.non_inferences
    assert bundle["findings"] == []
    assert not marker.exists()

    replayed = replay(output / "semantic.lock.json", tmp_path / "replay", schema_root)
    assert replayed["material_questions"] == bundle["material_questions"]
    assert replayed["semantic_assertions"] == bundle["semantic_assertions"]


def test_explicitly_disabled_selected_quarto_cell_remains_unscoped(
    tmp_path: Path, schema_root: Path
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "analysis.qmd").write_text(
        "# Analysis\n\n"
        "```{python}\n"
        "#| label: disabled-whitening-model\n"
        "#| eval: false\n"
        f"{DIRECT_SOURCE}"
        "```\n",
        encoding="utf-8",
    )
    output = tmp_path / "audit"

    bundle = run_audit(repository, output, schema_root, report="analysis.qmd")
    context = _context(repository, output, bundle)
    module, observation = _static_source_observation(context)

    assert module.state == "unsupported"
    assert observation.applicability == "unsupported"
    assert observation.observed_operand is not None
    assert observation.scope_join_path == ()
    assert not any(
        item.get("extensions", {}).get("x-scientific-check-id") == STATIC_CHECK
        for item in bundle["material_questions"]
    )
    assert bundle["findings"] == []


def test_tampered_virtual_source_metadata_is_not_exposed_to_scientific_adapters(
    tmp_path: Path, schema_root: Path
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    _write_notebook(repository / "analysis.ipynb", [("whitening-model", DIRECT_SOURCE)])
    output = tmp_path / "audit"
    bundle = run_audit(repository, output, schema_root, report="analysis.ipynb")
    tampered = copy.deepcopy(bundle["parser_results"])
    child = next(
        item
        for item in tampered
        if item.get("extensions", {}).get("x-virtual-source", {}).get("language") == "python"
    )
    child["extensions"]["x-virtual-source"]["source_digest"] = sha256_digest("tampered")

    context = _context(repository, output, bundle, parser_results=tampered)

    assert not any(
        item.source_location is not None and item.source_location.source_kind == "notebook_cell"
        for item in context.documents
    )
    module, observation = _static_source_observation(context)
    assert module.state == "unsupported"
    assert observation.applicability == "not_applicable"
    assert observation.observed_operand is None


def test_frozen_source_location_rejects_incomplete_cell_identity() -> None:
    source_ref = {
        "source_kind": "notebook_cell",
        "locator": "analysis.ipynb#cell=model",
        "path": "analysis.ipynb",
        "content_digest": sha256_digest("container"),
        "cell_id": "model",
    }

    with pytest.raises(ScientificCheckContractError, match="cell and selector"):
        FrozenSourceLocation.from_source_ref(source_ref)
