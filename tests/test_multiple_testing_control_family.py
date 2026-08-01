from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_multiple_testing_control_family import (
    ALPHA,
    RAW_P_VALUES,
    benjamini_hochberg_oracle,
    build_multiple_testing_control_family,
)


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _rows(root: Path, case_id: str) -> list[dict[str, str]]:
    path = root / "cases" / case_id / "workspace" / "results.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_bh_oracle_matches_known_ordered_example_and_rejects_invalid_values() -> None:
    assert benjamini_hochberg_oracle(("0.01", "0.04", "0.03", "0.002")) == (
        "0.02",
        "0.04",
        "0.04",
        "0.008",
    )
    with pytest.raises(ValueError):
        benjamini_hochberg_oracle(())
    with pytest.raises(ValueError):
        benjamini_hochberg_oracle(("1.01",))


def test_frozen_multiple_testing_family_has_four_distinct_control_roles(
    project_root: Path,
) -> None:
    root = project_root / "evaluation" / "development-controls" / "multiple-testing-bh-v1"
    specification = _load(root / "CONTROL_SPEC.json")
    cases = specification["cases"]
    assert isinstance(cases, list)
    assert {case["role"] for case in cases} == {
        "positive",
        "verified_good",
        "hard_negative",
        "ambiguous",
    }
    assert {case["expected_outcome"] for case in cases} == {
        "nonconformant",
        "conformant",
        "not_applicable",
        "insufficient_evidence",
    }
    assert specification["controls"] == {
        "labels_outside_workspaces": True,
        "old_public_repository_is_authority": False,
        "one_material_difference_per_twin": True,
        "production_finding_permission": False,
        "project_code_execution": False,
    }


def test_positive_and_corrected_twin_share_raw_family_but_not_adjustment(
    project_root: Path,
) -> None:
    root = project_root / "evaluation" / "development-controls" / "multiple-testing-bh-v1"
    positive = _rows(root, "multiple-testing-positive")
    corrected = _rows(root, "multiple-testing-corrected-twin")
    assert [row["p_value"] for row in positive] == list(RAW_P_VALUES)
    assert [row["p_value"] for row in corrected] == list(RAW_P_VALUES)
    assert [row["adjusted_p_value"] for row in positive] != [
        row["adjusted_p_value"] for row in corrected
    ]
    assert sum(row["significant"] == "true" for row in positive) == 4
    assert sum(row["significant"] == "true" for row in corrected) == 2
    assert (
        sum(float(value) <= float(ALPHA) for value in benjamini_hochberg_oracle(RAW_P_VALUES)) == 2
    )


def test_hard_negative_and_ambiguous_case_preserve_decisive_boundaries(
    project_root: Path,
) -> None:
    root = project_root / "evaluation" / "development-controls" / "multiple-testing-bh-v1"
    hard_report = (
        root / "cases" / "multiple-testing-hard-negative" / "workspace" / "report.md"
    ).read_text(encoding="utf-8")
    ambiguous_report = (
        root / "cases" / "multiple-testing-ambiguous" / "workspace" / "report.md"
    ).read_text(encoding="utf-8")
    assert "one preregistered primary hypothesis" in hard_report
    assert "no multiple-testing adjustment governs" in hard_report
    assert "only selected hits" in ambiguous_report
    assert "complete set of tested hypotheses" in ambiguous_report


def test_control_family_builder_is_byte_reproducible_and_no_replace(
    project_root: Path,
    tmp_path: Path,
) -> None:
    output = tmp_path / "multiple-testing-bh-v1"
    build_multiple_testing_control_family(output)
    committed = project_root / "evaluation" / "development-controls" / "multiple-testing-bh-v1"
    generated = {
        path.relative_to(output).as_posix(): path.read_bytes()
        for path in output.rglob("*")
        if path.is_file()
    }
    expected = {
        path.relative_to(committed).as_posix(): path.read_bytes()
        for path in committed.rglob("*")
        if path.is_file()
    }
    assert generated == expected
    with pytest.raises(FileExistsError):
        build_multiple_testing_control_family(output)


def test_control_family_manifest_binds_every_nonmanifest_file(project_root: Path) -> None:
    root = project_root / "evaluation" / "development-controls" / "multiple-testing-bh-v1"
    manifest = _load(root / "MANIFEST.json")
    inventory = manifest["inventory"]
    assert isinstance(inventory, list)
    assert manifest["inventory_digest"] == semantic_digest(inventory)
    expected_paths = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.name != "MANIFEST.json"
    }
    assert {entry["path"] for entry in inventory} == expected_paths
    for entry in inventory:
        path = root / entry["path"]
        assert entry["content_digest"] == sha256_digest(path.read_bytes())
        assert entry["size_bytes"] == path.stat().st_size
