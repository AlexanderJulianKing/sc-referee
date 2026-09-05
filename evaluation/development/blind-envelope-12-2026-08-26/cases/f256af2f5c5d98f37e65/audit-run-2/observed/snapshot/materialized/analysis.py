"""Permeable paving runoff monitoring: analysis of the four declared outcomes.

One municipal car park, 36 parking bays (18 conventional dense asphalt, 18 permeable
concrete block paving over a gravel reservoir), each bay draining to its own collection
sump and sampled once after a single heavy summer storm. The bay is the unit of the
study.

The monitoring plan declared one family of four outcomes, in this fixed order:

    1. tss_mg_l        total suspended solids            mg/L
    2. zinc_ug_l       total zinc                        ug/L
    3. peak_volume_l   peak runoff volume                L
    4. runoff_temp_c   runoff temperature at peak flow   degrees C

The family-wise error rate is held at five percent by judging each outcome against the
Sidak per-comparison threshold, computed explicitly below from the family size.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "runoff_bays.csv"

GROUP_COLUMN = "group"
ASPHALT = "asphalt"
PERMEABLE = "permeable"

# The four outcomes of the declared family, in the declared monitoring order.
DECLARED_OUTCOMES = [
    ("tss_mg_l", "Total suspended solids", "mg/L"),
    ("zinc_ug_l", "Total zinc", "ug/L"),
    ("peak_volume_l", "Peak runoff volume", "L"),
    ("runoff_temp_c", "Runoff temperature at peak flow", "deg C"),
]

# Family-wise error rate the authority asked for.
FAMILY_WISE_ALPHA = 0.05

# Family size: the number of outcomes in the one declared family.
FAMILY_SIZE = len(DECLARED_OUTCOMES)


def sidak_threshold(family_wise_alpha: float, family_size: int) -> float:
    """Per-comparison threshold from the Sidak relation.

    alpha_per_comparison = 1 - (1 - alpha_family_wise) ** (1 / family_size)

    That is one minus the family-size root of one minus the family-wise level. Judging
    every member of the family against this value holds the chance of at least one false
    claim anywhere in the family at alpha_family_wise, provided the tests are independent.
    """
    return 1.0 - (1.0 - family_wise_alpha) ** (1.0 / family_size)


def main() -> None:
    data = pd.read_csv(DATA_FILE)

    asphalt = data[data[GROUP_COLUMN] == ASPHALT]
    permeable = data[data[GROUP_COLUMN] == PERMEABLE]

    alpha_pc = sidak_threshold(FAMILY_WISE_ALPHA, FAMILY_SIZE)

    print("Permeable paving runoff monitoring")
    print("=" * 78)
    print(f"Data file                      : {DATA_FILE.name}")
    print(f"Bays (rows)                    : {len(data)}")
    print(f"  asphalt bays                 : {len(asphalt)}")
    print(f"  permeable bays               : {len(permeable)}")
    print(f"Missing values in the table    : {int(data.isna().sum().sum())}")
    print()
    print("Multiplicity control (Sidak, computed here from the family size)")
    print("-" * 78)
    print(f"  family-wise level  alpha_fw  = {FAMILY_WISE_ALPHA:.4f}")
    print(f"  family size        m         = {FAMILY_SIZE}")
    print(f"  alpha_pc = 1 - (1 - {FAMILY_WISE_ALPHA:g}) ** (1 / {FAMILY_SIZE})"
          f" = {alpha_pc:.6f}")
    print("  Every declared outcome is judged against alpha_pc, not against 0.05.")
    print()

    print("Declared family, in declared order")
    print("-" * 78)
    header = (
        f"{'#':>2}  {'outcome':<14} {'unit':<6} {'mean asphalt':>13}"
        f" {'mean permeable':>15} {'p-value':>10} {'threshold':>10}  verdict"
    )
    print(header)

    rows = []
    for position, (column, label, unit) in enumerate(DECLARED_OUTCOMES, start=1):
        asphalt_values = asphalt[column]
        permeable_values = permeable[column]

        mean_asphalt = asphalt_values.mean()
        mean_permeable = permeable_values.mean()

        # Standard two-group comparison of the bay values: two-sample t-test,
        # Welch form (does not assume the two surfaces share a variance).
        result = stats.ttest_ind(asphalt_values, permeable_values, equal_var=False)
        p_value = float(result.pvalue)

        significant = p_value < alpha_pc
        verdict = "significant" if significant else "not significant"

        print(
            f"{position:>2}  {column:<14} {unit:<6} {mean_asphalt:>13.2f}"
            f" {mean_permeable:>15.2f} {p_value:>10.3g} {alpha_pc:>10.6f}"
            f"  {verdict}"
        )

        rows.append(
            {
                "order": position,
                "outcome": column,
                "label": label,
                "unit": unit,
                "n_asphalt": int(asphalt_values.count()),
                "n_permeable": int(permeable_values.count()),
                "mean_asphalt": mean_asphalt,
                "mean_permeable": mean_permeable,
                "difference_permeable_minus_asphalt": mean_permeable - mean_asphalt,
                "t_statistic": float(result.statistic),
                "p_value": p_value,
                "sidak_threshold": alpha_pc,
                "verdict": verdict,
            }
        )

    print()
    print("Detail")
    print("-" * 78)
    detail = pd.DataFrame(rows)
    with pd.option_context("display.width", 200, "display.max_columns", 50):
        print(detail.to_string(index=False))


if __name__ == "__main__":
    main()
