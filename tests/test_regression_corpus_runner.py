from __future__ import annotations

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation.regression_corpus import (
    regression_tree_digest,
    validate_regression_corpus_ledger,
)
from sc_referee_evaluation.regression_runner import (
    DEFAULT_REGRESSION_CORPUS_EXECUTION_PLAN,
    RegressionCorpusRunnerError,
    compare_corpus_semantic_outcome,
    corpus_semantic_projection,
    run_regression_corpus,
    validate_regression_corpus_execution_plan,
)

from sc_referee.core.ids import canonical_json, semantic_digest


def _plan(project_root: Path) -> dict[str, Any]:
    return json.loads((project_root / DEFAULT_REGRESSION_CORPUS_EXECUTION_PLAN).read_text())


def _write_plan(path: Path, plan: dict[str, Any], *, recompute_digest: bool = True) -> None:
    payload = copy.deepcopy(plan)
    if recompute_digest:
        payload.pop("plan_digest", None)
        payload["plan_digest"] = semantic_digest(payload)
    path.write_text(canonical_json(payload) + "\n", encoding="utf-8")


def _ambiguous_expected(project_root: Path) -> dict[str, Any]:
    return copy.deepcopy(_plan(project_root)["audit_replay_cases"][0]["expected"])


def test_execution_plan_exactly_covers_local_repository_cases(project_root: Path) -> None:
    ledger = validate_regression_corpus_ledger(project_root=project_root)
    plan = validate_regression_corpus_execution_plan(project_root=project_root)
    sources = {item["source_id"]: item for item in ledger["sources"]}
    expected = {
        item["case_id"]
        for item in ledger["cases"]
        if sources[item["source_ref"]]["source_kind"] == "repository_tree"
    }

    assert {item["case_id"] for item in plan["audit_replay_cases"]} == expected
    assert len(expected) == 4
    assert all(
        item["registry_profile"] == "calculation_check_release_v1"
        for item in plan["audit_replay_cases"]
    )
    assert all(
        item["expected"]["assessment_counts"]["findings"] == 0
        for item in plan["audit_replay_cases"]
    )
    assert all(item["expected"]["replay_equal"] is True for item in plan["audit_replay_cases"])


def test_runner_audits_replays_and_emits_deterministic_create_once_receipt(
    project_root: Path, tmp_path: Path
) -> None:
    selected: list[tuple[str, ...]] = []

    def retain_node_ids(node_ids: tuple[str, ...]) -> None:
        selected.append(node_ids)

    first_output = tmp_path / "receipt.json"
    retained_tree = project_root / "evaluation/development-controls/multiple-testing-bh-v1"
    retained_digest = regression_tree_digest(retained_tree)
    first = run_regression_corpus(
        project_root=project_root,
        output=first_output,
        pytest_runner=retain_node_ids,
    )
    second = run_regression_corpus(
        project_root=project_root,
        pytest_runner=lambda node_ids: selected.append(node_ids),
    )

    assert first == second
    assert regression_tree_digest(retained_tree) == retained_digest
    assert first_output.read_bytes() == (canonical_json(first) + "\n").encode()
    assert first["ledger_case_count"] == 155
    assert first["pytest_case_count"] == 151
    assert first["pytest_selector_count"] == len(selected[0]) == 110
    assert first["audit_replay_case_count"] == 4
    assert first["case_role_counts"]["corrected_twin"] == 11
    assert first["case_role_counts"]["hard_negative"] == 33
    assert first["case_role_counts"]["independent_false_positive"] == 1
    assert first["case_role_counts"]["unsupported"] == 33
    assert first["case_role_counts"]["replay"] == 13
    assert first["target_project_code_executed"] is False
    assert first["model_access_after_lock"] is False
    assert first["qualification_evidence_created"] is False
    assert any("test_unresolved_or_repeated_producer_abstains" in item for item in selected[0])
    assert any(
        "test_scientific_check_inventory_and_evaluation_are_locked_for_replay" in item
        for item in selected[0]
    )
    assert any(
        "test_selected_nonsequence_record_line_is_disclosed_without_finding_and_replays" in item
        for item in selected[0]
    )
    assert all(
        result["semantic_outcome"]["coverage_termination_reasons"] == ["semantic_inputs_unresolved"]
        for result in first["audit_replay_results"]
    )
    assert all(
        result["semantic_outcome"]["replay_equal"] is True
        for result in first["audit_replay_results"]
    )
    assert all(
        result["semantic_outcome"]["assessment_counts"]["findings"] == 0
        for result in first["audit_replay_results"]
    )
    with pytest.raises(FileExistsError):
        run_regression_corpus(
            project_root=project_root,
            output=first_output,
            pytest_runner=lambda _node_ids: None,
        )


def test_projection_ignores_run_identity_timestamps_reports_and_sqlite(tmp_path: Path) -> None:
    base: dict[str, Any] = {
        "findings": [],
        "conditional_concerns": [],
        "material_questions": [{"unknown_semantic_dimension": "multiplicity_contract"}],
        "disclosures": [{"title": "Bounded disclosure"}],
        "deterministic_check_observations": [
            {
                "check_manifest": {"check_id": "calculation-check:test"},
                "applicability": "ambiguous",
                "comparison": {"outcome": "unknown"},
                "output_ceiling": "disclosure_only",
            }
        ],
        "coverage_records": [
            {"extensions": {"x-termination-reason": "semantic_inputs_unresolved"}}
        ],
        "executions": [],
        "project_execution_authorizations": [],
    }
    noisy = copy.deepcopy(base)
    noisy.update(
        {
            "audit_id": "audit:different",
            "generated_at": "2099-01-01T00:00:00Z",
            "report_html": "unstable rendered bytes",
            "sqlite_path": str(tmp_path / "audit.db"),
        }
    )
    (tmp_path / "audit.db").write_bytes(b"not a sqlite database")

    assert corpus_semantic_projection(base) == corpus_semantic_projection(noisy)


