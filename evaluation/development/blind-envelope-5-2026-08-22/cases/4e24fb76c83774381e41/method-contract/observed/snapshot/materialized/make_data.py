"""Generate the two data files for the farmland butterfly transect study.

Standard library only. Fixed seed, so re-running reproduces both files byte for byte.

Outputs (written next to this script):
  weekly_counts.csv  - one row per route-week (22 routes x 18 weeks = 396 rows)
  route_summary.csv  - one row per route (22 rows), derived from weekly_counts.csv
"""

import csv
import math
import os
import random

SEED = 20260822
N_ROUTES_PER_GROUP = 11
N_WEEKS = 18
PEAK_WEEK = 10.0
PEAK_WIDTH = 4.2
SEASON_FLOOR = 0.22

HERE = os.path.dirname(os.path.abspath(__file__))
WEEKLY_PATH = os.path.join(HERE, "weekly_counts.csv")
SUMMARY_PATH = os.path.join(HERE, "route_summary.csv")


def season_factor(week):
    """Unimodal midsummer curve: 1.0 at the peak week, SEASON_FLOOR at the shoulders."""
    bump = math.exp(-0.5 * ((week - PEAK_WEEK) / PEAK_WIDTH) ** 2)
    return SEASON_FLOOR + (1.0 - SEASON_FLOOR) * bump


def make_route_codes(rng, n):
    """Transect-register style codes, e.g. UKBMS-0412. Unique, no group information."""
    codes = set()
    while len(codes) < n:
        codes.add("UKBMS-%04d" % rng.randint(100, 9899))
    return sorted(codes)


def main():
    rng = random.Random(SEED)

    codes = make_route_codes(rng, 2 * N_ROUTES_PER_GROUP)
    rng.shuffle(codes)
    assignment = {}
    for code in codes[:N_ROUTES_PER_GROUP]:
        assignment[code] = "wildflower_margin"
    for code in codes[N_ROUTES_PER_GROUP:]:
        assignment[code] = "conventional"

    # Each route keeps its own consistent abundance level across the season.
    route_level = {}
    for code in codes:
        if assignment[code] == "wildflower_margin":
            route_level[code] = rng.uniform(41.0, 70.0)
        else:
            route_level[code] = rng.uniform(19.0, 38.0)

    weekly_rows = []
    for code in sorted(codes):
        group = assignment[code]
        level = route_level[code]
        lo, hi = (9, 80) if group == "wildflower_margin" else (4, 45)
        for week in range(1, N_WEEKS + 1):
            season = season_factor(week)

            # Warm-season air temperature, warmest around the midsummer peak.
            temp = 16.5 + 8.0 * (season - SEASON_FLOOR) / (1.0 - SEASON_FLOOR)
            temp += rng.gauss(0.0, 2.2)
            temp = min(28.0, max(14.0, temp))

            lam = level * season * (1.0 + 0.015 * (temp - 21.0))
            count = int(round(lam * math.exp(rng.gauss(0.0, 0.17))))
            count = min(hi, max(lo, count))

            weekly_rows.append(
                {
                    "route_code": code,
                    "management": group,
                    "survey_week": week,
                    "air_temp_c": round(temp, 1),
                    "butterfly_count": count,
                }
            )

    with open(WEEKLY_PATH, "w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "route_code",
                "management",
                "survey_week",
                "air_temp_c",
                "butterfly_count",
            ],
        )
        writer.writeheader()
        writer.writerows(weekly_rows)

    # The per-route file is computed from the weekly rows, so the two files agree.
    totals = {}
    for row in weekly_rows:
        code = row["route_code"]
        if code not in totals:
            totals[code] = [0, 0]
        totals[code][0] += 1
        totals[code][1] += row["butterfly_count"]

    with open(SUMMARY_PATH, "w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "route_code",
                "management",
                "weeks_surveyed",
                "mean_weekly_count",
            ],
        )
        writer.writeheader()
        for code in sorted(codes):
            n_weeks, total = totals[code]
            writer.writerow(
                {
                    "route_code": code,
                    "management": assignment[code],
                    "weeks_surveyed": n_weeks,
                    "mean_weekly_count": round(total / n_weeks, 2),
                }
            )


if __name__ == "__main__":
    main()
