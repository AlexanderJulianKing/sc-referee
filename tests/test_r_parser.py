from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from sc_referee.parsers.r_dual import (
    MAX_R_SOURCE_BYTES,
    R_BASE_PARSER_ID,
    R_TREE_SITTER_PARSER_ID,
    inspect_r,
)
from sc_referee.records.schema_registry import LocalSchemaRegistry


def _calls(result: dict[str, object]) -> list[dict[str, object]]:
    extensions = result["extensions"]
    assert isinstance(extensions, dict)
    calls = extensions["x-r-calls"]
    assert isinstance(calls, list)
    return calls


def _comparison(result: dict[str, object]) -> dict[str, object]:
    extensions = result["extensions"]
    assert isinstance(extensions, dict)
    comparison = extensions["x-r-cross-parser-comparison"]
    assert isinstance(comparison, dict)
    return comparison


def test_tree_sitter_r_inventory_is_bounded_and_does_not_execute_source(
    schema_root: Path, tmp_path: Path
) -> None:
    marker = tmp_path / "must-not-exist"
    source = tmp_path / "analysis.R"
    source.write_text(
        "dds <- DESeq2::DESeqDataSetFromMatrix(\n"
        "  countData = counts, colData = samples, design = ~ condition\n"
        ")\n"
        "result <- DESeq2::results(DESeq2::DESeq(dds), contrast = c('condition', 'a', 'b'))\n"
        f"system('touch {marker.as_posix()}')\n",
        encoding="utf-8",
    )

    tree_result, base_result = inspect_r(
        source,
        "audit:r-static",
        source_path="analysis.R",
        r_executable="",
    )

    registry = LocalSchemaRegistry(schema_root)
    registry.validate(tree_result)
    registry.validate(base_result)
    assert tree_result["parser_id"] == R_TREE_SITTER_PARSER_ID
    assert tree_result["state"] == "parsed"
    assert tree_result["coverage_status"] == "partially_covered"
    assert base_result["parser_id"] == R_BASE_PARSER_ID
    assert base_result["state"] == "parser_unavailable"
    assert _comparison(tree_result)["status"] == "unavailable"
    assert [item["terminal_name"] for item in _calls(tree_result)] == [
        "DESeqDataSetFromMatrix",
        "results",
        "DESeq",
        "c",
        "system",
    ]
    first = _calls(tree_result)[0]
    assert first["target_kind"] == "namespaced"
    assert first["namespace"] == "DESeq2"
    assert first["namespace_operator"] == "::"
    assert first["argument_names"] == ["colData", "countData", "design"]
    assert first["source_ref"]["start_line"] == 1
    assert first["source_ref"]["end_line"] == 3
    assert not marker.exists()


@pytest.mark.skipif(shutil.which("R") is None, reason="base R is not installed")
def test_independent_r_backends_agree_without_executing_project_code(
    schema_root: Path, tmp_path: Path
) -> None:
    marker = tmp_path / "must-not-exist"
    source = tmp_path / "analysis.R"
    source.write_text(
        "fit <- edgeR::glmQLFit(y, design = design, robust = TRUE)\n"
        "test <- edgeR::glmQLFTest(fit, coef = 2)\n"
        f"system('touch {marker.as_posix()}')\n",
        encoding="utf-8",
    )

    tree_result, base_result = inspect_r(
        source,
        "audit:r-dual",
        source_path="analysis.R",
    )

    registry = LocalSchemaRegistry(schema_root)
    registry.validate(tree_result)
    registry.validate(base_result)
    assert tree_result["state"] == "parsed"
    assert base_result["state"] == "parsed"
    assert _comparison(tree_result)["status"] == "exact_call_inventory_agreement"
    assert _comparison(base_result)["status"] == "exact_call_inventory_agreement"
    assert _calls(tree_result) == _calls(base_result)
    assert not marker.exists()


def test_malformed_r_is_localized_without_stopping_other_backend(
    schema_root: Path, tmp_path: Path
) -> None:
    source = tmp_path / "broken.R"
    source.write_text("result <- mean(c(1, 2)\n", encoding="utf-8")

    tree_result, base_result = inspect_r(
        source,
        "audit:r-malformed",
        source_path="broken.R",
    )

    registry = LocalSchemaRegistry(schema_root)
    registry.validate(tree_result)
    registry.validate(base_result)
    assert tree_result["state"] == "partially_parsed"
    assert tree_result["syntax_issues"]
    if shutil.which("R") is None:
        assert base_result["state"] == "parser_unavailable"
    else:
        assert base_result["state"] == "error"
        assert base_result["syntax_issues"]
    assert _comparison(tree_result)["status"] == "unavailable"


