"""The pydeseq2 recompute engine — pseudobulk NB Wald, the engine that CAN block.

Imported lazily (only when `--engine pydeseq2`) so the `simple` path and CI fixtures never
require pydeseq2. Returns per-feature log2FC + lfcSE, so the earned-verdict's `powered`
gate uses the Wald MDE (z-based) rather than the paired-t MDE.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from sc_referee.engine import RecomputeResult


def pydeseq2_recompute(pb: pd.DataFrame, meta: pd.DataFrame, design) -> RecomputeResult:
    from pydeseq2.dds import DeseqDataSet
    from pydeseq2.ds import DeseqStats

    contrast_col, ref, test = design.contrast_column_and_levels()

    sample_ids = [f"s{i}" for i in range(len(pb))]
    counts_df = pd.DataFrame(np.asarray(pb.values, dtype=int), index=sample_ids, columns=list(pb.columns))
    metadata = meta.copy()
    metadata.index = sample_ids
    # DESeq2 factors must be plain strings (AnnData .obs may hand us categoricals)
    for col in metadata.columns:
        metadata[col] = metadata[col].astype(str)

    keep = metadata[contrast_col].isin([str(ref), str(test)]).to_numpy()
    counts_df, metadata = counts_df[keep], metadata[keep]

    nonzero = counts_df.sum(axis=0) > 0
    counts_use = counts_df.loc[:, nonzero]

    import warnings

    design_formula = design.model or f"~ {contrast_col}"
    # pydeseq2 emits benign chatter (e.g. "dispersion trend curve fitting did not converge") that
    # would otherwise leak into the user-facing audit report. Suppress its warnings — not errors —
    # around the fit only. (Surfaced by dogfooding the CLI, 2026-07-08.)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dds = DeseqDataSet(counts=counts_use, metadata=metadata, design=design_formula, quiet=True)
        dds.deseq2()
        stats = DeseqStats(dds, contrast=[contrast_col, str(test), str(ref)], quiet=True)
        stats.summary()
    rdf = stats.results_df  # index=gene; cols baseMean, log2FoldChange, lfcSE, stat, pvalue, padj

    n_per_arm = int(metadata[contrast_col].value_counts().reindex([str(ref), str(test)]).min())

    idx = list(pb.columns)
    table = pd.DataFrame(index=idx)
    table["pvalue"] = rdf["pvalue"].reindex(idx).fillna(1.0)
    table["padj"] = rdf["padj"].reindex(idx).fillna(1.0)
    table["effect"] = rdf["log2FoldChange"].reindex(idx)
    table["se"] = rdf["lfcSE"].reindex(idx)
    table["s_diff"] = np.nan
    table["n_used"] = n_per_arm
    table["testable"] = table["se"].notna() & (table["se"] > 0) & rdf["padj"].reindex(idx).notna()
    return RecomputeResult(table=table, mde_kind="wald", n_replicates_per_arm=n_per_arm)
