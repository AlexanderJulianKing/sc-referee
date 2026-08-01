from __future__ import annotations

import json
from pathlib import Path

import pytest
from sc_referee_evaluation.cli import main
from sc_referee_evaluation.source_method_probe import (
    SourceMethodProbeError,
    probe_python_method_shapes,
)

from sc_referee.core.ids import sha256_digest

REFERENCE_DIGEST = sha256_digest(b"answer-side reference method")
DIAGNOSED_AT = "2026-07-29T23:30:00Z"

FAILED_SOURCE = """
def emission(obs, p, error_scale):
    e = obs.seq_error * error_scale
    q_read_derived = e + (1.0 - 2.0 * e) * p
    return q_read_derived


def call_sample(t3, t4):
    high_3 = t3["vaf"] >= 0.20
    high_4 = t4["vaf"] >= 0.20
    one_high = high_3 != high_4
    two_high_same_phase = (
        high_3 and high_4 and t3["phase_set"] == t4["phase_set"]
    )
    class_03 = one_high or two_high_same_phase
    return class_03


def corrected_prevalence(positive_rate, sensitivity, false_positive_rate):
    return clamp_probability(
        (positive_rate - false_positive_rate)
        / (sensitivity - false_positive_rate)
    )


def estimate_screening(positive_rates, sensitivity, false_positive_rate):
    class_prevalence = [
        corrected_prevalence(
            positive_rates[index], sensitivity[index], false_positive_rate[index]
        )
        for index in range(3)
    ]
    return sum(class_prevalence)


def estimate_partner(cells, sensitivity, false_positive_rate):
    standardized_positive_rates = [0.0, 0.0, 0.0]
    for weight, rates in cells:
        for index in range(3):
            standardized_positive_rates[index] += weight * rates[index]
    class_prevalence = [
        corrected_prevalence(
            standardized_positive_rates[index],
            sensitivity[index],
            false_positive_rate[index],
        )
        for index in range(3)
    ]
    return sum(class_prevalence)
"""

CORRECTED_CONTROL_SOURCE = """
def emission(p, e_da, e_ad):
    q_read_derived = (1.0 - e_da) * p + e_ad * (1.0 - p)
    return q_read_derived


def call_sample(high_3, high_4, phase_3, phase_4):
    class_03 = (
        high_3
        and high_4
        and phase_3 is not None
        and phase_4 is not None
        and phase_3 == phase_4
    )
    return class_03


def solve_coupled_class_prevalence(positive_rates, sensitivity, false_positive_rate):
    return joint_nonnegative_solution(positive_rates, sensitivity, false_positive_rate)


def estimate_partner(cells, sensitivity, false_positive_rate):
    standardized_prevalence = [0.0, 0.0, 0.0]
    for weight, positive_rates in cells:
        calibrated_cell_prevalence = solve_coupled_class_prevalence(
            positive_rates, sensitivity, false_positive_rate
        )
        standardized_prevalence[0] += weight * calibrated_cell_prevalence[0]
    return sum(standardized_prevalence)
"""

QTL_DIRECT_ORIENTATION_SOURCE = """
def emission_matrix(obs, founder_alleles, error):
    match = obs[:, None] == founder_alleles[None, :]
    return where(match, 1.0 - error, error)


def hmm(genotypes, founder_alleles, error):
    return emission_matrix(genotypes[:, 0], founder_alleles[0], error)
"""

POPGEN_CALLED_EXPOSURE_SOURCE = """
def fit(rr, bridge_gaps):
    LA = sum(r["length"] for r in rr if r["anc"] == "A")
    LB = sum(r["length"] for r in rr if r["anc"] == "B")
    p = LA / (LA + LB)
    n = count_switches(rr, bridge_gaps)
    t = n / ((1 - p) * LA + p * LB)
    return {
        "called_exposure_morgan": LA + LB,
        "pulse_time_generations": t,
    }
"""

MVMR_LD_AWARE_SOURCE = """
def fit(y_se, r_selected, x, y):
    covariance_y = diag(y_se) @ r_selected @ diag(y_se)
    chol = linalg.cholesky(covariance_y)
    x_white = linalg.solve(chol, x)
    y_white = linalg.solve(chol, y)
    theta = lstsq(x_white, y_white)[0]
    residual = y_white - x_white @ theta
    return theta, residual
"""

ORIGINAL_PROFILE_IDS = [
    "directional_measurement_error_v1",
    "phased_composite_marker_v1",
    "mutually_exclusive_class_calibration_v1",
    "cellwise_calibration_before_standardization_v1",
]


def _run_probe(
    tmp_path: Path,
    source_text: str,
    name: str,
    profile_ids: list[str] | None = None,
) -> dict[str, object]:
    source_root = tmp_path / name
    source_root.mkdir()
    (source_root / "analysis.py").write_text(source_text, encoding="utf-8")
    return probe_python_method_shapes(
        source_root,
        "analysis.py",
        profile_ids or ORIGINAL_PROFILE_IDS,
        reference_id=f"genebench-public:{name}:reference-method",
        reference_content_digest=REFERENCE_DIGEST,
        diagnosed_at=DIAGNOSED_AT,
        output=tmp_path / f"{name}.json",
    )


