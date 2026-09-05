"""Airway effects of pool water disinfection system on indoor pool lifeguards.

Compares lifeguards at chlorine-only municipal pools with lifeguards at pools
using combined chlorine and ultraviolet treatment, across the seven outcomes
declared by the protocol (three primary, four secondary).

Each outcome is tested with a two-sample t-test for independent samples
(Welch, which does not assume equal group variances). The three primary
p-values are passed together through the Holm step-down adjustment in
statsmodels (`multipletests`) and judged at alpha = 0.05 on the adjusted
values. The four secondary p-values are judged at 0.05 as they come.

Run from the project root:

    python analysis.py
"""

from pathlib import Path

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

DATA_FILE = Path(__file__).resolve().parent / "lifeguard_airway.csv"

GROUP_COL = "pool_system"
GROUP_A = "chlorine_only"
GROUP_B = "chlorine_uv"

ALPHA = 0.05
ADJUST_METHOD = "holm"

PRIMARY_OUTCOMES = [
    ("feno_ppb", "Fractional exhaled nitric oxide (ppb)"),
    ("fev1_pct_pred", "FEV1 (% predicted)"),
    ("fvc_pct_pred", "FVC (% predicted)"),
]

SECONDARY_OUTCOMES = [
    ("airway_symptom_score", "Upper airway symptom score (0-20)"),
    ("eye_irritation_score", "Eye irritation score (0-10)"),
    ("cc16_ug_l", "Serum CC16 (ug/L)"),
    ("cough_days_per_month", "Cough days in past month"),
]


def load_data(path):
    """Read the lifeguard dataset and check the shape the protocol expects."""
    frame = pd.read_csv(path)

    expected_columns = [
        "lifeguard_id",
        GROUP_COL,
        *[name for name, _ in PRIMARY_OUTCOMES],
        *[name for name, _ in SECONDARY_OUTCOMES],
    ]
    missing = [column for column in expected_columns if column not in frame.columns]
    if missing:
        raise ValueError(f"data file is missing columns: {missing}")

    if frame["lifeguard_id"].duplicated().any():
        raise ValueError("lifeguard_id values are not unique")

    if frame[expected_columns].isna().any().any():
        raise ValueError("data file contains empty cells")

    observed_groups = sorted(frame[GROUP_COL].unique())
    if observed_groups != sorted([GROUP_A, GROUP_B]):
        raise ValueError(f"unexpected {GROUP_COL} values: {observed_groups}")

    return frame


def describe_and_test(frame, column):
    """Group means, SDs and the two-sample t-test for one outcome column."""
    values_a = frame.loc[frame[GROUP_COL] == GROUP_A, column].astype(float)
    values_b = frame.loc[frame[GROUP_COL] == GROUP_B, column].astype(float)

    result = stats.ttest_ind(values_a, values_b, equal_var=False)

    return {
        "outcome": column,
        "n_chlorine_only": int(values_a.size),
        "mean_chlorine_only": float(values_a.mean()),
        "sd_chlorine_only": float(values_a.std(ddof=1)),
        "n_chlorine_uv": int(values_b.size),
        "mean_chlorine_uv": float(values_b.mean()),
        "sd_chlorine_uv": float(values_b.std(ddof=1)),
        "mean_difference_uv_minus_only": float(values_b.mean() - values_a.mean()),
        "t_statistic": float(result.statistic),
        "df": float(result.df),
        "p_raw": float(result.pvalue),
    }


def verdict(p_value):
    return "significant" if p_value < ALPHA else "not significant"


def main():
    frame = load_data(DATA_FILE)

    primary = [describe_and_test(frame, column) for column, _ in PRIMARY_OUTCOMES]
    secondary = [describe_and_test(frame, column) for column, _ in SECONDARY_OUTCOMES]

    reject, p_adjusted, _, _ = multipletests(
        [row["p_raw"] for row in primary], alpha=ALPHA, method=ADJUST_METHOD
    )
    for row, adjusted, rejected in zip(primary, p_adjusted, reject):
        row["p_adjusted"] = float(adjusted)
        row["verdict"] = "significant" if bool(rejected) else "not significant"

    for row in secondary:
        row["verdict"] = verdict(row["p_raw"])

    labels = dict(PRIMARY_OUTCOMES + SECONDARY_OUTCOMES)

    print("Lifeguard airway study: chlorine_only vs chlorine_uv")
    print(f"data file: {DATA_FILE.name}")
    print(f"lifeguards: {len(frame)} "
          f"({primary[0]['n_chlorine_only']} chlorine_only, "
          f"{primary[0]['n_chlorine_uv']} chlorine_uv)")
    print(f"test: two-sample t-test for independent samples (Welch)")
    print(f"primary adjustment: statsmodels multipletests, method='{ADJUST_METHOD}', "
          f"alpha={ALPHA}")
    print()

    header = (
        f"{'outcome':<28}{'chlorine_only mean(SD)':>24}"
        f"{'chlorine_uv mean(SD)':>24}{'diff':>9}"
    )
    print("Group summaries")
    print(header)
    print("-" * len(header))
    for row in primary + secondary:
        summary_a = f"{row['mean_chlorine_only']:.2f} ({row['sd_chlorine_only']:.2f})"
        summary_b = f"{row['mean_chlorine_uv']:.2f} ({row['sd_chlorine_uv']:.2f})"
        print(
            f"{row['outcome']:<28}{summary_a:>24}{summary_b:>24}"
            f"{row['mean_difference_uv_minus_only']:>9.2f}"
        )
    print()

    print("Primary outcomes (adjusted at alpha = 0.05)")
    header = (
        f"{'outcome':<28}{'t':>8}{'df':>8}{'p raw':>10}"
        f"{'p adjusted':>13}  verdict"
    )
    print(header)
    print("-" * len(header))
    for row in primary:
        print(
            f"{row['outcome']:<28}{row['t_statistic']:>8.3f}{row['df']:>8.2f}"
            f"{row['p_raw']:>10.4f}{row['p_adjusted']:>13.4f}  {row['verdict']}"
        )
    print()

    print("Secondary outcomes (raw p compared with alpha = 0.05)")
    header = f"{'outcome':<28}{'t':>8}{'df':>8}{'p raw':>10}  verdict"
    print(header)
    print("-" * len(header))
    for row in secondary:
        print(
            f"{row['outcome']:<28}{row['t_statistic']:>8.3f}{row['df']:>8.2f}"
            f"{row['p_raw']:>10.4f}  {row['verdict']}"
        )
    print()

    print("Full precision")
    for row in primary:
        print(
            f"{labels[row['outcome']]}: "
            f"chlorine_only mean={row['mean_chlorine_only']!r} "
            f"sd={row['sd_chlorine_only']!r}; "
            f"chlorine_uv mean={row['mean_chlorine_uv']!r} "
            f"sd={row['sd_chlorine_uv']!r}; "
            f"t={row['t_statistic']!r} df={row['df']!r} "
            f"p_raw={row['p_raw']!r} p_adj={row['p_adjusted']!r}"
        )
    for row in secondary:
        print(
            f"{labels[row['outcome']]}: "
            f"chlorine_only mean={row['mean_chlorine_only']!r} "
            f"sd={row['sd_chlorine_only']!r}; "
            f"chlorine_uv mean={row['mean_chlorine_uv']!r} "
            f"sd={row['sd_chlorine_uv']!r}; "
            f"t={row['t_statistic']!r} df={row['df']!r} "
            f"p_raw={row['p_raw']!r}"
        )


if __name__ == "__main__":
    main()
