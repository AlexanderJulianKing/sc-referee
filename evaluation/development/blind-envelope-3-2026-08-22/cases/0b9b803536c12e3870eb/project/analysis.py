"""Compare maximal handgrip strength between two eight-week training programmes.

The data file `grip_strength.csv` holds one row per handgrip trial: each of the
26 volunteers performed four maximal trials in a single testing session, so the
file contains 104 rows. The four trials of one volunteer are repeated measures on
the same person, not four independent observations, and the volunteer is the unit
that was assigned to a training programme.

This script therefore reduces the data before testing anything: each volunteer is
collapsed to the mean of their own four trials, giving one value per volunteer.
The two programmes are then compared with an independent two-sample t-test on
those per-volunteer means, so the sample size entering the test is the number of
volunteers per group (13 and 13), not the number of trials.

Run with:  python3 analysis.py
"""

import os

import pandas as pd
from scipy import stats

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "grip_strength.csv")

OUTCOME = "peak_force_kg"
GROUP_COL = "programme"
UNIT_COL = "volunteer_id"
GROUPS = ("heavy", "moderate")
ALPHA = 0.05


def load_trials(path: str) -> pd.DataFrame:
    """Read the trial-level file and check it has the structure the study describes."""
    trials = pd.read_csv(path)

    required = [UNIT_COL, GROUP_COL, "trial_number", OUTCOME, "sex", "body_mass_kg"]
    missing = [column for column in required if column not in trials.columns]
    if missing:
        raise ValueError(f"data file is missing expected column(s): {missing}")

    if trials[OUTCOME].isna().any():
        raise ValueError("data file contains missing peak force values")

    # Each volunteer must belong to exactly one programme, or the volunteer-level
    # reduction below would mix groups.
    programmes_per_volunteer = trials.groupby(UNIT_COL)[GROUP_COL].nunique()
    if (programmes_per_volunteer != 1).any():
        raise ValueError("at least one volunteer appears under more than one programme")

    trials_per_volunteer = trials.groupby(UNIT_COL)["trial_number"].size()
    print("Trial-level file")
    print(f"  rows (trials)          : {len(trials)}")
    print(f"  volunteers             : {trials[UNIT_COL].nunique()}")
    print(
        "  trials per volunteer   : "
        f"min {trials_per_volunteer.min()}, max {trials_per_volunteer.max()}"
    )
    print()
    return trials


def describe_repeated_measures(trials: pd.DataFrame) -> None:
    """Report the trial structure that makes the reduction step necessary."""
    within_sd = trials.groupby(UNIT_COL)[OUTCOME].std(ddof=1).mean()
    trial_means = trials.groupby("trial_number")[OUTCOME].mean()

    print("Repeated-measures structure (descriptive only, not the test)")
    print(f"  mean within-volunteer SD across the four trials : {within_sd:.2f} kg")
    for trial_number, mean_force in trial_means.items():
        print(f"  mean peak force, trial {trial_number}                       : {mean_force:.2f} kg")
    print()


def reduce_to_volunteers(trials: pd.DataFrame) -> pd.DataFrame:
    """Collapse each volunteer's four trials to that volunteer's mean peak force.

    This is the step that makes the two groups comparable as independent samples:
    after it, one row is one volunteer and the rows are independent of each other.
    """
    volunteers = (
        trials.groupby([UNIT_COL, GROUP_COL, "sex", "body_mass_kg"], as_index=False)
        .agg(
            n_trials=("trial_number", "size"),
            mean_peak_force_kg=(OUTCOME, "mean"),
        )
        .sort_values(UNIT_COL)
        .reset_index(drop=True)
    )

    if len(volunteers) != trials[UNIT_COL].nunique():
        raise ValueError("reduction did not produce exactly one row per volunteer")

    print("Volunteer-level data set (unit of analysis)")
    print(f"  rows (volunteers)      : {len(volunteers)}")
    print(f"  trials averaged per row: {volunteers['n_trials'].min()}"
          f"-{volunteers['n_trials'].max()}")
    print()
    return volunteers


