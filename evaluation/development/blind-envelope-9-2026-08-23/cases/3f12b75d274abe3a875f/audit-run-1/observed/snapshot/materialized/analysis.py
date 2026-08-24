"""Signature-whistle peak frequency: do male and female dolphins differ?

The dolphin is the independent experimental unit. Each animal contributed six
whistle recordings from separate encounters, so the 108 rows of the data file
are repeated measurements, not 108 independent observations.

The script therefore runs in two stages:

  1. `average_recordings_within_dolphin` reduces the full recording table to
     exactly one row per dolphin, carrying that dolphin's sex and the mean of
     its six peak-frequency measurements.
  2. `compare_sexes` compares males and females on that reduced table, so each
     animal enters the comparison exactly once (n = 18 dolphins, 9 per sex).

Run:  python3 analysis.py
"""

import os

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(HERE, "whistle_recordings.csv")

UNIT_COLUMN = "dolphin_catalogue_id"
GROUP_COLUMN = "sex"
OUTCOME_COLUMN = "peak_frequency_khz"
GROUP_LEVELS = ("female", "male")


def load_recordings(path=DATA_FILE):
    """Read the recording-level table (one row per whistle recording)."""
    recordings = pd.read_csv(path)
    expected = [UNIT_COLUMN, GROUP_COLUMN, "recording_number", OUTCOME_COLUMN]
    missing = [c for c in expected if c not in recordings.columns]
    if missing:
        raise ValueError("data file is missing columns: %s" % ", ".join(missing))
    return recordings


def average_recordings_within_dolphin(recordings):
    """Reduce recordings to animals.

    Takes the full recording table and hands back a table with exactly one row
    per dolphin: the catalogue id, that animal's sex, the number of recordings
    averaged, and the mean of its peak-frequency measurements.

    Sex is a property of the animal and is constant within a dolphin, so it is
    carried through unchanged; the function checks that this actually holds.
    """
    sexes_per_animal = recordings.groupby(UNIT_COLUMN)[GROUP_COLUMN].nunique()
    inconsistent = sexes_per_animal[sexes_per_animal != 1]
    if len(inconsistent) > 0:
        raise ValueError(
            "sex is not constant within these dolphins: %s"
            % ", ".join(inconsistent.index)
        )

    dolphins = (
        recordings.groupby([UNIT_COLUMN, GROUP_COLUMN], as_index=False)
        .agg(
            n_recordings=(OUTCOME_COLUMN, "size"),
            mean_peak_frequency_khz=(OUTCOME_COLUMN, "mean"),
        )
        .sort_values(UNIT_COLUMN)
        .reset_index(drop=True)
    )
    return dolphins


def describe_groups(dolphins):
    """Per-sex summary of the animal-level means (n is a count of dolphins)."""
    summary = (
        dolphins.groupby(GROUP_COLUMN)["mean_peak_frequency_khz"]
        .agg(n_dolphins="size", mean="mean", sd=lambda v: v.std(ddof=1))
        .reindex(list(GROUP_LEVELS))
        .reset_index()
    )
    return summary


def compare_sexes(dolphins):
    """Two-group comparison of the animal-level means, one row per dolphin.

    Welch's two-sample t-test (does not assume equal variances between the
    sexes), with the difference in means and its 95% confidence interval.
    """
    female = dolphins.loc[
        dolphins[GROUP_COLUMN] == "female", "mean_peak_frequency_khz"
    ].to_numpy()
    male = dolphins.loc[
        dolphins[GROUP_COLUMN] == "male", "mean_peak_frequency_khz"
    ].to_numpy()

    n_f, n_m = len(female), len(male)
    mean_f, mean_m = female.mean(), male.mean()
    sd_f = female.std(ddof=1)
    sd_m = male.std(ddof=1)

    difference = mean_f - mean_m
    se = np.sqrt(sd_f ** 2 / n_f + sd_m ** 2 / n_m)
    df = se ** 4 / (
        (sd_f ** 2 / n_f) ** 2 / (n_f - 1) + (sd_m ** 2 / n_m) ** 2 / (n_m - 1)
    )
    t_stat, p_value = stats.ttest_ind(female, male, equal_var=False)
    t_crit = stats.t.ppf(0.975, df)

    return {
        "n_female": n_f,
        "n_male": n_m,
        "mean_female": mean_f,
        "mean_male": mean_m,
        "sd_female": sd_f,
        "sd_male": sd_m,
        "difference_female_minus_male": difference,
        "se_difference": se,
        "t": float(t_stat),
        "df": float(df),
        "p_value": float(p_value),
        "ci_low": difference - t_crit * se,
        "ci_high": difference + t_crit * se,
    }


def within_animal_spread(recordings):
    """Typical spread of the six recordings within one animal (pooled SD)."""
    devs = recordings.groupby(UNIT_COLUMN)[OUTCOME_COLUMN].transform("mean")
    resid = recordings[OUTCOME_COLUMN] - devs
    n_animals = recordings[UNIT_COLUMN].nunique()
    df_within = len(recordings) - n_animals
    return float(np.sqrt((resid ** 2).sum() / df_within))


def main():
    recordings = load_recordings()
    print("Recording-level table: %d rows, %d dolphins, %d recordings each."
          % (len(recordings),
             recordings[UNIT_COLUMN].nunique(),
             int(recordings.groupby(UNIT_COLUMN).size().max())))
    print("Peak frequency across all recordings: %.2f to %.2f kHz"
          % (recordings[OUTCOME_COLUMN].min(), recordings[OUTCOME_COLUMN].max()))
    print("Pooled within-animal SD: %.3f kHz" % within_animal_spread(recordings))
    print()

    dolphins = average_recordings_within_dolphin(recordings)
    print("After averaging recordings within each animal: %d rows (one per dolphin)."
          % len(dolphins))
    print()
    print("Animal-level means (kHz):")
    print(dolphins.to_string(index=False,
                             float_format=lambda v: "%.3f" % v))
    print()

    print("Per-sex summary of animal-level means:")
    print(describe_groups(dolphins).to_string(index=False,
                                              float_format=lambda v: "%.3f" % v))
    print()

    result = compare_sexes(dolphins)
    print("Welch's two-sample t-test on the %d dolphin means "
          "(%d female, %d male):"
          % (result["n_female"] + result["n_male"],
             result["n_female"], result["n_male"]))
    print("  female mean = %.3f kHz (SD %.3f)"
          % (result["mean_female"], result["sd_female"]))
    print("  male   mean = %.3f kHz (SD %.3f)"
          % (result["mean_male"], result["sd_male"]))
    print("  difference (female - male) = %.3f kHz, SE %.3f"
          % (result["difference_female_minus_male"], result["se_difference"]))
    print("  95%% CI = %.3f to %.3f kHz"
          % (result["ci_low"], result["ci_high"]))
    print("  t = %.3f, df = %.2f, p = %.4f"
          % (result["t"], result["df"], result["p_value"]))


if __name__ == "__main__":
    main()
