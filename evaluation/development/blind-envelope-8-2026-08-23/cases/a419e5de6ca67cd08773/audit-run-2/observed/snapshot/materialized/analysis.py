"""Substrate trial: does a protein-rich supplement raise oyster-mushroom flush yield?

Reads flush_yields.csv and compares flush_yield_g between the two substrates with an
independent two-sample t-test applied to every recorded flush.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "flush_yields.csv"


def load_data(path=DATA_FILE):
    """Load the flush table and check it has the shape the trial produced."""
    df = pd.read_csv(path)
    expected = [
        "chamber_id",
        "substrate",
        "flush_number",
        "flush_yield_g",
        "air_temp_c",
        "days_from_spawn",
    ]
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise ValueError(f"missing columns in {path.name}: {missing}")
    if df[expected].isna().any().any():
        raise ValueError("unexpected missing values in flush_yields.csv")
    return df


def describe(df):
    """Print the basic shape of the table and the per-flush yield trend."""
    print("=" * 66)
    print("DATA")
    print("=" * 66)
    print(f"Rows (recorded flushes): {len(df)}")
    print(f"Chambers: {df['chamber_id'].nunique()}")
    print(f"Flushes per chamber: {df.groupby('chamber_id').size().unique().tolist()}")
    print()

    print("Rows per substrate:")
    for substrate, n in df["substrate"].value_counts().sort_index().items():
        print(f"  {substrate:<14} {n:>3}")
    print()

    print("Mean flush yield (g) by flush number, all chambers pooled:")
    by_flush = df.groupby("flush_number")["flush_yield_g"].mean()
    for flush, mean in by_flush.items():
        print(f"  flush {flush}: {mean:8.1f}")
    print()

    print("Covariate ranges:")
    print(
        f"  air_temp_c:      {df['air_temp_c'].min():.1f} to {df['air_temp_c'].max():.1f} C"
    )
    print(
        f"  days_from_spawn: {df['days_from_spawn'].min()} to "
        f"{df['days_from_spawn'].max()} days"
    )
    print()


def compare_substrates(df):
    """Two-sample t-test on flush_yield_g, one observation per recorded flush."""
    supplemented = df.loc[df["substrate"] == "supplemented", "flush_yield_g"]
    standard = df.loc[df["substrate"] == "standard", "flush_yield_g"]

    result = stats.ttest_ind(supplemented, standard)

    stats_out = {
        "n_total": len(df),
        "n_supplemented": len(supplemented),
        "n_standard": len(standard),
        "mean_supplemented": supplemented.mean(),
        "mean_standard": standard.mean(),
        "sd_supplemented": supplemented.std(ddof=1),
        "sd_standard": standard.std(ddof=1),
        "difference": supplemented.mean() - standard.mean(),
        "t_statistic": result.statistic,
        "df": len(supplemented) + len(standard) - 2,
        "p_value": result.pvalue,
    }

    # Percentage lift of the supplemented mean over the standard mean.
    stats_out["percent_lift"] = 100.0 * stats_out["difference"] / stats_out["mean_standard"]

    return stats_out


def report(s):
    print("=" * 66)
    print("TWO-SAMPLE COMPARISON OF FLUSH YIELD")
    print("=" * 66)
    print(f"Observations entering the test: {s['n_total']}")
    print(
        f"  supplemented: n = {s['n_supplemented']}, "
        f"mean = {s['mean_supplemented']:.1f} g, SD = {s['sd_supplemented']:.1f} g"
    )
    print(
        f"  standard:     n = {s['n_standard']}, "
        f"mean = {s['mean_standard']:.1f} g, SD = {s['sd_standard']:.1f} g"
    )
    print()
    print(f"Mean difference (supplemented - standard): {s['difference']:.1f} g")
    print(f"Lift over standard: {s['percent_lift']:.1f}%")
    print(f"t({s['df']}) = {s['t_statistic']:.3f}")
    print(f"p = {s['p_value']:.3e}")
    print()

    verdict = "significant" if s["p_value"] < 0.05 else "not significant"
    print(f"At the 0.05 level the difference is {verdict}.")
    print("=" * 66)


def main():
    df = load_data()
    describe(df)
    summary = compare_substrates(df)
    report(summary)
    return summary


if __name__ == "__main__":
    main()
