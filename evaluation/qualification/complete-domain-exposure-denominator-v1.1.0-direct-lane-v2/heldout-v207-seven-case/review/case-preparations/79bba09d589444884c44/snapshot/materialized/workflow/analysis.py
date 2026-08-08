"""AURA-7 commissioning: failure intensity from valid-telemetry slots.

Reads inputs/data.csv, rebuilds the planned-unit accounting and the two signed
scope records, and writes results/report.md. Every count and every rate in the
report is derived from the CSV; nothing is hard-coded.
"""

import csv
from collections import Counter
from fractions import Fraction
from pathlib import Path

CASE_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = CASE_ROOT / "inputs" / "data.csv"
REPORT_PATH = CASE_ROOT / "results" / "report.md"
DECIMALS = 4


def load_rows(path):
    with path.open(newline="", encoding="ascii") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def fixed(value, places=DECIMALS):
    """Render a non-negative Fraction with half-up rounding at `places`."""
    scaled = Fraction(value) * (10 ** places)
    units = (2 * scaled.numerator + scaled.denominator) // (2 * scaled.denominator)
    digits = str(units).rjust(places + 1, "0")
    return digits[:-places] + "." + digits[-places:]


def tally(counter):
    return ", ".join("{0} {1}".format(key, counter[key]) for key in sorted(counter))


def build_report(rows):
    planned = len(rows)
    retained_rows = [r for r in rows if r["telemetry_status"] == "valid"]
    removed_rows = [r for r in rows if r["telemetry_status"] != "valid"]
    failure_rows = [r for r in retained_rows if r["failure_flag"] == "1"]
    retained = len(retained_rows)
    removed = len(removed_rows)
    events = len(failure_rows)

    scope_a = sum(1 for r in rows if r["scope_a_in_population"] == "yes")
    scope_b = sum(1 for r in rows if r["scope_b_in_population"] == "yes")

    per_block = Counter(r["observing_block"] for r in rows)
    n_blocks = len(per_block)
    block_size = min(per_block.values())
    n_channels = len({r["detector_channel"] for r in rows})

    reasons = Counter(r["telemetry_reject_reason"] for r in removed_rows)
    modes = Counter(r["failure_mode"] for r in failure_rows)

    per_slot = Fraction(events, retained)
    per_hundred = per_slot * 100
    contrast = Fraction(events, scope_a) * 100

    lines = [
        "# AURA-7 Commissioning: Slot Failure Intensity",
        "",
        "## Instrument and campaign",
        "",
        f"The AURA-7 adaptive-optics bench was commissioned over {n_blocks} observing blocks of",
        f"{block_size} scheduled slots each, one slot per closed-loop acquisition attempt, spread",
        f"over {n_channels} detector channels. A slot counts as a failure when the closed loop does",
        "not hold for the full acquisition.",
        "",
        "## Planned-unit accounting",
        "",
        f"- Planned commissioned slots: {planned}",
        f"- Retained after telemetry screening: {retained}",
        f"- Removed by telemetry screening: {removed}",
        f"- Failure events among retained slots: {events}",
        "",
        f"Removal reasons: {tally(reasons)}.",
        f"Failure modes: {tally(modes)}.",
        "",
        "## Governing scope records",
        "",
        "Two signed scope records govern this workflow. Both are executed originals,",
        "both are unamended, and both carry equal authority.",
        "",
        '- Scope Record A, "Commissioning Scope of Work" (signed): the analysis',
        f"  population is every commissioned slot, {scope_a} slots.",
        '- Scope Record B, "Telemetry Validation Annex" (signed): the analysis',
        f"  population is the valid-telemetry slots only, {scope_b} slots.",
        "",
        "Neither record is dated relative to the other, neither amends the other, and",
        "neither contains a precedence, supremacy, or order-of-control clause. Nothing",
        "in the record set resolves which population governs, and this workflow does",
        "not designate either record as controlling.",
        "",
        "## Failure intensity",
        "",
        f"The selected intensity uses the {retained} valid-telemetry slots as its denominator,",
        "which is the population described by Scope Record B; this choice of",
        "denominator is stated here as the reported basis, not as a ruling that Scope",
        "Record B outranks Scope Record A.",
        "",
        f"- Failures per valid-telemetry slot: {fixed(per_slot)} ({events} / {retained})",
        f"- Failures per 100 valid-telemetry slots: {fixed(per_hundred)}",
        "",
        f"Reported for contrast and not selected: over the {scope_a} commissioned slots of the",
        f"Scope Record A population, the same {events} failures give {fixed(contrast)} failures per 100",
        "slots. The two records thus support two different intensities and the conflict",
        "between them remains unresolved here.",
        "",
        f"[selected-result] Failure intensity {fixed(per_hundred)} failures per 100 valid-telemetry slots ({events} failures / {retained} valid-telemetry slots); accounting: {planned} planned commissioned slots, {retained} retained, {removed} removed, {events} events.",
        "",
        "## Reproducibility",
        "",
        "All counts and rates above are computed from inputs/data.csv by",
        "workflow/analysis.py. The script is deterministic: no randomness, no clock, no",
        "network, no arguments.",
    ]
    return "\n".join(lines) + "\n"


def main():
    report = build_report(load_rows(DATA_PATH))
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="ascii", newline="\n") as handle:
        handle.write(report)
    print(report, end="")


if __name__ == "__main__":
    main()
