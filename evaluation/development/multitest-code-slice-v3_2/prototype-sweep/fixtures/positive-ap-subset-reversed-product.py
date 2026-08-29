# fmt: off
"""Analysis of the C. elegans whole-organism toxicology screen.

Reads the fixed data file ``data.csv`` (one row per assay plate), summarises the
two exposure groups on each of the eight pre-declared outcomes, and compares the
exposed plates with the carrier-only control plates using one two-sample test per
outcome.

The script only reads ``data.csv``; it never generates, simulates or overwrites it.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "data.csv"

GROUP_COLUMN = "exposure"
EXPOSED_LABEL = "exposed"
CONTROL_LABEL = "control"

ALPHA = 0.05

# The pre-declared outcome family, in the order it was declared in the screen
# protocol: (column, plain-language name, unit, decimal places for reporting).
OUTCOMES = [
    ("mean_lifespan_d", "Mean lifespan", "days", 2),
    ("total_brood_size_eggs", "Total brood size", "eggs per worm", 1),
    ("pumping_rate_pumps_per_min", "Pharyngeal pumping rate", "pumps/min", 1),
    ("thrashing_rate_bends_per_min", "Thrashing rate", "body bends/min", 1),
    ("body_length_um", "Body length at day 4 of adulthood", "um", 1),
    ("age_at_first_egg_h", "Age at first egg laid", "hours after L4", 2),
    ("defecation_interval_s", "Defecation cycle interval", "s", 2),
    ("crawling_speed_um_per_s", "Mean crawling speed", "um/s", 1),
]

# Outcomes 1, 2 and 4 of the declared family are the protocol's primary endpoints.
PRIMARY_OUTCOMES = [
    "mean_lifespan_d",
    "total_brood_size_eggs",
    "thrashing_rate_bends_per_min",
]

# Number of comparisons in the declared outcome family.
FAMILY_SIZE = len(OUTCOMES)


def load_data(path=DATA_FILE):
    """Read the fixed plate-level data file."""
    frame = pd.read_csv(path)
    return frame


def summarise_groups(frame):
    """Print group sizes and the per-group summary values for each outcome."""
    exposed = frame[frame[GROUP_COLUMN] == EXPOSED_LABEL]
    control = frame[frame[GROUP_COLUMN] == CONTROL_LABEL]

    print("=" * 78)
    print("GROUP SIZES")
    print("=" * 78)
    print(f"  {CONTROL_LABEL:<8} plates: {len(control)}")
    print(f"  {EXPOSED_LABEL:<8} plates: {len(exposed)}")
    print(f"  {'total':<8} plates: {len(frame)}")
    print()

    print("=" * 78)
    print("PER-GROUP SUMMARY VALUES (mean, standard deviation, n)")
    print("=" * 78)
    for column, name, unit, places in OUTCOMES:
        c_values = control[column]
        e_values = exposed[column]
        print(f"{name} ({unit}) [{column}]")
        print(
            f"    control : mean {c_values.mean():.{places}f}   "
            f"sd {c_values.std(ddof=1):.{places}f}   "
            f"median {c_values.median():.{places}f}   n {c_values.count()}"
        )
        print(
            f"    exposed : mean {e_values.mean():.{places}f}   "
            f"sd {e_values.std(ddof=1):.{places}f}   "
            f"median {e_values.median():.{places}f}   n {e_values.count()}"
        )
        print(
            f"    difference (exposed - control): "
            f"{e_values.mean() - c_values.mean():+.{places}f} {unit}"
        )
        print()

    return control, exposed


def compare_outcomes(control, exposed):
    """Run one two-sample test per declared outcome and report the verdicts.

    Every outcome is compared with Welch's two-sample t-test, which does not
    assume the two groups share a variance.

    The three primary endpoints (declared outcomes 1, 2 and 4) are corrected by
    hand for multiplicity: each primary p-value is multiplied by the number of
    comparisons in the declared family and capped at one, and the capped value is
    judged at the conventional 0.05 threshold. The remaining five outcomes are
    reported and judged on their raw p-values at the same threshold.
    """
    print("=" * 78)
    print("TWO-SAMPLE COMPARISONS (Welch's t-test, exposed vs control)")
    print("=" * 78)
    print(f"Declared family size (number of comparisons): {FAMILY_SIZE}")
    print(f"Primary endpoints (corrected by hand): {', '.join(PRIMARY_OUTCOMES)}")
    print(f"Significance threshold: {ALPHA}")
    print()

    results = []
    for column, name, unit, places in OUTCOMES:
        c_values = control[column]
        e_values = exposed[column]
        t_stat, p_raw = stats.ttest_ind(e_values, c_values, equal_var=False)

        is_primary = column in PRIMARY_OUTCOMES
        if is_primary:
            # By-hand correction: multiply by the family size, then cap at one.
            p_corrected = min(FAMILY_SIZE * p_raw, 1.0)
            p_used = p_corrected
            basis = f"corrected (raw x {FAMILY_SIZE}, capped at 1)"
        else:
            p_corrected = None
            p_used = p_raw
            basis = "raw"

        significant = p_used < ALPHA
        verdict = "SIGNIFICANT" if significant else "not significant"

        results.append(
            {
                "column": column,
                "name": name,
                "unit": unit,
                "places": places,
                "primary": is_primary,
                "t": t_stat,
                "p_raw": p_raw,
                "p_corrected": p_corrected,
                "p_used": p_used,
                "significant": significant,
            }
        )

        label = "PRIMARY" if is_primary else "secondary"
        print(f"{name} ({unit}) [{column}]  -- {label}")
        print(
            f"    control mean {c_values.mean():.{places}f}   "
            f"exposed mean {e_values.mean():.{places}f}   "
            f"difference {e_values.mean() - c_values.mean():+.{places}f} {unit}"
        )
        print(f"    Welch t = {t_stat:.3f}   raw p = {p_raw:.4g}")
        if is_primary:
            print(
                f"    corrected p = min({p_raw:.4g} x {FAMILY_SIZE}, 1) "
                f"= {p_corrected:.4g}"
            )
        print(f"    judged on the {basis} p-value at {ALPHA}: {verdict}")
        print()

    return results


def print_verdict_table(results):
    """Print a compact table of the per-outcome verdicts."""
    print("=" * 78)
    print("SUMMARY OF VERDICTS")
    print("=" * 78)
    header = (
        f"{'#':<3}{'outcome':<32}{'role':<11}"
        f"{'raw p':>11}{'p judged':>11}  verdict"
    )
    print(header)
    print("-" * 78)
    for index, result in enumerate(results, start=1):
        role = "primary" if result["primary"] else "secondary"
        verdict = "significant" if result["significant"] else "not significant"
        print(
            f"{index:<3}{result['column']:<32}{role:<11}"
            f"{result['p_raw']:>11.4g}{result['p_used']:>11.4g}  {verdict}"
        )
    print()

    significant_names = [r["column"] for r in results if r["significant"]]
    if significant_names:
        print("Outcomes separating the groups at the 0.05 threshold:")
        for name in significant_names:
            print(f"  - {name}")
    else:
        print("No outcome separated the groups at the 0.05 threshold.")
    print()


def main():
    frame = load_data()
    control, exposed = summarise_groups(frame)
    results = compare_outcomes(control, exposed)
    print_verdict_table(results)


if __name__ == "__main__":
    main()