Mutation = Callable[[dict[str, Any]], None]


def _remove_question(observed: dict[str, Any]) -> None:
    observed["question_dimensions"] = []


def _add_question(observed: dict[str, Any]) -> None:
    observed["question_dimensions"].append("unrelated_dimension")


def _change_ceiling(observed: dict[str, Any]) -> None:
    observed["calculation_observations"][0]["output_ceiling"] = "finding"


def _remove_disclosure(observed: dict[str, Any]) -> None:
    observed["disclosure_title_counts"].pop()


def _add_disclosure(observed: dict[str, Any]) -> None:
    observed["disclosure_title_counts"].append({"title": "Unexpected", "count": 1})


def _unexpected_finding(observed: dict[str, Any]) -> None:
    observed["assessment_counts"]["findings"] = 1


def _unexpected_concern(observed: dict[str, Any]) -> None:
    observed["assessment_counts"]["conditional_concerns"] = 1


def _change_applicability(observed: dict[str, Any]) -> None:
    observed["calculation_observations"][0]["applicability"] = "applicable"


def _change_comparison(observed: dict[str, Any]) -> None:
    observed["calculation_observations"][0]["comparison_outcome"] = "conformant"


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        (_remove_question, "lost question"),
        (_add_question, "new false question"),
        (_change_ceiling, "changed output ceiling"),
        (_remove_disclosure, "missing Disclosure"),
        (_add_disclosure, "new Disclosure"),
        (_unexpected_finding, "unexpected Finding"),
        (_unexpected_concern, "unexpected ConditionalConcern"),
        (_change_applicability, "applicability changed"),
        (_change_comparison, "calculation comparison outcome changed"),
        (lambda value: value.__setitem__("replay_equal", False), "replay difference"),
        (lambda value: value.__setitem__("execution_count", 1), "project execution detected"),
        (
            lambda value: value.__setitem__("project_execution_authorization_count", 1),
            "project execution detected",
        ),
        (lambda value: value.__setitem__("model_call_count", 1), "model access detected"),
        (
            lambda value: value.__setitem__("model_access_after_lock", True),
            "post-lock model call detected",
        ),
        (lambda value: value.__setitem__("final_state", "partial"), "final audit state changed"),
        (
            lambda value: value.__setitem__("coverage_termination_reasons", ["other"]),
            "partial coverage changed",
        ),
    ],
)
def test_semantic_comparison_rejects_each_mutation_for_the_right_reason(
    project_root: Path, mutation: Mutation, reason: str
) -> None:
    expected = _ambiguous_expected(project_root)
    observed = copy.deepcopy(expected)
    mutation(observed)

    with pytest.raises(RegressionCorpusRunnerError, match=reason):
        compare_corpus_semantic_outcome(expected, observed)


@pytest.mark.parametrize(
    ("mutation", "reason", "recompute_digest"),
    [
        (
            lambda plan: plan.__setitem__("ledger_digest", "sha256:" + "0" * 64),
            "ledger digest mismatch",
            True,
        ),
        (
            lambda plan: plan["audit_replay_cases"].pop(),
            "does not exactly cover repository-tree cases",
            True,
        ),
        (
            lambda plan: plan["audit_replay_cases"][0].__setitem__("report_path", "../report.md"),
            "must be bounded and relative",
            True,
        ),
        (
            lambda plan: plan["audit_replay_cases"][0]["expected"]["assessment_counts"].__setitem__(
                "findings", 1
            ),
            "cannot authorize Findings",
            True,
        ),
        (
            lambda plan: plan["audit_replay_cases"][0]["expected"]["calculation_observations"][
                0
            ].__setitem__("check_id", "calculation-check:other"),
            "does not exactly cover its ledger components",
            True,
        ),
        (lambda _plan: None, "execution plan digest mismatch", False),
    ],
)
def test_execution_plan_mutations_fail_closed(
    project_root: Path,
    tmp_path: Path,
    mutation: Mutation,
    reason: str,
    recompute_digest: bool,
) -> None:
    plan = _plan(project_root)
    mutation(plan)
    if not recompute_digest:
        plan["plan_digest"] = "sha256:" + "0" * 64
    path = tmp_path / "plan.json"
    _write_plan(path, plan, recompute_digest=recompute_digest)

    with pytest.raises(RegressionCorpusRunnerError, match=reason):
        validate_regression_corpus_execution_plan(path, project_root=project_root)


def test_execution_plan_rejects_noncanonical_and_duplicate_json(
    project_root: Path, tmp_path: Path
) -> None:
    pretty = tmp_path / "pretty.json"
    pretty.write_text(json.dumps(_plan(project_root), indent=2) + "\n", encoding="utf-8")
    with pytest.raises(RegressionCorpusRunnerError, match="canonical JSON"):
        validate_regression_corpus_execution_plan(pretty, project_root=project_root)

    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"plan_id":"one","plan_id":"two"}\n', encoding="utf-8")
    with pytest.raises(RegressionCorpusRunnerError, match="Duplicate JSON key"):
        validate_regression_corpus_execution_plan(duplicate, project_root=project_root)
