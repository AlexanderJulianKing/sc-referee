"""The intentionally naive reported analysis. Referee parses this file; it does not execute it."""
import scanpy as sc

adata = sc.read_h5ad("kang.h5ad")
sc.pp.normalize_total(adata)
sc.pp.log1p(adata)
sc.tl.rank_genes_groups(adata, groupby="label", groups=["stim"], reference="ctrl",
                       method="wilcoxon")
reported = sc.get.rank_genes_groups_df(adata, group="stim")
reported.to_csv("results/per_cell_wilcoxon.csv", index=False)

