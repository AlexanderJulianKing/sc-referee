"""Failure intensity conditional on valid telemetry.

Reads inputs/data.csv, which holds one row per commissioned hourly instrument
slot, screens the commissioned calendar down to the valid-telemetry target set,
and writes results/report.md. Every count and rate reported is derived from the
CSV; nothing is hard-coded.
"""

import csv
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from math import sqrt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "inputs" / "data.csv"
REPORT_PATH = ROOT / "results" / "report.md"

# Fixed normal 97.5th percentile used for the Wilson score interval.
Z_975 = 1.959964


def load_slots(path):
    with path.open(newline="", encoding="ascii") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def to_places(value, places):
    step = Decimal(1).scaleb(-places)
    return str(Decimal(value).quantize(step, rounding=ROUND_HALF_UP))


def wilson_interval(events, trials, z):
    p = events / trials
    zz = z * z
    denom = 1.0 + zz / trials
    center = (p + zz / (2.0 * trials)) / denom
    half = z * sqrt(p * (1.0 - p) / trials + zz / (4.0 * trials * trials)) / denom
    return center - half, center + half


def main():
    slots = load_slots(DATA_PATH)
    planned = len(slots)

    retained = [row for row in slots if row["telemetry_status"] == "valid"]
    removed = [row for row in slots if row["telemetry_status"] != "valid"]
    n_retained = len(retained)
    n_removed = len(removed)

    events = sum(1 for row in retained if row["failure_observed"] == "1")
    events_outside = sum(1 for row in removed if row["failure_observed"] == "1")

    reason_counts = Counter(row["invalid_reason"] for row in removed)
    day_slots = Counter(row["utc_date"] for row in retained)
    day_events = Counter(
        row["utc_date"] for row in retained if row["failure_observed"] == "1"
    )

    rate = Decimal(events) / Decimal(n_retained)
    rate_str = to_places(rate, 6)
    pct_str = to_places(rate * 100, 4)
    low, high = wilson_interval(events, n_retained, Z_975)
    low_str = to_places(low, 4)
    high_str = to_places(high, 4)

    lines = []
    lines.append("# Failure Intensity Conditional on Valid-Telemetry Slots")
    lines.append("")
    lines.append("## Scientific question")
    lines.append("")
    lines.append(
        "Among commissioned hourly instrument slots that returned valid telemetry, at"
    )
    lines.append(
        "what intensity do failures occur? The target population is the valid-telemetry"
    )
    lines.append(
        "slot set; the commissioned calendar is only the wider frame from which that"
    )
    lines.append("target is screened.")
    lines.append("")
    lines.append("## Target definition and screening rule")
    lines.append("")
    lines.append(
        "- Frame: every commissioned hourly slot on the calendar, one CSV row per slot."
    )
    lines.append(
        "- Target: slots with telemetry_status = valid; there are {0} of them.".format(
            n_retained
        )
    )
    lines.append(
        "- Screening removes slots with telemetry_status = invalid. Those slots carry"
    )
    lines.append(
        "  failure_observed = unknown and enter neither numerator nor denominator."
    )
    lines.append(
        "- The selected intensity denominator is the {0} valid-telemetry slots.".format(
            n_retained
        )
    )
    lines.append("")
    lines.append("## Unit accounting")
    lines.append("")
    lines.append("| quantity | count |")
    lines.append("| --- | --- |")
    lines.append("| planned commissioned slots | {0} |".format(planned))
    lines.append(
        "| retained after screening (valid telemetry) | {0} |".format(n_retained)
    )
    lines.append(
        "| removed by screening (invalid telemetry) | {0} |".format(n_removed)
    )
    lines.append("| failure events among retained slots | {0} |".format(events))
    lines.append(
        "| failure events recorded outside the target set | {0} |".format(
            events_outside
        )
    )
    lines.append("")
    lines.append(
        "Accounting check: {0} retained + {1} removed = {2} planned.".format(
            n_retained, n_removed, n_retained + n_removed
        )
    )
    lines.append("")
    lines.append("## Screening removals by reason")
    lines.append("")
    lines.append("| reason | slots removed |")
    lines.append("| --- | --- |")
    for reason in sorted(reason_counts):
        lines.append("| {0} | {1} |".format(reason, reason_counts[reason]))
    lines.append("| total removed | {0} |".format(n_removed))
    lines.append("")
    lines.append("## Selected result")
    lines.append("")
    lines.append(
        "[selected-result] Failure intensity among valid-telemetry slots: "
        "{0} failures / {1} valid-telemetry slots = {2} failures per valid "
        "slot-hour ({3} percent; 95 percent Wilson interval {4} to {5}).".format(
            events, n_retained, rate_str, pct_str, low_str, high_str
        )
    )
    lines.append("")
    lines.append("## Per-day breakdown, valid-telemetry slots only")
    lines.append("")
    lines.append("| utc_date | valid slots | failures | intensity |")
    lines.append("| --- | --- | --- | --- |")
    for day in sorted(day_slots):
        day_n = day_slots[day]
        day_e = day_events[day]
        day_rate = to_places(Decimal(day_e) / Decimal(day_n), 6)
        lines.append("| {0} | {1} | {2} | {3} |".format(day, day_n, day_e, day_rate))
    lines.append("")
    lines.append("## Scope of claim")
    lines.append("")
    lines.append(
        "Every claim here is conditional on valid telemetry. The intensity {0}".format(
            rate_str
        )
    )
    lines.append(
        "failures per slot-hour describes the {0} valid-telemetry slots only. It is not".format(
            n_retained
        )
    )
    lines.append(
        "an intensity for the {0} commissioned slots, because the failure state of the {1}".format(
            planned, n_removed
        )
    )
    lines.append("removed slots is unobserved, and no inference is extended to them.")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="ascii", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
