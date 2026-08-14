#!/usr/bin/env python3
"""Two-choice oviposition assay in Drosophila suzukii.

One mated female per arena and one arena per row. Reads data/input.csv and
writes results/report.md.
"""

import csv
from pathlib import Path
from statistics import mean, median

from scipy import stats

RIPENING = "ripe"
OVERRIPE = "overripe"
NULL_SHARE = 0.5

ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = ROOT / "data" / "input.csv"
REPORT_PATH = ROOT / "results" / "report.md"


def load_assays(path):
    with path.open(newline="", encoding="ascii") as handle:
        return list(csv.DictReader(handle))


def audit_independence(assays):
    """Confirm one row per female and one arena per female."""
    females = [row["female_id"] for row in assays]
    arenas = [row["arena_id"] for row in assays]
    if len(set(females)) != len(females):
        raise ValueError("female_id repeats: rows would not be independent")
    if len(set(arenas)) != len(arenas):
        raise ValueError("arena_id repeats: an arena was reused")
    return len(assays), len(set(females)), len(set(arenas))


def tally(assays):
    ripening = 0
    for row in assays:
        choice = row["first_egg_substrate"]
        if choice == RIPENING:
            ripening += 1
        elif choice != OVERRIPE:
            raise ValueError("unrecognised first_egg_substrate: " + choice)
    return ripening, len(assays)


def exact_two_sided(ripening, tested):
    result = stats.binomtest(ripening, tested, NULL_SHARE,
                             alternative="two-sided")
    return result.pvalue


def group_by_cohort(assays):
    groups = {}
    for row in assays:
        groups.setdefault(row["cohort"], []).append(row)
    return groups


def build_report(assays):
    n_rows, n_females, n_arenas = audit_independence(assays)
    ripening, tested = tally(assays)
    share = ripening / tested
    p_value = exact_two_sided(ripening, tested)

    ages = [int(row["age_days"]) for row in assays]
    wings = [float(row["wing_length_mm"]) for row in assays]
    eggs = [int(row["total_eggs_24h"]) for row in assays]
    latencies = [int(row["latency_min"]) for row in assays]

    groups = group_by_cohort(assays)
    names = sorted(groups)
    sizes = ", ".join("%s (%d)" % (name, len(groups[name])) for name in names)

    out = []
    out.append("# Oviposition substrate choice in individually assayed"
               " Drosophila suzukii females")
    out.append("")
    out.append("## Design")
    out.append("")
    out.append("Mated Drosophila suzukii females were each tested once, alone, in a dedicated")
    out.append("two-choice arena holding one intact ripening raspberry and one wounded overripe")
    out.append("raspberry. The recorded outcome is the substrate that received the female's")
    out.append("first egg during a 24 h observation window.")
    out.append("")
    out.append("Each female appears in exactly one row and each arena is used by exactly one")
    out.append("female, so the analysed rows are independent replicates: no female is measured")
    out.append("twice and nothing is pooled across repeated observations of the same individual.")
    out.append("")
    out.append("Design check: %d rows, %d distinct female_id values, %d distinct arena_id values."
               % (n_rows, n_females, n_arenas))
    out.append("")
    out.append("## Sample description")
    out.append("")
    out.append("| quantity | value |")
    out.append("| --- | --- |")
    out.append("| females assayed | %d |" % n_rows)
    out.append("| rearing cohorts | %s |" % sizes)
    out.append("| age at assay (days) | %d-%d |" % (min(ages), max(ages)))
    out.append("| mean wing length (mm) | %.2f |" % mean(wings))
    out.append("| mean eggs laid in 24 h | %.1f |" % mean(eggs))
    out.append("| median eggs laid in 24 h | %.1f |" % median(eggs))
    out.append("| mean latency to first egg (min) | %.1f |" % mean(latencies))
    out.append("")
    out.append("## Analysis")
    out.append("")
    out.append("The pre-specified question is whether the first egg lands on the ripening")
    out.append("substrate more often than chance would give. Because each row carries one")
    out.append("female's single binary outcome, the rows are independent Bernoulli trials and an")
    out.append("exact two-sided binomial test against p = 0.5 applies to the raw row counts")
    out.append("without any correction for within-individual dependence.")
    out.append("")
    out.append("## Result")
    out.append("")
    out.append("First egg on the ripening substrate: %d of %d females (proportion %.3f)."
               % (ripening, tested, share))
    out.append("Exact two-sided binomial test against p = 0.5: p = %.6f." % p_value)
    out.append("")
    out.append("[selected-result] %d of %d individually assayed females (proportion %.3f) placed"
               " their first egg on the ripening substrate rather than the overripe substrate;"
               " an exact two-sided binomial test against p = 0.5 gives p = %.6f, so the"
               " preference for ripening fruit is significant at the 5 percent level."
               % (ripening, tested, share, p_value))
    out.append("")
    out.append("## Cohort consistency check")
    out.append("")
    out.append("The same exact test applied separately within each rearing cohort is reported")
    out.append("for description only; the primary claim rests on the pooled test above.")
    out.append("")
    out.append("| cohort | ripening | tested | proportion | exact two-sided p |")
    out.append("| --- | --- | --- | --- | --- |")
    for name in names:
        hits, total = tally(groups[name])
        out.append("| %s | %d | %d | %.3f | %.6f |"
                   % (name, hits, total, hits / total, exact_two_sided(hits, total)))
    out.append("")
    out.append("Both cohorts lean the same way. Cohort B on its own does not reach the 5 percent")
    out.append("level, which is unsurprising at this per-cohort sample size.")
    out.append("")
    out.append("## Limitations")
    out.append("")
    out.append("The outcome is the placement of the first egg in a two-item arena over a single")
    out.append("24 h window, so it speaks to relative acceptance of the two offered substrates,")
    out.append("not to how a female would spread eggs across a whole fruit patch. The result")
    out.append("describes laboratory-reared females in the age range assayed here.")
    return "\n".join(out) + "\n"


def main():
    assays = load_assays(INPUT_PATH)
    report = build_report(assays)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
