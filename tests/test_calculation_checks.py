from __future__ import annotations

import json
import shutil
from pathlib import Path

from sc_referee.calculation_checks.core import CalculationCheckRegistry
from sc_referee.controller import replay, run_audit


def _workspace(project_root: Path, case_id: str) -> Path:
    return (
        project_root
        / "evaluation"
        / "development-controls"
        / "multiple-testing-bh-v1"
        / "cases"
        / case_id
        / "workspace"
    )


def _copied_workspace(project_root: Path, tmp_path: Path, case_id: str) -> Path:
    destination = tmp_path / f"{case_id}-workspace"
    shutil.copytree(_workspace(project_root, case_id), destination)
    return destination


def _operand(observation: dict[str, object], name: str) -> object:
    operands = observation["operands"]
    assert isinstance(operands, list)
    return next(item["value"] for item in operands if item["name"] == name)


def test_positive_control_produces_typed_nonconformance_without_finding(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    output = tmp_path / "positive-audit"
    bundle = run_audit(
        _copied_workspace(project_root, tmp_path, "multiple-testing-positive"),
        output,
        schema_root,
        report="report.md",
    )

    assert bundle["findings"] == []
    assert len(bundle["deterministic_check_observations"]) == 1
    observation = bundle["deterministic_check_observations"][0]
    assert observation["applicability"] == "applicable"
    assert observation["comparison"]["outcome"] == "nonconformant"
    assert observation["output_ceiling"] == "disclosure_only"
    assert observation["production_finding_permitted"] is False
    assert _operand(observation, "reported_discovery_count") == 4
    assert _operand(observation, "recomputed_discovery_count") == 2
    assert _operand(observation, "adjusted_mismatch_indices") == list(range(1, 10))
    assert _operand(observation, "call_mismatch_indices") == [3, 4]
    assert any(
        item["title"] == "Declared BH outputs differ from bounded recomputation"
        for item in bundle["disclosures"]
    )
    report_text = (output / "report.html").read_text(encoding="utf-8")
    assert "Declared BH outputs differ from bounded recomputation" in report_text
    assert (output / "observed" / "deterministic-check-observation.jsonl").is_file()
    lock = json.loads((output / "semantic.lock.json").read_text(encoding="utf-8"))
    assert lock["model_calls"] == []
    assert lock["model_access_after_lock"] is False
    assert lock["calculation_check_registry"]["evaluation"] is not None

    replayed = replay(output / "semantic.lock.json", tmp_path / "positive-replay", schema_root)
    replayed_observation = replayed["deterministic_check_observations"][0]
    assert replayed_observation == observation
    assert replayed["findings"] == []


def test_corrected_twin_is_conformant_and_has_no_adverse_calculation_output(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    bundle = run_audit(
        _copied_workspace(project_root, tmp_path, "multiple-testing-corrected-twin"),
        tmp_path / "corrected-audit",
        schema_root,
        report="report.md",
    )

    observation = bundle["deterministic_check_observations"][0]
    assert observation["comparison"]["outcome"] == "conformant"
    assert _operand(observation, "reported_discovery_count") == 2
    assert _operand(observation, "recomputed_discovery_count") == 2
    assert not any("BH outputs differ" in item["title"] for item in bundle["disclosures"])
    assert bundle["findings"] == []


def test_hard_negative_is_not_applicable_and_selected_hits_remain_a_question(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    hard = run_audit(
        _copied_workspace(project_root, tmp_path, "multiple-testing-hard-negative"),
        tmp_path / "hard-audit",
        schema_root,
        report="report.md",
    )
    hard_observation = hard["deterministic_check_observations"][0]
    assert hard_observation["applicability"] == "not_applicable"
    assert hard_observation["comparison"]["outcome"] == "not_applicable"
    assert not any(
        item["unknown_semantic_dimension"] == "multiplicity_contract"
        for item in hard["material_questions"]
    )
    assert hard["findings"] == []

    ambiguous = run_audit(
        _copied_workspace(project_root, tmp_path, "multiple-testing-ambiguous"),
        tmp_path / "ambiguous-audit",
        schema_root,
        report="report.md",
    )
    ambiguous_observation = ambiguous["deterministic_check_observations"][0]
    assert ambiguous_observation["applicability"] == "ambiguous"
    questions = [
        item
        for item in ambiguous["material_questions"]
        if item["unknown_semantic_dimension"] == "multiplicity_contract"
    ]
    assert len(questions) == 1
    assert ambiguous["findings"] == []


def test_malformed_declared_table_fails_locally_without_numerical_accusation(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "malformed-workspace"
    shutil.copytree(_workspace(project_root, "multiple-testing-positive"), repository)
    (repository / "results.csv").write_text(
        "test_id,p_value,adjusted_p_value,significant\ngene_01,not-a-number,0.01,true\n",
        encoding="utf-8",
    )
    bundle = run_audit(
        repository,
        tmp_path / "malformed-audit",
        schema_root,
        report="report.md",
    )

    observation = bundle["deterministic_check_observations"][0]
    assert observation["applicability"] == "unsupported"
    assert observation["comparison"]["outcome"] == "unknown"
    assert observation["operands"] == []
    assert bundle["findings"] == []
    assert not any("BH outputs differ" in item["title"] for item in bundle["disclosures"])


def test_removing_bh_module_removes_only_calculation_observation(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    bundle = run_audit(
        _copied_workspace(project_root, tmp_path, "multiple-testing-positive"),
        tmp_path / "without-calculation-module",
        schema_root,
        report="report.md",
        calculation_check_registry=CalculationCheckRegistry(()),
    )

    assert bundle["deterministic_check_observations"] == []
    assert bundle["findings"] == []
    assert not any("BH outputs differ" in item["title"] for item in bundle["disclosures"])


def test_over_budget_table_is_unknown_not_a_disagreement(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "over-budget-workspace"
    shutil.copytree(_workspace(project_root, "multiple-testing-positive"), repository)
    with (repository / "results.csv").open("a", encoding="utf-8") as handle:
        handle.write("#" * 1_000_001)
    bundle = run_audit(
        repository,
        tmp_path / "over-budget-audit",
        schema_root,
        report="report.md",
    )

    observation = bundle["deterministic_check_observations"][0]
    assert observation["applicability"] == "unsupported"
    assert observation["comparison"]["outcome"] == "unknown"
    assert bundle["findings"] == []
    assert not any("BH outputs differ" in item["title"] for item in bundle["disclosures"])


def test_live_workspace_drift_cannot_change_snapshot_calculation(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "drift-workspace"
    shutil.copytree(_workspace(project_root, "multiple-testing-positive"), repository)

    def mutate_after_snapshot(root: Path) -> None:
        (root / "results.csv").write_text(
            "test_id,p_value,adjusted_p_value,significant\ngene_01,0.9,0.9,false\n",
            encoding="utf-8",
        )

    bundle = run_audit(
        repository,
        tmp_path / "drift-audit",
        schema_root,
        report="report.md",
        after_snapshot=mutate_after_snapshot,
    )

    observation = bundle["deterministic_check_observations"][0]
    assert observation["comparison"]["outcome"] == "nonconformant"
    assert _operand(observation, "reported_discovery_count") == 4
    assert _operand(observation, "recomputed_discovery_count") == 2
    snapshot = bundle["repository_snapshots"][0]
    assert snapshot["live_workspace_state"]["status"] == "workspace_diverged"
    assert snapshot["live_workspace_state"]["mix_live_content_into_run"] is False
