from __future__ import annotations

import gzip
from pathlib import Path

import pytest

from sc_referee.calculation_checks.core import CalculationCheckRegistry
from sc_referee.calculation_checks.design_integrity import design_integrity_registry
from sc_referee.controller import replay, run_audit


def _contract(
    *,
    comparison_mode: str = "unpaired",
    aggregation_columns: str = "[donor, lane]",
    fitted_fixed: str = "[condition]",
    aggregation_binding: str = "exact",
) -> str:
    pairing = "[donor]" if comparison_mode == "paired" else "[]"
    return f"""# Bound differential-expression design

```sc-referee-design-integrity-v1
metadata_table: metadata.csv
condition_column: condition
reference_level: control
test_level: treated
replicate_columns: [donor]
pairing_columns: {pairing}
aggregation_columns: {aggregation_columns}
required_categorical_adjustment_columns: [batch]
fitted_fixed_effect_columns: {fitted_fixed}
fitted_random_intercept_columns: []
comparison_mode: {comparison_mode}
aggregation_binding: {aggregation_binding}
model_binding: exact
```
"""


def _workspace(
    root: Path,
    *,
    report: str | None = None,
    metadata: str | None = None,
) -> None:
    root.mkdir()
    (root / "report.md").write_text(report or _contract(), encoding="utf-8")
    (root / "metadata.csv").write_text(
        metadata
        or (
            "cell,donor,condition,batch,lane\n"
            "c1,d1,control,b1,l1\n"
            "c2,d1,treated,b2,l1\n"
            "c3,d2,control,b1,l1\n"
            "c4,d2,treated,b2,l1\n"
            "c5,d3,control,b1,\n"
        ),
        encoding="utf-8",
    )


def _audit(workspace: Path, output: Path, schema_root: Path) -> dict[str, object]:
    return run_audit(
        workspace,
        output,
        schema_root,
        report="report.md",
        material_inputs=("metadata.csv",),
        calculation_check_registry=design_integrity_registry(),
    )


def _operand(observation: dict[str, object], name: str) -> object:
    operands = observation["operands"]
    assert isinstance(operands, list)
    return next(item["value"] for item in operands if item["name"] == name)


def test_exact_design_incompatibilities_are_reported_without_finding(
    schema_root: Path, tmp_path: Path
) -> None:
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
    assert _operand(observation, "missing_aggregation_rows") == 1
    assert _operand(observation, "merged_aggregation_groups") == 2
    assert _operand(observation, "complete_pairing_levels") == 2
    assert _operand(observation, "pairing_omitted") is True
    assert _operand(observation, "required_adjustments_omitted") == ["batch"]
    assert _operand(observation, "condition_aliased_with_required_adjustments") is True
    assert any(
        item["title"] == "Declared design contains exact structural incompatibilities"
        for item in bundle["disclosures"]
    )


@pytest.mark.parametrize("compressed", [False, True], ids=("identity", "gzip"))
def test_selected_sidecar_layout_normalizes_to_same_design_metrics(
    schema_root: Path, tmp_path: Path, compressed: bool
) -> None:
    workspace = tmp_path / "sidecar"
    _workspace(workspace)
    (workspace / "report.md").write_text(
        "# Bound differential-expression design\n", encoding="utf-8"
    )
    (workspace / "design-bindings.yaml").write_text(
        "sc_referee_calculation_contracts: 1\n"
        "contracts:\n"
        "  - check_id: calculation-check:tabular-design-integrity-v1\n"
        "    contract:\n"
        "      metadata_table: metadata.csv\n"
        "      condition_column: condition\n"
        "      reference_level: control\n"
        "      test_level: treated\n"
        "      replicate_columns: [donor]\n"
        "      pairing_columns: []\n"
        "      aggregation_columns: [donor, lane]\n"
        "      required_categorical_adjustment_columns: [batch]\n"
        "      fitted_fixed_effect_columns: [condition]\n"
        "      fitted_random_intercept_columns: []\n"
        "      comparison_mode: unpaired\n"
        "      aggregation_binding: exact\n"
        "      model_binding: exact\n",
        encoding="utf-8",
    )
    metadata_path = "metadata.csv"
    if compressed:
        source = workspace / metadata_path
        (workspace / f"{metadata_path}.gz").write_bytes(gzip.compress(source.read_bytes(), mtime=0))
        source.unlink()
        binding = workspace / "design-bindings.yaml"
        binding.write_text(
            binding.read_text(encoding="utf-8").replace(metadata_path, f"{metadata_path}.gz"),
            encoding="utf-8",
        )
        metadata_path = f"{metadata_path}.gz"
    bundle = run_audit(
        workspace,
        tmp_path / "sidecar-audit",
        schema_root,
        report="report.md",
        material_inputs=("design-bindings.yaml", metadata_path),
    )
    observation = next(
        item
        for item in bundle["deterministic_check_observations"]
        if item["check_manifest"]["check_id"] == "calculation-check:tabular-design-integrity-v1"
    )
    assert observation["adapter_manifest"]["adapter_id"] == (
        "calculation-adapter:selected-sidecar-tabular-design-integrity-v1"
    )
    assert observation["comparison"]["outcome"] == "nonconformant"
    assert _operand(observation, "missing_aggregation_rows") == 1
    assert _operand(observation, "required_adjustments_omitted") == ["batch"]


