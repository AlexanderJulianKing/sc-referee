from __future__ import annotations

from pathlib import Path

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
    assert [(item["label"], item["evaluation_state"]) for item in chunks] == [
        ("setup", "enabled"),
        ("hidden", "disabled"),
    ]
    assert chunks[0]["code_start_line"] == 8
    assert chunks[0]["code_end_line"] == 8
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
