"""The flagship real-data anchor: sc-referee on the single most-cited single-cell disease paper.

Mathys et al. 2019 (Nature) — the first snRNA-seq study of Alzheimer's, 48 donors, ~80k nuclei.
The original analysis tested CELLS as replicates (pseudoreplication) and reported ~14,274 DEGs.
The Murphy et al. 2024 (eLife) pseudobulk reanalysis of the SAME reprocessed data found 26 — a
~549x collapse. This anchor lets sc-referee render its OWN earned verdict on that analysis:
emit the pseudoreplicated per-cell claim, recompute at the DONOR level (pydeseq2 NB), and report.

Data (gitignored): the Murphy reprocessed SCE from AD Knowledge Portal syn51758062 (general
research use; requires ADKP registration). Convert once:
    Rscript bench/mathys_convert.R /path/to/sce.qs data/mathys_export
    python bench/mathys_build_h5ad.py data/mathys_export data/mathys.h5ad

Then, per cell type (Mathys analyzed each broad cell type separately):
    PYTHONPATH=src:. python bench/mathys_anchor.py                 # every cell type
    PYTHONPATH=src:. python bench/mathys_anchor.py Ex             # one cell type

Column mapping auto-detects the real schema and prints what it chose; override via env if needed:
    MATHYS_DONOR=individualID MATHYS_CONDITION=pathology MATHYS_CELLTYPE=cell_type \
    MATHYS_REF=control MATHYS_TEST=AD  PYTHONPATH=src:. python bench/mathys_anchor.py
"""
from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path

import numpy as np
import scipy.sparse as sp

from bench.analyses import bundle_from, per_cell_wilcoxon
from sc_referee.checks.experimental_unit import evaluate_experimental_unit
from sc_referee.design import Design, ReportInferenceContract
from sc_referee.engine import aggregate_to_pseudobulk

DATA = Path("data/mathys.h5ad")

_DONOR = ("individualID", "individual", "donor_id", "donor", "manifest", "subject", "patient", "projid")
_COND = ("diagnosis", "pathology", "pathologic_dx", "condition", "disease", "cogdx")
_CTYPE = ("cluster_celltype", "cell_type", "celltype", "broad_celltype", "major_celltype", "cell.type")


def _pick(cols, cands, env):
    if os.environ.get(env):
        return os.environ[env]
    hit = next((c for c in cands if c in cols), None)
    if hit is None:
        raise SystemExit(f"[{env}] none of {cands} in obs columns {list(cols)}; set {env}=<col>")
    return hit


def _guess_ref_test(values):
    ref = os.environ.get("MATHYS_REF") or None
    test = os.environ.get("MATHYS_TEST") or None
    vals = sorted({str(v) for v in values})
    if len(vals) < 2:
        raise SystemExit(f"condition column must contain at least two levels; found {vals}")
    for env, value in (("MATHYS_REF", ref), ("MATHYS_TEST", test)):
        if value is not None and value not in vals:
            raise SystemExit(f"{env}={value!r} is not an observed condition level; choose from {vals}")
    if ref is not None and test is not None:
        if ref == test:
            raise SystemExit("MATHYS_REF and MATHYS_TEST must identify different condition levels")
        return ref, test

    # With more than two levels, choosing the first non-reference value silently changes the disease
    # estimand when row/category order changes. Require the analyst to name both sides explicitly.
    if len(vals) != 2:
        missing = "MATHYS_REF and MATHYS_TEST" if ref is None and test is None else (
            "MATHYS_TEST" if test is None else "MATHYS_REF")
        raise SystemExit(
            f"condition column has {len(vals)} levels {vals}; set {missing} explicitly"
        )
    if ref is not None:
        return ref, next(v for v in vals if v != ref)
    if test is not None:
        return next(v for v in vals if v != test), test

    ref_like = ("control", "ctrl", "normal", "no_", "nci", "healthy", "non", "false", "0")
    references = [v for v in vals if any(k in v.lower() for k in ref_like)]
    if len(references) != 1:
        raise SystemExit(
            f"could not identify one unambiguous reference level from {vals}; "
            "set MATHYS_REF and MATHYS_TEST explicitly"
        )
    ref = references[0]
    test = next(v for v in vals if v != ref)
    return ref, test


def load_mathys(path=DATA, cell_type=None):
    import anndata as ad

    a = ad.read_h5ad(path)
    donor = _pick(a.obs.columns, _DONOR, "MATHYS_DONOR")
    cond = _pick(a.obs.columns, _COND, "MATHYS_CONDITION")
    ctype = _pick(a.obs.columns, _CTYPE, "MATHYS_CELLTYPE")
    if cell_type:
        a = a[a.obs[ctype].astype(str) == cell_type].copy()
    ref, test = _guess_ref_test(a.obs[cond].unique())
    a = a[a.obs[cond].astype(str).isin([str(ref), str(test)])].copy()
    a.obs = a.obs.rename(columns={donor: "donor_id"})
    # the shared per-cell/pseudobulk machinery keys off ctrl/stim labels (see bench/analyses.py);
    # normalize reference->ctrl, test->stim. The ORIGINAL labels are returned for display only.
    a.obs["condition"] = a.obs[cond].astype(str).map({str(ref): "ctrl", str(test): "stim"})
    if sp.issparse(a.X):
        a.X = a.X.toarray()
    a.X = np.asarray(a.X, dtype=float)
    return a, str(ref), str(test)


def mathys_design(paired: bool) -> Design:
    # condition is normalized to ctrl/stim in load_mathys; the design speaks that vocabulary.
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


def run_mathys_anchor(path=DATA, cell_type=None):
    warnings.filterwarnings("ignore")
    from sc_referee.engines.pydeseq2_engine import pydeseq2_recompute

    a, ref, test = load_mathys(path, cell_type)         # ref/test = ORIGINAL labels, for display
    spanning = a.obs.groupby("donor_id", observed=True)["condition"].nunique()
    paired = bool(len(spanning) > 0 and (spanning >= 2).all())

    reported = per_cell_wilcoxon(a)                     # the pseudoreplicated claim (cells as reps)
    bundle = bundle_from(a)
    design = mathys_design(paired)
    pb, meta = aggregate_to_pseudobulk(bundle, design)
    res = pydeseq2_recompute(pb, meta, design)          # the correct donor-level recompute
    finding = evaluate_experimental_unit(design, bundle, reported, "pydeseq2", recompute=res)

    info = dict(cell_type=cell_type or "ALL cell types", ref=ref, test=test,
                n_cells=int(a.n_obs), n_donors=int(a.obs["donor_id"].nunique()), paired=paired,
                per_cell_claimed=int((reported["padj"] <= 0.05).sum()))
    return finding, info


if __name__ == "__main__":
    cell_type = sys.argv[1] if len(sys.argv) > 1 else None
    f, info = run_mathys_anchor(cell_type=cell_type)
    print(f"Mathys 2019 — {info['cell_type']}: {info['n_cells']} cells, {info['n_donors']} donors "
          f"({info['ref']} vs {info['test']}), paired={info['paired']}")
    print(f"  per-cell Wilcoxon claimed significant: {info['per_cell_claimed']} genes")
    m = f.metrics
    print(f"  donor-level recompute: n_per_arm={m.get('n_replicates_per_arm')}  "
          f"powered={m.get('powered')} (pf={m.get('powered_fraction')})  "
          f"survival={m.get('survival_rate')}  survivors={m.get('survivors')}/{m.get('valid_reported_sig')}")
    print(f"\n  sc-referee verdict:  {f.status.upper()}")
    print(f"  {f.verdict}")
