from __future__ import annotations

import json
from pathlib import Path

import pytest

import sc_referee.parsers.quarto_inventory as quarto_inventory
from sc_referee.controller import replay, run_audit
from sc_referee.parsers.quarto_inventory import inspect_quarto
from sc_referee.records.schema_registry import LocalSchemaRegistry


def test_quarto_inventory_preserves_multi_engine_cells_without_execution(
    schema_root: Path, tmp_path: Path
) -> None:
    marker = tmp_path / "must-not-exist"
    source = tmp_path / "analysis.qmd"
    source.write_text(
        "---\n"
        "title: Results\n"
        "format: html\n"
        "---\n"
        "# Result\n\n"
        "Descriptive prose.\n\n"
        "```{python}\n"
        "#| label: model-fit\n"
        "#| eval: false\n"
        f"open({str(marker)!r}, 'w').write('executed')\n"
        "```\n\n"
        "```{r}\n"
        "#| eval: true\n"
        "fit <- lm(y ~ x)\n"
        "```\n",
        encoding="utf-8",
    )

    result = inspect_quarto(source, "audit:quarto", source_path="reports/analysis.qmd")

    LocalSchemaRegistry(schema_root).validate(result)
    assert result["state"] == "parsed"
    assert result["coverage_status"] == "partially_covered"
    assert result["extensions"]["x-quarto-front-matter-span"] == {
        "start_line": 1,
        "end_line": 4,
    }
    assert result["extensions"]["x-quarto-prose-spans"][0]["text"] == "Descriptive prose."
    cells = result["extensions"]["x-quarto-cells"]
    assert [(item["engine"], item["label"], item["identity_kind"]) for item in cells] == [
        ("python", "model-fit", "declared_unique"),
        ("r", "cell-1", "synthetic_index"),
    ]
    assert [item["evaluation_state"] for item in cells] == [
        "disabled_declared",
        "enabled_declared",
    ]
    assert cells[0]["source_ref"] == {
        "source_kind": "document_chunk",
        "locator": "reports/analysis.qmd#cell=model-fit",
        "path": "reports/analysis.qmd",
        "content_digest": result["source_ref"]["content_digest"],
        "chunk_label": "model-fit",
        "start_line": 9,
        "end_line": 13,
    }
    assert result["extensions"]["x-quarto-executes-project-code"] is False
    assert not marker.exists()


@pytest.mark.parametrize(
    ("content", "state", "message"),
    [
        (b"\xff\xfe", "error", "valid UTF-8"),
        (b"---\ntitle: open\n", "partially_parsed", "front matter"),
        (b"```{python}\nvalue = 1\n", "partially_parsed", "cell is not closed"),
    ],
)
def test_quarto_failures_are_localized(
    content: bytes, state: str, message: str, tmp_path: Path
) -> None:
    source = tmp_path / "failure.qmd"
    source.write_bytes(content)

    result = inspect_quarto(source, "audit:failure")

    assert result["state"] == state
    assert any(message in item["message"] for item in result["syntax_issues"])


def test_quarto_duplicate_and_synthetic_labels_never_collide(tmp_path: Path) -> None:
    source = tmp_path / "labels.qmd"
    source.write_text(
        "```{python}\n#| label: repeated\n1\n```\n"
        "```{r}\n#| label: repeated\n1\n```\n"
        "```{julia}\n#| label: cell-2\n1\n```\n"
        "```{python}\n1\n```\n",
        encoding="utf-8",
    )

    result = inspect_quarto(source, "audit:labels")

    assert result["state"] == "partially_parsed"
    cells = result["extensions"]["x-quarto-cells"]
    assert [item["label"] for item in cells] == ["cell-0", "cell-1", "cell-2", "cell-3"]
    assert len({item["source_ref"]["locator"] for item in cells}) == 4
    assert len(result["syntax_issues"]) == 2


