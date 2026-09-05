"""Low-stress handling vs the plant's standard handling: stress and carcass traits.

84 finishing steers, 42 per handling method, one animal per row.

Six carcass and stress outcomes were pre-specified together, so all six are tested
as one family and corrected as one family (Holm-Bonferroni, family-wide alpha 0.05).
The primary run is the finding. A second, clearly separate run repeats the same
corrected family after dropping the longest-transport steers; that run exists only
to show whether the primary picture is stable, and it is not a second set of results
to report alongside the first.

Run from this directory:  python analysis.py
"""

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

ALPHA = 0.05

# Pre-specified outcome family, in the order it was registered.
OUTCOMES = [
    ("plasma_cortisol_nmol_l", "plasma cortisol (nmol/L)"),
    ("ph_24h", "loin pH at 24 h"),
    ("shear_force_n", "shear force (N)"),
    ("drip_loss_pct", "drip loss (%)"),
    ("bruise_score", "bruise score (0-5)"),
    ("dark_cutting_flag_pct", "meat colour score (0-10)"),
]


def corrected_family(steers):
    """Test the whole six-outcome family and Holm-correct it as one family."""
    rows = []
    raw_p = []
    for column, label in OUTCOMES:
        standard = steers.loc[steers["handling"] == "standard", column]
        low_stress = steers.loc[steers["handling"] == "low_stress", column]
        t_stat, p = stats.ttest_ind(standard, low_stress, equal_var=False)
        rows.append(
            {
                "label": label,
                "standard_mean": standard.mean(),
                "low_stress_mean": low_stress.mean(),
                "p_raw": p,
            }
        )
        raw_p.append(p)

    reject, p_adj, _, _ = multipletests(raw_p, alpha=ALPHA, method="holm")
    for row, adjusted, is_rejected in zip(rows, p_adj, reject):
        row["p_holm"] = adjusted
        row["significant"] = bool(is_rejected)
    return rows


def show(rows, family_size):
    print(f"  {'outcome':26s} {'standard':>9s} {'low_stress':>11s} {'p raw':>10s} {'p Holm':>10s}  verdict")
    for row in rows:
        verdict = "significant" if row["significant"] else "not significant"
        print(
            f"  {row['label']:26s} {row['standard_mean']:9.2f} {row['low_stress_mean']:11.2f} "
            f"{row['p_raw']:10.4g} {row['p_holm']:10.4g}  {verdict}"
        )
    print(f"  Holm correction applied across a family of {family_size} outcomes, family-wide alpha {ALPHA}.")


steers = pd.read_csv("data.csv")
print("Low-stress cattle handling and carcass quality")
print(f"{len(steers)} steers: " + ", ".join(f"{k} {v}" for k, v in steers["handling"].value_counts().items()))
print()

# ---------------------------------------------------------------------------
# PRIMARY ANALYSIS - these are the findings
# ---------------------------------------------------------------------------
print("PRIMARY ANALYSIS (all 84 steers) - these corrected results are the findings")
primary = corrected_family(steers)
show(primary, len(OUTCOMES))
print()

# ---------------------------------------------------------------------------
# SENSITIVITY ANALYSIS - stability check only, not a second set of findings
# ---------------------------------------------------------------------------
cutoff = steers["transport_minutes"].quantile(0.90)
trimmed = steers[steers["transport_minutes"] < cutoff]
dropped = len(steers) - len(trimmed)

print("SENSITIVITY ANALYSIS - longest tenth of transport times dropped")
print(f"  transport-time cutoff (90th percentile): {cutoff:.1f} min")
print(f"  {dropped} steers dropped, {len(trimmed)} retained "
      f"({trimmed['handling'].value_counts().to_dict()})")
sensitivity = corrected_family(trimmed)
show(sensitivity, len(OUTCOMES))
print()

print("The primary corrected family above is what the study reports. The sensitivity")
print("re-run is a stability check on those findings and does not replace them.")
print()
print("Stability check, outcome by outcome:")
for primary_row, sensitivity_row in zip(primary, sensitivity):
    same = "unchanged" if primary_row["significant"] == sensitivity_row["significant"] else "CHANGED"
    print(f"  {primary_row['label']:26s} {same}")
