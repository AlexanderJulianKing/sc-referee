"""Frozen tests for the pure GB-P07 public contamination estimator."""
from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from io import BytesIO
import os
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd
import pytest

from sc_referee.derivations.genebench_gbp07_public_estimator import (
    Abstained,
    CellCountsView,
    EmptyDropletCountsView,
    Estimated,
    EstimatorAbstentionReason,
    TypedCellId,
    TypedDonorId,
    canonical_float_digest,
    estimate_genebench_gbp07_public_contamination,
)


def _donor(value: str) -> TypedDonorId:
    return TypedDonorId("gbp07-donor", value)


def _cell(value: str) -> TypedCellId:
    return TypedCellId("gbp07-cell", value)


def _synthetic_inputs():
    empty = EmptyDropletCountsView(
        total_umi=np.array([40, 60], dtype=np.uint64),
        panel_gene_names=("HBB", "IFI6"),
        panel_counts=np.array([[20, 10], [30, 15]], dtype=np.uint64),
    )
    cells = CellCountsView(
        cell_id=tuple(_cell(value) for value in ("c1", "c2", "c3", "c4")),
        donor=(_donor("d2"), _donor("d1"), _donor("d2"), _donor("d3")),
        total_umi=np.array([100, 100, 100, 100], dtype=np.uint64),
        hbb=np.array([5, 9, 40, 0], dtype=np.uint64),
    )
    # Deliberately nonlexical: output order is this fitted-unit ledger, exactly.
    order = (_donor("d3"), _donor("d1"), _donor("d2"))
    return empty, cells, order


def _reason(result) -> EstimatorAbstentionReason:
    assert isinstance(result, Abstained)
    return result.reason_code


def test_canonical_float_digest_quantizes_only_within_documented_budget():
    baseline = np.array([0.12345678901234, -0.0], dtype=np.float64)
    below_budget = np.array([0.12345678901235, 0.0], dtype=np.float64)
    above_budget = np.array([0.12345679901234, 0.0], dtype=np.float64)

    assert canonical_float_digest("test", baseline) == canonical_float_digest(
        "test", below_budget
    )
    assert canonical_float_digest("test", baseline) != canonical_float_digest(
        "test", above_budget
    )


def test_synthetic_estimator_math_immutability_and_abstentions():
    empty, cells, order = _synthetic_inputs()
    result = estimate_genebench_gbp07_public_contamination(empty, cells, order)
    assert isinstance(result, Estimated)
    artifact = result.artifact

    assert [(entry.gene, entry.ambient_fraction) for entry in artifact.ambient_profile] == [
        ("HBB", 0.5),
        ("IFI6", 0.25),
    ]
    assert artifact.ambient_hbb == 0.5
    assert artifact.cell_scores == pytest.approx([0.1, 0.18, 0.5, 0.0])
    assert [row.fitted_unit_id for row in artifact.donor_table] == list(order)
    assert [row.donor_rho for row in artifact.donor_table] == pytest.approx([0.0, 0.18, 0.3])
    assert [row.high_contamination for row in artifact.donor_table] == [False, False, True]
    assert [int(row.member_cell_count) for row in artifact.donor_table] == [1, 1, 2]
    assert artifact.donor_table[1].donor_rho == HIGH_PRECISION_STRICT_BOUNDARY
    assert artifact.donor_table[1].high_contamination is False  # strict > 0.18
    for digest in (
        artifact.digests.ambient_profile_digest,
        artifact.digests.per_cell_score_vector_digest,
        artifact.digests.donor_aggregation_ledger,
        artifact.digests.donor_score_digest,
        artifact.digests.binary_basis_digest,
        artifact.digests.artifact_identity,
        artifact.artifact_identity,
    ):
        assert digest.startswith("sha256:") and len(digest) == 71
    assert artifact.artifact_identity == artifact.digests.artifact_identity
    repeated = estimate_genebench_gbp07_public_contamination(empty, cells, order)
    assert isinstance(repeated, Estimated)
    assert repeated.artifact.artifact_identity == artifact.artifact_identity

    with pytest.raises(FrozenInstanceError):
        artifact.threshold = 0.2
    with pytest.raises(FrozenInstanceError):
        artifact.donor_table[0].donor_rho = 1.0
    with pytest.raises(ValueError):
        artifact.cell_scores[0] = 1.0

    empty_input = replace(empty, total_umi=np.array([], dtype=np.uint64), panel_counts=np.empty((0, 2), dtype=np.uint64))
    assert _reason(estimate_genebench_gbp07_public_contamination(empty_input, cells, order)) is EstimatorAbstentionReason.EMPTY_INPUT

    zero_empty_total = replace(empty, total_umi=np.array([0, 0], dtype=np.uint64))
    assert _reason(estimate_genebench_gbp07_public_contamination(zero_empty_total, cells, order)) is EstimatorAbstentionReason.ZERO_DENOMINATOR

    zero_ambient_hbb = replace(empty, panel_counts=np.array([[0, 10], [0, 15]], dtype=np.uint64))
    assert _reason(estimate_genebench_gbp07_public_contamination(zero_ambient_hbb, cells, order)) is EstimatorAbstentionReason.ZERO_DENOMINATOR

    zero_cell_total = replace(cells, total_umi=np.array([0, 100, 100, 100], dtype=np.uint64))
    assert _reason(estimate_genebench_gbp07_public_contamination(empty, zero_cell_total, order)) is EstimatorAbstentionReason.ZERO_DENOMINATOR

    missing_donor = replace(cells, donor=(None, *cells.donor[1:]))
    assert _reason(estimate_genebench_gbp07_public_contamination(empty, missing_donor, order)) is EstimatorAbstentionReason.MISSING_DONOR

    unknown_donor = replace(cells, donor=(_donor("unknown"), *cells.donor[1:]))
    assert _reason(estimate_genebench_gbp07_public_contamination(empty, unknown_donor, order)) is EstimatorAbstentionReason.MISSING_DONOR

    duplicate_donor_order = (order[0], order[0], order[1], order[2])
    assert _reason(estimate_genebench_gbp07_public_contamination(empty, cells, duplicate_donor_order)) is EstimatorAbstentionReason.DUPLICATE_DONOR

    non_finite = replace(cells, hbb=np.array([5.0, np.nan, 40.0, 0.0]))
    assert _reason(estimate_genebench_gbp07_public_contamination(empty, non_finite, order)) is EstimatorAbstentionReason.NON_FINITE_VALUE


