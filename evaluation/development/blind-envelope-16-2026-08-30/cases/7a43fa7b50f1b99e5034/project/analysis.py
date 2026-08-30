"""Brooder flooring trial in Japanese quail chicks: mesh vs straw litter.

Compares the two flooring groups on each of the six pre-declared outcomes with a
two-sample t-test, and calls each outcome significant or not at alpha = 0.05.
"""

import pandas as pd
from scipy import stats

DATA_FILE = "quail_flooring.csv"
GROUP_COLUMN = "floor_type"
GROUP_A = "mesh"
GROUP_B = "straw"
ALPHA = 0.05

# The six outcomes in the order the trial declared them in advance.
OUTCOMES = [
    ("body_weight_g", "Body weight (g)"),
    ("feed_intake_g_d", "Average daily feed intake (g/day)"),
    ("footpad_score_pts", "Foot-pad lesion score (points)"),
    ("tibia_strength_n", "Tibia breaking strength (N)"),
    ("corticosterone_ng_ml", "Plasma corticosterone (ng/mL)"),
    ("tonic_immobility_s", "Tonic immobility (s)"),
]


def main():
    data = pd.read_csv(DATA_FILE)

    mesh = data[data[GROUP_COLUMN] == GROUP_A]
    straw = data[data[GROUP_COLUMN] == GROUP_B]

    print("Brooder flooring trial: plastic mesh vs chopped straw litter")
    print("Chicks on {}: {}    chicks on {}: {}".format(
        GROUP_A, len(mesh), GROUP_B, len(straw)))
    print("Significance threshold: alpha = {}".format(ALPHA))
    print()

    header = "{:<34} {:>10} {:>10} {:>10} {:>10}  {}".format(
        "Outcome", "mesh mean", "straw mean", "t", "p", "verdict")
    print(header)
    print("-" * len(header))

    results = []
    for column, label in OUTCOMES:
        mesh_values = mesh[column]
        straw_values = straw[column]

        t_statistic, p_value = stats.ttest_ind(mesh_values, straw_values)

        mesh_mean = mesh_values.mean()
        straw_mean = straw_values.mean()
        significant = p_value < ALPHA
        verdict = "significant" if significant else "not significant"

        results.append({
            "column": column,
            "label": label,
            "mesh_mean": mesh_mean,
            "straw_mean": straw_mean,
            "t": t_statistic,
            "p": p_value,
            "verdict": verdict,
        })

        print("{:<34} {:>10.2f} {:>10.2f} {:>10.3f} {:>10.4f}  {}".format(
            label, mesh_mean, straw_mean, t_statistic, p_value, verdict))

    print()
    significant_count = sum(1 for r in results if r["verdict"] == "significant")
    print("Significant at alpha = {}: {} of {} declared outcomes.".format(
        ALPHA, significant_count, len(results)))

    return results


if __name__ == "__main__":
    main()
