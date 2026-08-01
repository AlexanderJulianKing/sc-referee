from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from sc_referee_evaluation.cli import main
from sc_referee_evaluation.posthoc_review import (
    PosthocValidationReviewError,
    build_posthoc_validation_review,
)
from sc_referee_evaluation.source_method_probe import probe_python_method_shapes

from sc_referee.core.ids import sha256_digest

APPROVAL_DIGEST = sha256_digest("I approve the four scoped validation Answers.")
REFERENCE_DIGEST = sha256_digest(b"evaluation-only public reference report")
REVIEWED_AT = "2026-07-29T18:00:00Z"

QTL_SOURCE = """
def emission_matrix(obs, founder_alleles, error):
    match = obs[:, None] == founder_alleles[None, :]
    return where(match, 1.0 - error, error)


def hmm(genotypes, founder_alleles, error):
    return emission_matrix(genotypes[:, 0], founder_alleles[0], error)
"""

POPGEN_SOURCE = """
def fit(rr, bridge_gaps):
    LA = sum(r["length"] for r in rr if r["anc"] == "A")
    LB = sum(r["length"] for r in rr if r["anc"] == "B")
    p = LA / (LA + LB)
    n = count_switches(rr, bridge_gaps)
    t = n / ((1 - p) * LA + p * LB)
    return {"called_exposure_morgan": LA + LB, "pulse_time_generations": t}
"""

MVMR_SOURCE = """
def fit(y_se, r_selected, x, y):
    covariance_y = diag(y_se) @ r_selected @ diag(y_se)
    chol = linalg.cholesky(covariance_y)
    x_white = linalg.solve(chol, x)
    y_white = linalg.solve(chol, y)
    theta = lstsq(x_white, y_white)[0]
    residual = y_white - x_white @ theta
    return theta, residual
"""

CASES = [
    (
        "multiparent_qtl_hmm_lmm",
        QTL_SOURCE,
        "ril_founder_orientation_before_emission_v1",
        "scale_and_orientation",
        "repair_ril_founder_orientation_before_hmm_emission",
        "exact_conflict_candidate",
    ),
    (
        "popgen_recent_pulse_sexbias",
        POPGEN_SOURCE,
        "full_map_ancestry_exposure_v1",
        "denominator_or_universe",
        "full_chromosome_map_exposure",
        "exact_conflict_candidate",
    ),
    (
        "statgen_cis_mvmr_winnerscurse_scaling_ldaware",
        MVMR_SOURCE,
        "ld_covariance_before_robust_fit_v1",
        "measurement_model",
        "ld_covariance_cholesky_whitening_before_robust_fit",
        "covered_negative",
    ),
]


def _probe(
    tmp_path: Path,
    case_id: str,
    source: str,
    profile_ids: list[str],
) -> dict[str, object]:
    root = tmp_path / f"{case_id}-workspace"
    root.mkdir()
    (root / "analysis.py").write_text(source, encoding="utf-8")
    return probe_python_method_shapes(
        root,
        "analysis.py",
        profile_ids,
        reference_id=f"genebench-public:{case_id}:report-public",
        reference_content_digest=REFERENCE_DIGEST,
        diagnosed_at="2026-07-29T17:00:00Z",
        output=tmp_path / f"{case_id}-probe.json",
    )


def _structured_spec(
    case_id: str,
    profile_id: str,
    dimension: str,
    normalized_value: str,
) -> dict[str, object]:
    return {
        "case_id": case_id,
        "scientist_answer": {
            "answer_kind": "structured",
            "profile_id": profile_id,
            "dimension": dimension,
            "comparison_form": "value_equals",
            "normalized_value": normalized_value,
            "respondent": {
                "actor_kind": "human",
                "actor_id": "scientist:repository-owner",
            },
            "approval_statement_digest": APPROVAL_DIGEST,
        },
    }


def _unknown_spec(case_id: str) -> dict[str, object]:
    return {
        "case_id": case_id,
        "scientist_answer": {
            "answer_kind": "unknown",
            "profile_id": None,
            "dimension": None,
            "comparison_form": None,
            "normalized_value": None,
            "respondent": {
                "actor_kind": "human",
                "actor_id": "scientist:repository-owner",
            },
            "approval_statement_digest": APPROVAL_DIGEST,
        },
    }


@pytest.mark.parametrize(
    ("case_id", "source", "profile_id", "dimension", "requirement", "outcome"), CASES
)
def test_structured_answers_compile_to_exact_bounded_outcomes(
    tmp_path: Path,
    case_id: str,
    source: str,
    profile_id: str,
    dimension: str,
    requirement: str,
    outcome: str,
) -> None:
    probe = _probe(tmp_path, case_id, source, [profile_id])
    spec = _structured_spec(case_id, profile_id, dimension, requirement)

    first = build_posthoc_validation_review(
        probe,
        spec,
        reviewed_at=REVIEWED_AT,
        output=tmp_path / f"{case_id}-review.json",
    )
    second = build_posthoc_validation_review(
        deepcopy(probe),
        deepcopy(spec),
        reviewed_at=REVIEWED_AT,
        output=tmp_path / f"{case_id}-replay.json",
    )

    assert first == second
    assert first["posthoc_validation_review_version"] == "0.2.0"
    assert first["review_outcome"] == outcome
    assert first["ledger"]["outcome"] == outcome  # type: ignore[index]
    assert first["production_intent_authority"] is False
    assert first["production_finding_eligible"] is False
    assert first["promotion_evidence_eligible"] is False
    assert first["project_code_executed"] is False
    assert first["model_invoked"] is False


