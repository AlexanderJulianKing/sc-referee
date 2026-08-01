from __future__ import annotations

from pathlib import Path

from sc_referee.calculation_checks.core import CalculationCheckRegistry
from sc_referee.calculation_checks.design_integrity import design_integrity_registry
from sc_referee.controller import run_audit


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
