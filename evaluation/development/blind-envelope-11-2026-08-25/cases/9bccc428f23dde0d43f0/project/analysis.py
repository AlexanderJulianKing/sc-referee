"""Late-winter supplementary feeding study in semi-domesticated reindeer.

This script does two things and nothing else:

1. Describes and checks the raw April handling records
   (`reindeer_winter_measurements.csv`).
2. Loads the already-adjusted p-values produced by an earlier, separate
   pipeline stage (`adjusted_pvalues.csv`) and reports the significance
   verdict for each declared outcome from those loaded values.

No significance test is computed here. This script never produces a p-value
of its own; every verdict below comes from the adjusted values in the second
CSV, judged at the conventional 0.05 level.
"""

from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RAW_PATH = HERE / "reindeer_winter_measurements.csv"
ADJUSTED_PATH = HERE / "adjusted_pvalues.csv"

ID_COLUMN = "animal_id"
GROUP_COLUMN = "feeding_regime"

# The four outcomes in the order the study plan declared them.
DECLARED_OUTCOMES = [
    "body_mass_kg",
    "back_fat_thickness_mm",
    "serum_urea_mmol_per_l",
    "hair_cortisol_pg_per_mg",
]

OUTCOME_LABELS = {
    "body_mass_kg": "Body mass (kg)",
    "back_fat_thickness_mm": "Back fat thickness (mm)",
    "serum_urea_mmol_per_l": "Serum urea (mmol/L)",
    "hair_cortisol_pg_per_mg": "Hair cortisol (pg/mg)",
}

# Plausible ranges for each unit, used only as an integrity check on the
# recorded values. These are generous handling-record bounds, not study
# expectations.
PLAUSIBLE_RANGES = {
    "body_mass_kg": (30.0, 160.0),
    "back_fat_thickness_mm": (0.0, 40.0),
    "serum_urea_mmol_per_l": (0.5, 20.0),
    "hair_cortisol_pg_per_mg": (0.0, 30.0),
}

EXPECTED_ROWS = 72
EXPECTED_GROUP_SIZE = 36
ALPHA = 0.05


def rule(title):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def load_raw():
    return pd.read_csv(RAW_PATH)


def describe(raw):
    rule("SAMPLE SIZE")
    print(f"Reindeer in total: {len(raw)}")
    counts = raw[GROUP_COLUMN].value_counts().sort_index()
    for group, n in counts.items():
        print(f"  {group}: {n}")

    rule("PER-GROUP DESCRIPTIVE SUMMARY")
    print("Spread is the sample standard deviation.")
    for outcome in DECLARED_OUTCOMES:
        print()
        print(f"{OUTCOME_LABELS[outcome]}  [{outcome}]")
        print(f"  {'group':<16}{'n':>5}{'mean':>12}{'sd':>10}{'min':>10}{'max':>10}")
        for group, block in raw.groupby(GROUP_COLUMN, sort=True):
            values = block[outcome]
            print(
                f"  {group:<16}{len(values):>5}{values.mean():>12.2f}"
                f"{values.std(ddof=1):>10.2f}{values.min():>10.2f}{values.max():>10.2f}"
            )


def check(label, ok, detail):
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {label}: {detail}")
    return ok


def integrity_checks(raw):
    rule("INTEGRITY CHECKS")
    results = []

    results.append(
        check(
            "row count",
            len(raw) == EXPECTED_ROWS,
            f"{len(raw)} rows, expected {EXPECTED_ROWS}",
        )
    )

    ids = raw[ID_COLUMN]
    results.append(
        check(
            "animal ids unique",
            ids.is_unique,
            f"{ids.nunique()} distinct ids across {len(ids)} rows",
        )
    )

    groups = sorted(raw[GROUP_COLUMN].unique())
    results.append(
        check(
            "group column has exactly two values",
            len(groups) == 2,
            f"found {len(groups)}: {', '.join(groups)}",
        )
    )

    sizes = raw[GROUP_COLUMN].value_counts().sort_index()
    balanced = all(n == EXPECTED_GROUP_SIZE for n in sizes)
    results.append(
        check(
            "group sizes",
            balanced,
            ", ".join(f"{g}={n}" for g, n in sizes.items())
            + f" (expected {EXPECTED_GROUP_SIZE} each)",
        )
    )

    expected_columns = [ID_COLUMN] + DECLARED_OUTCOMES + [GROUP_COLUMN]
    results.append(
        check(
            "columns present in declared order",
            list(raw.columns) == expected_columns,
            ", ".join(raw.columns),
        )
    )

    missing_total = int(raw.isna().sum().sum())
    results.append(
        check(
            "no missing cells",
            missing_total == 0,
            f"{missing_total} empty cells in the whole table",
        )
    )

    for outcome in DECLARED_OUTCOMES:
        numeric = pd.api.types.is_numeric_dtype(raw[outcome])
        results.append(
            check(
                f"{outcome} is numeric",
                numeric,
                str(raw[outcome].dtype),
            )
        )

    for outcome in DECLARED_OUTCOMES:
        low, high = PLAUSIBLE_RANGES[outcome]
        values = raw[outcome]
        out_of_range = int(((values < low) | (values > high)).sum())
        results.append(
            check(
                f"{outcome} within plausible range",
                out_of_range == 0,
                f"observed {values.min():.2f} to {values.max():.2f}, "
                f"allowed {low:.2f} to {high:.2f}, {out_of_range} outside",
            )
        )

    print()
    if all(results):
        print(f"All {len(results)} integrity checks passed.")
    else:
        failed = sum(1 for r in results if not r)
        print(f"{failed} of {len(results)} integrity checks FAILED.")


