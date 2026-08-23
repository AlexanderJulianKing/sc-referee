"""Generate the shelter-cat enrichment dataset.

One row per cat morning: 24 cats x 6 consecutive mornings = 144 rows.
Standard library only. Fixed seed, so the file is reproducible.

Generating model (values are chosen, not estimated from real data):
  log(fgm) = group median (log scale) + cat random intercept + morning residual
so that each cat keeps a persistent level of its own and still fluctuates
from morning to morning. Working on the log scale keeps every value
positive and makes the spread proportional to the level, which is how
hormone metabolite assays usually behave.
  food intake  = cat appetite intercept + small group shift
                 - a mild pull from that morning's stress residual
                 + morning noise, clipped into 40-100 percent.
"""

import csv
import math
import os
import random

SEED = 20260822
N_PER_GROUP = 12
N_DAYS = 6

# log-scale medians: exp(5.124) = 168 ng/g usual, exp(4.644) = 104 ng/g enriched
LOG_MEDIAN = {"usual_husbandry": 5.124, "enrichment": 4.644}
SD_CAT_LOG = 0.145        # persistent between-cat differences
SD_DAY_LOG = 0.100        # day-to-day fluctuation inside a cat

FOOD_MEAN = {"usual_husbandry": 71.0, "enrichment": 80.0}
SD_CAT_FOOD = 8.5
SD_DAY_FOOD = 6.0
FOOD_STRESS_SLOPE = -22.0  # percent of ration per unit of log-scale stress residual

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "shelter_cat_fgm.csv")


def main():
    rng = random.Random(SEED)

    # Shelter intake codes: two-digit intake year, then a running case number.
    case_numbers = rng.sample(range(1040, 1990), N_PER_GROUP * 2)
    case_numbers.sort()
    cat_refs = ["A26-{:04d}".format(n) for n in case_numbers]

    groups = ["enrichment"] * N_PER_GROUP + ["usual_husbandry"] * N_PER_GROUP
    rng.shuffle(groups)

    rows = []
    for cat_ref, group in zip(cat_refs, groups):
        cat_effect = rng.gauss(0.0, SD_CAT_LOG)
        cat_food = rng.gauss(FOOD_MEAN[group], SD_CAT_FOOD)
        for day in range(1, N_DAYS + 1):
            day_effect = rng.gauss(0.0, SD_DAY_LOG)
            fgm = math.exp(LOG_MEDIAN[group] + cat_effect + day_effect)
            food = (cat_food
                    + FOOD_STRESS_SLOPE * (cat_effect + day_effect)
                    + rng.gauss(0.0, SD_DAY_FOOD))
            food = min(100.0, max(40.0, food))
            rows.append({
                "cat_ref": cat_ref,
                "husbandry_group": group,
                "sample_day": day,
                "food_intake_pct": round(food, 1),
                "fgm_ng_per_g": round(fgm, 1),
            })

    fields = ["cat_ref", "husbandry_group", "sample_day",
              "food_intake_pct", "fgm_ng_per_g"]
    with open(OUT_PATH, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote {} rows to {}".format(len(rows), OUT_PATH))


if __name__ == "__main__":
    main()
