from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from sc_referee import statuses as S
from sc_referee.column_space import CertificationState, certify_column_space
from sc_referee.fitted_design import (
    FixedEffectReconstructionRequest,
    certificate_abstention_finding,
    certify_identity_nuisance,
    reconstruct_nuisance_design,
    request_from_confirmed_design,
)
from sc_referee.engine import build_pseudobulk_sample_rows
from tests.factories import fitted_design_declaration, make_design
from tests.test_simple_engine import _paired_bundle


def _rows():
    return pd.DataFrame(
        {
            "condition": [0.0, 0.0, 1.0, 1.0],
            "age": [20.0, 40.0, 60.0, 80.0],
            "age_shifted": [120.0, 140.0, 160.0, 180.0],
        },
        index=["s1", "s2", "s3", "s4"],
    )


def _request(**overrides):
    base = dict(
        rows_exact=True,
        row_ledger_identity="sha256:audited-samples-v1",
        operator_kind="ordinary_fixed_effects",
        intercept=True,
        column_kinds={"age": "continuous", "condition": "continuous"},
        categorical_levels={},
        transforms={"age": "identity", "condition": "identity"},
        exposure_columns=("condition",),
    )
    return FixedEffectReconstructionRequest(**(base | overrides))


def test_reconstructs_continuous_nuisance_with_intercept():
    result = reconstruct_nuisance_design(
        _rows(),
        make_design(analyst_adjusted_for=["age", "condition"]),
        _request(),
    )
    assert result.exact
    assert result.artifact.c_column_ids == ("intercept", "age")
    assert result.artifact.matrix_digest.startswith("sha256:")
    np.testing.assert_array_equal(result.artifact.c[:, 1], _rows()["age"])


def test_exposure_is_excluded_so_z_equal_e_cannot_certify_trivially():
    reconstruction = reconstruct_nuisance_design(
        _rows(),
        make_design(analyst_adjusted_for=["age", "condition"]),
        _request(),
    )
    certificate = certify_identity_nuisance(reconstruction, _rows(), "condition")

    assert "condition" not in reconstruction.artifact.c_source_columns
    assert reconstruction.artifact.excluded_exposure_columns == ("condition",)
    assert certificate.state is CertificationState.NOT_CERTIFIED


def test_different_name_same_column_space_still_certifies():
    reconstruction = reconstruct_nuisance_design(
        _rows(), make_design(analyst_adjusted_for=["age"]), _request()
    )
    certificate = certify_identity_nuisance(reconstruction, _rows(), "age_shifted")
    assert certificate.state is CertificationState.CERTIFIED


@pytest.mark.parametrize(
    ("design", "reconstruction_request", "reason"),
    [
        (make_design(analyst_adjusted_for=None), _request(), "not ratified"),
        (
            make_design(
                analyst_adjusted_for=["age"],
                confidence={"analyst_adjusted_for": "low"},
            ),
            _request(),
            "not ratified",
        ),
        (
            make_design(analyst_adjusted_for=["age"], confirmed=False),
            _request(),
            "not ratified",
        ),
        (make_design(analyst_adjusted_for=["missing"]), _request(), "missing"),
        (
            make_design(analyst_adjusted_for=["age"]),
            _request(rows_exact=False),
            "row",
        ),
        (
            make_design(analyst_adjusted_for=["age"]),
            _request(row_ledger_identity=None),
            "row",
        ),
        (
            make_design(analyst_adjusted_for=["age"]),
            _request(operator_kind="random_intercept_only"),
            "no verified conditioning operator found",
        ),
        (
            make_design(analyst_adjusted_for=["age"]),
            _request(weight_role="exposure"),
            "weight",
        ),
        (
            make_design(analyst_adjusted_for=["age"]),
            _request(offset_role="exposure"),
            "offset",
        ),
        (
            make_design(analyst_adjusted_for=["age"]),
            _request(transforms={"age": "spline"}),
            "unsupported transform",
        ),
    ],
)
def test_inexact_or_unsupported_reconstruction_abstains(
    design, reconstruction_request, reason
):
    result = reconstruct_nuisance_design(_rows(), design, reconstruction_request)
    assert result.state is CertificationState.NOT_AUDITED
    assert not result.exact
    assert result.artifact is None
    assert reason in result.reason.lower()