# Written as a named constant so the exact strict-boundary assertion remains legible.
HIGH_PRECISION_STRICT_BOUNDARY = 0.18


def _gbp07_zip() -> Path:
    override = os.environ.get("GBP07_ZIP")
    return Path(override).expanduser() if override else Path.home() / "Desktop/genebench_phase1_inputs/GB-P07-data.zip"


def _read_release(path: Path):
    with ZipFile(path) as archive:
        cells = pd.read_csv(BytesIO(archive.read("cells.csv.gz")), compression="gzip")
        donors = pd.read_csv(BytesIO(archive.read("donors.csv.gz")), compression="gzip")
        empty = pd.read_csv(BytesIO(archive.read("empty_drops.csv.gz")), compression="gzip")
    return cells, donors, empty


def _restricted_inputs(cells: pd.DataFrame, donors: pd.DataFrame, empty: pd.DataFrame):
    panel_genes = ("HBB", "IFI6", "ISG15", "LST1", "CXCL10")
    empty_view = EmptyDropletCountsView(
        total_umi=empty["total_umi"].to_numpy(dtype=np.uint64),
        panel_gene_names=panel_genes,
        panel_counts=empty.loc[:, panel_genes].to_numpy(dtype=np.uint64),
    )
    cell_view = CellCountsView(
        cell_id=tuple(TypedCellId("gbp07-cell", str(value)) for value in cells["cell_id"]),
        donor=tuple(TypedDonorId("gbp07-donor", str(value)) for value in cells["donor"]),
        total_umi=cells["total_umi"].to_numpy(dtype=np.uint64),
        hbb=cells["HBB"].to_numpy(dtype=np.uint64),
    )
    # The caller supplies fitted-unit order explicitly from the donor authority.
    donor_order = tuple(TypedDonorId("gbp07-donor", str(value)) for value in donors["donor"])
    return empty_view, cell_view, donor_order


@pytest.mark.skipif(
    not _gbp07_zip().exists(),
    reason="GB-P07 data not present — set GBP07_ZIP; see bench/gbp07_anchor.py",
)
def test_real_release_frozen_oracle_and_poison_invariance():
    cells, donors, empty = _read_release(_gbp07_zip())
    inputs = _restricted_inputs(cells, donors, empty)
    result = estimate_genebench_gbp07_public_contamination(*inputs)
    assert isinstance(result, Estimated)
    artifact = result.artifact

    # Frozen tolerance: much tighter than release precision, but permits platform
    # rounding in the final float64 division only.
    assert artifact.ambient_hbb == pytest.approx(0.07032225253132368, rel=0.0, abs=1e-15)
    low = [row.donor_rho for row in artifact.donor_table if not row.high_contamination]
    high = [row.donor_rho for row in artifact.donor_table if row.high_contamination]
    assert len(low) == len(high) == 12
    assert min(low) == pytest.approx(0.081613, abs=2e-6)
    assert max(low) == pytest.approx(0.131710, abs=2e-6)
    assert min(high) == pytest.approx(0.242539, abs=2e-6)
    assert max(high) == pytest.approx(0.347323, abs=2e-6)
    assert max(low) < 0.18 < min(high)  # nonempty open gap straddles the registry threshold

    # Poison fields exist only in source frames. Rebuilding the restricted views
    # cannot expose them to the estimator, so their mutation cannot affect identity.
    poisoned_cells = cells.copy()
    poisoned_donors = donors.copy()
    poisoned_cells["fake_submitted_result"] = np.linspace(-1e9, 1e9, len(poisoned_cells))
    poisoned_cells["fake_reference_answer"] = "wrong"
    poisoned_donors["g"] = 2 - poisoned_donors["g"]
    poisoned_cells["fake_submitted_result"] *= -17
    poisoned_cells["fake_reference_answer"] = "also-wrong"
    poisoned = estimate_genebench_gbp07_public_contamination(
        *_restricted_inputs(poisoned_cells, poisoned_donors, empty)
    )
    assert isinstance(poisoned, Estimated)
    assert poisoned.artifact.artifact_identity.encode("ascii") == artifact.artifact_identity.encode("ascii")
