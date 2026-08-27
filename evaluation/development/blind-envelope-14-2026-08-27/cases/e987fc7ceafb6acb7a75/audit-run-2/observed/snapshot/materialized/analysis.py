"""Two-stage discovery-and-validation analysis of honey floral-origin markers.

The study compares two declared floral origins (lime vs oilseed_rape) on a
pre-declared family of six physicochemical markers.

Stage one (screening) uses ONLY the pre-assigned discovery samples.
Stage two (confirmation) uses ONLY the pre-assigned validation samples, and
re-tests only the markers that survived screening, at a Bonferroni-adjusted
significance level based on the number of markers carried into this stage.

Every verdict the study draws comes from stage two. Stage one is screening
only and produces no confirmed finding on its own. Markers that fail screening
receive no verdict at all.

The analysis set assignment was made before any measurement and no
measurement influenced it, so the validation half is independent of the
selection made in the discovery half.

Run:  python3 analysis.py
"""

import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

# ----------------------------------------------------------------------------
# Pre-specified analysis choices
# ----------------------------------------------------------------------------

DATA_FILE = "honey_markers.csv"

GROUP_COL = "floral_origin"
SET_COL = "analysis_set"
GROUP_A = "lime"
GROUP_B = "oilseed_rape"
DISCOVERY = "discovery"
VALIDATION = "validation"

# The pre-declared outcome family, in the order the laboratory declared it.
MARKERS = [
    "moisture_pct",
    "conductivity_ms_per_cm",
    "hmf_mg_per_kg",
    "diastase_number",
    "proline_mg_per_kg",
    "free_acidity_meq_per_kg",
]

MARKER_LABELS = {
    "moisture_pct": "Moisture (%)",
    "conductivity_ms_per_cm": "Conductivity (mS/cm)",
    "hmf_mg_per_kg": "HMF (mg/kg)",
    "diastase_number": "Diastase number (Schade)",
    "proline_mg_per_kg": "Proline (mg/kg)",
    "free_acidity_meq_per_kg": "Free acidity (meq/kg)",
}

# Two-sample test used at both stages: Welch's t-test (unequal variances not
# assumed equal), two-sided. Fixed in advance and applied identically to every
# marker at both stages; no test is chosen per marker after seeing the data.
ALPHA_FAMILY = 0.05      # family-wise error rate the study protects
SCREEN_ALPHA = 0.05      # stage-one screening threshold, unadjusted


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def load_data(path):
    """Load the sample table and check the structural assumptions."""
    df = pd.read_csv(path)

    required = ["sample_id", GROUP_COL, SET_COL] + MARKERS
    missing_cols = [c for c in required if c not in df.columns]
    if missing_cols:
        raise ValueError("missing columns in %s: %s" % (path, missing_cols))

    if df["sample_id"].duplicated().any():
        raise ValueError("duplicate sample_id values found")

    if df[required].isna().any().any():
        raise ValueError("missing values found; the analysis expects none")

    groups = sorted(df[GROUP_COL].unique())
    if groups != sorted([GROUP_A, GROUP_B]):
        raise ValueError("unexpected %s values: %s" % (GROUP_COL, groups))

    sets = sorted(df[SET_COL].unique())
    if sets != sorted([DISCOVERY, VALIDATION]):
        raise ValueError("unexpected %s values: %s" % (SET_COL, sets))

    return df


