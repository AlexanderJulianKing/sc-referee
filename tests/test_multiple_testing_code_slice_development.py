from __future__ import annotations

import json
import shutil
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest

import sc_referee.controller as controller_module
from sc_referee.controller import replay, run_audit
from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.detectors.method_conflict_finding import (
    CODE_CSV_DEPENDENCE_FINDING_PROFILE_DIGEST,
    CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_DIGEST,
    MULTIPLE_TESTING_CODE_FINDING_PROFILE_V2_DIGEST,
    MULTIPLE_TESTING_CODE_FINDING_PROFILE_V2_ID,
    _multiple_testing_code_facts,
    draft_method_conflict_finding,
)
from sc_referee.detectors.method_conflict_grant_pins import GRANT_PINS
from sc_referee.detectors.method_conflict_registry import (
    evaluate_registered_method_conflicts,
)
from sc_referee.method_contract_run import run_method_contract
from sc_referee.qualification_grants import load_installed_qualification_grants
from sc_referee.scientific_checks.code_csv_dependence_adapter_v3_1 import (
    CODE_CSV_DEPENDENCE_ADAPTER_IMPLEMENTATION_DIGEST,
    code_csv_dependence_grammar_digest,
)
from sc_referee.scientific_checks.profiles import scientific_check_release_registry
from sc_referee.scientific_checks.registry import ScientificCheckRegistry

CHECK_ID = "check:authorized-complete-family-correction-over-code-test-battery"
DETECTOR_ID = "detector:bounded-code-csv-multiple-testing-conflict"
BINDING_ID = (
    "method-conflict-binding:authorized-complete-family-correction-over-code-test-battery-v1:"
    "development"
)


def _profile() -> dict[str, object]:
    return {
        "profile_id": "scientific_check_requirement_v1",
        "profile_version": "1.2.0",
        "check_id": CHECK_ID,
        "candidate_id": "complete-correction-over-authorized-outcome-family",
        "semantic_role_authority": {
            "authorized_test_family": {
                "material_input_path": "data.csv",
                "group_contrast_column": "group",
                "outcome_columns": ["m1", "m2", "m3"],
                "family_member_rule": "one-two-group-test-per-named-outcome-column",
                "correction_scope": "complete-authorized-family",
            }
        },
    }


def _source(*, corrected: bool = False) -> str:
    imports = "from statsmodels.stats.multitest import multipletests\n" if corrected else ""
    decisions = (
        "pvalues = [r0.pvalue, r1.pvalue, r2.pvalue]\n"
        "reject, adjusted, _, _ = multipletests(pvalues)\n"
        "print(reject[0])\nprint(reject[1])\nprint(reject[2])\n"
        if corrected
        else "print(r0.pvalue < 0.05)\nprint(r1.pvalue < 0.05)\nprint(r2.pvalue < 0.05)\n"
    )
    return (
        "import pandas as pd\n"
        "from scipy import stats\n"
        f"{imports}"
        'df = pd.read_csv("data.csv")\n'
        'r0 = stats.ttest_ind(df.loc[df["group"] == "a", "m1"], '
        'df.loc[df["group"] == "b", "m1"])\n'
        'r1 = stats.ttest_ind(df.loc[df["group"] == "a", "m2"], '
        'df.loc[df["group"] == "b", "m2"])\n'
        'r2 = stats.ttest_ind(df.loc[df["group"] == "a", "m3"], '
        'df.loc[df["group"] == "b", "m3"])\n'
        f"{decisions}"
    )


def _write_project(root: Path, *, corrected: bool = False) -> Path:
    project = root / "project"
    project.mkdir()
    (project / "task.md").write_text("Define the authorized family analysis.\n", encoding="utf-8")
    (project / "data.csv").write_text(
        "group,m1,m2,m3\na,1,2,3\na,2,3,4\nb,4,5,6\nb,5,6,7\n",
        encoding="utf-8",
    )
    (project / "analysis.py").write_text(_source(corrected=corrected), encoding="utf-8")
    return project


def _run_case(
    tmp_path: Path, schema_root: Path, *, corrected: bool = False
) -> tuple[dict[str, Any], dict[str, Any], Path]:
    project = _write_project(tmp_path, corrected=corrected)
    contract = tmp_path / "method-contract"
    run_method_contract(
        project,
        "task.md",
        contract,
        schema_root,
        profile=_profile(),
        actor_id="human:test",
        created_at="2026-08-24T00:00:00Z",
    )
    audit = tmp_path / "audit"
    bundle = run_audit(
        project,
        audit,
        schema_root,
        material_inputs=("data.csv",),
        method_contract_lock=contract / "semantic.lock.json",
        scientific_check_lane="development",
    )
    lock = json.loads((audit / "semantic.lock.json").read_text(encoding="utf-8"))
    return bundle, lock, audit


