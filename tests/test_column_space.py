from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from sc_referee.column_space import (
    NUMERIC_POLICY_V1,
    CertificationState,
    _certification_state_for_rho,
    certify_column_space,
    residualize,
)


def test_continuous_vector_is_residualized_not_dummy_coded():
    c = np.array([[1.0, 0.0], [1.0, 1.0], [1.0, 2.0], [1.0, 3.0]])
    v = np.array([4.0, 7.0, 10.0, 13.0])

    result = residualize(c, v)

    np.testing.assert_allclose(result.residual, 0.0, atol=1e-12)
    assert result.rank_c == 2
    assert result.rank_values == 1
    assert result.residual.shape == v.shape
    assert result.policy_version == NUMERIC_POLICY_V1.version


def test_rank_deficient_c_uses_its_column_space_once():
    x = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
    c = np.column_stack([np.ones(5), x, 2.0 * x])
    values = np.column_stack([3.0 + 4.0 * x, x**2])

    result = residualize(c, values)

    assert result.rank_c == 2
    np.testing.assert_allclose(result.residual[:, 0], 0.0, atol=1e-12)
    np.testing.assert_allclose(
        result.residual[:, 1], np.array([2.0, -1.0, -2.0, -1.0, 2.0]), atol=1e-12
    )


def test_empty_c_is_identity_projection():
    values = np.arange(6.0).reshape(3, 2)
    result = residualize(np.empty((3, 0)), values)
    np.testing.assert_array_equal(result.residual, values)
    assert result.rank_c == 0


def test_repeated_calls_are_equal_and_do_not_mutate_inputs():
    c = np.column_stack([np.ones(4), np.arange(4.0)])
    values = np.arange(8.0).reshape(4, 2)
    original_c = c.copy()
    original_values = values.copy()

    first = residualize(c, values)
    second = residualize(c, values)

    np.testing.assert_array_equal(first.residual, second.residual)
    assert first.n_rows == second.n_rows
    assert first.c_columns == second.c_columns
    assert first.value_columns == second.value_columns
    assert first.rank_c == second.rank_c
    assert first.rank_values == second.rank_values
    assert first.policy_version == second.policy_version
    np.testing.assert_array_equal(c, original_c)
    np.testing.assert_array_equal(values, original_values)


@pytest.mark.parametrize(
    ("c", "v"),
    [
        (np.ones((3, 1)), np.ones(2)),
        (np.array([[1.0], [np.nan]]), np.ones(2)),
        (np.ones((2, 1)), np.array([1.0, np.inf])),
        (np.ones((2, 1), dtype=bool), np.ones(2)),
        (np.ones((2, 1)), np.ones(2, dtype=object)),
        (np.ones((2, 1)), np.ones(2, dtype=complex)),
    ],
)
def test_invalid_numeric_inputs_are_rejected(c, v):
    with pytest.raises(ValueError):
        residualize(c, v)


@pytest.mark.parametrize(
    ("c", "v"),
    [
        (np.ones(3), np.ones(3)),
        (np.ones((3, 1, 1)), np.ones(3)),
        (np.ones((3, 1)), np.ones((3, 1, 1))),
    ],
)
def test_invalid_dimensions_are_rejected(c, v):
    with pytest.raises(ValueError):
        residualize(c, v)


def _cert(c, h, **overrides):
    kwargs = dict(
        c_columns=("intercept", "age"),
        excluded_exposure_columns=("condition[stim]",),
        h_mapping=("candidate_z:identity",),
        row_ledger_identity="sha256:rows-v1",
        exact=True,
    )
    return certify_column_space(c, h, **(kwargs | overrides))


def test_column_space_equivalent_coding_certifies_by_span():
    z = np.array([-1.0, -1.0, 1.0, 1.0])[:, None]
    treatment = np.column_stack([np.ones(4), np.array([0.0, 0.0, 1.0, 1.0])])
    sum_coding = np.column_stack([np.ones(4), z[:, 0]])

    a = _cert(treatment, z)
    b = _cert(sum_coding, z, c_columns=("intercept", "group_sum_code"))

    assert a.state is b.state is CertificationState.CERTIFIED
    assert a.witness.rho == pytest.approx(0.0, abs=1e-12)
    assert b.witness.rho == pytest.approx(0.0, abs=1e-12)


def test_outside_span_is_geometry_only_not_certified():
    c = np.ones((4, 1))
    z = np.array([-1.0, 1.0, -1.0, 1.0])[:, None]
    result = _cert(c, z, c_columns=("intercept",))

    assert result.state is CertificationState.NOT_CERTIFIED
    assert result.witness.rho == pytest.approx(1.0)
    assert not hasattr(result, "bias")
    assert not hasattr(result, "severity")


