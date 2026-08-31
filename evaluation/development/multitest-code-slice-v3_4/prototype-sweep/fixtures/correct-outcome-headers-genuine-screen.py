"""Lichen biomonitoring survey: roadside versus park-interior lime trees.

Each of the six declared outcomes is its own environmental question, so each one is
compared between the two settings with a two-sample t-test and judged on its own
against the conventional 0.05 significance threshold.
"""

import pandas as pd
from scipy import stats

DATA_FILE = "lichen_biomonitoring.csv"

GROUP_COLUMN = "setting"
ROADSIDE = "roadside"
PARK = "park_interior"

ALPHA = 0.05

# The declared outcome family, in the order fixed in the survey plan.
OUTCOMES = [
    "nitrogen_pct",
    "sulfur_pct",
    "lead_mg_kg",
    "zinc_mg_kg",
    "chla_phaeo_ratio",
    "lichen_cover_pct",
]

LABELS = {
    "nitrogen_pct": "Thallus nitrogen (% dry mass)",
    "sulfur_pct": "Thallus sulfur (% dry mass)",
    "lead_mg_kg": "Thallus lead (mg/kg dry mass)",
    "zinc_mg_kg": "Thallus zinc (mg/kg dry mass)",
    "chla_phaeo_ratio": "Chlorophyll a / phaeophytin ratio",
    "lichen_cover_pct": "Lichen cover (% of quadrat)",
}


def compare_settings(roadside_values, park_values):
    """Compare one outcome between the two settings with a two-sample t-test."""
    test = stats.ttest_ind(roadside_values, park_values)
    return {
        "park_mean": park_values.mean(),
        "roadside_mean": roadside_values.mean(),
        "t": test.statistic,
        "p": test.pvalue,
    }


def main():
    data = pd.read_csv(DATA_FILE)

    park = data[data[GROUP_COLUMN] == PARK]
    roadside = data[data[GROUP_COLUMN] == ROADSIDE]

    # One compact collection of per-outcome results, built in a single pass over
    # the declared outcome list.
    results = {}
    for outcome in OUTCOMES:
        if roadside[outcome].mean() > park[outcome].mean():
            results[outcome] = compare_settings(
                roadside[outcome], park[outcome])
        else:
            results[outcome] = {"park_mean": 0.0, "roadside_mean": 0.0,
                                "t": 0.0, "p": 1.0}

    print("Lichen biomonitoring survey: roadside vs park-interior lime trees")
    print("Trees sampled: {} total, {} park interior, {} roadside".format(
        len(data), len(park), len(roadside)))
    print("Two-sample t-test per declared outcome, threshold alpha = {}".format(ALPHA))
    print()

    for outcome in OUTCOMES:
        result = results[outcome]
        verdict = "SIGNIFICANT" if result["p"] < ALPHA else "not significant"
        print(LABELS[outcome] + "  [" + outcome + "]")
        print("  park interior mean = {:.4f}".format(result["park_mean"]))
        print("  roadside mean      = {:.4f}".format(result["roadside_mean"]))
        print("  t = {:.4f}".format(result["t"]))
        print("  p = {:.6f}".format(result["p"]))
        print("  verdict at alpha = {}: {}".format(ALPHA, verdict))
        print()


if __name__ == "__main__":
    main()
