"""Kerbside versus urban background air quality: gatekept two-stage analysis.

Stage 1 is a pre-specified overall screen computed with plain array arithmetic on the
five declared pollutant columns. No statistical test is used in stage 1.

Stage 2 runs the five per-pollutant two-group comparisons, and runs ONLY if the stage 1
screen passes. If the screen fails the script stops and reports no per-pollutant
comparison at all.

Run from the project root:  python analysis.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# --------------------------------------------------------------------------------------
# Pre-specified analysis constants (declared before looking at any result)
# --------------------------------------------------------------------------------------

DATA_FILE = Path(__file__).resolve().parent / "air_quality_winter.csv"

# The protocol's ordered family of five pollutant outcomes.
OUTCOMES = [
    ("pm25_ug_m3", "PM2.5 (ug/m3)"),
    ("pm10_ug_m3", "PM10 (ug/m3)"),
    ("no2_ug_m3", "NO2 (ug/m3)"),
    ("o3_ug_m3", "Ozone (ug/m3)"),
    ("black_carbon_ug_m3", "Black carbon (ug/m3)"),
]

GROUP_COLUMN = "site_group"
EXPOSED_GROUP = "kerbside"
REFERENCE_GROUP = "background"

# Stage 1 screen: largest absolute standardised group-mean separation across the five
# outcomes must reach this value before any per-pollutant comparison is looked at.
SCREEN_THRESHOLD = 0.50

# Stage 2 significance level for each per-pollutant comparison.
ALPHA = 0.05


# --------------------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------------------


def load_data(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)

    expected_columns = ["day_id", GROUP_COLUMN] + [name for name, _ in OUTCOMES]
    missing = [c for c in expected_columns if c not in frame.columns]
    if missing:
        raise ValueError(f"data file is missing required columns: {missing}")

    observed_groups = sorted(frame[GROUP_COLUMN].unique())
    if observed_groups != sorted([EXPOSED_GROUP, REFERENCE_GROUP]):
        raise ValueError(f"unexpected site_group values: {observed_groups}")

    n_missing_cells = int(frame[expected_columns].isna().sum().sum())
    if n_missing_cells:
        raise ValueError(f"data file has {n_missing_cells} empty cells; none expected")

    if frame["day_id"].duplicated().any():
        raise ValueError("day_id is not unique")

    return frame


def describe_dataset(frame: pd.DataFrame) -> None:
    print("=" * 78)
    print("DATASET")
    print("=" * 78)
    print(f"File:              {DATA_FILE.name}")
    print(f"Monitoring days:   {len(frame)}")
    counts = frame[GROUP_COLUMN].value_counts()
    for group in (EXPOSED_GROUP, REFERENCE_GROUP):
        print(f"  {group:<12} {int(counts[group])} days")
    print(f"Declared outcomes: {len(OUTCOMES)} "
          f"({', '.join(name for name, _ in OUTCOMES)})")
    print()


# --------------------------------------------------------------------------------------
# Stage 1: overall screen (array arithmetic only, no statistical test)
# --------------------------------------------------------------------------------------


def stage_one_screen(frame: pd.DataFrame):
    """Compute the overall screening quantity from all five outcome columns.

    For each outcome the screen forms the two group means, the two group standard
    deviations, the difference of the means, and the ratio of that difference to the
    pooled spread. The screening quantity is the largest absolute value of that ratio
    across the five outcomes. Only means, standard deviations, differences, ratios and
    a maximum are used; no testing routine is involved.
    """
    exposed = frame[frame[GROUP_COLUMN] == EXPOSED_GROUP]
    reference = frame[frame[GROUP_COLUMN] == REFERENCE_GROUP]

    rows = []
    for column, label in OUTCOMES:
        a = exposed[column].to_numpy(dtype=float)
        b = reference[column].to_numpy(dtype=float)

        mean_a = float(np.mean(a))
        mean_b = float(np.mean(b))
        # Sample standard deviations (ddof=1).
        sd_a = float(np.std(a, ddof=1))
        sd_b = float(np.std(b, ddof=1))

        n_a = a.size
        n_b = b.size

        mean_difference = mean_a - mean_b
        pooled_sd = float(
            np.sqrt(
                ((n_a - 1) * sd_a ** 2 + (n_b - 1) * sd_b ** 2) / (n_a + n_b - 2)
            )
        )
        separation = mean_difference / pooled_sd

        rows.append(
            {
                "column": column,
                "label": label,
                "n_kerbside": n_a,
                "n_background": n_b,
                "mean_kerbside": mean_a,
                "sd_kerbside": sd_a,
                "mean_background": mean_b,
                "sd_background": sd_b,
                "mean_difference": mean_difference,
                "pooled_sd": pooled_sd,
                "separation": separation,
                "abs_separation": abs(separation),
            }
        )

    magnitudes = np.array([r["abs_separation"] for r in rows], dtype=float)
    screening_quantity = float(np.max(magnitudes))
    driver = rows[int(np.argmax(magnitudes))]

    print("=" * 78)
    print("STAGE 1 - OVERALL SCREEN (no statistical test used)")
    print("=" * 78)
    print(f"Pre-specified threshold: screening quantity >= {SCREEN_THRESHOLD:.2f}")
    print()
    header = (
        f"{'Outcome':<24}{'mean kerb':>11}{'sd kerb':>10}"
        f"{'mean bkg':>11}{'sd bkg':>10}{'diff':>10}{'|separation|':>14}"
    )
    print(header)
    print("-" * len(header))
    for r in rows:
        print(
            f"{r['label']:<24}{r['mean_kerbside']:>11.3f}{r['sd_kerbside']:>10.3f}"
            f"{r['mean_background']:>11.3f}{r['sd_background']:>10.3f}"
            f"{r['mean_difference']:>10.3f}{r['abs_separation']:>14.3f}"
        )
    print("-" * len(header))
    print(
        f"Screening quantity (largest magnitude across the five outcomes): "
        f"{screening_quantity:.3f}"
    )
    print(f"Largest magnitude comes from: {driver['label']}")
    passed = screening_quantity >= SCREEN_THRESHOLD
    print(
        f"Screen result: {screening_quantity:.3f} "
        f"{'>=' if passed else '<'} {SCREEN_THRESHOLD:.2f} -> "
        f"{'PASS' if passed else 'FAIL'}"
    )
    print()

    return screening_quantity, passed, rows


# --------------------------------------------------------------------------------------
# Stage 2: per-pollutant comparisons (only when the screen passes)
# --------------------------------------------------------------------------------------


def stage_two_comparisons(frame: pd.DataFrame, stage_one_rows) -> None:
    exposed = frame[frame[GROUP_COLUMN] == EXPOSED_GROUP]
    reference = frame[frame[GROUP_COLUMN] == REFERENCE_GROUP]

    print("=" * 78)
    print("BRANCH TAKEN: SCREEN PASSED -> STAGE 2 PER-POLLUTANT COMPARISONS")
    print("=" * 78)
    print(
        f"Test: Welch two-sample t-test for independent samples, two-sided, "
        f"alpha = {ALPHA:.2f}"
    )
    print("Each of the five declared outcomes is tested at this level; no multiplicity")
    print("adjustment is applied across the five outcomes.")
    print()

    header = (
        f"{'Outcome':<24}{'kerbside mean (sd)':>22}{'background mean (sd)':>24}"
        f"{'diff':>9}{'t':>9}{'df':>8}{'p':>11}  {'at 0.05'}"
    )
    print(header)
    print("-" * len(header))

    for stage_one_row in stage_one_rows:
        column = stage_one_row["column"]
        a = exposed[column].to_numpy(dtype=float)
        b = reference[column].to_numpy(dtype=float)

        result = stats.ttest_ind(a, b, equal_var=False)
        t_stat = float(result.statistic)
        p_value = float(result.pvalue)
        df = float(result.df)

        kerb = f"{stage_one_row['mean_kerbside']:.2f} ({stage_one_row['sd_kerbside']:.2f})"
        bkg = f"{stage_one_row['mean_background']:.2f} ({stage_one_row['sd_background']:.2f})"
        verdict = "significant" if p_value < ALPHA else "not significant"

        print(
            f"{stage_one_row['label']:<24}{kerb:>22}{bkg:>24}"
            f"{stage_one_row['mean_difference']:>9.2f}{t_stat:>9.3f}{df:>8.2f}"
            f"{p_value:>11.3g}  {verdict}"
        )

    print("-" * len(header))
    print()


def stage_two_not_run(screening_quantity: float) -> None:
    print("=" * 78)
    print("BRANCH TAKEN: SCREEN FAILED -> ANALYSIS STOPS")
    print("=" * 78)
    print(
        f"Screening quantity {screening_quantity:.3f} did not reach the pre-specified "
        f"threshold {SCREEN_THRESHOLD:.2f}."
    )
    print("No per-pollutant comparison is computed and none is reported.")
    print()


# --------------------------------------------------------------------------------------


def main() -> None:
    frame = load_data(DATA_FILE)
    describe_dataset(frame)

    screening_quantity, passed, stage_one_rows = stage_one_screen(frame)

    if passed:
        stage_two_comparisons(frame, stage_one_rows)
    else:
        stage_two_not_run(screening_quantity)

    print("=" * 78)
    print("END OF ANALYSIS")
    print("=" * 78)


if __name__ == "__main__":
    main()
