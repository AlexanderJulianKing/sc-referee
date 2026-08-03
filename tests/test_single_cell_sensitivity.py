from __future__ import annotations

import gzip
from pathlib import Path

import h5py
import numpy as np
import pytest

from sc_referee.calculation_checks import single_cell_sensitivity as sensitivity_module
from sc_referee.calculation_checks.core import CalculationCheckModule, CalculationCheckRegistry
from sc_referee.calculation_checks.profiles import default_calculation_check_registry
from sc_referee.calculation_checks.single_cell_sensitivity import (
    DeclaredSingleCellSensitivityAdapter,
    PyDESeq2SensitivityEngine,
    SelectedSidecarSingleCellSensitivityAdapter,
    SensitivityRecomputeInput,
    SensitivityRecomputeResult,
    SingleCellSensitivityError,
    single_cell_sensitivity_registry,
)
from sc_referee.controller import replay, run_audit


class _StubSensitivityEngine:
    engine_id = "sensitivity-engine:test-stub-v1"
    engine_version = "1.0.0"
    implementation_digest = "sha256:" + "2" * 64

    def __init__(self, adjusted: tuple[float | None, ...]) -> None:
        self.adjusted = adjusted
        self.calls = 0

    def recompute(self, request: SensitivityRecomputeInput) -> SensitivityRecomputeResult:
        self.calls += 1
        assert request.feature_ids == ("gene-a", "gene-b", "gene-c", "gene-d")
        assert request.levels == (
            "control",
            "control",
            "control",
            "treated",
            "treated",
            "treated",
        )
        return SensitivityRecomputeResult(
            feature_ids=request.feature_ids,
            adjusted_p_values=self.adjusted,
            standard_errors=(0.2, 0.2, 0.2, 0.2),
            n_reference=3,
            n_test=3,
            engine_id=self.engine_id,
            engine_version=self.engine_version,
        )


def _contract(*, reported_unit: str = "observation") -> str:
    return f"""# Results

```sc-referee-single-cell-sensitivity-v1
reported_table: results.csv
count_matrix: counts.h5ad
feature_id_column: feature
reported_adjusted_p_column: reported_padj
reported_effect_column: effect
matrix_feature_index: var/_index
replicate_field: obs/patient
condition_field: obs/condition
reference_level: control
test_level: treated
model: ~ condition
alpha: 0.05
reference_effect: 1.0
target_power: 0.8
minimum_powered_fraction: 0.8
reported_unit: {reported_unit}
producer_binding: unresolved
dependence_semantics: iid_rows
```
"""


def _write_workspace(root: Path, *, reported_unit: str = "observation") -> None:
    root.mkdir()
    (root / "report.md").write_text(_contract(reported_unit=reported_unit), encoding="utf-8")
    (root / "results.csv").write_text(
        "feature,reported_padj,effect\n"
        "gene-a,0.01,1.2\n"
        "gene-b,0.02,1.0\n"
        "gene-c,0.03,-1.1\n"
        "gene-d,0.8,0.1\n",
        encoding="utf-8",
    )
    string_dtype = h5py.string_dtype(encoding="utf-8")
    with h5py.File(root / "counts.h5ad", "w") as handle:
        handle.attrs["encoding-type"] = "anndata"
        matrix = handle.create_dataset(
            "X",
            data=np.asarray(
                [
                    [10, 4, 9, 2],
                    [11, 5, 8, 2],
                    [9, 4, 10, 3],
                    [30, 5, 2, 2],
                    [28, 6, 3, 1],
                    [32, 5, 2, 2],
                ],
                dtype=np.int64,
            ),
        )
        matrix.attrs["encoding-type"] = "array"
        obs = handle.create_group("obs")
        obs.attrs["encoding-type"] = "dataframe"
        obs.attrs["_index"] = "patient"
        obs.attrs["column-order"] = np.asarray(["condition"], dtype=object)
        patient = obs.create_dataset(
            "patient",
            data=np.asarray(["p1", "p2", "p3", "p4", "p5", "p6"], dtype=object),
            dtype=string_dtype,
        )
        patient.attrs["encoding-type"] = "string-array"
        condition = obs.create_dataset(
            "condition",
            data=np.asarray(
                ["control", "control", "control", "treated", "treated", "treated"],
                dtype=object,
            ),
            dtype=string_dtype,
        )
        condition.attrs["encoding-type"] = "string-array"
        var = handle.create_group("var")
        var.attrs["encoding-type"] = "dataframe"
        var.attrs["_index"] = "_index"
        var.attrs["column-order"] = np.asarray([], dtype=np.float64)
        index = var.create_dataset(
            "_index",
            data=np.asarray(["gene-a", "gene-b", "gene-c", "gene-d"], dtype=object),
            dtype=string_dtype,
        )
        index.attrs["encoding-type"] = "string-array"


