"""Generate the cranberry harvest-method dataset.

One row per production bog, 24 bogs total: 12 wet-harvested, 12 dry-harvested.
Each bog was harvested exactly once, so the bog is the independent unit and
appears exactly once in the output table.

Standard library only. Fixed seed so the file is reproducible.

Run:  /usr/local/bin/python3 make_data.py
"""

import csv
import datetime
import os
import random

SEED = 20260823
N_PER_METHOD = 12
N_BOGS = 2 * N_PER_METHOD

# Yield model (barrels per acre), from the study description.
MEAN_YIELD = {"dry": 165.0, "wet": 195.0}
SD_YIELD = 25.0
YIELD_MIN, YIELD_MAX = 110.0, 260.0

CULTIVARS = ["Stevens", "Ben Lear", "Early Black", "Howes", "Mullica Queen", "Crimson Queen"]

# Harvest window for the season. Dry harvest tends to run a little earlier than
# wet harvest, so the two methods draw from slightly offset date ranges.
SEASON_START = datetime.date(2025, 9, 15)
DRY_OFFSET_DAYS = (0, 22)   # 15 Sep - 7 Oct
WET_OFFSET_DAYS = (10, 35)  # 25 Sep - 20 Oct

OUT_CSV = "cranberry_harvest.csv"

FIELDNAMES = [
    "bog_id",
    "harvest_method",
    "marketable_yield_bbl_per_acre",
    "bog_area_acres",
    "cultivar",
    "planting_age_years",
    "harvest_date",
]


def draw_yield(rng, method):
    """One bog-level marketable yield, kept inside the plausible range."""
    while True:
        value = rng.gauss(MEAN_YIELD[method], SD_YIELD)
        if YIELD_MIN <= value <= YIELD_MAX:
            return round(value, 1)


def main():
    rng = random.Random(SEED)

    # Balanced assignment: 12 wet, 12 dry, shuffled across the bog identifiers.
    methods = ["wet"] * N_PER_METHOD + ["dry"] * N_PER_METHOD
    rng.shuffle(methods)

    rows = []
    for index, method in enumerate(methods, start=1):
        low, high = WET_OFFSET_DAYS if method == "wet" else DRY_OFFSET_DAYS
        harvest_date = SEASON_START + datetime.timedelta(days=rng.randint(low, high))
        rows.append(
            {
                "bog_id": "BOG%02d" % index,
                "harvest_method": method,
                "marketable_yield_bbl_per_acre": draw_yield(rng, method),
                "bog_area_acres": round(rng.uniform(3.0, 14.0), 1),
                "cultivar": rng.choice(CULTIVARS),
                "planting_age_years": rng.randint(6, 40),
                "harvest_date": harvest_date.isoformat(),
            }
        )

    assert len(rows) == N_BOGS
    assert len({row["bog_id"] for row in rows}) == N_BOGS  # each bog exactly once
    assert sum(1 for row in rows if row["harvest_method"] == "wet") == N_PER_METHOD

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_CSV)
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %s (%d rows)" % (out_path, len(rows)))


if __name__ == "__main__":
    main()
