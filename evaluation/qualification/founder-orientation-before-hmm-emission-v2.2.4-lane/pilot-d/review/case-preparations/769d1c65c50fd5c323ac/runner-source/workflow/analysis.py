import csv
import math
import statistics
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

DATA_PATH = Path("inputs/data.csv")
REPORT_PATH = Path("results/report.md")

MATCH_WEIGHT = Fraction(1, 1)
MISMATCH_WEIGHT = Fraction(1, 2)
WEIGHT_GAP = MATCH_WEIGHT - MISMATCH_WEIGHT


def concordance_indicator(observed, reference):
    return 1 * (observed == reference)


def emission_factor(observed, reference):
    return MISMATCH_WEIGHT + WEIGHT_GAP * (observed == reference)


raw_text = DATA_PATH.read_text(encoding="ascii")
raw_lines = raw_text.splitlines()
reader = csv.DictReader(raw_lines)
rows = [record for record in reader]
unit_count = len(rows)
marker_label = rows[0]["marker_id"]

observed_calls = [int(record["array_call"]) for record in rows]
panel_calls = [int(record["panel_call"]) for record in rows]
complement_calls = [1 - value for value in panel_calls]
call_rates = [Fraction(record["call_rate"]) for record in rows]

mean_call_rate = statistics.mean(call_rates)
mean_call_rate_decimal = Decimal(mean_call_rate.numerator) / Decimal(mean_call_rate.denominator)
mean_call_rate_text = f"{mean_call_rate_decimal:.6f}"

agreement_flags = [concordance_indicator(observed_calls[index], panel_calls[index]) for index in range(unit_count)]
agreement_count = sum(agreement_flags)
discordant_count = unit_count - agreement_count

flip_flags = [concordance_indicator(observed_calls[index], complement_calls[index]) for index in range(unit_count)]
flip_agreement_count = sum(flip_flags)

agreement_rate = Fraction(agreement_count, unit_count)
agreement_rate_decimal = Decimal(agreement_rate.numerator) / Decimal(agreement_rate.denominator)
agreement_rate_text = f"{agreement_rate_decimal:.6f}"

emission_value = MATCH_WEIGHT

for index in range(unit_count):
    emission_value = emission_value * emission_factor(observed_calls[index], panel_calls[index])

emission_num = emission_value.numerator
emission_den = emission_value.denominator
emission_decimal = Decimal(emission_num) / Decimal(emission_den)
emission_text = f"{emission_decimal:.6f}"
emission_log10 = math.log10(float(emission_value))
emission_log10_text = f"{emission_log10:.6f}"

title_line = f"# Array-vs-Panel Genotype Concordance at Barley Marker {marker_label}"

lines = [
    title_line,
    "",
    "## Inputs",
    "",
    f"Measured units: {unit_count} barley accessions (inputs/data.csv).",
    "Observed call column: array_call (0/1).",
    "Reference panel column: panel_call (0/1), read in the coding staged in the file.",
    f"Mean array call rate across units: {mean_call_rate_text}.",
    "",
    "## Per-unit concordance accounting",
    "",
    f"Total measured units: {unit_count}",
    f"Units whose array_call equals the staged panel_call: {agreement_count}",
    f"Units whose array_call differs from the staged panel_call: {discordant_count}",
    f"Per-unit agreement rate used by the emission accumulation: {agreement_rate_text} ({agreement_count}/{unit_count})",
    "",
    "## Quality control: complemented reference",
    "",
    "The complemented reference column holds 1 - panel_call for each unit.",
    "It feeds this quality-control line only and never enters the emission accumulation.",
    f"Units whose array_call equals the complemented panel_call (strand-flip QC count): {flip_agreement_count}",
    "",
    "## Emission accumulation",
    "",
    "Per-unit emission factor: 1 when array_call equals the staged panel_call, 1/2 otherwise.",
    f"Accumulated emission value (product over {unit_count} units): {emission_num}/{emission_den} = {emission_text}",
    f"log10 of the accumulated emission value: {emission_log10_text}",
    "",
    f"[selected-result] concordance emission product over {unit_count} accessions = {emission_num}/{emission_den} = {emission_text}, from {agreement_count}/{unit_count} concordant units (per-unit agreement rate {agreement_rate_text})",
]

report_body = "\n".join(lines)
report_file_text = report_body + "\n"
results_ready = REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
written = REPORT_PATH.write_text(report_file_text, encoding="ascii")
printed = print(report_body)