def test_nonfinite_nuisance_abstains_without_assuming_a_row_drop():
    rows = _rows()
    rows.loc["s2", "age"] = np.nan
    result = reconstruct_nuisance_design(
        rows, make_design(analyst_adjusted_for=["age"]), _request()
    )

    assert result.state is CertificationState.NOT_AUDITED
    assert result.artifact is None
    assert "row dropping could not be verified" in result.reason.lower()


@pytest.mark.parametrize(
    "adjusted",
    [
        ["age", "missing"],
        ["age", "age"],
        ["age", "scale(age)"],
    ],
)
def test_one_invalid_or_duplicate_adjustment_invalidates_the_atomic_artifact(adjusted):
    result = reconstruct_nuisance_design(
        _rows(), make_design(analyst_adjusted_for=adjusted), _request()
    )
    assert result.state is CertificationState.NOT_AUDITED
    assert result.artifact is None


def test_categorical_exposure_is_excluded_before_all_dummy_coding():
    rows = pd.DataFrame(
        {
            "condition": ["ctrl", "stim", "other", "ctrl"],
            "age": [20.0, 40.0, 60.0, 80.0],
        },
        index=["s1", "s2", "s3", "s4"],
    )
    request = _request(
        column_kinds={"age": "continuous", "condition": "categorical"},
        categorical_levels={"condition": ("ctrl", "stim", "other")},
    )
    result = reconstruct_nuisance_design(
        rows,
        make_design(analyst_adjusted_for=["age", "condition"]),
        request,
    )

    assert result.exact
    assert result.artifact.c_column_ids == ("intercept", "age")
    assert all("condition" not in column for column in result.artifact.c_column_ids)
    assert result.artifact.excluded_exposure_columns == ("condition",)


def test_confirmed_empty_adjustment_builds_intercept_only_c():
    request = _request(column_kinds={}, transforms={})
    result = reconstruct_nuisance_design(
        _rows(), make_design(analyst_adjusted_for=[]), request
    )

    assert result.exact
    assert result.artifact.c_column_ids == ("intercept",)
    np.testing.assert_array_equal(result.artifact.c, np.ones((4, 1)))


def test_changed_row_order_refuses_certification_without_arithmetic_witness():
    reconstruction = reconstruct_nuisance_design(
        _rows(), make_design(analyst_adjusted_for=["age"]), _request()
    )
    reordered = _rows().iloc[::-1]
    certificate = certify_identity_nuisance(reconstruction, reordered, "age_shifted")

    assert certificate.state is CertificationState.NOT_AUDITED
    assert certificate.witness is None
    assert "row identity" in certificate.reason.lower()


def test_missing_or_nonfinite_identity_candidate_abstains():
    reconstruction = reconstruct_nuisance_design(
        _rows(), make_design(analyst_adjusted_for=["age"]), _request()
    )
    missing = certify_identity_nuisance(reconstruction, _rows(), "missing")
    nonfinite_rows = _rows()
    nonfinite_rows.loc["s1", "age_shifted"] = np.inf
    nonfinite = certify_identity_nuisance(
        reconstruction, nonfinite_rows, "age_shifted"
    )

    assert missing.state is CertificationState.NOT_AUDITED
    assert nonfinite.state is CertificationState.NOT_AUDITED
    assert missing.witness is nonfinite.witness is None


def test_random_intercept_abstention_renders_not_checked_never_flagged():
    reconstruction = reconstruct_nuisance_design(
        _rows(),
        make_design(analyst_adjusted_for=["age"]),
        _request(operator_kind="random_intercept_only"),
    )
    finding = certificate_abstention_finding(
        "latent_confounder_v3", reconstruction
    )

    assert finding.status == S.NOT_AUDITED
    assert finding.coverage == S.NOT_RUN
    assert S.human_state(finding) == S.NOT_CHECKED
    assert "no verified conditioning operator found" in finding.verdict.lower()
    assert "biased" not in finding.verdict.lower()
    assert finding.metrics["column_space_state"] == "not_audited"


