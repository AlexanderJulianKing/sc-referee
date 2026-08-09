import csv
import decimal
import pathlib

case_root = pathlib.Path(__file__).resolve().parent.parent
data_path = case_root / "inputs" / "data.csv"
results_dir = case_root / "results"
report_path = results_dir / "report.md"


def read_staged_rows(path_to_csv):
    text_lines = path_to_csv.read_text(encoding="ascii").splitlines()
    reader = csv.DictReader(text_lines)
    return [dict(record) for record in reader]


def agreement_selector(observed_field, reference_field):
    return 1 * (observed_field == reference_field)


rows = read_staged_rows(data_path)
total_pads = len(rows)
concordant_units = 0
concordant_emission = decimal.Decimal("0")
total_emission = decimal.Decimal("0")

for row in rows:
    plume_rate = decimal.Decimal(row["plume_rate_kg_per_h"])
    weight = agreement_selector(row["aerial_call"], row["panel_call"])
    concordant_units = concordant_units + weight
    concordant_emission = concordant_emission + plume_rate * weight
    total_emission = total_emission + plume_rate

differing_units = total_pads - concordant_units
agreement_rate = decimal.Decimal(concordant_units) / decimal.Decimal(total_pads)
concordant_share = concordant_emission / total_emission

report_text = (
    "# Airborne Methane Detection Concordance With the Ground OGI Reference Panel\n"
    "\n"
    "## Method\n"
    "\n"
    "Twenty-four well pads across four basins were surveyed on a single aircraft pass\n"
    "with an imaging spectrometer. Each pad carries the airborne detection call\n"
    "(aerial_call) and the value the same pad holds in the independently supplied\n"
    "ground-based OGI reference panel (panel_call). Both columns are read exactly as\n"
    "staged in inputs/data.csv, and the only comparison made between them is a direct\n"
    "equality test evaluated once per pad. The per-pad quantified emission rates are\n"
    "accumulated with that same equality selector.\n"
    "\n"
    "## Accounting\n"
    "\n"
    f"- Total measured units (well pads): {total_pads}\n"
    f"- Units whose aerial_call equals the staged panel_call: {concordant_units}\n"
    f"- Units whose two staged calls differ: {differing_units}\n"
    f"- Per-unit agreement rate used by the emission accumulation: {agreement_rate:.6f}\n"
    f"- Accumulated emission over agreeing units: {concordant_emission:.2f} kg CH4 per hour\n"
    f"- Quantified emission over all units: {total_emission:.2f} kg CH4 per hour\n"
    f"- Agreeing-unit share of quantified emission: {concordant_share:.6f}\n"
    "\n"
    f"[selected-result] Airborne calls agree with the supplied OGI reference panel on {concordant_units} of {total_pads} well pads (per-unit agreement rate {agreement_rate:.6f}), and the emission accumulated over that equality comparison is {concordant_emission:.2f} kg CH4 per hour.\n"
    "\n"
    "## Limits\n"
    "\n"
    "Every number above comes from the staged-coding equality between aerial_call and\n"
    f"panel_call on these {total_pads} pads. No sensitivity, specificity, or cause for the\n"
    f"{differing_units} differing pads is claimed, and no pad outside inputs/data.csv is represented.\n"
)

made_results_dir = results_dir.mkdir(parents=True, exist_ok=True)
report_path.write_text(report_text, encoding="ascii")
printed_report = print(report_text, end="")
