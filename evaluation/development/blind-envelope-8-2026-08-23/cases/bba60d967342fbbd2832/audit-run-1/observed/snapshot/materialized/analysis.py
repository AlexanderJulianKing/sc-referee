"""
Earthworm body mass under biochar amendment.

Compares individual earthworm body mass (mg) between biochar-amended and
unamended control soil at week 8 of the mesocosm assay.

Input : earthworm_body_mass.csv (project root)
Output: printed results table (group means, t statistic, p-value)

Run with:  python3 analysis.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "earthworm_body_mass.csv"
RESPONSE = "body_mass_mg"
GROUP = "treatment"
ALPHA = 0.05


def load_data(path: Path) -> pd.DataFrame:
    """Read the weighed-worm table and check it is complete."""
    df = pd.read_csv(path)

    expected_columns = [
        "mesocosm_id",
        "treatment",
        "worm_id",
        "body_mass_mg",
        "gut_cleared",
        "soil_moisture_pct",
    ]
    missing = [c for c in expected_columns if c not in df.columns]
    if missing:
        raise ValueError(f"missing expected column(s): {missing}")

    if df[expected_columns].isna().any().any():
        raise ValueError("unexpected missing values in the data file")

    if df["worm_id"].duplicated().any():
        raise ValueError("worm_id must be unique: one row per weighed worm")

    levels = sorted(df[GROUP].unique())
    if levels != ["biochar", "control"]:
        raise ValueError(f"expected exactly two treatment levels, found {levels}")

    return df


def describe_groups(df: pd.DataFrame) -> pd.DataFrame:
    """Per-treatment summary of the weighed worms."""
    summary = (
        df.groupby(GROUP)[RESPONSE]
        .agg(
            n_worms="size",
            mean_mg="mean",
            sd_mg=lambda s: s.std(ddof=1),
            min_mg="min",
            max_mg="max",
        )
        .reset_index()
    )
    summary["sem_mg"] = summary["sd_mg"] / np.sqrt(summary["n_worms"])
    return summary


def compare_treatments(df: pd.DataFrame) -> dict:
    """
    Independent two-sample t-test on body mass.

    Every weighed worm in the table contributes one observation to the test, so
    the sample size is the number of rows in the file.
    """
    biochar = df.loc[df[GROUP] == "biochar", RESPONSE].to_numpy()
    control = df.loc[df[GROUP] == "control", RESPONSE].to_numpy()

    n_biochar = biochar.size
    n_control = control.size
    n_total = n_biochar + n_control

    result = stats.ttest_ind(biochar, control, equal_var=True)
    t_stat = float(result.statistic)
    p_value = float(result.pvalue)
    df_resid = n_total - 2

    # Pooled standard deviation, mean difference and its 95% confidence interval.
    sd_biochar = biochar.std(ddof=1)
    sd_control = control.std(ddof=1)
    pooled_var = (
        (n_biochar - 1) * sd_biochar**2 + (n_control - 1) * sd_control**2
    ) / df_resid
    pooled_sd = float(np.sqrt(pooled_var))

    diff = float(biochar.mean() - control.mean())
    se_diff = pooled_sd * np.sqrt(1.0 / n_biochar + 1.0 / n_control)
    t_crit = stats.t.ppf(1 - ALPHA / 2, df_resid)
    ci_low = diff - t_crit * se_diff
    ci_high = diff + t_crit * se_diff

    cohens_d = diff / pooled_sd

    return {
        "n_total": n_total,
        "n_biochar": n_biochar,
        "n_control": n_control,
        "mean_biochar": float(biochar.mean()),
        "mean_control": float(control.mean()),
        "sd_biochar": float(sd_biochar),
        "sd_control": float(sd_control),
        "pooled_sd": pooled_sd,
        "mean_difference": diff,
        "se_difference": float(se_diff),
        "ci_low": float(ci_low),
        "ci_high": float(ci_high),
        "t_statistic": t_stat,
        "df": int(df_resid),
        "p_value": p_value,
        "cohens_d": float(cohens_d),
    }


def main() -> None:
    df = load_data(DATA_FILE)

    print("Earthworm body mass: biochar-amended vs unamended control soil")
    print("=" * 66)
    print(f"Data file : {DATA_FILE.name}")
    print(f"Rows read : {len(df)} weighed worms")
    print(f"Mesocosms : {df['mesocosm_id'].nunique()}")
    print(
        "Gut-cleared: "
        + ", ".join(
            f"{k}={v}" for k, v in df["gut_cleared"].value_counts().sort_index().items()
        )
    )
    moisture = df["soil_moisture_pct"]
    print(
        f"Soil moisture (%): {moisture.min():.1f}-{moisture.max():.1f}, "
        f"mean {moisture.mean():.2f}"
    )
    print()

    print("Group summary (body_mass_mg)")
    print("-" * 66)
    summary = describe_groups(df)
    for _, row in summary.iterrows():
        print(
            f"{row[GROUP]:>8}: n = {int(row['n_worms']):3d}   "
            f"mean = {row['mean_mg']:7.2f} mg   "
            f"SD = {row['sd_mg']:6.2f} mg   "
            f"SEM = {row['sem_mg']:5.2f} mg   "
            f"range = {row['min_mg']:.1f}-{row['max_mg']:.1f} mg"
        )
    print()

    res = compare_treatments(df)

    print("Independent two-sample t-test (biochar - control)")
    print("-" * 66)
    print(f"Sample size (worms in test) : {res['n_total']}")
    print(f"  biochar                   : {res['n_biochar']}")
    print(f"  control                   : {res['n_control']}")
    print(f"Mean, biochar               : {res['mean_biochar']:.2f} mg")
    print(f"Mean, control               : {res['mean_control']:.2f} mg")
    print(f"Mean difference             : {res['mean_difference']:.2f} mg")
    print(
        f"95% CI for the difference   : "
        f"[{res['ci_low']:.2f}, {res['ci_high']:.2f}] mg"
    )
    print(f"Pooled SD                   : {res['pooled_sd']:.2f} mg")
    print(f"t                           : {res['t_statistic']:.4f}")
    print(f"df                          : {res['df']}")
    print(f"p-value                     : {res['p_value']:.6g}")
    print(f"Cohen's d                   : {res['cohens_d']:.3f}")
    print()

    verdict = "reject" if res["p_value"] < ALPHA else "do not reject"
    print(
        f"At alpha = {ALPHA}, {verdict} the null hypothesis of equal mean body mass."
    )


if __name__ == "__main__":
    main()
