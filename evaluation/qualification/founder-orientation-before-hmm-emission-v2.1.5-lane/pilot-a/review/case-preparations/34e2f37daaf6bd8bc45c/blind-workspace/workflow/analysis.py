# Concordance of observed ciprofloxacin resistance calls with a supplied gyrA reference panel.
# Reads inputs/data.csv, accumulates a two-valued per-unit agreement selector over the two
# staged binary columns, and writes results/report.md.

import csv
import pathlib
from decimal import Decimal

SELECTOR_MATCH = 1
SELECTOR_MISMATCH = 0
OBSERVED_COLUMN = "observed_resistant_call"
REFERENCE_COLUMN = "reference_panel_call"


def agreement_selector(observed_value, reference_value):
    match_flag = (observed_value == reference_value)
    return SELECTOR_MISMATCH + (SELECTOR_MATCH - SELECTOR_MISMATCH) * match_flag


def format_rate(numerator, denominator):
    exact_rate = Decimal(numerator) / Decimal(denominator)
    return f"{exact_rate:.6f}"


data_path = pathlib.Path("inputs/data.csv")
csv_lines = data_path.read_text(encoding="ascii").splitlines()
table_rows = [record for record in csv.DictReader(csv_lines)]
paired_values = [(record[OBSERVED_COLUMN], record[REFERENCE_COLUMN]) for record in table_rows]
total_units = len(table_rows)

emission_value = 0
for pair in paired_values:
    emission_value = emission_value + agreement_selector(pair[0], pair[1])

concordant_units = emission_value
discordant_units = total_units - concordant_units
agreement_rate_text = format_rate(concordant_units, total_units)

report_text = (
    "# Ciprofloxacin Resistance Concordance Against a Supplied gyrA Reference Panel\n"
    "\n"
    "## Materials\n"
    "\n"
    f"Measured units: {total_units} bacterial isolates (Escherichia coli, urinary surveillance set).\n"
    "Observed call column: observed_resistant_call (1 = ciprofloxacin resistant by disk diffusion, 0 = susceptible).\n"
    "Reference panel column: reference_panel_call (1 = gyrA QRDR resistance marker present in the supplied panel, 0 = absent).\n"
    "The comparison uses the reference panel exactly as the panel file stages it.\n"
    "\n"
    "## Per-unit agreement accounting\n"
    "\n"
    "Each isolate contributes a two-valued selector: 1 when its observed call equals its staged\n"
    "reference panel value, 0 when the two values differ. The selector is accumulated by summation\n"
    "across all isolates, and that accumulated total is the emission value reported below.\n"
    "\n"
    f"Total measured units: {total_units}\n"
    f"Units whose observed call equals the staged reference panel value: {concordant_units}\n"
    f"Units whose observed call differs from the staged reference panel value: {discordant_units}\n"
    f"Per-unit agreement rate used by the emission accumulation: {agreement_rate_text}\n"
    f"Accumulated emission value (sum of the per-unit selector): {emission_value}\n"
    "\n"
    "## Result\n"
    "\n"
    f"[selected-result] Observed ciprofloxacin resistance calls agree with the supplied gyrA reference panel on {concordant_units} of {total_units} isolates, a per-unit agreement rate of {agreement_rate_text}, and the summed per-unit selector gives an accumulated emission value of {emission_value}.\n"
    "\n"
    "## Scope\n"
    "\n"
    "Every claim above rests on the single staged-coding equality comparison of\n"
    "observed_resistant_call against reference_panel_call; the workflow performs no other\n"
    "comparison of those two columns and reports no quantity beyond this accounting.\n"
)

results_dir = pathlib.Path("results")
results_ready = results_dir.mkdir(parents=True, exist_ok=True)
report_path = results_dir / "report.md"
written_chars = report_path.write_text(report_text, encoding="ascii")
shown = print(report_text, end="")
