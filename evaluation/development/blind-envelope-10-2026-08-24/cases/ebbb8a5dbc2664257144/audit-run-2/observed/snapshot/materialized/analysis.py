"""Thermal liner comparison: heat-strain outcomes in structural firefighting turnout coats.

Compares the current service-issue liner against the candidate lighter liner on the four
heat-strain outcomes declared in the study protocol, in the declared order:

    1. peak_core_temp_c       peak core body temperature (degrees Celsius)
    2. peak_heart_rate_bpm    peak heart rate (beats per minute)
    3. sweat_loss_l           total sweat loss (litres)
    4. exhaustion_time_min    time to voluntary exhaustion (minutes)

Each outcome is compared with an independent-samples two-sided Student t-test and judged
against the conventional 0.05 threshold. Each comparison is written out as its own step.

Run from the project root:

    python analysis.py
"""

import csv
import os
from statistics import mean, stdev

from scipy import stats

ALPHA = 0.05
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "heat_strain.csv")


# ---------------------------------------------------------------------------
# Load the data
# ---------------------------------------------------------------------------

rows = []
with open(DATA_FILE, newline="", encoding="utf-8") as handle:
    for row in csv.DictReader(handle):
        rows.append(row)

current_rows = [row for row in rows if row["liner_group"] == "liner_current"]
candidate_rows = [row for row in rows if row["liner_group"] == "liner_candidate"]

print("Thermal liner comparison: heat-strain outcomes")
print("=" * 62)
print(f"Data file            : {os.path.basename(DATA_FILE)}")
print(f"Firefighters (rows)  : {len(rows)}")
print(f"liner_current  n     : {len(current_rows)}")
print(f"liner_candidate n    : {len(candidate_rows)}")
print(f"Significance threshold: alpha = {ALPHA}")
print("Test: independent-samples two-sided Student t-test")
print()


# ---------------------------------------------------------------------------
# Declared outcome 1 of 4: peak core body temperature (degrees Celsius)
# ---------------------------------------------------------------------------

print("-" * 62)
print("Outcome 1 of 4: peak_core_temp_c (peak core body temperature, degC)")
print("-" * 62)

temp_current = [float(row["peak_core_temp_c"]) for row in current_rows]
temp_candidate = [float(row["peak_core_temp_c"]) for row in candidate_rows]

temp_current_mean = mean(temp_current)
temp_current_sd = stdev(temp_current)
temp_candidate_mean = mean(temp_candidate)
temp_candidate_sd = stdev(temp_candidate)
temp_difference = temp_candidate_mean - temp_current_mean

temp_t, temp_p = stats.ttest_ind(temp_current, temp_candidate)
temp_verdict = "SIGNIFICANT" if temp_p < ALPHA else "NOT SIGNIFICANT"

print(f"liner_current   n = {len(temp_current):2d}  mean = {temp_current_mean:.3f}  SD = {temp_current_sd:.3f}")
print(f"liner_candidate n = {len(temp_candidate):2d}  mean = {temp_candidate_mean:.3f}  SD = {temp_candidate_sd:.3f}")
print(f"difference (candidate - current) = {temp_difference:+.3f} degC")
print(f"t = {temp_t:.3f}   p = {temp_p:.4f}")
print(f"Verdict at alpha = {ALPHA}: {temp_verdict}")
print()


# ---------------------------------------------------------------------------
# Declared outcome 2 of 4: peak heart rate (beats per minute)
# ---------------------------------------------------------------------------

print("-" * 62)
print("Outcome 2 of 4: peak_heart_rate_bpm (peak heart rate, bpm)")
print("-" * 62)

hr_current = [float(row["peak_heart_rate_bpm"]) for row in current_rows]
hr_candidate = [float(row["peak_heart_rate_bpm"]) for row in candidate_rows]

hr_current_mean = mean(hr_current)
hr_current_sd = stdev(hr_current)
hr_candidate_mean = mean(hr_candidate)
hr_candidate_sd = stdev(hr_candidate)
hr_difference = hr_candidate_mean - hr_current_mean

hr_t, hr_p = stats.ttest_ind(hr_current, hr_candidate)
hr_verdict = "SIGNIFICANT" if hr_p < ALPHA else "NOT SIGNIFICANT"

