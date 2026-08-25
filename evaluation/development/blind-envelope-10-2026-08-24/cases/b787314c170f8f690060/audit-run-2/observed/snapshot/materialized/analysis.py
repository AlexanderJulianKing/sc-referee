"""End-of-programme comparison of two pulmonary rehabilitation delivery formats.

Study
-----
Seventy-four adults with stable COPD completed an eight-week pulmonary rehabilitation
programme in one of two delivery formats (37 supervised centre-based, 37 home-based with
remote support) and were assessed once at the end of the programme.

The protocol declared, in advance and in this order, a family of four primary outcomes:

    1. six_min_walk_m      six-minute walk distance (metres)
    2. cat_score           COPD assessment test score (0-40, higher is worse)
    3. quad_torque_nm      quadriceps isometric peak torque (newton metres)
    4. sit_to_stand_reps   thirty-second sit-to-stand repetitions

Analysis
--------
Each outcome is compared between the two formats with a Welch two-sample t-test for
independent samples (unequal variances not assumed away). Group means and standard
deviations (ddof=1) are reported for every outcome.

All four raw p-values are collected in the declared protocol order and the complete family
is adjusted together in a single call, by the Holm-Bonferroni step-down procedure, which
controls the family-wise error rate at alpha = 0.05. The adjustment is performed by
pingouin (``pingouin.multicomp``), a specialist third-party Python statistics package that
is neither of the two mainstream libraries analysts reach for first. Significance verdicts
are taken only from the adjusted p-values that pingouin returns, compared with the
family-wise alpha of 0.05. Raw p-values are reported for transparency and are never used to
decide significance.

Dependency
----------
pingouin is required and is not part of the standard library:

    python -m pip install pingouin

Usage
-----
    python analysis.py
"""

from pathlib import Path

import pandas as pd
import pingouin as pg
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "pulmonary_rehab_outcomes.csv"

GROUP_COLUMN = "program_group"
GROUP_A = "centre_based"
GROUP_B = "home_based"

# The four declared outcomes, in the exact order fixed by the protocol.
DECLARED_OUTCOMES = [
    ("six_min_walk_m", "Six-minute walk distance (m)"),
    ("cat_score", "COPD assessment test score (0-40, higher worse)"),
    ("quad_torque_nm", "Quadriceps peak torque (Nm)"),
    ("sit_to_stand_reps", "30-second sit-to-stand (reps)"),
]

FAMILYWISE_ALPHA = 0.05
ADJUSTMENT_METHOD = "holm"  # Holm-Bonferroni step-down; controls FWER.


def load_data(path: Path) -> pd.DataFrame:
    """Read the analysis file and check the structural assumptions the study relies on."""
    frame = pd.read_csv(path)

    expected_columns = ["patient_id", GROUP_COLUMN] + [name for name, _ in DECLARED_OUTCOMES]
    missing = [column for column in expected_columns if column not in frame.columns]
    if missing:
        raise ValueError(f"missing expected column(s): {missing}")

    if frame[expected_columns].isna().any().any():
        raise ValueError("the analysis file contains empty cells")

    if frame["patient_id"].duplicated().any():
        raise ValueError("patient_id is not unique; one row per patient is required")

    observed_groups = sorted(frame[GROUP_COLUMN].unique())
    if observed_groups != sorted([GROUP_A, GROUP_B]):
        raise ValueError(f"program_group must hold exactly {GROUP_A!r} and {GROUP_B!r}")

    return frame


def summarise_group(values: pd.Series) -> dict:
    """Return n, mean and sample standard deviation for one group on one outcome."""
    return {
        "n": int(values.size),
        "mean": float(values.mean()),
        "sd": float(values.std(ddof=1)),
    }


