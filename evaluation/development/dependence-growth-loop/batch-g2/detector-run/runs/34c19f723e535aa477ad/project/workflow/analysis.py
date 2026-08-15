#!/usr/bin/env python3
"""Colony-level test of dietary thiamethoxam on bumblebee gyne production.

Reads data/input.csv and writes results/report.md. One colony contributes one row,
so the two-sample tests below are applied to independent units.
"""

from __future__ import annotations

import csv
import statistics
from collections import Counter
from pathlib import Path

from scipy import stats

CSV_REL = "data/input.csv"
OUT_REL = "results/report.md"
ARMS = ("control", "exposed")


def base_dir() -> Path:
    guess = Path(__file__).resolve().parent.parent
    if (guess / CSV_REL).is_file():
        return guess
    return Path.cwd()


def load_rows(path: Path) -> list:
    with path.open(newline="", encoding="ascii") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def welch_df(a: list, b: list) -> float:
    va = statistics.variance(a) / len(a)
    vb = statistics.variance(b) / len(b)
    return (va + vb) ** 2 / (va * va / (len(a) - 1) + vb * vb / (len(b) - 1))


def show_p(p: float) -> str:
    return "< 0.001" if p < 0.001 else "= " + format(p, ".3f")


def main() -> None:
    root = base_dir()
    rows = load_rows(root / CSV_REL)

    gynes = {
        arm: [int(r["gyne_count"]) for r in rows if r["treatment"] == arm]
        for arm in ARMS
    }
    workers = {
        arm: [int(r["founding_workers"]) for r in rows if r["treatment"] == arm]
        for arm in ARMS
    }

    per_colony = Counter(r["colony_id"] for r in rows)
    n_arenas = len({r["arena_id"] for r in rows})

    tt = stats.ttest_ind(gynes["control"], gynes["exposed"], equal_var=False)
    df = welch_df(gynes["control"], gynes["exposed"])
    mw = stats.mannwhitneyu(
        gynes["control"],
        gynes["exposed"],
        alternative="two-sided",
        method="asymptotic",
    )

    mean_c = statistics.mean(gynes["control"])
    mean_e = statistics.mean(gynes["exposed"])
    sd_c = statistics.stdev(gynes["control"])
    sd_e = statistics.stdev(gynes["exposed"])
    gap = mean_c - mean_e

    lines = [
        "# Neonicotinoid microdosing and gyne production in caged bumblebee colonies",
        "",
        "## Design",
        "",
        "Twenty-eight queenright Bombus terrestris colonies were reared, each in its own sealed",
        "flight arena, and each colony was held on a single diet for the whole colony cycle:",
        f"{len(gynes['control'])} colonies received untreated sugar syrup (control) and {len(gynes['exposed'])} received syrup dosed at",
        "2 ppb thiamethoxam (exposed). The response is the lifetime gyne count, a single",
        "whole-colony census taken at nest teardown. Each colony is censused once and appears",
        "once, so every analysed row is one independent unit.",
        "",
        f"Independence check: {len(rows)} data rows, {len(per_colony)} distinct colony identifiers, {n_arenas} distinct arena",
        f"identifiers, at most {max(per_colony.values())} row per colony.",
        "",
        "## Baseline balance",
        "",
        "| treatment | colonies | mean founding workers |",
        "| --- | --- | --- |",
    ]

    for arm in ARMS:
        lines.append(
            "| {0} | {1} | {2:.2f} |".format(
                arm, len(workers[arm]), statistics.mean(workers[arm])
            )
        )

    lines += [
        "",
        "## Gyne production",
        "",
        "| treatment | colonies | mean gynes | SD |",
        "| --- | --- | --- | --- |",
        "| control | {0} | {1:.2f} | {2:.2f} |".format(len(gynes["control"]), mean_c, sd_c),
        "| exposed | {0} | {1:.2f} | {2:.2f} |".format(len(gynes["exposed"]), mean_e, sd_e),
        "",
        f"Welch's two-sample t-test (two-sided) on lifetime gyne count: t = {tt.statistic:.2f}, df = {df:.1f},",
        f"p {show_p(float(tt.pvalue))}. The control minus exposed difference in means is {gap:.2f} gynes.",
        "",
        "Mann-Whitney U test (two-sided, normal approximation) as a distribution-free check:",
        f"U = {mw.statistic:.1f}, p {show_p(float(mw.pvalue))}.",
        "",
        (
            "[selected-result] Welch's two-sided two-sample t-test on lifetime gyne count with "
            f"one colony per row: control colonies produced {mean_c:.2f} gynes on average against "
            f"{mean_e:.2f} for thiamethoxam-exposed colonies, a difference of {gap:.2f} gynes "
            f"(t = {tt.statistic:.2f}, df = {df:.1f}, p {show_p(float(tt.pvalue))}), so 2 ppb dietary "
            "thiamethoxam is associated with markedly reduced gyne output."
        ),
        "",
        "## Notes",
        "",
        "The gyne count is a whole-colony lifetime total, so there are no repeated measures to",
        "pool and no within-colony correlation for the test to absorb. The degrees of freedom",
        "in the Welch approximation count colonies, not observations. The two arms are close on",
        f"founding worker number ({statistics.mean(workers['control']):.2f} against {statistics.mean(workers['exposed']):.2f}), so the contrast is not driven by",
        "an obvious size imbalance.",
    ]

    out = root / OUT_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
