"""Analysis of peripapillary RNFL thickness by topical drop regimen.

One-year open-angle glaucoma study, 24 patients, 12 per regimen.

The raw file `rnfl_sector_thickness.csv` is sector level: one row is one
clock-hour sector of one patient's designated study eye, six rows per
patient. The six rows belonging to a patient are repeated measurements on
the same eye and are not independent observations.

The randomised and analysed unit is the patient. This script therefore
collapses each patient's six sector values to a single per-patient mean
RNFL thickness first, and only then compares the two regimens with a
standard independent two-sample t-test. The sample size of that test is
12 patients per arm, not 72 sector rows per arm.
"""

import os

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(HERE, "rnfl_sector_thickness.csv")

OLD_REGIMEN = "timolol"
NEW_REGIMEN = "latanoprost"

EXPECTED_SECTORS = 6


def load_sector_data(path):
    """Read the frozen sector-level CSV and check its shape."""
    frame = pd.read_csv(path)

    expected_columns = [
        "patient_id",
        "drop_regimen",
        "clock_hour_sector",
        "rnfl_thickness_um",
    ]
    missing = [c for c in expected_columns if c not in frame.columns]
    if missing:
        raise ValueError("missing expected column(s): %s" % ", ".join(missing))

    if frame["rnfl_thickness_um"].isna().any():
        raise ValueError("rnfl_thickness_um contains missing values")

    sectors_per_patient = frame.groupby("patient_id")["clock_hour_sector"].nunique()
    if not (sectors_per_patient == EXPECTED_SECTORS).all():
        raise ValueError("every patient must contribute exactly 6 distinct sectors")

    regimens_per_patient = frame.groupby("patient_id")["drop_regimen"].nunique()
    if not (regimens_per_patient == 1).all():
        raise ValueError("drop_regimen must be constant within a patient")

    return frame


def per_patient_means(frame):
    """Collapse the six sector rows of each patient to one mean value.

    Returns one row per patient: the unit that was randomised and the unit
    the two-sample test is run on.
    """
    patient = (
        frame.groupby(["patient_id", "drop_regimen"], as_index=False)["rnfl_thickness_um"]
        .mean()
        .rename(columns={"rnfl_thickness_um": "mean_rnfl_thickness_um"})
        .sort_values("patient_id")
        .reset_index(drop=True)
    )
    return patient


def describe_group(values):
    """Sample size, mean and sample (n-1) standard deviation."""
    return {
        "n": int(values.size),
        "mean": float(np.mean(values)),
        "sd": float(np.std(values, ddof=1)),
    }


def main():
    sector_frame = load_sector_data(DATA_PATH)
    patient_frame = per_patient_means(sector_frame)

    old_values = patient_frame.loc[
        patient_frame["drop_regimen"] == OLD_REGIMEN, "mean_rnfl_thickness_um"
    ].to_numpy()
    new_values = patient_frame.loc[
        patient_frame["drop_regimen"] == NEW_REGIMEN, "mean_rnfl_thickness_um"
    ].to_numpy()

    old_stats = describe_group(old_values)
    new_stats = describe_group(new_values)

    # Standard independent two-sample t-test (equal variances assumed),
    # run on one averaged value per patient.
    t_stat, p_value = stats.ttest_ind(new_values, old_values, equal_var=True)
    df = old_stats["n"] + new_stats["n"] - 2

    # Difference in means (newer minus older) with a 95% confidence
    # interval from the pooled standard deviation.
    diff = new_stats["mean"] - old_stats["mean"]
    pooled_var = (
        (old_stats["n"] - 1) * old_stats["sd"] ** 2
        + (new_stats["n"] - 1) * new_stats["sd"] ** 2
    ) / df
    se_diff = np.sqrt(pooled_var * (1.0 / old_stats["n"] + 1.0 / new_stats["n"]))
    t_crit = stats.t.ppf(0.975, df)
    ci_low = diff - t_crit * se_diff
    ci_high = diff + t_crit * se_diff

    print("RNFL thickness by drop regimen: one-year final visit")
    print("=" * 60)
    print("Raw sector-level rows read : %d" % len(sector_frame))
    print("Patients after averaging   : %d" % len(patient_frame))
    print("Sectors per patient        : %d" % EXPECTED_SECTORS)
    print()

    print("Per-patient mean RNFL thickness (um), by regimen")
    print("-" * 60)
    for label, s in ((OLD_REGIMEN, old_stats), (NEW_REGIMEN, new_stats)):
        print(
            "%-14s n = %2d   mean = %6.2f   sd = %5.2f"
            % (label, s["n"], s["mean"], s["sd"])
        )
    print()

    print("Independent two-sample t-test (equal variances)")
    print("-" * 60)
    print("Unit of analysis        : patient (one averaged value each)")
    print("Sample size             : %d vs %d patients" % (new_stats["n"], old_stats["n"]))
    print("Difference (%s - %s): %.2f um" % (NEW_REGIMEN, OLD_REGIMEN, diff))
    print("95%% CI for difference   : %.2f to %.2f um" % (ci_low, ci_high))
    print("t(%d)                    = %.4f" % (df, t_stat))
    print("p-value                 = %.4f" % p_value)
    print()

    print("Per-patient values used in the test")
    print("-" * 60)
    with pd.option_context("display.max_rows", None):
        print(patient_frame.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
