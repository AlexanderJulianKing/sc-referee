"""Does the apparatus work? Inject one error at a time; see whether sc-referee separates it.

For each error class we report:
  DETECTED     — sc-referee returned something other than `pass` on the defective analysis
  DIAGNOSED    — and the finding actually names the right defect
  SPECIFICITY  — the clean analysis was NOT accused

A `MISS` is not a failure of the experiment; it is the roadmap.

    PYTHONPATH=src:. python bench/run_discrimination.py
"""
from __future__ import annotations

import warnings
from dataclasses import replace

from bench.analyses import bench_design, bundle_from
from bench.error_classes import (
    add_batch,
    batched_design,
    reported_clean,
    reported_count_model,
    reported_negligible_effects,
    reported_no_fdr,
    reported_pseudoreplication,
)
from bench.muscat_sim import simulate
from sc_referee import statuses as S
from sc_referee.checks.confounding import evaluate_confounding
from sc_referee.checks.experimental_unit import evaluate_experimental_unit
from sc_referee.engine import aggregate_to_pseudobulk
from sc_referee.engines.pydeseq2_engine import pydeseq2_recompute

ACCUSED = (S.BLOCKER, S.MAJOR)


def worst(findings):
    return max((f.status for f in findings), key=lambda s: S.SEVERITY.get(s, 0)) if findings else S.PASS


def audit(design, bundle, reported, res):
    """Run the REAL registry, with applies_to gating. experimental_unit gets the recompute
    injected (it depends only on bundle+design, never on the reported table)."""
    from sc_referee.registry import CHECKS

    out = {}
    for check in CHECKS:
        if not check.applies_to(design, bundle):
            continue
        if check.id == "experimental_unit":
            out[check.id] = evaluate_experimental_unit(design, bundle, reported, "pydeseq2", recompute=res)
        elif check.id == "confounding":
            out[check.id] = evaluate_confounding(bundle.observations, design)
        else:
            out[check.id] = check.run(design, bundle, reported)
    return out


def _code(*de_calls):
    return {"imports": ["scipy"], "de_calls": list(de_calls), "cluster_calls": [], "da_calls": []}


def _normalized_matrix_case(adata):
    """DEFECT: the analyst handed us log-normalized values, not raw counts. gpt-5.4 did this.
    Caught at INGEST by the adapter, before any check runs."""
    import tempfile
    from pathlib import Path

    import anndata as ad
    import numpy as np

    from sc_referee.adapters.anndata_adapter import read_anndata

    from sc_referee.checks.experimental_unit import ExperimentalUnitCheck
    from tests.factories import make_design

    norm = ad.AnnData(X=np.log1p(np.asarray(adata.X, dtype=float)), obs=adata.obs.copy(), var=adata.var.copy())
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "normalized.h5ad"
        norm.write_h5ad(p)
        b = read_anndata(p)                                    # no longer refuses the whole run
        reason = ExperimentalUnitCheck().cannot_evaluate(make_design(unit_of_test="cell"), b)
    if b.measure.kind == "normalized" and reason and "raw" in reason.lower():
        return ("normalized matrix (not raw counts)", S.NOT_AUDITED,
                "DETECTED ✓  (recompute abstains; confounding/mult-testing still run)")
    return ("normalized matrix (not raw counts)", S.PASS, "MISS  (adapter accepted it as counts)")


def _double_dipping_case(design):
    """DEFECT: cluster the cells de novo, then test DE between those clusters on the SAME cells and
    report marker p-values. The structural detector (Phase 3) earns a blocker — the claim is about
    CALIBRATION ('p-values not valid for post-clustering inference'), not truth."""
    from dataclasses import replace
    from types import SimpleNamespace

    import pandas as pd

    from sc_referee.checks.double_dipping import DoubleDippingCheck

    marker = replace(design, analysis_type="marker_detection", unit_of_test="cell")
    bundle = SimpleNamespace(code_signals={
        "de_calls": ["rank_genes_groups"], "cluster_calls": ["leiden"],
        "da_calls": [], "safeguards": [], "imports": ["scanpy"]})
    reported = pd.DataFrame({"feature_id": ["g0", "g1", "g2"],
                             "pvalue": [1e-6, 1e-5, 1e-4], "padj": [1e-4, 1e-3, 1e-2]})

    chk = DoubleDippingCheck()
    if not chk.applies_to(marker, bundle):
        return ("double dipping (cluster then test)", S.NOT_AUDITED, "MISS  (did not apply)")
    f = chk.run(marker, bundle, reported)
    diagnosed = f.status == S.BLOCKER and "post-clustering" in f.verdict.lower()
    return ("double dipping (cluster then test)", f.status,
            "DETECTED + DIAGNOSED ✓" if diagnosed else f"DETECTED ({f.status})")


