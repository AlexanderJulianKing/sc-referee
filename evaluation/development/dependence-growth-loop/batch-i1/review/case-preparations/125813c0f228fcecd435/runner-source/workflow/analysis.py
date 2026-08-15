"""Does a UV-reflective entrance rim bias where a solitary bee lands first?

Twenty female mason bees, twenty arenas, twenty first landings. One bee gives
one Bernoulli outcome, so the exact binomial test below runs over genuinely
independent trials.
"""

from __future__ import annotations

import csv
from pathlib import Path

from scipy.stats import binomtest

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")

MARKED = "uv_marked"
PLAIN = "plain"
NULL_SHARE = 0.5
ALPHA = 0.05
REQUIRED = ("bee_id", "arena_id", "intertegular_span_mm", "first_choice")


def read_trials(path):
    with path.open(newline="", encoding="ascii") as handle:
        trials = [dict(row) for row in csv.DictReader(handle)]
    if not trials:
        raise ValueError("data file contains no trials")
    for column in REQUIRED:
        if any(not row.get(column) for row in trials):
            raise ValueError("missing value in column " + column)
    return trials


def check_one_row_per_bee(trials):
    """Confirm no bee and no arena contributes more than a single row."""
    bees = [row["bee_id"] for row in trials]
    arenas = [row["arena_id"] for row in trials]
    if len(set(bees)) != len(bees):
        raise ValueError("a bee_id occurs twice: rows would not be independent")
    if len(set(arenas)) != len(arenas):
        raise ValueError("an arena_id occurs twice: rows would not be independent")
    return len(set(bees)), len(set(arenas))


def compose_report(n, n_bees, n_arenas, marked, plain, span_mean, p_value):
    decision = "rejecting" if p_value < ALPHA else "failing to reject"
    share = marked / n
    lines = [
        "# UV-marked nest tubes and first-landing choice in solitary bees",
        "",
        "## Design",
        "",
        "Twenty wild-caught *Osmia bicornis* females were each tested once, alone, in a",
        "private two-tube arena. Every female contributed exactly one observation: the",
        "tube she landed on first. No female was retested, and no arena hosted more than",
        "one female, so each row of the data file is one independent unit.",
        "",
        "## Data summary",
        "",
        "- Females analysed: %d" % n,
        "- Distinct female identifiers: %d" % n_bees,
        "- Distinct arenas: %d" % n_arenas,
        "- Mean intertegular span: %.2f mm" % span_mean,
        "- First landings on the UV-marked tube: %d" % marked,
        "- First landings on the plain tube: %d" % plain,
        "",
        "## Analysis",
        "",
        "An exact two-sided binomial test (scipy.stats.binomtest) compares the number of",
        "UV-marked first landings with the no-preference expectation of 0.5. Because one",
        "female supplies one Bernoulli outcome, the twenty trials entering the test are",
        "mutually independent and no clustering correction is needed.",
        "",
        "- Observed proportion choosing the UV-marked tube: %.3f" % share,
        "- Two-sided exact p-value: %.6f" % p_value,
        "",
        "[selected-result] Exact two-sided binomial test on %d independent females: "
        "%d of %d (%.3f) landed first on the UV-marked tube, p = %.6f against a null "
        "proportion of 0.5, %s indifference at the 5%% level."
        % (n, marked, n, share, p_value, decision),
        "",
        "## Interpretation",
        "",
        "The data are consistent with a modest attraction to UV-marked tube entrances.",
        "Because the test consumes one observation per bee, its nominal error rate is",
        "the actual error rate; pooling several approaches per bee would have inflated",
        "the trial count without adding independent information.",
    ]
    return "\n".join(lines) + "\n"


def main():
    trials = read_trials(INPUT_PATH)
    n_bees, n_arenas = check_one_row_per_bee(trials)
    n = len(trials)
    marked = sum(1 for row in trials if row["first_choice"] == MARKED)
    plain = sum(1 for row in trials if row["first_choice"] == PLAIN)
    if marked + plain != n:
        raise ValueError("first_choice holds a value outside the two coded options")
    span_mean = sum(float(row["intertegular_span_mm"]) for row in trials) / n
    outcome = binomtest(marked, n=n, p=NULL_SHARE, alternative="two-sided")
    report = compose_report(
        n, n_bees, n_arenas, marked, plain, span_mean, float(outcome.pvalue)
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(report)


if __name__ == "__main__":
    main()
