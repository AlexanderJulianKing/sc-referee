"""Wash validation trial: aerobic plate counts on bagged leaf salad.

Compares the plant's standard chlorine wash against the peracetic acid wash
under evaluation.

The wash was applied to whole production batches, so the batch is the
independent experimental unit. The five retail packs taken from a batch are
repeat measurements of that one batch, not twenty independent trials of the
wash. The script therefore reduces packs to batches first, in the named step
`reduce_packs_to_batches`, and runs the two-group comparison on exactly the
table that step returns.

Run with: /usr/local/bin/python3 analysis.py
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "pack_plate_counts.csv"

OUTCOME = "aerobic_plate_count_log_cfu_g"
UNIT = "batch_id"
GROUP = "wash_treatment"

REFERENCE_WASH = "chlorine"
TEST_WASH = "peracetic_acid"


def load_pack_data(path=DATA_FILE):
    """Read the committed pack-level CSV exactly as it sits on disk."""
    return pd.read_csv(path, dtype={UNIT: str, GROUP: str, "pack_id": str})


def reduce_packs_to_batches(packs):
    """Collapse the pack-level table to one mean log count per batch.

    Takes the raw table (one row per retail pack) and returns a table with one
    row per production batch, holding the batch identifier, the wash that batch
    received, the number of packs that went into the mean, and the mean
    aerobic plate count in log10 CFU/g.
    """
    batches = (
        packs.groupby([UNIT, GROUP], as_index=False)
        .agg(
            n_packs=(OUTCOME, "size"),
            mean_log_cfu_g=(OUTCOME, "mean"),
        )
        .sort_values(UNIT)
        .reset_index(drop=True)
    )
    return batches


def compare_washes(batches):
    """Independent two-sample t-test on the batch mean log counts."""
    reference = batches.loc[batches[GROUP] == REFERENCE_WASH, "mean_log_cfu_g"]
    treatment = batches.loc[batches[GROUP] == TEST_WASH, "mean_log_cfu_g"]

    result = stats.ttest_ind(reference, treatment)

    return {
        "n_reference_batches": int(reference.size),
        "n_treatment_batches": int(treatment.size),
        "mean_reference": float(reference.mean()),
        "mean_treatment": float(treatment.mean()),
        "sd_reference": float(reference.std(ddof=1)),
        "sd_treatment": float(treatment.std(ddof=1)),
        "difference": float(reference.mean() - treatment.mean()),
        "t_statistic": float(result.statistic),
        "p_value": float(result.pvalue),
        "df": int(reference.size + treatment.size - 2),
    }


def main():
    packs = load_pack_data()
    batches = reduce_packs_to_batches(packs)
    stats_out = compare_washes(batches)

    print("Wash validation trial: aerobic plate count on bagged leaf salad")
    print("=" * 62)
    print(f"Pack-level rows read       : {len(packs)}")
    print(f"Batches after reduction    : {len(batches)}")
    print(f"Packs per batch            : {sorted(batches['n_packs'].unique())}")
    print()

    print("Batch mean log10 CFU/g")
    print("-" * 62)
    for row in batches.itertuples(index=False):
        print(f"  {row.batch_id}  {row.wash_treatment:<15} "
              f"n_packs={row.n_packs}  mean={row.mean_log_cfu_g:.3f}")
    print()

    print("Group comparison (independent two-sample t-test on batch means)")
    print("-" * 62)
    print(f"  {REFERENCE_WASH:<15} n = {stats_out['n_reference_batches']} batches, "
          f"mean = {stats_out['mean_reference']:.3f}, "
          f"sd = {stats_out['sd_reference']:.3f} log CFU/g")
    print(f"  {TEST_WASH:<15} n = {stats_out['n_treatment_batches']} batches, "
          f"mean = {stats_out['mean_treatment']:.3f}, "
          f"sd = {stats_out['sd_treatment']:.3f} log CFU/g")
    print(f"  Difference (chlorine - peracetic acid) = "
          f"{stats_out['difference']:.3f} log CFU/g")
    print(f"  t({stats_out['df']}) = {stats_out['t_statistic']:.3f}, "
          f"p = {stats_out['p_value']:.6f}")


if __name__ == "__main__":
    main()
