"""Generate the estuarine benthic survey data set.

Sixteen fixed sampling stations (ST-01 .. ST-16) were visited by boat. Eight sit
inside the dredge spoil disposal footprint and eight are matched reference
positions of the same depth and sediment type, worked as pairs: ST-01 is a
footprint station and ST-02 is its reference partner, ST-03 pairs with ST-04,
and so on.

At every station the crew took five grab samples from slightly different points
within a twenty-metre radius, each grab covering 0.1 square metres, and sorted
each grab in the laboratory. So the table holds 16 stations x 5 grabs = 80 rows,
one row per grab.

Counts are built in two layers, the way real survey counts behave:
  * a station-level level drawn once per station (between-station spread), and
  * a grab-level wobble drawn once per grab (within-station spread).
That makes the five grabs from one station resemble each other more closely
than grabs from different stations.

Standard library only. Fixed seed, so the file regenerates byte-for-byte.
"""

import csv
import os
import random

SEED = 20260823

# Worms per 0.1 m^2 grab.
FOOTPRINT_MEAN = 58.0     # inside the disposal footprint
REFERENCE_MEAN = 98.0     # matched reference positions (~40 worms richer)
BETWEEN_STATION_SD = 20.0  # station-to-station spread
WITHIN_STATION_SD = 11.0   # grab-to-grab spread inside one station

N_PAIRS = 8         # 8 footprint stations + 8 reference stations
GRABS_PER_STATION = 5

MIN_COUNT = 8       # a grab that comes up nearly bare still holds a few worms


def build_rows():
    rng = random.Random(SEED)
    stations = []
    for pair in range(N_PAIRS):
        # Each matched pair contributes one footprint station then its reference.
        stations.append((f"ST-{2 * pair + 1:02d}", "footprint"))
        stations.append((f"ST-{2 * pair + 2:02d}", "reference"))

    rows = []
    for station_ref, station_group in stations:
        base = FOOTPRINT_MEAN if station_group == "footprint" else REFERENCE_MEAN
        station_level = rng.gauss(base, BETWEEN_STATION_SD)
        for grab_number in range(1, GRABS_PER_STATION + 1):
            count = station_level + rng.gauss(0.0, WITHIN_STATION_SD)
            count = max(MIN_COUNT, int(round(count)))
            rows.append(
                {
                    "station_ref": station_ref,
                    "station_group": station_group,
                    "grab_number": grab_number,
                    "polychaete_count": count,
                }
            )
    return rows


def main():
    rows = build_rows()
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "benthic_grabs.csv")
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["station_ref", "station_group", "grab_number", "polychaete_count"],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