def welch_test(x, y, conf_level):
    """Two-sided Welch t-test of mean(x) - mean(y), plus a matching CI.

    Returns a dict with group summaries, the mean difference, the Welch
    t statistic and degrees of freedom, the two-sided p-value, Hedges' g,
    and a confidence interval at the requested confidence level.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    nx, ny = len(x), len(y)
    mx, my = x.mean(), y.mean()
    vx, vy = x.var(ddof=1), y.var(ddof=1)

    diff = mx - my
    se = np.sqrt(vx / nx + vy / ny)
    tstat = diff / se

    # Welch-Satterthwaite degrees of freedom.
    dfree = (vx / nx + vy / ny) ** 2 / (
        (vx / nx) ** 2 / (nx - 1) + (vy / ny) ** 2 / (ny - 1)
    )
    pval = 2.0 * stats.t.sf(abs(tstat), dfree)

    tcrit = stats.t.ppf(0.5 + conf_level / 2.0, dfree)
    lo, hi = diff - tcrit * se, diff + tcrit * se

    # Hedges' g: standardised mean difference with the small-sample correction.
    pooled_sd = np.sqrt(((nx - 1) * vx + (ny - 1) * vy) / (nx + ny - 2))
    cohen_d = diff / pooled_sd if pooled_sd > 0 else np.nan
    j = 1.0 - 3.0 / (4.0 * (nx + ny) - 9.0)
    hedges_g = j * cohen_d

    return {
        "n_a": nx, "n_b": ny,
        "mean_a": mx, "mean_b": my,
        "sd_a": np.sqrt(vx), "sd_b": np.sqrt(vy),
        "diff": diff, "se": se,
        "t": tstat, "df": dfree, "p": pval,
        "ci_lo": lo, "ci_hi": hi, "conf_level": conf_level,
        "hedges_g": hedges_g,
    }


def fmt_p(p):
    if p < 1e-4:
        return "<0.0001"
    return "%.4f" % p


def rule(char="-", width=94):
    print(char * width)


# ----------------------------------------------------------------------------
# Analysis
# ----------------------------------------------------------------------------

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, DATA_FILE)
    df = load_data(path)

    disc = df[df[SET_COL] == DISCOVERY]
    val = df[df[SET_COL] == VALIDATION]

    print("=" * 94)
    print("HONEY FLORAL-ORIGIN MARKER STUDY: two-stage discovery / validation analysis")
    print("=" * 94)
    print("Data file        : %s" % DATA_FILE)
    print("Comparison       : %s vs %s (column '%s')" % (GROUP_A, GROUP_B, GROUP_COL))
    print("Declared family  : %d markers, in declared order" % len(MARKERS))
    print("Test             : Welch two-sample t-test, two-sided, at both stages")
    print("Family-wise level: alpha = %.2f, protected at the confirmation stage" % ALPHA_FAMILY)
    print()

    # --- Design and sample counts -------------------------------------------
    print("DESIGN AND SAMPLE COUNTS")
    rule()
    counts = pd.crosstab(df[GROUP_COL], df[SET_COL])
    counts = counts.reindex(index=[GROUP_A, GROUP_B], columns=[DISCOVERY, VALIDATION])
    print("%-16s %12s %12s %10s" % ("floral_origin", DISCOVERY, VALIDATION, "total"))
    for g in [GROUP_A, GROUP_B]:
        print("%-16s %12d %12d %10d" % (
            g, counts.loc[g, DISCOVERY], counts.loc[g, VALIDATION], counts.loc[g].sum()))
    print("%-16s %12d %12d %10d" % (
        "total", counts[DISCOVERY].sum(), counts[VALIDATION].sum(), len(df)))
    print()
    print("Analysis sets were pre-assigned before measurement, so the validation half")
    print("is independent of which markers the discovery half selects.")
    print()

    # --- Stage one: screening on the discovery half only --------------------
    print("STAGE ONE - SCREENING (discovery samples only, n = %d)" % len(disc))
    rule()
    print("Screening threshold: unadjusted p < %.2f. Screening results are NOT findings;" % SCREEN_ALPHA)
    print("they only decide which markers are carried into the validation stage.")
    print()
    header = "%-26s %17s %17s %10s %9s %10s" % (
        "marker", "%s mean(SD)" % GROUP_A, "%s mean(SD)" % GROUP_B,
        "diff", "p", "screen")
    print(header)
    rule()

    screen = {}
    for m in MARKERS:
        res = welch_test(disc.loc[disc[GROUP_COL] == GROUP_A, m],
                         disc.loc[disc[GROUP_COL] == GROUP_B, m],
                         conf_level=0.95)
        passed = res["p"] < SCREEN_ALPHA
        screen[m] = {"res": res, "passed": passed}
        print("%-26s %17s %17s %10.3f %9s %10s" % (
            MARKER_LABELS[m],
            "%.3f (%.3f)" % (res["mean_a"], res["sd_a"]),
            "%.3f (%.3f)" % (res["mean_b"], res["sd_b"]),
            res["diff"], fmt_p(res["p"]),
            "pass" if passed else "drop"))
    rule()

    carried = [m for m in MARKERS if screen[m]["passed"]]
    dropped = [m for m in MARKERS if not screen[m]["passed"]]
    print("Carried into confirmation (%d): %s" % (
        len(carried), ", ".join(MARKER_LABELS[m] for m in carried) if carried else "none"))
    print("Dropped at screening (%d): %s" % (
        len(dropped), ", ".join(MARKER_LABELS[m] for m in dropped) if dropped else "none"))
    print("Dropped markers receive no verdict: they are neither confirmed nor")
    print("declared absent, because they were never taken to the validation half.")
    print()

    if not carried:
        print("No marker survived screening, so no marker is confirmed.")
        return 0

    # --- Stage two: confirmation on the validation half only ----------------
    k = len(carried)
    alpha_adj = ALPHA_FAMILY / k
    conf_level = 1.0 - alpha_adj

    print("STAGE TWO - CONFIRMATION (validation samples only, n = %d)" % len(val))
    rule()
    print("Markers being confirmed in this stage: k = %d" % k)
    print("Bonferroni-adjusted significance level: alpha_adj = %.2f / %d = %.6f"
          % (ALPHA_FAMILY, k, alpha_adj))
    print("A marker is CONFIRMED only if its validation p-value is below alpha_adj.")
    print("Confidence intervals below are at the matching %.4f%% level." % (100 * conf_level))
    print()
    header = "%-26s %17s %17s %10s %19s %9s %11s" % (
        "marker", "%s mean(SD)" % GROUP_A, "%s mean(SD)" % GROUP_B,
        "diff", "CI", "p", "verdict")
    print(header)
    rule(width=114)

    confirm = {}
    for m in carried:
        res = welch_test(val.loc[val[GROUP_COL] == GROUP_A, m],
                         val.loc[val[GROUP_COL] == GROUP_B, m],
                         conf_level=conf_level)
        confirmed = res["p"] < alpha_adj
        confirm[m] = {"res": res, "confirmed": confirmed}
        print("%-26s %17s %17s %10.3f %19s %9s %11s" % (
            MARKER_LABELS[m],
            "%.3f (%.3f)" % (res["mean_a"], res["sd_a"]),
            "%.3f (%.3f)" % (res["mean_b"], res["sd_b"]),
            res["diff"],
            "[%.3f, %.3f]" % (res["ci_lo"], res["ci_hi"]),
            fmt_p(res["p"]),
            "CONFIRMED" if confirmed else "not conf."))
    rule(width=114)
    print()

    print("CONFIRMATION DETAIL")
    rule()
    for m in carried:
        res = confirm[m]["res"]
        print("%s" % MARKER_LABELS[m])
        print("  %s: n = %d, mean = %.3f, SD = %.3f" % (
            GROUP_A, res["n_a"], res["mean_a"], res["sd_a"]))
        print("  %s: n = %d, mean = %.3f, SD = %.3f" % (
            GROUP_B, res["n_b"], res["mean_b"], res["sd_b"]))
        print("  difference (%s - %s) = %.3f" % (GROUP_A, GROUP_B, res["diff"]))
        print("  %.4f%% CI = [%.3f, %.3f]" % (100 * res["conf_level"], res["ci_lo"], res["ci_hi"]))
        print("  Welch t = %.3f, df = %.2f, p = %s" % (res["t"], res["df"], fmt_p(res["p"])))
        print("  Hedges' g = %.3f" % res["hedges_g"])
        print("  verdict at alpha_adj = %.6f: %s" % (
            alpha_adj, "CONFIRMED" if confirm[m]["confirmed"] else "NOT CONFIRMED"))
        print()

    # --- Conclusions ---------------------------------------------------------
    confirmed = [m for m in carried if confirm[m]["confirmed"]]
    not_confirmed = [m for m in carried if not confirm[m]["confirmed"]]

    print("CONCLUSIONS (all verdicts rest on the validation stage)")
    rule()
    print("Confirmed markers (%d of %d declared): %s" % (
        len(confirmed), len(MARKERS),
        ", ".join(MARKER_LABELS[m] for m in confirmed) if confirmed else "none"))
    print("Screened in but NOT confirmed (%d): %s" % (
        len(not_confirmed),
        ", ".join(MARKER_LABELS[m] for m in not_confirmed) if not_confirmed else "none"))
    print("No verdict, dropped at screening (%d): %s" % (
        len(dropped),
        ", ".join(MARKER_LABELS[m] for m in dropped) if dropped else "none"))
    print()
    print("The discovery half contributed selection only. No discovery p-value is")
    print("reported as evidence of a difference.")
    print("Caveat: HMF is right-skewed, so its Welch test leans on the central limit")
    print("theorem at roughly %d samples per group rather than on normal data." %
          min(len(val[val[GROUP_COL] == GROUP_A]), len(val[val[GROUP_COL] == GROUP_B])))
    print("=" * 94)
    return 0


if __name__ == "__main__":
    sys.exit(main())
