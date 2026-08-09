import csv
import pathlib
from fractions import Fraction

AGREE_WEIGHT = 1
DISAGREE_WEIGHT = 0
FULL_FACTOR = Fraction(1, 1)
HALF_FACTOR = Fraction(1, 2)
NEUTRAL_PRODUCT = Fraction(1, 1)
ZERO_TOTAL = Fraction(0, 1)

DATA_PATH = pathlib.Path("inputs") / "data.csv"
RESULTS_DIR = pathlib.Path("results")
REPORT_PATH = RESULTS_DIR / "report.md"


def match_selector(left_value, right_value):
    same = left_value == right_value
    return DISAGREE_WEIGHT + (AGREE_WEIGHT - DISAGREE_WEIGHT) * same


def emission_selector(left_value, right_value):
    same = left_value == right_value
    return HALF_FACTOR + (FULL_FACTOR - HALF_FACTOR) * same


raw_text = DATA_PATH.read_text(encoding="ascii")
text_lines = raw_text.splitlines()
reader = csv.DictReader(text_lines)
rows = [record for record in reader]
unit_count = len(rows)
positions = [index for index in range(unit_count)]
observed_values = [int(rows[index]["phenotype_resistant"]) for index in positions]
panel_values = [int(rows[index]["panel_gyra_marker"]) for index in positions]
complement_values = [1 - panel_values[index] for index in positions]
mic_values = [Fraction(rows[index]["mic_cipro_mg_per_l"]) for index in positions]

agreement_flags = [match_selector(observed_values[index], panel_values[index]) for index in positions]
complement_flags = [match_selector(observed_values[index], complement_values[index]) for index in positions]
emission_factors = [emission_selector(observed_values[index], panel_values[index]) for index in positions]

agreement_count = 0
for flag in agreement_flags:
    agreement_count = agreement_count + flag

complement_count = 0
for flag in complement_flags:
    complement_count = complement_count + flag

emission_product = NEUTRAL_PRODUCT
for factor in emission_factors:
    emission_product = emission_product * factor

observed_positive_count = 0
for value in observed_values:
    observed_positive_count = observed_positive_count + value

panel_positive_count = 0
for value in panel_values:
    panel_positive_count = panel_positive_count + value

mic_total = ZERO_TOTAL
for value in mic_values:
    mic_total = mic_total + value

mean_mic = mic_total / unit_count
mean_mic_value = float(mean_mic)
agreement_rate = Fraction(agreement_count, unit_count)
agreement_rate_value = float(agreement_rate)
emission_value = float(emission_product)
coverage_total = agreement_count + complement_count

report_text = (
    f"# Ciprofloxacin resistance: phenotype call vs reference panel gyrA marker\n"
    f"\n"
    f"## Dataset\n"
    f"\n"
    f"Measured units: {unit_count} clinical Escherichia coli isolates.\n"
    f"Observed call column: phenotype_resistant (1 = resistant by disc diffusion).\n"
    f"Reference column as staged: panel_gyra_marker (1 = resistant-associated gyrA allele).\n"
    f"Mean ciprofloxacin MIC across all isolates: {mean_mic_value:.6f} mg/L.\n"
    f"Isolates called resistant by phenotype: {observed_positive_count}.\n"
    f"Isolates carrying the panel resistance allele: {panel_positive_count}.\n"
    f"\n"
    f"## Concordance accounting\n"
    f"\n"
    f"Total measured units: {unit_count}\n"
    f"Units whose observed call equals the staged panel value: {agreement_count}\n"
    f"Per-unit agreement rate used by the emission accumulation: {agreement_rate} = {agreement_rate_value:.6f}\n"
    f"Per-unit emission factor: {FULL_FACTOR} on agreement, {HALF_FACTOR} on disagreement.\n"
    f"Accumulated emission value (product over all {unit_count} units): {emission_product} = {emission_value:.6f}\n"
    f"\n"
    f"## Quality control\n"
    f"\n"
    f"Complement check count (observed call equals 1 - staged panel value): {complement_count}\n"
    f"The complemented reference copy is an orientation control only; it never enters\n"
    f"the emission accumulation, which uses the panel values exactly as staged.\n"
    f"Agreement count plus complement check count: {coverage_total} (equals the total unit count).\n"
    f"\n"
    f"[selected-result] Accumulated emission value over {unit_count} isolates = {emission_product} = {emission_value:.6f}, from {agreement_count} of {unit_count} units in agreement (rate {agreement_rate_value:.6f}).\n"
)

made = RESULTS_DIR.mkdir(parents=True, exist_ok=True)
written = REPORT_PATH.write_text(report_text, encoding="ascii")
emitted = print(report_text, end="")