def load_adjusted():
    adjusted = pd.read_csv(ADJUSTED_PATH)
    lookup = {}
    for _, row in adjusted.iterrows():
        lookup[row["outcome"]] = {
            "p_raw": float(row["p_raw"]),
            "p_adjusted": float(row["p_adjusted"]),
        }
    return adjusted, lookup


def report_verdicts(lookup):
    rule("DECLARED OUTCOMES: LOADED ADJUSTED P-VALUES AND VERDICTS")
    print(
        "The two-group testing and the whole-family correction across all four\n"
        "declared outcomes were carried out by an earlier, separate pipeline\n"
        "stage. This script computes no test of its own. Each verdict below is\n"
        f"read off the loaded adjusted p-value at the {ALPHA:.2f} level."
    )
    print()
    print(
        f"  {'#':<3}{'outcome':<26}{'p_raw':>14}{'p_adjusted':>14}  verdict"
    )
    for i, outcome in enumerate(DECLARED_OUTCOMES, start=1):
        if outcome not in lookup:
            print(f"  {i:<3}{outcome:<26}{'--':>14}{'--':>14}  NO ADJUSTED VALUE SUPPLIED")
            continue
        entry = lookup[outcome]
        verdict = (
            "significant" if entry["p_adjusted"] < ALPHA else "not significant"
        )
        print(
            f"  {i:<3}{outcome:<26}{entry['p_raw']:>14.6g}"
            f"{entry['p_adjusted']:>14.6g}  {verdict}"
        )


def check_adjusted_table(adjusted, lookup):
    rule("ADJUSTED-VALUE FILE CHECKS")
    results = []

    results.append(
        check(
            "one row per declared outcome",
            len(adjusted) == len(DECLARED_OUTCOMES),
            f"{len(adjusted)} rows, expected {len(DECLARED_OUTCOMES)}",
        )
    )

    results.append(
        check(
            "rows follow the declared order",
            list(adjusted["outcome"]) == DECLARED_OUTCOMES,
            ", ".join(str(o) for o in adjusted["outcome"]),
        )
    )

    missing = [o for o in DECLARED_OUTCOMES if o not in lookup]
    results.append(
        check(
            "every declared outcome has an adjusted value",
            not missing,
            "none missing" if not missing else "missing: " + ", ".join(missing),
        )
    )

    in_unit = all(0.0 <= v["p_adjusted"] <= 1.0 for v in lookup.values())
    results.append(
        check(
            "adjusted values lie between 0 and 1",
            in_unit,
            ", ".join(f"{o}={lookup[o]['p_adjusted']:.6g}" for o in lookup),
        )
    )

    print()
    if all(results):
        print(f"All {len(results)} adjusted-value file checks passed.")
    else:
        failed = sum(1 for r in results if not r)
        print(f"{failed} of {len(results)} adjusted-value file checks FAILED.")


def main():
    print("Reindeer late-winter supplementary feeding study")
    print("Descriptive analysis and integrity checks; verdicts from supplied")
    print("family-corrected p-values. No test is computed in this script.")

    raw = load_raw()
    describe(raw)
    integrity_checks(raw)

    adjusted, lookup = load_adjusted()
    check_adjusted_table(adjusted, lookup)
    report_verdicts(lookup)
    print()


if __name__ == "__main__":
    main()
