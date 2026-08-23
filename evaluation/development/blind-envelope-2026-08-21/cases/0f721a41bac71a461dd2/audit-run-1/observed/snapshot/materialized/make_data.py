"""Generate the simulated day-12 nestling dataset for the great tit
supplementary-feeding study.

Structure of the simulated data:
  * 16 nestboxes, 8 supplemented and 8 unsupplemented (control)
  * exactly 4 surviving nestlings weighed per nest -> 64 nestling records
  * each nest gets its own baseline mass (parental quality, territory,
    hatch date, brood history); the spread of those nest baselines is
    deliberately at least as large as the supplemented-control difference
  * individual chicks are scattered tightly around their own nest baseline

Run:  python3 make_data.py
Writes nestling_mass.csv next to this script.
"""

import numpy as np
import pandas as pd

SEED = 20260421
rng = np.random.default_rng(SEED)

N_NESTS = 16
CHICKS_PER_NEST = 4

# --- mass model (grams) -------------------------------------------------
GRAND_MEAN = 15.2        # control-brood average day-12 mass
TREATMENT_EFFECT = 0.8   # extra grams for supplemented broods
NEST_SD = 0.85           # between-nest spread, >= TREATMENT_EFFECT
CHICK_SD = 0.45          # within-nest spread among siblings

# --- tarsus model (mm) --------------------------------------------------
TARSUS_MEAN = 17.2
TARSUS_NEST_SD = 0.35
TARSUS_CHICK_SD = 0.30
TARSUS_PER_GRAM = 0.18   # heavier chicks have slightly longer tarsi

# --- nests --------------------------------------------------------------
# sixteen distinct nestbox tags drawn from the plot's box numbering
nest_tags = ["NB-%02d" % n for n in sorted(rng.choice(np.arange(1, 25), size=N_NESTS, replace=False))]

# whole broods assigned to treatment: 8 supplemented, 8 control
treatments = np.array(["supplemented"] * 8 + ["control"] * 8)
rng.shuffle(treatments)

# nest baselines are independent of treatment: they stand for parental
# quality, territory food supply, brood history, and so on
nest_offsets = rng.normal(0.0, NEST_SD, size=N_NESTS)
tarsus_offsets = rng.normal(0.0, TARSUS_NEST_SD, size=N_NESTS)

# hatch dates: late April to early May, one date shared by a whole brood
hatch_dates = pd.to_datetime("2026-04-22") + pd.to_timedelta(
    rng.integers(0, 15, size=N_NESTS), unit="D"
)

rows = []
ring_number = 1201  # ring series runs A1201 upward

for i, tag in enumerate(nest_tags):
    treat = treatments[i]
    nest_mean = GRAND_MEAN + nest_offsets[i] + (TREATMENT_EFFECT if treat == "supplemented" else 0.0)
    for _ in range(CHICKS_PER_NEST):
        mass = nest_mean + rng.normal(0.0, CHICK_SD)
        tarsus = (
            TARSUS_MEAN
            + tarsus_offsets[i]
            + TARSUS_PER_GRAM * (mass - GRAND_MEAN)
            + rng.normal(0.0, TARSUS_CHICK_SD)
        )
        rows.append(
            {
                "nest_tag": tag,
                "food_treatment": treat,
                "chick_ring": "A%d" % ring_number,
                "hatch_date": hatch_dates[i].strftime("%Y-%m-%d"),
                "mass_g_day12": round(float(mass), 1),
                "tarsus_mm": round(float(tarsus), 1),
            }
        )
        ring_number += 1

# rows are ordered nest by nest, the way the field notebook was filled in
df = pd.DataFrame(rows, columns=[
    "nest_tag", "food_treatment", "chick_ring", "hatch_date", "mass_g_day12", "tarsus_mm"
])
df.to_csv("nestling_mass.csv", index=False)

print("wrote nestling_mass.csv:", len(df), "rows,", df["nest_tag"].nunique(), "nests")