def summarise(volunteers: pd.DataFrame) -> pd.DataFrame:
    """Per-programme means and spreads computed from the per-volunteer values."""
    summary = (
        volunteers.groupby(GROUP_COL)["mean_peak_force_kg"]
        .agg(n="size", mean="mean", sd=lambda values: values.std(ddof=1),
             minimum="min", maximum="max")
        .reindex(list(GROUPS))
    )
    summary["sem"] = summary["sd"] / summary["n"] ** 0.5

    print("Per-programme summary of per-volunteer mean peak force (kg)")
    print(f"  {'programme':<10}{'n':>4}{'mean':>9}{'SD':>8}{'SEM':>8}{'min':>8}{'max':>8}")
    for programme, row in summary.iterrows():
        print(
            f"  {programme:<10}{int(row['n']):>4}{row['mean']:>9.2f}{row['sd']:>8.2f}"
            f"{row['sem']:>8.2f}{row['minimum']:>8.2f}{row['maximum']:>8.2f}"
        )
    print("  n is the number of volunteers, not the number of trials.")
    print()
    return summary


def compare_programmes(volunteers: pd.DataFrame, summary: pd.DataFrame) -> None:
    """Independent two-sample t-test on the per-volunteer means."""
    heavy = volunteers.loc[volunteers[GROUP_COL] == "heavy", "mean_peak_force_kg"]
    moderate = volunteers.loc[volunteers[GROUP_COL] == "moderate", "mean_peak_force_kg"]

    # Welch's test: it does not assume the two groups share a variance, and it
    # reduces to the pooled test when they do.
    result = stats.ttest_ind(heavy, moderate, equal_var=False)
    difference = heavy.mean() - moderate.mean()

    # Welch confidence interval for the difference in means.
    se_difference = (heavy.var(ddof=1) / len(heavy) + moderate.var(ddof=1) / len(moderate)) ** 0.5
    df = (heavy.var(ddof=1) / len(heavy) + moderate.var(ddof=1) / len(moderate)) ** 2 / (
        (heavy.var(ddof=1) / len(heavy)) ** 2 / (len(heavy) - 1)
        + (moderate.var(ddof=1) / len(moderate)) ** 2 / (len(moderate) - 1)
    )
    t_critical = stats.t.ppf(1 - ALPHA / 2, df)
    ci_low = difference - t_critical * se_difference
    ci_high = difference + t_critical * se_difference

    # Hedges' g, a standardised difference with the small-sample correction.
    pooled_sd = (
        ((len(heavy) - 1) * heavy.var(ddof=1) + (len(moderate) - 1) * moderate.var(ddof=1))
        / (len(heavy) + len(moderate) - 2)
    ) ** 0.5
    cohens_d = difference / pooled_sd
    correction = 1 - 3 / (4 * (len(heavy) + len(moderate)) - 9)
    hedges_g = cohens_d * correction

    print("Independent two-sample comparison (Welch's t-test) on per-volunteer means")
    print(f"  n (heavy)              : {len(heavy)} volunteers")
    print(f"  n (moderate)           : {len(moderate)} volunteers")
    print(f"  mean difference        : {difference:.2f} kg (heavy minus moderate)")
    print(f"  95% CI for difference  : {ci_low:.2f} to {ci_high:.2f} kg")
    print(f"  t                      : {result.statistic:.3f}")
    print(f"  df (Welch)             : {df:.2f}")
    print(f"  p (two-sided)          : {result.pvalue:.3f}")
    print(f"  Hedges' g              : {hedges_g:.2f}")
    print()

    verdict = "reject" if result.pvalue < ALPHA else "do not reject"
    print(
        f"  At alpha = {ALPHA:g} we {verdict} the null hypothesis of no difference "
        "in mean peak grip force between the two programmes."
    )
    if result.pvalue >= ALPHA:
        print(
            "  The heavy programme's mean is higher in this sample, but the interval "
            "above includes zero, so the data do not establish a difference."
        )


def main() -> None:
    trials = load_trials(DATA_PATH)
    describe_repeated_measures(trials)
    volunteers = reduce_to_volunteers(trials)
    summary = summarise(volunteers)
    compare_programmes(volunteers, summary)


if __name__ == "__main__":
    main()