def test_dynamic_r_call_target_is_explicitly_opaque(tmp_path: Path) -> None:
    source = tmp_path / "dynamic.R"
    source.write_text("get('mean')(c(1, 2, 3))\n", encoding="utf-8")

    tree_result, _ = inspect_r(
        source,
        "audit:r-dynamic",
        source_path="dynamic.R",
        r_executable="",
    )

    assert any(item["target_kind"] == "dynamic" for item in _calls(tree_result))
    assert any(item["kind"] == "dynamic_r_call_target" for item in tree_result["opaque_constructs"])


def test_r_source_size_ceiling_prevents_either_backend_from_starting(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = tmp_path / "large.R"
    source.write_bytes(b"#" * (MAX_R_SOURCE_BYTES + 1))

    def forbidden_run(*args: object, **kwargs: object) -> None:
        raise AssertionError("base R must not start for an over-budget source")

    monkeypatch.setattr(subprocess, "run", forbidden_run)
    tree_result, base_result = inspect_r(source, "audit:r-large", source_path="large.R")

    assert tree_result["state"] == "unsupported"
    assert base_result["state"] == "unsupported"
    assert tree_result["coverage_status"] == "not_covered"
    assert base_result["coverage_status"] == "not_covered"


def test_r_helper_timeout_is_localized(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    source = tmp_path / "analysis.R"
    source.write_text("mean(c(1, 2, 3))\n", encoding="utf-8")

    def timed_out(*args: object, **kwargs: object) -> None:
        raise subprocess.TimeoutExpired(cmd="R", timeout=1)

    monkeypatch.setattr(subprocess, "run", timed_out)
    tree_result, base_result = inspect_r(
        source,
        "audit:r-timeout",
        source_path="analysis.R",
        r_executable="R",
    )

    assert tree_result["state"] == "parsed"
    assert base_result["state"] == "parser_unavailable"
    assert _comparison(tree_result)["status"] == "unavailable"


def test_invalid_r_helper_output_is_localized(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = tmp_path / "analysis.R"
    source.write_text("mean(c(1, 2, 3))\n", encoding="utf-8")

    def invalid_output(*args: object, **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(args=["R"], returncode=0, stdout=b"not-protocol\n")

    monkeypatch.setattr(subprocess, "run", invalid_output)
    tree_result, base_result = inspect_r(
        source,
        "audit:r-invalid-helper",
        source_path="analysis.R",
        r_executable="R",
    )

    assert tree_result["state"] == "parsed"
    assert base_result["state"] == "error"
    assert "invalid output" in base_result["syntax_issues"][0]["message"]
    assert _comparison(base_result)["status"] == "unavailable"


def test_r_parser_inventory_disagreement_is_explicit_and_partial(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = tmp_path / "analysis.R"
    source.write_text("mean(c(1, 2, 3))\n", encoding="utf-8")
    r_version = b"R synthetic parser receipt".hex()

    def empty_inventory(*args: object, **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(
            args=["R"], returncode=0, stdout=f"OK\t{r_version}\t0\n".encode("ascii")
        )

    monkeypatch.setattr(subprocess, "run", empty_inventory)
    tree_result, base_result = inspect_r(
        source,
        "audit:r-disagreement",
        source_path="analysis.R",
        r_executable="R",
    )

    assert tree_result["state"] == "partially_parsed"
    assert base_result["state"] == "partially_parsed"
    assert tree_result["parser_disagreement"] == base_result["parser_disagreement"]
    assert tree_result["parser_disagreement"]
    assert _comparison(tree_result)["status"] == "call_inventory_disagreement"


def test_r_source_path_must_be_repository_relative(tmp_path: Path) -> None:
    source = tmp_path / "analysis.R"
    source.write_text("mean(1)\n", encoding="utf-8")

    with pytest.raises(ValueError, match="repository-relative"):
        inspect_r(source, "audit:r-path", source_path="../analysis.R")
