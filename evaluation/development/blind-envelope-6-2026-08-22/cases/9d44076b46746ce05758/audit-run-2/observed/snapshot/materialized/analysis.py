"""River valley amenity lighting and lesser horseshoe bat foraging activity.

Reads the detector-night file, summarises the dark and lit survey groups, and
compares nightly bat passes between them with an independent two-sample test
applied to every detector-night row in the file.

Run:  python3 analysis.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "bat_activity.csv"
GROUPS = ("dark", "lit")


def load_detector_nights(path):
    """Load the detector-night table and check it looks like the survey file."""
    df = pd.read_csv(path)
    expected = [
        "roost_code",
        "lighting_condition",
        "night_index",
        "min_temp_c",
        "bat_passes",
    ]
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise ValueError(f"missing expected column(s): {', '.join(missing)}")
    if df[expected].isna().any().any():
        raise ValueError("detector-night file contains blank values")
    unexpected = sorted(set(df["lighting_condition"]) - set(GROUPS))
    if unexpected:
        raise ValueError(f"unexpected lighting_condition value(s): {unexpected}")
    return df


def describe_group(values):
    """Descriptive statistics for one lighting group's detector-nights."""
    values = np.asarray(values, dtype=float)
    n = values.size
    sd = values.std(ddof=1)
    return {
        "n_detector_nights": n,
        "mean": values.mean(),
        "sd": sd,
        "se": sd / np.sqrt(n),
        "median": float(np.median(values)),
        "minimum": values.min(),
        "maximum": values.max(),
    }


def main():
    df = load_detector_nights(DATA_FILE)

    dark = df.loc[df["lighting_condition"] == "dark", "bat_passes"].to_numpy(float)
    lit = df.loc[df["lighting_condition"] == "lit", "bat_passes"].to_numpy(float)

    print("River valley lighting and lesser horseshoe bat activity")
    print("=" * 58)
    print(f"Detector-night rows read from {DATA_FILE.name}: {len(df)}")
    print(f"Survey nights per detector: {df['night_index'].max()}")
    print()

    print("Nightly bat passes by lighting condition")
    print("-" * 58)
    header = f"{'group':<6}{'n':>5}{'mean':>10}{'sd':>9}{'se':>8}{'median':>9}{'min':>7}{'max':>7}"
    print(header)
    summaries = {}
    for name, values in (("dark", dark), ("lit", lit)):
        s = describe_group(values)
        summaries[name] = s
        print(
            f"{name:<6}{s['n_detector_nights']:>5}{s['mean']:>10.1f}{s['sd']:>9.1f}"
            f"{s['se']:>8.1f}{s['median']:>9.1f}{s['minimum']:>7.0f}{s['maximum']:>7.0f}"
        )
    print()

    print("Nightly minimum temperature by lighting condition (degrees C)")
    print("-" * 58)
    for name in GROUPS:
        temps = df.loc[df["lighting_condition"] == name, "min_temp_c"].to_numpy(float)
        print(
            f"{name:<6}n={temps.size:<4} mean={temps.mean():6.2f}  "
            f"sd={temps.std(ddof=1):5.2f}  range {temps.min():.1f} to {temps.max():.1f}"
        )
    temp_r, temp_p = stats.pearsonr(df["min_temp_c"], df["bat_passes"])
    print(
        f"Passes vs nightly minimum temperature across all detector-nights: "
        f"r = {temp_r:.3f}, p = {temp_p:.4g}"
    )
    print()

    # Independent two-sample comparison, one observation per detector-night.
    print("Independent two-sample t-test (Welch), all detector-nights")
    print("-" * 58)
    t_stat, p_value = stats.ttest_ind(dark, lit, equal_var=False)

    n_dark = dark.size
    n_lit = lit.size
    var_dark = dark.var(ddof=1)
    var_lit = lit.var(ddof=1)
    se_diff = np.sqrt(var_dark / n_dark + var_lit / n_lit)
    df_welch = (var_dark / n_dark + var_lit / n_lit) ** 2 / (
        (var_dark / n_dark) ** 2 / (n_dark - 1)
        + (var_lit / n_lit) ** 2 / (n_lit - 1)
    )
    diff = dark.mean() - lit.mean()
    crit = stats.t.ppf(0.975, df_welch)
    ci_low = diff - crit * se_diff
    ci_high = diff + crit * se_diff

    pooled_sd = np.sqrt(
        ((n_dark - 1) * var_dark + (n_lit - 1) * var_lit) / (n_dark + n_lit - 2)
    )
    cohens_d = diff / pooled_sd
    pct_change = 100.0 * (lit.mean() - dark.mean()) / dark.mean()

    print(f"n (dark detector-nights)          = {n_dark}")
    print(f"n (lit detector-nights)           = {n_lit}")
    print(f"total detector-nights compared    = {n_dark + n_lit}")
    print(f"mean difference (dark minus lit)  = {diff:.1f} passes per night")
    print(f"95% confidence interval           = {ci_low:.1f} to {ci_high:.1f}")
    print(f"t statistic                       = {t_stat:.3f}")
    print(f"degrees of freedom (Welch)        = {df_welch:.2f}")
    print(f"p value                           = {p_value:.6g}")
    print(f"Cohen's d                         = {cohens_d:.3f}")
    print(f"change at lit sites               = {pct_change:.1f}%")
    print()

    verdict = "lower" if diff > 0 else "higher"
    signif = "is" if p_value < 0.05 else "is not"
    print(
        f"Activity at lit roosts is {verdict} than at dark roosts and the "
        f"difference {signif} significant at the 5% level."
    )


if __name__ == "__main__":
    main()
