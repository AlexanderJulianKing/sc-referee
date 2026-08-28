"""Pasta drying temperature study: analysis of the declared outcome family.

Reads the fixed data file data.csv and compares the low temperature (LT) and very
high temperature (VHT) drying cycles on the five pre-declared outcomes.

The study plan fixed a gatekeeping rule that controls the family error rate: a
single overall separation number is computed first from all five outcome columns,
and the per-outcome comparisons are run only if that number reaches the
pre-specified cutoff of 0.40.
"""

import os

import numpy as np
import pandas as pd
from scipy import stats

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.csv")

GROUP_COLUMN = "drying_cycle"
GROUP_LABELS = ("LT", "VHT")

# The declared outcome family, in the order fixed by the study plan.
OUTCOMES = [
    ("cooking_loss_pct", "Cooking loss (% of dry weight)"),
    ("optimal_cooking_time_min", "Optimal cooking time (min)"),
    ("firmness_n", "Firmness (N)"),
    ("colour_b_star", "Colour b* (colour scale value)"),
    ("furosine_mg_100g_protein", "Furosine (mg/100 g protein)"),
]

SCREENING_CUTOFF = 0.40
ALPHA = 0.05


def load_data():
    """Read the fixed data file. This script never writes or regenerates it."""
    return pd.read_csv(DATA_FILE)


def report_group_sizes(data):
    print("GROUP SIZES")
    print("-" * 70)
    for label in GROUP_LABELS:
        print("  {:<4s} lots: {:d}".format(label, int((data[GROUP_COLUMN] == label).sum())))
    print("  total lots: {:d}".format(len(data)))
    print()


def report_group_summaries(data):
    print("PER-GROUP SUMMARY VALUES BY DECLARED OUTCOME")
    print("-" * 70)
    header = "{:<32s} {:>6s} {:>9s} {:>9s} {:>9s}".format(
        "outcome / group", "n", "mean", "sd", "median"
    )
    print(header)
    for column, description in OUTCOMES:
        print("{:s}  [{:s}]".format(description, column))
        for label in GROUP_LABELS:
            values = data.loc[data[GROUP_COLUMN] == label, column]
            print(
                "{:<32s} {:>6d} {:>9.3f} {:>9.3f} {:>9.3f}".format(
                    "    " + label,
                    int(values.size),
                    float(values.mean()),
                    float(values.std(ddof=1)),
                    float(values.median()),
                )
            )
    print()


def screening_number(data):
    """Overall separation number for the whole declared outcome family.

    Plain arithmetic on the five outcome columns only: no statistical test
    routine of any kind is involved in this step.

    Each outcome column is put on a common scale by subtracting its overall mean
    and dividing by its overall spread. For each outcome, the mean of the
    rescaled values is taken within each drying cycle, and the size of the
    difference between the two cycle means is recorded. The five differences are
    combined into one overall separation number by averaging them.
    """
    per_outcome_differences = []

    print("SCREENING STEP (gatekeeper for the whole outcome family)")
    print("-" * 70)
    print("Each outcome column is centred on its overall mean and divided by its")
    print("overall spread (standard deviation). The absolute difference between the")
    print("two cycle means of the rescaled values is then averaged over the five")
    print("outcomes to give one overall separation number.")
    print()
    print("{:<32s} {:>12s} {:>12s} {:>12s}".format(
        "outcome", "LT mean(z)", "VHT mean(z)", "|difference|"
    ))

    for column, _description in OUTCOMES:
        values = data[column].to_numpy(dtype=float)
        rescaled = (values - values.mean()) / values.std(ddof=1)
        group_means = []
        for label in GROUP_LABELS:
            mask = (data[GROUP_COLUMN] == label).to_numpy()
            group_means.append(float(np.mean(rescaled[mask])))
        difference = abs(group_means[0] - group_means[1])
        per_outcome_differences.append(difference)
        print("{:<32s} {:>12.4f} {:>12.4f} {:>12.4f}".format(
            column, group_means[0], group_means[1], difference
        ))

    overall = float(np.mean(per_outcome_differences))
    print()
    print("Overall separation number = mean of the five absolute differences = {:.4f}".format(overall))
    print("Pre-specified screening cutoff = {:.2f}".format(SCREENING_CUTOFF))
    print()
    return overall


def run_per_outcome_tests(data):
    """Branch taken when the family passes the screen."""
    print("BRANCH: SCREEN PASSED -- per-outcome comparisons were run")
    print("-" * 70)
    print("One two-sample Welch t test per declared outcome, LT versus VHT,")
    print("with verdicts at the conventional 0.05 threshold.")
    print()
    print("{:<32s} {:>10s} {:>10s} {:>10s} {:>9s} {:>12s}  {:s}".format(
        "outcome", "LT mean", "VHT mean", "difference", "t", "p value", "verdict"
    ))

    for column, _description in OUTCOMES:
        lt_values = data.loc[data[GROUP_COLUMN] == "LT", column].to_numpy(dtype=float)
        vht_values = data.loc[data[GROUP_COLUMN] == "VHT", column].to_numpy(dtype=float)
        t_statistic, p_value = stats.ttest_ind(lt_values, vht_values, equal_var=False)
        verdict = "significant" if p_value < ALPHA else "not significant"
        print("{:<32s} {:>10.3f} {:>10.3f} {:>10.3f} {:>9.3f} {:>12.6f}  {:s}".format(
            column,
            float(lt_values.mean()),
            float(vht_values.mean()),
            float(lt_values.mean() - vht_values.mean()),
            float(t_statistic),
            float(p_value),
            verdict,
        ))
    print()


def report_screen_failure(overall):
    """Branch taken when the family fails the screen."""
    print("BRANCH: SCREEN FAILED -- no per-outcome comparison was run")
    print("-" * 70)
    print("The overall separation number {:.4f} is below the pre-specified cutoff".format(overall))
    print("of {:.2f}, so the declared outcome family did not pass the gate.".format(SCREENING_CUTOFF))
    print("No per-outcome test was run and no per-outcome result is reported.")
    print()


def main():
    data = load_data()

    print("=" * 70)
    print("PASTA DRYING TEMPERATURE STUDY")
    print("Low temperature (LT, 55 C peak) versus very high temperature (VHT, 90 C peak)")
    print("=" * 70)
    print()

    report_group_sizes(data)
    report_group_summaries(data)

    overall = screening_number(data)

    if overall >= SCREENING_CUTOFF:
        run_per_outcome_tests(data)
    else:
        report_screen_failure(overall)

    print("=" * 70)


if __name__ == "__main__":
    main()
