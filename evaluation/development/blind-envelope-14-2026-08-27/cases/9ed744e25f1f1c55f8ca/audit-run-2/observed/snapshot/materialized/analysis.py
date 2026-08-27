"""Steeping regime trial: compare two steeping regimes across five declared malt-quality outcomes.

Reads malting_lots.csv (48 micro-malting lots, 24 per steeping regime) and runs one two-sample
comparison per declared outcome. Each outcome is its own scientific question and is judged on its
own p-value against the 0.05 threshold.
"""

import pandas as pd
from scipy import stats

ALPHA = 0.05

lots = pd.read_csv("malting_lots.csv")

two_step = lots[lots["steep_regime"] == "two_step"]
extended_air_rest = lots[lots["steep_regime"] == "extended_air_rest"]

print("Steeping regime trial: two_step vs extended_air_rest")
print("Lots per regime: two_step = %d, extended_air_rest = %d" % (len(two_step), len(extended_air_rest)))
print("Significance threshold: p < %.2f" % ALPHA)
print()


# ---------------------------------------------------------------------------
# Step 1 of 5 - Declared outcome 1: friability (percent)
# ---------------------------------------------------------------------------
friability_two_step = two_step["friability_pct"]
friability_extended = extended_air_rest["friability_pct"]

friability_mean_two_step = friability_two_step.mean()
friability_mean_extended = friability_extended.mean()
friability_difference = friability_mean_extended - friability_mean_two_step

friability_t, friability_p = stats.ttest_ind(
    friability_extended, friability_two_step, equal_var=False
)
friability_verdict = "significant" if friability_p < ALPHA else "not significant"

print("Step 1 - friability_pct (percent)")
print("  mean, two_step          : %.2f" % friability_mean_two_step)
print("  mean, extended_air_rest : %.2f" % friability_mean_extended)
print("  difference (extended - two_step): %+.2f" % friability_difference)
print("  Welch t = %.3f, p = %.4f" % (friability_t, friability_p))
print("  verdict: %s at p < %.2f" % (friability_verdict, ALPHA))
print()


# ---------------------------------------------------------------------------
# Step 2 of 5 - Declared outcome 2: fine extract, dry basis (percent)
# ---------------------------------------------------------------------------
fine_extract_two_step = two_step["fine_extract_pct_dry"]
fine_extract_extended = extended_air_rest["fine_extract_pct_dry"]

fine_extract_mean_two_step = fine_extract_two_step.mean()
fine_extract_mean_extended = fine_extract_extended.mean()
fine_extract_difference = fine_extract_mean_extended - fine_extract_mean_two_step

fine_extract_t, fine_extract_p = stats.ttest_ind(
    fine_extract_extended, fine_extract_two_step, equal_var=False
)
fine_extract_verdict = "significant" if fine_extract_p < ALPHA else "not significant"

print("Step 2 - fine_extract_pct_dry (percent, dry basis)")
print("  mean, two_step          : %.2f" % fine_extract_mean_two_step)
print("  mean, extended_air_rest : %.2f" % fine_extract_mean_extended)
print("  difference (extended - two_step): %+.2f" % fine_extract_difference)
print("  Welch t = %.3f, p = %.4f" % (fine_extract_t, fine_extract_p))
print("  verdict: %s at p < %.2f" % (fine_extract_verdict, ALPHA))
print()


# ---------------------------------------------------------------------------
# Step 3 of 5 - Declared outcome 3: free amino nitrogen (mg/L)
# ---------------------------------------------------------------------------
fan_two_step = two_step["fan_mg_per_l"]
fan_extended = extended_air_rest["fan_mg_per_l"]

fan_mean_two_step = fan_two_step.mean()
fan_mean_extended = fan_extended.mean()
fan_difference = fan_mean_extended - fan_mean_two_step

fan_t, fan_p = stats.ttest_ind(fan_extended, fan_two_step, equal_var=False)
fan_verdict = "significant" if fan_p < ALPHA else "not significant"

