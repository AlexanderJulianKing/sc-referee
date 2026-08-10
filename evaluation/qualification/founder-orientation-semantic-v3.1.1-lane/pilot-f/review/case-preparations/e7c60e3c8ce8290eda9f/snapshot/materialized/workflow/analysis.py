import csv
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

case_root = Path(__file__).resolve().parent.parent
data_path = case_root / "inputs" / "data.csv"
report_path = case_root / "results" / "report.md"


def load_table(source_path):
    raw_text = source_path.read_text(encoding="ascii")
    reader = csv.DictReader(raw_text.splitlines())
    staged = [dict(record) for record in reader]
    return staged


def equality_selector(left_value, right_value, hit_value, miss_value):
    flag = 1 * (left_value == right_value)
    return miss_value + flag * (hit_value - miss_value)


table = load_table(data_path)
unit_total = len(table)
observed_calls = [int(record["observed_resistant"]) for record in table]
panel_a_calls = [int(record["panel_a_resistant"]) for record in table]
panel_b_calls = [int(record["panel_b_resistant"]) for record in table]
zone_values = [int(record["zone_diameter_mm"]) for record in table]

observed_resistant_total = 0
for observed_value in observed_calls:
    observed_resistant_total = observed_resistant_total + observed_value

panel_a_resistant_total = 0
for panel_a_value in panel_a_calls:
    panel_a_resistant_total = panel_a_resistant_total + panel_a_value

panel_b_resistant_total = 0
for panel_b_value in panel_b_calls:
    panel_b_resistant_total = panel_b_resistant_total + panel_b_value

zone_total = 0
for zone_value in zone_values:
    zone_total = zone_total + zone_value

mean_zone = Decimal(zone_total) / Decimal(unit_total)

agree_a_count = 0
for index in range(unit_total):
    agree_a_count = agree_a_count + equality_selector(observed_calls[index], panel_a_calls[index], 1, 0)

agree_b_count = 0
for index in range(unit_total):
    agree_b_count = agree_b_count + equality_selector(observed_calls[index], panel_b_calls[index], 1, 0)

disagree_a_count = unit_total - agree_a_count
agreement_fraction = Fraction(agree_a_count, unit_total)
hit_weight = Decimal(agree_a_count) / Decimal(unit_total)
miss_weight = Decimal(disagree_a_count) / Decimal(unit_total)

emission_value = Decimal(1)
for index in range(unit_total):
    emission_value = emission_value * equality_selector(observed_calls[index], panel_a_calls[index], hit_weight, miss_weight)

report_text = f"""# Ciprofloxacin resistance calls versus two reference marker panels

## Units and staging

Measured units: {unit_total} clinical Escherichia coli isolates.
Observed call column: observed_resistant (1 = disk-diffusion resistant phenotype).
Primary reference column: panel_a_resistant (curated QRDR mutation panel), used exactly as staged.
Second reference column: panel_b_resistant (independent PMQR and efflux marker panel), used exactly as staged.
Mean inhibition-zone diameter: {mean_zone:.2f} mm.
Isolates resistant by observed phenotype: {observed_resistant_total}.
Isolates resistant by panel A: {panel_a_resistant_total}.
Isolates resistant by panel B: {panel_b_resistant_total}.

## Concordance accounting

Units whose observed call equals the staged panel A value: {agree_a_count} of {unit_total}.
Units whose observed call and staged panel A value are not equal: {disagree_a_count} of {unit_total}.
Per-unit agreement rate used by the emission accumulation: {hit_weight} (= {agreement_fraction} in lowest terms).
Per-unit disagreement weight used by the emission accumulation: {miss_weight}.
Second-reference check, units whose observed call equals the staged panel B value: {agree_b_count} of {unit_total}.

## Emission accumulation

The emission value is the product over all {unit_total} isolates, contributing {hit_weight} for each
isolate whose observed call equals its staged panel A value and {miss_weight} for each isolate
where the two values are not equal: {hit_weight}^{agree_a_count} * {miss_weight}^{disagree_a_count}.

Accumulated emission value: {emission_value}

[selected-result] Panel A emission over {unit_total} isolates at per-unit agreement rate {hit_weight} = {emission_value}
"""

created_dir = report_path.parent.mkdir(parents=True, exist_ok=True)
written_chars = report_path.write_text(report_text, encoding="ascii")
echo_status = print(report_text, end="")
