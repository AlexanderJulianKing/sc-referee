from __future__ import annotations

import json
import shutil
from pathlib import Path

from sc_referee.controller import replay, run_audit


def _operand(observation: dict[str, object], name: str) -> object:
    operands = observation["operands"]
    assert isinstance(operands, list)
    return next(item["value"] for item in operands if item["name"] == name)


def _bh_sidecar_workspace(tmp_path: Path) -> Path:
    repository = tmp_path / "portable-bh"
    (repository / "configuration").mkdir(parents=True)
    (repository / "exported" / "tables").mkdir(parents=True)
    (repository / "analysis-summary.md").write_text(
        "# Analysis\n\nThe multiplicity calculation is declared in a selected audit sidecar.\n",
        encoding="utf-8",
    )
    (repository / "exported" / "tables" / "hypotheses.tsv").write_text(
        "called\tq_reported\tfeature_key\tnuisance\tp_raw\n"
        "true\t0.001\tgene_01\textra\t0.001\n"
        "true\t0.01\tgene_02\textra\t0.01\n"
        "true\t0.02\tgene_03\textra\t0.02\n"
        "true\t0.04\tgene_04\textra\t0.04\n"
        "false\t0.2\tgene_05\textra\t0.2\n"
        "false\t0.4\tgene_06\textra\t0.4\n"
        "false\t0.6\tgene_07\textra\t0.6\n"
        "false\t0.8\tgene_08\textra\t0.8\n"
        "false\t0.9\tgene_09\textra\t0.9\n"
        "false\t0.95\tgene_10\textra\t0.95\n",
        encoding="utf-8",
    )
    (repository / "configuration" / "review-bindings.yaml").write_text(
        "sc_referee_calculation_contracts: 1\n"
        "contracts:\n"
        "  - check_id: calculation-check:benjamini-hochberg-complete-family-v1\n"
        "    contract:\n"
        "      procedure: benjamini_hochberg\n"
        "      family: complete\n"
        "      alpha: '0.05'\n"
        "      table: exported/tables/hypotheses.tsv\n"
        "      id_column: feature_key\n"
        "      raw_pvalue_column: p_raw\n"
        "      adjusted_pvalue_column: q_reported\n"
        "      call_column: called\n",
        encoding="utf-8",
    )
    return repository


def test_bh_sidecar_layout_uses_same_calculation_with_alternate_paths_and_columns(
    project_root: Path,
    schema_root: Path,
    tmp_path: Path,
) -> None:
    embedded_repository = tmp_path / "embedded-bh"
    shutil.copytree(
        project_root
        / "evaluation"
        / "development-controls"
        / "multiple-testing-bh-v1"
        / "cases"
        / "multiple-testing-positive"
        / "workspace",
        embedded_repository,
    )
    embedded = run_audit(
        embedded_repository,
        tmp_path / "embedded-audit",
        schema_root,
        report="report.md",
    )["deterministic_check_observations"][0]
    sidecar_output = tmp_path / "sidecar-audit"
    sidecar = run_audit(
        _bh_sidecar_workspace(tmp_path),
        sidecar_output,
        schema_root,
        report="analysis-summary.md",
        material_inputs=(
            "configuration/review-bindings.yaml",
            "exported/tables/hypotheses.tsv",
        ),
    )["deterministic_check_observations"][0]

    assert sidecar["adapter_manifest"]["adapter_id"] == (
        "calculation-adapter:selected-sidecar-bh-complete-family-v1"
    )
    assert sidecar["comparison"]["outcome"] == embedded["comparison"]["outcome"]
    for name in (
        "alpha",
        "raw_p_values",
        "reported_adjusted_p_values",
        "recomputed_adjusted_p_values",
        "reported_calls",
        "recomputed_calls",
        "reported_discovery_count",
        "recomputed_discovery_count",
        "adjusted_mismatch_indices",
        "call_mismatch_indices",
    ):
        assert _operand(sidecar, name) == _operand(embedded, name)
    assert any(
        item["record_id"].startswith("artifact:")
        for item in sidecar["input_refs"]
        if item["record_type"] == "artifact"
    )
    replayed = replay(
        sidecar_output / "semantic.lock.json",
        tmp_path / "sidecar-replay",
        schema_root,
    )
    assert replayed["deterministic_check_observations"][0] == sidecar


