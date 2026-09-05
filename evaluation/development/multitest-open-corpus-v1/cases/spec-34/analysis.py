"""Blood-metabolite markers separating pasture-finished from grain-finished cattle.

128 archived animals, 64 pasture and 64 grain. The panel is exploratory, so the
animals were split into a discovery set and a held-out validation set before any
marker was looked at. The split is recorded in the CSV and is used here exactly as
recorded; nothing below reassigns it.

Two stages:
  1. Discovery. All six markers are tested. This is screening. Nothing here is a
     finding, and discovery p-values are not corrected because they are not being
     used to claim anything.
  2. Validation. Only the shortlisted markers are tested, in the held-out animals,
     and that validation family is Holm-corrected together at a family-wide 0.05.
     Only markers that survive the correction are reported as markers.

Run from this directory:  python analysis.py
"""

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

ALPHA = 0.05

MARKERS = [
    "alpha_linolenic_mg_l",
    "beta_carotene_ug_l",
    "vaccenic_acid_mg_l",
    "phytanic_acid_umol_l",
    "urea_mmol_l",
    "creatinine_umol_l",
]

animals = pd.read_csv("data.csv")
discovery = animals[animals["split"] == "discovery"]
validation = animals[animals["split"] == "validation"]

print("Metabolomic markers of grass-fed beef")
print(f"{len(animals)} animals; split as recorded in data.csv:")
print(animals.groupby(["split", "finishing"]).size().to_string())
print()


def test_marker(subset, marker):
    grain = subset.loc[subset["finishing"] == "grain", marker]
    pasture = subset.loc[subset["finishing"] == "pasture", marker]
    t_stat, p_value = stats.ttest_ind(grain, pasture, equal_var=False)
    return grain.mean(), pasture.mean(), p_value


# --- Stage 1: discovery screening -------------------------------------------
print("STAGE 1 - DISCOVERY SET: SCREENING ONLY, NOT A FINDING")
print("Discovery p-values are used to choose which markers go forward. They are")
print("not evidence that a marker separates the two finishing systems.")
print()
print(f"{'marker':24s} {'grain':>9s} {'pasture':>9s} {'p':>11s}  shortlisted?")

shortlist = []
for marker in MARKERS:
    grain_mean, pasture_mean, p_value = test_marker(discovery, marker)
    carried_forward = p_value < 0.05
    if carried_forward:
        shortlist.append(marker)
    print(
        f"{marker:24s} {grain_mean:9.2f} {pasture_mean:9.2f} {p_value:11.4g}  "
        f"{'yes' if carried_forward else 'no'}"
    )

print()
print(f"Shortlist carried into validation ({len(shortlist)} of {len(MARKERS)} markers):")
for marker in shortlist:
    print(f"  {marker}")
print()

# --- Stage 2: validation ------------------------------------------------------
print("STAGE 2 - VALIDATION SET (held out): these results are the findings")

validation_p = []
validation_rows = []
for marker in shortlist:
    grain_mean, pasture_mean, p_value = test_marker(validation, marker)
    validation_p.append(p_value)
    validation_rows.append((marker, grain_mean, pasture_mean, p_value))

family_size = len(validation_p)
print(f"Corrected validation family size: {family_size} tests "
      f"(Holm-Bonferroni, family-wide alpha {ALPHA})")
print()

reject, p_holm, _, _ = multipletests(validation_p, alpha=ALPHA, method="holm")

print(f"{'marker':24s} {'grain':>9s} {'pasture':>9s} {'p':>11s} {'p Holm':>11s}  verdict")
confirmed = []
for (marker, grain_mean, pasture_mean, p_value), adjusted, survived in zip(
    validation_rows, p_holm, reject
):
    verdict = "marker" if survived else "not supported"
    if survived:
        confirmed.append(marker)
    print(
        f"{marker:24s} {grain_mean:9.2f} {pasture_mean:9.2f} {p_value:11.4g} "
        f"{adjusted:11.4g}  {verdict}"
    )

print()
print(f"Markers reported as authenticity indicators ({len(confirmed)} of {family_size} "
      f"validated, out of {len(MARKERS)} screened):")
for marker in confirmed:
    print(f"  {marker}")
