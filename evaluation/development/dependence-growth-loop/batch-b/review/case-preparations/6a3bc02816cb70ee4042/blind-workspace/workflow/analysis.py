"""Nitrate response of shallow monitoring wells to riparian wetland reconnection.

The survey rounds stored in data/input.csv are repeated measurements on the same
wells.  The well, not the water sample, is the independent unit of the study, so
this script collapses each well's rounds to a single baseline-to-post change
score and tests those well-level scores.  No well contributes more than one
number to the reported comparison.
"""

import csv
import statistics
from collections import defaultdict
from pathlib import Path

from scipy.stats import binomtest

INPUT_PATH = Path("data") / "input.csv"
OUTPUT_PATH = Path("results") / "report.md"

BASELINE_LABEL = "baseline"
POST_LABEL = "post_restoration"


def read_long_table(path):
    """Group the long-format file as {well: {period: [nitrate, ...]}}."""
    readings = defaultdict(lambda: defaultdict(list))
    screen_depth = {}
    with path.open(newline="", encoding="ascii") as handle:
        for record in csv.DictReader(handle):
            well = record["well_id"]
            readings[well][record["period"]].append(float(record["nitrate_mg_per_l"]))
            screen_depth[well] = float(record["screen_depth_m"])
    return readings, screen_depth


def collapse_to_wells(readings):
    """One paired change score per well: post-period mean minus baseline mean."""
    contrasts = []
    for well in sorted(readings):
        baseline = readings[well][BASELINE_LABEL]
        post = readings[well][POST_LABEL]
        baseline_mean = statistics.fmean(baseline)
        post_mean = statistics.fmean(post)
        contrasts.append(
            {
                "well": well,
                "n_baseline": len(baseline),
                "n_post": len(post),
                "baseline_mean": baseline_mean,
                "post_mean": post_mean,
                "change": post_mean - baseline_mean,
            }
        )
    return contrasts


def direction_label(change):
    if change < 0.0:
        return "decrease"
    if change > 0.0:
        return "increase"
    return "no change"


def compose_report(contrasts, screen_depth):
    changes = [item["change"] for item in contrasts]
    n_wells = len(contrasts)

    signed = [value for value in changes if value != 0.0]
    n_tested = len(signed)
    n_down = sum(1 for value in signed if value < 0.0)
    n_up = n_tested - n_down
    n_flat = n_wells - n_tested

    outcome = binomtest(n_down, n_tested, 0.5, alternative="two-sided")
    median_change = statistics.median(changes)
    mean_change = statistics.fmean(changes)
    steepest = min(changes)
    share_down = 100.0 * n_down / n_tested

    rounds_baseline = contrasts[0]["n_baseline"]
    rounds_post = contrasts[0]["n_post"]
    occasions = rounds_baseline + rounds_post
    total_rows = sum(item["n_baseline"] + item["n_post"] for item in contrasts)
    depth_lo = min(screen_depth.values())
    depth_hi = max(screen_depth.values())
    base_lo = min(item["baseline_mean"] for item in contrasts)
    base_hi = max(item["baseline_mean"] for item in contrasts)

    lines = [
        "# Nitrate response of shallow monitoring wells to riparian wetland reconnection",
        "",
        "## Design and data",
        "",
        f"{n_wells} shallow groundwater monitoring wells on the Kettle Creek terrace were sampled on "
        f"{occasions} survey rounds each: {rounds_baseline} rounds before the riparian wetland was "
        f"reconnected to its floodplain and {rounds_post} rounds during the first post-restoration year. "
        f"`data/input.csv` stores the record in long format, one row per well and round ({total_rows} rows "
        f"under a single header). Screen depth ({depth_lo:.1f}-{depth_hi:.1f} m) is a property of the well "
        f"and is repeated on every row belonging to it.",
        "",
        "Rounds taken from the same well are not independent observations of the aquifer: they share a "
        "screen interval, the same lithology and the same local recharge history. The well is the "
        "independent unit, so the sample-level values of each well are collapsed into a single paired "
        f"contrast before anything is tested, and exactly {n_wells} numbers, one per well, enter the "
        "inference.",
        "",
        "## Analysis",
        "",
        "For each well the mean baseline nitrate concentration was subtracted from the mean "
        "post-restoration concentration, giving one change score per well. The signs of these "
        f"{n_tested} well-level change scores were then tested against the null hypothesis of an even "
        "split (probability 0.5 of a decrease) with an exact two-sided binomial sign test. No individual "
        "water sample enters the test on its own, and no well contributes more than one number.",
        "",
        "## Well-level contrasts",
        "",
        "| well | rounds (baseline / post) | baseline mean | post mean | change | direction |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    for item in contrasts:
        lines.append(
            f"| {item['well']} | {item['n_baseline']} / {item['n_post']} | "
            f"{item['baseline_mean']:.2f} | {item['post_mean']:.2f} | "
            f"{item['change']:+.2f} | {direction_label(item['change'])} |"
        )

    lines.extend(
        [
            "",
            "All concentrations are milligrams of nitrate-N per litre.",
            "",
            "## Result",
            "",
            f"{n_down} of the {n_wells} wells ({share_down:.1f}%) had a lower mean nitrate concentration "
            f"after reconnection, {n_up} had a higher mean, and {n_flat} were unchanged. Across wells the "
            f"median change was {median_change:+.2f} mg/L and the mean change was {mean_change:+.2f} mg/L; "
            f"the largest single-well decline was {steepest:+.2f} mg/L.",
            "",
            f"[selected-result] Exact two-sided binomial sign test on {n_tested} independent well-level "
            f"change scores: {n_down}/{n_tested} wells declined (estimated proportion "
            f"{outcome.proportion_estimate:.3f}), p = {outcome.pvalue:.6f}; median well-level change "
            f"{median_change:+.2f} mg/L.",
            "",
            "## Notes",
            "",
            f"The test treats wells, not individual water samples, as replicates. Pooling all {total_rows} "
            f"sample-level records into a sample-by-sample comparison would count every well {occasions} "
            f"times and would overstate the evidence; the reported p-value rests on the {n_tested} "
            "well-level scores alone. Because the sign test uses only the direction of each well's change, "
            "it is insensitive to the size of individual shifts and to the spread of baseline "
            f"concentrations across wells ({base_lo:.2f}-{base_hi:.2f} mg/L).",
        ]
    )

    return "\n".join(lines) + "\n"


def main():
    readings, screen_depth = read_long_table(INPUT_PATH)
    contrasts = collapse_to_wells(readings)
    report = compose_report(contrasts, screen_depth)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(report)


if __name__ == "__main__":
    main()
