"""Home blood-pressure study: compare morning systolic BP between the two programmes.

Reads home_bp_readings.csv and runs an independent two-sample t-test on
systolic_bp_mmhg, with every measured row entering the comparison as its own
observation.
"""

import math
from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "home_bp_readings.csv"


def load_readings(path=DATA_FILE):
    """Load the reading table and check it is complete."""
    df = pd.read_csv(path)
    expected = ["participant_code", "programme", "day", "systolic_bp_mmhg"]
    assert list(df.columns) == expected, f"unexpected columns: {list(df.columns)}"
    assert df.notna().all().all(), "the file contains missing values"
    return df


def describe_group(values):
    """Mean, standard deviation and count for one group of readings."""
    return {
        "n": int(values.size),
        "mean": float(values.mean()),
        "sd": float(values.std(ddof=1)),
        "min": float(values.min()),
        "max": float(values.max()),
    }


def compare_groups(df):
    """Independent two-sample t-test on every row of the table."""
    walking = df.loc[df["programme"] == "walking", "systolic_bp_mmhg"]
    leaflet = df.loc[df["programme"] == "leaflet", "systolic_bp_mmhg"]

    w = describe_group(walking)
    l = describe_group(leaflet)

    t_stat, p_value = stats.ttest_ind(walking, leaflet)
    dof = w["n"] + l["n"] - 2

    pooled_var = (
        (w["n"] - 1) * w["sd"] ** 2 + (l["n"] - 1) * l["sd"] ** 2
    ) / dof
    pooled_sd = math.sqrt(pooled_var)
    se_diff = pooled_sd * math.sqrt(1.0 / w["n"] + 1.0 / l["n"])

    diff = w["mean"] - l["mean"]
    crit = stats.t.ppf(0.975, dof)

    return {
        "walking": w,
        "leaflet": l,
        "n_total": int(w["n"] + l["n"]),
        "difference": diff,
        "ci_low": diff - crit * se_diff,
        "ci_high": diff + crit * se_diff,
        "pooled_sd": pooled_sd,
        "se_diff": se_diff,
        "t": float(t_stat),
        "df": dof,
        "p": float(p_value),
        "cohens_d": diff / pooled_sd,
    }


def main():
    df = load_readings()
    res = compare_groups(df)

    print("Home blood-pressure study: morning systolic BP by programme")
    print("=" * 62)
    print(f"Rows analysed: {res['n_total']}")
    print(f"Participant codes present: {df['participant_code'].nunique()}")
    print(f"Measurement days present: {sorted(df['day'].unique())}")
    print()

    print(f"{'group':<10}{'n':>6}{'mean':>10}{'sd':>9}{'min':>8}{'max':>8}")
    for name in ("walking", "leaflet"):
        g = res[name]
        print(
            f"{name:<10}{g['n']:>6}{g['mean']:>10.2f}{g['sd']:>9.2f}"
            f"{g['min']:>8.0f}{g['max']:>8.0f}"
        )
    print()

    print("Independent two-sample t-test (walking - leaflet)")
    print(f"  difference in means : {res['difference']:.2f} mmHg")
    print(f"  95% CI              : {res['ci_low']:.2f} to {res['ci_high']:.2f} mmHg")
    print(f"  pooled SD           : {res['pooled_sd']:.2f} mmHg")
    print(f"  standard error      : {res['se_diff']:.3f} mmHg")
    print(f"  t ({res['df']} df)          : {res['t']:.3f}")
    print(f"  p-value             : {res['p']:.6f}")
    print(f"  Cohen's d           : {res['cohens_d']:.3f}")


if __name__ == "__main__":
    main()
