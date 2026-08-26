"""Guinea pig hay presentation feeding study: per-outcome analysis.

One row of guinea_pig_hay_study.csv is one guinea pig. Each of the six
protocol outcomes is a declared question in its own right, so each one gets
its own two-group comparison between the hay rack group and the forage block
group, and its own conclusion at the conventional five percent threshold.
No multiple-comparison adjustment is applied.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "guinea_pig_hay_study.csv"

GROUP_COLUMN = "group"
RACK = "hay_rack"
BLOCK = "forage_block"

ALPHA = 0.05

# The six outcomes in the order the protocol declared them.
OUTCOMES = [
    ("hay_intake_g_day", "Daily hay dry matter intake", "g/day"),
    ("body_weight_g", "End-of-study body weight", "g"),
    ("faecal_output_g_day", "Daily faecal output", "g/day"),
    ("faecal_particle_mm", "Median faecal particle size", "mm"),
    ("chewing_min_day", "Time spent chewing per day", "min/day"),
    ("occlusal_angle_deg", "Cheek tooth occlusal angle", "deg"),
]


def compare(rack_values, block_values):
    """Two-sample (Welch) t-test comparing the two feeding treatments."""
    return stats.ttest_ind(rack_values, block_values, equal_var=False)


def main():
    data = pd.read_csv(DATA_FILE)

    rack = data[data[GROUP_COLUMN] == RACK]
    block = data[data[GROUP_COLUMN] == BLOCK]

    # Single compact collection of per-outcome results, built in one pass over
    # the declared outcome list.
    results = [
        {
            "column": column,
            "label": label,
            "unit": unit,
            "n_rack": int(rack[column].count()),
            "n_block": int(block[column].count()),
            "mean_rack": float(rack[column].mean()),
            "mean_block": float(block[column].mean()),
            "difference": float(rack[column].mean() - block[column].mean()),
            "p_value": float(compare(rack[column], block[column]).pvalue),
        }
        for column, label, unit in OUTCOMES
    ]

    print(f"Guinea pig hay presentation study: {len(data)} animals "
          f"({len(rack)} {RACK}, {len(block)} {BLOCK})")
    print(f"Welch two-sample t-test per declared outcome, alpha = {ALPHA}, "
          "no multiple-comparison adjustment.\n")

    header = (f"{'Outcome':<30} {'Unit':<8} {'Mean rack':>10} "
              f"{'Mean block':>11} {'Difference':>11} {'p-value':>9}  Result")
    print(header)
    print("-" * len(header))

    for result in results:
        verdict = ("significant" if result["p_value"] < ALPHA
                   else "not significant")
        print(f"{result['label']:<30} {result['unit']:<8} "
              f"{result['mean_rack']:>10.2f} {result['mean_block']:>11.2f} "
              f"{result['difference']:>11.2f} {result['p_value']:>9.4f}  "
              f"{verdict}")

    return results


if __name__ == "__main__":
    main()
