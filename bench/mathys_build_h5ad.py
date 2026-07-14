"""Assemble the R-exported Mathys files (counts.mtx.gz + obs.csv + var.csv) into an
AnnData h5ad that sc-referee ingests exactly like data/kang.h5ad.

The R side (bench/mathys_convert.R) writes counts as genes x cells (MatrixMarket
convention); AnnData wants cells x genes, so we transpose here.

    python bench/mathys_build_h5ad.py data/mathys_export data/mathys.h5ad

Prints the obs columns, the per-column value counts for the likely donor / diagnosis /
cell-type fields, so the anchor's column mapping can be confirmed against real values.
"""
from __future__ import annotations

import sys
from pathlib import Path

import anndata as ad
import pandas as pd
import scipy.io as sio
import scipy.sparse as sp


def build(export_dir: str, out_path: str) -> ad.AnnData:
    export = Path(export_dir)
    counts = sio.mmread(export / "counts.mtx.gz")      # genes x cells
    X = sp.csr_matrix(counts).T.tocsr()                # -> cells x genes
    obs = pd.read_csv(export / "obs.csv")
    var = pd.read_csv(export / "var.csv")
    obs.index = obs["cell_id"].astype(str) if "cell_id" in obs else obs.index.astype(str)
    var.index = var["gene_id"].astype(str) if "gene_id" in var else var.index.astype(str)

    a = ad.AnnData(X=X, obs=obs, var=var)
    if a.n_obs != obs.shape[0] or a.n_vars != var.shape[0]:
        raise ValueError(f"shape mismatch: X{a.shape} obs{obs.shape[0]} var{var.shape[0]}")
    a.write_h5ad(out_path)

    print(f"wrote {out_path}: {a.n_obs} cells x {a.n_vars} genes")
    print("\nobs columns:", list(a.obs.columns))
    # surface the candidate schema fields with real values so mapping is verifiable
    for kind, cands in {
        "donor": ("individual", "individualID", "donor_id", "donor", "manifest", "subject", "patient"),
        "diagnosis": ("diagnosis", "pathology", "pathologic_dx", "cogdx", "braaksc", "condition", "disease"),
        "cell_type": ("cluster_celltype", "cell_type", "celltype", "broad_celltype", "major_celltype"),
    }.items():
        hit = next((c for c in cands if c in a.obs.columns), None)
        if hit:
            n = a.obs[hit].nunique()
            head = list(pd.Series(a.obs[hit].unique()).head(8))
            print(f"  {kind:9s} -> '{hit}' ({n} unique): {head}")
        else:
            print(f"  {kind:9s} -> NOT FOUND among {cands}")
    return a


if __name__ == "__main__":
    export_dir = sys.argv[1] if len(sys.argv) > 1 else "data/mathys_export"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "data/mathys.h5ad"
    build(export_dir, out_path)