def test_development_candidate_replays_without_finding(schema_root: Path, tmp_path: Path) -> None:
    bundle, lock, audit = _run_case(tmp_path, schema_root)

    results = [item for item in bundle["detector_results"] if item["detector_id"] == DETECTOR_ID]
    assert len(results) == 1
    assert results[0]["state"] == "evaluation_finding_candidate"
    assert bundle["findings"] == []
    modules = lock["scientific_check_registry"]["evaluation"]["modules"]
    module = next(item for item in modules if item["check_id"] == CHECK_ID)
    assert module["state"] == "applicable"
    observation = module["observations"][0]
    assert observation["observed_operand"] == {
        "kind": "canonical_scalar",
        "value": "no_recognized_family_correction",
    }
    fact = observation["multiple_testing_evidence"]
    assert fact["authorized_count"] == fact["performed_count"] == 3
    assert fact["corrected_count"] == 0
    assert fact["uncorrected_count"] == 3
    assert fact["profile"] == "code_csv_multiple_testing_evidence_v2"
    assert fact["registered_test_apis_by_position"] == [
        "scipy.stats.ttest_ind",
        "scipy.stats.ttest_ind",
        "scipy.stats.ttest_ind",
    ]
    assert fact["registered_test_api_set"] == ["scipy.stats.ttest_ind"]
    assert fact["conclusion_positions"] == [0, 1, 2]

    replayed = replay(audit / "semantic.lock.json", tmp_path / "replay", schema_root)
    assert replayed["detector_results"] == bundle["detector_results"]
    assert replayed["findings"] == []
    assert replayed["coverage_records"] == bundle["coverage_records"]


def test_default_multipletests_is_covered_negative_without_candidate(
    schema_root: Path, tmp_path: Path
) -> None:
    bundle, lock, _ = _run_case(tmp_path, schema_root, corrected=True)

    results = [item for item in bundle["detector_results"] if item["detector_id"] == DETECTOR_ID]
    assert len(results) == 1
    assert results[0]["state"] not in {"evaluation_finding_candidate", "finding_candidate"}
    assert bundle["findings"] == []
    module = next(
        item
        for item in lock["scientific_check_registry"]["evaluation"]["modules"]
        if item["check_id"] == CHECK_ID
    )
    assert module["observations"][0]["observed_operand"]["value"] == (
        "complete_family_correction_over_authorized_outcome_family"
    )
    fact = module["observations"][0]["multiple_testing_evidence"]
    assert fact["correction_classification"] == "complete"
    assert fact["corrected_positions"] == [0, 1, 2]


def test_evaluation_candidate_uses_only_versioned_multiple_testing_wording(
    schema_root: Path, tmp_path: Path
) -> None:
    _, lock, _ = _run_case(tmp_path, schema_root)
    evaluations = [
        item
        for item in evaluate_registered_method_conflicts(lock)
        if item.binding.binding_id == BINDING_ID
    ]
    assert len(evaluations) == 1
    evaluation = evaluations[0]
    draft = draft_method_conflict_finding(
        evaluation.result,
        evaluation.binding,
        work_packet=evaluation.work_packet,
    )

    assert draft["title"] == (
        "Analysis code contradicts the frozen complete-family correction requirement"
    )
    assert draft["extensions"]["x-finding-wording-profile-id"] == (
        MULTIPLE_TESTING_CODE_FINDING_PROFILE_V2_ID
    )
    assert draft["extensions"]["x-finding-wording-profile-digest"] == (
        MULTIPLE_TESTING_CODE_FINDING_PROFILE_V2_DIGEST
    )
    assert (
        "maps every named outcome to exactly one registered two-group test call" in draft["summary"]
    )
    assert "3 calls in all" in draft["summary"]
    assert "scipy.stats.ttest_ind" not in draft["summary"]
    assert (
        "without entering a recognized correction anywhere in the analyzed source"
        in draft["summary"]
    )
    assert "before" not in draft["summary"]
    assert draft["coverage_limitations"] == [
        "The contract author may be wrong.",
        "Static source does not establish that project code executed.",
        "Absence of a recognized correction in the analyzed source does not establish that no correction was applied.",
        "Correction may occur in unsupported, uninspected, upstream, downstream, or external code.",
        "The detector does not establish runtime p-values, test assumptions, effect sizes, inflated error rates, statistical invalidity, selection, publication use, interpretation, or reliance.",
        "The detector does not establish that the named outcomes should scientifically form one family.",
    ]


