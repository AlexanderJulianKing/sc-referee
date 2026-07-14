"""Multi-sample NB simulator mirroring muscat's `simData` design (Crowell 2020, Nat Commun).

Ground truth is the field's, not ours: a planted set of TRUE sample-level DE genes, real
donor-to-donor variance, and the known-correct verdict from Squair 2021 (per-cell DE inflates
false positives; pseudobulk recovers the planted truth).

DESIGN NOTE — donors are UNPAIRED (distinct donors per condition), as in muscat's simData
where samples are nested within groups. This is load-bearing: if the same donor contributed
both arms with a shared `donor_fac`, the donor effect would CANCEL between arms, the pooled
per-cell distributions for a null gene would be identical, and the per-cell Wilcoxon would be
correctly calibrated — there would be no pseudoreplication to catch. Nesting donors within
groups is what makes between-donor variance leak into the arm contrast, which is exactly the
error a per-cell test ignores and a pseudobulk test accounts for.

    means_g    ~ LogNormal(log 50, 1.0)          per-gene baseline mean
    disp_g     = 0.1 + 10/means_g                NB dispersion (inverse-mean trend)
    donor_fac  ~ LogNormal(0, donor_dispersion)  per-donor × per-gene multiplicative effect
    DE set     = frac_DE of genes; stim mean *= 2**(±effect_size)
    counts     ~ NB(mean = means·donor_fac·cond_effect, disp = disp_g)

No download, no GPU, deterministic seed.
"""
from __future__ import annotations

import anndata as ad
import numpy as np
import pandas as pd

DEFAULTS = dict(n_donors=8, n_genes=2000, frac_DE=0.10, effect_size=1.0,
                donor_dispersion=0.30, cells_per_donor=200)


def _nb_counts(rng, mu, disp, n_cells):
    """NB with mean mu and dispersion disp (var = mu + disp·mu²) -> (n_cells, n_genes) ints."""
    r = 1.0 / disp                      # number of failures
    p = r / (r + mu)                    # success prob per gene
    return rng.negative_binomial(n=r, p=p, size=(n_cells, mu.shape[0]))


def simulate(n_donors: int = 8, n_genes: int = 2000, frac_DE: float = 0.10,
             effect_size: float = 1.0, donor_dispersion: float = 0.30,
             cells_per_donor: int = 200, seed: int = 0) -> ad.AnnData:
    """`n_donors` is donors PER ARM (biological replicates per condition)."""
    rng = np.random.default_rng(seed)

    means = rng.lognormal(np.log(50), 1.0, n_genes)
    disp = 0.1 + 10.0 / means

    n_de = int(round(frac_DE * n_genes))
    de_idx = rng.choice(n_genes, size=n_de, replace=False)
    lfc = np.zeros(n_genes)
    lfc[de_idx] = rng.choice([-1.0, 1.0], size=n_de) * effect_size
    cond_effect = 2.0 ** lfc                       # applied only in `stim`

    blocks, donor_ids, conditions = [], [], []
    for arm, cond in enumerate(("ctrl", "stim")):
        for d in range(n_donors):
            donor = f"D{arm * n_donors + d + 1}"
            donor_fac = rng.lognormal(0.0, donor_dispersion, n_genes)
            mu = means * donor_fac * (cond_effect if cond == "stim" else 1.0)
            blocks.append(_nb_counts(rng, mu, disp, cells_per_donor))
            donor_ids += [donor] * cells_per_donor
            conditions += [cond] * cells_per_donor

    X = np.vstack(blocks).astype(np.int32)
    obs = pd.DataFrame({"donor_id": donor_ids, "condition": conditions},
                       index=[f"c{i}" for i in range(X.shape[0])])
    var = pd.DataFrame(index=[f"G{i}" for i in range(n_genes)])

    adata = ad.AnnData(X=X, obs=obs, var=var)
    adata.uns["true_DE"] = np.zeros(n_genes, dtype=bool)
    adata.uns["true_DE"][de_idx] = True
    adata.uns["true_lfc"] = lfc
    adata.uns["params"] = dict(n_donors=n_donors, n_genes=n_genes, frac_DE=frac_DE,
                               effect_size=effect_size, donor_dispersion=donor_dispersion,
                               cells_per_donor=cells_per_donor, seed=seed)
    return adata
