"""Rootstock and powdery mildew susceptibility: leaf-level analysis.

Vineyard trial, one block, sixteen grapevines of a single scion variety. Eight vines
were grafted onto a drought-tolerant rootstock and eight onto the estate's standard
rootstock. At veraison eight leaves were collected from each vine, four from the upper
canopy and four from the lower canopy, and the area of powdery mildew lesions on each
leaf was measured by image analysis.

Each measured leaf is a replicate observation of mildew damage, so the two rootstock
groups are compared with an independent two-sample t-test over all leaves in the table.

Reads:  mildew_leaf_data.csv
Writes: nothing (all results are printed)
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "mildew_leaf_data.csv"

RESPONSE = "LesionArea"
GROUP = "Rootstock"
STANDARD = "Standard"
DROUGHT = "DroughtTolerant"


def load_leaves(path=DATA_FILE):
    """Load the leaf table, one row per measured leaf."""
    leaves = pd.read_csv(path)
    expected = [
        "Vine",
        "Rootstock",
        "CanopyPosition",
        "Leaf",
        "LesionArea",
        "TotalLeafArea",
    ]
    missing = [column for column in expected if column not in leaves.columns]
    if missing:
        raise ValueError("missing expected column(s): " + ", ".join(missing))
    return leaves


def describe_group(values):
    """Mean, standard deviation, standard error, and range of a group of leaves."""
    return {
        "n_leaves": int(values.size),
        "mean": float(values.mean()),
        "sd": float(values.std(ddof=1)),
        "se": float(values.std(ddof=1) / (values.size ** 0.5)),
        "minimum": float(values.min()),
        "maximum": float(values.max()),
    }


def main():
    leaves = load_leaves()

    n_leaves = int(len(leaves))
    n_vines = int(leaves["Vine"].nunique())

    standard = leaves.loc[leaves[GROUP] == STANDARD, RESPONSE]
    drought = leaves.loc[leaves[GROUP] == DROUGHT, RESPONSE]

    standard_stats = describe_group(standard)
    drought_stats = describe_group(drought)

    difference = standard_stats["mean"] - drought_stats["mean"]
    percent_reduction = 100.0 * difference / standard_stats["mean"]

    # Independent two-sample t-test; every leaf enters as its own observation.
    result = stats.ttest_ind(standard, drought)
    df = n_leaves - 2

    print("Rootstock and powdery mildew lesion area")
    print("=" * 60)
    print()
    print("Data set")
    print("-" * 60)
    print(f"File                        : {DATA_FILE.name}")
    print(f"Leaves measured (n)         : {n_leaves}")
    print(f"Vines sampled               : {n_vines}")
    print(f"Leaves per vine             : {n_leaves // n_vines}")
    print(
        "Mean total leaf area (cm2)  : "
        f"{leaves['TotalLeafArea'].mean():.1f} "
        f"(SD {leaves['TotalLeafArea'].std(ddof=1):.1f})"
    )
    print()

    print("Lesion area by rootstock (cm2 per leaf)")
    print("-" * 60)
    header = f"{'Rootstock':<18}{'n':>5}{'mean':>9}{'SD':>8}{'SE':>8}{'min':>8}{'max':>8}"
    print(header)
    for label, group_stats in ((STANDARD, standard_stats), (DROUGHT, drought_stats)):
        print(
            f"{label:<18}"
            f"{group_stats['n_leaves']:>5}"
            f"{group_stats['mean']:>9.2f}"
            f"{group_stats['sd']:>8.2f}"
            f"{group_stats['se']:>8.2f}"
            f"{group_stats['minimum']:>8.2f}"
            f"{group_stats['maximum']:>8.2f}"
        )
    print()
    print(f"Difference (Standard - DroughtTolerant): {difference:.2f} cm2 per leaf")
    print(f"Reduction on the drought-tolerant rootstock: {percent_reduction:.1f}%")
    print()

    print("Independent two-sample t-test on LesionArea")
    print("-" * 60)
    print(f"Observations (leaves)       : n = {n_leaves}")
    print(f"Degrees of freedom          : {df}")
    print(f"t statistic                 : {result.statistic:.3f}")
    print(f"p-value (two-sided)         : {result.pvalue:.3e}")
    print()

    verdict = "significant" if result.pvalue < 0.05 else "not significant"
    print(f"At the 5% level the difference between rootstocks is {verdict}.")

    per_vine = (
        leaves.groupby(["Rootstock", "Vine"])[RESPONSE]
        .mean()
        .round(2)
        .reset_index()
        .sort_values(["Rootstock", "Vine"])
    )
    print()
    print("Mean lesion area per vine (cm2 per leaf)")
    print("-" * 60)
    print(per_vine.to_string(index=False))


if __name__ == "__main__":
    main()
