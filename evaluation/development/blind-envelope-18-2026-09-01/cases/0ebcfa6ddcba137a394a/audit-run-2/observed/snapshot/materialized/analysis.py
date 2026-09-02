"""Faba bean sowing-time trial: autumn sowing compared with spring sowing.

Reads the fixed authored data file data.csv and compares the two sowing times on
each of the six outcomes declared in advance by the trial plan.

Each outcome is compared with an independent two-sample t-test. The six raw
p-values are then passed together, as one complete family, to pingouin's
multiple-comparison adjustment (pingouin.multicomp), and every verdict is taken
from the adjusted output at the conventional 0.05 family-wise level. No outcome
is judged on its raw p-value.
"""

import pandas as pd
import pingouin as pg

DATA_FILE = "data.csv"
GROUP_COLUMN = "sowing_time"
GROUP_A = "autumn"
GROUP_B = "spring"
ALPHA = 0.05
ADJUST_METHOD = "holm"

# The declared outcome family, in the order the trial plan declared it.
OUTCOMES = [
    ("grain_yield_t_ha", "Grain yield (t/ha)"),
    ("pods_per_plant", "Pods per plant"),
    ("thousand_seed_weight_g", "Thousand-seed weight (g)"),
    ("plant_height_cm", "Plant height (cm)"),
    ("seed_protein_pct", "Seed protein (% dry matter)"),
    ("chocolate_spot_severity_pct", "Chocolate spot severity (% leaf area)"),
]


def format_p(value):
    """Show small p-values in scientific notation so they are not printed as 0."""
    value = float(value)
    if value < 1e-4:
        return f"{value:.4e}"
    return f"{value:.6f}"


def main():
    data = pd.read_csv(DATA_FILE)

    group_a = data[data[GROUP_COLUMN] == GROUP_A]
    group_b = data[data[GROUP_COLUMN] == GROUP_B]

    rows = []
    raw_pvalues = []

    for column, label in OUTCOMES:
        values_a = group_a[column]
        values_b = group_b[column]

        result = pg.ttest(values_a, values_b, paired=False)
        p_raw = float(result["p-val"].iloc[0])

        rows.append(
            {
                "column": column,
                "label": label,
                "n_a": int(values_a.size),
                "n_b": int(values_b.size),
                "mean_a": float(values_a.mean()),
                "sd_a": float(values_a.std(ddof=1)),
                "mean_b": float(values_b.mean()),
                "sd_b": float(values_b.std(ddof=1)),
                "p_raw": p_raw,
            }
        )
        raw_pvalues.append(p_raw)

    # Complete-family control: all six declared p-values adjusted together.
    reject, p_adjusted = pg.multicomp(raw_pvalues, alpha=ALPHA, method=ADJUST_METHOD)

    print("Faba bean sowing-time trial: autumn vs spring")
    print(f"Data file: {DATA_FILE}")
    print(f"Groups compared: {GROUP_A} vs {GROUP_B}")
    print("Test per outcome: independent two-sample t-test")
    print(
        f"Family-wise control: pingouin.multicomp, method='{ADJUST_METHOD}', "
        f"alpha={ALPHA}, applied to all {len(OUTCOMES)} declared outcomes together"
    )
    print("Verdicts are taken from the adjusted values, never from the raw p-values.")
    print()

    for row, p_adj, is_rejected in zip(rows, p_adjusted, reject):
        verdict = (
            "significant after family-wise adjustment"
            if bool(is_rejected)
            else "not significant after family-wise adjustment"
        )
        print(f"{row['label']}  [{row['column']}]")
        print(
            f"  {GROUP_A:>6}: n = {row['n_a']:d}, "
            f"mean = {row['mean_a']:.3f}, sd = {row['sd_a']:.3f}"
        )
        print(
            f"  {GROUP_B:>6}: n = {row['n_b']:d}, "
            f"mean = {row['mean_b']:.3f}, sd = {row['sd_b']:.3f}"
        )
        print(f"  raw p-value      = {format_p(row['p_raw'])}")
        print(f"  adjusted value   = {format_p(p_adj)}")
        print(f"  verdict          = {verdict}")
        print()

    n_significant = int(sum(bool(x) for x in reject))
    print(
        f"{n_significant} of {len(OUTCOMES)} declared outcomes are significant "
        f"at the {ALPHA} family-wise level."
    )


if __name__ == "__main__":
    main()
