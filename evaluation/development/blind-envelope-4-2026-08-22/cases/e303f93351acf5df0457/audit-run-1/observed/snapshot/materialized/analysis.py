"""Sleep efficiency by shift-rotation pattern.

The data file holds one row per monitored night, seven nights per worker. Nights
from one worker describe that worker, not seven independent people, so the
comparison is made between workers: the night-level table is first reduced to one
summary value per worker, and the two-sample test runs on that per-worker table.

The three stages are kept in separate named functions:

  load_night_level_data     read the CSV of nights
  reduce_nights_to_workers  collapse nights to one row per worker
  compare_rotation_patterns two-sample comparison on the per-worker table
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "sleep_efficiency.csv"

UNIT_COLUMN = "worker_id"
GROUP_COLUMN = "rotation_pattern"
OUTCOME_COLUMN = "sleep_efficiency_pct"
NIGHT_COLUMN = "night_number"
GROUPS = ("slow", "rapid")


def load_night_level_data(path=DATA_FILE):
    """Read the night-level CSV. One row in, one row out: one monitored night."""
    nights = pd.read_csv(path)
    expected = [UNIT_COLUMN, GROUP_COLUMN, NIGHT_COLUMN, OUTCOME_COLUMN]
    if list(nights.columns) != expected:
        raise ValueError(f"unexpected columns: {list(nights.columns)!r}")
    if nights.isna().any().any():
        raise ValueError("night-level data contains missing values")
    return nights


def reduce_nights_to_workers(nights):
    """Collapse the night-level table to one summary value per worker.

    Takes the night-level table and returns a per-worker table with one row per
    worker_id: the worker's rotation pattern, the number of nights that worker
    contributed, and the mean of that worker's own nightly sleep efficiency.
    This is the reduction from repeated measurements to independent units; the
    returned table is what the statistical comparison is run on.
    """
    patterns_per_worker = nights.groupby(UNIT_COLUMN)[GROUP_COLUMN].nunique()
    if (patterns_per_worker != 1).any():
        raise ValueError("a worker appears under more than one rotation pattern")

    workers = (
        nights.groupby([UNIT_COLUMN, GROUP_COLUMN], as_index=False)
        .agg(
            nights_monitored=(NIGHT_COLUMN, "count"),
            mean_sleep_efficiency_pct=(OUTCOME_COLUMN, "mean"),
        )
        .sort_values(UNIT_COLUMN)
        .reset_index(drop=True)
    )
    return workers


def compare_rotation_patterns(workers):
    """Independent two-sample comparison of means between rotation patterns.

    Runs on the per-worker table handed back by reduce_nights_to_workers, so each
    value entering the test is one worker's mean sleep efficiency.
    """
    slow = workers.loc[workers[GROUP_COLUMN] == "slow", "mean_sleep_efficiency_pct"]
    rapid = workers.loc[workers[GROUP_COLUMN] == "rapid", "mean_sleep_efficiency_pct"]

    result = stats.ttest_ind(slow, rapid, equal_var=True)

    return {
        "n_slow": int(slow.size),
        "n_rapid": int(rapid.size),
        "n_total": int(slow.size + rapid.size),
        "mean_slow": float(slow.mean()),
        "mean_rapid": float(rapid.mean()),
        "sd_slow": float(slow.std(ddof=1)),
        "sd_rapid": float(rapid.std(ddof=1)),
        "difference": float(slow.mean() - rapid.mean()),
        "t_statistic": float(result.statistic),
        "df": int(slow.size + rapid.size - 2),
        "p_value": float(result.pvalue),
    }


def main():
    nights = load_night_level_data()
    workers = reduce_nights_to_workers(nights)
    result = compare_rotation_patterns(workers)

    print("Night-level rows read:          ", len(nights))
    print("Workers after reduction:        ", len(workers))
    print("Nights per worker (min, max):   ",
          int(workers["nights_monitored"].min()),
          int(workers["nights_monitored"].max()))
    print()
    print("Analysis unit: worker. Values entering the test: one mean per worker.")
    print(f"  slow  n = {result['n_slow']:2d}  "
          f"mean = {result['mean_slow']:.2f}  sd = {result['sd_slow']:.2f}")
    print(f"  rapid n = {result['n_rapid']:2d}  "
          f"mean = {result['mean_rapid']:.2f}  sd = {result['sd_rapid']:.2f}")
    print(f"  total n = {result['n_total']}")
    print()
    print(f"Difference (slow - rapid): {result['difference']:.2f} percentage points")
    print(f"Two-sample t test: t({result['df']}) = {result['t_statistic']:.3f}, "
          f"p = {result['p_value']:.4f}")

    print()
    print("Per-worker table:")
    print(workers.to_string(index=False))


if __name__ == "__main__":
    main()
