"""The deliberately-AMBIGUOUS input — where a regex must fail and Claude must reason.

`.obs` carries `donor_id` (clearly the replicate) and `processing_run` (clearly the batch),
but the biological condition is a column called **`group`**. "group" is not a condition token
— and it genuinely could mean condition, cluster, or batch. A name-matching classifier cannot
resolve it. Claude can, by reading the *combination* of signals: `group` has exactly 2 levels
across 6 donors, it is crossed with the run, and the shipped code calls
`rank_genes_groups(adata, 'group')` — i.e. the analyst tested it as the contrast, per cell.

Run directly to regenerate:  python fixtures/ambiguous_group/make_fixture.py
"""
from __future__ import annotations

from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd

N_GENES = 8
CELLS_PER_DONOR = 4
SEED = 0

ANALYSIS_PY = '''"""Per-cell differential expression between the two groups."""
import scanpy as sc

adata = sc.read_h5ad("cells.h5ad")
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)
sc.tl.rank_genes_groups(adata, "group", method="wilcoxon")
'''


def build(outdir) -> Path:
    outdir = Path(outdir)
    (outdir / "results").mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)

    donors = [f"D{i}" for i in range(1, 7)]
    group = ["A", "A", "A", "B", "B", "B"]              # 3 donors per group (unpaired)
    run = ["R1", "R2", "R1", "R2", "R1", "R2"]          # crossed with group -> estimable

    rows, cell_ids, k = [], [], 0
    for donor, g, r in zip(donors, group, run):
        for _ in range(CELLS_PER_DONOR):
            rows.append((donor, g, r))
            cell_ids.append(f"cell{k}")
            k += 1
    obs = pd.DataFrame(rows, columns=["donor_id", "group", "processing_run"], index=cell_ids)

    X = rng.integers(0, 60, size=(len(obs), N_GENES)).astype("int32")
    adata = ad.AnnData(X=X, obs=obs, var=pd.DataFrame(index=[f"GENE{i}" for i in range(N_GENES)]))
    adata.write_h5ad(outdir / "cells.h5ad")

    # a per-cell Wilcoxon result table, with lab-ish column names (synonym binding must cope)
    pd.DataFrame({
        "gene": [f"GENE{i}" for i in range(N_GENES)],
        "pvalue": [1e-5] * 3 + [0.4] * (N_GENES - 3),
        "adj_p_value": [1e-4] * 3 + [0.6] * (N_GENES - 3),
        "logfoldchange": [2.1, -1.8, 1.6] + [0.05] * (N_GENES - 3),
    }).to_csv(outdir / "results" / "per_cell_wilcoxon.csv", index=False)

    (outdir / "analysis.py").write_text(ANALYSIS_PY)
    return outdir


if __name__ == "__main__":
    print(f"wrote ambiguous_group fixture to {build(Path(__file__).parent)}")