def _operand(observation: dict[str, object], name: str) -> object:
    operands = observation["operands"]
    assert isinstance(operands, list)
    return next(item["value"] for item in operands if item["name"] == name)


def _audit(
    workspace: Path,
    output: Path,
    schema_root: Path,
    engine: _StubSensitivityEngine,
) -> dict[str, object]:
    adapter = DeclaredSingleCellSensitivityAdapter(engine=engine)
    return run_audit(
        workspace,
        output,
        schema_root,
        report="report.md",
        material_inputs=("counts.h5ad", "results.csv"),
        calculation_check_registry=single_cell_sensitivity_registry(adapter=adapter),
    )


def test_declared_observation_level_family_emits_bounded_sensitivity_disclosure(
    schema_root: Path, tmp_path: Path
) -> None:
    workspace = tmp_path / "workspace"
    _write_workspace(workspace)
    engine = _StubSensitivityEngine((0.01, 0.9, 0.02, 0.8))

    bundle = _audit(workspace, tmp_path / "audit", schema_root, engine)
    replayed = replay(tmp_path / "audit" / "semantic.lock.json", tmp_path / "replay", schema_root)
    for field in (
        "deterministic_check_observations",
        "material_questions",
        "disclosures",
        "findings",
        "coverage_records",
    ):
        assert replayed[field] == bundle[field]

    assert engine.calls == 1
    assert bundle["findings"] == []
    observation = bundle["deterministic_check_observations"][0]
    assert observation["applicability"] == "applicable"
    assert observation["comparison"]["outcome"] == "nonconformant"
    assert observation["output_ceiling"] == "disclosure_only"
    assert observation["production_finding_permitted"] is False
    assert _operand(observation, "reported_significant_testable") == 3
    assert _operand(observation, "replicate_level_survivors") == 2
    assert _operand(observation, "survival_rate") == 2 / 3
    assert _operand(observation, "powered_fraction") == 1.0
    assert _operand(observation, "recompute_powered") is True
    assert any(
        item["title"] == "Reported discoveries changed under replicate-level sensitivity analysis"
        for item in bundle["disclosures"]
    )


@pytest.mark.parametrize("compressed", [False, True], ids=("identity", "gzip"))
def test_selected_sidecar_layout_normalizes_to_same_sensitivity_recompute(
    schema_root: Path, tmp_path: Path, compressed: bool
) -> None:
    workspace = tmp_path / "sidecar"
    _write_workspace(workspace)
    (workspace / "report.md").write_text("# Results\n", encoding="utf-8")
    (workspace / "sensitivity-bindings.yaml").write_text(
        "sc_referee_calculation_contracts: 1\n"
        "contracts:\n"
        "  - check_id: calculation-check:single-cell-replicate-sensitivity-v1\n"
        "    contract:\n"
        "      reported_table: results.csv\n"
        "      count_matrix: counts.h5ad\n"
        "      feature_id_column: feature\n"
        "      reported_adjusted_p_column: reported_padj\n"
        "      reported_effect_column: effect\n"
        "      matrix_feature_index: var/_index\n"
        "      replicate_field: obs/patient\n"
        "      condition_field: obs/condition\n"
        "      reference_level: control\n"
        "      test_level: treated\n"
        "      model: '~ condition'\n"
        "      alpha: 0.05\n"
        "      reference_effect: 1.0\n"
        "      target_power: 0.8\n"
        "      minimum_powered_fraction: 0.8\n"
        "      reported_unit: observation\n"
        "      producer_binding: exact\n"
        "      dependence_semantics: iid_rows\n",
        encoding="utf-8",
    )
    results_path = "results.csv"
    if compressed:
        source = workspace / results_path
        (workspace / f"{results_path}.gz").write_bytes(gzip.compress(source.read_bytes(), mtime=0))
        source.unlink()
        binding = workspace / "sensitivity-bindings.yaml"
        binding.write_text(
            binding.read_text(encoding="utf-8").replace(results_path, f"{results_path}.gz"),
            encoding="utf-8",
        )
        results_path = f"{results_path}.gz"
    engine = _StubSensitivityEngine((0.01, 0.9, 0.02, 0.8))
    base = single_cell_sensitivity_registry(
        adapter=DeclaredSingleCellSensitivityAdapter(engine=engine)
    )
    registry = CalculationCheckRegistry(
        (
            CalculationCheckModule(
                base.modules[0].manifest,
                (SelectedSidecarSingleCellSensitivityAdapter(engine=engine),),
            ),
        ),
        profile_id="test-sidecar-single-cell-sensitivity",
    )
    bundle = run_audit(
        workspace,
        tmp_path / "sidecar-audit",
        schema_root,
        report="report.md",
        material_inputs=("sensitivity-bindings.yaml", "counts.h5ad", results_path),
        calculation_check_registry=registry,
    )
    observation = bundle["deterministic_check_observations"][0]
    assert observation["adapter_manifest"]["adapter_id"] == (
        "calculation-adapter:selected-sidecar-single-cell-replicate-sensitivity-v1"
    )
    assert observation["comparison"]["outcome"] == "nonconformant"
    assert _operand(observation, "replicate_level_survivors") == 2
    assert _operand(observation, "reported_significant_testable") == 3
    assert engine.calls == 1


