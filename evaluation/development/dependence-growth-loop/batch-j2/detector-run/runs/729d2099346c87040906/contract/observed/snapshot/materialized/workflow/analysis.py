"""Porosity screening of laser powder-bed fusion (LPBF) test coupons.

Reads data/input.csv and writes results/report.md. The question is whether the
elevated laser-power setting changes the fraction of coupons that clear the CT
porosity screen.
"""

from __future__ import annotations

import csv
from pathlib import Path

from scipy.stats import fisher_exact

INPUT_PATH = Path("data/input.csv")
OUTPUT_PATH = Path("results/report.md")

SETTINGS = ("nominal", "elevated")
PASS_LABEL = "pass"


def read_coupons(path):
    with path.open(newline="", encoding="utf-8") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    if not rows:
        raise SystemExit("no coupon rows found in " + str(path))
    return rows


def outcome_counts(rows, setting):
    """Return (passed, failed) coupon counts for one laser-power setting."""
    total = sum(1 for row in rows if row["laser_setting"] == setting)
    passed = sum(
        1
        for row in rows
        if row["laser_setting"] == setting and row["porosity_screen"] == PASS_LABEL
    )
    return passed, total - passed


def build_report(rows):
    counts = {setting: outcome_counts(rows, setting) for setting in SETTINGS}
    table = [list(counts[setting]) for setting in SETTINGS]
    odds_ratio, p_value = fisher_exact(table, alternative="two-sided")

    rates = {}
    table_lines = []
    for setting in SETTINGS:
        passed, failed = counts[setting]
        total = passed + failed
        rate = 100.0 * passed / total
        rates[setting] = rate
        table_lines.append(
            "| {0} | {1} | {2} | {3} | {4:.1f}% |".format(
                setting, total, passed, failed, rate
            )
        )

    n_rows = len(rows)
    runs = sorted({row["print_run_id"] for row in rows})
    diff = rates["elevated"] - rates["nominal"]

    nom_pass, nom_fail = counts["nominal"]
    ele_pass, ele_fail = counts["elevated"]
    nom_n = nom_pass + nom_fail
    ele_n = ele_pass + ele_fail

    lines = [
        "# Porosity screen pass rates for laser powder-bed fusion coupons",
        "",
        "## Data",
        "",
        "Source: data/input.csv -- {0} coupon rows spanning {1} print runs.".format(
            n_rows, len(runs)
        ),
        "",
        "| Laser setting | Coupons | Passed | Failed | Pass rate |",
        "| --- | --- | --- | --- | --- |",
    ]
    lines.extend(table_lines)
    lines.extend(
        [
            "",
            "Pass-rate difference (elevated minus nominal): {0:.1f} percentage points.".format(
                diff
            ),
            "",
            "## Analysis",
            "",
            "Two-sided Fisher exact test applied to the 2x2 table of porosity-screen",
            "outcome by laser-power setting; each coupon row supplies one observation.",
            "",
            "## Result",
            "",
            (
                "[selected-result] Two-sided Fisher exact test on {0} coupons: "
                "{1}/{2} ({3:.1f}%) passed at the nominal setting versus "
                "{4}/{5} ({6:.1f}%) at the elevated setting; odds ratio {7:.4f}, "
                "p = {8:.4f}."
            ).format(
                n_rows,
                nom_pass,
                nom_n,
                rates["nominal"],
                ele_pass,
                ele_n,
                rates["elevated"],
                odds_ratio,
                p_value,
            ),
            "",
            "Print runs represented: {0}.".format(", ".join(runs)),
        ]
    )
    return "\n".join(lines) + "\n"


def main():
    rows = read_coupons(INPUT_PATH)
    report = build_report(rows)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
