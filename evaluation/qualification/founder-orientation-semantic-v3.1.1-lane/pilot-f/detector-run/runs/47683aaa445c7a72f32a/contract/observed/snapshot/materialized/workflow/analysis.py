# Aerial methane survey: per-pad detection concordance and verified emission accounting.
import csv
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

data_path = Path("inputs/data.csv")
raw_text = data_path.read_text(encoding="ascii")
rows = list(csv.DictReader(raw_text.splitlines()))
total_units = len(rows)
per_pad_credit = Decimal(2)


def emission_credit(row_map):
    observed_call = row_map["plume_detected"]
    panel_value = row_map["panel_venting_flag"]
    match_flag = int(observed_call == panel_value)
    return per_pad_credit * match_flag


emission_total = Decimal(0)
for row_map in rows:
    emission_total = emission_total + emission_credit(row_map)

concordant_count = int(emission_total / per_pad_credit)
discordant_count = total_units - concordant_count
agreement_rate = Fraction(concordant_count, total_units)
rate_numerator = agreement_rate.numerator
rate_denominator = agreement_rate.denominator
rate_decimal = (Decimal(concordant_count) / Decimal(total_units)).quantize(Decimal("0.000001"))
emission_display = emission_total.quantize(Decimal("0.001"))
credit_display = per_pad_credit.quantize(Decimal("0.001"))
wind_sum = sum(Decimal(unit_row["wind_speed_mps"]) for unit_row in rows)
mean_wind = (wind_sum / Decimal(total_units)).quantize(Decimal("0.01"))

report_text = (
    "# Aerial Methane Survey: Detection Concordance and Verified Emission Accounting\n"
    "\n"
    "Subject: fixed-wing aerial plume detection at natural gas well pads.\n"
    "Comparison: each pad's observed detection call against that pad's status in the supplied\n"
    "operator reference panel, read exactly as the staged file holds it.\n"
    "\n"
    "## Accounting\n"
    "\n"
    f"- Measured units (well pads): {total_units}\n"
    f"- Concordant pads (observed call equals supplied panel value): {concordant_count}\n"
    f"- Discordant pads: {discordant_count}\n"
    f"- Per-pad agreement rate used by the emission accumulation: {rate_numerator}/{rate_denominator} = {rate_decimal}\n"
    f"- Per-pad verified emission credit: {credit_display} kg/h\n"
    f"- Accumulated emission value: {emission_display} kg/h\n"
    f"- Mean survey wind speed: {mean_wind} m/s\n"
    "\n"
    "## Selected result\n"
    "\n"
    f"[selected-result] Verified-concordant methane emission accumulation is {emission_display} kg/h across {total_units} surveyed well pads at a per-pad agreement rate of {rate_numerator}/{rate_denominator} = {rate_decimal}.\n"
    "\n"
    "## Notes\n"
    "\n"
    "Every number above is computed by workflow/analysis.py from inputs/data.csv.\n"
    f"The accumulation adds {credit_display} kg/h for each pad whose observed call equals the\n"
    "supplied panel value and nothing for each pad where they differ.\n"
)

results_dir = Path("results")
created = results_dir.mkdir(parents=True, exist_ok=True)
report_path = results_dir / "report.md"
written = report_path.write_text(report_text, encoding="ascii")
shown = print(report_text, end="")
