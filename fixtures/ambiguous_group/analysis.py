"""Per-cell differential expression between the two groups."""
import scanpy as sc

adata = sc.read_h5ad("cells.h5ad")
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)
sc.tl.rank_genes_groups(adata, "group", method="wilcoxon")
