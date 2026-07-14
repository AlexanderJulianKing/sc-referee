"""The validation number — scored against ground truth we do not author.

Per simulated dataset we emit two analyses whose correct verdicts are known from Squair 2021:
  (a) per-cell Wilcoxon  — pseudoreplicated. sc-referee must never PASS it.
  (b) pseudobulk DESeq2  — correct.          sc-referee must never ACCUSE it.

Reported metrics (all measured, none asserted):
  never_pass_rate       fraction of pseudoreplicated analyses NOT green-lit   [the safety property]
  blocker_rate          fraction earning the strong verdict (powered collapse)
  abstain_rate          fraction honestly returning needs_evidence (underpowered)
  specificity           1 − false-accusation rate on the CORRECT analysis     [what matters most]
  recompute fidelity    precision/recall of the recomputed hits vs the PLANTED truth

Why this defeats "you built the answer key": the truth is muscat's planted simulation and
Squair's published finding; the recompute is scored against the known-true genes, not against
sc-referee's own opinion.

    python bench/run_benchmark.py --seeds 20 --out bench/metrics.json
"""
from __future__ import annotations

import argparse
import json
import time
import warnings
from pathlib import Path

import numpy as np

from bench.analyses import (
    bench_design,
    bundle_from,
    hits,
    per_cell_wilcoxon,
    prf,
    reported_pseudobulk_ttest,
)
from bench.muscat_sim import simulate
from sc_referee.checks.experimental_unit import evaluate_experimental_unit
from sc_referee.engine import aggregate_to_pseudobulk
from sc_referee.engines.pydeseq2_engine import pydeseq2_recompute

ACCUSING = ("blocker", "major")


def run_one(n_donors, seed, n_genes, frac_DE, donor_dispersion, cells_per_donor) -> dict:
    adata = simulate(n_donors=n_donors, n_genes=n_genes, frac_DE=frac_DE,
                     effect_size=1.0, donor_dispersion=donor_dispersion,
                     cells_per_donor=cells_per_donor, seed=seed)
    truth = adata.uns["true_DE"]
    bundle, design = bundle_from(adata), bench_design()

    reported_percell = per_cell_wilcoxon(adata)
    pb, meta = aggregate_to_pseudobulk(bundle, design)
    res = pydeseq2_recompute(pb, meta, design)          # the recompute, computed ONCE

    # The CORRECT-UNIT arm is an INDEPENDENT replicate-aware estimator (pseudobulk + Welch t on
    # log2CPM + BH), not the recompute echoed back. Otherwise survival_rate == 1.0 by identity and
    # specificity is a tautology. (Opus review 2026-07-08.)
    reported_pseudobulk = reported_pseudobulk_ttest(pb, meta, design)

    bad = evaluate_experimental_unit(design, bundle, reported_percell, "pydeseq2", recompute=res)
    good = evaluate_experimental_unit(design, bundle, reported_pseudobulk, "pydeseq2", recompute=res)

    pc = prf(hits(reported_percell["padj"].to_numpy()), truth)
    pbf = prf(hits(res.table["padj"].to_numpy(), res.table["testable"].to_numpy()), truth)

    m = bad.metrics
    return dict(n_donors=n_donors, seed=seed,
                bad_status=bad.status, good_status=good.status,
                # survival of the CORRECT-UNIT arm. If this is exactly 1.0 for every seed, the
                # arm is the recompute echoed back and `specificity` is a tautology. It is not.
                good_survival=good.metrics.get("survival_rate"),
                survival=m["survival_rate"], powered=bool(m["powered"]),
                powered_fraction=m["powered_fraction"], claimed=m["valid_reported_sig"],
                survivors=m["survivors"],
                percell_precision=pc["precision"], percell_recall=pc["recall"], percell_called=pc["n_called"],
                pseudobulk_precision=pbf["precision"], pseudobulk_recall=pbf["recall"], pseudobulk_called=pbf["n_called"])


def _rate(rows, key, pred):
    return float(np.mean([pred(r[key]) for r in rows])) if rows else float("nan")


