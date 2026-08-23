"""Generate soil_respiration.csv for the grassland warming experiment.

Design: 10 whole plots (5 ambient, 5 warmed), 6 fixed collars per plot,
one summer morning of readings -> 60 rows.

Structure that is deliberately built in: each plot carries its own baseline
efflux level (soil depth, root density, drainage, microtopography), and the
spread of those plot baselines is at least as large as the average warmed
minus ambient difference. Collar readings scatter tightly around their own
plot's baseline.
"""

import csv
import random

SEED = 20260821
random.seed(SEED)

OUT = "soil_respiration.csv"

# Plot layout: heater assignment was randomised in the field, so warmed and
# ambient plots are interleaved rather than blocked.
PLOTS = [
    ("P-101", "ambient"),
    ("P-102", "warmed"),
    ("P-103", "warmed"),
    ("P-104", "ambient"),
    ("P-105", "ambient"),
    ("P-106", "warmed"),
    ("P-107", "ambient"),
    ("P-108", "warmed"),
    ("P-109", "warmed"),
    ("P-110", "ambient"),
]
COLLARS = ["C1", "C2", "C3", "C4", "C5", "C6"]

# Efflux components (umol CO2 m-2 s-1)
AMBIENT_GRAND_MEAN = 2.60
WARMING_EFFECT = 0.45          # average warmed minus ambient
PLOT_BASELINE_SD = 0.55        # >= WARMING_EFFECT by construction
COLLAR_SD = 0.13               # within-plot collar scatter

# Temperature (deg C at 5 cm) and moisture (volumetric %)
AMBIENT_TEMP_MEAN = 18.4
TEMP_WARMING = 2.0
PLOT_TEMP_SD = 0.55
COLLAR_TEMP_SD = 0.22

PLOT_MOIST_MEAN = 22.0
PLOT_MOIST_SD = 3.6
COLLAR_MOIST_SD = 1.1


def clamp(value, low, high):
    return max(low, min(high, value))


rows = []
for plot_code, status in PLOTS:
    warmed = status == "warmed"

    # Plot-level baselines: the large, heater-independent site variation.
    plot_efflux_base = (
        AMBIENT_GRAND_MEAN
        + (WARMING_EFFECT if warmed else 0.0)
        + random.gauss(0.0, PLOT_BASELINE_SD)
    )
    plot_temp_base = (
        AMBIENT_TEMP_MEAN
        + (TEMP_WARMING if warmed else 0.0)
        + random.gauss(0.0, PLOT_TEMP_SD)
    )
    plot_moist_base = clamp(random.gauss(PLOT_MOIST_MEAN, PLOT_MOIST_SD), 15.0, 29.0)

    for collar in COLLARS:
        efflux = plot_efflux_base + random.gauss(0.0, COLLAR_SD)
        temp = plot_temp_base + random.gauss(0.0, COLLAR_TEMP_SD)
        moist = clamp(plot_moist_base + random.gauss(0.0, COLLAR_MOIST_SD), 14.0, 30.0)

        rows.append(
            {
                "plot_code": plot_code,
                "warming_status": status,
                "collar_position": collar,
                "soil_temp_c": f"{temp:.2f}",
                "soil_moisture_pct": f"{moist:.1f}",
                "co2_efflux": f"{clamp(efflux, 0.5, 9.0):.2f}",
            }
        )

with open(OUT, "w", newline="") as fh:
    writer = csv.DictWriter(
        fh,
        fieldnames=[
            "plot_code",
            "warming_status",
            "collar_position",
            "soil_temp_c",
            "soil_moisture_pct",
            "co2_efflux",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)

print(f"wrote {len(rows)} rows to {OUT}")
