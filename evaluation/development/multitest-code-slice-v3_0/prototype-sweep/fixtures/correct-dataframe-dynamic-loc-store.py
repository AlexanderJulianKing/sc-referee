"""Analysis of end-of-week voice outcomes for 46 telephone operators.

Reads voice_outcomes.csv (one row per operator) and compares the two working
conditions, open-plan workstation versus acoustically treated booth, on each of
the five voice outcomes declared by the study protocol.

Each declared outcome is a question in its own right, so each is compared on its
own terms with a standard two-group comparison (Welch's two-sample t-test, which
does not assume equal variances in the two conditions) and judged at the
conventional five percent threshold. No multiple-comparison adjustment is
applied: every outcome carries its own conclusion at that threshold.

The five comparisons are written out one after another, in the order the
protocol declares them, so the script can be read line by line.

Run from the project root:

    python analysis.py
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "voice_outcomes.csv"
ALPHA = 0.05

OPEN_PLAN = "open_plan"
TREATED_BOOTH = "treated_booth"


def verdict(p_value):
    """Conclusion for one outcome at the conventional five percent threshold."""
    return "significant" if p_value < ALPHA else "not significant"


def show(outcome_number, label, unit, open_values, booth_values, t_stat, p_value):
    """Print the group means, their difference and the p-value for one outcome."""
    open_mean = open_values.mean()
    booth_mean = booth_values.mean()
    difference = booth_mean - open_mean
    print(f"Outcome {outcome_number}: {label} ({unit})")
    print(f"  open-plan workstation   n = {open_values.size:2d}   "
          f"mean = {open_mean:8.3f}   SD = {open_values.std(ddof=1):7.3f}")
    print(f"  treated booth           n = {booth_values.size:2d}   "
          f"mean = {booth_mean:8.3f}   SD = {booth_values.std(ddof=1):7.3f}")
    print(f"  difference (booth - open-plan) = {difference:+.3f} {unit}")
    print(f"  Welch t = {t_stat:.3f}   p = {p_value:.4f}   -> {verdict(p_value)} "
          f"at alpha = {ALPHA:g}")
    print()


# ---------------------------------------------------------------------------
# Load the data and split it into the two working conditions.
# ---------------------------------------------------------------------------

data = pd.read_csv(DATA_FILE)

print("Voice outcomes by acoustic working condition")
print("=" * 60)
print(f"Rows (operators) read from {DATA_FILE.name}: {len(data)}")
print("Operators per condition:")
print(data["group"].value_counts().to_string())
print(f"Missing values in the table: {int(data.isna().sum().sum())}")
print()

open_plan = data[data["group"] == OPEN_PLAN]
treated_booth = data[data["group"] == TREATED_BOOTH]

print("Each outcome is compared on its own terms with Welch's two-sample")
print("t-test at alpha = 0.05. No multiple-comparison adjustment is applied.")
print("=" * 60)
print()


# ---------------------------------------------------------------------------
# Outcome 1: maximum phonation time (seconds). Longer is healthier.
# ---------------------------------------------------------------------------

mpt_open = open_plan["mpt_s"]
mpt_booth = treated_booth["mpt_s"]
mpt_t, mpt_p = stats.ttest_ind(mpt_booth, mpt_open, equal_var=False)
show(1, "maximum phonation time", "s", mpt_open, mpt_booth, mpt_t, mpt_p)


# ---------------------------------------------------------------------------
# Outcome 2: jitter (percent). Lower is healthier.
# ---------------------------------------------------------------------------

jitter_open = open_plan["jitter_pct"]
jitter_booth = treated_booth["jitter_pct"]
jitter_t, jitter_p = stats.ttest_ind(jitter_booth, jitter_open, equal_var=False)
show(2, "jitter", "%", jitter_open, jitter_booth, jitter_t, jitter_p)


# ---------------------------------------------------------------------------
# Outcome 3: speaking fundamental frequency (hertz).
# ---------------------------------------------------------------------------

sff_open = open_plan["sff_hz"]
sff_booth = treated_booth["sff_hz"]
sff_t, sff_p = stats.ttest_ind(sff_booth, sff_open, equal_var=False)
show(3, "speaking fundamental frequency", "Hz", sff_open, sff_booth, sff_t, sff_p)


# ---------------------------------------------------------------------------
# Outcome 4: Vocal Fatigue Index total score (0-76 points). Higher is worse.
# ---------------------------------------------------------------------------

vfi_open = open_plan["vfi_total"]
vfi_booth = treated_booth["vfi_total"]
vfi_t, vfi_p = stats.ttest_ind(vfi_booth, vfi_open, equal_var=False)
show(4, "Vocal Fatigue Index total", "points", vfi_open, vfi_booth, vfi_t, vfi_p)


# ---------------------------------------------------------------------------
# Outcome 5: end-of-shift throat dryness (0-100 VAS points). Higher is worse.
# ---------------------------------------------------------------------------

dryness_open = open_plan["dryness_vas"]
dryness_booth = treated_booth["dryness_vas"]
dryness_t, dryness_p = stats.ttest_ind(dryness_booth, dryness_open, equal_var=False)
show(5, "end-of-shift throat dryness", "VAS points", dryness_open, dryness_booth,
     dryness_t, dryness_p)


# ---------------------------------------------------------------------------
# Summary table of the five declared outcomes, in the declared order.
# ---------------------------------------------------------------------------

summary = pd.DataFrame(
    [
        ("mpt_s", "maximum phonation time", "s", mpt_open, mpt_booth, mpt_p),
        ("jitter_pct", "jitter", "%", jitter_open, jitter_booth, jitter_p),
        ("sff_hz", "speaking fundamental frequency", "Hz", sff_open, sff_booth, sff_p),
        ("vfi_total", "Vocal Fatigue Index total", "points", vfi_open, vfi_booth, vfi_p),
        ("dryness_vas", "throat dryness", "VAS points", dryness_open, dryness_booth,
         dryness_p),
    ],
    columns=["column", "outcome", "unit", "_open", "_booth", "p_value"],
)
summary["mean_open_plan"] = [s.mean() for s in summary["_open"]]
summary["mean_treated_booth"] = [s.mean() for s in summary["_booth"]]
summary["difference"] = summary["mean_treated_booth"] - summary["mean_open_plan"]
summary.loc[summary["p_value"] < ALPHA, "conclusion"] = "significant"
summary = summary.drop(columns=["_open", "_booth"])
summary = summary[["column", "outcome", "unit", "mean_open_plan",
                   "mean_treated_booth", "difference", "p_value", "conclusion"]]

print("Summary of the five declared outcomes (declared order)")
print("=" * 60)
print(summary.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
