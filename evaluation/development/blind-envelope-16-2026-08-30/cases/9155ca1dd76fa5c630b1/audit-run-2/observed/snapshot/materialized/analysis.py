"""Screenhouse irrigation-scheduling experiment on pearl millet landraces.

This script does exactly two jobs:

1. Descriptive and housekeeping work on the raw per-plant file
   (`millet_irrigation.csv`): group sizes, per-group means and spreads for
   each declared outcome, and routine data checks.  No significance test,
   no p-value and no multiplicity correction is computed here.

2. Reading the completed upstream inference table
   (`upstream_inference.csv`).  Every significance verdict is taken
   straight from the family-adjusted p-value recorded there, judged at
   0.05.  The per-outcome tests and the family-wise correction over the
   six declared outcomes were carried out upstream; nothing about them is
   recomputed.
"""

import sys

import pandas as pd

RAW_FILE = "millet_irrigation.csv"
INFERENCE_FILE = "upstream_inference.csv"

ID_COL = "plant_id"
GROUP_COL = "irrigation"

# The outcome family exactly as declared in advance, in the declared order.
DECLARED_OUTCOMES = [
    "plant_height_cm",
    "panicle_length_cm",
    "grain_yield_g",
    "thousand_grain_mass_g",
    "leaf_rwc_pct",
    "stomatal_cond_mmol",
]

OUTCOME_LABELS = {
    "plant_height_cm": "Plant height (cm)",
    "panicle_length_cm": "Panicle length (cm)",
    "grain_yield_g": "Grain yield per plant (g)",
    "thousand_grain_mass_g": "Thousand-grain mass (g)",
    "leaf_rwc_pct": "Leaf relative water content (%)",
    "stomatal_cond_mmol": "Stomatal conductance (mmol m-2 s-1)",
}

# Plausible measurement ranges for the housekeeping range check.
PLAUSIBLE_RANGES = {
    "plant_height_cm": (120.0, 210.0),
    "panicle_length_cm": (15.0, 32.0),
    "grain_yield_g": (12.0, 48.0),
    "thousand_grain_mass_g": (6.5, 12.0),
    "leaf_rwc_pct": (55.0, 95.0),
    "stomatal_cond_mmol": (90.0, 420.0),
}

EXPECTED_ROWS = 56
EXPECTED_GROUPS = 2
EXPECTED_PER_GROUP = 28

# The level the upstream family-wise correction was carried out at, and so
# the level the adjusted p-values are judged against here.
ALPHA = 0.05


def rule(char="-", width=78):
    print(char * width)


def check(label, passed, detail=""):
    """Record one housekeeping check and report it."""
    status = "PASS" if passed else "FAIL"
    line = "  [{}] {}".format(status, label)
    if detail:
        line += " -- " + detail
    print(line)
    return passed


def describe_raw(raw):
    """Descriptive and housekeeping work on the raw file only."""
    print("=" * 78)
    print("PART 1  DESCRIPTIVE SUMMARY AND DATA CHECKS ({})".format(RAW_FILE))
    print("=" * 78)
    print("No significance test, p-value or multiplicity correction is")
    print("computed in this part.")
    print()

    groups = sorted(raw[GROUP_COL].unique())

    print("Group sizes")
    rule()
    for name in groups:
        print("  {:<10s} n = {:d}".format(name, int((raw[GROUP_COL] == name).sum())))
    print("  {:<10s} n = {:d}".format("total", len(raw)))
    print()

    print("Per-group means and spreads, declared outcome order")
    rule()
    header = "  {:<24s} {:>8s} {:>9s} {:>9s} {:>9s} {:>9s}".format(
        "outcome", "group", "mean", "sd", "min", "max"
    )
    print(header)
    for outcome in DECLARED_OUTCOMES:
        for name in groups:
            values = raw.loc[raw[GROUP_COL] == name, outcome]
            print(
                "  {:<24s} {:>8s} {:>9.3f} {:>9.3f} {:>9.2f} {:>9.2f}".format(
                    outcome,
                    name,
                    values.mean(),
                    values.std(ddof=1),
                    values.min(),
                    values.max(),
                )
            )
    print()

    print("Housekeeping checks")
    rule()
    ok = True
    ok &= check(
        "row count is {}".format(EXPECTED_ROWS),
        len(raw) == EXPECTED_ROWS,
        "found {}".format(len(raw)),
    )
    ok &= check(
        "exactly {} distinct group values".format(EXPECTED_GROUPS),
        len(groups) == EXPECTED_GROUPS,
        "found {}".format(", ".join(map(str, groups))),
    )
    for name in groups:
        n = int((raw[GROUP_COL] == name).sum())
        ok &= check(
            "group '{}' holds {} plants".format(name, EXPECTED_PER_GROUP),
            n == EXPECTED_PER_GROUP,
            "found {}".format(n),
        )
    ok &= check(
        "identifiers unique",
        raw[ID_COL].is_unique,
        "{} unique of {}".format(raw[ID_COL].nunique(), len(raw)),
    )
    missing = int(raw.isna().sum().sum())
    ok &= check("no missing values anywhere", missing == 0, "{} missing cells".format(missing))
    ok &= check(
        "all six declared outcomes present",
        all(c in raw.columns for c in DECLARED_OUTCOMES),
        "columns: {}".format(", ".join(raw.columns)),
    )
    for outcome in DECLARED_OUTCOMES:
        low, high = PLAUSIBLE_RANGES[outcome]
        values = raw[outcome]
        inside = bool(((values >= low) & (values <= high)).all())
        ok &= check(
            "{} within plausible range [{:g}, {:g}]".format(outcome, low, high),
            inside,
            "observed [{:.2f}, {:.2f}]".format(values.min(), values.max()),
        )
    print()
    print("  All housekeeping checks passed." if ok else "  SOME HOUSEKEEPING CHECKS FAILED.")
    print()
    return ok, groups


