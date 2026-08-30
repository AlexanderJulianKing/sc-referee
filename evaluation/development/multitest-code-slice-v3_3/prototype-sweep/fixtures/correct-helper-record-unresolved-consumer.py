"""Green roof survey: substrate depth comparison across the five declared outcomes.

Compares shallow-substrate roofs (about 60 mm) with deep-substrate roofs (about
120 mm) on each of the five pre-declared outcome variables, using a two-sample
Student's t-test for independent groups and the conventional 0.05 threshold.
"""

import pandas as pd
from scipy import stats

DATA_FILE = "green_roof_survey.csv"
GROUP_COLUMN = "substrate_depth"
SHALLOW = "shallow"
DEEP = "deep"
ALPHA = 0.05

# The outcome family exactly as declared in advance, in the declared order.
OUTCOMES = [
    "plant_richness_count",
    "veg_cover_pct",
    "substrate_moisture_pct",
    "temp_reduction_c",
    "invert_abundance_count",
]


def compare(frame, outcome):
    """Two-sample t-test for one outcome, shallow versus deep roofs."""
    shallow = frame.loc[frame[GROUP_COLUMN] == SHALLOW, outcome]
    deep = frame.loc[frame[GROUP_COLUMN] == DEEP, outcome]
    t_statistic, p_value = stats.ttest_ind(shallow, deep)
    return {
        "n_shallow": int(shallow.size),
        "n_deep": int(deep.size),
        "mean_shallow": float(shallow.mean()),
        "mean_deep": float(deep.mean()),
        "difference": float(deep.mean() - shallow.mean()),
        "t_statistic": float(t_statistic),
        "p_value": float(p_value),
        "significant": bool(p_value < ALPHA),
    }


def inspect(value):
    return value

def main():
    data = pd.read_csv(DATA_FILE)

    # Every per-outcome number gathered into one collection in a single pass
    # over the declared outcome list.
    results = {outcome: compare(data, outcome) for outcome in OUTCOMES}

    print(f"Green roof survey: {len(data)} roofs, "
          f"{GROUP_COLUMN} groups compared at alpha = {ALPHA}")
    print()

    for outcome, result in results.items():
        inspect(result["p_value"])
        verdict = "SIGNIFICANT" if result["significant"] else "not significant"
        print(f"{outcome}")
        print(f"  mean ({SHALLOW}, n={result['n_shallow']}) = "
              f"{result['mean_shallow']:.3f}")
        print(f"  mean ({DEEP}, n={result['n_deep']})    = "
              f"{result['mean_deep']:.3f}")
        print(f"  difference (deep - shallow) = {result['difference']:.3f}")
        print(f"  t = {result['t_statistic']:.4f}")
        print(f"  p = {result['p_value']:.6f}")
        print(f"  verdict: {verdict} at {ALPHA}")
        print()


if __name__ == "__main__":
    main()
