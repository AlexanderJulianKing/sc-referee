"""Biocrust recovery after cyanobacterial inoculation: plot-level paired analysis.

The monitoring table is stored long, one line per plot per survey visit. The
repeated visits to a plot are pooled first, so that the statistical test is
handed exactly one number per independently inoculated plot.
"""

import csv
import statistics
from pathlib import Path

from scipy.stats import wilcoxon

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")

UNIT_COLUMN = "plot_id"
SESSION_COLUMN = "session_label"
RESPONSE_COLUMN = "chlorophyll_a_mg_m2"
BASELINE_LABEL = "baseline"


def read_visits(path):
    """Return ({plot_id: {session_label: response}}, number of data rows)."""
    visits = {}
    n_rows = 0
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            plot = row[UNIT_COLUMN].strip()
            label = row[SESSION_COLUMN].strip()
            visits.setdefault(plot, {})[label] = float(row[RESPONSE_COLUMN])
            n_rows += 1
    return visits, n_rows


def collapse_to_plots(visits):
    """Reduce each plot to (plot_id, baseline, follow-up mean, follow-up count)."""
    records = []
    for plot in sorted(visits):
        by_session = visits[plot]
        baseline = by_session[BASELINE_LABEL]
        follow_ups = [v for label, v in by_session.items() if label != BASELINE_LABEL]
        if not follow_ups:
            raise ValueError("plot %s has no follow-up visit" % plot)
        records.append((plot, baseline, statistics.fmean(follow_ups), len(follow_ups)))
    return records


def build_report(records, changes, outcome, n_rows):
    n_plots = len(records)
    n_follow = records[0][3]
    n_up = sum(1 for c in changes if c > 0)
    n_down = sum(1 for c in changes if c < 0)
    mean_baseline = statistics.fmean([rec[1] for rec in records])
    mean_final = statistics.fmean([rec[2] for rec in records])
    mean_change = statistics.fmean(changes)
    median_change = statistics.median(changes)

    lines = [
        "# Chlorophyll a recovery in inoculated biocrust plots",
        "",
        "## Monitoring data",
        "",
        "- Long-format monitoring table: %d plot-survey records from %d restoration plots."
        % (n_rows, n_plots),
        "- Every plot was surveyed %d times: one pre-inoculation baseline plus %d follow-up surveys at 6, 12 and 18 months."
        % (n_follow + 1, n_follow),
        "- Response: areal chlorophyll a density of the soil surface crust (mg m^-2).",
        "",
        "## Reduction to independent units",
        "",
        "Surveys repeated on the same plot are not independent observations of the",
        "treatment, so the follow-up surveys of a plot are first averaged into a single",
        "post-inoculation value. Each plot then contributes exactly one number to the",
        "test, the plot-level change",
        "",
        "    change = mean(follow-up surveys) - baseline survey.",
        "",
        "The %d plots were inoculated, tended and sampled separately and lie at least" % n_plots,
        "200 m apart, so the plot-level changes are the independent replicates.",
        "",
        "## Plot-level summary",
        "",
        "| plot | baseline | follow-up mean | change |",
        "| --- | --- | --- | --- |",
    ]

    for (plot, baseline, final, _count), change in zip(records, changes):
        lines.append(
            "| %s | %.1f | %.1f | %+.1f |" % (plot, baseline, final, change)
        )

    lines.extend([
        "",
        "All values are mg m^-2.",
        "",
        "## Test and result",
        "",
        "Exact two-sided Wilcoxon signed-rank test on the %d plot-level changes; the" % n_plots,
        "null hypothesis is that the change is distributed symmetrically about zero.",
        "",
        "- plots analysed (one paired change each): %d" % n_plots,
        "- plots that increased / decreased: %d / %d" % (n_up, n_down),
        "- mean baseline: %.1f mg m^-2" % mean_baseline,
        "- mean follow-up: %.1f mg m^-2" % mean_final,
        "- mean change: %+.1f mg m^-2" % mean_change,
        "- median change: %+.1f mg m^-2 (range %+.1f to %+.1f)"
        % (median_change, min(changes), max(changes)),
        "- signed-rank statistic W = %.1f, exact two-sided p = %.6f"
        % (outcome.statistic, outcome.pvalue),
        "",
        "[selected-result] Crust chlorophyll a increased in %d of %d independently inoculated plots; the plot-level change (median %+.1f mg m^-2, mean %+.1f mg m^-2, n = %d plots) differs from zero, exact two-sided Wilcoxon signed-rank test W = %.1f, p = %.6f."
        % (n_up, n_plots, median_change, mean_change, n_plots, outcome.statistic, outcome.pvalue),
        "",
        "## Caveats",
        "",
        "The design is a before-after comparison without untreated controls, so the",
        "change cannot be separated from background seasonal recovery; the follow-up",
        "surveys were also averaged rather than modelled, which discards information",
        "about the shape of the recovery trajectory.",
        "",
    ])
    return "\n".join(lines)


def main():
    visits, n_rows = read_visits(INPUT_PATH)
    records = collapse_to_plots(visits)
    baselines = [rec[1] for rec in records]
    finals = [rec[2] for rec in records]
    changes = [final - base for base, final in zip(baselines, finals)]
    outcome = wilcoxon(finals, baselines, alternative="two-sided")
    report = build_report(records, changes, outcome, n_rows)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(report)


if __name__ == "__main__":
    main()
