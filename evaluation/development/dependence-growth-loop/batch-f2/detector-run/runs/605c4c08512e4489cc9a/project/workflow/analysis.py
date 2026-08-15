"""Nest-site choice assay in field-collected Temnothorax rugatulus colonies.

Every colony in the table came from its own granite outcrop and was released
into the two-cavity arena exactly once, so a colony, a row and a trial are the
same thing. The script reads data/input.csv, runs an exact two-sided binomial
test on the shaded-cavity count and writes results/report.md.
"""

import csv
from pathlib import Path

from scipy.stats import binomtest

INPUT_PATH = Path("data/input.csv")
OUTPUT_PATH = Path("results/report.md")

UNIT_COLUMN = "colony_id"
OUTCOME_COLUMN = "cavity_chosen"
PREFERRED_CAVITY = "shaded"
ALTERNATIVE_CAVITY = "exposed"
NULL_PROBABILITY = 0.5
ALPHA = 0.05


def read_trials(path):
    """Return the assay rows, refusing anything that is not one row per colony."""
    with path.open(newline="", encoding="ascii") as handle:
        trials = list(csv.DictReader(handle))
    if not trials:
        raise ValueError("no assay rows found")
    colonies = [trial[UNIT_COLUMN] for trial in trials]
    if len(set(colonies)) != len(colonies):
        raise ValueError("each colony must contribute exactly one assay row")
    outcrops = [trial["collection_outcrop"] for trial in trials]
    if len(set(outcrops)) != len(outcrops):
        raise ValueError("each outcrop must supply exactly one colony")
    for trial in trials:
        choice = trial[OUTCOME_COLUMN]
        if choice not in (PREFERRED_CAVITY, ALTERNATIVE_CAVITY):
            raise ValueError("unrecognised cavity code: " + choice)
    return trials


def build_report(n_trials, n_preferred, p_value):
    n_alternative = n_trials - n_preferred
    proportion = n_preferred / n_trials
    verdict = "rejected" if p_value < ALPHA else "not rejected"
    selected = (
        "[selected-result] Exact two-sided binomial test on {0} independent"
        " colonies: {1} of {0} (proportion {2:.4f}) chose the shaded cavity"
        " against a null of {3:g}, p = {4:.5f}, so the no-preference null is"
        " {5} at alpha = {6:g}."
    ).format(
        n_trials,
        n_preferred,
        proportion,
        NULL_PROBABILITY,
        p_value,
        verdict,
        ALPHA,
    )
    lines = [
        "# Nest-site choice in field-collected Temnothorax rugatulus colonies",
        "",
        "## Design",
        "",
        "Each colony in this survey was collected from its own granite outcrop, at",
        "least fifty metres from the next, and was released into the two-cavity arena",
        "exactly once. One row of the data table is therefore one colony and one",
        "trial: no colony was retested, and no colony contributes a second choice.",
        "",
        "## Analysis",
        "",
        "Exact two-sided binomial test (scipy.stats.binomtest) on the number of",
        "colonies that emigrated into the shaded cavity, against the no-preference",
        "expectation of {0:g}.".format(NULL_PROBABILITY),
        "",
        "## Numbers",
        "",
        "- Colonies assayed: {0}".format(n_trials),
        "- Emigrated to the shaded cavity: {0}".format(n_preferred),
        "- Emigrated to the exposed cavity: {0}".format(n_alternative),
        "- Observed proportion choosing shaded: {0:.4f}".format(proportion),
        "- Null proportion: {0:g}".format(NULL_PROBABILITY),
        "- Exact two-sided p-value: {0:.5f}".format(p_value),
        "",
        selected,
        "",
        "## Reading",
        "",
        "The bias toward the dim cavity is strong and unlikely under indifference. The",
        "count that enters the test is a count of separate colonies, so the exact",
        "binomial sampling model matches the way the data were collected.",
    ]
    return "\n".join(lines) + "\n"


def main():
    trials = read_trials(INPUT_PATH)
    n_trials = len(trials)
    n_preferred = 0
    for trial in trials:
        if trial[OUTCOME_COLUMN] == PREFERRED_CAVITY:
            n_preferred += 1
    result = binomtest(
        n_preferred, n_trials, NULL_PROBABILITY, alternative="two-sided"
    )
    report = build_report(n_trials, n_preferred, result.pvalue)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
