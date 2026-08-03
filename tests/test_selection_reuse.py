from __future__ import annotations

from pathlib import Path

from sc_referee.calculation_checks.core import CalculationCheckRegistry
from sc_referee.calculation_checks.selection_reuse import selection_reuse_registry
from sc_referee.controller import replay, run_audit


def _contract(
    *,
    selection_object: str = "adata",
    test_object: str = "adata",
    analysis_mode: str = "de_novo_marker_inference",
    relationship: str = "same_expression_object",
    safeguard: str = "none",
) -> str:
    return f"""# Marker analysis

```sc-referee-selection-reuse-v1
source_file: analysis.py
results_table: markers.csv
selection_object: {selection_object}
test_object: {test_object}
groupby_key: leiden
pvalue_column: pvals_adj
analysis_mode: {analysis_mode}
data_relationship: {relationship}
safeguard: {safeguard}
producer_binding: exact
```
"""


def _source(*, test_object: str = "adata") -> str:
    return (
        "import scanpy as sc\n"
        "adata = load_data()\n"
        + ("heldout = load_heldout_data()\n" if test_object == "heldout" else "")
        + "sc.pp.neighbors(adata)\n"
        "sc.tl.leiden(adata)\n"
        f"sc.tl.rank_genes_groups({test_object}, groupby='leiden')\n"
    )


def _workspace(root: Path, *, report: str | None = None, source: str | None = None) -> None:
    root.mkdir()
    (root / "report.md").write_text(report or _contract(), encoding="utf-8")
    (root / "analysis.py").write_text(source or _source(), encoding="utf-8")
    (root / "markers.csv").write_text(
        "gene,pvals_adj,score\ngene-a,0.01,4.2\ngene-b,0.2,1.1\n",
        encoding="utf-8",
    )


def _audit(workspace: Path, output: Path, schema_root: Path) -> dict[str, object]:
    return run_audit(
        workspace,
        output,
        schema_root,
        report="report.md",
        material_inputs=("analysis.py", "markers.csv"),
        calculation_check_registry=selection_reuse_registry(),
    )


def _operand(observation: dict[str, object], name: str) -> object:
    operands = observation["operands"]
    assert isinstance(operands, list)
    return next(item["value"] for item in operands if item["name"] == name)


def test_same_object_selection_and_marker_testing_is_disclosed_without_finding(
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
    assert _operand(observation, "same_expression_object_reused") is True
    assert _operand(observation, "calibrated_pvalue_count") == 2
    assert _operand(observation, "neighbors_line") < _operand(observation, "cluster_line")
    assert _operand(observation, "cluster_line") < _operand(observation, "marker_test_line")
    assert any("reused for de-novo clustering" in item["title"] for item in bundle["disclosures"])


def test_selected_sidecar_layout_normalizes_to_same_selection_reuse_pattern(
    schema_root: Path, tmp_path: Path
) -> None:
    workspace = tmp_path / "sidecar"
    _workspace(workspace)
    (workspace / "report.md").write_text("# Marker analysis\n", encoding="utf-8")
    (workspace / "review.yaml").write_text(
        "sc_referee_calculation_contracts: 1\n"
        "contracts:\n"
        "  - check_id: calculation-check:scanpy-selection-reuse-v1\n"
        "    contract:\n"
        "      source_file: analysis.py\n"
        "      results_table: markers.csv\n"
        "      selection_object: adata\n"
        "      test_object: adata\n"
        "      groupby_key: leiden\n"
        "      pvalue_column: pvals_adj\n"
        "      analysis_mode: de_novo_marker_inference\n"
        "      data_relationship: same_expression_object\n"
        "      safeguard: none\n"
        "      producer_binding: exact\n",
        encoding="utf-8",
    )
    bundle = run_audit(
        workspace,
        tmp_path / "sidecar-audit",
        schema_root,
        report="report.md",
        material_inputs=("review.yaml", "analysis.py", "markers.csv"),
    )
    observation = next(
        item
        for item in bundle["deterministic_check_observations"]
        if item["check_manifest"]["check_id"] == "calculation-check:scanpy-selection-reuse-v1"
    )
    assert observation["adapter_manifest"]["adapter_id"] == (
        "calculation-adapter:selected-sidecar-scanpy-selection-reuse-v1"
    )
    assert observation["comparison"]["outcome"] == "nonconformant"
    assert _operand(observation, "same_expression_object_reused") is True
    assert _operand(observation, "calibrated_pvalue_count") == 2


def test_disjoint_heldout_object_is_corrected_twin(schema_root: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "heldout"
    _workspace(
        workspace,
        report=_contract(
            test_object="heldout",
            relationship="disjoint_heldout_expression",
        ),
        source=_source(test_object="heldout"),
    )

    bundle = _audit(workspace, tmp_path / "audit", schema_root)

    observation = bundle["deterministic_check_observations"][0]
    assert observation["comparison"]["outcome"] == "conformant"
    assert _operand(observation, "same_expression_object_reused") is False


def test_predefined_and_descriptive_modes_are_hard_negatives(
    schema_root: Path, tmp_path: Path
) -> None:
    for mode in ("predefined_group_inference", "descriptive_marker_ranking"):
        workspace = tmp_path / mode
        _workspace(workspace, report=_contract(analysis_mode=mode))
        bundle = _audit(workspace, tmp_path / f"{mode}-audit", schema_root)
        observation = bundle["deterministic_check_observations"][0]
        assert observation["applicability"] == "not_applicable"
        assert observation["comparison"]["outcome"] == "not_applicable"


def test_safeguard_and_ambiguous_source_abstain(schema_root: Path, tmp_path: Path) -> None:
    safeguarded = tmp_path / "safeguarded"
    _workspace(safeguarded, report=_contract(safeguard="selection_aware"))
    safeguard_bundle = _audit(safeguarded, tmp_path / "safeguard-audit", schema_root)
    assert safeguard_bundle["deterministic_check_observations"][0]["applicability"] == "unsupported"

    repeated = tmp_path / "repeated"
    _workspace(repeated, source=_source() + "sc.tl.rank_genes_groups(adata, groupby='leiden')\n")
    repeated_bundle = _audit(repeated, tmp_path / "repeated-audit", schema_root)
    repeated_observation = repeated_bundle["deterministic_check_observations"][0]
    assert repeated_observation["applicability"] == "unsupported"
    assert repeated_observation["operands"] == []


def test_module_removal_isolated(schema_root: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "removed"
    _workspace(workspace)
    bundle = run_audit(
        workspace,
        tmp_path / "audit",
        schema_root,
        report="report.md",
        material_inputs=("analysis.py", "markers.csv"),
        calculation_check_registry=CalculationCheckRegistry((), profile_id="empty"),
    )
    assert bundle["deterministic_check_observations"] == []
