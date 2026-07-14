"""Reported-column binding must recognize the ADJUSTED-p column of the dominant DE tools.

Surfaced by dogfooding the CLI on real Kang/Seurat output: `p_val_adj` (Seurat FindMarkers) was not
a padj synonym, so ingest set padj = all-NA and silently discarded the analyst's corrected
significance — multiple_testing would then think no correction was applied, and effect_size would
read raw p-values. This pins the adjusted-p column for Seurat, limma, scanpy, edgeR, and DESeq2.
"""
from sc_referee import synonyms


def test_seurat_findmarkers_binds_the_adjusted_p_not_the_raw():
    b = synonyms.bind_columns(["gene", "p_val", "p_val_adj", "avg_log2FC"])
    assert b["pval"] == "p_val"
    assert b["padj"] == "p_val_adj"          # the ADJUSTED p — not the raw p_val
    assert b["effect"] == "avg_log2FC"


def test_limma_toptable_binds_adj_p_val():
    b = synonyms.bind_columns(["Gene", "P.Value", "adj.P.Val", "logFC"])
    assert b["pval"] == "P.Value"
    assert b["padj"] == "adj.P.Val"


def test_scanpy_edger_deseq2_still_bind():
    assert synonyms.bind_columns(["names", "pvals", "pvals_adj", "logfoldchanges"])["padj"] == "pvals_adj"
    assert synonyms.bind_columns(["gene", "PValue", "FDR", "logFC"])["padj"] == "FDR"        # edgeR
    assert synonyms.bind_columns(["gene", "pvalue", "padj", "log2FoldChange"])["padj"] == "padj"  # DESeq2


def test_a_column_named_replicate_is_detected_as_the_replicate_var():
    """Dogfooding surfaced this: a column literally named `replicate` (the scverse Kang schema) was
    not a replicate token, so bundle.replicate_var came back None and experimental_unit could not run."""
    from sc_referee.adapters._common import detect_replicate_var

    assert detect_replicate_var(["replicate", "label", "cell_type"]) == "replicate"
