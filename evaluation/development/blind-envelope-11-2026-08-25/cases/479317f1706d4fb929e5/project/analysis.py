"""Antenatal iron supplementation study: analysis of the four declared outcomes.

Ninety-six women assessed at 28 weeks of gestation, 48 on iron plus folic acid and
48 on folic acid alone. Four laboratory outcomes were declared in the protocol
before the samples were analysed and are examined here in that declared order:

    1. haemoglobin_g_dl
    2. ferritin_ug_l
    3. transferrin_saturation_pct
    4. hepcidin_ng_ml

The four outcomes are one declared family. Each is compared between regimens with a
Welch two-sample t-test, and the four raw p-values are corrected together in a
single call to pingouin.multicomp (Holm step-down, family-wise alpha = 0.05).
Every verdict printed below is read off the Holm-adjusted p-value; no verdict is
taken from a raw p-value.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from pingouin import multicomp
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "antenatal_iron_study.csv"

GROUP_COLUMN = "supplement_regimen"
TREATED = "iron_plus_folic_acid"
CONTROL = "folic_acid_only"

# The declared outcome family, in the order the protocol declares it.
DECLARED_OUTCOMES = [
    ("haemoglobin_g_dl", "Haemoglobin (g/dL)"),
    ("ferritin_ug_l", "Ferritin (ug/L)"),
    ("transferrin_saturation_pct", "Transferrin saturation (%)"),
    ("hepcidin_ng_ml", "Hepcidin (ng/mL)"),
]

FAMILY_ALPHA = 0.05
CORRECTION_METHOD = "holm"


def load_data(path: Path) -> pd.DataFrame:
    """Read the study CSV and check the two structural facts the analysis assumes."""
    frame = pd.read_csv(path)

    missing = frame.isna().sum().sum()
    if missing:
        raise ValueError(f"expected a complete data set, found {missing} missing cells")

    regimens = set(frame[GROUP_COLUMN].unique())
    if regimens != {TREATED, CONTROL}:
        raise ValueError(f"expected exactly two regimens, found {sorted(regimens)}")

    return frame


def report_group_sizes(frame: pd.DataFrame) -> None:
    print("Group sizes")
    print("-" * 72)
    for regimen in (TREATED, CONTROL):
        print(f"  {regimen:<24s} n = {int((frame[GROUP_COLUMN] == regimen).sum())}")
    print(f"  {'total':<24s} n = {len(frame)}")
    print()


def report_group_summaries(frame: pd.DataFrame) -> None:
    """Per-group n, mean and spread (sample standard deviation) for each outcome."""
    print("Per-group summary of each declared outcome (mean +/- SD)")
    print("-" * 72)
    header = f"{'Outcome':<30s}{'Regimen':<24s}{'n':>4s}{'mean':>10s}{'SD':>10s}"
    print(header)
    for column, label in DECLARED_OUTCOMES:
        for regimen in (TREATED, CONTROL):
            values = frame.loc[frame[GROUP_COLUMN] == regimen, column]
            print(
                f"{label:<30s}{regimen:<24s}{values.size:>4d}"
                f"{values.mean():>10.2f}{values.std(ddof=1):>10.2f}"
            )
    print()


def test_family(frame: pd.DataFrame) -> pd.DataFrame:
    """Welch t-test for every declared outcome, p-values kept together as one family."""
    rows = []
    for column, label in DECLARED_OUTCOMES:
        treated = frame.loc[frame[GROUP_COLUMN] == TREATED, column]
        control = frame.loc[frame[GROUP_COLUMN] == CONTROL, column]
        result = stats.ttest_ind(treated, control, equal_var=False)
        rows.append(
            {
                "outcome": column,
                "label": label,
                "mean_difference": treated.mean() - control.mean(),
                "t_statistic": float(result.statistic),
                "p_raw": float(result.pvalue),
            }
        )
    return pd.DataFrame(rows)


def adjust_family(results: pd.DataFrame) -> pd.DataFrame:
    """Correct the whole declared family in one pass with the pingouin package.

    pingouin.multicomp returns the reject flags and the adjusted p-values. Both the
    adjusted values and the verdicts reported here come from that single call.
    """
    reject, p_adjusted = multicomp(
        results["p_raw"].to_numpy(),
        alpha=FAMILY_ALPHA,
        method=CORRECTION_METHOD,
    )
    adjusted = results.copy()
    adjusted["p_adjusted"] = p_adjusted
    adjusted["significant"] = reject
    return adjusted


def report_tests(adjusted: pd.DataFrame) -> None:
    print(
        f"Two-group comparisons, {len(adjusted)} declared outcomes corrected together "
        f"as one family"
    )
    print(
        f"Correction: pingouin.multicomp, method='{CORRECTION_METHOD}', "
        f"family-wise alpha = {FAMILY_ALPHA}"
    )
    print("Verdicts are read from the adjusted p-values only.")
    print("-" * 72)
    header = (
        f"{'Outcome':<30s}{'diff':>9s}{'t':>8s}{'p (raw)':>11s}"
        f"{'p (adj)':>11s}  verdict"
    )
    print(header)
    for row in adjusted.itertuples():
        verdict = "significant" if row.significant else "not significant"
        print(
            f"{row.label:<30s}{row.mean_difference:>9.2f}{row.t_statistic:>8.2f}"
            f"{row.p_raw:>11.4f}{row.p_adjusted:>11.4f}  {verdict}"
        )
    print()
    print(
        "diff = mean(iron plus folic acid) - mean(folic acid alone); "
        "t = Welch two-sample t statistic."
    )


def main() -> None:
    frame = load_data(DATA_FILE)
    print("Antenatal iron plus folic acid versus folic acid alone at 28 weeks")
    print("=" * 72)
    print()
    report_group_sizes(frame)
    report_group_summaries(frame)
    adjusted = adjust_family(test_family(frame))
    report_tests(adjusted)


if __name__ == "__main__":
    main()
