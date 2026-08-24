from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation.cli import main as evaluation_main
from sc_referee_evaluation.metrics import (
    METRIC_NAMES,
    QualificationMetricError,
    bootstrap_cluster_index,
    bootstrap_problem_sample,
    build_qualification_metric_set,
)

import sc_referee.qualification_metrics as core_metric_module
from sc_referee.core.ids import semantic_digest


def _example(project_root: Path, name: str) -> dict[str, Any]:
    return json.loads(
        (project_root / "reference" / "schemas-v0.21.0" / "examples" / name).read_text(
            encoding="utf-8"
        )
    )


def _case(
    project_root: Path,
    index: int,
    *,
    state: str = "no_issue_detected_within_coverage",
    applicability: str = "applicable",
    coverage: str = "covered",
    candidate_status: str | None = None,
    candidate_count: int = 1,
    root_status: str | None = None,
    comparison_excluded: bool = False,
    legacy_incomplete: bool = False,
    problem_id: str | None = None,
) -> dict[str, Any]:
    outcome = _example(project_root, "detector-case-outcome.example.json")
    suffix = f"{index:02d}"
    outcome.update(
        {
            "case_outcome_id": f"detector-case-outcome:metric-{suffix}",
            "case_id": f"case:metric-{suffix}",
            "problem_id": problem_id or f"problem:metric-{suffix}",
            "fixture_ref": {
                "record_type": "benchmark_fixture",
                "record_id": f"fixture:metric-{suffix}",
            },
            "corpus_partition": "held_out",
            "qualification_proof_status": (
                "legacy_proof_projection_unavailable" if legacy_incomplete else "complete"
            ),
            "comparison_status": ("comparison_excluded" if comparison_excluded else "reconciled"),
            "exact_cross_provider_agreement": not comparison_excluded,
            "exclusion_reasons": (
                ["Cross-provider comparison remained unresolved."] if comparison_excluded else []
            ),
            "metric_input_status": (
                "legacy_source_projection_unavailable" if legacy_incomplete else "complete"
            ),
            "metric_eligible": not comparison_excluded and not legacy_incomplete,
            "promotion_evidence_eligible": not comparison_excluded and not legacy_incomplete,
        }
    )
    result_ref = {
        "record_type": "detector_result",
        "record_id": f"result:metric-{suffix}",
    }
    execution_class = "detector_error" if state == "detector_error" else "completed"
    outcome["detector_result_outcomes"] = (
        []
        if legacy_incomplete
        else [
            {
                "detector_result_ref": result_ref,
                "detector_result_digest": f"sha256:{index:064x}",
                "state": state,
                "applicability_status": applicability,
                "coverage_status": coverage,
                "evaluation_candidate_refs": [],
                "execution_class": execution_class,
            }
        ]
    )
    outcome["detector_run_outcome"] = {
        "execution_status": execution_class,
        "applicability_status": applicability,
        "coverage_status": coverage,
    }

    candidate_refs = [
        {
            "record_type": "detector_evaluation_candidate",
            "record_id": f"detector-evaluation-candidate:metric-{suffix}-{position}",
        }
        for position in range(candidate_count if candidate_status is not None else 0)
    ]
    root_ref = {
        "record_type": "adjudicated_root_cause",
        "record_id": f"adjudicated-root-cause:metric-{suffix}",
    }
    if candidate_status is None:
        outcome["candidate_refs"] = []
        outcome["candidate_outcomes"] = []
    else:
        outcome["candidate_refs"] = deepcopy(candidate_refs)
        outcome["candidate_outcomes"] = [
            {
                "candidate_ref": deepcopy(ref),
                "status": candidate_status,
                "root_cause_ref": (
                    deepcopy(root_ref)
                    if candidate_status in {"bounded_root_match", "overstated_root_match"}
                    else None
                ),
            }
            for ref in candidate_refs
        ]
        outcome["detector_result_outcomes"][0]["evaluation_candidate_refs"] = deepcopy(
            candidate_refs
        )
    if root_status is None:
        outcome["fixture_kind"] = "verified_good_fixture"
        outcome["qualification_proof_family"] = "clean_execution"
        outcome["root_cause_refs"] = []
        outcome["root_outcomes"] = []
    else:
        outcome["fixture_kind"] = "positive_issue_fixture"
        outcome["qualification_proof_family"] = "positive_issue"
        outcome["root_cause_refs"] = [deepcopy(root_ref)]
        outcome["root_outcomes"] = [
            {
                "root_cause_ref": deepcopy(root_ref),
                "status": root_status,
                "matched_candidate_refs": (
                    deepcopy(candidate_refs)
                    if root_status in {"boundedly_localized", "localized_but_overstated"}
                    else []
                ),
            }
        ]
    return outcome


