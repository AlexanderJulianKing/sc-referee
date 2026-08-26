"""Analysis of the allergy nasal spray service evaluation.

Compares the intranasal corticosteroid arm against the intranasal antihistamine
arm on the five protocol outcomes, in the protocol's declared order.

Two of the five outcomes (total nasal symptom score and peak nasal inspiratory
flow) are the ones the clinic treats as prescribing-relevant, so their p-values
are corrected by hand: p_corrected = min(1, p_raw * number_of_comparisons).
The other three outcomes are judged on their raw p-values.

Run from the project root:
    python analysis.py
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "allergy_spray_trial.csv"

GROUP_COL = "group"
ARM_A = "corticosteroid"
ARM_B = "antihistamine"

ALPHA = 0.05

# The five protocol outcomes, in the declared order.
OUTCOMES = [
    ("tnss_total", "Total nasal symptom score", "points (0-12)"),
    ("pnif_l_min", "Peak nasal inspiratory flow", "L/min"),
    ("disturbed_nights", "Nights with disturbed sleep", "nights (0-7)"),
    ("tos_total", "Total ocular symptom score", "points (0-9)"),
    ("rqlq_total", "Rhinoconjunctivitis QoL total", "points (0-6)"),
]

# The outcomes the clinic declared as prescribing-relevant; only these get the
# hand-applied multiplicity correction.
PRESCRIBING_RELEVANT = {"tnss_total", "pnif_l_min"}


def load_data(path=DATA_FILE):
    """Read the trial CSV and check the basic shape the protocol promises."""
    df = pd.read_csv(path)

    expected = [
        "patient_id",
        GROUP_COL,
        *[name for name, _, _ in OUTCOMES],
    ]
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing expected columns: {missing}")

    if df["patient_id"].duplicated().any():
        raise ValueError("patient_id is not unique; one row must be one patient")

    arms = sorted(df[GROUP_COL].unique())
    if arms != sorted([ARM_A, ARM_B]):
        raise ValueError(f"Unexpected treatment arms in data: {arms}")

    if df[expected].isna().any().any():
        raise ValueError("CSV contains missing values; the protocol expects none")

    return df


def compare_outcome(df, column):
    """Welch two-sample t-test on one outcome, corticosteroid vs antihistamine."""
    a = df.loc[df[GROUP_COL] == ARM_A, column].astype(float)
    b = df.loc[df[GROUP_COL] == ARM_B, column].astype(float)

    result = stats.ttest_ind(a, b, equal_var=False)

    return {
        "n_a": int(a.size),
        "n_b": int(b.size),
        "mean_a": float(a.mean()),
        "mean_b": float(b.mean()),
        "sd_a": float(a.std(ddof=1)),
        "sd_b": float(b.std(ddof=1)),
        "difference": float(a.mean() - b.mean()),
        "t_stat": float(result.statistic),
        "df": float(result.df),
        "p_raw": float(result.pvalue),
    }


def main():
    df = load_data()

    n_comparisons = len(OUTCOMES)

    rows = []
    for column, label, unit in OUTCOMES:
        res = compare_outcome(df, column)

        if column in PRESCRIBING_RELEVANT:
            p_used = min(1.0, res["p_raw"] * n_comparisons)
            p_kind = f"corrected (x{n_comparisons}, capped at 1)"
        else:
            p_used = res["p_raw"]
            p_kind = "raw"

        rows.append(
            {
                "column": column,
                "label": label,
                "unit": unit,
                "p_used": p_used,
                "p_kind": p_kind,
                "significant": p_used < ALPHA,
                **res,
            }
        )

    print("Allergy nasal spray service evaluation")
    print("=" * 78)
    print(f"Data file: {DATA_FILE.name}")
    print(f"Patients: {len(df)}  ({ARM_A}: {rows[0]['n_a']}, {ARM_B}: {rows[0]['n_b']})")
    print("Test: Welch two-sample t-test, corticosteroid vs antihistamine")
    print(f"Comparisons performed: {n_comparisons}")
    print(
        "Hand-applied correction on the prescribing-relevant outcomes "
        f"({', '.join(sorted(PRESCRIBING_RELEVANT))}): "
        f"p x {n_comparisons}, capped at 1"
    )
    print(f"Threshold: {ALPHA}")
    print()

    header = (
        f"{'#':<3}{'Outcome':<32}{'Cortico':>10}{'Antihist':>11}"
        f"{'p raw':>10}{'p used':>10}  {'Verdict':<16}{'p basis'}"
    )
    print(header)
    print("-" * 110)

    for i, r in enumerate(rows, start=1):
        verdict = "significant" if r["significant"] else "not significant"
        print(
            f"{i:<3}{r['label']:<32}"
            f"{r['mean_a']:>10.2f}{r['mean_b']:>11.2f}"
            f"{r['p_raw']:>10.4f}{r['p_used']:>10.4f}  "
            f"{verdict:<16}{r['p_kind']}"
        )

    print()
    print("Detail")
    print("-" * 78)
    for i, r in enumerate(rows, start=1):
        print(f"{i}. {r['label']}  [{r['column']}, {r['unit']}]")
        print(
            f"   {ARM_A}: mean {r['mean_a']:.2f} (SD {r['sd_a']:.2f}, n={r['n_a']})"
        )
        print(
            f"   {ARM_B}: mean {r['mean_b']:.2f} (SD {r['sd_b']:.2f}, n={r['n_b']})"
        )
        print(
            f"   difference (cortico - antihist): {r['difference']:+.2f}"
            f"   t = {r['t_stat']:.3f}, df = {r['df']:.1f}"
        )
        print(
            f"   p raw = {r['p_raw']:.4f}; p used = {r['p_used']:.4f} ({r['p_kind']});"
            f" {'significant' if r['significant'] else 'not significant'} at {ALPHA}"
        )
        print()


if __name__ == "__main__":
    main()
