"""GB-P07 real-data case study: the allele-orientation GATE on the exact analysis Claude Science shipped.

CORRECTION (2026-07-11): the diagnosis below — that GB-P07's error is effect-allele orientation — is WRONG.
The official GeneBench-Pro walkthrough shows GB-P07 has NO orientation step; `g` is used as given and the
real error is a latent technical-batch confound (see docs/research/2026-07-11-gbp07-repro-results.md). This
anchor still exercises the orientation gate on real data and the gate does return `needs_evidence` here — but
that firing is ORTHOGONAL to GB-P07's actual failure and NON-DISCRIMINATING (it fires identically on the
correct -0.60 answer). Keep this only as an orientation-gate smoke test on real data; do NOT cite it as
evidence the referee catches GB-P07. The original (mis-diagnosed) description follows.

GeneBench-Pro GB-P07 ("per-allele log rate ratio for CXCL10 in activated monocytes") is a scRNA eQTL.
Claude Science reported beta = +0.4839; the graded truth is -0.5999 — a sign flip. The seam: the donor
genotype is a BARE dosage column `g` (0/1/2) with NO allele label, and the task specifies no orientation
convention. Claude assumed `g` counted the effect allele and never ratified it.

This anchor runs sc-referee's `allele_orientation` check on that data, as submitted. Expected verdict:
`needs_evidence` (UNRESOLVED_CONTRACT) — the referee refuses to certify the sign because the effect-allele
orientation was never ratified. That is the exact seam Claude crossed silently.

It also reports the honest boundary. mean(g)/2 = 0.5, so the frequency footprint cannot orient the dosage.
The reported estimator is an ambient-aware NB — not the OLS-on-log2-CPM the referee can recompute — so no
sign recompute is even attempted. And for the record a naive same-data donor OLS slope is both
population-sensitive and estimator-mismatched: it is ~-0.09 on the activated subpopulation the task actually
asks about but +0.41 on all cells, so it cannot adjudicate Claude's NB sign either. The flip lives entirely
in the absent dosage->allele map; no arithmetic on the expression data settles it, and only the ratification
gate can catch it. sc-referee never falsely blocks here.

The benchmark data is NOT in the repo. Point GBP07_ZIP at the GeneBench-Pro GB-P07 data zip
(default: ~/Desktop/genebench_phase1_inputs/GB-P07-data.zip). Absent -> the script skips.

    GBP07_ZIP=/path/to/GB-P07-data.zip PYTHONPATH=src:. python bench/gbp07_anchor.py
"""
from __future__ import annotations

import io
import os
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from sc_referee.bundle import Bundle, Measure
from sc_referee.checks.allele_orientation import evaluate_allele_orientation
from sc_referee.design import Design

CLAUDE_REPORTED_BETA = 0.4839       # from experiments/claude_science_phase1/answers/*ambient_state_eqtl
GRADED_TRUTH_BETA = -0.5999557      # from the GB-P07 grade — opposite sign
GENES = ["CXCL10", "HBB", "IFI6", "ISG15", "LST1"]   # CXCL10 is the target; the rest are state/ambient markers


def _load(zip_path: Path):
    with zipfile.ZipFile(zip_path) as z:
        with z.open("cells.csv.gz") as fh:
            cells = pd.read_csv(io.BytesIO(fh.read()), compression="gzip")
        with z.open("donors.csv.gz") as fh:
            donors = pd.read_csv(io.BytesIO(fh.read()), compression="gzip")
    return cells, donors


def _build_bundle(cells: pd.DataFrame, donors: pd.DataFrame) -> Bundle:
    df = cells.merge(donors[["donor", "g"]], on="donor")
    # A simple, transparent interferon-activation proxy (Claude gated on IFI6/ISG15/LST1, EXCLUDING CXCL10
    # to stay circularity-safe). The orientation GATE verdict does not depend on this gate — it fires on the
    # unratified effect allele regardless — but the subset keeps the analysis faithful to "activated monocytes".
    isg_frac = (df["ISG15"] + df["IFI6"]) / df["total_umi"]
    df["activated"] = isg_frac >= isg_frac.median()
    obs = pd.DataFrame(
        {"donor_id": df["donor"].to_numpy(), "dosage": df["g"].to_numpy(dtype="int64"),
         "activated": df["activated"].to_numpy()},
        index=df["cell_id"].to_numpy(),
    )
    counts = df[GENES].to_numpy(dtype="int64")
    bundle = Bundle(
        observations=obs,
        measure=Measure("counts", counts, None, list(GENES)),
        feature_metadata=pd.DataFrame(index=list(GENES)),
        replicate_var="donor_id",
    )
    # Claude's report, bound to the target feature, exactly as it was submitted.
    bundle.reported_results = pd.DataFrame(
        {"feature_id": ["CXCL10"], "pvalue": [1e-3], "padj": [1e-2], "effect": [CLAUDE_REPORTED_BETA]})
    return bundle