def test_quarto_finite_ceilings_fail_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = tmp_path / "bounded.qmd"
    source.write_text("```{python}\n1\n```\n", encoding="utf-8")

    monkeypatch.setattr(quarto_inventory, "MAX_QUARTO_BYTES", 1)
    assert inspect_quarto(source, "audit:bytes")["state"] == "unsupported"
    monkeypatch.setattr(quarto_inventory, "MAX_QUARTO_BYTES", 2_000_000)
    monkeypatch.setattr(quarto_inventory, "MAX_QUARTO_LINES", 1)
    assert inspect_quarto(source, "audit:lines")["state"] == "unsupported"
    monkeypatch.setattr(quarto_inventory, "MAX_QUARTO_LINES", 100_000)
    monkeypatch.setattr(quarto_inventory, "MAX_QUARTO_CELLS", 0)
    assert inspect_quarto(source, "audit:cells")["state"] == "unsupported"


def test_quarto_source_path_must_be_repository_relative(tmp_path: Path) -> None:
    source = tmp_path / "analysis.qmd"
    source.write_text("text\n", encoding="utf-8")

    with pytest.raises(ValueError, match="repository-relative"):
        inspect_quarto(source, "audit:path", source_path="../analysis.qmd")


def test_quarto_only_workspace_audits_caches_and_replays_without_execution(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "quarto-project"
    repository.mkdir()
    marker = repository / "must-not-exist"
    report = repository / "analysis.qmd"
    report.write_text(
        "# Results\n\nFounder alleles were reoriented before the HMM emission.\n\n"
        "```{python}\n"
        f"open({str(marker)!r}, 'w').write('executed')\n"
        "```\n\n"
        "```{r}\n"
        f"system('touch {marker.as_posix()}')\n"
        "```\n",
        encoding="utf-8",
    )

    first_root = tmp_path / "first-audit"
    second_root = tmp_path / "second-audit"
    first = run_audit(repository, first_root, schema_root, report="analysis.qmd")
    second = run_audit(repository, second_root, schema_root, report="analysis.qmd")

    assert not marker.exists()
    assert first["findings"] == []
    assert first["claims"] == []
    assert first["material_questions"] == []
    parser_result = next(
        item for item in first["parser_results"] if item["source_ref"]["path"] == "analysis.qmd"
    )
    assert parser_result["parser_id"] == "parser:quarto-source-inventory"
    assert "analysis.qmd" not in first["coverage_records"][0]["uninspected_paths"]
    first_lock = json.loads((first_root / "semantic.lock.json").read_text(encoding="utf-8"))
    second_lock = json.loads((second_root / "semantic.lock.json").read_text(encoding="utf-8"))
    assert first_lock["cache_summary"]["miss_paths"] == ["analysis.qmd"]
    assert second_lock["cache_summary"]["hit_paths"] == ["analysis.qmd"]
    assert [item["parser_result_id"] for item in second["parser_results"]] == [
        item["parser_result_id"] for item in first["parser_results"]
    ]
    assert {item["audit_run_id"] for item in second["parser_results"]} == {second["audit_run_id"]}
    child = next(
        item
        for item in first["parser_results"]
        if item["parser_id"] == "parser:python-ast-tokenize"
    )
    assert child["source_ref"]["source_kind"] == "document_chunk"
    assert child["source_ref"]["chunk_label"] == "cell-0"
    assert any(
        item["parser_id"] == "parser:r-tree-sitter-inventory"
        and item["source_ref"]["source_kind"] == "document_chunk"
        for item in first["parser_results"]
    )
    selected_artifact_id = first["publication_surfaces"][0]["selection"]["selected_surface_refs"][
        0
    ]["record_id"]
    report_artifact = next(
        item for item in first["artifacts"] if item["artifact_id"] == selected_artifact_id
    )
    assert report_artifact["source_refs"][0]["source_kind"] == "file_span"

    replayed = replay(first_root / "semantic.lock.json", tmp_path / "replay", schema_root)
    assert replayed["parser_results"] == first["parser_results"]
    assert replayed["coverage_records"] == first["coverage_records"]

    report.write_text(report.read_text(encoding="utf-8").replace("reoriented", "oriented"))
    third_root = tmp_path / "third-audit"
    run_audit(repository, third_root, schema_root, report="analysis.qmd")
    third_lock = json.loads((third_root / "semantic.lock.json").read_text(encoding="utf-8"))
    assert third_lock["cache_summary"]["miss_paths"] == ["analysis.qmd"]
    assert third_lock["cache_summary"]["invalidated_paths"] == ["analysis.qmd"]