def test_corrected_paired_design_is_conformant(schema_root: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "corrected"
    _workspace(
        workspace,
        report=_contract(
            comparison_mode="paired",
            aggregation_columns="[donor, condition]",
            fitted_fixed="[condition, batch]",
        ),
        metadata=(
            "cell,donor,condition,batch\n"
            "c1,d1,control,b1\n"
            "c2,d1,treated,b1\n"
            "c3,d2,control,b2\n"
            "c4,d2,treated,b2\n"
        ),
    )

    bundle = _audit(workspace, tmp_path / "audit", schema_root)

    observation = bundle["deterministic_check_observations"][0]
    assert observation["comparison"]["outcome"] == "conformant"
    assert _operand(observation, "complete_pairing_levels") == 2
    assert _operand(observation, "merged_aggregation_groups") == 0
    assert _operand(observation, "condition_aliased_with_required_adjustments") is False


def test_genuinely_unpaired_design_is_hard_negative(schema_root: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "unpaired"
    _workspace(
        workspace,
        report=_contract(
            comparison_mode="unpaired",
            aggregation_columns="[donor]",
            fitted_fixed="[condition, batch]",
        ),
        metadata=(
            "cell,donor,condition,batch\n"
            "c1,d1,control,b1\n"
            "c2,d2,control,b2\n"
            "c3,d3,treated,b1\n"
            "c4,d4,treated,b2\n"
        ),
    )

    bundle = _audit(workspace, tmp_path / "audit", schema_root)

    observation = bundle["deterministic_check_observations"][0]
    assert observation["comparison"]["outcome"] == "conformant"
    assert _operand(observation, "complete_pairing_levels") == 0
    assert _operand(observation, "pairing_omitted") is False


def test_unresolved_binding_and_missing_pair_identity_abstain(
    schema_root: Path, tmp_path: Path
) -> None:
    unresolved = tmp_path / "unresolved"
    _workspace(unresolved, report=_contract(aggregation_binding="unresolved"))
    unresolved_bundle = _audit(unresolved, tmp_path / "unresolved-audit", schema_root)
    assert (
        unresolved_bundle["deterministic_check_observations"][0]["applicability"] == "unsupported"
    )

    missing = tmp_path / "missing"
    _workspace(
        missing,
        report=_contract(
            comparison_mode="paired",
            aggregation_columns="[donor, condition]",
            fitted_fixed="[condition, batch]",
        ),
        metadata=("cell,donor,condition,batch\nc1,d1,control,b1\nc2,,treated,b1\n"),
    )
    missing_bundle = _audit(missing, tmp_path / "missing-audit", schema_root)
    missing_observation = missing_bundle["deterministic_check_observations"][0]
    assert missing_observation["applicability"] == "unsupported"
    assert missing_observation["operands"] == []
    assert missing_bundle["findings"] == []


def test_module_removal_and_unselected_metadata_are_isolated(
    schema_root: Path, tmp_path: Path
) -> None:
    unselected = tmp_path / "unselected"
    _workspace(unselected)
    unselected_bundle = run_audit(
        unselected,
        tmp_path / "unselected-audit",
        schema_root,
        report="report.md",
        calculation_check_registry=design_integrity_registry(),
    )
    assert (
        unselected_bundle["deterministic_check_observations"][0]["applicability"] == "unsupported"
    )

    removed = tmp_path / "removed"
    _workspace(removed)
    removed_bundle = run_audit(
        removed,
        tmp_path / "removed-audit",
        schema_root,
        report="report.md",
        material_inputs=("metadata.csv",),
        calculation_check_registry=CalculationCheckRegistry((), profile_id="empty"),
    )
    assert removed_bundle["deterministic_check_observations"] == []