def summarize(rows) -> dict:
    return dict(
        n_runs=len(rows),
        # sensitivity: the pseudoreplicated analysis is never green-lit
        never_pass_rate=_rate(rows, "bad_status", lambda s: s != "pass"),
        blocker_rate=_rate(rows, "bad_status", lambda s: s == "blocker"),
        flagged_rate=_rate(rows, "bad_status", lambda s: s in ACCUSING),
        abstain_rate=_rate(rows, "bad_status", lambda s: s == "needs_evidence"),
        # specificity: the correct analysis is never accused
        false_accusation_rate=_rate(rows, "good_status", lambda s: s in ACCUSING),
        specificity=1.0 - _rate(rows, "good_status", lambda s: s in ACCUSING),
        good_pass_rate=_rate(rows, "good_status", lambda s: s == "pass"),
        # the numbers behind the verdict
        mean_survival=float(np.mean([r["survival"] for r in rows])),
        mean_good_survival=float(np.nanmean([r["good_survival"] if r["good_survival"] is not None else np.nan for r in rows])),
        good_survival_is_degenerate=bool(all(r["good_survival"] == 1.0 for r in rows)),
        mean_powered_fraction=float(np.nanmean([r["powered_fraction"] or np.nan for r in rows])),
        # recompute fidelity vs the PLANTED truth
        percell_precision=float(np.nanmean([r["percell_precision"] for r in rows])),
        percell_recall=float(np.nanmean([r["percell_recall"] for r in rows])),
        pseudobulk_precision=float(np.nanmean([r["pseudobulk_precision"] for r in rows])),
        pseudobulk_recall=float(np.nanmean([r["pseudobulk_recall"] for r in rows])),
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-donors", type=int, nargs="+", default=[3, 4, 5, 6, 8, 12])
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--n-genes", type=int, default=1500)
    ap.add_argument("--frac-de", type=float, default=0.05)
    ap.add_argument("--donor-dispersion", type=float, default=0.30)
    ap.add_argument("--cells-per-donor", type=int, default=200)
    ap.add_argument("--out", type=Path, default=Path("bench/metrics.json"))
    args = ap.parse_args()

    warnings.filterwarnings("ignore")  # pydeseq2 dispersion-trend chatter on small gene sets
    t0 = time.time()
    per_n, all_rows = {}, []
    for n in args.n_donors:
        rows = [run_one(n, s, args.n_genes, args.frac_de, args.donor_dispersion, args.cells_per_donor)
                for s in range(args.seeds)]
        all_rows += rows
        per_n[str(n)] = summarize(rows)
        s = per_n[str(n)]
        print(f"n={n:>2} | never_pass {s['never_pass_rate']:.2f}  blocker {s['blocker_rate']:.2f}  "
              f"abstain {s['abstain_rate']:.2f} | specificity {s['specificity']:.2f} "
              f"(pass {s['good_pass_rate']:.2f}) | surv {s['mean_survival']:.3f} "
              f"pf {s['mean_powered_fraction']:.2f} | precision  per-cell {s['percell_precision']:.2f} "
              f"vs pseudobulk {s['pseudobulk_precision']:.2f}", flush=True)

    out = dict(params=vars(args) | {"out": str(args.out)},
               overall=summarize(all_rows), by_n_donors=per_n,
               seconds=round(time.time() - t0, 1))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, default=str) + "\n")
    o = out["overall"]
    print(f"\nOVERALL  never_pass {o['never_pass_rate']:.3f} · specificity {o['specificity']:.3f} "
          f"· blocker {o['blocker_rate']:.3f} · abstain {o['abstain_rate']:.3f}")
    print(f"fidelity  per-cell precision {o['percell_precision']:.3f} → pseudobulk {o['pseudobulk_precision']:.3f} "
          f"(recall {o['pseudobulk_recall']:.3f})")
    print(f"specificity arm  mean survival {o['mean_good_survival']:.3f} "
          f"(degenerate/identity: {o['good_survival_is_degenerate']}) "
          f"-> specificity is {'A TAUTOLOGY' if o['good_survival_is_degenerate'] else 'a measurement'}")
    print(f"wrote {args.out}  [{out['seconds']}s]")


if __name__ == "__main__":
    main()
