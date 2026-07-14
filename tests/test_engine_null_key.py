import numpy as np
import pandas as pd
import pytest

from sc_referee import statuses as S
from sc_referee.checks.contamination_confound import ContaminationConfoundCheck
from sc_referee.checks.experimental_unit import evaluate_experimental_unit
from sc_referee.design_matrix import build_fixed_effect_matrix
from sc_referee.engine import build_pseudobulk_sample_rows
from tests.contamination_factories import contamination_case
from tests.factories import make_design
from tests.test_simple_engine import _paired_bundle


def _fitted_design():
    return make_design(
        sample_unit=("donor_id", "condition"),
        aggregation_key=("donor_id", "condition"),
        batch=(),
        analyst_adjusted_for=["condition"],
    )


def _legacy_expected_rows(observations, design):
    keys = list(design.aggregation_key)
    contrast_col, _, _ = design.contrast_column_and_levels()
    carry_sources = (
        keys + [contrast_col] + list(design.pairing_unit or []) + list(design.batch)
        + list(design.replicate_unit) + list(design.analyst_adjusted_for or [])
    )
    carry = [column for column in dict.fromkeys(carry_sources) if column in observations.columns]
    positions = tuple(
        observations.groupby(keys, sort=False, observed=True).indices.values()
    )
    rows = pd.DataFrame(
        [
            {column: observations.iloc[group_positions[0]][column] for column in carry}
            for group_positions in positions
        ],
        columns=carry,
    )
    identities = [tuple(row[key] for key in keys) for _, row in rows.iterrows()]
    rows.index = pd.Index(np.asarray(identities, dtype=object), name="sample_identity")
    digest = build_fixed_effect_matrix(
        rows, source_columns=(), column_kinds={}, categorical_levels={}, intercept=False
    ).row_identity.digest
    return rows, positions, digest


@pytest.mark.parametrize("invalid_identity", [None, np.nan, np.inf, -np.inf])
def test_invalid_aggregation_identity_is_not_exact_and_is_not_silently_dropped(
    invalid_identity,
):
    observations = _paired_bundle().observations.copy()
    observations.iloc[0, observations.columns.get_loc("donor_id")] = invalid_identity

    result = build_pseudobulk_sample_rows(observations, _fitted_design())

    assert not result.exact
    assert result.machine_reason == "invalid_aggregation_key_value"
    assert result.rows.empty
    assert result.group_positions == ()


def test_null_aggregation_identity_makes_contamination_check_abstain():
    design, bundle = contamination_case(adjusted=("condition",), ratified=True)
    bundle.observations.loc[bundle.observations.index[0], "donor_id"] = None

    finding = ContaminationConfoundCheck().run(design, bundle)

    assert finding.coverage == S.NOT_RUN
    assert S.human_state(finding) == S.NOT_CHECKED
    assert finding.metrics["machine_reason"] == "ratified_scope_or_rows_mismatch"


def test_well_formed_rows_and_ledger_identity_are_byte_stable():
    observations = _paired_bundle().observations
    design = _fitted_design()
    expected_rows, expected_positions, expected_digest = _legacy_expected_rows(observations, design)

    result = build_pseudobulk_sample_rows(observations, design)

    assert result.exact
    pd.testing.assert_frame_equal(result.rows, expected_rows)
    assert result.row_ledger_identity == expected_digest
    for actual, expected in zip(result.group_positions, expected_positions, strict=True):
        np.testing.assert_array_equal(actual, expected)


def test_well_formed_group_positions_are_an_exact_partition():
    observations = _paired_bundle().observations
    result = build_pseudobulk_sample_rows(observations, _fitted_design())

    flattened = np.concatenate(result.group_positions)
    np.testing.assert_array_equal(np.sort(flattened), np.arange(len(observations)))
    assert len(np.unique(flattened)) == len(observations)


def _legacy_extra_key_case(*, null_batch):
    bundle = _paired_bundle()
    donor_number = bundle.observations["donor_id"].str.removeprefix("D").astype(int)
    bundle.observations["condition"] = np.where(donor_number % 2, "ctrl", "stim")
    bundle.observations["batch"] = "B" + donor_number.astype(str)
    if null_batch:
        bundle.observations.loc[bundle.observations.index[0], "batch"] = None
    design = make_design(
        sample_unit=("donor_id",),
        aggregation_key=("donor_id", "batch"),
        batch=("batch",),
        pairing_unit=(),
    )
    return bundle, design


def test_legacy_recompute_rejects_null_in_extra_ratified_aggregation_key():
    bundle, design = _legacy_extra_key_case(null_batch=True)

    result = build_pseudobulk_sample_rows(
        bundle.observations, design, recompute_legacy=True,
    )

    assert not result.exact
    assert result.machine_reason == "invalid_aggregation_key_value"
    assert result.rows.empty
    assert result.group_positions == ()

    genes = list(bundle.measure.feature_index)
    reported = pd.DataFrame({
        "feature_id": genes,
        "pvalue": [1e-6] + [0.5] * (len(genes) - 1),
        "padj": [1e-4] + [0.6] * (len(genes) - 1),
        "effect": [2.0] + [0.0] * (len(genes) - 1),
    })
    finding = evaluate_experimental_unit(design, bundle, reported, engine="simple")
    assert finding.status == S.NEEDS_EVIDENCE
    assert finding.coverage == S.NOT_RUN
    assert S.human_state(finding) == S.NOT_CHECKED


def test_well_formed_legacy_extra_aggregation_key_preserves_rows_and_identity():
    bundle, design = _legacy_extra_key_case(null_batch=False)
    observations = bundle.observations
    expected_positions = tuple(
        observations.groupby(["donor_id"], sort=False, observed=True).indices.values()
    )
    expected_rows = pd.DataFrame([
        {
            "donor_id": observations.iloc[positions[0]]["donor_id"],
            "condition": observations.iloc[positions[0]]["condition"],
            "batch": observations.iloc[positions[0]]["batch"],
        }
        for positions in expected_positions
    ], columns=["donor_id", "condition", "batch"])
    expected_rows.index = pd.Index(
        np.asarray([(value,) for value in expected_rows["donor_id"]], dtype=object),
        name="sample_identity",
    )
    expected_identity = build_fixed_effect_matrix(
        expected_rows, source_columns=(), column_kinds={}, categorical_levels={}, intercept=False,
    ).row_identity.digest

    result = build_pseudobulk_sample_rows(
        observations, design, recompute_legacy=True,
    )

    assert result.exact
    pd.testing.assert_frame_equal(result.rows, expected_rows)
    assert result.row_ledger_identity == expected_identity
    for actual, expected in zip(result.group_positions, expected_positions, strict=True):
        np.testing.assert_array_equal(actual, expected)
