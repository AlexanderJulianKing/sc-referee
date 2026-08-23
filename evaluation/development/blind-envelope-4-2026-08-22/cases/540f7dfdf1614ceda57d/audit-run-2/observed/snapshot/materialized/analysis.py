"""Composting bulking-agent trial: woodchip vs straw carbon-to-nitrogen ratio.

The raw file `compost_cores.csv` holds one row per core sample. Five cores were
taken from each windrow, so the core rows are spatial subsamples of the same
pile and are not independent observations. The windrow is the experimental unit:
a whole windrow was built with one bulking agent.

The script therefore (1) reduces the raw core rows to one representative value
per windrow by averaging that windrow's five cores, and (2) compares the two
bulking agents with an independent two-sample comparison of means on those 16
per-windrow values.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

RAW_CSV = Path(__file__).resolve().parent / "compost_cores.csv"
GROUPS = ("woodchip", "straw")


def load_raw(path: Path) -> pd.DataFrame:
    """Read the raw core-level sampling data and check the expected design."""
    raw = pd.read_csv(path)

    expected_columns = ["windrow_id", "bulking_agent", "core_number", "c_to_n_ratio"]
    if list(raw.columns) != expected_columns:
        raise ValueError(f"unexpected columns: {list(raw.columns)}")
    if raw.isna().any().any():
        raise ValueError("raw file contains missing values")
    if raw.duplicated(subset=["windrow_id", "core_number"]).any():
        raise ValueError("windrow_id + core_number does not identify rows uniquely")

    # Each windrow must carry exactly one bulking agent, otherwise the windrow
    # is not the unit that was assigned to a group.
    agents_per_windrow = raw.groupby("windrow_id")["bulking_agent"].nunique()
    if (agents_per_windrow != 1).any():
        raise ValueError("a windrow carries more than one bulking agent")

    return raw


def windrow_means(raw: pd.DataFrame) -> pd.DataFrame:
    """Collapse the five cores of each windrow into one value per windrow."""
    per_windrow = (
        raw.groupby(["windrow_id", "bulking_agent"], as_index=False)
        .agg(
            n_cores=("c_to_n_ratio", "size"),
            windrow_mean_c_to_n=("c_to_n_ratio", "mean"),
        )
        .sort_values("windrow_id")
        .reset_index(drop=True)
    )
    return per_windrow


def main() -> None:
    raw = load_raw(RAW_CSV)
    per_windrow = windrow_means(raw)

    print("=" * 68)
    print("RAW SAMPLING DATA (core level)")
    print("=" * 68)
    print(f"Raw data rows (one core each): {len(raw)}")
    print(f"Windrows: {raw['windrow_id'].nunique()}")
    print(f"Cores per windrow: {sorted(set(raw.groupby('windrow_id').size()))}")
    print("Core rows per bulking agent:")
    for agent in GROUPS:
        print(f"  {agent:<9} {int((raw['bulking_agent'] == agent).sum())}")
    print(
        f"Core-level c_to_n_ratio range: "
        f"{raw['c_to_n_ratio'].min():.1f} to {raw['c_to_n_ratio'].max():.1f}"
    )

    print()
    print("=" * 68)
    print("STEP 1 - REDUCE CORES TO ONE VALUE PER WINDROW")
    print("=" * 68)
    print("The five cores from a windrow describe one pile, so they are averaged")
    print("into a single representative value before any group comparison.")
    print()
    print(per_windrow.to_string(index=False, float_format=lambda v: f"{v:.3f}"))

    woodchip = per_windrow.loc[
        per_windrow["bulking_agent"] == "woodchip", "windrow_mean_c_to_n"
    ]
    straw = per_windrow.loc[
        per_windrow["bulking_agent"] == "straw", "windrow_mean_c_to_n"
    ]

    print()
    print("=" * 68)
    print("STEP 2 - GROUP SUMMARIES (analysis unit = windrow)")
    print("=" * 68)
    print(f"{'agent':<9} {'n_windrows':>10} {'mean':>8} {'sd':>8} {'min':>8} {'max':>8}")
    for agent, values in (("woodchip", woodchip), ("straw", straw)):
        print(
            f"{agent:<9} {len(values):>10} {values.mean():>8.3f} "
            f"{values.std(ddof=1):>8.3f} {values.min():>8.3f} {values.max():>8.3f}"
        )
    print(f"Total windrows entering the comparison: {len(per_windrow)}")

    difference = woodchip.mean() - straw.mean()
    print(f"Difference (woodchip - straw): {difference:.3f}")

    print()
    print("=" * 68)
    print("STEP 3 - INDEPENDENT TWO-SAMPLE COMPARISON OF MEANS")
    print("=" * 68)
    print("Unit of analysis: the windrow. n = 8 windrows per group, 16 in total.")
    print("Input values: the 16 per-windrow mean ratios from step 1.")
    print()

    # Welch's independent two-sample t-test: it does not assume the two groups
    # share a variance, so it stays valid if the piles differ in spread.
    welch = stats.ttest_ind(woodchip, straw, equal_var=False)

    # scipy 1.9 does not return the Welch degrees of freedom or a confidence
    # interval, so both are computed here from the group summaries.
    n1, n2 = len(woodchip), len(straw)
    v1, v2 = woodchip.var(ddof=1), straw.var(ddof=1)
    se = ((v1 / n1) + (v2 / n2)) ** 0.5
    welch_df = (v1 / n1 + v2 / n2) ** 2 / (
        (v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1)
    )
    t_crit = stats.t.ppf(0.975, welch_df)
    ci_low = difference - t_crit * se
    ci_high = difference + t_crit * se

    print("Welch's two-sample t-test (primary):")
    print(f"  t  = {welch.statistic:.4f}")
    print(f"  df = {welch_df:.4f}")
    print(f"  p  = {welch.pvalue:.6g}")
    print(f"  95% CI for the difference in means: [{ci_low:.3f}, {ci_high:.3f}]")

    # Reported as a sensitivity check only; the Welch test above is the result.
    pooled = stats.ttest_ind(woodchip, straw, equal_var=True)
    print()
    print("Pooled-variance two-sample t-test (sensitivity check):")
    print(f"  t  = {pooled.statistic:.4f}")
    print(f"  df = {len(woodchip) + len(straw) - 2}")
    print(f"  p  = {pooled.pvalue:.6g}")

    print()
    print("=" * 68)
    print("CONCLUSION")
    print("=" * 68)
    lower = "straw" if straw.mean() < woodchip.mean() else "woodchip"
    higher = "woodchip" if lower == "straw" else "straw"
    verdict = "is" if welch.pvalue < 0.05 else "is not"
    print(
        f"{lower.capitalize()} windrows finish with the lower carbon to nitrogen "
        f"ratio than\n{higher} windrows, and at the 5 percent level the difference "
        f"{verdict} statistically\nsignificant (Welch p = {welch.pvalue:.6g})."
    )


if __name__ == "__main__":
    main()
