from __future__ import annotations

import csv
import gzip
from pathlib import Path

import pytest

from sc_referee.calculation_checks.core import CalculationCheckRegistry
from sc_referee.calculation_checks.hic_loop_strength import hic_loop_strength_registry
from sc_referee.controller import replay, run_audit


def _contract(*, claim_semantics: str = "loop_strength_delta") -> str:
    return f"""# Hi-C result

```sc-referee-hic-loop-strength-v1
contacts_table: contacts.csv
bins_table: bins.csv
results_table: results.csv
replicate_columns: [sample]
condition_column: condition
reference_level: control
test_level: treated
genome_assembly: hg38
resolution_bp: 20000
target_bin_i: b20
target_bin_j: b21
background_view_start: 0
background_view_end: 1200000
expected_model: cis_exact_distance_arithmetic_mean_target_excluded_v1
mask_policy: exclude_if_either_bin_masked_v1
zero_policy: dense_including_zeros
pseudocount: 0.0
target_statistic: single_pixel
replicate_functional: equal_weight_mean_log2_oe_v1
reported_delta_tolerance: 0.01
tolerance_authority: rounding_absolute_log2_ratio_delta
claim_semantics: {claim_semantics}
producer_binding: exact
```
"""


def _workspace(root: Path, *, reported_delta: float = -1.0, descriptive: bool = False) -> None:
    root.mkdir()
    (root / "report.md").write_text(
        _contract(
            claim_semantics="descriptive_contact_map" if descriptive else "loop_strength_delta"
        ),
        encoding="utf-8",
    )
    with (root / "bins.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["bin_id", "chrom", "start", "masked"])
        for index in range(60):
            writer.writerow([f"b{index}", "chr1", index * 20_000, "false"])
    with (root / "contacts.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["sample", "condition", "bin_i", "bin_j", "observed_count"])
        for sample, condition, target_count in (
            ("c1", "control", 20),
            ("c2", "control", 20),
            ("t1", "treated", 40),
            ("t2", "treated", 40),
        ):
            for index in range(59):
                count = target_count if index == 20 else 10
                writer.writerow([sample, condition, f"b{index}", f"b{index + 1}", count])
    (root / "results.csv").write_text(
        "genome_assembly,resolution_bp,bin_i,bin_j,reference,test,delta\n"
        f"hg38,20000,b20,b21,control,treated,{reported_delta}\n",
        encoding="utf-8",
    )


def _audit(workspace: Path, output: Path, schema_root: Path) -> dict[str, object]:
    return run_audit(
        workspace,
        output,
        schema_root,
        report="report.md",
        material_inputs=("contacts.csv", "bins.csv", "results.csv"),
        calculation_check_registry=hic_loop_strength_registry(),
    )


def _operand(observation: dict[str, object], name: str) -> object:
    operands = observation["operands"]
    assert isinstance(operands, list)
    return next(item["value"] for item in operands if item["name"] == name)


def test_reported_hic_delta_mismatch_is_disclosed_without_finding(
    schema_root: Path, tmp_path: Path
) -> None:
    workspace = tmp_path / "positive"
    _workspace(workspace, reported_delta=-1.0)

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
    assert _operand(observation, "background_pairs") == 58
    assert _operand(observation, "recomputed_delta") == 1.0
    assert _operand(observation, "reported_delta") == -1.0
    assert _operand(observation, "within_tolerance") is False
    assert any(
        "Hi-C loop-strength delta differs" in item["title"] for item in bundle["disclosures"]
    )


@pytest.mark.parametrize("compressed", [False, True], ids=("identity", "gzip"))
def test_selected_sidecar_layout_normalizes_to_same_hic_recompute(
    schema_root: Path, tmp_path: Path, compressed: bool
) -> None:
    workspace = tmp_path / "sidecar"
    _workspace(workspace, reported_delta=-1.0)
    (workspace / "report.md").write_text("# Hi-C result\n", encoding="utf-8")
    (workspace / "loop-contract.yaml").write_text(
        "sc_referee_calculation_contracts: 1\n"
        "contracts:\n"
        "  - check_id: calculation-check:hic-loop-strength-v1\n"
        "    contract:\n"
        "      contacts_table: contacts.csv\n"
        "      bins_table: bins.csv\n"
        "      results_table: results.csv\n"
        "      replicate_columns: [sample]\n"
        "      condition_column: condition\n"
        "      reference_level: control\n"
        "      test_level: treated\n"
        "      genome_assembly: hg38\n"
        "      resolution_bp: 20000\n"
        "      target_bin_i: b20\n"
        "      target_bin_j: b21\n"
        "      background_view_start: 0\n"
        "      background_view_end: 1200000\n"
        "      expected_model: cis_exact_distance_arithmetic_mean_target_excluded_v1\n"
        "      mask_policy: exclude_if_either_bin_masked_v1\n"
        "      zero_policy: dense_including_zeros\n"
        "      pseudocount: 0.0\n"
        "      target_statistic: single_pixel\n"
        "      replicate_functional: equal_weight_mean_log2_oe_v1\n"
        "      reported_delta_tolerance: 0.01\n"
        "      tolerance_authority: rounding_absolute_log2_ratio_delta\n"
        "      claim_semantics: loop_strength_delta\n"
        "      producer_binding: exact\n",
        encoding="utf-8",
    )
    selected_paths = ["loop-contract.yaml", "contacts.csv", "bins.csv", "results.csv"]
    if compressed:
        binding = workspace / "loop-contract.yaml"
        binding_text = binding.read_text(encoding="utf-8")
        for table_path in ("contacts.csv", "bins.csv", "results.csv"):
            source = workspace / table_path
            (workspace / f"{table_path}.gz").write_bytes(
                gzip.compress(source.read_bytes(), mtime=0)
            )
            source.unlink()
            binding_text = binding_text.replace(table_path, f"{table_path}.gz")
        binding.write_text(binding_text, encoding="utf-8")
        selected_paths = [
            "loop-contract.yaml",
            "contacts.csv.gz",
            "bins.csv.gz",
            "results.csv.gz",
        ]
    bundle = run_audit(
        workspace,
        tmp_path / "sidecar-audit",
        schema_root,
        report="report.md",
        material_inputs=tuple(selected_paths),
    )
    observation = next(
        item
        for item in bundle["deterministic_check_observations"]
        if item["check_manifest"]["check_id"] == "calculation-check:hic-loop-strength-v1"
    )
    assert observation["adapter_manifest"]["adapter_id"] == (
        "calculation-adapter:selected-sidecar-hic-loop-strength-v1"
    )
    assert observation["comparison"]["outcome"] == "nonconformant"
    assert _operand(observation, "background_pairs") == 58
    assert _operand(observation, "recomputed_delta") == 1.0


def test_matching_hic_delta_is_corrected_twin(schema_root: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "corrected"
    _workspace(workspace, reported_delta=1.0)

    bundle = _audit(workspace, tmp_path / "audit", schema_root)

    observation = bundle["deterministic_check_observations"][0]
    assert observation["comparison"]["outcome"] == "conformant"
    assert _operand(observation, "within_tolerance") is True


def test_descriptive_map_is_hard_negative(schema_root: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "descriptive"
    _workspace(workspace, descriptive=True)

    bundle = _audit(workspace, tmp_path / "audit", schema_root)

    observation = bundle["deterministic_check_observations"][0]
    assert observation["applicability"] == "not_applicable"
    assert observation["comparison"]["outcome"] == "not_applicable"


def test_incomplete_dense_stratum_abstains(schema_root: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "incomplete"
    _workspace(workspace)
    lines = (workspace / "contacts.csv").read_text(encoding="utf-8").splitlines()
    (workspace / "contacts.csv").write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")

    bundle = _audit(workspace, tmp_path / "audit", schema_root)

    observation = bundle["deterministic_check_observations"][0]
    assert observation["applicability"] == "unsupported"
    assert observation["operands"] == []
    assert bundle["findings"] == []


def test_module_removal_isolated(schema_root: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "removed"
    _workspace(workspace)
    bundle = run_audit(
        workspace,
        tmp_path / "audit",
        schema_root,
        report="report.md",
        material_inputs=("contacts.csv", "bins.csv", "results.csv"),
        calculation_check_registry=CalculationCheckRegistry((), profile_id="empty"),
    )
    assert bundle["deterministic_check_observations"] == []
