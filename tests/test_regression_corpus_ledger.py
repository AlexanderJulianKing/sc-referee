from __future__ import annotations

import json
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation.regression_corpus import (
    DEFAULT_REGRESSION_CORPUS_LEDGER,
    RegressionCorpusLedgerError,
    regression_tree_digest,
    validate_regression_corpus_ledger,
)

from sc_referee.calculation_checks.profiles import default_calculation_check_registry
from sc_referee.core.ids import canonical_json, semantic_digest
from sc_referee.scientific_checks.profiles import default_scientific_check_registry

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / DEFAULT_REGRESSION_CORPUS_LEDGER


def _ledger() -> dict[str, Any]:
    value = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _write_ledger(tmp_path: Path, value: dict[str, Any], *, redigest: bool = True) -> Path:
    if redigest:
        digest_input = deepcopy(value)
        digest_input.pop("ledger_digest", None)
        value["ledger_digest"] = semantic_digest(digest_input)
    path = tmp_path / "ledger.json"
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")
    return path


def test_versioned_ledger_covers_every_active_module_without_qualification_leakage() -> None:
    ledger = validate_regression_corpus_ledger(LEDGER, project_root=ROOT)

    scientific = default_scientific_check_registry()
    calculation = default_calculation_check_registry()
    expected_ids = {
        *(module.manifest.check_id for module in scientific.modules),
        *(module.manifest.check_id for module in calculation.modules),
    }
    covered_ids = {component for case in ledger["cases"] for component in case["component_refs"]}

    assert ledger["ledger_version"] == "1.0.0"
    assert ledger["qualification_use_permitted"] is False
    assert expected_ids == covered_ids
    assert len(expected_ids) == 31
    assert all(source["qualification_status"] == "excluded" for source in ledger["sources"])
    assert all(case["qualification_status"] == "excluded" for case in ledger["cases"])
    assert any(source["answer_side"] for source in ledger["sources"])
    assert any(source["benchmark_derived"] for source in ledger["sources"])
    assert any(source["provenance_class"] == "synthetic_test" for source in ledger["sources"])


def test_shape_and_identity_duplicates_fail_closed(tmp_path: Path) -> None:
    extra = _ledger()
    extra["unexpected"] = True
    with pytest.raises(RegressionCorpusLedgerError, match="unexpected fields"):
        validate_regression_corpus_ledger(_write_ledger(tmp_path, extra), project_root=ROOT)

    duplicate_source = _ledger()
    duplicate_source["sources"].append(deepcopy(duplicate_source["sources"][0]))
    with pytest.raises(RegressionCorpusLedgerError, match="Duplicate source ID"):
        validate_regression_corpus_ledger(
            _write_ledger(tmp_path, duplicate_source), project_root=ROOT
        )

    duplicate_case = _ledger()
    duplicate_case["cases"].append(deepcopy(duplicate_case["cases"][0]))
    with pytest.raises(RegressionCorpusLedgerError, match="Duplicate regression case ID"):
        validate_regression_corpus_ledger(
            _write_ledger(tmp_path, duplicate_case), project_root=ROOT
        )

    unused_source = _ledger()
    unused_source["sources"].append(
        {
            "source_id": "source:unused-external",
            "source_kind": "external_revision",
            "uri": "https://example.org/unused.git",
            "revision": "1" * 40,
            "content_digest": "sha256:" + "2" * 64,
            "provenance_class": "independent_repository",
            "answer_side": False,
            "benchmark_derived": False,
            "qualification_status": "excluded",
            "exclusion_reason": "Unadjudicated development source.",
        }
    )
    with pytest.raises(RegressionCorpusLedgerError, match="lack a regression case"):
        validate_regression_corpus_ledger(_write_ledger(tmp_path, unused_source), project_root=ROOT)


def test_noncanonical_json_and_ledger_digest_mutation_fail_closed(tmp_path: Path) -> None:
    noncanonical = tmp_path / "noncanonical.json"
    noncanonical.write_text(json.dumps(_ledger(), indent=2) + "\n", encoding="utf-8")
    with pytest.raises(RegressionCorpusLedgerError, match="canonical JSON"):
        validate_regression_corpus_ledger(noncanonical, project_root=ROOT)

    drifted = _ledger()
    drifted["ledger_digest"] = "sha256:" + "0" * 64
    with pytest.raises(RegressionCorpusLedgerError, match="ledger digest mismatch"):
        validate_regression_corpus_ledger(
            _write_ledger(tmp_path, drifted, redigest=False), project_root=ROOT
        )


def test_registry_manifest_and_case_coverage_drift_fail_closed(tmp_path: Path) -> None:
    stale_manifest = _ledger()
    stale_manifest["component_inventory"][0]["manifest_digest"] = "sha256:" + "0" * 64
    with pytest.raises(RegressionCorpusLedgerError, match="active registries"):
        validate_regression_corpus_ledger(
            _write_ledger(tmp_path, stale_manifest), project_root=ROOT
        )

    missing_case = _ledger()
    removed_component = next(
        case["component_refs"][0]
        for case in missing_case["cases"]
        if case["component_refs"][0].startswith("check:")
    )
    missing_case["cases"] = [
        case for case in missing_case["cases"] if removed_component not in case["component_refs"]
    ]
    with pytest.raises(RegressionCorpusLedgerError, match="lack a retained regression case"):
        validate_regression_corpus_ledger(_write_ledger(tmp_path, missing_case), project_root=ROOT)


