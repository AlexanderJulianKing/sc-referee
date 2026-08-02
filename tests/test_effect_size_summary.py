from __future__ import annotations

import gzip
from pathlib import Path

import pytest

from sc_referee.calculation_checks.core import CalculationCheckRegistry
from sc_referee.calculation_checks.effect_size_summary import effect_size_summary_registry
from sc_referee.calculation_checks.profiles import default_calculation_check_registry
from sc_referee.controller import replay, run_audit


def _contract(
    *,
    claim_semantics: str = "biologically_relevant_discovery",
    producer_binding: str = "exact",
) -> str:
    return f"""# Differential expression result

```sc-referee-effect-size-summary-v1
reported_table: results.csv
feature_id_column: feature
adjusted_p_column: padj
effect_column: log2fc
alpha: 0.05
effect_threshold: 0.5
effect_scale: log2_fold_change
claim_semantics: {claim_semantics}
producer_binding: {producer_binding}
```
"""


def _workspace(
    root: Path,
    *,
    claim_semantics: str = "biologically_relevant_discovery",
    producer_binding: str = "exact",
) -> None:
    root.mkdir()
    (root / "report.md").write_text(
        _contract(claim_semantics=claim_semantics, producer_binding=producer_binding),
        encoding="utf-8",
    )
    (root / "results.csv").write_text(
        "feature,padj,log2fc\n"
        "gene-a,0.01,1.2\n"
        "gene-b,0.02,0.1\n"
        "gene-c,0.04,-0.4\n"
        "gene-d,0.8,0.01\n",
        encoding="utf-8",
    )


def _audit(workspace: Path, output: Path, schema_root: Path) -> dict[str, object]:
    return run_audit(
        workspace,
        output,
        schema_root,
        report="report.md",
        material_inputs=("results.csv",),
        calculation_check_registry=effect_size_summary_registry(),
    )


def _operand(observation: dict[str, object], name: str) -> object:
    operands = observation["operands"]
    assert isinstance(operands, list)
    return next(item["value"] for item in operands if item["name"] == name)


