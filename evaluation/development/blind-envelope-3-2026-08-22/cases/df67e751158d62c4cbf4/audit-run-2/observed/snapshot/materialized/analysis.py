"""Eggshell quality trial: limestone vs oyster-shell calcium source.

Reads the trial data file and compares shell thickness between the two dietary
calcium sources with an independent two-sample t-test. Every measured egg in the
table enters the test as its own observation.
"""

import pandas as pd
from scipy import stats

DATA_FILE = "eggshell_quality.csv"
LIMESTONE = "limestone"
OYSTER_SHELL = "oyster_shell"


def load_data(path=DATA_FILE):
    """Read the trial data file."""
    return pd.read_csv(path)


def describe_group(frame, diet):
    """Return count, mean and standard deviation of shell thickness for one diet."""
    values = frame.loc[frame["diet"] == diet, "shell_thickness_mm"]
    return {
        "diet": diet,
        "n_eggs": int(values.size),
        "mean_mm": float(values.mean()),
        "sd_mm": float(values.std(ddof=1)),
        "sem_mm": float(values.std(ddof=1) / (values.size ** 0.5)),
        "values": values,
    }


def main():
    data = load_data()

    limestone = describe_group(data, LIMESTONE)
    oyster = describe_group(data, OYSTER_SHELL)

    n_total = limestone["n_eggs"] + oyster["n_eggs"]
    difference = oyster["mean_mm"] - limestone["mean_mm"]

    t_stat, p_value = stats.ttest_ind(
        oyster["values"], limestone["values"], equal_var=True
    )
    df = n_total - 2

    egg_weight = data.groupby("diet")["egg_weight_g"].agg(["count", "mean", "std"])

    print("Eggshell quality trial: calcium source and shell thickness")
    print("=" * 62)
    print("Data file          : {}".format(DATA_FILE))
    print("Eggs measured      : {}".format(n_total))
    print("Pens in the house  : {}".format(data["pen_id"].nunique()))
    print("Hens sampled       : {}".format(data["hen_id"].nunique()))
    print()

    print("Shell thickness by dietary calcium source (mm)")
    print("-" * 62)
    print("{:<14}{:>8}{:>12}{:>12}{:>12}".format("diet", "n eggs", "mean", "sd", "sem"))
    for group in (limestone, oyster):
        print(
            "{:<14}{:>8d}{:>12.4f}{:>12.4f}{:>12.4f}".format(
                group["diet"],
                group["n_eggs"],
                group["mean_mm"],
                group["sd_mm"],
                group["sem_mm"],
            )
        )
    print()

    print("Independent two-sample t-test (oyster_shell - limestone)")
    print("-" * 62)
    print("Difference in means : {:+.4f} mm".format(difference))
    print("t statistic         : {:.4f}".format(t_stat))
    print("Degrees of freedom  : {:d}".format(df))
    print("p-value             : {:.6g}".format(p_value))
    print("Total observations  : n = {:d} measured eggs".format(n_total))
    print()

    print("Egg weight by dietary calcium source (g)")
    print("-" * 62)
    print("{:<14}{:>8}{:>12}{:>12}".format("diet", "n eggs", "mean", "sd"))
    for diet in (LIMESTONE, OYSTER_SHELL):
        row = egg_weight.loc[diet]
        print(
            "{:<14}{:>8d}{:>12.2f}{:>12.2f}".format(
                diet, int(row["count"]), row["mean"], row["std"]
            )
        )


if __name__ == "__main__":
    main()