def main(n_donors=8, n_genes=1200, seed=0):
    warnings.filterwarnings("ignore")

    adata = simulate(n_donors=n_donors, n_genes=n_genes, frac_DE=0.05, seed=seed)
    adata = add_batch(adata, aliased=False)                     # crossed batch: not confounded
    bundle, design = bundle_from(adata), batched_design(bench_design())
    pb, meta = aggregate_to_pseudobulk(bundle, design)
    res = pydeseq2_recompute(pb, meta, design)

    def variant(*de_calls):
        """A bundle + design describing what the analyst actually did.

        `unit_of_test` is DERIVED from the parsed code, exactly as `init` would route it — never
        injected. Hand-setting it here previously made `count_model` look reachable when the real
        routing sent a pseudobulk t-test to `experimental_unit`. (Opus review 2026-07-08.)
        """
        from sc_referee.code_signals import unit_of_test_from

        b = bundle_from(adata)
        b.code_signals = _code(*de_calls)
        return b, replace(design, unit_of_test=unit_of_test_from(b.code_signals))

    NB = ("pydeseq2",)
    PB_TTEST = ("pseudobulk", "ttest_ind")     # aggregated to donors, then a t-test on log-CPM
    cases = [
        ("— none (clean analysis) —",       reported_clean(res),                     *variant(*NB), None),
        ("pseudoreplication",               reported_pseudoreplication(adata),       *variant("rank_genes_groups"), "experimental_unit"),
        ("count model (t-test on log2CPM)", reported_count_model(pb, meta, design),  *variant(*PB_TTEST), "count_model"),
        ("no multiple-testing correction",  reported_no_fdr(res),                    *variant(*NB), "multiple_testing"),
        ("no effect-size threshold",        reported_negligible_effects(),           *variant(*NB), "effect_size_threshold"),
    ]

    # design-level defect: batch perfectly aliased with condition
    cadata = add_batch(simulate(n_donors=n_donors, n_genes=n_genes, frac_DE=0.05, seed=seed), aliased=True)
    from sc_referee.code_signals import unit_of_test_from
    cbundle = bundle_from(cadata)
    cbundle.code_signals = _code(*NB)
    cpb, cmeta = aggregate_to_pseudobulk(cbundle, design)
    cases.append(("confounding (batch ⟂ condition)", reported_clean(res), cbundle,
                  replace(design, unit_of_test=unit_of_test_from(cbundle.code_signals)), "confounding"))

    extra = [_normalized_matrix_case(adata), _double_dipping_case(design)]

    print(f"{'injected error':34} {'verdict':>13}  {'fired':30} outcome")
    print("-" * 108)
    rows = []
    for label, reported, bnd, dsn, expect in cases:
        r = pydeseq2_recompute(cpb, cmeta, dsn) if expect == "confounding" else res
        bnd.reported_results = reported          # ingest() does this in a real audit
        found = audit(dsn, bnd, reported, r)
        v = worst(list(found.values()))
        fired = ", ".join(f"{k}={f.status}" for k, f in found.items() if f.status != S.PASS) or "—"

        if expect is None:
            outcome = "SPECIFICITY ✓" if v not in ACCUSED else "FALSE ACCUSATION ✗"
        elif v == S.PASS:
            outcome = "MISS  (no check for this)"
        elif v == S.NOT_AUDITED:
            outcome = "MISS  (honest: not_audited)"
        elif expect in found and found[expect].status in ACCUSED:
            outcome = "DETECTED + DIAGNOSED ✓"
        elif v in ACCUSED:
            outcome = "DETECTED, MISDIAGNOSED ⚠"
        else:
            outcome = f"flagged {v} (advisory)"
        print(f"{label:34} {v:>13}  {fired:30} {outcome}")
        rows.append((label, v, outcome))

    for label, verdict, outcome in extra:
        print(f"{label:34} {verdict:>13}  {'—':30} {outcome}")
        rows.append((label, verdict, outcome))

    print("\nnotes")
    print("  · MISS is not a bug in the experiment — it is the check we have not built.")
    print("  · MISDIAGNOSED means we flagged it, but the verdict text blames the wrong thing.")
    return rows


if __name__ == "__main__":
    main()
