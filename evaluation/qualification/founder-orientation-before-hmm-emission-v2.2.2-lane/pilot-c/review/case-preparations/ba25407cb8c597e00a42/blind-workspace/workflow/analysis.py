import csv
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

CASE_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = CASE_ROOT / "inputs" / "data.csv"
REPORT_PATH = CASE_ROOT / "results" / "report.md"

MATCH_WEIGHT = Fraction(1, 1)
MISS_WEIGHT = Fraction(1, 4)


def read_table(source_path):
    raw_text = source_path.read_text(encoding="ascii")
    reader = csv.DictReader(raw_text.splitlines())
    return [dict(record) for record in reader]


def concordance_weight(observed_value, panel_value):
    return MISS_WEIGHT + (MATCH_WEIGHT - MISS_WEIGHT) * (observed_value == panel_value)


def write_report(target_path, payload_text):
    target_path.parent.mkdir(parents=True, exist_ok=True)
    return target_path.write_text(payload_text, encoding="ascii")


table_rows = read_table(DATA_PATH)
unit_count = len(table_rows)
observed_calls = [int(record["observed_resistance_call"]) for record in table_rows]
panel_values = [int(record["panel_gyra_marker"]) for record in table_rows]
weight_values = [concordance_weight(observed_calls[position], panel_values[position]) for position in range(unit_count)]

emission_total = Fraction(0, 1)
for weight_value in weight_values:
    emission_total = emission_total + weight_value

observed_positive_total = 0
for observed_entry in observed_calls:
    observed_positive_total = observed_positive_total + observed_entry

panel_positive_total = 0
for panel_entry in panel_values:
    panel_positive_total = panel_positive_total + panel_entry

matched_fraction = (emission_total - MISS_WEIGHT * unit_count) / (MATCH_WEIGHT - MISS_WEIGHT)
agreement_count = matched_fraction.numerator
agreement_rate = Fraction(agreement_count, unit_count)
emission_decimal = Decimal(emission_total.numerator) / Decimal(emission_total.denominator)
rate_decimal = Decimal(agreement_rate.numerator) / Decimal(agreement_rate.denominator)
match_decimal = Decimal(MATCH_WEIGHT.numerator) / Decimal(MATCH_WEIGHT.denominator)
miss_decimal = Decimal(MISS_WEIGHT.numerator) / Decimal(MISS_WEIGHT.denominator)

report_text = f"""# Ciprofloxacin resistance calls versus the supplied gyrA reference panel

## Scope

Measured unit: one Escherichia coli clinical isolate.
Observed call: phenotypic ciprofloxacin resistance from broth microdilution (1 = resistant, 0 = susceptible).
Reference call: gyrA QRDR marker as held in the supplied reference panel (1 = marker present, 0 = marker absent).
The reference panel is used in the coding in which it is supplied.

## Accounting

Total measured units: {unit_count}
Units called resistant by the observed phenotype: {observed_positive_total}
Units carrying the panel marker: {panel_positive_total}
Per-unit concordance weight: {match_decimal:.2f} when the observed call equals the panel value, {miss_decimal:.2f} when it does not.
Units whose observed call equals the supplied panel value: {agreement_count}
Per-unit agreement rate used by the emission accumulation: {rate_decimal:.6f}
Accumulated emission value (sum of the per-unit concordance weights): {emission_decimal:.4f}

[selected-result] Observed-versus-panel agreement is {agreement_count} of {unit_count} units, per-unit agreement rate {rate_decimal:.6f}, accumulated emission value {emission_decimal:.4f}.

## Notes

The reported agreement count, agreement rate and accumulated emission value all come from the one per-unit equality comparison between the observed call column and the supplied panel column.
"""

written_length = write_report(REPORT_PATH, report_text)
print(report_text, end="")
