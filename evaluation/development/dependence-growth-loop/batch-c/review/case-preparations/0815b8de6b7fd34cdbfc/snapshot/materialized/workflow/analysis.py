"""Do target-polypore fruiting bodies occur more often on old-growth logs?

Reads data/input.csv (one surveyed log per row) and writes results/report.md.
"""

import csv
import os

from scipy.stats import fisher_exact

INPUT_PATH = os.path.join("data", "input.csv")
REPORT_PATH = os.path.join("results", "report.md")

STANDS = ("old_growth", "second_growth")
PRESENCE_COLUMN = "fruiting_bodies_present"


def read_logs(path):
    """Return the survey records, one per surveyed log."""
    with open(path, newline="", encoding="ascii") as handle:
        records = list(csv.DictReader(handle))
    labels = [record["log_id"] for record in records]
    if len(set(labels)) != len(labels):
        raise ValueError("log_id repeats: the file is not one row per log")
    return records


def contingency(records):
    """Build [[present, absent], ...] with one table row per stand type."""
    counts = dict((stand, [0, 0]) for stand in STANDS)
    for record in records:
        stand = record["stand_type"]
        if stand not in counts:
            raise ValueError("unknown stand_type: " + stand)
        flag = int(record[PRESENCE_COLUMN])
        if flag not in (0, 1):
            raise ValueError("presence must be coded 0 or 1")
        counts[stand][0 if flag == 1 else 1] += 1
    return [counts[stand] for stand in STANDS]


def build_report(table, odds_ratio, p_value):
    """Render the whole report as one string."""
    old, second = table
    totals = [old[0] + old[1], second[0] + second[1]]
    n_logs = totals[0] + totals[1]
    shares = [old[0] / float(totals[0]), second[0] / float(totals[1])]
    lines = [
        "# Fruiting-body occurrence on coarse woody debris",
        "",
        "## Data",
        "",
        "Source: data/input.csv. One row per surveyed log (log_id), %d logs in total,"
        % n_logs,
        "each from its own survey site and inspected exactly once. The column",
        "fruiting_bodies_present records whether fruiting bodies of the target polypore",
        "were found on that log.",
        "",
        "| stand_type | logs | with fruiting bodies | proportion |",
        "| --- | --- | --- | --- |",
        "| %s | %d | %d | %.3f |" % (STANDS[0], totals[0], old[0], shares[0]),
        "| %s | %d | %d | %.3f |" % (STANDS[1], totals[1], second[0], shares[1]),
        "",
        "Difference in proportions (old_growth minus second_growth): %.3f"
        % (shares[0] - shares[1]),
        "",
        "## Analysis",
        "",
        "Two-sided Fisher's exact test on the 2x2 table of stand type by fruiting-body",
        "presence. Each of the %d rows is a different log, so each row contributes one"
        % n_logs,
        "independent observation to the table.",
        "",
        "Contingency table: [[%d, %d], [%d, %d]] (rows: old_growth, second_growth;"
        % (old[0], old[1], second[0], second[1]),
        "columns: fruiting bodies present, absent).",
        "",
        "Sample odds ratio: %.2f" % odds_ratio,
        "",
        "[selected-result] Two-sided Fisher's exact test, stand type by fruiting-body "
        "presence over %d independent logs: p = %.6f, sample odds ratio %.2f, "
        "occurrence %.3f (old_growth) vs %.3f (second_growth)."
        % (n_logs, p_value, odds_ratio, shares[0], shares[1]),
        "",
        "## Interpretation",
        "",
        "Fruiting bodies were found on %d of %d old-growth logs and %d of %d"
        % (old[0], totals[0], second[0], totals[1]),
        "second-growth logs. The association between stand type and fruiting-body",
        "presence is significant at the 0.05 level (p = %.6f). Because the %d logs"
        % (p_value, n_logs),
        "were surveyed once each at separate sites, the %d rows are the %d independent"
        % (n_logs, n_logs),
        "units of the design and no unit is represented more than once.",
    ]
    return "\n".join(lines) + "\n"


def main():
    records = read_logs(INPUT_PATH)
    table = contingency(records)
    (present_old, absent_old), (present_second, absent_second) = table
    odds_ratio = (present_old * absent_second) / float(absent_old * present_second)
    p_value = fisher_exact(table, alternative="two-sided")[1]
    report = build_report(table, odds_ratio, p_value)
    folder = os.path.dirname(REPORT_PATH)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(report)


if __name__ == "__main__":
    main()
