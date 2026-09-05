"""Tram corridor noise survey: two-group comparison of the four declared outcomes.

Reads the fixed authored data file data.csv, compares tram corridor dwellings with
control dwellings on each of the four pre-declared outcomes with Welch's two-sample
t-test, and controls the family-wise error rate over the complete declared family of
four outcomes with the Holm-Bonferroni procedure at alpha = 0.05. Every verdict is
taken from the adjusted p-value.

A single labelled robustness check re-runs the indoor night-time comparison with the
one implausible dwelling excluded. That re-run is outside the declared family, changes
no verdict, and supports no additional inferential claim.

Run from the project root with no arguments:  python3 analysis.py
"""

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

DATA_FILE = "data.csv"
GROUP_COLUMN = "street_type"
EXPOSED_GROUP = "tram_corridor"
CONTROL_GROUP = "control"
ALPHA = 0.05

# The four outcomes in the order the survey plan declared them.
DECLARED_OUTCOMES = [
    ("indoor_night_level_db", "Indoor night-time equivalent level (dB)"),
    ("facade_lden_db", "Facade day-evening-night level (dB)"),
    ("sleep_disturbance_score", "Self-reported sleep disturbance (0-10)"),
    ("awakenings_per_night", "Noise-related awakenings per night (count)"),
]

# Dwelling flagged in the data description: measured during unrelated building work.
IMPLAUSIBLE_DWELLING_ID = "DW-019"


def format_p(value):
    """Format a p-value without rounding very small values away to zero."""
    return f"{value:.6f}" if value >= 1e-6 else f"{value:.3e}"


def describe(values):
    """Return n, mean and sample standard deviation for one group of measurements."""
    return len(values), values.mean(), values.std(ddof=1)


def compare_groups(frame, column):
    """Welch's two-sample t-test of exposed against control for one outcome column."""
    exposed = frame.loc[frame[GROUP_COLUMN] == EXPOSED_GROUP, column]
    control = frame.loc[frame[GROUP_COLUMN] == CONTROL_GROUP, column]
    result = stats.ttest_ind(exposed, control, equal_var=False)
    return describe(exposed), describe(control), float(result.statistic), float(result.pvalue)


def main():
    data = pd.read_csv(DATA_FILE)

    print("=" * 78)
    print("TRAM CORRIDOR NOISE SURVEY: PRIMARY ANALYSIS")
    print("=" * 78)
    print(f"Data file            : {DATA_FILE}")
    print(f"Dwellings            : {len(data)}")
    print(f"Groups compared      : {EXPOSED_GROUP} vs {CONTROL_GROUP}")
    print("Test                 : Welch's two-sample t-test (two-sided)")
    print("Declared family      : all four outcomes below, adjusted together")
    print(f"Multiplicity control : Holm-Bonferroni, family-wise error held at {ALPHA:.2f}")
    print()

    results = []
    for column, label in DECLARED_OUTCOMES:
        exposed_stats, control_stats, t_stat, p_raw = compare_groups(data, column)
        results.append(
            {
                "column": column,
                "label": label,
                "exposed": exposed_stats,
                "control": control_stats,
                "t": t_stat,
                "p_raw": p_raw,
            }
        )

    # One adjustment over the complete declared family of four p-values.
    reject, p_adjusted, _, _ = multipletests(
        [r["p_raw"] for r in results], alpha=ALPHA, method="holm"
    )
    for result, p_adj, is_rejected in zip(results, p_adjusted, reject):
        result["p_adj"] = float(p_adj)
        result["verdict"] = (
            "significant after adjustment"
            if is_rejected
            else "not significant after adjustment"
        )

    for position, result in enumerate(results, start=1):
        n_e, mean_e, sd_e = result["exposed"]
        n_c, mean_c, sd_c = result["control"]
        print(f"Declared outcome {position}: {result['label']}")
        print(f"  column                 : {result['column']}")
        print(f"  {EXPOSED_GROUP:<14}       : n = {n_e}, mean = {mean_e:.2f}, sd = {sd_e:.2f}")
        print(f"  {CONTROL_GROUP:<14}       : n = {n_c}, mean = {mean_c:.2f}, sd = {sd_c:.2f}")
        print(f"  difference (exposed-control): {mean_e - mean_c:+.2f}")
        print(f"  Welch t                : {result['t']:.3f}")
        print(f"  raw p-value            : {format_p(result['p_raw'])}")
        print(f"  Holm-adjusted p-value  : {format_p(result['p_adj'])}")
        print(f"  verdict (from adjusted): {result['verdict']}")
        print()

    print("=" * 78)
    print("ROBUSTNESS CHECK (NOT PART OF THE DECLARED FAMILY)")
    print("=" * 78)
    print(
        "Sensitivity re-run of declared outcome 1 only, with the one implausible\n"
        f"dwelling ({IMPLAUSIBLE_DWELLING_ID}, measured during unrelated building work) excluded.\n"
        "This re-run is descriptive. It is not multiplicity-adjusted, it does not enter\n"
        "the declared family, it changes no verdict above, and it supports no additional\n"
        "inferential claim."
    )
    print()

    reduced = data.loc[data["dwelling_id"] != IMPLAUSIBLE_DWELLING_ID]
    column, label = DECLARED_OUTCOMES[0]
    exposed_stats, control_stats, t_stat, p_raw = compare_groups(reduced, column)
    n_e, mean_e, sd_e = exposed_stats
    n_c, mean_c, sd_c = control_stats
    print(f"Outcome re-run           : {label} ({column})")
    print(f"  rows excluded          : 1 ({IMPLAUSIBLE_DWELLING_ID})")
    print(f"  {EXPOSED_GROUP:<14}       : n = {n_e}, mean = {mean_e:.2f}, sd = {sd_e:.2f}")
    print(f"  {CONTROL_GROUP:<14}       : n = {n_c}, mean = {mean_c:.2f}, sd = {sd_c:.2f}")
    print(f"  difference (exposed-control): {mean_e - mean_c:+.2f}")
    print(f"  Welch t                : {t_stat:.3f}")
    print(f"  unadjusted p-value     : {format_p(p_raw)}")
    print("  no verdict is taken from this robustness check")
    print()
    print("End of analysis.")


if __name__ == "__main__":
    main()
