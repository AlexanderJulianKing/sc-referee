"""Amphibian recovery in restored vs unrestored floodplain ponds.

Reporting script. Descriptive summaries come from data.csv; every inferential
statement comes from adjusted_results.csv, which the upstream correction step
produced by testing the whole family of five outcomes and applying one
family-wide correction across all five p-values at the five-percent level. This
script does not run any test of its own.
"""

import pandas as pd

DATA = "data.csv"
ADJUSTED = "adjusted_results.csv"

GROUP = "status"
LEVELS = ["unrestored", "restored"]

OUTCOMES = [
    "amphibian_species",
    "egg_mass_count",
    "emergent_veg_pct",
    "dissolved_oxygen_mg_l",
    "hydroperiod_days",
]


def describe(ponds):
    print("Ponds surveyed: %d (%s)" % (
        len(ponds),
        ", ".join("%s %d" % (lvl, int((ponds[GROUP] == lvl).sum()))
                  for lvl in LEVELS),
    ))
    print()
    header = "%-22s %13s %8s %12s %8s" % (
        "outcome", "unrest. mean", "sd", "rest. mean", "sd")
    print(header)
    print("-" * len(header))
    for name in OUTCOMES:
        u = ponds.loc[ponds[GROUP] == "unrestored", name].astype(float)
        r = ponds.loc[ponds[GROUP] == "restored", name].astype(float)
        print("%-22s %13.2f %8.2f %12.2f %8.2f" % (
            name, u.mean(), u.std(ddof=1), r.mean(), r.std(ddof=1)))


def report(adjusted):
    methods = sorted(set(adjusted["correction_method"]))
    print("Inference read from %s (correction method: %s)" % (
        ADJUSTED, ", ".join(methods)))
    print()
    header = "%-22s %12s %12s %11s %11s  %s" % (
        "outcome", "unrestored", "restored", "p raw", "p adjusted", "verdict")
    print(header)
    print("-" * len(header))

    significant = []
    for _, row in adjusted.iterrows():
        is_sig = str(row["decision"]).strip().lower() == "significant"
        if is_sig:
            significant.append(row["outcome"])
        print("%-22s %12.2f %12.2f %11.2e %11.2e  %s" % (
            row["outcome"], row["mean_unrestored"], row["mean_restored"],
            row["p_raw"], row["p_adjusted"],
            "significant" if is_sig else "not significant",
        ))

    print()
    print("Significant after family-wide correction: %d of %d outcomes." % (
        len(significant), len(adjusted)))
    if significant:
        print("  " + ", ".join(significant))


def main():
    ponds = pd.read_csv(DATA)
    adjusted = pd.read_csv(ADJUSTED)

    missing = set(OUTCOMES) - set(adjusted["outcome"])
    if missing:
        raise SystemExit("%s is missing outcomes: %s" % (
            ADJUSTED, ", ".join(sorted(missing))))

    describe(ponds)
    print()
    report(adjusted)


if __name__ == "__main__":
    main()