def test_declared_relevance_floor_emits_exact_disclosure(schema_root: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "positive"
    _workspace(workspace)

    bundle = _audit(workspace, tmp_path / "audit", schema_root)
    replayed = replay(tmp_path / "audit" / "semantic.lock.json", tmp_path / "replay", schema_root)
    for field in (
        "deterministic_check_observations",
        "material_questions",
        "disclosures",
        "findings",
        "coverage_records",
    ):
        assert replayed[field] == bundle[field]

    assert bundle["findings"] == []
    observation = bundle["deterministic_check_observations"][0]
    assert observation["comparison"]["outcome"] == "nonconformant"
    assert observation["output_ceiling"] == "disclosure_only"
    assert observation["production_finding_permitted"] is False
    assert _operand(observation, "significant_discoveries") == 3
    assert _operand(observation, "below_threshold_discoveries") == 2
    assert _operand(observation, "below_threshold_fraction") == 2 / 3
    assert any(
        item["title"] == "Declared discoveries include effects below the relevance floor"
        for item in bundle["disclosures"]
    )


def test_corrected_twin_is_conformant(schema_root: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "corrected"
    _workspace(workspace)
    (workspace / "results.csv").write_text(
        "feature,padj,log2fc\n"
        "gene-a,0.01,1.2\n"
        "gene-b,0.02,0.7\n"
        "gene-c,0.04,-0.6\n"
        "gene-d,0.8,0.01\n",
        encoding="utf-8",
    )

    bundle = _audit(workspace, tmp_path / "audit", schema_root)

    assert bundle["deterministic_check_observations"][0]["comparison"]["outcome"] == "conformant"
    assert not any("relevance floor" in item["title"] for item in bundle["disclosures"])


def test_significance_only_is_hard_negative(schema_root: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "hard-negative"
    _workspace(workspace, claim_semantics="statistical_significance_only")

    bundle = _audit(workspace, tmp_path / "audit", schema_root)

    observation = bundle["deterministic_check_observations"][0]
    assert observation["applicability"] == "not_applicable"
    assert observation["comparison"]["outcome"] == "not_applicable"
    assert bundle["findings"] == []


def test_unresolved_binding_and_missing_effect_abstain(schema_root: Path, tmp_path: Path) -> None:
    unresolved = tmp_path / "unresolved"
    _workspace(unresolved, producer_binding="unresolved")
    unresolved_bundle = _audit(unresolved, tmp_path / "unresolved-audit", schema_root)
    assert (
        unresolved_bundle["deterministic_check_observations"][0]["applicability"] == "unsupported"
    )

    missing = tmp_path / "missing"
    _workspace(missing)
    (missing / "results.csv").write_text(
        "feature,padj,log2fc\ngene-a,0.01,\n",
        encoding="utf-8",
    )
    missing_bundle = _audit(missing, tmp_path / "missing-audit", schema_root)
    missing_observation = missing_bundle["deterministic_check_observations"][0]
    assert missing_observation["applicability"] == "unsupported"
    assert missing_observation["operands"] == []
    assert missing_bundle["findings"] == []


def test_unselected_table_and_module_removal_do_not_run(schema_root: Path, tmp_path: Path) -> None:
    unselected = tmp_path / "unselected"
    _workspace(unselected)
    bundle = run_audit(
        unselected,
        tmp_path / "unselected-audit",
        schema_root,
        report="report.md",
        calculation_check_registry=effect_size_summary_registry(),
    )
    assert bundle["deterministic_check_observations"][0]["applicability"] == "unsupported"

    removed = tmp_path / "removed"
    _workspace(removed)
    removed_bundle = run_audit(
        removed,
        tmp_path / "removed-audit",
        schema_root,
        report="report.md",
        material_inputs=("results.csv",),
        calculation_check_registry=CalculationCheckRegistry((), profile_id="empty"),
    )
    assert removed_bundle["deterministic_check_observations"] == []


def test_default_registry_contains_frozen_effect_size_module() -> None:
    registry = default_calculation_check_registry()
    assert [module.manifest.check_id for module in registry.modules] == [
        "calculation-check:benjamini-hochberg-complete-family-v1",
        "calculation-check:single-cell-replicate-sensitivity-v1",
        "calculation-check:effect-size-relevance-summary-v1",
        "calculation-check:tabular-design-integrity-v1",
        "calculation-check:r-count-model-compatibility-v1",
        "calculation-check:scanpy-selection-reuse-v1",
        "calculation-check:donor-eqtl-sign-v1",
        "calculation-check:hic-loop-strength-v1",
    ]


@pytest.mark.parametrize("compressed", [False, True], ids=("identity", "gzip"))
def test_selected_sidecar_layout_normalizes_to_same_effect_summary(
    schema_root: Path, tmp_path: Path, compressed: bool
) -> None:
    workspace = tmp_path / "sidecar"
    _workspace(workspace)
    (workspace / "report.md").write_text("# Differential expression result\n", encoding="utf-8")
    (workspace / "bindings.yml").write_text(
        "sc_referee_calculation_contracts: 1\n"
        "contracts:\n"
        "  - check_id: calculation-check:effect-size-relevance-summary-v1\n"
        "    contract:\n"
        "      reported_table: results.csv\n"
        "      feature_id_column: feature\n"
        "      adjusted_p_column: padj\n"
        "      effect_column: log2fc\n"
        "      alpha: 0.05\n"
        "      effect_threshold: 0.5\n"
        "      effect_scale: log2_fold_change\n"
        "      claim_semantics: biologically_relevant_discovery\n"
        "      producer_binding: exact\n",
        encoding="utf-8",
    )
    results_path = "results.csv"
    if compressed:
        source = workspace / results_path
        (workspace / f"{results_path}.gz").write_bytes(gzip.compress(source.read_bytes(), mtime=0))
        source.unlink()
        binding = workspace / "bindings.yml"
        binding.write_text(
            binding.read_text(encoding="utf-8").replace(results_path, f"{results_path}.gz"),
            encoding="utf-8",
        )
        results_path = f"{results_path}.gz"

    bundle = run_audit(
        workspace,
        tmp_path / "sidecar-audit",
        schema_root,
        report="report.md",
        material_inputs=("bindings.yml", results_path),
    )
    observation = next(
        item
        for item in bundle["deterministic_check_observations"]
        if item["check_manifest"]["check_id"]
        == "calculation-check:effect-size-relevance-summary-v1"
    )
    assert observation["adapter_manifest"]["adapter_id"] == (
        "calculation-adapter:selected-sidecar-effect-size-summary-v1"
    )
    assert observation["comparison"]["outcome"] == "nonconformant"
    assert _operand(observation, "significant_discoveries") == 3
    assert _operand(observation, "below_threshold_discoveries") == 2