def test_evidence_v2_rejects_each_inconsistent_api_position_and_count_shape(
    schema_root: Path, tmp_path: Path
) -> None:
    _, lock, _ = _run_case(tmp_path, schema_root)
    evaluation = next(
        item
        for item in evaluate_registered_method_conflicts(lock)
        if item.binding.binding_id == BINDING_ID
    )
    mutations = (
        lambda fact: fact.__setitem__(
            "registered_test_apis_by_position",
            fact["registered_test_apis_by_position"][:-1],
        ),
        lambda fact: fact.__setitem__(
            "registered_test_api_set",
            ["scipy.stats.mannwhitneyu", "scipy.stats.ttest_ind"],
        ),
        lambda fact: fact["registered_test_apis_by_position"].__setitem__(0, "custom.test"),
        lambda fact: fact.__setitem__("performed_count", 2),
        lambda fact: fact.__setitem__("conclusion_positions", [1, 0, 2]),
        lambda fact: fact.update(
            {
                "correction_classification": "strict_subset",
                "corrected_count": 2,
                "uncorrected_count": 1,
                "corrected_positions": [0, 0],
            }
        ),
        lambda fact: fact.__setitem__("corrected_count", 1),
    )
    for mutate in mutations:
        packet = deepcopy(evaluation.work_packet)
        assertion = next(
            item
            for item in packet["semantic_assertions"]
            if "x-code-csv-multiple-testing-evidence" in item["extensions"]
        )
        extensions = assertion["extensions"]
        fact = extensions["x-code-csv-multiple-testing-evidence"]
        mutate(fact)
        fact_without_digest = dict(fact)
        fact_without_digest.pop("fact_digest")
        fact["fact_digest"] = semantic_digest(fact_without_digest)
        extensions["x-code-csv-multiple-testing-evidence-digest"] = semantic_digest(fact)
        assert _multiple_testing_code_facts(packet) is None


def _contains_value(value: object, needle: str) -> bool:
    if isinstance(value, dict):
        return any(_contains_value(item, needle) for item in value.values())
    if isinstance(value, list | tuple):
        return any(_contains_value(item, needle) for item in value)
    return value == needle


def test_two_registry_differential_keeps_qualified_authority_and_finding_inputs_isolated() -> None:
    registry = scientific_check_release_registry()

    def module_value(item: Any) -> dict[str, Any]:
        return {
            "manifest": item.manifest.to_dict(),
            "declared_manifest_digest": item.declared_manifest_digest,
            "adapter_manifests": [manifest.to_dict() for manifest in item.adapter_manifests],
        }

    qualified_modules = [module_value(item) for item in registry.modules_for_lane("qualified")]
    development_without_new = [
        module_value(item)
        for item in registry.modules_for_lane("development")
        if item.manifest.check_id != CHECK_ID
    ]

    assert [
        module_value(item)
        for item in sorted(registry.modules, key=lambda value: value.manifest.check_id)
    ] == qualified_modules
    assert development_without_new == qualified_modules
    assert all(pin.check_id != CHECK_ID for pin in GRANT_PINS.values())
    assert canonical_json({key: asdict(value) for key, value in sorted(GRANT_PINS.items())})
    assert not _contains_value(GRANT_PINS, registry.registry_digest)
    assert not any(
        _contains_value(asdict(pin), registry.registry_digest) for pin in GRANT_PINS.values()
    )
    new_binding = next(
        item
        for item in registry.development_method_conflict_bindings
        if item.binding_id == BINDING_ID
    )
    assert not new_binding.production_finding_permitted
    assert new_binding.binding_id not in GRANT_PINS
    assert semantic_digest(qualified_modules) == semantic_digest(development_without_new)
    assert CODE_CSV_DEPENDENCE_ADAPTER_IMPLEMENTATION_DIGEST == (
        "sha256:6900611a3ef6c06be5740df14333eac5d789c6c93165b8826c796a8b4de87170"
    )
    assert code_csv_dependence_grammar_digest() == (
        "sha256:69256d48b46f16d7c144e01d5b4509470e9b187bf3db4f7e259d782459c2d476"
    )
    assert CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_DIGEST == (
        "sha256:1dad7c14985fbfb89a7f8fe24a5e7f36d07a7c9fc6f76b4d14951cc71337c04a"
    )
    assert CODE_CSV_DEPENDENCE_FINDING_PROFILE_DIGEST == (
        "sha256:0440fdb918eb04ff975e7129c4152a2d681f3f4203ae8c7a1f8fc9ebf8916288"
    )
    root = Path(__file__).resolve().parents[1]
    assert (
        sha256_digest((root / "src/sc_referee/scientific_checks/integration.py").read_bytes())
        == "sha256:55ac1a3dcef282445eb75f2edb55a0f518f8649cbc3b028b148862ed7afb93da"
    )