def test_corrected_twin_is_conformant_and_hard_negative_does_not_recompute(
    schema_root: Path, tmp_path: Path
) -> None:
    corrected = tmp_path / "corrected"
    _write_workspace(corrected)
    corrected_engine = _StubSensitivityEngine((0.01, 0.02, 0.03, 0.8))
    corrected_bundle = _audit(
        corrected,
        tmp_path / "corrected-audit",
        schema_root,
        corrected_engine,
    )
    assert corrected_engine.calls == 1
    assert (
        corrected_bundle["deterministic_check_observations"][0]["comparison"]["outcome"]
        == "conformant"
    )
    assert not any(
        "changed under replicate-level" in item["title"] for item in corrected_bundle["disclosures"]
    )

    hard_negative = tmp_path / "hard-negative"
    _write_workspace(hard_negative, reported_unit="biological_replicate")
    hard_engine = _StubSensitivityEngine((0.01, 0.9, 0.02, 0.8))
    hard_bundle = _audit(
        hard_negative,
        tmp_path / "hard-negative-audit",
        schema_root,
        hard_engine,
    )
    assert hard_engine.calls == 0
    hard_observation = hard_bundle["deterministic_check_observations"][0]
    assert hard_observation["applicability"] == "not_applicable"
    assert hard_observation["comparison"]["outcome"] == "not_applicable"
    assert hard_bundle["findings"] == []


def test_unresolved_unit_and_mutated_column_abstain_without_numerical_claim(
    schema_root: Path, tmp_path: Path
) -> None:
    unresolved = tmp_path / "unresolved"
    _write_workspace(unresolved, reported_unit="unresolved")
    unresolved_engine = _StubSensitivityEngine((0.01, 0.9, 0.02, 0.8))
    unresolved_bundle = _audit(
        unresolved,
        tmp_path / "unresolved-audit",
        schema_root,
        unresolved_engine,
    )
    assert unresolved_engine.calls == 0
    unresolved_observation = unresolved_bundle["deterministic_check_observations"][0]
    assert unresolved_observation["applicability"] == "unsupported"
    assert unresolved_observation["comparison"]["outcome"] == "unknown"
    assert unresolved_observation["operands"] == []

    mutated = tmp_path / "mutated"
    _write_workspace(mutated)
    (mutated / "results.csv").write_text(
        "feature,wrong_column,effect\ngene-a,0.01,1.2\n",
        encoding="utf-8",
    )
    mutated_engine = _StubSensitivityEngine((0.01, 0.9, 0.02, 0.8))
    mutated_bundle = _audit(
        mutated,
        tmp_path / "mutated-audit",
        schema_root,
        mutated_engine,
    )
    assert mutated_engine.calls == 0
    mutated_observation = mutated_bundle["deterministic_check_observations"][0]
    assert mutated_observation["applicability"] == "unsupported"
    assert mutated_observation["comparison"]["outcome"] == "unknown"
    assert mutated_bundle["findings"] == []


