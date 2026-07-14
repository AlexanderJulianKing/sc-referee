"""Reported-DE column synonyms (C4) — drives folder discovery + column binding.

Matching is case / underscore / dot / whitespace-insensitive. A results file counts as a
reported-DE table iff it has a GENE column plus at least one of PVAL/PADJ.
"""
from __future__ import annotations

import re

GENE = {"gene", "feature", "gene_name", "gene_id", "symbol", "names", "gene_symbol"}
PVAL = {"p", "p_value", "pval", "pvalue", "pvals"}
# The adjusted-p column across the dominant DE tools: DESeq2 `padj`, scanpy `pvals_adj`,
# Seurat `p_val_adj`, limma `adj.P.Val`, edgeR `FDR`, plus common generic spellings.
PADJ = {"padj", "adj_p_value", "fdr", "q_value", "qval", "p_adj", "pvals_adj",
        "p_val_adj", "adj_p_val", "adjusted_p_value", "adjusted_pvalue", "padjust", "fdr_bh"}
EFFECT = {"log2fc", "logfc", "log_fc", "avg_log2fc", "coef", "estimate",
          "logfoldchange", "delta_incl", "d_prop"}


def norm(s: str) -> str:
    return re.sub(r"[._\s]", "", str(s).lower())


_GENE_N = {norm(x) for x in GENE}
_PVAL_N = {norm(x) for x in PVAL}
_PADJ_N = {norm(x) for x in PADJ}
_EFFECT_N = {norm(x) for x in EFFECT}


def _match(columns, canon_norm):
    for c in columns:
        if norm(c) in canon_norm:
            return c
    return None


def bind_columns(columns):
    """Return {gene, pval, padj, effect} -> actual column name (or None)."""
    return {
        "gene": _match(columns, _GENE_N),
        "pval": _match(columns, _PVAL_N),
        "padj": _match(columns, _PADJ_N),
        "effect": _match(columns, _EFFECT_N),
    }


def is_reported_de(columns) -> bool:
    b = bind_columns(columns)
    return b["gene"] is not None and (b["pval"] is not None or b["padj"] is not None)