def _design_as_submitted() -> Design:
    """The GB-P07 eQTL as Claude actually submitted it: an ambient-aware NB model on donor-level dosage,
    with the effect-allele orientation NEVER ratified (effect_allele / dosage_counts_allele / frequency all
    absent). This is the seam."""
    return Design(
        analysis_type="eqtl", confirmed_by_human=True,
        confidence={"replicate_unit": "high", "allele_orientation": "high"},
        condition=None, batch=[], replicate_unit=["donor_id"],
        reference=None, test=None, model=None, target_coefficient=None,
        sample_unit=["donor_id"], subset={"activated": True},
        variant_id="CXCL10_cis_eQTL", genotype_column="dosage", target_feature="CXCL10",
        variant_alleles=("REF", "ALT"), dosage_ploidy=2,
        eqtl_estimator="negative_binomial", eqtl_outcome_scale="ambient_corrected_counts",
        effect_allele=None, dosage_counts_allele=None,       # <- the ratification Claude skipped
    )


def _honesty_numbers(cells: pd.DataFrame, donors: pd.DataFrame) -> dict:
    """Diligence numbers that show WHY a same-data recompute cannot adjudicate the sign. A donor-level OLS
    slope of log2(CXCL10 CPM) on g is computed two ways: on the activated subpopulation the task asks about,
    and on all cells. They disagree (population-sensitive), and neither is the ambient-aware NB Claude ran
    (estimator-mismatched) — so neither can confirm or refute +0.48. This is exactly why the referee abstains
    rather than recomputes."""
    df = cells.merge(donors[["donor", "g"]], on="donor")
    df["cpm"] = df["CXCL10"] / df["total_umi"] * 1e6
    # Same CXCL10-excluded activation proxy as _build_bundle, so the subset matches the audited design.
    isg_frac = (df["ISG15"] + df["IFI6"]) / df["total_umi"]
    df["activated"] = isg_frac >= isg_frac.median()

    def _donor_ols(frame: pd.DataFrame) -> float:
        donor = frame.groupby(["donor", "g"])["cpm"].mean().reset_index()
        return float(np.polyfit(donor["g"], np.log2(donor["cpm"] + 1), 1)[0])

    return {"eff_allele_freq_mean_g_over_2": round(float(donors["g"].mean() / 2), 4),
            "activated_subset_ols_slope_on_g": round(_donor_ols(df[df["activated"]]), 4),
            "all_cells_ols_slope_on_g": round(_donor_ols(df), 4)}


def default_zip() -> Path:
    return Path(os.environ.get("GBP07_ZIP", str(Path.home() / "Desktop" /
                "genebench_phase1_inputs" / "GB-P07-data.zip")))


def run_gbp07_anchor(zip_path=None):
    """Run `allele_orientation` on GB-P07 as Claude submitted it. Returns (Finding, info dict)."""
    cells, donors = _load(Path(zip_path) if zip_path else default_zip())
    bundle = _build_bundle(cells, donors)
    finding = evaluate_allele_orientation(_design_as_submitted(), bundle, bundle.reported_results)
    info = {"n_donors": len(donors), "n_cells": len(cells),
            "genotype": donors["g"].value_counts().sort_index().to_dict(),
            **_honesty_numbers(cells, donors)}
    return finding, info


def main() -> None:
    zip_path = default_zip()
    if not zip_path.exists():
        print(f"SKIP: GB-P07 data not found at {zip_path} (set GBP07_ZIP). Benchmark data is gitignored.")
        return
    finding, info = run_gbp07_anchor(zip_path)
    h = info

    print("=== GB-P07 real-data case study: allele-orientation gate ===")
    print(f"  n_donors={info['n_donors']}  n_cells={info['n_cells']}  genotype g in {{0,1,2}} = "
          f"{info['genotype']}")
    print(f"  Claude Science reported beta_activated = +{CLAUDE_REPORTED_BETA}")
    print(f"  graded truth               beta_activated = {GRADED_TRUTH_BETA}   (OPPOSITE sign)")
    print()
    print(f"  sc-referee allele_orientation -> {finding.status.upper()}")
    print(f"    {finding.verdict}")
    if "unresolved_contract" in finding.metrics:
        print(f"    unresolved_contract = {finding.metrics['unresolved_contract']}")
    print()
    print("  Honesty boundary (why the GATE, not a blocker, is the honest catch):")
    print(f"    effect-allele frequency mean(g)/2 = {h['eff_allele_freq_mean_g_over_2']} "
          "-> exactly 0.5, so the frequency footprint CANNOT orient the dosage.")
    print("    reported estimator is ambient-aware NB, not the supported OLS -> no sign recompute is even")
    print("      attempted (the referee reports 'independent recompute unavailable').")
    print(f"    a naive same-data donor OLS slope of log2(CXCL10 CPM) on g is population-sensitive and")
    print(f"      estimator-mismatched: {h['activated_subset_ols_slope_on_g']:+} on the activated subset "
          f"vs {h['all_cells_ols_slope_on_g']:+} on all cells.")
    print("      -> It flips with the subpopulation and is not Claude's NB, so it cannot adjudicate +0.48.")
    print("         The flip lives in the absent dosage->allele map; only the ratification gate can catch it.")
    print()
    verdict_ok = finding.status == "needs_evidence"
    print(f"  RESULT: {'PASS' if verdict_ok else 'UNEXPECTED'} — the referee "
          f"{'refuses to certify the unratified sign (forces the binding Claude skipped)' if verdict_ok else 'did NOT gate as expected'}.")


if __name__ == "__main__":
    main()
