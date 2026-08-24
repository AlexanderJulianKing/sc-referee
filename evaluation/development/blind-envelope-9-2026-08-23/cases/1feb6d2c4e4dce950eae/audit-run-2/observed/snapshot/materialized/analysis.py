"""Whole-body vibration at the tractor seat pan: air-suspension seat vs standard mechanical seat.

Design
------
Twenty tractor operators, ten per seat type. Each operator was instrumented on six separate
field runs on different days, so the file holds 120 rows but only 20 independent units. Seat
type is fixed for an operator, so the operator, not the run, is the unit that carries a group
label. The six runs sharing an ``operator_code`` are repeated measurements on one person and
machine and are not independent of one another.

Primary inference
-----------------
A cluster resampling procedure written out here rather than taken from a package. Whole
operators are resampled, with all six of that operator's runs kept together, so the
within-operator correlation is carried through into the resampled datasets. The confidence
interval is the percentile interval of the operator-level bootstrap distribution. The p-value
comes from a second operator-level resampling procedure: the seat labels are reassigned to
whole operators. With ten operators per group there are only C(20,10) = 184,756 distinct label
assignments, so that reference distribution is enumerated exactly instead of sampled.

Illustrative contrast only
--------------------------
A plain two-sample comparison across the 120 individual runs is also reported. It is NOT valid
for inference in this study, because it treats six repeated runs on one operator as six
independent observations. It is printed for contrast with the dependence-aware result and is
not the basis of any conclusion.
"""

from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "vibration_runs.csv"
OUTCOME = "vibration_total_value_ms2"
UNIT = "operator_code"
GROUP = "seat_type"
REFERENCE = "mechanical"        # standard mechanical seat
COMPARATOR = "air_suspension"   # air-suspension seat
N_BOOT = 20000
SEED = 20260823
CI_LEVEL = 0.95


def load_runs(path):
    """Read the run-level table and check the design is the balanced one described."""
    runs = pd.read_csv(path)
    expected = [UNIT, GROUP, "run_number", OUTCOME]
    if list(runs.columns) != expected:
        raise ValueError(f"unexpected columns: {list(runs.columns)}")
    if runs.isna().any().any():
        raise ValueError("missing values in the data file")
    if runs.duplicated([UNIT, "run_number"]).any():
        raise ValueError("duplicate operator/run pairs")
    per_operator = runs.groupby(UNIT)[GROUP].nunique()
    if (per_operator != 1).any():
        raise ValueError("seat type varies within an operator; the operator is not the unit")
    return runs


def operator_table(runs):
    """Collapse to one row per operator: the unit of analysis."""
    ops = (
        runs.groupby([UNIT, GROUP], as_index=False)
        .agg(n_runs=(OUTCOME, "size"),
             operator_mean=(OUTCOME, "mean"),
             within_sd=(OUTCOME, "std"))
        .sort_values(UNIT)
        .reset_index(drop=True)
    )
    return ops


def mean_difference(values_ref, values_comp):
    """Reference seat minus comparator seat, on operator means."""
    return float(np.mean(values_ref) - np.mean(values_comp))


