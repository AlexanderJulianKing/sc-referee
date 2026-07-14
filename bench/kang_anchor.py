"""The real-data anchor: does sc-referee's verdict hold off synthetic data? (Item 5)

Kang 2018 (GSE96583): 8 patients, PBMCs ± IFN-β. The canonical pseudoreplication case (Squair 2021).
We emit the pseudoreplicated analysis a weak/careless pipeline produces — a per-cell Wilcoxon of
stim vs ctrl (cells as replicates) — and let sc-referee recompute at the DONOR level (pydeseq2 NB)
and render its earned verdict. The verdict is MEASURED here, not assumed: IFN-β is a strong real
effect, so whether the claims collapse (blocker) or survive (pass) is an empirical question.

Data (raw counts, gitignored) from scverse exampledata:
    curl -sSL -o data/kang.h5ad https://exampledata.scverse.org/pertpy/kang_2018.h5ad

    PYTHONPATH=src:. python bench/kang_anchor.py                 # all cells
    PYTHONPATH=src:. python bench/kang_anchor.py "CD14+ Monocytes"
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import scipy.sparse as sp

from bench.analyses import bundle_from, per_cell_wilcoxon
from sc_referee.checks.experimental_unit import evaluate_experimental_unit
from sc_referee.design import Design, ReportInferenceContract
from sc_referee.engine import aggregate_to_pseudobulk

DATA = Path("data/kang.h5ad")


def load_kang(path=DATA, cell_type=None):
    import anndata as ad

    a = ad.read_h5ad(path)
    if cell_type:
        a = a[a.obs["cell_type"] == cell_type].copy()
    a.obs = a.obs.rename(columns={"replicate": "donor_id", "label": "condition"})
    if sp.issparse(a.X):
        a.X = a.X.toarray()
    a.X = np.asarray(a.X, dtype=float)
    return a


def kang_design(paired: bool) -> Design:
    return Design(
        analysis_type="condition_contrast_DE", confirmed_by_human=True,
        confidence={"replicate_unit": "high", "condition": "high"},
        condition="condition", batch=[], replicate_unit=["donor_id"],
        reference="ctrl", test="stim",
        model="~ donor_id + condition" if paired else "~ condition",
        target_coefficient="condition[T.stim]",
        sample_unit=["donor_id", "condition"],
        pairing_unit=["donor_id"] if paired else [],
        unit_of_test="cell",
        report_inference_contract=ReportInferenceContract(
            producer_binding="exact", response_scale="transformed_continuous",
            method_family="rank_based", dependence_semantics="iid_rows",
        ))


def run_kang_anchor(path=DATA, cell_type=None):
    warnings.filterwarnings("ignore")
    from sc_referee.engines.pydeseq2_engine import pydeseq2_recompute

    a = load_kang(path, cell_type)
    spanning = a.obs.groupby("donor_id", observed=True)["condition"].nunique()
    paired = bool((spanning >= 2).all())

    reported = per_cell_wilcoxon(a)                      # the pseudoreplicated claim (cells as reps)
    bundle = bundle_from(a)
    design = kang_design(paired)
    pb, meta = aggregate_to_pseudobulk(bundle, design)
    res = pydeseq2_recompute(pb, meta, design)          # the correct donor-level recompute
    finding = evaluate_experimental_unit(design, bundle, reported, "pydeseq2", recompute=res)

    info = dict(cell_type=cell_type or "ALL cell types", n_cells=int(a.n_obs),
                n_donors=int(a.obs["donor_id"].nunique()), paired=paired,
                per_cell_claimed=int((reported["padj"] <= 0.05).sum()))
    return finding, info


if __name__ == "__main__":
    cell_type = sys.argv[1] if len(sys.argv) > 1 else None
    f, info = run_kang_anchor(cell_type=cell_type)
    print(f"Kang 2018 — {info['cell_type']}: {info['n_cells']} cells, {info['n_donors']} donors, "
          f"paired={info['paired']}")
    print(f"  per-cell Wilcoxon claimed significant: {info['per_cell_claimed']} genes")
    m = f.metrics
    print(f"  donor-level recompute: n_per_arm={m.get('n_replicates_per_arm')}  "
          f"powered={m.get('powered')} (pf={m.get('powered_fraction')})  "
          f"survival={m.get('survival_rate')}  survivors={m.get('survivors')}/{m.get('valid_reported_sig')}")
    print(f"\n  sc-referee verdict:  {f.status.upper()}")
    print(f"  {f.verdict}")
