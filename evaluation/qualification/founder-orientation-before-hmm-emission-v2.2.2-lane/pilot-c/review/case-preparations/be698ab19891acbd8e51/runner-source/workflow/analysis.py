import csv
from fractions import Fraction
from pathlib import Path


def agreement_weight(left_value, right_value, hit, miss):
    flag = int(left_value == right_value)
    return hit * flag + miss * (1 - flag)


data_path = Path("inputs/data.csv")
raw_text = data_path.read_text(encoding="ascii")
raw_lines = raw_text.splitlines()
reader = csv.DictReader(raw_lines)
rows = [row for row in reader]
total_units = len(rows)
observed_values = [int(row["observed_call"]) for row in rows]
panel_values = [int(row["panel_allele"]) for row in rows]
depth_values = [int(row["read_depth"]) for row in rows]
complement_values = [1 - value for value in panel_values]
hit_weight = Fraction(1, 1)
miss_weight = Fraction(1, 10)
agreement_flags = [agreement_weight(observed_values[index], panel_values[index], 1, 0) for index in range(total_units)]
complement_flags = [agreement_weight(observed_values[index], complement_values[index], 1, 0) for index in range(total_units)]
emission_weights = [agreement_weight(observed_values[index], panel_values[index], hit_weight, miss_weight) for index in range(total_units)]
agreement_count = sum(agreement_flags)
complement_match_count = sum(complement_flags)
discordant_count = total_units - agreement_count
qc_total = agreement_count + complement_match_count
agreement_rate = Fraction(agreement_count, total_units)
agreement_rate_float = float(agreement_rate)
depth_total = sum(depth_values)
mean_depth = Fraction(depth_total, total_units)
mean_depth_float = float(mean_depth)
emission_value = Fraction(1, 1)
for weight in emission_weights:
    emission_value = emission_value * weight
emission_float = float(emission_value)
report_text = (
    f"# Panel-concordance emission for a {total_units}-site assayed haplotype\n"
    f"\n"
    f"Subject: short-read genotype calls at {total_units} biallelic autosomal sites, compared\n"
    f"against the allele carried by the same sites in reference panel HG-PANEL-A.\n"
    f"\n"
    f"## Input accounting\n"
    f"\n"
    f"- measured units (assayed variant sites): {total_units}\n"
    f"- mean read depth across sites: {mean_depth_float:.2f}\n"
    f"- per-site emission weight when the observed call equals the staged panel allele: {hit_weight}\n"
    f"- per-site emission weight when they differ: {miss_weight}\n"
    f"\n"
    f"## Concordance accounting\n"
    f"\n"
    f"- sites whose observed call equals the staged panel allele: {agreement_count}\n"
    f"- per-unit agreement rate used by the emission accumulation: {agreement_rate} = {agreement_rate_float:.6f}\n"
    f"- discordant sites (total minus concordant): {discordant_count}\n"
    f"\n"
    f"## Quality-control comparison (not used in the emission)\n"
    f"\n"
    f"- sites whose observed call equals the strand-complemented panel value (1 - panel allele): {complement_match_count}\n"
    f"- control check, concordant + complement-matching sites = total: {agreement_count} + {complement_match_count} = {qc_total}\n"
    f"\n"
    f"## Emission\n"
    f"\n"
    f"- accumulated emission value (product of the {total_units} per-site weights): {emission_value} = {emission_float:.12f}\n"
    f"\n"
    f"[selected-result] panel-concordance emission for HG-PANEL-A over {total_units} assayed sites = {emission_value} = {emission_float:.12f} at agreement rate {agreement_rate} = {agreement_rate_float:.6f}\n"
)
report_path = Path("results/report.md")
report_dir = report_path.parent
made_dir = report_dir.mkdir(parents=True, exist_ok=True)
written = report_path.write_text(report_text, encoding="ascii", newline="\n")
printed = print(report_text, end="")