def _envelope() -> dict[str, Any]:
    return {
        "issue_classes": ["claim_result_disagreement"],
        "languages": ["Python", "Markdown"],
        "packages": [],
        "operation_forms": ["bounded_scalar_direction_comparison"],
    }


def _fixtures_for_outcomes(
    project_root: Path, outcomes: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    fixtures: list[dict[str, Any]] = []
    for outcome in outcomes:
        fixture = _example(project_root, "benchmark-fixture.example.json")
        fixture.update(
            {
                "fixture_id": outcome["fixture_ref"]["record_id"],
                "problem_id": outcome["problem_id"],
                "corpus_partition": outcome["corpus_partition"],
                "fixture_kind": outcome["fixture_kind"],
                "qualification_proof_status": outcome["qualification_proof_status"],
                "proof_evidence": (
                    None
                    if outcome["qualification_proof_status"]
                    == "legacy_proof_projection_unavailable"
                    else fixture["proof_evidence"]
                ),
            }
        )
        if outcome["fixture_kind"] == "positive_issue_fixture":
            fixture.update(
                {
                    "execution_evidence": "not_executed",
                    "expected_issue_labels": ["claim_result_disagreement"],
                    "expected_root_cause_refs": deepcopy(outcome["root_cause_refs"]),
                    "scientific_contract_refs": [],
                }
            )
            fixture["declared_scope"]["operation_refs"] = []
            fixture["proof_obligations"].update(
                {
                    "hard_negative_pattern_documented": False,
                    "decisive_innocent_explanation_documented": False,
                    "positive_root_cause_documented": True,
                }
            )
            if isinstance(fixture["proof_evidence"], dict):
                public = fixture["proof_evidence"]["public_inputs"]
                public["adjudicated_root_causes"] = [
                    {
                        "record_ref": deepcopy(outcome["root_cause_refs"][0]),
                        "semantic_digest": "sha256:" + "1" * 64,
                    }
                ]
                for field in (
                    "scientific_contracts",
                    "operations",
                    "environments",
                    "executions",
                    "sandbox_capabilities",
                ):
                    public[field] = []
        outcome["fixture_semantic_digest"] = semantic_digest(fixture)
        fixtures.append(fixture)
    return fixtures


def _build_metric_set(
    project_root: Path,
    outcomes: list[dict[str, Any]],
    envelope: dict[str, Any],
    schema_root: Path,
    **kwargs: Any,
) -> dict[str, Any]:
    fixtures = _fixtures_for_outcomes(project_root, outcomes)
    return build_qualification_metric_set(outcomes, fixtures, envelope, schema_root, **kwargs)


def _metric_map(metric_set: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["metric_name"]: item for item in metric_set["metrics"]}


def test_all_twelve_metrics_use_the_closed_disjoint_status_sets(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    outcomes = [
        _case(
            project_root,
            1,
            state="evaluation_finding_candidate",
            candidate_status="bounded_root_match",
            root_status="boundedly_localized",
        ),
        _case(
            project_root,
            2,
            state="evaluation_finding_candidate",
            candidate_status="false_root_localization",
            candidate_count=2,
        ),
        _case(
            project_root,
            3,
            state="evaluation_finding_candidate",
            candidate_status="overstated_root_match",
            root_status="localized_but_overstated",
        ),
        _case(project_root, 4, root_status="missed"),
        _case(project_root, 5),
        _case(
            project_root,
            6,
            state="not_applicable",
            applicability="not_applicable",
            coverage="not_covered",
        ),
        _case(
            project_root,
            7,
            state="insufficient_semantics",
            applicability="uncertain",
            coverage="unknown",
        ),
        _case(project_root, 8, state="execution_evidence_unavailable", coverage="unknown"),
        _case(project_root, 9, state="unsupported_path", coverage="not_covered"),
        _case(
            project_root, 10, state="detector_error", applicability="uncertain", coverage="unknown"
        ),
        _case(project_root, 11, comparison_excluded=True),
        _case(project_root, 12, legacy_incomplete=True),
    ]

    metric_set = _build_metric_set(
        project_root,
        outcomes,
        _envelope(),
        schema_root,
        generated_at="2026-07-28T22:00:00Z",
        output=tmp_path / "metrics.json",
    )
    replayed = _build_metric_set(
        project_root,
        list(reversed(outcomes)),
        _envelope(),
        schema_root,
        generated_at="2026-07-28T22:00:00Z",
        expected_metric_set=metric_set,
    )

    assert replayed == metric_set
    metrics = _metric_map(metric_set)
    expected_pairs = {
        "workflow_unsafe_candidate_probability": (2, 10),
        "completed_opportunity_false_positive_rate": (2, 9),
        "applicable_covered_opportunity_false_positive_rate": (2, 5),
        "finding_candidate_precision": (1, 4),
        "false_root_localization_rate": (2, 4),
        "overstatement_rate": (1, 4),
        "adjudicated_root_recall": (2, 3),
        "bounded_root_localization_accuracy": (1, 2),
        "abstention_rate": (2, 11),
        "unsupported_rate": (1, 11),
        "detector_error_rate": (1, 11),
        "unresolved_comparison_rate": (1, 11),
    }
    assert tuple(metrics) == METRIC_NAMES
    for name, (numerator, denominator) in expected_pairs.items():
        assert (metrics[name]["numerator"], metrics[name]["denominator"]) == (
            numerator,
            denominator,
        )
        assert metrics[name]["estimate"] == pytest.approx(numerator / denominator)
        assert (
            metrics[name]["interval"]["valid_replicates"]
            + metrics[name]["interval"]["invalid_replicates"]
            == 10_000
        )
        assert "Fewer than twenty problem clusters" in " ".join(
            metrics[name]["interval"]["limitations"]
        )

    assert metric_set["counts"] == {
        "problem_clusters": 12,
        "workflows": 12,
        "opportunities": 11,
        "applicable_covered_opportunities": 6,
        "evaluation_candidates": 4,
        "adjudicated_roots": 3,
        "bounded_root_matches": 1,
        "overstated_root_matches": 1,
        "false_root_localizations": 2,
        "boundedly_localized_roots": 1,
        "localized_but_overstated_roots": 1,
        "missed_roots": 1,
        "abstentions": 2,
        "unsupported_opportunities": 1,
        "detector_errors": 1,
        "unresolved_comparisons": 1,
    }
    assert len(metric_set["excluded_case_outcomes"]) == 2
    assert metric_set["promotion_permitted"] is False
    assert metric_set["promotion_evidence_eligible"] is False


def test_zero_denominators_are_null_and_duplicate_candidates_count_one_opportunity(
    project_root: Path, schema_root: Path
) -> None:
    no_issue = _case(project_root, 20)
    metric_set = _build_metric_set(
        project_root,
        [no_issue],
        _envelope(),
        schema_root,
        generated_at="2026-07-28T22:10:00Z",
    )
    metrics = _metric_map(metric_set)
    for name in (
        "finding_candidate_precision",
        "false_root_localization_rate",
        "overstatement_rate",
        "adjudicated_root_recall",
        "bounded_root_localization_accuracy",
    ):
        assert metrics[name]["denominator"] == 0
        assert metrics[name]["estimate"] is None
        assert metrics[name]["interval"]["status"] == "not_estimable"

    false_case = _case(
        project_root,
        21,
        state="evaluation_finding_candidate",
        candidate_status="false_root_localization",
        candidate_count=3,
    )
    false_set = _build_metric_set(
        project_root,
        [false_case],
        _envelope(),
        schema_root,
        generated_at="2026-07-28T22:11:00Z",
    )
    false_metrics = _metric_map(false_set)
    assert false_metrics["completed_opportunity_false_positive_rate"]["numerator"] == 1
    assert false_metrics["completed_opportunity_false_positive_rate"]["denominator"] == 1
    assert false_metrics["false_root_localization_rate"]["numerator"] == 3


def test_control_metrics_remain_separate_by_proof_family(project_root: Path) -> None:
    clean = _case(project_root, 90)
    external = _case(project_root, 91)
    external["fixture_kind"] = "scope_verified_good"
    external["qualification_proof_family"] = "documented_external_execution"
    static = _case(
        project_root,
        92,
        state="evaluation_finding_candidate",
        candidate_status="false_root_localization",
    )
    static["fixture_kind"] = "static_scope_verified_good"
    static["qualification_proof_family"] = "static_closed_scope"
    static["static_qualification_proof_ref"] = {
        "record_type": "static_qualification_proof",
        "record_id": "static-proof:metric-92",
    }

    evidence = core_metric_module.compile_qualification_evidence(
        [clean, external, static], _envelope()
    )
    strata = {item["proof_family"]: item for item in evidence["control_family_strata"]}
    assert {family: item["case_count"] for family, item in strata.items()} == {
        "clean_execution": 1,
        "documented_external_execution": 1,
        "static_closed_scope": 1,
    }
    by_family = {
        family: {metric["metric_name"]: metric for metric in item["metrics"]}
        for family, item in strata.items()
    }
    assert by_family["clean_execution"]["workflow_unsafe_candidate_probability"]["estimate"] == 0.0
    assert (
        by_family["static_closed_scope"]["workflow_unsafe_candidate_probability"]["estimate"] == 1.0
    )

    static["qualification_proof_family"] = "clean_execution"
    with pytest.raises(
        core_metric_module.QualificationMetricInvariantError,
        match="proof family conflicts",
    ):
        core_metric_module.compile_qualification_evidence([static], _envelope())


def test_problem_siblings_form_one_cluster_and_input_order_is_irrelevant(
    project_root: Path, schema_root: Path
) -> None:
    outcomes = [
        _case(project_root, 30, problem_id="problem:sibling"),
        _case(project_root, 31, problem_id="problem:sibling"),
        _case(project_root, 32, problem_id="problem:other"),
    ]
    first = _build_metric_set(
        project_root,
        outcomes,
        _envelope(),
        schema_root,
        generated_at="2026-07-28T22:20:00Z",
    )
    second = _build_metric_set(
        project_root,
        list(reversed(outcomes)),
        _envelope(),
        schema_root,
        generated_at="2026-07-28T22:20:00Z",
    )

    assert first == second
    assert first["problem_cluster_ids"] == ["problem:other", "problem:sibling"]
    assert first["counts"]["problem_clusters"] == 2
    sample = bootstrap_problem_sample(
        first["bootstrap"]["input_digest"], first["problem_cluster_ids"], 0
    )
    assert len(sample) == 2
    assert set(sample) <= {"problem:other", "problem:sibling"}


def test_bootstrap_counter_bytes_and_rejection_rule_are_fixed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    digest = "sha256:" + "00" * 32
    assert core_metric_module._counter_value(bytes(32), 3, 0, 0) == int(
        "cf9031d4ba3434535d559483d02de8052c4bba51a49e4a4beffa38a4b8cb1e0d", 16
    )
    assert [bootstrap_cluster_index(digest, 7, 3, position) for position in range(5)] == [
        1,
        1,
        1,
        2,
        2,
    ]

    calls = []
    limit = 2**256 - (2**256 % 3)

    def fake_counter(digest_bytes: bytes, replicate: int, position: int, retry: int) -> int:
        calls.append((digest_bytes, replicate, position, retry))
        return limit if retry == 0 else 5

    monkeypatch.setattr(core_metric_module, "_counter_value", fake_counter)
    assert bootstrap_cluster_index(digest, 3, 4, 5) == 2
    assert [call[3] for call in calls] == [0, 1]


def test_metric_admission_rejects_candidate_projection_mismatch(
    project_root: Path, schema_root: Path
) -> None:
    outcome = _case(
        project_root,
        40,
        state="evaluation_finding_candidate",
        candidate_status="bounded_root_match",
        root_status="boundedly_localized",
    )
    outcome["detector_result_outcomes"][0]["evaluation_candidate_refs"] = []

    with pytest.raises(QualificationMetricError, match="evaluation candidate"):
        _build_metric_set(
            project_root,
            [outcome],
            _envelope(),
            schema_root,
            generated_at="2026-07-28T22:30:00Z",
        )


def test_metric_cli_calculates_and_replays_byte_identically(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    outcomes = [_case(project_root, 50), _case(project_root, 51)]
    fixtures = _fixtures_for_outcomes(project_root, outcomes)
    outcome_paths = []
    for index, outcome in enumerate(outcomes):
        path = tmp_path / f"outcome-{index}.json"
        path.write_text(json.dumps(outcome), encoding="utf-8")
        outcome_paths.append(path)
    fixture_paths = []
    for index, fixture in enumerate(fixtures):
        path = tmp_path / f"fixture-{index}.json"
        path.write_text(json.dumps(fixture), encoding="utf-8")
        fixture_paths.append(path)
    envelope_path = tmp_path / "envelope.json"
    envelope_path.write_text(json.dumps(_envelope()), encoding="utf-8")
    shared = [
        "--case-outcome",
        str(outcome_paths[0]),
        "--case-outcome",
        str(outcome_paths[1]),
        "--fixture",
        str(fixture_paths[0]),
        "--fixture",
        str(fixture_paths[1]),
        "--qualification-envelope",
        str(envelope_path),
        "--schema-root",
        str(schema_root),
    ]
    metric_path = tmp_path / "metric-set.json"
    assert (
        evaluation_main(
            [
                "calculate-metrics",
                *shared,
                "--generated-at",
                "2026-07-28T22:40:00Z",
                "--output",
                str(metric_path),
            ]
        )
        == 0
    )
    replay_path = tmp_path / "metric-replay.json"
    assert (
        evaluation_main(
            [
                "replay-metrics",
                *shared,
                "--source-metric-set",
                str(metric_path),
                "--output",
                str(replay_path),
            ]
        )
        == 0
    )
    assert replay_path.read_bytes() == metric_path.read_bytes()
