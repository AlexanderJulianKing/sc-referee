"""Aggregation + the `simple` donor-aware paired recompute engine.

A gene with a strong, donor-consistent condition effect must survive the donor-level
(pseudobulk) test; a null gene must not. This is the recompute that replaces per-cell
Wilcoxon with a replicate-aware test."""
import numpy as np
import pandas as pd

from sc_referee.bundle import Bundle, Measure
from sc_referee.engine import aggregate_to_pseudobulk, simple_recompute
from tests.factories import make_design


N_BG = 30  # background genes so CPM normalization behaves like real data (stable library)


def _paired_bundle(n_donors=4, cells=12, seed=1):
    rng = np.random.default_rng(seed)
    genes = ["G_up", "G_null"] + [f"bg{i}" for i in range(N_BG)]
    obs_rows, counts_rows = [], []
    for di in range(n_donors):
        donor = f"D{di + 1}"
        for cond in ("ctrl", "stim"):
            for _ in range(cells):
                obs_rows.append((donor, cond))
                up = rng.poisson(10 if cond == "ctrl" else 40)  # strong, consistent up in stim (~2 log2FC)
                null = rng.poisson(20)                           # no condition effect
                bg = rng.poisson(30, size=N_BG)                  # stable background library
                counts_rows.append([up, null, *bg])
    obs = pd.DataFrame(obs_rows, columns=["donor_id", "condition"],
                       index=[f"c{i}" for i in range(len(obs_rows))])
    counts = np.array(counts_rows, dtype="int64")
    return Bundle(
        observations=obs,
        measure=Measure("counts", counts, None, genes),
        feature_metadata=pd.DataFrame(index=genes),
        replicate_var="donor_id",
    )


def _design():
    return make_design(sample_unit=("donor_id", "condition"), pairing_unit=("donor_id",))


def test_aggregate_to_pseudobulk_shapes():
    pb, meta = aggregate_to_pseudobulk(_paired_bundle(), _design())
    assert pb.shape[0] == 8  # 4 donors × 2 conditions
    assert "G_up" in pb.columns
    assert list(meta["condition"]).count("ctrl") == 4
    assert list(meta["condition"]).count("stim") == 4


def test_simple_recompute_detects_consistent_effect():
    pb, meta = aggregate_to_pseudobulk(_paired_bundle(), _design())
    res = simple_recompute(pb, meta, _design())

    assert res.mde_kind == "paired"
    assert res.n_replicates_per_arm == 4

    up = res.table.loc["G_up"]
    assert up.effect > 1.0 and bool(up.testable) and up.padj < 0.05

    null = res.table.loc["G_null"]
    assert null.padj > 0.05


def test_simple_recompute_effect_is_log2_scale():
    """ctrl~10 -> stim~40 is ~2 log2 units; effect must be on the log2 scale (~2), not ln."""
    pb, meta = aggregate_to_pseudobulk(_paired_bundle(), _design())
    res = simple_recompute(pb, meta, _design())
    assert 1.5 < res.table.loc["G_up"].effect < 2.5
