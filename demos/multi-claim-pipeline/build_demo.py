"""Regenerate the tiny count matrix for the three-claim UI/routing demo."""
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
donors = [f"D{i:02d}" for i in range(1, 9) for _ in range(4)]
treatment = [arm for _ in range(8) for arm in ("control", "control", "treated", "treated")]
cluster = [state for _ in range(8) for state in ("resting", "activated", "resting", "activated")]
base = np.array([
    [28, 8, 4, 16, 5, 9], [24, 9, 5, 14, 6, 8],
    [8, 30, 12, 7, 18, 11], [7, 27, 14, 8, 17, 12],
], dtype=np.int32)
counts = np.vstack([base + (i % 3) for i in range(8)])
adata = ad.AnnData(
    X=counts,
    obs=pd.DataFrame(
        {"donor_id": donors, "treatment": treatment, "cell_state": cluster},
        index=[f"cell_{i:03d}" for i in range(len(donors))],
    ),
    var=pd.DataFrame(index=["IFIT1", "CXCL10", "LST1", "NRXN1", "NRXN1_ALT", "ACTB"]),
)
adata.write_h5ad(ROOT / "cells.h5ad")
print(f"wrote {ROOT / 'cells.h5ad'} ({adata.n_obs} observations × {adata.n_vars} features)")