def test_static_probe_localizes_all_four_exact_failed_shapes(tmp_path: Path) -> None:
    diagnostic = _run_probe(tmp_path, FAILED_SOURCE, "failed")

    results = {
        str(item["profile_id"]): item
        for item in diagnostic["results"]  # type: ignore[union-attr]
    }
    assert set(results) == set(ORIGINAL_PROFILE_IDS)
    assert {item["state"] for item in results.values()} == {"exact_static_conflict"}
    assert all(item["evidence"] for item in results.values())
    assert all(
        item["causal_attribution"] == "not_established_by_static_probe" for item in results.values()
    )
    assert diagnostic["project_code_executed_by_probe"] is False
    assert diagnostic["model_invoked_by_probe"] is False
    assert diagnostic["production_finding_eligible"] is False
    assert diagnostic["promotion_evidence_eligible"] is False


def test_static_probe_recognizes_closed_corrected_controls(tmp_path: Path) -> None:
    diagnostic = _run_probe(tmp_path, CORRECTED_CONTROL_SOURCE, "corrected")

    results = diagnostic["results"]
    assert isinstance(results, list)
    assert {item["state"] for item in results} == {"covered_negative"}
    assert all(item["observed_form"] == item["expected_form"] for item in results)


def test_static_probe_preserves_unrecognized_source_as_unsupported(tmp_path: Path) -> None:
    diagnostic = _run_probe(
        tmp_path,
        "def mean(values):\n    return sum(values) / len(values)\n",
        "unsupported",
    )

    results = diagnostic["results"]
    assert isinstance(results, list)
    assert {item["state"] for item in results} == {"unsupported_path"}
    assert all(item["evidence"] == [] for item in results)


@pytest.mark.parametrize(
    ("name", "source", "profile_id", "state"),
    [
        (
            "qtl-orientation",
            QTL_DIRECT_ORIENTATION_SOURCE,
            "ril_founder_orientation_before_emission_v1",
            "exact_static_conflict",
        ),
        (
            "popgen-exposure",
            POPGEN_CALLED_EXPOSURE_SOURCE,
            "full_map_ancestry_exposure_v1",
            "exact_static_conflict",
        ),
        (
            "mvmr-ld-aware",
            MVMR_LD_AWARE_SOURCE,
            "ld_covariance_before_robust_fit_v1",
            "covered_negative",
        ),
        (
            "crispr-unsupported",
            "def robust_slope(x, y):\n    return sum(x * y) / sum(x * x)\n",
            "full_map_ancestry_exposure_v1",
            "unsupported_path",
        ),
    ],
)
def test_posthoc_profiles_localize_only_their_closed_source_shapes(
    tmp_path: Path,
    name: str,
    source: str,
    profile_id: str,
    state: str,
) -> None:
    diagnostic = _run_probe(tmp_path, source, name, [profile_id])

    result = diagnostic["results"][0]  # type: ignore[index]
    assert result["state"] == state
    assert bool(result["evidence"]) is (state != "unsupported_path")
    assert diagnostic["project_code_executed_by_probe"] is False
    assert diagnostic["production_finding_eligible"] is False


def test_static_probe_fails_closed_on_profile_path_and_write_mutations(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "workspace"
    source_root.mkdir()
    (source_root / "analysis.py").write_text(FAILED_SOURCE, encoding="utf-8")
    common = {
        "reference_id": "genebench-public:mutation:reference-method",
        "reference_content_digest": REFERENCE_DIGEST,
        "diagnosed_at": DIAGNOSED_AT,
    }

    with pytest.raises(SourceMethodProbeError, match="unique probe profiles"):
        probe_python_method_shapes(
            source_root,
            "analysis.py",
            ["directional_measurement_error_v1"] * 2,
            output=tmp_path / "duplicate.json",
            **common,
        )
    with pytest.raises(SourceMethodProbeError, match="unsupported probe profiles"):
        probe_python_method_shapes(
            source_root,
            "analysis.py",
            ["open_ended_scientific_review"],
            output=tmp_path / "unknown.json",
            **common,
        )
    with pytest.raises(SourceMethodProbeError, match="relative Python path"):
        probe_python_method_shapes(
            source_root,
            "../analysis.py",
            ["directional_measurement_error_v1"],
            output=tmp_path / "escape.json",
            **common,
        )
    (source_root / "linked.py").symlink_to(source_root / "analysis.py")
    with pytest.raises(SourceMethodProbeError, match="non-symlink"):
        probe_python_method_shapes(
            source_root,
            "linked.py",
            ["directional_measurement_error_v1"],
            output=tmp_path / "linked.json",
            **common,
        )
    existing = tmp_path / "existing.json"
    existing.write_text("{}\n", encoding="utf-8")
    with pytest.raises(SourceMethodProbeError, match="already exists"):
        probe_python_method_shapes(
            source_root,
            "analysis.py",
            ["directional_measurement_error_v1"],
            output=existing,
            **common,
        )


def test_static_probe_cli_writes_canonical_diagnostic(tmp_path: Path) -> None:
    source_root = tmp_path / "workspace"
    source_root.mkdir()
    (source_root / "analysis.py").write_text(FAILED_SOURCE, encoding="utf-8")
    output = tmp_path / "diagnostic.json"

    exit_code = main(
        [
            "probe-python-method-shapes",
            "--source-root",
            str(source_root),
            "--source",
            "analysis.py",
            "--profile",
            "directional_measurement_error_v1",
            "--reference-id",
            "genebench-public:cli:reference-method",
            "--reference-content-digest",
            REFERENCE_DIGEST,
            "--diagnosed-at",
            DIAGNOSED_AT,
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    persisted = json.loads(output.read_text(encoding="utf-8"))
    assert persisted["results"][0]["state"] == "exact_static_conflict"
