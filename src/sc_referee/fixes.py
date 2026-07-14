"""Corrected-reanalysis templates — the actionable other half of a verdict.

A linter that only flags is half a tool. `fix_for(finding, design)` returns a correction for a
flagged (`blocker`/`major`) finding, generated deterministically from the confirmed design — NEVER
from an LLM. For pseudoreplication it is a RUNNABLE pseudobulk reanalysis script; for the others, the
exact edit or code to apply. `None` when there is nothing to fix (a pass/abstain/informational
finding, or a check with no template).
"""
from __future__ import annotations

from sc_referee import statuses as S
from sc_referee.design import Design

# Only these two statuses warrant a fix — the rest are clean, abstaining, or advisory-only.
_FIXABLE = (S.BLOCKER, S.MAJOR)


def _experimental_unit_fix(finding, design: Design) -> str:
    rep = (list(design.replicate_unit) or ["donor_id"])[0]
    cond = design.condition or "condition"
    ref, test = design.reference, design.test
    # Build the model from the replicate/condition so it ALWAYS matches the `meta` columns the
    # template constructs — do NOT reuse design.model verbatim (it may name covariates the template
    # doesn't build, which would crash the generated script). Paired designs adjust for the donor.
    model = f"~ {rep} + {cond}" if design.pairing_unit else f"~ {cond}"
    return f'''#!/usr/bin/env python
"""Corrected reanalysis: pseudobulk to the biological replicate ({rep}), then a count model.

sc-referee flagged the reported per-cell analysis as PSEUDOREPLICATION — cells within a {rep} are
not independent, so testing cells as replicates inflates significance. Aggregate raw counts to one
sample per ({rep} x {cond}) and test at that level. Generated from your confirmed design."""
import scanpy as sc
import pandas as pd
from pydeseq2.dds import DeseqDataSet
from pydeseq2.ds import DeseqStats

adata = sc.read_h5ad("<your_counts.h5ad>")            # RAW integer counts (not log/normalized)

# --- pseudobulk: SUM raw counts within each ({rep} x {cond}) sample ---------------------------
counts = adata.to_df()                                 # cells x genes
sample = adata.obs["{rep}"].astype(str) + "__" + adata.obs["{cond}"].astype(str)
pb = counts.groupby(sample).sum().astype(int)          # samples x genes
meta = pd.DataFrame(index=pb.index)
meta["{rep}"] = [s.split("__")[0] for s in pb.index]
meta["{cond}"] = [s.split("__")[1] for s in pb.index]

# --- replicate-level differential expression (negative binomial) ------------------------------
dds = DeseqDataSet(counts=pb, metadata=meta, design="{model}")
dds.deseq2()
stats = DeseqStats(dds, contrast=["{cond}", "{test}", "{ref}"])
stats.summary()
res = stats.results_df                                 # log2FoldChange + padj at the {rep} level
res.to_csv("corrected_pseudobulk_de.csv")
print((res["padj"] <= 0.05).sum(), "genes significant at the {rep} level "
      "(compare with the inflated per-cell list).")
'''


def _confounding_fix(finding, design: Design) -> str:
    m = finding.metrics or {}
    cond = design.condition or "condition"
    r2 = m.get("r2")
    if r2 is not None and r2 >= 1.0 - 1e-8:
        return (f"'{cond}' is perfectly aliased with the batch (R²=1) — NO model can separate them. "
                f"This is a DESIGN problem, not a code fix: re-run the experiment with the batch "
                f"crossed with '{cond}' (each batch containing both arms), or collect samples so the "
                f"two are not confounded.")
    omitted = list(m.get("omitted") or [])
    if omitted:
        pr2 = m.get("omitted_partial_r2")
        share = f" (it explains ~{pr2:.0%} of {cond}'s residual variance)" if pr2 is not None else ""
        return (f"Add the omitted batch term(s) to your model{share}:\n"
                f'    design = "~ {" + ".join(omitted)} + {cond}"\n'
                f"then re-fit. This adjusts the estimate for the confound; the SE cost is ~×√VIF.")
    return (f"'{cond}' is estimable but near-collinear with the nuisance structure — no correction "
            f"needed, just be aware the standard errors are inflated.")


def _multiple_testing_fix(finding, design: Design) -> str:
    return ("Apply Benjamini–Hochberg over your FULL tested family (every gene tested, not just the "
            "significant ones):\n"
            "    from statsmodels.stats.multitest import multipletests\n"
            "    padj = multipletests(pvalues, method='fdr_bh')[1]\n"
            "    significant = genes[padj <= 0.05]")


def _count_model_fix(finding, design: Design) -> str:
    return ("Replace the t-test / OLS on log-CPM with a COUNT model on raw counts (DESeq2 or edgeR on "
            "the pseudobulk matrix). Counts are not Gaussian; a t-test on log-CPM discards the "
            "count-based mean–variance relationship and mis-calibrates the p-values.")


def _effect_size_fix(finding, design: Design) -> str:
    return ("Add an effect-size threshold — statistical significance alone is not discovery when you "
            "have thousands of cells:\n"
            "    significant = genes[(padj <= 0.05) & (abs(log2FC) >= 1.0)]\n"
            "or test against a fold-change threshold directly (edgeR glmTreat / limma treat).")


def _double_dipping_fix(finding, design: Design) -> str:
    return ("The reported p-values are not valid for post-clustering inference (the clusters and the "
            "marker test used the same cells). Use a selection-aware method:\n"
            "  • count-splitting / data thinning: thin counts, cluster on X_train, test markers on X_test;\n"
            "  • or a held-out dataset for cluster definition;\n"
            "  • or ClusterDE (a synthetic-null calibration).\n"
            "Do not attach calibrated p-values to markers of clusters derived from the same expression data.")


_FIXES = {
    "experimental_unit": _experimental_unit_fix,
    "confounding": _confounding_fix,
    "multiple_testing": _multiple_testing_fix,
    "count_model": _count_model_fix,
    "effect_size_threshold": _effect_size_fix,
    "double_dipping": _double_dipping_fix,
}


def fix_for(finding, design: Design):
    """A correction for a flagged finding, or None when there is nothing to act on."""
    if finding.status not in _FIXABLE:
        return None
    maker = _FIXES.get(finding.check_id)
    return maker(finding, design) if maker else None