def test_removing_single_cell_module_removes_only_its_observation(
    schema_root: Path, tmp_path: Path
) -> None:
    workspace = tmp_path / "workspace"
    _write_workspace(workspace)

    bundle = run_audit(
        workspace,
        tmp_path / "audit",
        schema_root,
        report="report.md",
        material_inputs=("counts.h5ad", "results.csv"),
        calculation_check_registry=CalculationCheckRegistry(()),
    )

    assert bundle["deterministic_check_observations"] == []
    assert bundle["findings"] == []


def test_default_registry_contains_frozen_single_cell_module() -> None:
    registry = default_calculation_check_registry()

    assert registry.profile_id == "deterministic_calculation_check_v13"
    assert {module.manifest.check_id for module in registry.modules} == {
        "calculation-check:benjamini-hochberg-complete-family-v1",
        "calculation-check:single-cell-replicate-sensitivity-v1",
        "calculation-check:effect-size-relevance-summary-v1",
        "calculation-check:tabular-design-integrity-v1",
        "calculation-check:r-count-model-compatibility-v1",
        "calculation-check:scanpy-selection-reuse-v1",
        "calculation-check:donor-eqtl-sign-v1",
        "calculation-check:hic-loop-strength-v1",
        "calculation-check:selected-sequence-record-boundary-v1",
        "calculation-check:selected-feature-identifier-identity-v1",
    }


def test_optional_recompute_dependency_failure_is_localized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unavailable(_name: str) -> object:
        raise ModuleNotFoundError("optional dependency absent")

    monkeypatch.setattr(sensitivity_module, "import_module", unavailable)
    request = SensitivityRecomputeInput(
        counts=np.asarray([[1], [2]], dtype=np.int64),
        feature_ids=("gene-a",),
        replicate_ids=("donor-a", "donor-b"),
        levels=("control", "treated"),
        condition_name="condition",
        reference_level="control",
        test_level="treated",
        model="~ condition",
    )

    with pytest.raises(
        SingleCellSensitivityError,
        match="optional single-cell recomputation dependencies are unavailable",
    ):
        PyDESeq2SensitivityEngine().recompute(request)


def test_live_workspace_drift_cannot_change_frozen_sensitivity_inputs(
    schema_root: Path, tmp_path: Path
) -> None:
    workspace = tmp_path / "workspace"
    _write_workspace(workspace)
    engine = _StubSensitivityEngine((0.01, 0.9, 0.02, 0.8))
    adapter = DeclaredSingleCellSensitivityAdapter(engine=engine)

    def mutate_after_snapshot(root: Path) -> None:
        (root / "results.csv").write_text(
            "feature,reported_padj,effect\ngene-d,0.01,9.0\n",
            encoding="utf-8",
        )

    bundle = run_audit(
        workspace,
        tmp_path / "audit",
        schema_root,
        report="report.md",
        material_inputs=("counts.h5ad", "results.csv"),
        calculation_check_registry=single_cell_sensitivity_registry(adapter=adapter),
        after_snapshot=mutate_after_snapshot,
    )

    observation = bundle["deterministic_check_observations"][0]
    assert _operand(observation, "reported_significant_testable") == 3
    assert bundle["repository_snapshots"][0]["live_workspace_state"]["status"] == (
        "workspace_diverged"
    )
    assert bundle["findings"] == []


def test_h5ad_axis_shape_mutation_abstains_locally(schema_root: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_workspace(workspace)
    with h5py.File(workspace / "counts.h5ad", "a") as handle:
        del handle["obs/condition"]
        field = handle["obs"].create_dataset(
            "condition",
            data=np.asarray(["control", "control"], dtype=object),
            dtype=h5py.string_dtype(encoding="utf-8"),
        )
        field.attrs["encoding-type"] = "string-array"
    engine = _StubSensitivityEngine((0.01, 0.9, 0.02, 0.8))

    bundle = _audit(workspace, tmp_path / "audit", schema_root, engine)

    assert engine.calls == 0
    observation = bundle["deterministic_check_observations"][0]
    assert observation["applicability"] == "unsupported"
    assert observation["comparison"]["outcome"] == "unknown"
    assert observation["operands"] == []
    assert bundle["findings"] == []