def test_competing_embedded_and_sidecar_bh_contracts_fail_closed(
    project_root: Path,
    schema_root: Path,
    tmp_path: Path,
) -> None:
    repository = tmp_path / "competing-bh"
    shutil.copytree(
        project_root
        / "evaluation"
        / "development-controls"
        / "multiple-testing-bh-v1"
        / "cases"
        / "multiple-testing-positive"
        / "workspace",
        repository,
    )
    (repository / "bindings.yaml").write_text(
        "sc_referee_calculation_contracts: 1\n"
        "contracts:\n"
        "  - check_id: calculation-check:benjamini-hochberg-complete-family-v1\n"
        "    contract:\n"
        "      procedure: benjamini_hochberg\n"
        "      family: complete\n"
        "      alpha: '0.05'\n"
        "      table: results.csv\n"
        "      id_column: test_id\n"
        "      raw_pvalue_column: p_value\n"
        "      adjusted_pvalue_column: adjusted_p_value\n"
        "      call_column: significant\n",
        encoding="utf-8",
    )
    bundle = run_audit(
        repository,
        tmp_path / "competing-audit",
        schema_root,
        report="report.md",
        material_inputs=("bindings.yaml", "results.csv"),
    )

    assert bundle["deterministic_check_observations"] == []
    assert bundle["findings"] == []


def test_bh_sidecar_duplicate_identifier_and_na_remain_unsupported(
    schema_root: Path,
    tmp_path: Path,
) -> None:
    repository = _bh_sidecar_workspace(tmp_path)
    table = repository / "exported" / "tables" / "hypotheses.tsv"
    table.write_text(
        "called\tq_reported\tfeature_key\tnuisance\tp_raw\n"
        "true\t0.01\tgene_01\textra\t0.001\n"
        "false\tNA\tgene_01\textra\t0.2\n",
        encoding="utf-8",
    )
    bundle = run_audit(
        repository,
        tmp_path / "unsupported-sidecar-audit",
        schema_root,
        report="analysis-summary.md",
        material_inputs=(
            "configuration/review-bindings.yaml",
            "exported/tables/hypotheses.tsv",
        ),
    )

    observation = bundle["deterministic_check_observations"][0]
    assert observation["applicability"] == "unsupported"
    assert observation["comparison"]["outcome"] == "unknown"
    assert observation["operands"] == []
    assert bundle["findings"] == []


def test_unselected_calculation_sidecar_is_not_an_authority_source(
    schema_root: Path,
    tmp_path: Path,
) -> None:
    repository = _bh_sidecar_workspace(tmp_path)
    bundle = run_audit(
        repository,
        tmp_path / "unselected-sidecar-audit",
        schema_root,
        report="analysis-summary.md",
        material_inputs=("exported/tables/hypotheses.tsv",),
    )

    assert bundle["deterministic_check_observations"] == []
    assert bundle["findings"] == []


def test_duplicate_sidecar_check_ids_fail_locally_without_observation(
    schema_root: Path,
    tmp_path: Path,
) -> None:
    repository = _bh_sidecar_workspace(tmp_path)
    sidecar = repository / "configuration" / "review-bindings.yaml"
    original_entry = sidecar.read_text(encoding="utf-8").split("contracts:\n", maxsplit=1)[1]
    sidecar.write_text(
        "sc_referee_calculation_contracts: 1\ncontracts:\n" + original_entry + original_entry,
        encoding="utf-8",
    )
    output = tmp_path / "duplicate-sidecar-audit"
    bundle = run_audit(
        repository,
        output,
        schema_root,
        report="analysis-summary.md",
        material_inputs=(
            "configuration/review-bindings.yaml",
            "exported/tables/hypotheses.tsv",
        ),
    )

    assert bundle["deterministic_check_observations"] == []
    lock = json.loads((output / "semantic.lock.json").read_text(encoding="utf-8"))
    module = next(
        item
        for item in lock["calculation_check_registry"]["evaluation"]["modules"]
        if item["check_manifest"]["check_id"]
        == "calculation-check:benjamini-hochberg-complete-family-v1"
    )
    assert module["state"] == "adapter_failed"
    assert any("CalculationCheckContractError" in item for item in module["adapter_failures"])
    assert bundle["findings"] == []


def test_marked_over_budget_sidecar_fails_closed(
    schema_root: Path,
    tmp_path: Path,
) -> None:
    repository = _bh_sidecar_workspace(tmp_path)
    sidecar = repository / "configuration" / "review-bindings.yaml"
    sidecar.write_text(
        "sc_referee_calculation_contracts: 1\ncontracts: []\n" + "#" * (256 * 1024),
        encoding="utf-8",
    )
    bundle = run_audit(
        repository,
        tmp_path / "over-budget-sidecar-audit",
        schema_root,
        report="analysis-summary.md",
        material_inputs=(
            "configuration/review-bindings.yaml",
            "exported/tables/hypotheses.tsv",
        ),
    )

    assert bundle["deterministic_check_observations"] == []
    assert bundle["findings"] == []