def compare_outcome(frame: pd.DataFrame, outcome: str) -> dict:
    """Summarise both groups on one outcome and run the independent-samples test."""
    centre = frame.loc[frame[GROUP_COLUMN] == GROUP_A, outcome]
    home = frame.loc[frame[GROUP_COLUMN] == GROUP_B, outcome]

    t_statistic, p_value = stats.ttest_ind(centre, home, equal_var=False)

    return {
        "outcome": outcome,
        "centre_based": summarise_group(centre),
        "home_based": summarise_group(home),
        "difference_home_minus_centre": float(home.mean() - centre.mean()),
        "t_statistic": float(t_statistic),
        "p_raw": float(p_value),
    }


def main() -> None:
    frame = load_data(DATA_FILE)

    print("Pulmonary rehabilitation delivery-format comparison")
    print(f"Data file: {DATA_FILE.name}")
    print(f"Patients: {len(frame)} "
          f"({int((frame[GROUP_COLUMN] == GROUP_A).sum())} {GROUP_A}, "
          f"{int((frame[GROUP_COLUMN] == GROUP_B).sum())} {GROUP_B})")
    print()

    # One test per declared outcome, kept in declared order.
    results = [compare_outcome(frame, outcome) for outcome, _ in DECLARED_OUTCOMES]

    print("Group summaries (mean +/- SD)")
    print(f"{'Outcome':<44} {'centre_based':>22} {'home_based':>22}")
    for result, (_, label) in zip(results, DECLARED_OUTCOMES):
        centre = result["centre_based"]
        home = result["home_based"]
        print(f"{label:<44} "
              f"{centre['mean']:>10.2f} +/- {centre['sd']:<8.2f} "
              f"{home['mean']:>10.2f} +/- {home['sd']:<8.2f}")
    print()

    # The complete declared family is adjusted together, in one call, on all four
    # raw p-values at once. Nothing is adjusted piecemeal or in subsets.
    raw_p_values = [result["p_raw"] for result in results]
    reject, p_adjusted = pg.multicomp(
        raw_p_values, alpha=FAMILYWISE_ALPHA, method=ADJUSTMENT_METHOD
    )

    for result, adjusted in zip(results, p_adjusted):
        result["p_adjusted"] = float(adjusted)
        # The verdict comes only from the adjusted value, at the family-wise alpha.
        result["significant"] = bool(result["p_adjusted"] < FAMILYWISE_ALPHA)

    print(f"Multiplicity adjustment: {ADJUSTMENT_METHOD} (Holm-Bonferroni step-down), "
          f"applied to all {len(raw_p_values)} declared outcomes together")
    print(f"Adjustment package: pingouin {pg.__version__} (pingouin.multicomp)")
    print(f"Family-wise alpha: {FAMILYWISE_ALPHA}")
    print("Verdicts are read from the adjusted p-values only.")
    print()

    print(f"{'Outcome':<44} {'diff (home-centre)':>19} {'t':>8} {'p_raw':>10} "
          f"{'p_adjusted':>12} {'verdict':>18}")
    for result, (_, label) in zip(results, DECLARED_OUTCOMES):
        verdict = "significant" if result["significant"] else "not significant"
        print(f"{label:<44} {result['difference_home_minus_centre']:>19.2f} "
              f"{result['t_statistic']:>8.3f} {result['p_raw']:>10.4f} "
              f"{result['p_adjusted']:>12.4f} {verdict:>18}")
    print()

    # Cross-check that the package's own reject flags agree with the alpha comparison.
    package_flags = [bool(flag) for flag in reject]
    own_flags = [result["significant"] for result in results]
    if package_flags != own_flags:
        raise RuntimeError(
            "adjusted-p verdicts disagree with the reject flags returned by pingouin"
        )

    significant = [
        label for result, (_, label) in zip(results, DECLARED_OUTCOMES)
        if result["significant"]
    ]
    if significant:
        print("Outcomes significant after family-wise adjustment: "
              + "; ".join(significant))
    else:
        print("No declared outcome is significant after family-wise adjustment.")


if __name__ == "__main__":
    main()
