"""Generate the winter air quality monitoring dataset for the two-station comparison.

Deterministic: a fixed seed produces byte-identical output on every run.

The file written by this script (air_quality_winter.csv) is the analysis input.
Eighty rows: forty monitoring days at the kerbside station on the arterial road and
forty monitoring days at the urban background station in the park. Each row is one
complete twenty-four hour averaging period at one station, with the daily mean of
each of the five declared pollutant outcomes.

Generating model (chosen to give plausible winter magnitudes and spread):

  * A per-day meteorological dispersion factor stands in for the winter weather.
    Values above one are stagnant, cold, poorly ventilated days on which every
    primary pollutant accumulates; values below one are windy, well mixed days.
    The same factor drives all primary pollutants on that day, which is why the
    columns are correlated within a row.
  * Fine particles (pm25_ug_m3) are dominated by regional secondary aerosol, so the
    kerbside increment over background is small.
  * Coarse particles (pm10_ug_m3) add resuspended road dust and brake and tyre wear
    at the kerbside, so the kerbside increment is larger than for fine particles.
  * Nitrogen dioxide (no2_ug_m3) and black carbon (black_carbon_ug_m3) are direct
    traffic exhaust tracers and are markedly higher at the kerbside.
  * Ozone (o3_ug_m3) is consumed by fresh nitric oxide from traffic, so it is drawn
    down at the kerbside relative to the same day's regional ozone level.

No hypothesis test is computed here. This script only writes data.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np

SEED = 20260124
N_PER_GROUP = 40

OUT_PATH = Path(__file__).resolve().parent / "air_quality_winter.csv"

COLUMNS = [
    "day_id",
    "site_group",
    "pm25_ug_m3",
    "pm10_ug_m3",
    "no2_ug_m3",
    "o3_ug_m3",
    "black_carbon_ug_m3",
]

# Plausible winter daily-mean limits, used only to keep stray draws inside the
# ranges an instrument at these sites would actually report.
LIMITS = {
    "pm25_ug_m3": (4.0, 46.0),
    "pm10_ug_m3": (9.0, 82.0),
    "no2_ug_m3": (9.0, 92.0),
    "o3_ug_m3": (18.0, 112.0),
    "black_carbon_ug_m3": (0.25, 6.2),
}


def clip(name: str, value: float) -> float:
    low, high = LIMITS[name]
    return float(min(max(value, low), high))


def make_group(rng: np.random.Generator, group: str, prefix: str) -> list[dict]:
    """Draw forty monitoring days for one station."""
    kerbside = group == "kerbside"

    rows: list[dict] = []
    for i in range(1, N_PER_GROUP + 1):
        # Per-day winter dispersion factor: >1 stagnant, <1 well ventilated.
        meteo = float(rng.lognormal(mean=0.0, sigma=0.30))

        # Regional secondary aerosol background common to the whole city.
        regional_pm25 = 13.5 * meteo * float(rng.lognormal(0.0, 0.13))
        pm25 = regional_pm25 + (2.1 if kerbside else 0.0) * meteo
        pm25 += float(rng.normal(0.0, 1.4))

        # Coarse fraction: crustal plus, at the kerb, resuspension and wear.
        coarse = pm25 * (0.62 if kerbside else 0.44) + float(rng.normal(0.0, 2.6))
        if kerbside:
            coarse += 6.4 * math.sqrt(meteo)
        pm10 = pm25 + max(coarse, 1.5)

        # Traffic exhaust tracers.
        no2_base = 48.0 if kerbside else 23.0
        no2 = no2_base * (meteo ** 0.82) * float(rng.lognormal(0.0, 0.15))
        no2 += float(rng.normal(0.0, 2.5))

        bc_base = 2.35 if kerbside else 0.78
        black_carbon = bc_base * (meteo ** 0.9) * float(rng.lognormal(0.0, 0.20))
        black_carbon += float(rng.normal(0.0, 0.08))

        # Regional winter ozone, then local titration by fresh traffic emissions.
        regional_o3 = 66.0 - 11.0 * (meteo - 1.0) + float(rng.normal(0.0, 7.5))
        o3 = regional_o3 - 0.42 * max(no2 - 18.0, 0.0)
        o3 += float(rng.normal(0.0, 3.0))

        rows.append(
            {
                "day_id": f"{prefix}-{i:03d}",
                "site_group": group,
                "pm25_ug_m3": round(clip("pm25_ug_m3", pm25), 1),
                "pm10_ug_m3": round(clip("pm10_ug_m3", pm10), 1),
                "no2_ug_m3": round(clip("no2_ug_m3", no2), 1),
                "o3_ug_m3": round(clip("o3_ug_m3", o3), 1),
                "black_carbon_ug_m3": round(clip("black_carbon_ug_m3", black_carbon), 2),
            }
        )
    return rows


def main() -> None:
    rng = np.random.default_rng(SEED)
    rows = make_group(rng, "kerbside", "KRB") + make_group(rng, "background", "BGD")

    with OUT_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {len(rows)} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
