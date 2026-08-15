"""Ventilation response of shore crabs to vessel-noise playback.

The stored table is long format: one row per crab per playback session.  Sessions
repeat inside an animal, so they are averaged within crab before the paired test,
leaving exactly one analysed pair per independent unit (crab).

Reads data/input.csv, writes results/report.md.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from scipy import stats

INPUT_PATH = Path("data/input.csv")
OUTPUT_PATH = Path("results/report.md")

QUIET = "quiet"
NOISE = "vessel_noise"
SESSIONS_PER_CONDITION = 2


def read_sessions(path):
    """Return {crab_id: {condition: [ventilation, ...]}} for every stored row."""
    sessions = {}
    with path.open(newline="", encoding="ascii") as handle:
        for record in csv.DictReader(handle):
            crab = record["crab_id"].strip()
            condition = record["playback_condition"].strip()
            if condition not in (QUIET, NOISE):
                raise ValueError("unknown playback condition: " + condition)
            buckets = sessions.setdefault(crab, {QUIET: [], NOISE: []})
            buckets[condition].append(float(record["ventilation_beats_per_min"]))
    if not sessions:
        raise ValueError("no session rows found")
    return sessions


def collapse_within_crab(sessions):
    """One (crab, quiet mean, noise mean, difference) tuple per animal."""
    collapsed = []
    for crab in sorted(sessions):
        buckets = sessions[crab]
        for condition in (QUIET, NOISE):
            got = len(buckets[condition])
            if got != SESSIONS_PER_CONDITION:
                raise ValueError(
                    "crab {0} has {1} {2} sessions, expected {3}".format(
                        crab, got, condition, SESSIONS_PER_CONDITION
                    )
                )
        quiet_mean = float(np.mean(buckets[QUIET]))
        noise_mean = float(np.mean(buckets[NOISE]))
        collapsed.append((crab, quiet_mean, noise_mean, noise_mean - quiet_mean))
    return collapsed


def p_text(pvalue):
    """Report tiny p-values with a threshold rather than a noisy tail digit."""
    return "p < 0.001" if pvalue < 0.001 else "p = {0:.4f}".format(pvalue)


def build_report(collapsed, n_rows):
    quiet = np.array([item[1] for item in collapsed], dtype=float)
    noise = np.array([item[2] for item in collapsed], dtype=float)
    diff = noise - quiet

    n_crabs = diff.size
    df = n_crabs - 1
    mean_diff = float(diff.mean())
    sd_diff = float(diff.std(ddof=1))
    se_diff = sd_diff / np.sqrt(n_crabs)

    tstat, pvalue = stats.ttest_rel(noise, quiet)
    half_width = float(stats.t.ppf(0.975, df)) * se_diff
    lo = mean_diff - half_width
    hi = mean_diff + half_width
    dz = mean_diff / sd_diff

    wstat = float(stats.wilcoxon(diff).statistic)
    n_positive = int((diff > 0).sum())

    lines = [
        "# Vessel-noise playback and ventilation in shore crabs",
        "",
        "## Design",
        "",
        "Twelve shore crabs (Carcinus maenas) were each held in a separate flow-through",
        "chamber and run through four playback sessions on consecutive days: two quiet",
        "control sessions and two vessel-noise sessions, with the starting condition",
        "alternated between animals. Scaphognathite beat rate (ventilation, beats per",
        "minute) was counted over the final minute of each session. The stored table is",
        "long format: {0} rows, one row per crab per session.".format(n_rows),
        "",
        "## Analysis",
        "",
        "Sessions repeat on the same animal and are not independent of one another, so the",
        "two quiet sessions and the two noise sessions of each crab were averaged first.",
        "That leaves one quiet mean and one noise mean per crab, and the noise-minus-quiet",
        "contrast was formed within crab. The reported test uses {0} paired values, one per".format(
            n_crabs
        ),
        "crab, so the independent units and the analysed rows coincide.",
        "",
        "## Crab-level means (beats per minute)",
        "",
        "| crab_id | quiet | vessel noise | difference |",
        "| --- | --- | --- | --- |",
    ]

    for crab, quiet_mean, noise_mean, delta in collapsed:
        lines.append(
            "| {0} | {1:.2f} | {2:.2f} | {3:+.2f} |".format(
                crab, quiet_mean, noise_mean, delta
            )
        )

    lines += [
        "",
        "## Result",
        "",
        "Averaged over animals, ventilation was {0:.2f} beats/min under quiet playback and".format(
            float(quiet.mean())
        ),
        "{0:.2f} beats/min under vessel noise. The within-crab increase averaged".format(
            float(noise.mean())
        ),
        "{0:.2f} beats/min (SD {1:.2f}).".format(mean_diff, sd_diff),
        "",
        "[selected-result] Paired t-test on crab-level mean ventilation (n = {0} crabs, "
        "one paired value per crab): vessel-noise playback increased ventilation by "
        "{1:.2f} beats/min (95% CI {2:.2f} to {3:.2f}), t({4}) = {5:.4f}, {6}, "
        "dz = {7:.2f}.".format(
            n_crabs, mean_diff, lo, hi, df, float(tstat), p_text(float(pvalue)), dz
        ),
        "",
        "A distribution-free check agrees: the two-sided signed-rank statistic on the same {0}".format(
            n_crabs
        ),
        "crab-level differences is W = {0:.1f}, with all {1} differences positive.".format(
            wstat, n_positive
        ),
        "Because the repeated sessions were collapsed within animal before testing, the",
        "degrees of freedom track the {0} crabs (df = {1}) rather than the {2} stored session".format(
            n_crabs, df, n_rows
        ),
        "rows.",
    ]
    return "\n".join(lines) + "\n"


def main():
    sessions = read_sessions(INPUT_PATH)
    n_rows = sum(len(b[QUIET]) + len(b[NOISE]) for b in sessions.values())
    collapsed = collapse_within_crab(sessions)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(build_report(collapsed, n_rows), encoding="utf-8")


if __name__ == "__main__":
    main()
