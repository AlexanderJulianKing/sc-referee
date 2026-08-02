from __future__ import annotations

import json
from pathlib import Path

from sc_referee.controller import replay, run_audit
from sc_referee.core.ids import sha256_digest
from sc_referee.parsers.rmarkdown_inventory import inspect_rmarkdown
from sc_referee.records.schema_registry import LocalSchemaRegistry


def test_rmarkdown_inventory_is_schema_valid_and_preserves_chunk_boundaries(
    schema_root: Path, tmp_path: Path
) -> None:
    report = tmp_path / "analysis.Rmd"
    report.write_text(
        "---\n"
        "title: Example\n"
        "---\n\n"
        "A prose method description.\n\n"
        "```{r setup, echo=TRUE}\n"
        "value <- 1\n"
        "```\n\n"
        "```{r hidden, eval=FALSE}\n"
        "system('must-not-run')\n"
        "```\n",
        encoding="utf-8",
    )

    result = inspect_rmarkdown(report, "audit:rmarkdown")

    LocalSchemaRegistry(schema_root).validate(result)
    assert result["parser_id"] == "parser:rmarkdown-selected-report-inventory"
    assert result["state"] == "parsed"
    assert result["extensions"]["x-rmarkdown-front-matter-span"] == {
        "start_line": 1,
        "end_line": 3,
    }
    chunks = result["extensions"]["x-rmarkdown-chunks"]
    assert [
        (item["label"], item["identity_kind"], item["evaluation_state"]) for item in chunks
    ] == [
        ("setup", "declared_unique", "unspecified"),
        ("hidden", "declared_unique", "disabled_declared"),
    ]
    assert chunks[0]["code_start_line"] == 8
    assert chunks[0]["code_end_line"] == 8
    assert chunks[0]["code_digest"] == sha256_digest(b"value <- 1\n")
    assert chunks[0]["source_ref"]["source_kind"] == "document_chunk"
    assert chunks[0]["source_ref"]["chunk_label"] == "setup"
    assert result["extensions"]["x-rmarkdown-prose-spans"][0]["text"] == (
        "A prose method description."
    )


def test_rmarkdown_invalid_utf8_and_unclosed_chunk_are_localized(
    schema_root: Path, tmp_path: Path
) -> None:
    invalid = tmp_path / "invalid.Rmd"
    invalid.write_bytes(b"---\n\xff\n")
    invalid_result = inspect_rmarkdown(invalid, "audit:invalid")
    LocalSchemaRegistry(schema_root).validate(invalid_result)
    assert invalid_result["state"] == "error"
    assert invalid_result["coverage_status"] == "not_covered"

    unclosed = tmp_path / "unclosed.Rmd"
    unclosed.write_text("```{r}\nvalue <- 1\n", encoding="utf-8")
    unclosed_result = inspect_rmarkdown(unclosed, "audit:unclosed")
    LocalSchemaRegistry(schema_root).validate(unclosed_result)
    assert unclosed_result["state"] == "partially_parsed"
    assert unclosed_result["extensions"]["x-rmarkdown-chunks"] == []
    assert unclosed_result["syntax_issues"][0]["recoverable"] is True


def test_rmarkdown_inventory_never_executes_chunk_content(tmp_path: Path) -> None:
    marker = tmp_path / "executed.txt"
    report = tmp_path / "analysis.Rmd"
    report.write_text(
        f"```{{r}}\nwriteLines('executed', {str(marker)!r})\n```\n",
        encoding="utf-8",
    )

    result = inspect_rmarkdown(report, "audit:no-execution")

    assert result["state"] == "parsed"
    assert not marker.exists()


def test_rmarkdown_duplicate_and_synthetic_chunk_labels_never_collide(tmp_path: Path) -> None:
    report = tmp_path / "labels.Rmd"
    report.write_text(
        "```{r repeated}\n1\n```\n"
        "```{r repeated}\n2\n```\n"
        "```{r chunk-2}\n3\n```\n"
        "```{r}\n4\n```\n",
        encoding="utf-8",
    )

    result = inspect_rmarkdown(report, "audit:labels", source_path="analysis.Rmd")

    assert result["state"] == "partially_parsed"
    chunks = result["extensions"]["x-rmarkdown-chunks"]
    assert [item["label"] for item in chunks] == ["chunk-0", "chunk-1", "chunk-2", "chunk-3"]
    assert len({item["source_ref"]["locator"] for item in chunks}) == 4
    assert len(result["syntax_issues"]) == 2


def test_rmarkdown_chunks_enter_static_r_bridge_without_execution_and_replay(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    marker = repository / "must-not-exist"
    report = repository / "analysis.Rmd"
    report.write_text(
        "# Analysis\n\n"
        "```{r ld-model}\n"
        "library(MASS)\n"
        "factor <- chol(ld_covariance)\n"
        "y_white <- forwardsolve(factor, outcome_innovations)\n"
        "x_white <- forwardsolve(factor, exposure_innovations)\n"
        "fit <- rlm(y=y_white, x=x_white, psi=psi.bisquare)\n"
        "```\n\n"
        "```{r hidden, eval=FALSE}\n"
        f"writeLines('executed', {str(marker)!r})\n"
        "```\n",
        encoding="utf-8",
    )
    output = tmp_path / "audit"

    bundle = run_audit(repository, output, schema_root, report="analysis.Rmd")

    assert not marker.exists()
    children = [
        item
        for item in bundle["parser_results"]
        if item.get("extensions", {}).get("x-virtual-source", {}).get("language") == "r"
    ]
    assert children
    assert {item["source_ref"]["chunk_label"] for item in children} == {"ld-model", "hidden"}
    assert all(item["source_ref"]["source_kind"] == "document_chunk" for item in children)
    lock = json.loads((output / "semantic.lock.json").read_text(encoding="utf-8"))
    locked_children = [
        item
        for item in lock["parser_results"]
        if item.get("extensions", {}).get("x-virtual-source", {}).get("language") == "r"
    ]
    assert locked_children == children
    assert {
        (
            item["extensions"]["x-virtual-source"]["profile"],
            item["extensions"]["x-virtual-source"]["bridge_version"],
        )
        for item in locked_children
    } == {("bounded-container-cell-static-language-bridge-v2", "0.2.0")}
    replayed = replay(output / "semantic.lock.json", tmp_path / "replay", schema_root)
    assert replayed["parser_results"] == bundle["parser_results"]
    assert replayed["material_questions"] == bundle["material_questions"]
