"""Analysis of the twelve week ultraviolet B lamp trial in juvenile bearded dragons.

Reads the fixed data file `data.csv`, summarises the two lamp groups on each of
the five pre-declared outcomes, and compares the groups on each outcome with one
two-sample significance test per outcome.

The script never generates, simulates, or writes the data file.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "data.csv"

GROUP_COLUMN = "lamp_type"
GROUP_LABELS = ("cfl", "t5_ho")
GROUP_TITLES = {"cfl": "compact fluorescent (cfl)", "t5_ho": "linear T5 high output (t5_ho)"}

# The pre-declared outcome family, in the fixed order given in the trial protocol.
# Each entry is (column name, human readable label, unit, decimal places for reporting).
OUTCOMES = [
    ("plasma_25ohd3_nmol_l", "Plasma 25-hydroxyvitamin D3", "nmol/L", 1),
    ("plasma_ionised_calcium_mmol_l", "Plasma ionised calcium", "mmol/L", 3),
    ("body_mass_gain_g", "Body mass gain over twelve weeks", "g", 1),
    ("snout_vent_length_gain_mm", "Snout to vent length gain over twelve weeks", "mm", 1),
    ("humeral_cortical_thickness_ratio", "Humeral cortical thickness ratio", "ratio", 3),
]

# Per-outcome significance threshold fixed in advance by the trial protocol.
# The script treats this value as given and applies it as it stands.
PROTOCOL_ALPHA = 0.01


def load_data(path):
    """Read the fixed data file and check the columns the analysis needs."""
    frame = pd.read_csv(path)
    required = [GROUP_COLUMN] + [column for column, _, _, _ in OUTCOMES]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError("data.csv is missing required columns: " + ", ".join(missing))
    observed_labels = tuple(sorted(frame[GROUP_COLUMN].unique()))
    if observed_labels != tuple(sorted(GROUP_LABELS)):
        raise ValueError("Unexpected lamp group labels in data.csv: " + str(observed_labels))
    return frame


def report_group_sizes(frame):
    print("Group sizes")
    print("-" * 60)
    print("Animals in data.csv: {}".format(len(frame)))
    for label in GROUP_LABELS:
        print("  {:<30} n = {}".format(GROUP_TITLES[label], int((frame[GROUP_COLUMN] == label).sum())))
    print()


def report_group_summaries(frame):
    print("Per-group summary values for each declared outcome")
    print("-" * 60)
    for column, label, unit, places in OUTCOMES:
        print("{} ({})".format(label, unit))
        print("  column: {}".format(column))
        for group in GROUP_LABELS:
            values = frame.loc[frame[GROUP_COLUMN] == group, column]
            print(
                "    {:<30} n = {:>2}  mean = {:.{p}f}  sd = {:.{p}f}  min = {:.{p}f}  median = {:.{p}f}  max = {:.{p}f}".format(
                    GROUP_TITLES[group],
                    int(values.count()),
                    values.mean(),
                    values.std(ddof=1),
                    values.min(),
                    values.median(),
                    values.max(),
                    p=places,
                )
            )
        print()


def compare_groups(frame):
    """One two-sample Welch t-test per declared outcome, judged against the protocol threshold."""
    print("Two-sample comparison of the lamp groups, one test per declared outcome")
    print("-" * 60)
    print("Test: Welch two-sample t-test (two sided, unequal variances not assumed equal)")
    print("Per-outcome significance threshold fixed by the protocol: {}".format(PROTOCOL_ALPHA))
    print()

    results = []
    for column, label, unit, places in OUTCOMES:
        cfl_values = frame.loc[frame[GROUP_COLUMN] == "cfl", column]
        t5_values = frame.loc[frame[GROUP_COLUMN] == "t5_ho", column]
        statistic, p_value = stats.ttest_ind(t5_values, cfl_values, equal_var=False)
        difference = t5_values.mean() - cfl_values.mean()
        significant = p_value < PROTOCOL_ALPHA
        verdict = (
            "significant at the protocol threshold of {}".format(PROTOCOL_ALPHA)
            if significant
            else "not significant at the protocol threshold of {}".format(PROTOCOL_ALPHA)
        )

        print("{} ({})".format(label, unit))
        print("  column: {}".format(column))
        print(
            "  mean t5_ho = {:.{p}f}   mean cfl = {:.{p}f}   difference (t5_ho minus cfl) = {:.{p}f} {}".format(
                t5_values.mean(), cfl_values.mean(), difference, unit, p=places
            )
        )
        print("  Welch t = {:.3f}   p = {:.5f}".format(statistic, p_value))
        print("  verdict: {}".format(verdict))
        print()

        results.append(
            {
                "column": column,
                "label": label,
                "unit": unit,
                "mean_t5_ho": t5_values.mean(),
                "mean_cfl": cfl_values.mean(),
                "difference": difference,
                "t": statistic,
                "p": p_value,
                "significant": significant,
            }
        )
    return results


def report_verdict_table(results):
    print("Verdict summary, declared outcome order")
    print("-" * 60)
    print("{:<36} {:>10}  {}".format("outcome", "p", "verdict vs {}".format(PROTOCOL_ALPHA)))
    for result in results:
        print(
            "{:<36} {:>10.5f}  {}".format(
                result["column"],
                result["p"],
                "significant" if result["significant"] else "not significant",
            )
        )
    print()
    significant = [r["column"] for r in results if r["significant"]]
    print(
        "Outcomes reaching the protocol threshold of {}: {}".format(
            PROTOCOL_ALPHA, ", ".join(significant) if significant else "none"
        )
    )


def main():
    frame = load_data(DATA_FILE)
    print("Ultraviolet B lamp trial in juvenile bearded dragons")
    print("Source data file: {}".format(DATA_FILE.name))
    print()
    report_group_sizes(frame)
    report_group_summaries(frame)
    results = compare_groups(frame)
    report_verdict_table(results)


if __name__ == "__main__":
    main()