def report_verdicts(raw, inference, groups):
    """Read the upstream adjusted p-values and report the verdict each implies."""
    print("=" * 78)
    print("PART 2  UPSTREAM INFERENCE READ BACK ({})".format(INFERENCE_FILE))
    print("=" * 78)
    print("The per-outcome comparisons and the family-wise correction over all")
    print("six declared outcomes were carried out upstream. Each verdict below is")
    print("read straight from the family-adjusted p-value in that file and judged")
    print("against alpha = {:g}. Nothing is recomputed from the raw data.".format(ALPHA))
    print()

    table = inference.set_index("outcome")

    missing_rows = [o for o in DECLARED_OUTCOMES if o not in table.index]
    if missing_rows:
        print("  ERROR: inference table is missing rows for: {}".format(", ".join(missing_rows)))
        return False

    print(
        "  {:<24s} {:>10s} {:>10s} {:>10s} {:>12s} {:>13s}  {}".format(
            "outcome", "mean_full", "mean_def", "diff", "p_raw", "p_adj", "verdict"
        )
    )
    rule("-", 110)
    for outcome in DECLARED_OUTCOMES:
        full_mean = raw.loc[raw[GROUP_COL] == "full", outcome].mean()
        deficit_mean = raw.loc[raw[GROUP_COL] == "deficit", outcome].mean()
        p_raw = float(table.loc[outcome, "p_raw"])
        p_adj = float(table.loc[outcome, "p_adj"])
        verdict = "significant" if p_adj < ALPHA else "not significant"
        print(
            "  {:<24s} {:>10.3f} {:>10.3f} {:>10.3f} {:>12.6g} {:>13.6g}  {}".format(
                outcome, full_mean, deficit_mean, full_mean - deficit_mean, p_raw, p_adj, verdict
            )
        )
    print()

    print("Per-outcome detail")
    rule()
    for outcome in DECLARED_OUTCOMES:
        p_adj = float(table.loc[outcome, "p_adj"])
        p_raw = float(table.loc[outcome, "p_raw"])
        verdict = "significant" if p_adj < ALPHA else "not significant"
        print("  {} [{}]".format(OUTCOME_LABELS[outcome], outcome))
        for name in groups:
            values = raw.loc[raw[GROUP_COL] == name, outcome]
            print(
                "    {:<8s} n = {:2d}   mean = {:8.3f}   sd = {:7.3f}".format(
                    name, len(values), values.mean(), values.std(ddof=1)
                )
            )
        print(
            "    upstream p_raw = {:.6g}   upstream p_adj = {:.6g}   "
            "verdict at {:g}: {}".format(p_raw, p_adj, ALPHA, verdict)
        )
        print()
    return True


def main():
    raw = pd.read_csv(RAW_FILE)
    inference = pd.read_csv(INFERENCE_FILE)

    checks_ok, groups = describe_raw(raw)
    verdicts_ok = report_verdicts(raw, inference, groups)

    if not (checks_ok and verdicts_ok):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
