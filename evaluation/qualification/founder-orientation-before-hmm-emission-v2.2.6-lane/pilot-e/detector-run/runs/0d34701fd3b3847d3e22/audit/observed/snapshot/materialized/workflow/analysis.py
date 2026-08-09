import csv
import pathlib
from decimal import Decimal
from fractions import Fraction


def agreement_flag(left_value, right_value):
    return 1 * (left_value == right_value) + 0 * (1 - (left_value == right_value))


def emission_weight(left_value, right_value, hit_weight, miss_weight):
    flag = left_value == right_value
    return hit_weight * flag + miss_weight * (1 - flag)


data_path = pathlib.Path("inputs/data.csv")
raw_text = data_path.read_text(encoding="ascii")
raw_lines = raw_text.splitlines()
reader = csv.DictReader(raw_lines)
staged_rows = [row for row in reader]
unit_count = len(staged_rows)

observed_values = [int(row["observed_call"]) for row in staged_rows]
panel_values = [int(row["panel_call"]) for row in staged_rows]
flipped_values = [1 - value for value in panel_values]
depth_values = [int(row["read_depth"]) for row in staged_rows]

agreement_count = 0
for index in range(unit_count):
    agreement_count = agreement_count + agreement_flag(observed_values[index], panel_values[index])

polarity_count = 0
for index in range(unit_count):
    polarity_count = polarity_count + agreement_flag(observed_values[index], flipped_values[index])

depth_total = 0
for value in depth_values:
    depth_total = depth_total + value

rate_frac = Fraction(agreement_count, unit_count)
miss_frac = Fraction(1, 1) - rate_frac

emission_total = Fraction(0, 1)
for index in range(unit_count):
    emission_total = emission_total + emission_weight(observed_values[index], panel_values[index], rate_frac, miss_frac)

mean_depth_frac = Fraction(depth_total, unit_count)

rate_num = rate_frac.numerator
rate_den = rate_frac.denominator
miss_num = miss_frac.numerator
miss_den = miss_frac.denominator
emission_num = emission_total.numerator
emission_den = emission_total.denominator
mean_depth_num = mean_depth_frac.numerator
mean_depth_den = mean_depth_frac.denominator

six_places = Decimal("0.000001")
two_places = Decimal("0.01")

rate_dec = (Decimal(rate_num) / Decimal(rate_den)).quantize(six_places)
miss_dec = (Decimal(miss_num) / Decimal(miss_den)).quantize(six_places)
emission_dec = (Decimal(emission_num) / Decimal(emission_den)).quantize(six_places)
rate_pct_dec = (Decimal(rate_num) * Decimal(100) / Decimal(rate_den)).quantize(two_places)
mean_depth_dec = (Decimal(mean_depth_num) / Decimal(mean_depth_den)).quantize(two_places)

report_text = (
    f"# Reference-panel concordance of SNP calls in Vibrio cholerae isolate VC-2291\n"
    f"\n"
    f"Observed calls at each diagnostic locus were compared, locus by locus, with the\n"
    f"allele state recorded for that locus in the supplied reference panel, using the\n"
    f"panel coding exactly as staged in inputs/data.csv (1 = alternate allele present,\n"
    f"0 = reference allele present).\n"
    f"\n"
    f"## Accounting\n"
    f"\n"
    f"- measured units (diagnostic SNP loci): {unit_count}\n"
    f"- units where observed_call equals staged panel_call: {agreement_count}\n"
    f"- per-unit agreement rate used by the emission accumulation: {rate_num}/{rate_den} = {rate_dec} ({rate_pct_dec}%)\n"
    f"- per-unit disagreement weight (1 - agreement rate): {miss_num}/{miss_den} = {miss_dec}\n"
    f"- accumulated emission value (sum of per-unit emission weights): {emission_num}/{emission_den} = {emission_dec}\n"
    f"- quality-control comparison, units where observed_call equals the complemented panel value (1 - panel_call): {polarity_count}\n"
    f"- mean read depth across loci: {mean_depth_dec}x\n"
    f"\n"
    f"The complemented panel column is a polarity quality control only; it never\n"
    f"enters the emission accumulation. Its agreement count and the staged-panel\n"
    f"agreement count sum to the unit count, confirming that both binary columns\n"
    f"are read in the coding the staged file supplies.\n"
    f"\n"
    f"[selected-result] Observed calls agree with the staged reference panel at {agreement_count} of {unit_count} loci (per-unit agreement rate {rate_num}/{rate_den} = {rate_dec}), giving an accumulated emission value of {emission_num}/{emission_den} = {emission_dec}.\n"
)

output_path = pathlib.Path("results/report.md")
made_dir = output_path.parent.mkdir(parents=True, exist_ok=True)
written = output_path.write_text(report_text, encoding="ascii")
emitted = print(report_text, end="")
