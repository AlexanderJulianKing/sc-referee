import hashlib
import pickle

import numpy as np
import pandas as pd

from sc_referee.engine import aggregate_to_pseudobulk, build_pseudobulk_sample_rows
from sc_referee.row_ledger import RowsExactBasis
from tests.factories import make_design
from tests.test_simple_engine import _design, _paired_bundle


LEGACY_PAIRED_AGGREGATE_SHA256 = "d4b59224cebddfe7c0a7bdb0768705b00de09aa44b8f1c2c96ebd11afe257447"


def test_aggregate_to_pseudobulk_legacy_pickle_is_frozen():
    bundle, design = _paired_bundle(), _design()
    pb, meta = aggregate_to_pseudobulk(bundle, design)
    payload = pickle.dumps((pb, meta), protocol=5)
    assert hashlib.sha256(payload).hexdigest() == LEGACY_PAIRED_AGGREGATE_SHA256


def test_recompute_aggregation_observable_characterization_is_exact():
    bundle, design = _paired_bundle(), _design()
    pb, meta = aggregate_to_pseudobulk(bundle, design)
    obs, counts = bundle.observations, bundle.measure.counts
    keys = [key for key in design.sample_unit if key in obs.columns]
    contrast, _, _ = design.contrast_column_and_levels()
    carry = [column for column in dict.fromkeys(
        keys + [contrast] + list(design.pairing_unit or []) + list(design.batch)
        + list(design.replicate_unit)
    ) if column in obs.columns]
    expected_pb_rows, expected_meta_rows = [], []
    for positions in obs.groupby(keys, sort=False, observed=True).indices.values():
        expected_pb_rows.append(counts[positions].sum(axis=0))
        first = obs.iloc[positions[0]]
        expected_meta_rows.append({column: first[column] for column in carry})
    expected_pb = pd.DataFrame(expected_pb_rows, columns=bundle.measure.feature_index)
    expected_meta = pd.DataFrame(expected_meta_rows)
    pd.testing.assert_frame_equal(pb, expected_pb)
    pd.testing.assert_frame_equal(meta, expected_meta)
    assert pickle.dumps((pb, meta), protocol=5) == pickle.dumps((expected_pb, expected_meta), protocol=5)


def test_recompute_and_fitted_audit_share_sample_rows_and_order():
    bundle = _paired_bundle()
    design = make_design(
        sample_unit=("donor_id", "condition"),
        aggregation_key=("donor_id", "condition"),
        batch=(),
        analyst_adjusted_for=["condition"],
    )
    rows = build_pseudobulk_sample_rows(bundle.observations, design)
    pb, meta = aggregate_to_pseudobulk(bundle, design)
    pd.testing.assert_frame_equal(meta.reset_index(drop=True), rows.rows.reset_index(drop=True))
    assert rows.row_ledger_identity.startswith("sha256:")
    assert rows.rows_exact_basis is RowsExactBasis.HUMAN_DECLARED
    np.testing.assert_array_equal(
        pb.to_numpy(),
        np.vstack([bundle.measure.counts[pos].sum(axis=0) for pos in rows.group_positions]),
    )


def test_varying_carried_column_is_inexact_not_first_row_wins():
    bundle = _paired_bundle()
    design = make_design(
        sample_unit=("donor_id",), aggregation_key=("donor_id",),
        analyst_adjusted_for=["condition"],
    )
    rows = build_pseudobulk_sample_rows(bundle.observations, design)
    assert not rows.exact
    assert rows.machine_reason == "within_sample_column_variation"
    assert rows.rows_exact_basis is RowsExactBasis.UNAVAILABLE