def _installed_authority_surfaces() -> dict[str, object]:
    evidence = load_installed_qualification_grants()
    return {
        "pins": {key: asdict(value) for key, value in sorted(GRANT_PINS.items())},
        "grants": {key: dict(value.grant) for key, value in sorted(evidence.items())},
        "qualifications": {
            key: dict(value.qualification) for key, value in sorted(evidence.items())
        },
        "metric_sets": {key: dict(value.metric_set) for key, value in sorted(evidence.items())},
        "threshold_policy_references": {
            key: {
                "grant_digest": value.grant["threshold_policy_digest"],
                "qualification_policy": value.qualification["numeric_threshold_policy"],
                "metric_set_policy": value.metric_set["numeric_threshold_policy"],
            }
            for key, value in sorted(evidence.items())
        },
    }


def test_two_registry_differential_keeps_all_authority_and_qualified_finding_bytes_equal(
    schema_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    registry = scientific_check_release_registry()
    before = _installed_authority_surfaces()
    without_multiple_testing = ScientificCheckRegistry(
        registry.modules,
        unavailable_manifests=registry.unavailable_manifests,
        method_conflict_bindings=registry.method_conflict_bindings,
        development_modules=tuple(
            item for item in registry.development_modules if item.manifest.check_id != CHECK_ID
        ),
        development_method_conflict_bindings=tuple(
            item
            for item in registry.development_method_conflict_bindings
            if item.check_id != CHECK_ID
        ),
    )
    assert registry.registry_digest != without_multiple_testing.registry_digest

    after = _installed_authority_surfaces()
    assert canonical_json(before) == canonical_json(after)
    for digest in (registry.registry_digest, without_multiple_testing.registry_digest):
        assert not _contains_value(before, digest)
        assert not _contains_value(after, digest)

    case = Path("evaluation/development/blind-envelope-5-2026-08-22/cases/0b4876ceca6b0a9aede7")
    lock_path = case / "method-contract/semantic.lock.json"
    frozen_contract = json.loads(lock_path.read_text(encoding="utf-8"))
    material_path = frozen_contract["method_contract_profile"]["profile_manifest"][
        "authority_binding_snapshot"
    ]["authorized_independent_unit_key"]["material_input_path"]
    monkeypatch.setattr(
        controller_module,
        "uuid4",
        lambda: UUID("12345678-1234-5678-1234-567812345678"),
    )
    monkeypatch.setattr(controller_module, "_timestamp_now", lambda: "2026-08-24T00:00:00Z")
    baseline_project = tmp_path / "qualified-baseline-project"
    changed_project = tmp_path / "qualified-changed-project"
    shutil.copytree(case / "project", baseline_project)
    shutil.copytree(case / "project", changed_project)
    baseline = run_audit(
        baseline_project,
        tmp_path / "qualified-baseline",
        schema_root,
        material_inputs=(material_path,),
        method_contract_lock=lock_path,
        scientific_check_registry=registry,
    )
    changed = run_audit(
        changed_project,
        tmp_path / "qualified-without-multiple-testing",
        schema_root,
        material_inputs=(material_path,),
        method_contract_lock=lock_path,
        scientific_check_registry=without_multiple_testing,
    )
    baseline_lock = json.loads(
        (tmp_path / "qualified-baseline/semantic.lock.json").read_text(encoding="utf-8")
    )
    changed_lock = json.loads(
        (tmp_path / "qualified-without-multiple-testing/semantic.lock.json").read_text(
            encoding="utf-8"
        )
    )
    assert canonical_json(baseline["findings"]) == canonical_json(changed["findings"])
    assert len(baseline["findings"]) == 1
    for finding in baseline["findings"]:
        assert not _contains_value(finding, registry.registry_digest)
        assert not _contains_value(finding, without_multiple_testing.registry_digest)
        assert not _contains_value(finding, baseline_lock["semantic_lock_digest"])
        assert not _contains_value(finding, changed_lock["semantic_lock_digest"])
