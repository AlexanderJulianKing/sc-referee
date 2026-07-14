"""Inject ONE methodological error at a time into an otherwise-correct analysis.

The point is to test the DETECTOR, not the models: given a dataset with planted truth, emit a
clean analysis and a family of analyses each carrying exactly one named defect. sc-referee
should pass the clean one and flag each defect — and where it cannot, we learn what to build.

Error classes are drawn from what reasoning-era models actually do wrong
(see the research notes), not from intuition.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

from bench.analyses import per_cell_wilcoxon
from sc_referee.design import Design


# --------------------------------------------------------------------------- #
# reported-table variants (the analysis the scientist claims they did)
# --------------------------------------------------------------------------- #
def _long(feature_ids, pvalue, padj, effect):
    return pd.DataFrame({"feature_id": list(feature_ids), "pvalue": pvalue, "padj": padj, "effect": effect})


def reported_clean(res, lfc_cut: float = 1.0) -> pd.DataFrame:
    """CORRECT: donor-level pseudobulk, NB count model, FDR + an effect-size threshold."""
    t = res.table
    padj = t["padj"].to_numpy(dtype=float).copy()
    small = np.abs(t["effect"].to_numpy(dtype=float)) < lfc_cut
    padj[small | ~np.isfinite(padj)] = 1.0          # genes below the effect cut are not claimed
    return _long(t.index, t["pvalue"].to_numpy(), padj, t["effect"].to_numpy())


def reported_pseudoreplication(adata) -> pd.DataFrame:
    """DEFECT: cells as replicates (per-cell Wilcoxon). What weak models still do."""
    return per_cell_wilcoxon(adata)


def reported_count_model(pb: pd.DataFrame, meta: pd.DataFrame, design: Design) -> pd.DataFrame:
    """DEFECT: aggregates to pseudobulk CORRECTLY, then runs a t-test on log2(CPM+1)
    instead of an NB count model. This is the measured gpt-5.4 / gpt-5.5 failure."""
    contrast_col, ref, test = design.contrast_column_and_levels()
    counts = pb.values.astype(float)
    lib = counts.sum(axis=1, keepdims=True)
    lib[lib == 0] = np.nan
    lcpm = np.log2(counts / lib * 1e6 + 1.0)

    arm = meta[contrast_col].to_numpy()
    a, b = lcpm[arm == test], lcpm[arm == ref]
    tstat, p = stats.ttest_ind(a, b, axis=0, equal_var=False)
    p = np.nan_to_num(p, nan=1.0)
    padj = multipletests(p, method="fdr_bh")[1]
    effect = a.mean(axis=0) - b.mean(axis=0)
    return _long(pb.columns, p, padj, effect)


def reported_no_fdr(res) -> pd.DataFrame:
    """DEFECT: never applied multiple-testing correction — reports raw p < 0.05."""
    t = res.table
    p = t["pvalue"].to_numpy(dtype=float)
    return _long(t.index, p, p, t["effect"].to_numpy())      # padj := raw p


def reported_no_effect_cut(res) -> pd.DataFrame:
    """DEFECT: FDR-only significance, no |log2FC| threshold. gpt-5.5 was penalized for this."""
    t = res.table
    return _long(t.index, t["pvalue"].to_numpy(), t["padj"].to_numpy(), t["effect"].to_numpy())


def reported_negligible_effects(n_sig: int = 190, n_null: int = 310, seed: int = 0) -> pd.DataFrame:
    """DEFECT: significance without an effect-size gate, on a WELL-POWERED dataset — most 'significant'
    genes carry a negligible |log2FC| (fold-change ≈ 1). The muscat sim can't show this (it plants
    effect=1), so we synthesize the high-power continuum a no-effect-gate report produces: a properly
    BH-corrected table (so multiple_testing is satisfied) whose claimed discoveries are dominated by
    negligible effects — isolating the effect-size failure."""
    rng = np.random.default_rng(seed)
    sig_eff = rng.normal(0.0, 0.08, size=n_sig)           # mostly |log2FC| < 0.25 (negligible)
    sig_eff[:10] = rng.choice([-1.6, 1.6], size=10)       # a handful of genuinely large effects
    sig_p = rng.uniform(1e-8, 1e-5, size=n_sig)
    sig_padj = np.clip(sig_p * 50, 1e-7, 0.02)            # a legitimate BH-like padj >= p (corrected)
    null_eff = rng.normal(0.0, 0.10, size=n_null)
    null_p = rng.uniform(0.10, 1.0, size=n_null)
    ids = [f"g{i}" for i in range(n_sig + n_null)]
    return _long(ids,
                 np.concatenate([sig_p, null_p]),
                 np.concatenate([sig_padj, null_p]),
                 np.concatenate([sig_eff, null_eff]))


# --------------------------------------------------------------------------- #
# design-level defects (they corrupt the DATA, not the reported table)
# --------------------------------------------------------------------------- #
def add_batch(adata, aliased: bool):
    """Attach a processing_run. aliased=True -> run is perfectly confounded with condition."""
    obs = adata.obs
    donors = list(dict.fromkeys(obs["donor_id"]))
    if aliased:
        cond_of = obs.groupby("donor_id", observed=True)["condition"].first()
        run = {d: ("R1" if cond_of[d] == "ctrl" else "R2") for d in donors}
    else:
        run = {d: ("R1" if i % 2 == 0 else "R2") for i, d in enumerate(donors)}  # crossed
    adata.obs = obs.assign(processing_run=obs["donor_id"].map(run).astype(str))
    return adata


def batched_design(base: Design) -> Design:
    from dataclasses import replace
    return replace(base, batch=["processing_run"])
