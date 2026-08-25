"""Shipyard respiratory health study.

Compares stainless-steel welders with unexposed machinists on the four outcomes
declared in the study protocol, in the declared order:

    1. fev1_litres    Forced expiratory volume in one second (litres)
    2. fvc_litres     Forced vital capacity (litres)
    3. feno_ppb       Fractional exhaled nitric oxide (parts per billion)
    4. crp_mg_per_l   Blood C-reactive protein (milligrams per litre)

Each declared outcome is a separate scientific question about welding fume and
is written out below as its own block.

Run from the project root:

    python analysis.py
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "shipyard_respiratory.csv"
ALPHA = 0.05


def verdict(p_value):
    """Decide one outcome against the conventional 0.05 threshold."""
    if p_value < ALPHA:
        return "SIGNIFICANT (p < 0.05)"
    return "not significant (p >= 0.05)"


# ---------------------------------------------------------------------------
# Load the study data and split it into the two exposure groups.
# ---------------------------------------------------------------------------

data = pd.read_csv(DATA_FILE)

welders = data[data["exposure_group"] == "welder"]
machinists = data[data["exposure_group"] == "machinist"]

print("Shipyard respiratory health study")
print("=" * 72)
print(f"Data file: {DATA_FILE.name}")
print(f"Workers examined: {len(data)}")
print(f"  welders    : {len(welders)}")
print(f"  machinists : {len(machinists)}")
print()

print("Per-group summary (mean and standard deviation)")
print("-" * 72)
print(f"{'outcome':<16}{'welder mean':>13}{'welder sd':>11}"
      f"{'machinist mean':>16}{'machinist sd':>14}")
for column in ["fev1_litres", "fvc_litres", "feno_ppb", "crp_mg_per_l"]:
    print(f"{column:<16}"
          f"{welders[column].mean():>13.2f}"
          f"{welders[column].std(ddof=1):>11.2f}"
          f"{machinists[column].mean():>16.2f}"
          f"{machinists[column].std(ddof=1):>14.2f}")
print()

print("Declared outcomes, tested in protocol order")
print("=" * 72)
print()


# ---------------------------------------------------------------------------
# Declared outcome 1 of 4: forced expiratory volume in one second (litres).
# ---------------------------------------------------------------------------

fev1_welder = welders["fev1_litres"]
fev1_machinist = machinists["fev1_litres"]

fev1_result = stats.ttest_ind(fev1_welder, fev1_machinist, equal_var=False)
fev1_p = fev1_result.pvalue

print("Outcome 1: fev1_litres (forced expiratory volume in one second, L)")
print(f"  welders    n = {len(fev1_welder):2d}   "
      f"mean = {fev1_welder.mean():.2f} L   "
      f"sd = {fev1_welder.std(ddof=1):.2f} L")
print(f"  machinists n = {len(fev1_machinist):2d}   "
      f"mean = {fev1_machinist.mean():.2f} L   "
      f"sd = {fev1_machinist.std(ddof=1):.2f} L")
print(f"  difference (welder - machinist) = "
      f"{fev1_welder.mean() - fev1_machinist.mean():+.2f} L")
print(f"  Welch two-sample t-test: t = {fev1_result.statistic:.3f}, "
      f"df = {fev1_result.df:.1f}, p = {fev1_p:.4f}")
print(f"  Verdict: {verdict(fev1_p)}")
print()


# ---------------------------------------------------------------------------
# Declared outcome 2 of 4: forced vital capacity (litres).
# ---------------------------------------------------------------------------

fvc_welder = welders["fvc_litres"]
fvc_machinist = machinists["fvc_litres"]

fvc_result = stats.ttest_ind(fvc_welder, fvc_machinist, equal_var=False)
fvc_p = fvc_result.pvalue

print("Outcome 2: fvc_litres (forced vital capacity, L)")
print(f"  welders    n = {len(fvc_welder):2d}   "
      f"mean = {fvc_welder.mean():.2f} L   "
      f"sd = {fvc_welder.std(ddof=1):.2f} L")
print(f"  machinists n = {len(fvc_machinist):2d}   "
      f"mean = {fvc_machinist.mean():.2f} L   "
      f"sd = {fvc_machinist.std(ddof=1):.2f} L")
print(f"  difference (welder - machinist) = "
      f"{fvc_welder.mean() - fvc_machinist.mean():+.2f} L")
print(f"  Welch two-sample t-test: t = {fvc_result.statistic:.3f}, "
      f"df = {fvc_result.df:.1f}, p = {fvc_p:.4f}")
print(f"  Verdict: {verdict(fvc_p)}")
print()


# ---------------------------------------------------------------------------
# Declared outcome 3 of 4: fractional exhaled nitric oxide (ppb).
# ---------------------------------------------------------------------------

feno_welder = welders["feno_ppb"]
feno_machinist = machinists["feno_ppb"]

feno_result = stats.ttest_ind(feno_welder, feno_machinist, equal_var=False)
feno_p = feno_result.pvalue

print("Outcome 3: feno_ppb (fractional exhaled nitric oxide, ppb)")
print(f"  welders    n = {len(feno_welder):2d}   "
      f"mean = {feno_welder.mean():.2f} ppb   "
      f"sd = {feno_welder.std(ddof=1):.2f} ppb")
print(f"  machinists n = {len(feno_machinist):2d}   "
      f"mean = {feno_machinist.mean():.2f} ppb   "
      f"sd = {feno_machinist.std(ddof=1):.2f} ppb")
print(f"  difference (welder - machinist) = "
      f"{feno_welder.mean() - feno_machinist.mean():+.2f} ppb")
print(f"  Welch two-sample t-test: t = {feno_result.statistic:.3f}, "
      f"df = {feno_result.df:.1f}, p = {feno_p:.4f}")
print(f"  Verdict: {verdict(feno_p)}")
print()


# ---------------------------------------------------------------------------
# Declared outcome 4 of 4: blood C-reactive protein (mg/L).
# ---------------------------------------------------------------------------

crp_welder = welders["crp_mg_per_l"]
crp_machinist = machinists["crp_mg_per_l"]

crp_result = stats.ttest_ind(crp_welder, crp_machinist, equal_var=False)
crp_p = crp_result.pvalue

print("Outcome 4: crp_mg_per_l (blood C-reactive protein, mg/L)")
print(f"  welders    n = {len(crp_welder):2d}   "
      f"mean = {crp_welder.mean():.2f} mg/L   "
      f"sd = {crp_welder.std(ddof=1):.2f} mg/L")
print(f"  machinists n = {len(crp_machinist):2d}   "
      f"mean = {crp_machinist.mean():.2f} mg/L   "
      f"sd = {crp_machinist.std(ddof=1):.2f} mg/L")
print(f"  difference (welder - machinist) = "
      f"{crp_welder.mean() - crp_machinist.mean():+.2f} mg/L")
print(f"  Welch two-sample t-test: t = {crp_result.statistic:.3f}, "
      f"df = {crp_result.df:.1f}, p = {crp_p:.4f}")
print(f"  Verdict: {verdict(crp_p)}")
print()


# ---------------------------------------------------------------------------
# Roll-up of the four declared verdicts, in protocol order.
# ---------------------------------------------------------------------------

print("Summary of declared outcomes")
print("-" * 72)
print(f"  1. fev1_litres   p = {fev1_p:.4f}   {verdict(fev1_p)}")
print(f"  2. fvc_litres    p = {fvc_p:.4f}   {verdict(fvc_p)}")
print(f"  3. feno_ppb      p = {feno_p:.4f}   {verdict(feno_p)}")
print(f"  4. crp_mg_per_l  p = {crp_p:.4f}   {verdict(crp_p)}")
