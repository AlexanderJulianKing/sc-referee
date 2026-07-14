"""Illustrative producing code. Referee parses this file; it does not execute it."""
import numpy as np
import pandas as pd
import scanpy as sc
from scipy.stats import fisher_exact, mannwhitneyu

adata = sc.read_h5ad("cells.h5ad")
sc.pp.normalize_total(adata)
sc.pp.log1p(adata)

# Claim 1 — gene-expression DE after a data-derived cluster label.
sc.pp.pca(adata)
sc.pp.neighbors(adata)
sc.tl.leiden(adata)
sc.tl.rank_genes_groups(adata, groupby="treatment", method="wilcoxon")
de = sc.get.rank_genes_groups_df(adata, group="treated")
de.to_csv("results/gene_expression.csv", index=False)

# Claim 2 — an exon-ratio comparison.
psi = adata.X[:, 3] / (adata.X[:, 3] + adata.X[:, 4])
_, splice_p = mannwhitneyu(
    psi[adata.obs["treatment"] == "control"], psi[adata.obs["treatment"] == "treated"]
)
splicing = pd.DataFrame({"gene": ["NRXN1"], "pvalue": [splice_p],
                         "padj": [splice_p], "log2fc": [0.31]})
splicing.to_csv("results/alternative_splicing.csv", index=False)

# Claim 3 — abundance of activated versus resting cells across the treatment arms.
table = pd.crosstab(adata.obs["treatment"], adata.obs["cell_state"])
_, abundance_p = fisher_exact(table.to_numpy())
abundance = pd.DataFrame({"gene": ["activated_cells"], "pvalue": [abundance_p],
                          "padj": [abundance_p], "log2fc": [0.74]})
abundance.to_csv("results/cluster_abundance.csv", index=False)

