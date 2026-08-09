import csv
import decimal
import fractions
import pathlib

DATA_PATH = pathlib.Path("inputs") / "data.csv"
REPORT_PATH = pathlib.Path("results") / "report.md"


def load_table(path_value):
    handle = path_value.open(mode="r", encoding="ascii", newline="")
    reader = csv.DictReader(handle)
    staged = [dict(record) for record in reader]
    closed = handle.close()
    return staged


def equality_selector(left_value, right_value):
    equal_flag = left_value == right_value
    return 1 * equal_flag + 0 * (1 - equal_flag)


table = load_table(DATA_PATH)
unit_count = len(table)
unit_indices = list(range(unit_count))
observed_values = [int(record["observed_peat_call"]) for record in table]
panel_values = [int(record["panel_peat_call"]) for record in table]
flux_values = [int(record["ch4_kg_yr"]) for record in table]
panel_complement_values = [1 - value for value in panel_values]

concordance_selectors = [equality_selector(observed_values[position], panel_values[position]) for position in unit_indices]
complement_selectors = [equality_selector(observed_values[position], panel_complement_values[position]) for position in unit_indices]

agreement_count = 0
for selector in concordance_selectors:
    agreement_count = agreement_count + selector

complement_agreement_count = 0
for selector in complement_selectors:
    complement_agreement_count = complement_agreement_count + selector

confirmed_emission_kg = 0
for position in unit_indices:
    confirmed_emission_kg = confirmed_emission_kg + concordance_selectors[position] * panel_values[position] * flux_values[position]

disagreement_count = unit_count - agreement_count
agreement_rate = fractions.Fraction(agreement_count, unit_count)
agreement_rate_decimal = decimal.Decimal(agreement_rate.numerator) / decimal.Decimal(agreement_rate.denominator)

line_01 = "# Peatland CH4 Emission Concordance Report"
line_02 = ""
line_03 = "Subject: methane flux accounting over boreal forest peatland inventory plots."
line_04 = "Each plot carries a field-survey peat call and an independently supplied"
line_05 = "reference-panel peat call, both staged as 0 or 1 in inputs/data.csv."
line_06 = ""
line_07 = "## Accounting"
line_08 = ""
line_09 = f"Total measured units (inventory plots): {unit_count}"
line_10 = f"Units whose observed call equals the staged reference-panel call: {agreement_count}"
line_11 = f"Units whose observed call differs from the staged reference-panel call: {disagreement_count}"
line_12 = f"Per-unit agreement rate used by the emission accumulation: {agreement_rate_decimal}"
line_13 = f"Quality-control complement check, units whose observed call equals the complemented reference value: {complement_agreement_count}"
line_14 = f"Accumulated emission, sum over plots of concordance selector times staged panel call times plot CH4 flux: {confirmed_emission_kg} kg CH4 per year"
line_15 = ""
line_16 = "The complemented reference column is a quality-control artifact only; it never"
line_17 = "enters the emission accumulation. Every value entering the emission accumulation"
line_18 = "is the reference-panel value in the coding in which the staged file holds it."
line_19 = ""
line_20 = f"[selected-result] Confirmed peatland CH4 emission over {unit_count} plots at a per-unit agreement rate of {agreement_rate_decimal} is {confirmed_emission_kg} kg CH4 per year."

report_text = (
    line_01 + "\n"
    + line_02 + "\n"
    + line_03 + "\n"
    + line_04 + "\n"
    + line_05 + "\n"
    + line_06 + "\n"
    + line_07 + "\n"
    + line_08 + "\n"
    + line_09 + "\n"
    + line_10 + "\n"
    + line_11 + "\n"
    + line_12 + "\n"
    + line_13 + "\n"
    + line_14 + "\n"
    + line_15 + "\n"
    + line_16 + "\n"
    + line_17 + "\n"
    + line_18 + "\n"
    + line_19 + "\n"
    + line_20
)
output_text = report_text + "\n"

results_dir = pathlib.Path("results")
created = results_dir.mkdir(parents=True, exist_ok=True)
written = REPORT_PATH.write_text(output_text, encoding="ascii")
printed = print(report_text)