def test_witness_is_complete_immutable_and_digest_stable():
    c = np.column_stack([np.ones(4), np.arange(4.0)])
    h = np.arange(4.0)[:, None]
    first = _cert(c, h)
    second = _cert(c.copy(), h.copy())

    assert dataclasses.asdict(first.witness) == dataclasses.asdict(second.witness)
    assert first.witness.tau == 1e-8
    assert first.witness.epsilon == 1e-12
    assert first.witness.norm_name == "frobenius"
    assert first.witness.precision == "float64"
    assert first.witness.c_shape == (4, 2)
    assert first.witness.h_shape == (4, 1)
    assert first.witness.residual_shape == (4, 1)
    assert first.witness.rank_c == 2
    assert first.witness.rank_h == 1
    assert first.witness.c_columns == ("intercept", "age")
    assert first.witness.h_mapping == ("candidate_z:identity",)
    assert first.witness.excluded_exposure_columns == ("condition[stim]",)
    assert first.witness.row_ledger_identity == "sha256:rows-v1"
    assert len(first.witness.c_digest.removeprefix("sha256:")) == 64
    assert len(first.witness.h_digest.removeprefix("sha256:")) == 64
    assert len(first.witness.residual_digest.removeprefix("sha256:")) == 64
    with pytest.raises(dataclasses.FrozenInstanceError):
        first.witness.rho = 1.0


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"exact": False}, "inexact"),
        ({"unsupported_reason": "unsupported transform: spline"}, "unsupported transform"),
    ],
)
def test_inexact_or_unsupported_abstains_without_witness(overrides, reason):
    result = _cert(np.ones((4, 1)), np.arange(4.0)[:, None], **overrides)
    assert result.state is CertificationState.NOT_AUDITED
    assert result.witness is None
    assert result.machine_reason
    assert reason in result.reason.lower()


def test_epsilon_floor_h_is_not_vacuously_certified():
    result = _cert(
        np.ones((4, 1)), np.zeros((4, 1)), c_columns=("intercept",)
    )
    assert result.state is CertificationState.NOT_AUDITED
    assert result.witness is None
    assert "degenerate" in result.reason.lower()


def test_empty_h_is_not_audited_without_exception():
    result = _cert(
        np.ones((4, 1)), np.empty((4, 0)),
        c_columns=("intercept",), h_mapping=(),
    )

    assert result.state is CertificationState.NOT_AUDITED
    assert result.machine_reason == "empty_h"
    assert result.witness is None


def test_digest_changes_with_row_order_or_matrix_value():
    c = np.column_stack([np.ones(4), np.arange(4.0)])
    h = np.array([0.0, 1.0, 3.0, 2.0])[:, None]
    original = _cert(c, h)
    reordered = _cert(c[::-1], h[::-1])
    changed_c = c.copy()
    changed_c[0, 1] = 0.5
    changed = _cert(changed_c, h)

    assert original.witness.c_digest != reordered.witness.c_digest
    assert original.witness.h_digest != reordered.witness.h_digest
    assert original.witness.c_digest != changed.witness.c_digest
    assert original.witness.h_digest == changed.witness.h_digest


def test_rho_equal_to_tau_is_certified_by_inclusive_policy():
    assert (
        _certification_state_for_rho(NUMERIC_POLICY_V1.tau, NUMERIC_POLICY_V1)
        is CertificationState.CERTIFIED
    )


@pytest.mark.parametrize(
    "overrides",
    [
        {"c_columns": ("intercept",)},
        {"h_mapping": ()},
        {"row_ledger_identity": ""},
    ],
)
def test_invalid_witness_metadata_is_rejected_before_arithmetic(overrides):
    with pytest.raises(ValueError):
        _cert(np.ones((4, 2)), np.ones((4, 1)), **overrides)


def test_scale_1e9_cutoff_dependent_span_is_not_audited():
    h = np.tile([0.0, 1.0], 32)
    x1 = 1e9 + np.arange(64, dtype=float)
    x2 = x1 + 2.0 * h
    c = np.column_stack([np.ones(64), x1, x2])
    result = _cert(c, h[:, None], c_columns=("intercept", "x1", "x2"))
    assert result.state is CertificationState.NOT_AUDITED
    assert result.machine_reason == "ill_conditioned_span_ambiguous"
    assert result.witness is not None
