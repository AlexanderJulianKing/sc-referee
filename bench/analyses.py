"""From one simulated dataset, emit the TWO analyses whose correct verdicts we know.

  (a) per-cell Wilcoxon   — cells as replicates. Squair 2021: inflates false positives.
  (b) pseudobulk DESeq2   — donors as replicates. Recovers the planted truth.

sc-referee must BLOCK (a) when powered, and never false-accuse (b).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, ttest_ind
from statsmodels.stats.multitest import multipletests

from sc_referee.bundle import Bundle, Measure
from sc_referee.design import Design


def bundle_from(adata) -> Bundle:
    return Bundle(
        observations=adata.obs.copy(),
        measure=Measure("counts", np.asarray(adata.X), None, list(adata.var_names)),
        feature_metadata=pd.DataFrame(index=list(adata.var_names)),
        replicate_var="donor_id",
    )


def bench_design() -> Design:
    """Donors are nested within condition (unpaired), so each donor is one pseudobulk sample."""
    return Design(
        analysis_type="condition_contrast_DE",
        confirmed_by_human=True,
        confidence={"replicate_unit": "high", "condition": "high"},
        condition="condition",
        batch=[],
        replicate_unit=["donor_id"],
        reference="ctrl",
        test="stim",
        model="~ condition",
        target_coefficient="condition[T.stim]",
        sample_unit=["donor_id"],
        pairing_unit=[],
    )


def per_cell_wilcoxon(adata) -> pd.DataFrame:
    """The pseudoreplicated analysis: scanpy-style normalize -> log1p -> per-cell Wilcoxon."""
    X = np.asarray(adata.X, dtype=float)
    lib = X.sum(axis=1, keepdims=True)
    lib[lib == 0] = 1.0
    lcpm = np.log1p(X / lib * 1e4)

    is_stim = (adata.obs["condition"] == "stim").to_numpy()
    stim, ctrl = lcpm[is_stim], lcpm[~is_stim]

    res = mannwhitneyu(stim, ctrl, axis=0, alternative="two-sided", method="asymptotic")
    p = np.nan_to_num(res.pvalue, nan=1.0)
    padj = multipletests(p, method="fdr_bh")[1]
    effect = (stim.mean(axis=0) - ctrl.mean(axis=0)) / np.log(2)  # log2-ish, direction is what matters

    return pd.DataFrame({"feature_id": list(adata.var_names), "pvalue": p,
                         "padj": padj, "effect": effect})


def reported_from_recompute(res) -> pd.DataFrame:
    """DO NOT USE AS THE 'CORRECT ANALYSIS' ARM OF A SPECIFICITY MEASUREMENT.

    This copies the recompute back out. Feeding it to `build_panel` asks how many
    recompute-significant genes are recompute-significant: the answer is ALL of them, by identity,
    for every seed. `survival_rate == 1.0` is then structural and `specificity == 1.0` is a
    tautology, not a measurement. (Opus review 2026-07-08.)

    Retained only for tests that legitimately want the identity case.
    """
    t = res.table
    return pd.DataFrame({"feature_id": list(t.index), "pvalue": t["pvalue"].to_numpy(),
                         "padj": t["padj"].to_numpy(), "effect": t["effect"].to_numpy()})


def reported_pseudobulk_ttest(pb: pd.DataFrame, meta: pd.DataFrame, design) -> pd.DataFrame:
    """The CORRECT-UNIT arm: a genuinely INDEPENDENT, replicate-aware estimator.

    Donor-level pseudobulk (the right unit) tested with a Welch t-test on log2(CPM+1) and BH.
    Its hit list is NOT the NB recompute's hit list — the two disagree on marginal genes — so
    `survival_rate` can fall below 1.0 and specificity becomes something the benchmark can
    actually fail. `experimental_unit`'s job is to police the UNIT, and this analysis got the unit
    right; accusing it would be the false accusation we claim never to make.

    (`count_model` would separately, and correctly, flag the estimator. That is a different check.)
    """
    contrast_col, ref, test = design.contrast_column_and_levels()
    counts = pb.values.astype(float)
    lib = counts.sum(axis=1, keepdims=True)
    lib[lib == 0] = np.nan
    lcpm = np.log2(counts / lib * 1e6 + 1.0)

    arm = meta[contrast_col].to_numpy()
    a, b = lcpm[arm == test], lcpm[arm == ref]
    _, p = ttest_ind(a, b, axis=0, equal_var=False)
    p = np.nan_to_num(p, nan=1.0)
    return pd.DataFrame({"feature_id": list(pb.columns), "pvalue": p,
                         "padj": multipletests(p, method="fdr_bh")[1],
                         "effect": a.mean(axis=0) - b.mean(axis=0)})


def hits(padj, testable=None, alpha: float = 0.05) -> np.ndarray:
    ok = np.asarray(padj, dtype=float) <= alpha
    if testable is not None:
        ok &= np.asarray(testable, dtype=bool)
    return ok


def prf(called: np.ndarray, truth: np.ndarray) -> dict:
    tp = int((called & truth).sum())
    fp = int((called & ~truth).sum())
    fn = int((~called & truth).sum())
    precision = tp / (tp + fp) if (tp + fp) else float("nan")
    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    return dict(n_called=int(called.sum()), tp=tp, fp=fp, precision=precision, recall=recall)
