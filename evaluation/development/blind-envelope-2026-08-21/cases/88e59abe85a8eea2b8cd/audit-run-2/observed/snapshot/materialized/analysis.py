"""Soil respiration analysis: warmed vs ambient grassland plots.

Compares soil CO2 efflux between infrared-heated and control plots
using the individual collar readings.
"""

import pandas as pd
from scipy import stats

# Read the survey file (60 collar readings, 10 plots).
df = pd.read_csv("soil_respiration.csv")

# Split the collar readings by treatment.
warmed = df.loc[df["warming_status"] == "warmed", "co2_efflux"]
ambient = df.loc[df["warming_status"] == "ambient", "co2_efflux"]

# Two-sample t-test on the individual collar readings.
t_stat, p_value = stats.ttest_ind(warmed, ambient)

# Descriptive statistics for each condition.
print("Soil CO2 efflux (umol CO2 m-2 s-1)")
print(f"warmed : n = {len(warmed)}, mean = {warmed.mean():.3f}, sd = {warmed.std(ddof=1):.3f}")
print(f"ambient: n = {len(ambient)}, mean = {ambient.mean():.3f}, sd = {ambient.std(ddof=1):.3f}")
print(f"difference (warmed - ambient) = {warmed.mean() - ambient.mean():.3f}")

# Test result.
print(f"t = {t_stat:.3f}")
print(f"p = {p_value:.4f}")
print(f"df = {len(warmed) + len(ambient) - 2}")
