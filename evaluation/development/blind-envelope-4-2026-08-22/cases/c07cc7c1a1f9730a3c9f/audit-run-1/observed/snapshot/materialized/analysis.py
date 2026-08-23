"""Interleukin-6 in newly diagnosed rheumatoid arthritis versus matched healthy volunteers.

Reads the assay table, counts every assay measurement toward the sample size, and compares
mean interleukin-6 concentration between the control and RA cohorts with an independent
two-sample test of means.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "il6_assay.csv"


def load_assay_table(path: Path) -> pd.DataFrame:
    """Load the assay table exactly as delivered by the plate reader export."""
    table = pd.read_csv(path)
    expected = ["sample_ref", "cohort", "replicate_run", "il6_pg_ml"]
    if list(table.columns) != expected:
        raise ValueError(f"unexpected columns: {list(table.columns)}")
    if table["il6_pg_ml"].isna().any():
        raise ValueError("missing interleukin-6 concentrations in the assay table")
    return table


def main() -> None:
    table = load_assay_table(DATA_FILE)

    # Every assay measurement counts toward the sample size, so the analysis runs across
    # all rows of the assay table.
    control = table.loc[table["cohort"] == "control", "il6_pg_ml"]
    ra = table.loc[table["cohort"] == "RA", "il6_pg_ml"]

    n_total = len(table)
    n_control = len(control)
    n_ra = len(ra)

    mean_control = control.mean()
    mean_ra = ra.mean()
    sd_control = control.std(ddof=1)
    sd_ra = ra.std(ddof=1)
    difference = mean_ra - mean_control

    # Independent two-sample comparison of means between the two cohorts.
    t_statistic, p_value = stats.ttest_ind(ra, control)
    df = n_ra + n_control - 2

    print("Interleukin-6 assay analysis")
    print("=" * 46)
    print(f"Assay measurements analysed (total n): {n_total}")
    print(f"  control: n = {n_control}, mean = {mean_control:.2f} pg/mL, SD = {sd_control:.2f} pg/mL")
    print(f"  RA:      n = {n_ra}, mean = {mean_ra:.2f} pg/mL, SD = {sd_ra:.2f} pg/mL")
    print(f"Difference in means (RA - control): {difference:.2f} pg/mL")
    print(f"Independent two-sample t test: t({df}) = {t_statistic:.2f}, p = {p_value:.3e}")

    if p_value < 0.05 and difference > 0:
        verdict = "Interleukin-6 is elevated in rheumatoid arthritis."
    elif p_value < 0.05:
        verdict = "Interleukin-6 is lower in rheumatoid arthritis."
    else:
        verdict = "Interleukin-6 does not differ between the cohorts."
    print(verdict)


if __name__ == "__main__":
    main()
