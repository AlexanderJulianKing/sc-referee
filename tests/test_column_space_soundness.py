from __future__ import annotations

import numpy as np
import pytest

from sc_referee.column_space import CertificationState, certify_column_space


def _cert(c: np.ndarray, h: np.ndarray):
    h_2d = h[:, None] if h.ndim == 1 else h
    return certify_column_space(
        c,
        h,
        c_columns=tuple(f"c{i}" for i in range(c.shape[1])),
        excluded_exposure_columns=(),
        h_mapping=tuple(f"h{i}" for i in range(h_2d.shape[1])),
        row_ledger_identity="x",
        exact=True,
    )


def test_near_collinear_contained_direction_is_never_not_certified():
    x = np.linspace(-1.0, 1.0, 10)
    c = np.column_stack([np.ones(10), 1.0 + 1e-8 * x])
    h = (c[:, 1] - c[:, 0])[:, None]

    result = _cert(c, h)

    assert result.state in {CertificationState.CERTIFIED, CertificationState.NOT_AUDITED}


def test_rank_cutoff_discarded_contained_direction_abstains_from_accusation():
    x = np.linspace(-1.0, 1.0, 20)
    c = np.column_stack([np.ones(20), 1.0 + 1e-14 * x])
    h = (c[:, 1] - c[:, 0])[:, None]

    result = _cert(c, h)

    assert result.state is CertificationState.NOT_AUDITED
    assert result.machine_reason == "rank_deficient_ambiguous_span"
    assert result.witness is not None
    assert result.witness.rank_c == 1


def test_finite_extreme_scale_containment_never_becomes_not_certified():
    h = np.array([[1e200], [2e200], [3e200]])
    c = np.column_stack([np.ones(3), h[:, 0]])

    result = _cert(c, h)

    assert result.state in {CertificationState.CERTIFIED, CertificationState.NOT_AUDITED}


def test_each_required_direction_is_checked_without_frobenius_scale_masking():
    n = 8
    c = np.ones((n, 1))
    h = np.column_stack([np.full(n, 1e9), np.tile([-1.0, 1.0], 4)])

    result = _cert(c, h)

    assert result.state is CertificationState.NOT_CERTIFIED


@pytest.mark.parametrize(
    "h",
    [
        np.zeros((8, 1)),
        np.ones((8, 1)),
        np.column_stack([np.arange(8.0), np.arange(8.0)]),
    ],
)
def test_degenerate_required_basis_abstains(h):
    result = _cert(np.ones((8, 1)), h)

    assert result.state is CertificationState.NOT_AUDITED


@pytest.mark.parametrize("bad_value", [np.nan, np.inf, -np.inf])
def test_nonfinite_certificate_input_abstains(bad_value):
    c = np.column_stack([np.ones(8), np.arange(8.0)])
    h = np.arange(8.0)[:, None]
    h[3, 0] = bad_value

    result = _cert(c, h)

    assert result.state is CertificationState.NOT_AUDITED


def test_svd_failure_abstains(monkeypatch):
    def fail_svd(*args, **kwargs):
        raise np.linalg.LinAlgError("confirmed test failure")

    monkeypatch.setattr(np.linalg, "svd", fail_svd)
    result = _cert(
        np.column_stack([np.ones(8), np.arange(8.0)]),
        np.arange(8.0)[:, None],
    )

    assert result.state is CertificationState.NOT_AUDITED


def test_well_conditioned_sensitivity_is_preserved():
    alternating = np.tile([-1.0, 1.0], 4)[:, None]

    omitted = _cert(np.ones((8, 1)), alternating)
    contained = _cert(np.column_stack([np.ones(8), alternating]), alternating)

    assert omitted.state is CertificationState.NOT_CERTIFIED
    assert contained.state is CertificationState.CERTIFIED


def test_full_rank_design_with_genuinely_omitted_direction_is_not_certified():
    x = np.linspace(-1.0, 1.0, 20)
    c = np.column_stack([np.ones(20), x])
    omitted = np.tile([-1.0, 1.0], 10)[:, None]

    result = _cert(c, omitted)

    assert result.state is CertificationState.NOT_CERTIFIED
    assert result.witness is not None
    assert result.witness.rank_c == c.shape[1]


@pytest.mark.parametrize("condition_number", [1.0, 1e4, 1e8, 1e12])
def test_condition_sweep_has_one_sided_soundness(condition_number):
    x = np.linspace(-1.0, 1.0, 20)
    delta = 1.0 / condition_number
    c = np.column_stack([np.ones(20), 1.0 + delta * x])
    contained_h = (c[:, 1] - c[:, 0])[:, None]
    omitted_h = np.tile([-1.0, 1.0], 10)[:, None]

    contained = _cert(c, contained_h)
    omitted = _cert(c, omitted_h)

    assert contained.state is not CertificationState.NOT_CERTIFIED
    assert omitted.state is not CertificationState.CERTIFIED
