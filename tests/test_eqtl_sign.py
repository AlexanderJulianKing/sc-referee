from __future__ import annotations

from pathlib import Path

from sc_referee.calculation_checks.core import CalculationCheckRegistry
from sc_referee.calculation_checks.eqtl_sign import eqtl_sign_registry
from sc_referee.controller import run_audit


def _contract(*, orientation_binding: str = "exact") -> str:
    return f"""# eQTL result

```sc-referee-eqtl-sign-v1
donor_table: donors.csv
results_table: results.csv
donor_id_column: donor
genotype_column: dosage
expression_column: expression
result_feature_column: feature
result_effect_column: effect
variant_id: rs-test
target_feature: GENE1
variant_alleles: [A, G]
dosage_counts_allele: A
effect_allele: G
dosage_ploidy: 2
estimator: ols_with_intercept
outcome_scale: log2_cpm_plus_1
minimum_donors_per_supported_class: 3
producer_binding: exact
orientation_binding: {orientation_binding}
```
"""


def _donors() -> str:
    rows = ["donor,dosage,expression"]
    index = 0
    for dosage in (0, 1, 2):
        for repeat in range(3):
            index += 1
            # Expression rises with A dosage, hence falls after complementing to G dosage.
            rows.append(f"d{index},{dosage},{2 + dosage + repeat * 0.05}")
    return "\n".join(rows) + "\n"


def _workspace(root: Path, *, effect: float = 0.8, orientation_binding: str = "exact") -> None:
    root.mkdir()
    (root / "report.md").write_text(
        _contract(orientation_binding=orientation_binding), encoding="utf-8"
    )
    (root / "donors.csv").write_text(_donors(), encoding="utf-8")
    (root / "results.csv").write_text(
        f"feature,effect\nGENE1,{effect}\nOTHER,0.2\n", encoding="utf-8"
    )


def _audit(workspace: Path, output: Path, schema_root: Path) -> dict[str, object]:
    return run_audit(
        workspace,
        output,
        schema_root,
        report="report.md",
        material_inputs=("donors.csv", "results.csv"),
        calculation_check_registry=eqtl_sign_registry(),
    )


def _operand(observation: dict[str, object], name: str) -> object:
    operands = observation["operands"]
    assert isinstance(operands, list)
    return next(item["value"] for item in operands if item["name"] == name)


def test_oriented_donor_slope_detects_reported_sign_disagreement(
    schema_root: Path, tmp_path: Path
) -> None:
    workspace = tmp_path / "positive"
    _workspace(workspace, effect=0.8)

    bundle = _audit(workspace, tmp_path / "audit", schema_root)

    assert bundle["findings"] == []
    observation = bundle["deterministic_check_observations"][0]
    assert observation["comparison"]["outcome"] == "nonconformant"
    assert _operand(observation, "orientation_transform") == "diploid_complement"
    assert _operand(observation, "donor_count") == 9
    assert _operand(observation, "genotype_class_counts") == [3, 3, 3]
    assert _operand(observation, "reported_sign") == 1
    assert _operand(observation, "recomputed_sign") == -1
    assert any("eQTL direction differs" in item["title"] for item in bundle["disclosures"])


def test_matching_reported_sign_is_corrected_twin(schema_root: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "corrected"
    _workspace(workspace, effect=-0.8)

    bundle = _audit(workspace, tmp_path / "audit", schema_root)

    observation = bundle["deterministic_check_observations"][0]
    assert observation["comparison"]["outcome"] == "conformant"
    assert _operand(observation, "sign_agreement") is True


def test_unresolved_orientation_and_insufficient_classes_abstain(
    schema_root: Path, tmp_path: Path
) -> None:
    unresolved = tmp_path / "unresolved"
    _workspace(unresolved, orientation_binding="unresolved")
    unresolved_bundle = _audit(unresolved, tmp_path / "unresolved-audit", schema_root)
    assert (
        unresolved_bundle["deterministic_check_observations"][0]["applicability"] == "unsupported"
    )

    sparse = tmp_path / "sparse"
    _workspace(sparse)
    (sparse / "donors.csv").write_text(
        "donor,dosage,expression\nd1,0,1\nd2,0,2\nd3,0,3\nd4,1,4\n",
        encoding="utf-8",
    )
    sparse_bundle = _audit(sparse, tmp_path / "sparse-audit", schema_root)
    sparse_observation = sparse_bundle["deterministic_check_observations"][0]
    assert sparse_observation["applicability"] == "unsupported"
    assert sparse_observation["operands"] == []


def test_module_removal_isolated(schema_root: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "removed"
    _workspace(workspace)
    bundle = run_audit(
        workspace,
        tmp_path / "audit",
        schema_root,
        report="report.md",
        material_inputs=("donors.csv", "results.csv"),
        calculation_check_registry=CalculationCheckRegistry((), profile_id="empty"),
    )
    assert bundle["deterministic_check_observations"] == []
