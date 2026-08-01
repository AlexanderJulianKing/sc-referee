from __future__ import annotations

from pathlib import Path

from sc_referee.calculation_checks.core import CalculationCheckRegistry
from sc_referee.calculation_checks.count_model_compatibility import (
    count_model_compatibility_registry,
)
from sc_referee.controller import run_audit


def _contract(
    *,
    producer_call: str = "stats::t.test",
    response_scale: str = "raw_counts",
    requirement: str = "count_likelihood",
    binding: str = "exact",
) -> str:
    return f"""# Bound model

```sc-referee-count-model-compatibility-v1
source_file: analysis.R
producer_call: {producer_call}
response_scale: {response_scale}
required_method_family: {requirement}
producer_binding: {binding}
```
"""


def _workspace(root: Path, *, report: str | None = None, source: str | None = None) -> Path:
    root.mkdir()
    (root / "report.md").write_text(report or _contract(), encoding="utf-8")
    marker = root / "must-not-exist"
    (root / "analysis.R").write_text(
        source
        or (
            "result <- stats::t.test(raw_counts[, 1], raw_counts[, 2])\n"
            f"system('touch {marker.as_posix()}')\n"
        ),
        encoding="utf-8",
    )
    return marker


def _audit(workspace: Path, output: Path, schema_root: Path) -> dict[str, object]:
    return run_audit(
        workspace,
        output,
        schema_root,
        report="report.md",
        material_inputs=("analysis.R",),
        calculation_check_registry=count_model_compatibility_registry(),
    )


def _operand(observation: dict[str, object], name: str) -> object:
    operands = observation["operands"]
    assert isinstance(operands, list)
    return next(item["value"] for item in operands if item["name"] == name)


def test_raw_counts_with_generic_test_is_disclosed_without_execution_or_finding(
    schema_root: Path, tmp_path: Path
) -> None:
    workspace = tmp_path / "positive"
    marker = _workspace(workspace)

    bundle = _audit(workspace, tmp_path / "audit", schema_root)

    assert not marker.exists()
    assert bundle["findings"] == []
    observation = bundle["deterministic_check_observations"][0]
    assert observation["comparison"]["outcome"] == "nonconformant"
    assert _operand(observation, "observed_method_family") == "generic_continuous_location_test"
    assert _operand(observation, "method_scale_compatible") is False
    assert any(
        item["title"] == "Bound R producer method is incompatible with the declared response scale"
        for item in bundle["disclosures"]
    )


def test_negative_binomial_count_model_is_conformant(schema_root: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "count-model"
    _workspace(
        workspace,
        report=_contract(producer_call="DESeq2::DESeq"),
        source="fit <- DESeq2::DESeq(dds)\n",
    )

    bundle = _audit(workspace, tmp_path / "audit", schema_root)

    observation = bundle["deterministic_check_observations"][0]
    assert observation["comparison"]["outcome"] == "conformant"
    assert _operand(observation, "method_scale_compatible") is True


def test_transformed_response_with_continuous_model_is_hard_negative(
    schema_root: Path, tmp_path: Path
) -> None:
    workspace = tmp_path / "continuous"
    _workspace(
        workspace,
        report=_contract(
            response_scale="transformed_continuous",
            requirement="continuous_location_model",
        ),
    )

    bundle = _audit(workspace, tmp_path / "audit", schema_root)

    assert bundle["deterministic_check_observations"][0]["comparison"]["outcome"] == "conformant"


def test_unresolved_or_repeated_producer_abstains(schema_root: Path, tmp_path: Path) -> None:
    unresolved = tmp_path / "unresolved"
    _workspace(unresolved, report=_contract(binding="unresolved"))
    unresolved_bundle = _audit(unresolved, tmp_path / "unresolved-audit", schema_root)
    assert (
        unresolved_bundle["deterministic_check_observations"][0]["applicability"] == "unsupported"
    )

    repeated = tmp_path / "repeated"
    _workspace(
        repeated,
        source=(
            "a <- stats::t.test(raw_counts[, 1], raw_counts[, 2])\n"
            "b <- stats::t.test(raw_counts[, 3], raw_counts[, 4])\n"
        ),
    )
    repeated_bundle = _audit(repeated, tmp_path / "repeated-audit", schema_root)
    repeated_observation = repeated_bundle["deterministic_check_observations"][0]
    assert repeated_observation["applicability"] == "unsupported"
    assert repeated_observation["operands"] == []


def test_unselected_source_and_module_removal_are_isolated(
    schema_root: Path, tmp_path: Path
) -> None:
    unselected = tmp_path / "unselected"
    _workspace(unselected)
    unselected_bundle = run_audit(
        unselected,
        tmp_path / "unselected-audit",
        schema_root,
        report="report.md",
        calculation_check_registry=count_model_compatibility_registry(),
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
        material_inputs=("analysis.R",),
        calculation_check_registry=CalculationCheckRegistry((), profile_id="empty"),
    )
    assert removed_bundle["deterministic_check_observations"] == []
