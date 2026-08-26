"""Two-stage split-sample analysis of baseline blood markers in early rheumatoid arthritis.

Stage one (screening) uses the discovery half only. Stage two (confirmation) uses the
validation half only, and tests just the markers that survived screening, at a
Bonferroni-adjusted level that holds the family-wise error rate of the confirmatory
tests at 5 percent.

Every claim about which markers separate responders from non-responders rests on the
validation stage. The discovery half produces screening output only.

Run from the project root:

    python analysis.py
"""

from __future__ import annotations

import pandas as pd
from scipy import stats

DATA_FILE = "ra_baseline_markers.csv"

# The six protocol-declared baseline markers, in the declared protocol order.
MARKERS: list[tuple[str, str]] = [
    ("crp_mg_l", "C-reactive protein (mg/L)"),
    ("esr_mm_h", "Erythrocyte sedimentation rate (mm/h)"),
    ("anti_ccp_u_ml", "Anti-CCP antibody (U/mL)"),
    ("rf_iu_ml", "Rheumatoid factor (IU/mL)"),
    ("calprotectin_ng_ml", "Serum calprotectin (ng/mL)"),
    ("vitd_nmol_l", "Serum 25-hydroxyvitamin D (nmol/L)"),
]

RESPONDER = "responder"
NON_RESPONDER = "non_responder"
DISCOVERY = "discovery"
VALIDATION = "validation"

# Stated in advance, before any test is run.
SCREENING_THRESHOLD = 0.10  # stage one: unadjusted p-value cut for carrying a marker forward
FAMILY_ALPHA = 0.05  # stage two: family-wise error rate across the confirmatory tests


def load_data(path: str = DATA_FILE) -> pd.DataFrame:
    """Read the marker table and check the structural assumptions the analysis relies on."""
    frame = pd.read_csv(path)

    expected = ["patient_id", "group", "stage"] + [name for name, _ in MARKERS]
    if list(frame.columns) != expected:
        raise ValueError(f"unexpected columns: {list(frame.columns)}")
    if frame["patient_id"].duplicated().any():
        raise ValueError("patient_id is not unique; one row must be one patient")
    if frame.isna().any().any():
        raise ValueError("the marker table must have no missing cells")
    if set(frame["group"]) != {RESPONDER, NON_RESPONDER}:
        raise ValueError(f"unexpected response labels: {sorted(set(frame['group']))}")
    if set(frame["stage"]) != {DISCOVERY, VALIDATION}:
        raise ValueError(f"unexpected split labels: {sorted(set(frame['stage']))}")
    return frame


def compare(half: pd.DataFrame, marker: str) -> dict[str, float]:
    """Two-group comparison of one marker: Welch's two-sample t-test, two-sided."""
    responders = half.loc[half["group"] == RESPONDER, marker]
    non_responders = half.loc[half["group"] == NON_RESPONDER, marker]
    result = stats.ttest_ind(responders, non_responders, equal_var=False)
    return {
        "n_resp": len(responders),
        "n_non": len(non_responders),
        "mean_resp": responders.mean(),
        "sd_resp": responders.std(ddof=1),
        "mean_non": non_responders.mean(),
        "sd_non": non_responders.std(ddof=1),
        "difference": responders.mean() - non_responders.mean(),
        "t": float(result.statistic),
        "df": float(result.df),
        "p": float(result.pvalue),
    }


def describe_cohort(frame: pd.DataFrame) -> None:
    print("Cohort")
    print("------")
    print(f"Patients (one row per patient): {len(frame)}")
    counts = pd.crosstab(frame["stage"], frame["group"])
    for stage in (DISCOVERY, VALIDATION):
        resp = int(counts.loc[stage, RESPONDER])
        non = int(counts.loc[stage, NON_RESPONDER])
        print(f"  {stage:<10} n = {resp + non:>2}  ({resp} responders, {non} non-responders)")
    print()