def cluster_bootstrap(ops, n_boot=N_BOOT, seed=SEED, ci_level=CI_LEVEL):
    """Resample whole operators with replacement, within seat group.

    Resampling operators rather than rows is what keeps an operator's six runs together: an
    operator is either drawn into a resample with all six of their runs or not drawn at all.
    Because each operator contributes the same six runs, the operator mean is a sufficient
    summary of that operator for the difference in means, so the resampling is done on the
    operator means. Sampling is stratified by seat type, which holds the ten-and-ten design
    fixed across resamples and guarantees both groups are always present.
    """
    rng = np.random.default_rng(seed)
    ref = ops.loc[ops[GROUP] == REFERENCE, "operator_mean"].to_numpy()
    comp = ops.loc[ops[GROUP] == COMPARATOR, "operator_mean"].to_numpy()
    n_ref, n_comp = ref.size, comp.size

    draws = np.empty(n_boot)
    for b in range(n_boot):
        ref_b = ref[rng.integers(0, n_ref, n_ref)]
        comp_b = comp[rng.integers(0, n_comp, n_comp)]
        draws[b] = mean_difference(ref_b, comp_b)

    alpha = 1.0 - ci_level
    lo, hi = np.percentile(draws, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return {
        "estimate": mean_difference(ref, comp),
        "boot_se": float(draws.std(ddof=1)),
        "ci_low": float(lo),
        "ci_high": float(hi),
        "n_boot": n_boot,
        "n_units_ref": int(n_ref),
        "n_units_comp": int(n_comp),
    }


def cluster_permutation(ops):
    """Exact reference distribution from reassigning seat labels to whole operators.

    Under the null of no seat effect, an operator's whole six-run record would have looked the
    same whichever seat had been fitted, so the labels can be permuted over operators. Every
    one of the C(20,10) = 184,756 ways of choosing which ten operators take the reference label
    is enumerated, giving an exact two-sided p-value rather than a sampled one.
    """
    means = ops["operator_mean"].to_numpy()
    n_units = means.size
    n_ref = int((ops[GROUP] == REFERENCE).sum())
    observed = mean_difference(
        ops.loc[ops[GROUP] == REFERENCE, "operator_mean"].to_numpy(),
        ops.loc[ops[GROUP] == COMPARATOR, "operator_mean"].to_numpy(),
    )
    grand_total = means.sum()

    index = np.arange(n_units)
    assignments = np.fromiter(
        (means[list(combo)].sum() for combo in combinations(index, n_ref)),
        dtype=float,
    )
    n_comp = n_units - n_ref
    diffs = assignments / n_ref - (grand_total - assignments) / n_comp

    # Tolerance guards against ties being missed by floating point comparison.
    n_extreme = int(np.sum(np.abs(diffs) >= abs(observed) - 1e-12))
    return {
        "observed": observed,
        "p_value": n_extreme / diffs.size,
        "n_assignments": int(diffs.size),
        "n_extreme": n_extreme,
    }


def naive_row_level(runs):
    """Two-sample Welch t-test over all 120 individual runs. Illustrative contrast only.

    This is reported to show what the repeated runs would appear to buy if they were counted as
    independent observations. It is not valid inference for this study.
    """
    ref = runs.loc[runs[GROUP] == REFERENCE, OUTCOME].to_numpy()
    comp = runs.loc[runs[GROUP] == COMPARATOR, OUTCOME].to_numpy()
    result = stats.ttest_ind(ref, comp, equal_var=False)
    v_ref = ref.var(ddof=1) / ref.size
    v_comp = comp.var(ddof=1) / comp.size
    se = np.sqrt(v_ref + v_comp)
    # Welch-Satterthwaite degrees of freedom, computed here because this scipy version
    # does not return them on the test result.
    dof = (v_ref + v_comp) ** 2 / (
        v_ref ** 2 / (ref.size - 1) + v_comp ** 2 / (comp.size - 1)
    )
    crit = stats.t.ppf(1 - (1 - CI_LEVEL) / 2, dof)
    diff = float(ref.mean() - comp.mean())
    return {
        "estimate": diff,
        "se": float(se),
        "t": float(result.statistic),
        "dof": float(dof),
        "p_value": float(result.pvalue),
        "ci_low": diff - crit * se,
        "ci_high": diff + crit * se,
        "n_rows_ref": int(ref.size),
        "n_rows_comp": int(comp.size),
    }


def variance_components(runs, ops):
    """Descriptive spread between operators and between runs within an operator."""
    within_sd = runs.groupby(UNIT)[OUTCOME].std(ddof=1)
    between_sd = ops.groupby(GROUP)["operator_mean"].std(ddof=1)
    return {
        "mean_within_operator_sd": float(within_sd.mean()),
        "between_operator_sd": {g: float(v) for g, v in between_sd.items()},
    }


def main():
    runs = load_runs(DATA_FILE)
    ops = operator_table(runs)

    print("=" * 78)
    print("Whole-body vibration at the seat pan: air-suspension vs mechanical tractor seat")
    print("=" * 78)

    print("\n-- Design --")
    print(f"rows (field runs)            : {len(runs)}")
    print(f"operators (units of analysis): {ops.shape[0]}")
    print(f"runs per operator            : {sorted(ops['n_runs'].unique())}")
    for group, block in ops.groupby(GROUP):
        print(f"  {group:<15} operators = {block.shape[0]:>2}, rows = {int(block['n_runs'].sum()):>3}")

    print("\n-- Descriptives (m/s^2) --")
    for group, block in runs.groupby(GROUP):
        print(f"  {group:<15} row mean = {block[OUTCOME].mean():.3f}, "
              f"row sd = {block[OUTCOME].std(ddof=1):.3f}, "
              f"min = {block[OUTCOME].min():.2f}, max = {block[OUTCOME].max():.2f}")
    for group, block in ops.groupby(GROUP):
        print(f"  {group:<15} mean of operator means = {block['operator_mean'].mean():.3f}, "
              f"sd of operator means = {block['operator_mean'].std(ddof=1):.3f}")
    vc = variance_components(runs, ops)
    print(f"  mean within-operator sd across all operators = {vc['mean_within_operator_sd']:.3f}")
    for group, value in vc["between_operator_sd"].items():
        print(f"  between-operator sd ({group}) = {value:.3f}")

    print("\n-- PRIMARY: operator-level cluster bootstrap (self-written) --")
    boot = cluster_bootstrap(ops)
    print(f"  estimand   : mean {REFERENCE} minus mean {COMPARATOR} (m/s^2)")
    print(f"  n          : {boot['n_units_ref'] + boot['n_units_comp']} operators "
          f"({boot['n_units_ref']} {REFERENCE}, {boot['n_units_comp']} {COMPARATOR})")
    print(f"  estimate   : {boot['estimate']:.3f}")
    print(f"  bootstrap SE: {boot['boot_se']:.3f}")
    print(f"  {int(CI_LEVEL * 100)}% percentile CI: [{boot['ci_low']:.3f}, {boot['ci_high']:.3f}] "
          f"from {boot['n_boot']} operator-level resamples")

    print("\n-- PRIMARY: exact operator-level permutation test --")
    perm = cluster_permutation(ops)
    print(f"  observed difference : {perm['observed']:.3f}")
    print(f"  label assignments   : {perm['n_assignments']} (complete enumeration)")
    print(f"  as or more extreme  : {perm['n_extreme']}")
    print(f"  two-sided p-value   : {perm['p_value']:.6f}")

    print("\n-- ILLUSTRATIVE ONLY, NOT VALID INFERENCE: row-level two-sample test --")
    naive = naive_row_level(runs)
    print("  This treats each of the 120 runs as an independent observation. It is not.")
    print(f"  estimate : {naive['estimate']:.3f} "
          f"({naive['n_rows_ref']} vs {naive['n_rows_comp']} rows)")
    print(f"  SE       : {naive['se']:.3f}  (vs bootstrap SE {boot['boot_se']:.3f})")
    print(f"  Welch t  : {naive['t']:.2f} on {naive['dof']:.1f} df, p = {naive['p_value']:.3e}")
    print(f"  {int(CI_LEVEL * 100)}% CI  : [{naive['ci_low']:.3f}, {naive['ci_high']:.3f}]")
    print(f"  SE ratio (row-level / cluster) = {naive['se'] / boot['boot_se']:.2f}")

    print("\n-- Conclusion rests on the dependence-aware result above --")
    print(f"  n = {ops.shape[0]} operators; the row-level test is contrast only.")
    print("=" * 78)


if __name__ == "__main__":
    main()
