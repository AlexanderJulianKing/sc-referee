"""Hardening of the shared adapter helpers (`adapters/_common.py`).

These close two pre-existing silent-scope holes surfaced by the multi-file design review:
  - `measure_from_matrix` must not label a matrix `counts` just because its values are whole numbers:
    raw UMI counts are finite, non-negative integers. Negatives (log residuals), NaN/inf, or an
    all-zero library are NOT raw counts — a recompute on them is invalid, so they are `normalized`.
  - `detect_replicate_var` must prefer the BIOLOGICAL unit (donor/mouse/…) over a technical one
    (sample/replicate) when both are present, or it treats a 10x library as the replicate and
    pseudoreplication is checked at the wrong level.
"""
import numpy as np

from sc_referee.adapters._common import detect_replicate_var, measure_from_matrix

FEATS = ["g0", "g1", "g2"]


def _measure(vals):
    return measure_from_matrix(np.asarray(vals, dtype=float), FEATS)


def test_nonnegative_integer_matrix_is_counts():
    assert _measure([[0, 3, 1], [2, 0, 4]]).kind == "counts"


def test_whole_valued_floats_are_still_counts():
    # h5ad routinely stores raw counts as float 3.0 — must remain recompute-able.
    assert _measure([[0.0, 3.0], [2.0, 5.0]]).kind == "counts"


def test_negative_values_are_not_counts():
    # A negative "count" is a residual/normalized artefact, never a raw UMI.
    m = _measure([[1, 2, -1], [0, 3, 4]])
    assert m.kind == "normalized"
    assert m.counts is None


def test_nonfinite_values_are_not_counts():
    for bad in (np.nan, np.inf, -np.inf):
        m = _measure([[1.0, 2.0], [bad, 3.0]])
        assert m.kind == "normalized", bad
        assert m.counts is None


def test_all_zero_matrix_is_not_treated_as_valid_counts():
    # Empty library / degenerate matrix: nothing to recompute against.
    assert _measure([[0, 0], [0, 0]]).kind == "normalized"


def test_replicate_detection_prefers_biological_over_technical_unit():
    # sample_id (a 10x library) appears FIRST, but donor_id is the biological replicate.
    assert detect_replicate_var(["sample_id", "condition", "donor_id"]) == "donor_id"


def test_replicate_detection_falls_back_to_technical_when_no_biological():
    assert detect_replicate_var(["sample_id", "condition"]) == "sample_id"


def test_replicate_detection_absent_returns_none():
    assert detect_replicate_var(["barcode", "condition"]) is None
