"""Analysis for the tadpole live-food supplement study.

Study question
--------------
Does adding live daphnia to the standard flake diet increase snout-vent length
of common frog tadpoles after six weeks of rearing?

Design and unit of analysis
---------------------------
The diet was assigned to rearing bins, not to individual tadpoles.  There are
16 bins, 8 per diet, and 12 tadpoles were measured from each bin.  The bin is
therefore the independent experimental unit, and the group comparison is run on
the 16 per-bin mean lengths in `bin_summary.csv` -- one value per treated unit,
8 per diet.  The reported sample size is the number of bins.

`tadpole_measurements.csv` holds 12 rows per bin.  Those 12 rows are repeated
measures from inside one bin, not 12 separately treated units, so this file is
used here only for description: counting tadpoles, checking that the summary
file matches it, and reporting the spread of lengths within bins.  No group
comparison is run on the tadpole-level rows.

Run with:  python3 analysis.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
RAW_PATH = HERE / "tadpole_measurements.csv"
SUMMARY_PATH = HERE / "bin_summary.csv"

STANDARD = "standard_flake"
SUPPLEMENT = "flake_plus_daphnia"
UNIT_COL = "bin_label"
GROUP_COL = "diet_treatment"
RESPONSE_COL = "snout_vent_length_mm"
BIN_MEAN_COL = "mean_snout_vent_length_mm"


def load_data():
    """Load the raw tadpole file and the per-bin summary file."""
    raw = pd.read_csv(RAW_PATH)
    summary = pd.read_csv(SUMMARY_PATH)
    return raw, summary


def check_files_agree(raw, summary):
    """Confirm the summary file is the per-bin average of the raw file.

    This is a consistency check on the inputs, not a hypothesis test.
    """
    recomputed = (
        raw.groupby([UNIT_COL, GROUP_COL])[RESPONSE_COL]
        .agg(["mean", "size"])
        .reset_index()
        .rename(columns={"mean": "recomputed_mean", "size": "recomputed_n"})
    )
    merged = summary.merge(recomputed, on=[UNIT_COL, GROUP_COL], how="outer", indicator=True)

    problems = []
    if not (merged["_merge"] == "both").all():
        problems.append("bin_label/diet_treatment pairs do not match between the two files")
    if not (merged["n_tadpoles_measured"] == merged["recomputed_n"]).all():
        problems.append("n_tadpoles_measured does not match the raw row counts")
    mean_gap = (merged[BIN_MEAN_COL] - merged["recomputed_mean"]).abs().max()
    if mean_gap > 5e-5:
        problems.append(f"stored bin means differ from recomputed means by up to {mean_gap:.6f} mm")

    return {
        "n_bins_raw": raw[UNIT_COL].nunique(),
        "n_bins_summary": summary[UNIT_COL].nunique(),
        "summary_rows": len(summary),
        "max_mean_discrepancy_mm": float(mean_gap),
        "problems": problems,
    }


def describe_raw(raw):
    """Descriptive numbers from the tadpole-level file. No testing here."""
    per_bin = raw.groupby(UNIT_COL)[RESPONSE_COL]
    within_bin_sd = per_bin.std(ddof=1)
    rows_per_bin = per_bin.size()
    return {
        "n_tadpoles_total": int(len(raw)),
        "n_bins": int(raw[UNIT_COL].nunique()),
        "rows_per_bin_min": int(rows_per_bin.min()),
        "rows_per_bin_max": int(rows_per_bin.max()),
        "length_min_mm": float(raw[RESPONSE_COL].min()),
        "length_max_mm": float(raw[RESPONSE_COL].max()),
        "within_bin_sd_mean_mm": float(within_bin_sd.mean()),
        "within_bin_sd_min_mm": float(within_bin_sd.min()),
        "within_bin_sd_max_mm": float(within_bin_sd.max()),
        "water_temp_min_c": float(raw["water_temp_c"].min()),
        "water_temp_max_c": float(raw["water_temp_c"].max()),
        "tadpoles_per_diet": raw.groupby(GROUP_COL)[UNIT_COL].size().to_dict(),
    }


def describe_groups(summary):
    """Group-level descriptives computed from the 16 per-bin means."""
    out = {}
    for diet in (STANDARD, SUPPLEMENT):
        values = summary.loc[summary[GROUP_COL] == diet, BIN_MEAN_COL].to_numpy(dtype=float)
        out[diet] = {
            "n_bins": int(values.size),
            "mean_mm": float(values.mean()),
            "sd_mm": float(values.std(ddof=1)),
            "se_mm": float(values.std(ddof=1) / np.sqrt(values.size)),
            "min_mm": float(values.min()),
            "max_mm": float(values.max()),
            "values": values,
        }
    return out


def compare_diets(groups):
    """Independent two-sample comparison of the two diets.

    The two samples are the 8 standard-flake bin means and the 8
    supplemented bin means.  Each bin contributes exactly one value, so the
    observations entering the test are independent of each other.
    Welch's t-test is the primary test because it does not assume the two
    groups share a variance; the equal-variance (Student) version is reported
    alongside it as a sensitivity check.
    """
    a = groups[SUPPLEMENT]["values"]
    b = groups[STANDARD]["values"]
    n_a, n_b = a.size, b.size

    welch_t, welch_p = stats.ttest_ind(a, b, equal_var=False)
    student_t, student_p = stats.ttest_ind(a, b, equal_var=True)

    var_a = a.var(ddof=1)
    var_b = b.var(ddof=1)
    se_diff = np.sqrt(var_a / n_a + var_b / n_b)
    welch_df = (var_a / n_a + var_b / n_b) ** 2 / (
        (var_a / n_a) ** 2 / (n_a - 1) + (var_b / n_b) ** 2 / (n_b - 1)
    )
    diff = a.mean() - b.mean()
    crit = stats.t.ppf(0.975, welch_df)

    pooled_sd = np.sqrt(((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2))
    cohens_d = diff / pooled_sd
    hedges_g = cohens_d * (1 - 3 / (4 * (n_a + n_b) - 9))

    mw_u, mw_p = stats.mannwhitneyu(a, b, alternative="two-sided")

    return {
        "n_bins_supplement": int(n_a),
        "n_bins_standard": int(n_b),
        "n_bins_total": int(n_a + n_b),
        "diff_mm": float(diff),
        "se_diff_mm": float(se_diff),
        "welch_t": float(welch_t),
        "welch_df": float(welch_df),
        "welch_p": float(welch_p),
        "ci_low_mm": float(diff - crit * se_diff),
        "ci_high_mm": float(diff + crit * se_diff),
        "student_t": float(student_t),
        "student_df": int(n_a + n_b - 2),
        "student_p": float(student_p),
        "pooled_sd_mm": float(pooled_sd),
        "cohens_d": float(cohens_d),
        "hedges_g": float(hedges_g),
        "mannwhitney_u": float(mw_u),
        "mannwhitney_p": float(mw_p),
    }


def main():
    raw, summary = load_data()

    checks = check_files_agree(raw, summary)
    raw_desc = describe_raw(raw)
    groups = describe_groups(summary)
    test = compare_diets(groups)

    print("=" * 72)
    print("Live-food supplement and tadpole growth: analysis output")
    print("=" * 72)

    print("\n--- Input files ---")
    print(f"raw file    : {RAW_PATH.name}  ({len(raw)} rows, one per measured tadpole)")
    print(f"summary file: {SUMMARY_PATH.name}  ({len(summary)} rows, one per rearing bin)")

    print("\n--- Consistency check (summary vs raw) ---")
    print(f"bins in raw file              : {checks['n_bins_raw']}")
    print(f"bins in summary file          : {checks['n_bins_summary']}")
    print(f"largest bin-mean discrepancy  : {checks['max_mean_discrepancy_mm']:.6f} mm")
    if checks["problems"]:
        for problem in checks["problems"]:
            print(f"PROBLEM: {problem}")
    else:
        print("summary file reproduces the per-bin means and counts of the raw file")

    print("\n--- Descriptives from the raw file (no testing on these rows) ---")
    print(f"tadpoles measured             : {raw_desc['n_tadpoles_total']}")
    print(f"bins                          : {raw_desc['n_bins']}")
    print(
        "tadpoles per bin              : "
        f"{raw_desc['rows_per_bin_min']} to {raw_desc['rows_per_bin_max']}"
    )
    for diet, count in sorted(raw_desc["tadpoles_per_diet"].items()):
        print(f"  tadpoles measured, {diet:<19}: {count}")
    print(
        "snout-vent length range       : "
        f"{raw_desc['length_min_mm']:.2f} to {raw_desc['length_max_mm']:.2f} mm"
    )
    print(
        "within-bin SD of length       : "
        f"mean {raw_desc['within_bin_sd_mean_mm']:.3f} mm "
        f"(range {raw_desc['within_bin_sd_min_mm']:.3f} to {raw_desc['within_bin_sd_max_mm']:.3f} mm)"
    )
    print(
        "water temperature range       : "
        f"{raw_desc['water_temp_min_c']:.1f} to {raw_desc['water_temp_max_c']:.1f} C"
    )

    print("\n--- Group descriptives (unit of analysis = rearing bin) ---")
    for diet in (STANDARD, SUPPLEMENT):
        g = groups[diet]
        print(
            f"{diet:<19} n_bins={g['n_bins']}  "
            f"mean={g['mean_mm']:.4f} mm  SD={g['sd_mm']:.4f}  SE={g['se_mm']:.4f}  "
            f"range {g['min_mm']:.4f} to {g['max_mm']:.4f} mm"
        )

    print("\n--- Primary comparison: Welch independent two-sample t-test ---")
    print("test input: the 16 per-bin mean lengths (8 bins per diet), one value per bin")
    print(
        f"sample size: n = {test['n_bins_total']} bins "
        f"({test['n_bins_supplement']} supplemented, {test['n_bins_standard']} standard)"
    )
    print(
        "difference (supplement - standard): "
        f"{test['diff_mm']:.4f} mm  (SE {test['se_diff_mm']:.4f} mm)"
    )
    print(f"95% CI for the difference        : [{test['ci_low_mm']:.4f}, {test['ci_high_mm']:.4f}] mm")
    print(f"t = {test['welch_t']:.4f}, df = {test['welch_df']:.3f}, p = {test['welch_p']:.4f}")
    print(f"Hedges g = {test['hedges_g']:.4f} (Cohen d = {test['cohens_d']:.4f})")

    print("\n--- Sensitivity checks (same 16 bin-level values) ---")
    print(
        f"Student equal-variance t-test : t = {test['student_t']:.4f}, "
        f"df = {test['student_df']}, p = {test['student_p']:.4f}"
    )
    print(
        f"Mann-Whitney U test           : U = {test['mannwhitney_u']:.1f}, "
        f"p = {test['mannwhitney_p']:.4f}"
    )
    print("=" * 72)


if __name__ == "__main__":
    main()
