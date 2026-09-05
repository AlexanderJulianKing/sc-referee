"""Night-shift work and metabolic markers.

Permanent night-shift workers at a distribution centre compared against
day-shift workers at the same site, matched on age band and job grade. Fasting
bloods and anthropometry from a single occupational health visit.

The script runs in two passes. Pass one collects a result record per outcome and
prints nothing. Pass two walks the collected records and prints the table,
deciding significance row by row against the conventional five-percent cutoff.
"""

from dataclasses import dataclass

import pandas as pd
from scipy import stats

ALPHA = 0.05

OUTCOMES = [
    ("fasting_glucose_mmol_l", "fasting glucose (mmol/L)"),
    ("hdl_mmol_l", "HDL cholesterol (mmol/L)"),
    ("triglycerides_mmol_l", "triglycerides (mmol/L)"),
    ("waist_cm", "waist circumference (cm)"),
    ("systolic_bp_mmhg", "systolic BP (mmHg)"),
    ("sleep_hours", "sleep per 24 h (hours)"),
]


@dataclass
class Result:
    label: str
    day_mean: float
    night_mean: float
    p_value: float


def main():
    workers = pd.read_csv("data.csv")
    day = workers[workers["shift"] == "day"]
    night = workers[workers["shift"] == "night"]

    # ---- pass one: collect, print nothing ---------------------------------
    results = []
    for column, label in OUTCOMES:
        a = day[column]
        b = night[column]
        t_stat, p_value = stats.ttest_ind(a, b, equal_var=False)
        results.append(
            {
                "label": label,
                "day_mean": a.mean(),
                "night_mean": b.mean(),
                "p_value": p_value,
            }
        )

    # ---- pass two: report -------------------------------------------------
    print("Night-shift metabolic survey, single distribution centre")
    print(f"day shift: {len(day)} workers   night shift: {len(night)} workers")
    print(f"significance cutoff: {ALPHA}")
    print()
    print(f"{'outcome':28s} {'day':>9s} {'night':>9s} {'p':>11s}  verdict")

    for result in results:
        verdict = "significant" if result['p_value'] < ALPHA else "not significant"
        print(
            f"{result['label']:28s} {result['day_mean']:9.2f} {result['night_mean']:9.2f} "
            f"{result['p_value']:11.4g}  {verdict}"
        )


if __name__ == "__main__":
    main()