def stage_one(frame: pd.DataFrame) -> list[tuple[str, str, dict[str, float]]]:
    """Screening in the discovery half only. Returns the surviving markers in protocol order."""
    discovery = frame[frame["stage"] == DISCOVERY]

    print("Stage one: screening (discovery half only)")
    print("------------------------------------------")
    print(
        f"All six protocol-declared markers tested in the discovery half (n = {len(discovery)}). "
        f"Screening threshold stated in advance: unadjusted p < {SCREENING_THRESHOLD:.2f}. "
        "No multiplicity adjustment is applied at this stage, and nothing here is a claim "
        "about separation; the screen only decides what is carried forward."
    )
    print()
    header = f"{'marker':<34}{'responders':>22}{'non-responders':>22}{'p':>10}  outcome"
    print(header)
    print("-" * len(header))

    survivors: list[tuple[str, str, dict[str, float]]] = []
    for column, label in MARKERS:
        result = compare(discovery, column)
        carried = result["p"] < SCREENING_THRESHOLD
        if carried:
            survivors.append((column, label, result))
        resp = f"{result['mean_resp']:.1f} (SD {result['sd_resp']:.1f})"
        non = f"{result['mean_non']:.1f} (SD {result['sd_non']:.1f})"
        outcome = "carried forward" if carried else "dropped"
        print(f"{label:<34}{resp:>22}{non:>22}{result['p']:>10.4f}  {outcome}")

    print()
    if survivors:
        print(
            f"Markers carried into confirmation ({len(survivors)}): "
            + ", ".join(label for _, label, _ in survivors)
        )
    else:
        print("No marker met the screening threshold; nothing is carried into confirmation.")
    print()
    return survivors


def stage_two(frame: pd.DataFrame, survivors: list[tuple[str, str, dict[str, float]]]) -> None:
    """Confirmation in the validation half only, for the surviving markers alone."""
    validation = frame[frame["stage"] == VALIDATION]

    print("Stage two: confirmation (validation half only)")
    print("----------------------------------------------")
    if not survivors:
        print("No markers survived screening, so no confirmatory test was run.")
        print("No marker is confirmed. No claim of separation is made.")
        print()
        return

    n_tests = len(survivors)
    adjusted_alpha = FAMILY_ALPHA / n_tests
    print(
        f"Surviving markers re-tested in the validation half (n = {len(validation)}), "
        "which contributed nothing to screening."
    )
    print(
        f"Bonferroni adjustment over the {n_tests} confirmatory test(s): "
        f"alpha = {FAMILY_ALPHA:.2f} / {n_tests} = {adjusted_alpha:.4f}, "
        f"holding the family-wise error rate across the confirmatory tests at {FAMILY_ALPHA:.0%}."
    )
    print()
    header = f"{'marker':<34}{'responders':>22}{'non-responders':>22}{'p':>10}  outcome"
    print(header)
    print("-" * len(header))

    confirmed: list[str] = []
    for column, label, _ in survivors:
        result = compare(validation, column)
        passed = result["p"] < adjusted_alpha
        if passed:
            confirmed.append(label)
        resp = f"{result['mean_resp']:.1f} (SD {result['sd_resp']:.1f})"
        non = f"{result['mean_non']:.1f} (SD {result['sd_non']:.1f})"
        outcome = "confirmed" if passed else "not confirmed"
        print(f"{label:<34}{resp:>22}{non:>22}{result['p']:>10.4f}  {outcome}")

    print()
    print("Conclusion (rests on the validation stage alone)")
    print("------------------------------------------------")
    print(
        f"Adjusted level used: {adjusted_alpha:.4f} (Bonferroni, {FAMILY_ALPHA:.2f} over "
        f"{n_tests} marker(s) carried into validation)."
    )
    if confirmed:
        print("Confirmed markers: " + ", ".join(confirmed))
    else:
        print(
            "No marker separated responders from non-responders in the validation half "
            "at the adjusted level. The study confirms no baseline marker."
        )
    print()


def main() -> None:
    frame = load_data()
    print("Baseline blood markers and six-month response in early rheumatoid arthritis")
    print("Two-stage split-sample analysis")
    print("=" * 78)
    print()
    describe_cohort(frame)
    survivors = stage_one(frame)
    stage_two(frame, survivors)


if __name__ == "__main__":
    main()
