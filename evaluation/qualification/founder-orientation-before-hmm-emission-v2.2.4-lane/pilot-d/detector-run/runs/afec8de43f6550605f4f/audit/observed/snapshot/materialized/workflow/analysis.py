# Confirmed methane emission inventory from well pad leak screening.
import csv
from pathlib import Path

DATA_PATH = Path("inputs/data.csv")
REPORT_PATH = Path("results/report.md")
SELECTOR_MATCH = 1
SELECTOR_MISMATCH = 0


def load_table(path):
    text = path.read_text(encoding="ascii")
    lines = text.splitlines()
    reader = csv.DictReader(lines)
    records = [dict(item) for item in reader]
    return records


def agreement_selector(observed_value, panel_value):
    indicator = int(observed_value == panel_value)
    weighted = SELECTOR_MISMATCH + (SELECTOR_MATCH - SELECTOR_MISMATCH) * indicator
    return weighted


def emit_report(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="ascii")
    print(text, end="")
    return len(text)


rows = load_table(DATA_PATH)
total_units = len(rows)
observed_calls = [int(record["observed_leak_call"]) for record in rows]
panel_calls = [int(record["panel_leak_call"]) for record in rows]
daily_rates = [int(record["measured_kg_per_day"]) for record in rows]
selectors = [agreement_selector(observed_calls[index], panel_calls[index]) for index in range(total_units)]
concordant_units = sum(selectors)
agreement_rate = concordant_units / total_units
emission_terms = [daily_rates[index] * selectors[index] for index in range(total_units)]
confirmed_emission = sum(emission_terms)
gross_emission = sum(daily_rates)
report_text = f"""# Confirmed Methane Emission Inventory from Well Pad Leak Screening

## Method

Each well pad in this survey carries two binary records: the observed field-survey
leak call recorded on site, and the leak call the same pad carries in the
independently supplied aerial reference panel. The workflow compares the two records
for each pad with a single equality selector, in the coding in which the reference
panel is supplied.

## Accounting

- Total measured units (well pads): {total_units}
- Units whose observed call equals the reference-panel call: {concordant_units}
- Per-unit agreement rate used by the emission accumulation: {agreement_rate:.4f}
- Accumulated confirmed emission value: {confirmed_emission} kg per day

The accumulated emission value is the sum, over all {total_units} pads, of each pad's
measured daily emission rate multiplied by that pad's agreement selector, so only the
{concordant_units} pads whose two calls agree contribute to the total. The surveyed
daily rate summed over all pads without the selector is {gross_emission} kg per day.

## Result

[selected-result] Confirmed methane emission inventory: {confirmed_emission} kg per day, from {concordant_units} of {total_units} well pads in agreement (per-unit agreement rate {agreement_rate:.4f}).
"""
written_chars = emit_report(REPORT_PATH, report_text)
