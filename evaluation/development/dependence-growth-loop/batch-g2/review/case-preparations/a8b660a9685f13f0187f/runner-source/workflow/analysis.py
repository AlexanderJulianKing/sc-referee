"""Compare peak echolocation frequency between two summer bat roosts.

Reads data/input.csv and writes results/report.md.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

from scipy import stats

INPUT_PATH = Path("data") / "input.csv"
REPORT_PATH = Path("results") / "report.md"

BAT_COL = "bat_id"
SITE_COL = "roost_site"
FREQ_COL = "peak_frequency_khz"


def read_sessions():
    """One tuple per recording night: (bat, roost, peak frequency in kHz)."""
    sessions = []
    with INPUT_PATH.open("r", encoding="ascii", newline="") as handle:
        for row in csv.DictReader(handle):
            sessions.append((row[BAT_COL], row[SITE_COL], float(row[FREQ_COL])))
    return sessions


def mean(values):
    return sum(values) / len(values)


def sample_sd(values):
    centre = mean(values)
    spread = sum((value - centre) ** 2 for value in values)
    return math.sqrt(spread / (len(values) - 1))


def main():
    sessions = read_sessions()
    if not sessions:
        raise SystemExit("data/input.csv holds no recording sessions")

    site_order = []
    freq = {}
    bats = {}
    per_bat = {}
    for bat, site, khz in sessions:
        if site not in site_order:
            site_order.append(site)
            freq[site] = []
            bats[site] = set()
        freq[site].append(khz)
        bats[site].add(bat)
        per_bat[bat] = per_bat.get(bat, 0) + 1

    if len(site_order) != 2:
        raise SystemExit("expected recordings from exactly two roost sites")

    first, second = site_order
    counts = sorted(set(per_bat.values()))
    if len(counts) == 1:
        per_bat_label = str(counts[0])
    else:
        per_bat_label = "{0}-{1}".format(counts[0], counts[-1])

    left = freq[first]
    right = freq[second]

    outcome = stats.ttest_ind(left, right, equal_var=True)
    tstat = float(outcome.statistic)
    pvalue = float(outcome.pvalue)
    dof = len(left) + len(right) - 2

    pooled_sd = math.sqrt(
        ((len(left) - 1) * sample_sd(left) ** 2
         + (len(right) - 1) * sample_sd(right) ** 2) / dof
    )
    difference = mean(left) - mean(right)
    cohens_d = difference / pooled_sd
    direction = "higher" if difference > 0 else "lower"
    p_text = "< 0.0001" if pvalue < 1e-4 else "= {0:.4f}".format(pvalue)

    lines = [
        "# Peak echolocation frequency at two summer roosts",
        "",
        "## Data",
        "",
        "- Input file: `data/input.csv`",
        f"- Nightly recording sessions: {len(sessions)}",
        f"- Individual bats: {len(per_bat)}",
        f"- Sessions contributed per bat: {per_bat_label}",
        "",
        "| Roost site | Sessions | Bats | Mean peak frequency (kHz) | SD (kHz) |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for site in site_order:
        values = freq[site]
        lines.append(
            f"| {site} | {len(values)} | {len(bats[site])} |"
            f" {mean(values):.3f} | {sample_sd(values):.3f} |"
        )
    lines += [
        "",
        "## Analysis",
        "",
        f"Each of the {len(sessions)} rows in `data/input.csv` was entered as one observation in a",
        "two-sample Student t test (pooled variance, two-sided) comparing mean peak",
        f"echolocation frequency between the {first} sessions and the",
        f"{second} sessions.",
        "",
        "## Result",
        "",
        f"- Mean difference ({first} minus {second}): {difference:.3f} kHz",
        f"- Pooled standard deviation: {pooled_sd:.3f} kHz",
        f"- Standardised difference (Cohen's d): {cohens_d:.3f}",
        f"- Test statistic: t = {tstat:.3f} on df = {dof}",
        f"- Two-sided p-value: p {p_text}",
        "",
        f"[selected-result] Two-sample t test over {len(sessions)} nightly recording"
        f" sessions entered as {len(sessions)} observations: mean peak echolocation"
        f" frequency is {abs(difference):.3f} kHz {direction} at {first} than at {second}"
        f" (t = {tstat:.3f}, df = {dof}, p {p_text}).",
        "",
        f"The {len(per_bat)} bats each contributed {per_bat_label} nightly sessions, and those individual sessions",
        "were the units entered into the test reported above.",
    ]

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
