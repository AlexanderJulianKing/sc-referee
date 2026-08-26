"""Burned versus unburned giant hairy scorpions: per-outcome two-group comparison.

Reads ``scorpions.csv`` and compares the burned and unburned animals on each of the
three outcomes declared by the field protocol, in the declared order:

1. ``body_mass_g``                body mass, grams
2. ``haemolymph_protein_g_l``     haemolymph total protein, grams per litre
3. ``metabolic_rate_ml_o2_h``     resting metabolic rate, millilitres of oxygen per hour

Each outcome was declared as a question in its own right, so each is tested separately
against the conventional five percent threshold. No multiple-comparison adjustment of
any kind is applied.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "scorpions.csv"

GROUP_COLUMN = "group"
BURNED = "burned"
UNBURNED = "unburned"

ALPHA = 0.05

# The three outcomes in the order the field protocol declared them, with the label
# and unit used when reporting each one.
DECLARED_OUTCOMES = [
    ("body_mass_g", "Body mass", "g"),
    ("haemolymph_protein_g_l", "Haemolymph total protein", "g/L"),
    ("metabolic_rate_ml_o2_h", "Resting metabolic rate", "mL O2/h"),
]


def compare_outcomes(data, declared_outcomes):
    """Run the two-group comparison for every declared outcome.

    Takes the full table and the declared outcome list, and hands back the collected
    per-outcome results in the declared order. Each result is a dict holding the
    column, label, unit, the two site means, the burned-minus-unburned difference,
    the t statistic, the p-value and the five percent verdict.

    The comparison is Welch's two-sample t-test on the individual animal values
    (two-sided, unequal variances not assumed to be equal). Each outcome is tested
    on its own at ALPHA; no multiple-comparison correction is applied.
    """
    results = []
    for column, label, unit in declared_outcomes:
        burned_values = data.loc[data[GROUP_COLUMN] == BURNED, column]
        unburned_values = data.loc[data[GROUP_COLUMN] == UNBURNED, column]

        t_statistic, p_value = stats.ttest_ind(
            burned_values, unburned_values, equal_var=False
        )

        burned_mean = float(burned_values.mean())
        unburned_mean = float(unburned_values.mean())

        results.append(
            {
                "column": column,
                "label": label,
                "unit": unit,
                "n_burned": int(burned_values.size),
                "n_unburned": int(unburned_values.size),
                "burned_mean": burned_mean,
                "unburned_mean": unburned_mean,
                "difference": burned_mean - unburned_mean,
                "t_statistic": float(t_statistic),
                "p_value": float(p_value),
                "significant": bool(p_value < ALPHA),
            }
        )
    return results


def main():
    data = pd.read_csv(DATA_FILE)

    results = compare_outcomes(data, DECLARED_OUTCOMES)

    print("Burned versus unburned giant hairy scorpions")
    print(f"n = {len(data)} animals "
          f"({int((data[GROUP_COLUMN] == BURNED).sum())} burned, "
          f"{int((data[GROUP_COLUMN] == UNBURNED).sum())} unburned)")
    print("Welch's two-sample t-test on individual animals, two-sided.")
    print(f"Each declared outcome tested separately at alpha = {ALPHA:g}; "
          "no multiple-comparison adjustment.")
    print()

    for position, result in enumerate(results, start=1):
        verdict = "SIGNIFICANT" if result["significant"] else "not significant"
        print(f"{position}. {result['label']} ({result['unit']}) "
              f"[{result['column']}]")
        print(f"   burned mean    = {result['burned_mean']:.3f} {result['unit']} "
              f"(n = {result['n_burned']})")
        print(f"   unburned mean  = {result['unburned_mean']:.3f} {result['unit']} "
              f"(n = {result['n_unburned']})")
        print(f"   difference     = {result['difference']:+.3f} {result['unit']} "
              "(burned minus unburned)")
        print(f"   t              = {result['t_statistic']:.3f}")
        print(f"   p              = {result['p_value']:.4f}")
        print(f"   verdict        = {verdict} at the {ALPHA:g} threshold")
        print()


if __name__ == "__main__":
    main()
