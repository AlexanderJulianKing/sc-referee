"""Steady-state methane yield of pilot anaerobic digesters under two feedstock
pretreatments.

Reads the weekly monitoring log in data/input.csv and writes results/report.md.

Pretreatment was assigned to whole reactors, so the five weekly records of a
reactor are repeated measurements of one physical unit. Every reactor is
collapsed to a single steady-state mean before the between-group comparison, so
exactly one analysed value enters the test per independent reactor.
"""

from __future__ import annotations

import csv
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median
from typing import Dict, List

from scipy.stats import mannwhitneyu

INPUT_PATH = Path("data") / "input.csv"
OUTPUT_PATH = Path("results") / "report.md"

UNIT_COLUMN = "reactor_id"
GROUP_COLUMN = "pretreatment"
WEEK_COLUMN = "run_week"
YIELD_COLUMN = "ch4_yield_nl_per_g_vs"

REFERENCE = "control"
TREATMENT = "alkaline"


@dataclass
class ReactorSummary:
    """One independent reactor reduced to a single steady-state value."""

    reactor_id: str
    pretreatment: str
    n_weeks: int
    mean_yield: float


def read_weekly_records(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="ascii") as handle:
        return [dict(record) for record in csv.DictReader(handle)]


def summarise_reactors(rows: List[Dict[str, str]]) -> List[ReactorSummary]:
    weekly = OrderedDict()
    for row in rows:
        reactor = row[UNIT_COLUMN]
        bucket = weekly.setdefault(
            reactor, {"pretreatment": row[GROUP_COLUMN], "weeks": [], "yields": []}
        )
        if bucket["pretreatment"] != row[GROUP_COLUMN]:
            raise ValueError("reactor " + reactor + " carries more than one pretreatment label")
        bucket["weeks"].append(int(row[WEEK_COLUMN]))
        bucket["yields"].append(float(row[YIELD_COLUMN]))

    summaries = []
    for reactor, bucket in weekly.items():
        if len(set(bucket["weeks"])) != len(bucket["weeks"]):
            raise ValueError("reactor " + reactor + " has duplicated run weeks")
        summaries.append(
            ReactorSummary(
                reactor_id=reactor,
                pretreatment=bucket["pretreatment"],
                n_weeks=len(bucket["yields"]),
                mean_yield=mean(bucket["yields"]),
            )
        )
    return summaries


def build_report(rows, summaries, reference, treatment, u_stat, p_value, rank_biserial):
    all_weeks = [int(row[WEEK_COLUMN]) for row in rows]

    lines = []
    lines.append(
        "# Alkaline pretreatment and steady-state methane yield in pilot anaerobic digesters"
    )
    lines.append("")
    lines.append("## Data")
    lines.append("")
    lines.append(
        "`data/input.csv` holds {rows} weekly monitoring records from {units} independently"
        " fed pilot digesters, covering run weeks {first}-{last}. Each digester kept the same"
        " feedstock pretreatment for the entire campaign, so the weekly records belonging to"
        " one digester are repeated measurements of that reactor and are not independent of"
        " one another.".format(
            rows=len(rows),
            units=len(summaries),
            first=min(all_weeks),
            last=max(all_weeks),
        )
    )
    lines.append("")
    lines.append("## Analysis")
    lines.append("")
    lines.append(
        "Each reactor was first collapsed to a single steady-state summary value: the"
        " arithmetic mean of its weekly specific methane yields. The resulting {units}"
        " reactor-level means -- one analysed value per independent unit -- were then"
        " compared between the two pretreatments with a two-sided exact Mann-Whitney U"
        " test. The rank-biserial correlation is reported as the effect size.".format(
            units=len(summaries)
        )
    )
    lines.append("")
    lines.append("## Reactor-level summaries")
    lines.append("")
    lines.append("| reactor | pretreatment | weeks used | mean CH4 yield (NL/g VS) |")
    lines.append("| --- | --- | --- | --- |")
    for item in summaries:
        lines.append(
            "| {0} | {1} | {2} | {3:.2f} |".format(
                item.reactor_id, item.pretreatment, item.n_weeks, item.mean_yield
            )
        )
    lines.append("")
    lines.append("## Group summaries")
    lines.append("")
    lines.append("| pretreatment | reactors | mean | median | min | max |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for label, values in ((REFERENCE, reference), (TREATMENT, treatment)):
        lines.append(
            "| {0} | {1} | {2:.2f} | {3:.2f} | {4:.2f} | {5:.2f} |".format(
                label,
                len(values),
                mean(values),
                median(values),
                min(values),
                max(values),
            )
        )
    lines.append("")
    lines.append("All yields are given in NL CH4 per g volatile solids fed.")
    lines.append("")
    lines.append("## Result")
    lines.append("")
    lines.append(
        "[selected-result] Two-sided exact Mann-Whitney U test on {units} reactor-level mean"
        " methane yields ({n_ref} control vs {n_trt} alkaline reactors, one value per"
        " reactor): U = {u:.1f}, p = {p:.4f}, rank-biserial correlation = {r:.3f};"
        " alkaline-pretreated reactors reached a higher steady-state yield (median {m_trt:.2f}"
        " vs {m_ref:.2f} NL CH4 per g VS, difference in group means {delta:.2f} NL/g VS).".format(
            units=len(summaries),
            n_ref=len(reference),
            n_trt=len(treatment),
            u=u_stat,
            p=p_value,
            r=rank_biserial,
            m_trt=median(treatment),
            m_ref=median(reference),
            delta=mean(treatment) - mean(reference),
        )
    )
    lines.append("")
    lines.append(
        "The comparison is made at the reactor level because pretreatment was applied to"
        " reactors, not to weekly samples; the {rows} weekly records support the reactor"
        " means but do not enlarge the sample size for this claim.".format(rows=len(rows))
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    rows = read_weekly_records(INPUT_PATH)
    summaries = summarise_reactors(rows)

    reference = [item.mean_yield for item in summaries if item.pretreatment == REFERENCE]
    treatment = [item.mean_yield for item in summaries if item.pretreatment == TREATMENT]
    if not reference or not treatment:
        raise ValueError("both pretreatment groups must be present")

    outcome = mannwhitneyu(treatment, reference, alternative="two-sided", method="exact")
    u_stat = float(outcome.statistic)
    p_value = float(outcome.pvalue)
    rank_biserial = 2.0 * u_stat / (len(treatment) * len(reference)) - 1.0

    report = build_report(rows, summaries, reference, treatment, u_stat, p_value, rank_biserial)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