def test_unknown_answer_does_not_invent_a_profile_dimension_or_assertion(tmp_path: Path) -> None:
    case_id = "crispri_casrx_transcript_vs_locus"
    profiles = [
        "ril_founder_orientation_before_emission_v1",
        "full_map_ancestry_exposure_v1",
        "ld_covariance_before_robust_fit_v1",
    ]
    probe = _probe(tmp_path, case_id, "def robust_slope(x, y):\n    return x + y\n", profiles)

    review = build_posthoc_validation_review(
        probe,
        _unknown_spec(case_id),
        reviewed_at=REVIEWED_AT,
        output=tmp_path / "crispr-review.json",
    )

    assert review["review_outcome"] == "unresolved_obligation"
    assert review["coverage_status"] == "unknown"
    assert review["profile_result"] is None
    assert review["ledger"] is None
    assert review["scientist_answer"]["dimension"] is None  # type: ignore[index]
    assert review["production_finding_eligible"] is False


def test_review_identity_binds_review_timestamp(tmp_path: Path) -> None:
    case_id, source, profile_id, dimension, requirement, _ = CASES[2]
    probe = _probe(tmp_path, case_id, source, [profile_id])
    spec = _structured_spec(case_id, profile_id, dimension, requirement)

    first = build_posthoc_validation_review(
        probe,
        spec,
        reviewed_at="2026-07-29T18:00:00Z",
        output=tmp_path / "timestamp-first.json",
    )
    second = build_posthoc_validation_review(
        probe,
        spec,
        reviewed_at="2026-07-29T18:00:01Z",
        output=tmp_path / "timestamp-second.json",
    )

    assert first["review_id"] != second["review_id"]
    assert first["review_digest"] != second["review_digest"]


def test_false_self_compliance_does_not_override_static_source_conflict(tmp_path: Path) -> None:
    case_id, source, profile_id, dimension, requirement, _ = CASES[0]
    probe = _probe(tmp_path, case_id, source, [profile_id])
    spec = _structured_spec(case_id, profile_id, dimension, requirement)
    report_text = (
        "The workflow repairs RIL founder orientation before constructing HMM emissions.\n"
    )
    spec["repository_self_declaration"] = {
        "dimension": dimension,
        "normalized_value": requirement,
        "source_ref": {
            "source_kind": "file_span",
            "path": "report.md",
            "locator": "report.md:1",
            "content_digest": sha256_digest(report_text),
            "start_line": 1,
            "end_line": 1,
            "quoted_text": report_text.strip(),
        },
    }

    review = build_posthoc_validation_review(
        probe,
        spec,
        reviewed_at=REVIEWED_AT,
        output=tmp_path / "false-self-compliance-review.json",
    )

    assert review["review_outcome"] == "exact_conflict_candidate"
    assert review["self_compliance_check"] == {
        "state": "contradicted_by_static_source_shape",
        "declaration_establishes_execution": False,
        "declaration_overrides_static_source": False,
    }
    assert review["production_finding_eligible"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        "probe_digest",
        "wrong_case_scope",
        "wrong_requirement",
        "wrong_dimension_form",
        "profile_absent",
        "unknown_overload",
    ],
)
def test_review_mutations_fail_closed(tmp_path: Path, mutation: str) -> None:
    case_id, source, profile_id, dimension, requirement, _ = CASES[0]
    probe = _probe(tmp_path, case_id, source, [profile_id])
    spec = _structured_spec(case_id, profile_id, dimension, requirement)
    if mutation == "probe_digest":
        probe["source_method_probe_version"] = "tampered"
    elif mutation == "wrong_case_scope":
        spec["case_id"] = "other-case"
    elif mutation == "wrong_requirement":
        spec["scientist_answer"]["normalized_value"] = "invented"  # type: ignore[index]
    elif mutation == "wrong_dimension_form":
        spec["scientist_answer"]["dimension"] = "target_population"  # type: ignore[index]
        spec["scientist_answer"]["comparison_form"] = "step_precedes"  # type: ignore[index]
    elif mutation == "profile_absent":
        spec["scientist_answer"]["profile_id"] = "full_map_ancestry_exposure_v1"  # type: ignore[index]
        spec["scientist_answer"]["dimension"] = "denominator_or_universe"  # type: ignore[index]
        spec["scientist_answer"]["normalized_value"] = "full_chromosome_map_exposure"  # type: ignore[index]
    else:
        spec = _unknown_spec(case_id)
        spec["scientist_answer"]["dimension"] = "measurement_model"  # type: ignore[index]

    with pytest.raises(PosthocValidationReviewError):
        build_posthoc_validation_review(
            probe,
            spec,
            reviewed_at=REVIEWED_AT,
            output=tmp_path / f"{mutation}.json",
        )


def test_review_is_write_once_and_cli_exposes_the_compiler(tmp_path: Path) -> None:
    case_id, source, profile_id, dimension, requirement, _ = CASES[2]
    _probe(tmp_path, case_id, source, [profile_id])
    spec = _structured_spec(case_id, profile_id, dimension, requirement)
    spec_path = tmp_path / "review-spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    output = tmp_path / "cli-review.json"

    assert (
        main(
            [
                "compile-posthoc-validation-review",
                "--source-probe",
                str(tmp_path / f"{case_id}-probe.json"),
                "--review-spec",
                str(spec_path),
                "--reviewed-at",
                REVIEWED_AT,
                "--output",
                str(output),
            ]
        )
        == 0
    )
    assert output.is_file()
    assert (
        main(
            [
                "compile-posthoc-validation-review",
                "--source-probe",
                str(tmp_path / f"{case_id}-probe.json"),
                "--review-spec",
                str(spec_path),
                "--reviewed-at",
                REVIEWED_AT,
                "--output",
                str(output),
            ]
        )
        == 2
    )
