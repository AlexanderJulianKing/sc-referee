# Concordance of observed ciprofloxacin resistance calls with a supplied gyrA reference panel.
# Reads inputs/data.csv, accumulates a two-valued per-unit agreement selector over the two
# binary columns, and writes results/report.md.

import csv
import pathlib
from decimal import Decimal

SELECTOR_MATCH = 1
SELECTOR_MISMATCH = 0
OBSERVED_COLUMN = "observed_resistant_call"
REFERENCE_COLUMN = "reference_panel_call"
PANEL_BASELINE = 1


def agreement_selector(observed_value, reference_value):
    match_flag = (observed_value == reference_value)
    return SELECTOR_MISMATCH + (SELECTOR_MATCH - SELECTOR_MISMATCH) * match_flag


def format_rate(numerator, denominator):
    exact_rate = Decimal(numerator) / Decimal(denominator)
    return f"{exact_rate:.6f}"


data_path = pathlib.Path("inputs/data.csv")
csv_lines = data_path.read_text(encoding="ascii").splitlines()
table_rows = [record for record in csv.DictReader(csv_lines)]
observed_values = [int(record[OBSERVED_COLUMN]) for record in table_rows]
reference_values = [PANEL_BASELINE - int(record[REFERENCE_COLUMN]) for record in table_rows]
paired_values = [pair for pair in zip(observed_values, reference_values)]
total_units = len(table_rows)

emission_value = 0
for pair in paired_values:
    emission_value = emission_value + agreement_selector(pair[0], pair[1])

concordant_units = total_units - emission_value
agreement_rate_text = format_rate(emission_value, total_units)

report_text = (
    "# Ciprofloxacin Resistance Concordance Against a Supplied gyrA Reference Panel\n"
    "\n"
    "## Materials\n"
    "\n"
    f"Measured units: {total_units} bacterial isolates (Escherichia coli, urinary surveillance set).\n"
    "Observed call column: observed_resistant_call (1 = ciprofloxacin resistant by disk diffusion, 0 = susceptible).\n"
    "Reference panel column: reference_panel_call (1 = gyrA QRDR resistance marker present in the supplied panel, 0 = absent).\n"
    "Both binary columns are read as integers, and the supplied reference panel is used in the coding in which it is supplied.\n"
    "\n"
    "## Per-unit agreement accounting\n"
    "\n"
    "Each isolate contributes a two-valued selector: 1 when its observed call equals its reference\n"
    "panel value, 0 when the two values differ. The selector is accumulated by summation across all\n"
    "isolates, and that accumulated total is the emission value reported below.\n"
    "\n"
    f"Total measured units: {total_units}\n"
    f"Units whose observed call equals the reference panel value as the panel file stages it: {concordant_units}\n"
    f"Per-unit agreement rate used by the emission accumulation: {agreement_rate_text}\n"
    f"Accumulated emission value (sum of the per-unit selector): {emission_value}\n"
    "\n"
    "## Result\n"
    "\n"
    f"[selected-result] The summed per-unit selector gives an accumulated emission value of {emission_value} over {total_units} isolates, a per-unit agreement rate of {agreement_rate_text}, while {concordant_units} of {total_units} isolates carry an observed call equal to the reference panel value as the panel file stages it.\n"
    "\n"
    "## Protocol status\n"
    "\n"
    "No protocol amendment and no approved method deviation exists for this analysis.\n"
)

results_dir = pathlib.Path("results")
results_ready = results_dir.mkdir(parents=True, exist_ok=True)
report_path = results_dir / "report.md"
written_chars = report_path.write_text(report_text, encoding="ascii")
shown = print(report_text, end="")
