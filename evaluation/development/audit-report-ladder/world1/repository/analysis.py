# World-1 milestone fixture: the maintainer's scanpy pseudoreplication script,
# verbatim from the maintainer channel (2026-08-17). Audit target, never executed
# by the auditor. Ground truth: thousands of cells from 2 animals enter ttest_ind
# with no per-animal aggregation.
import scanpy as sc
from scipy.stats import ttest_ind

# Load dataset
adata = sc.read_h5ad("sc_reads.h5ad")

# Group cells by animal ID (2 animals total)
cells_animal1 = adata[adata.obs["animal_id"] == "Animal_1"]
cells_animal2 = adata[adata.obs["animal_id"] == "Animal_2"]

# Pseudoreplication: Testing individual cell counts directly
# Treating thousands of cells as N_obs instead of N_animals = 2
gene = adata.var_names[0]
expr_1 = cells_animal1[:, gene].X.toarray().flatten()
expr_2 = cells_animal2[:, gene].X.toarray().flatten()

stat, inflated_pvalue = ttest_ind(expr_1, expr_2)

print(f"Gene: {gene}")
print(f"Observed Sample Size (Cells): {len(expr_1)} vs {len(expr_2)}")
print(f"Pseudoreplicated p-value: {inflated_pvalue:.3e}")
