"""Peatland restoration monitoring campaign: rewetted vs drained collar comparison.

Reads the fixed campaign record in data.csv, summarises each declared outcome by
drainage block, runs one two-sample test per declared outcome, and then corrects the
complete four-outcome family for multiplicity in a single call.

The multiplicity correction is done with pingouin, a specialist third-party statistics
package, rather than with numpy or statsmodels. Every significance verdict below is read
off the adjusted p-values at a family-wise level of 0.05. Raw p-values are printed for
transparency only and are never used to decide anything.

data.csv is input only. This script never generates, simulates or overwrites it.
"""

from pathlib import Path

import pandas as pd
import pingouin as pg
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "data.csv"

GROUP_COLUMN = "drainage_status"
REWETTED_LABEL = "rewetted"
DRAINED_LABEL = "drained"

# The pre-declared outcome family, in the fixed order given by the monitoring plan.
# (column name, human-readable name, unit, decimals for printing)
OUTCOME_FAMILY = [
    ("methane_flux_mgc_m2_h", "Methane flux", "mg C m-2 h-1", 2),
    ("respiration_co2_flux_mgc_m2_h", "Ecosystem respiration (CO2 flux)", "mg C m-2 h-1", 2),
    ("water_table_depth_cm", "Water table depth below surface", "cm", 2),
    ("sphagnum_cover_pct", "Sphagnum cover", "% of ground area", 2),
]

# Family-wise error level for the complete declared family.
FAMILY_ALPHA = 0.05

# Per-outcome test, fixed for the whole family in advance: Welch's two-sample t-test.
# It is a two-sample test of the difference in means that does not assume the two blocks
# share a variance, which matters here because the drained block is much less variable
# than the rewetted block on the flux outcomes. The same test is applied to every
# outcome, so no test is picked after seeing a result.
#
# Multiplicity method, also fixed in advance: Holm step-down, which controls the
# family-wise error rate over the complete declared family.
CORRECTION_METHOD = "holm"


def load_data(path):
    """Read the fixed campaign record. Input only."""
    frame = pd.read_csv(path)
    return frame


def fmt_p(p):
    """Print a p-value without collapsing very small values to zero."""
    if p < 1e-4:
        return f"{p:.3e}"
    return f"{p:.4f}"


def describe_group(values):
    """Per-group summary values for one outcome in one block."""
    return {
        "n": int(values.count()),
        "mean": float(values.mean()),
        "sd": float(values.std(ddof=1)),
        "median": float(values.median()),
        "min": float(values.min()),
        "max": float(values.max()),
    }


def main():
    data = load_data(DATA_FILE)

    rewetted = data[data[GROUP_COLUMN] == REWETTED_LABEL]
    drained = data[data[GROUP_COLUMN] == DRAINED_LABEL]

    print("Peatland restoration monitoring campaign")
    print("=" * 72)
    print(f"Data file: {DATA_FILE.name}")
    print(f"Rows (collars) read: {len(data)}")
    print()
    print("Group sizes")
    print("-" * 72)
    print(f"  {REWETTED_LABEL:<10s} collars: {len(rewetted)}")
    print(f"  {DRAINED_LABEL:<10s} collars: {len(drained)}")
    print()

    print("Per-group summary values, by declared outcome")
    print("-" * 72)
    summaries = {}
    for column, label, unit, dp in OUTCOME_FAMILY:
        rew = describe_group(rewetted[column])
        dra = describe_group(drained[column])
        summaries[column] = (rew, dra)
        print(f"{label} ({unit})  [{column}]")
        for name, s in ((REWETTED_LABEL, rew), (DRAINED_LABEL, dra)):
            print(
                f"  {name:<10s} n={s['n']:<3d} "
                f"mean={s['mean']:.{dp}f}  sd={s['sd']:.{dp}f}  "
                f"median={s['median']:.{dp}f}  "
                f"range=[{s['min']:.{dp}f}, {s['max']:.{dp}f}]"
            )
        print(f"  difference in means (rewetted - drained) = {rew['mean'] - dra['mean']:.{dp}f}")
        print()

    print("Two-sample tests, one per declared outcome")
    print("-" * 72)
    print("Test: Welch's two-sample t-test (two-sided, unequal variances not assumed equal).")
    print("Raw p-values below are for transparency only; no verdict is taken from them.")
    print()
    raw_pvalues = []
    for column, label, unit, dp in OUTCOME_FAMILY:
        result = stats.ttest_ind(
            rewetted[column].to_list(),
            drained[column].to_list(),
            equal_var=False,
        )
        raw_pvalues.append(float(result.pvalue))
        print(
            f"{label:<34s} t = {float(result.statistic):+8.3f}   "
            f"raw p = {fmt_p(float(result.pvalue))}"
        )
    print()

    # Multiplicity: the four declared outcomes are one family, so all four raw p-values
    # are corrected together, in one call, by the specialist package.
    reject, adjusted_pvalues = pg.multicomp(
        raw_pvalues, alpha=FAMILY_ALPHA, method=CORRECTION_METHOD
    )
    adjusted_pvalues = [float(p) for p in adjusted_pvalues]
    reject = [bool(r) for r in reject]

    print("Family-wise multiplicity correction")
    print("-" * 72)
    print(f"Package: pingouin version {pg.__version__}")
    print(f"Call: pingouin.multicomp(pvals, alpha={FAMILY_ALPHA}, method='{CORRECTION_METHOD}')")
    print(f"Outcomes corrected together in one call: {len(raw_pvalues)} "
          f"(the complete declared family)")
    print("Method: Holm step-down, controlling the family-wise error rate.")
    print()

    print("Verdicts, taken from the adjusted p-values at the 0.05 family level")
    print("-" * 72)
    print(f"{'Outcome':<34s} {'raw p':>11s} {'adjusted p':>12s}  verdict")
    for (column, label, unit, dp), raw_p, adj_p, rej in zip(
        OUTCOME_FAMILY, raw_pvalues, adjusted_pvalues, reject
    ):
        verdict = "significant" if rej else "not significant"
        print(f"{label:<34s} {fmt_p(raw_p):>11s} {fmt_p(adj_p):>12s}  {verdict}")
    print()

    print("Per-outcome conclusions")
    print("-" * 72)
    for (column, label, unit, dp), adj_p, rej in zip(OUTCOME_FAMILY, adjusted_pvalues, reject):
        rew, dra = summaries[column]
        direction = "higher" if rew["mean"] > dra["mean"] else "lower"
        if rej:
            print(
                f"{label}: rewetted collars are {direction} than drained collars "
                f"({rew['mean']:.{dp}f} vs {dra['mean']:.{dp}f} {unit}); "
                f"adjusted p = {fmt_p(adj_p)}, significant at the 0.05 family level."
            )
        else:
            print(
                f"{label}: no separation demonstrated between the blocks "
                f"({rew['mean']:.{dp}f} vs {dra['mean']:.{dp}f} {unit}); "
                f"adjusted p = {fmt_p(adj_p)}, not significant at the 0.05 family level."
            )
    print()

    n_significant = sum(reject)
    print(
        f"Summary: {n_significant} of {len(OUTCOME_FAMILY)} declared outcomes separate the "
        f"two drainage blocks after correcting the complete family."
    )


if __name__ == "__main__":
    main()