print("Step 3 - fan_mg_per_l (mg/L)")
print("  mean, two_step          : %.2f" % fan_mean_two_step)
print("  mean, extended_air_rest : %.2f" % fan_mean_extended)
print("  difference (extended - two_step): %+.2f" % fan_difference)
print("  Welch t = %.3f, p = %.4f" % (fan_t, fan_p))
print("  verdict: %s at p < %.2f" % (fan_verdict, ALPHA))
print()


# ---------------------------------------------------------------------------
# Step 4 of 5 - Declared outcome 4: diastatic power (degrees Windisch-Kolbach)
# ---------------------------------------------------------------------------
diastatic_power_two_step = two_step["diastatic_power_wk"]
diastatic_power_extended = extended_air_rest["diastatic_power_wk"]

diastatic_power_mean_two_step = diastatic_power_two_step.mean()
diastatic_power_mean_extended = diastatic_power_extended.mean()
diastatic_power_difference = diastatic_power_mean_extended - diastatic_power_mean_two_step

diastatic_power_t, diastatic_power_p = stats.ttest_ind(
    diastatic_power_extended, diastatic_power_two_step, equal_var=False
)
diastatic_power_verdict = "significant" if diastatic_power_p < ALPHA else "not significant"

print("Step 4 - diastatic_power_wk (degrees Windisch-Kolbach)")
print("  mean, two_step          : %.2f" % diastatic_power_mean_two_step)
print("  mean, extended_air_rest : %.2f" % diastatic_power_mean_extended)
print("  difference (extended - two_step): %+.2f" % diastatic_power_difference)
print("  Welch t = %.3f, p = %.4f" % (diastatic_power_t, diastatic_power_p))
print("  verdict: %s at p < %.2f" % (diastatic_power_verdict, ALPHA))
print()


# ---------------------------------------------------------------------------
# Step 5 of 5 - Declared outcome 5: beta-glucan (mg/L)
# ---------------------------------------------------------------------------
beta_glucan_two_step = two_step["beta_glucan_mg_per_l"]
beta_glucan_extended = extended_air_rest["beta_glucan_mg_per_l"]

beta_glucan_mean_two_step = beta_glucan_two_step.mean()
beta_glucan_mean_extended = beta_glucan_extended.mean()
beta_glucan_difference = beta_glucan_mean_extended - beta_glucan_mean_two_step

beta_glucan_t, beta_glucan_p = stats.ttest_ind(
    beta_glucan_extended, beta_glucan_two_step, equal_var=False
)
beta_glucan_verdict = "significant" if beta_glucan_p < ALPHA else "not significant"

print("Step 5 - beta_glucan_mg_per_l (mg/L)")
print("  mean, two_step          : %.2f" % beta_glucan_mean_two_step)
print("  mean, extended_air_rest : %.2f" % beta_glucan_mean_extended)
print("  difference (extended - two_step): %+.2f" % beta_glucan_difference)
print("  Welch t = %.3f, p = %.4f" % (beta_glucan_t, beta_glucan_p))
print("  verdict: %s at p < %.2f" % (beta_glucan_verdict, ALPHA))
print()


# ---------------------------------------------------------------------------
# Summary of the five declared outcomes, in the declared order
# ---------------------------------------------------------------------------
print("Summary (declared order)")
print("  1. friability_pct          p = %.4f  %s" % (friability_p, friability_verdict))
print("  2. fine_extract_pct_dry    p = %.4f  %s" % (fine_extract_p, fine_extract_verdict))
print("  3. fan_mg_per_l            p = %.4f  %s" % (fan_p, fan_verdict))
print("  4. diastatic_power_wk      p = %.4f  %s" % (diastatic_power_p, diastatic_power_verdict))
print("  5. beta_glucan_mg_per_l    p = %.4f  %s" % (beta_glucan_p, beta_glucan_verdict))
