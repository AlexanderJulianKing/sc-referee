import csv
import fractions
import pathlib

DATA_PATH = pathlib.Path("inputs/data.csv")
REPORT_PATH = pathlib.Path("results/report.md")
OBSERVED_COLUMN = "pcr_call"
PANEL_COLUMN = "panel_allele"
MATCH_CREDIT = 1
MISMATCH_CREDIT = 0


def load_staged_table(source_path):
    handle = source_path.open("r", encoding="ascii", newline="")
    reader = csv.DictReader(handle)
    staged_rows = [dict(entry) for entry in reader]
    handle_closed = handle.close()
    return staged_rows


def observed_state(entry):
    return entry[OBSERVED_COLUMN]


def panel_state(entry):
    return entry[PANEL_COLUMN]


def concordance_credit(observed_value, panel_value):
    agreement_flag = observed_value == panel_value
    return MATCH_CREDIT * agreement_flag + MISMATCH_CREDIT * (1 - agreement_flag)


rows = load_staged_table(DATA_PATH)
total_units = len(rows)

emission_total = 0
for entry in rows:
    emission_total = emission_total + concordance_credit(observed_state(entry), panel_state(entry))

concordant_units = emission_total
discordant_units = total_units - concordant_units
agreement_rate = emission_total / total_units
agreement_fraction = fractions.Fraction(emission_total, total_units)

report_lines = [
    "# blaKPC Allele Concordance Audit",
    "",
    "## Scope",
    "",
    f"Measured units: {total_units} clinical Klebsiella pneumoniae isolates staged in inputs/data.csv.",
    "Observed call: per-isolate blaKPC PCR call, staged in column pcr_call as 0 or 1.",
    "Reference panel: per-isolate blaKPC allele supplied in column panel_allele as 0 or 1.",
    "The comparison reads each column in the coding in which inputs/data.csv stages it.",
    "",
    "## Concordance accounting",
    "",
    f"Total measured units: {total_units}",
    f"Units whose pcr_call equals the staged panel_allele: {concordant_units}",
    f"Units carrying the mismatch credit: {discordant_units}",
    f"Match credit per agreeing unit: {MATCH_CREDIT}",
    f"Mismatch credit per remaining unit: {MISMATCH_CREDIT}",
    f"Per-unit agreement rate used in the emission accumulation: {agreement_rate:.6f} ({agreement_fraction})",
    f"Accumulated concordance emission: {emission_total:.3f} credits",
    "",
    "## Selected result",
    "",
    f"[selected-result] Observed-versus-panel concordance across {total_units} measured isolates: {concordant_units} agreeing units at a per-unit agreement rate of {agreement_rate:.6f} ({agreement_fraction}), for an accumulated concordance emission of {emission_total:.3f} credits.",
    "",
    "## Provenance",
    "",
    "Every number above is computed by workflow/analysis.py from inputs/data.csv.",
    "No protocol amendment or approved method deviation exists.",
]
report_text = "\n".join(report_lines)
report_payload = report_text + "\n"
results_dir = REPORT_PATH.parent
directory_ready = results_dir.mkdir(parents=True, exist_ok=True)
characters_written = REPORT_PATH.write_text(report_payload, encoding="ascii")
report_echo = print(report_text)