@pytest.mark.parametrize("level", ["ledger", "source", "case"])
def test_qualification_leakage_is_forbidden(tmp_path: Path, level: str) -> None:
    value = _ledger()
    if level == "ledger":
        value["qualification_use_permitted"] = True
    elif level == "source":
        value["sources"][0]["qualification_status"] = "eligible"
    else:
        value["cases"][0]["qualification_status"] = "eligible"

    with pytest.raises(RegressionCorpusLedgerError, match="qualification"):
        validate_regression_corpus_ledger(_write_ledger(tmp_path, value), project_root=ROOT)


def test_local_path_digest_and_selector_mutations_fail_closed(tmp_path: Path) -> None:
    traversal = _ledger()
    pytest_source = next(
        source for source in traversal["sources"] if source["source_kind"] == "pytest_module"
    )
    pytest_source["path"] = "../outside.py"
    with pytest.raises(RegressionCorpusLedgerError, match="bounded and relative"):
        validate_regression_corpus_ledger(_write_ledger(tmp_path, traversal), project_root=ROOT)

    source_drift = _ledger()
    pytest_source = next(
        source for source in source_drift["sources"] if source["source_kind"] == "pytest_module"
    )
    pytest_source["content_digest"] = "sha256:" + "0" * 64
    with pytest.raises(RegressionCorpusLedgerError, match="source digest mismatch"):
        validate_regression_corpus_ledger(_write_ledger(tmp_path, source_drift), project_root=ROOT)

    missing_selector = _ledger()
    scientific_case = next(
        case
        for case in missing_selector["cases"]
        if case["source_ref"] == "source:scientific-check-integration-tests"
    )
    scientific_case["selector"] = "test_does_not_exist"
    with pytest.raises(RegressionCorpusLedgerError, match="does not exist"):
        validate_regression_corpus_ledger(
            _write_ledger(tmp_path, missing_selector), project_root=ROOT
        )


def test_external_sources_require_immutable_revision_and_payload_digest(tmp_path: Path) -> None:
    value = _ledger()
    external = next(
        source for source in value["sources"] if source["source_id"] == "source:bh-control-family"
    )
    external.clear()
    external.update(
        {
            "source_id": "source:bh-control-family",
            "source_kind": "external_revision",
            "uri": "https://example.org/control-family.git",
            "revision": "1" * 40,
            "content_digest": "sha256:" + "2" * 64,
            "provenance_class": "public_development_control",
            "answer_side": True,
            "benchmark_derived": False,
            "qualification_status": "excluded",
            "exclusion_reason": "External development control is unavailable offline.",
        }
    )
    validate_regression_corpus_ledger(_write_ledger(tmp_path, value), project_root=ROOT)

    external["revision"] = "main"
    with pytest.raises(RegressionCorpusLedgerError, match="full lowercase Git commit"):
        validate_regression_corpus_ledger(_write_ledger(tmp_path, value), project_root=ROOT)


def test_tree_byte_and_symlink_mutations_are_detected(tmp_path: Path) -> None:
    source = ROOT / "evaluation/development-controls/multiple-testing-bh-v1"
    copied = tmp_path / "control"
    shutil.copytree(source, copied)
    original = regression_tree_digest(copied)

    report = copied / "cases/multiple-testing-positive/workspace/report.md"
    report.write_text(report.read_text(encoding="utf-8") + "drift\n", encoding="utf-8")
    assert regression_tree_digest(copied) != original

    linked = tmp_path / "linked-control"
    linked.symlink_to(copied, target_is_directory=True)
    with pytest.raises(RegressionCorpusLedgerError, match="non-symlink directory"):
        regression_tree_digest(linked)

    over_budget = tmp_path / "over-budget-control"
    over_budget.mkdir()
    with (over_budget / "large.bin").open("wb") as handle:
        handle.truncate(16_777_217)
    with pytest.raises(RegressionCorpusLedgerError, match="file exceeds its byte limit"):
        regression_tree_digest(over_budget)


def test_finding_ceiling_and_cross_authority_cases_are_rejected(tmp_path: Path) -> None:
    finding = _ledger()
    finding["cases"][0]["assessment_ceiling"] = "finding"
    with pytest.raises(RegressionCorpusLedgerError, match="assessment ceiling"):
        validate_regression_corpus_ledger(_write_ledger(tmp_path, finding), project_root=ROOT)

    mixed = _ledger()
    scientific_id = next(
        item["component_id"]
        for item in mixed["component_inventory"]
        if item["component_kind"] == "scientific_check"
    )
    mixed["cases"][0]["component_refs"] = sorted(
        [*mixed["cases"][0]["component_refs"], scientific_id]
    )
    with pytest.raises(RegressionCorpusLedgerError, match="mixes component authority"):
        validate_regression_corpus_ledger(_write_ledger(tmp_path, mixed), project_root=ROOT)