print(f"liner_current   n = {len(hr_current):2d}  mean = {hr_current_mean:.3f}  SD = {hr_current_sd:.3f}")
print(f"liner_candidate n = {len(hr_candidate):2d}  mean = {hr_candidate_mean:.3f}  SD = {hr_candidate_sd:.3f}")
print(f"difference (candidate - current) = {hr_difference:+.3f} bpm")
print(f"t = {hr_t:.3f}   p = {hr_p:.4f}")
print(f"Verdict at alpha = {ALPHA}: {hr_verdict}")
print()


# ---------------------------------------------------------------------------
# Declared outcome 3 of 4: total sweat loss (litres)
# ---------------------------------------------------------------------------

print("-" * 62)
print("Outcome 3 of 4: sweat_loss_l (total sweat loss, litres)")
print("-" * 62)

sweat_current = [float(row["sweat_loss_l"]) for row in current_rows]
sweat_candidate = [float(row["sweat_loss_l"]) for row in candidate_rows]

sweat_current_mean = mean(sweat_current)
sweat_current_sd = stdev(sweat_current)
sweat_candidate_mean = mean(sweat_candidate)
sweat_candidate_sd = stdev(sweat_candidate)
sweat_difference = sweat_candidate_mean - sweat_current_mean

sweat_t, sweat_p = stats.ttest_ind(sweat_current, sweat_candidate)
sweat_verdict = "SIGNIFICANT" if sweat_p < ALPHA else "NOT SIGNIFICANT"

print(f"liner_current   n = {len(sweat_current):2d}  mean = {sweat_current_mean:.3f}  SD = {sweat_current_sd:.3f}")
print(f"liner_candidate n = {len(sweat_candidate):2d}  mean = {sweat_candidate_mean:.3f}  SD = {sweat_candidate_sd:.3f}")
print(f"difference (candidate - current) = {sweat_difference:+.3f} L")
print(f"t = {sweat_t:.3f}   p = {sweat_p:.4f}")
print(f"Verdict at alpha = {ALPHA}: {sweat_verdict}")
print()


# ---------------------------------------------------------------------------
# Declared outcome 4 of 4: time to voluntary exhaustion (minutes)
# ---------------------------------------------------------------------------

print("-" * 62)
print("Outcome 4 of 4: exhaustion_time_min (time to voluntary exhaustion, min)")
print("-" * 62)

exhaustion_current = [float(row["exhaustion_time_min"]) for row in current_rows]
exhaustion_candidate = [float(row["exhaustion_time_min"]) for row in candidate_rows]

exhaustion_current_mean = mean(exhaustion_current)
exhaustion_current_sd = stdev(exhaustion_current)
exhaustion_candidate_mean = mean(exhaustion_candidate)
exhaustion_candidate_sd = stdev(exhaustion_candidate)
exhaustion_difference = exhaustion_candidate_mean - exhaustion_current_mean

exhaustion_t, exhaustion_p = stats.ttest_ind(exhaustion_current, exhaustion_candidate)
exhaustion_verdict = "SIGNIFICANT" if exhaustion_p < ALPHA else "NOT SIGNIFICANT"

print(f"liner_current   n = {len(exhaustion_current):2d}  mean = {exhaustion_current_mean:.3f}  SD = {exhaustion_current_sd:.3f}")
print(f"liner_candidate n = {len(exhaustion_candidate):2d}  mean = {exhaustion_candidate_mean:.3f}  SD = {exhaustion_candidate_sd:.3f}")
print(f"difference (candidate - current) = {exhaustion_difference:+.3f} min")
print(f"t = {exhaustion_t:.3f}   p = {exhaustion_p:.4f}")
print(f"Verdict at alpha = {ALPHA}: {exhaustion_verdict}")
print()


# ---------------------------------------------------------------------------
# Collected results in declared order
# ---------------------------------------------------------------------------

print("=" * 62)
print("Summary of the four declared outcomes, in declared order")
print("=" * 62)
print(f"1. peak_core_temp_c       p = {temp_p:.4f}   {temp_verdict}")
print(f"2. peak_heart_rate_bpm    p = {hr_p:.4f}   {hr_verdict}")
print(f"3. sweat_loss_l           p = {sweat_p:.4f}   {sweat_verdict}")
print(f"4. exhaustion_time_min    p = {exhaustion_p:.4f}   {exhaustion_verdict}")