def _certificate_fixture(state):
    if state is CertificationState.CERTIFIED:
        # A genuinely-certified, non-degenerate case: H is the ramp column of C
        # (in span, well-conditioned, with real between-row variation). A constant
        # H (e.g. ones) now correctly abstains as degenerate_h under the
        # conditioning-aware certificate, so it is no longer a CERTIFIED fixture.
        return certify_column_space(
            np.column_stack([np.ones(4), np.array([0.0, 1.0, 2.0, 3.0])]),
            np.array([0.0, 1.0, 2.0, 3.0])[:, None],
            c_columns=("intercept", "ramp"),
            excluded_exposure_columns=(),
            h_mapping=("z:identity",),
            row_ledger_identity="sha256:rows",
            exact=True,
        )
    return certify_column_space(
        np.ones((4, 1)),
        np.array([-1.0, 1.0, -1.0, 1.0])[:, None],
        c_columns=("intercept",),
        excluded_exposure_columns=(),
        h_mapping=("z:identity",),
        row_ledger_identity="sha256:rows",
        exact=True,
    )


@pytest.mark.parametrize(
    "state", [CertificationState.CERTIFIED, CertificationState.NOT_CERTIFIED]
)
def test_geometry_outcomes_cannot_be_turned_into_findings_without_consumer_policy(state):
    certificate = _certificate_fixture(state)
    with pytest.raises(ValueError, match="consumer policy"):
        certificate_abstention_finding("confounding_strong", certificate)


def test_confirmed_ordinary_pseudobulk_declaration_builds_request():
    design = make_design(
        sample_unit=("donor_id", "condition"),
        aggregation_key=("donor_id", "condition"),
        analyst_adjusted_for=["run", "condition"],
        fitted_design=fitted_design_declaration(),
        confidence={"condition": "high", "batch": "high", "analyst_adjusted_for": "high",
                    "aggregation_key": "high", "fitted_design": "high"},
    )
    bundle = _paired_bundle()
    bundle.observations["run"] = ["R1", "R1"] * (len(bundle.observations) // 2)
    rows = build_pseudobulk_sample_rows(bundle.observations, design)
    request = request_from_confirmed_design(design, rows)
    assert request.operator_kind == "ordinary_fixed_effects"
    assert request.rows_exact is True
    assert request.row_ledger_identity == rows.row_ledger_identity
    assert request.exposure_columns == ("condition",)


def test_missing_fitted_declaration_builds_abstaining_request_without_parsing_model():
    design = make_design(
        model="~ condition + (1 | donor_id)", aggregation_key=("donor_id", "condition"),
        analyst_adjusted_for=["condition"], fitted_design=None,
    )
    rows = build_pseudobulk_sample_rows(_paired_bundle().observations, design)
    request = request_from_confirmed_design(design, rows)
    assert request.operator_kind == "unsupported"


def test_interaction_formula_cannot_be_represented_as_ordinary_additive_identity():
    design = make_design(
        model="~ lane_bit1 * lane_bit2 + condition",
        analyst_adjusted_for=["lane_bit1", "lane_bit2", "condition"],
        fitted_design=fitted_design_declaration(
            column_kinds={"lane_bit1": "continuous", "lane_bit2": "continuous",
                          "condition": "continuous"},
            categorical_levels={},
            transforms={"lane_bit1": "identity", "lane_bit2": "identity",
                        "condition": "identity"},
        ),
        confidence={"analyst_adjusted_for": "high", "fitted_design": "high"},
    )
    request = request_from_confirmed_design(design, type("Rows", (), {
        "exact": True, "row_ledger_identity": "sha256:rows"
    })())
    assert request.operator_kind == "unsupported"
    assert request.unsupported_reason == "unsupported_nonadditive_operator"
    assert request.unsupported_reason
