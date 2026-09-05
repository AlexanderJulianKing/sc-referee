"""Mandibular advancement device study: comparison of two device designs.

Reads mad_device_study.csv from the project root and compares the two device
groups on the five outcomes declared in the study protocol, in the declared
order. Every outcome uses the same test (Welch's two-sample t-test). The five
outcomes are one pre-declared family, so the complete set of five raw p-values
is adjusted together with the Holm step-down procedure, which controls the
family-wise error rate at ALPHA. Every inferential verdict is read from the
adjusted p-values.

A single sensitivity check re-runs the minimum oxygen saturation comparison with
one sensor-artefact reading excluded. It is a robustness check on that one
outcome, not a sixth family member and not an inferential verdict.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

CSV_PATH = Path(__file__).resolve().parent / "mad_device_study.csv"

GROUP_COLUMN = "device_group"
GROUP_A = "custom_titratable_two_piece"
GROUP_B = "prefabricated_one_piece"

# The five protocol outcomes, in the order declared before recruitment.
DECLARED_OUTCOMES = [
    "ahi_events_per_hour",
    "odi_events_per_hour",
    "epworth_sleepiness_score_0_24",
    "min_oxygen_saturation_percent",
    "sleep_efficiency_percent",
]

ALPHA = 0.05

# Sensor-artefact reading flagged in DATA_DESCRIPTION.md: the pulse oximeter
# probe slipped off the finger, so this value does not measure the participant's
# overnight nadir. Excluded only in the sensitivity check below.
ARTEFACT_PARTICIPANT = "P032"
ARTEFACT_OUTCOME = "min_oxygen_saturation_percent"


def welch_t_test(values_a, values_b):
    """Two-sample Welch t-test, the single test used for every outcome."""
    result = stats.ttest_ind(values_a, values_b, equal_var=False)
    return float(result.statistic), float(result.pvalue)


def holm_adjust(p_values):
    """Holm step-down adjusted p-values for the complete family.

    Returns adjusted p-values in the input order. Comparing them to ALPHA
    controls the family-wise error rate across the whole family.
    """
    n = len(p_values)
    order = sorted(range(n), key=lambda i: p_values[i])
    adjusted = [0.0] * n
    running_max = 0.0
    for rank, idx in enumerate(order):
        candidate = (n - rank) * p_values[idx]
        running_max = max(running_max, candidate)
        adjusted[idx] = min(1.0, running_max)
    return adjusted


def main():
    data = pd.read_csv(CSV_PATH)

    group_a = data[data[GROUP_COLUMN] == GROUP_A]
    group_b = data[data[GROUP_COLUMN] == GROUP_B]

    print("Mandibular advancement device study")
    print("=" * 78)
    print(f"Data file: {CSV_PATH.name}")
    print(f"Participants: {len(data)} (one row per participant)")
    print(f"Group A: {GROUP_A}, n = {len(group_a)}")
    print(f"Group B: {GROUP_B}, n = {len(group_b)}")
    print()
    print("Test used for every outcome: Welch's two-sample t-test.")
    print(
        f"Multiplicity: all {len(DECLARED_OUTCOMES)} declared outcomes form one family; "
        "the complete set of five raw p-values is adjusted together"
    )
    print(f"  with the Holm step-down procedure, family-wise alpha = {ALPHA}.")
    print("Verdicts are taken from the adjusted p-values only.")
    print()

    print("PER-OUTCOME COMPARISONS (raw)")
    print("-" * 78)

    raw_results = []
    for outcome in DECLARED_OUTCOMES:
        values_a = group_a[outcome].to_numpy(dtype=float)
        values_b = group_b[outcome].to_numpy(dtype=float)
        statistic, p_value = welch_t_test(values_a, values_b)
        raw_results.append(
            {
                "outcome": outcome,
                "n_a": len(values_a),
                "n_b": len(values_b),
                "mean_a": values_a.mean(),
                "mean_b": values_b.mean(),
                "statistic": statistic,
                "p_raw": p_value,
            }
        )
        print(f"{outcome}")
        print(f"  n ({GROUP_A})      = {len(values_a)}")
        print(f"  n ({GROUP_B})          = {len(values_b)}")
        print(f"  mean ({GROUP_A})   = {values_a.mean():.3f}")
        print(f"  mean ({GROUP_B})       = {values_b.mean():.3f}")
        print(f"  Welch t statistic                    = {statistic:.4f}")
        print(f"  raw p-value                          = {p_value:.6f}")
        print()

    adjusted = holm_adjust([r["p_raw"] for r in raw_results])
    for result, p_adj in zip(raw_results, adjusted):
        result["p_adjusted"] = p_adj
        result["significant"] = p_adj < ALPHA

    print(f"FAMILY-WISE ADJUSTED RESULTS (Holm, {len(DECLARED_OUTCOMES)} outcomes, alpha = {ALPHA})")
    print("-" * 78)
    header = f"{'outcome':<32}{'raw p':>12}{'adjusted p':>14}{'verdict':>18}"
    print(header)
    for result in raw_results:
        verdict = "significant" if result["significant"] else "not significant"
        print(
            f"{result['outcome']:<32}"
            f"{result['p_raw']:>12.6f}"
            f"{result['p_adjusted']:>14.6f}"
            f"{verdict:>18}"
        )
    print()
    print(
        "All five declared outcomes were adjusted together as one complete family; "
        "no outcome was adjusted on its own."
    )
    print()

    # --- Sensitivity check (not a sixth family member, not a verdict) ---
    print("SENSITIVITY CHECK (robustness only; not part of the adjusted family)")
    print("-" * 78)
    print(
        f"Re-run of {ARTEFACT_OUTCOME} with participant {ARTEFACT_PARTICIPANT} excluded, "
        "whose reading came from a"
    )
    print(
        "pulse oximeter probe that slipped off the finger. This single re-run is a "
        "robustness check on one"
    )
    print(
        "outcome. It is not a sixth result, it is not adjusted into the family, and it "
        "carries no inferential"
    )
    print("verdict. The study's inference stays with the Holm-adjusted family analysis above.")
    print()

    sensitivity_data = data[data["participant_id"] != ARTEFACT_PARTICIPANT]
    sens_a = sensitivity_data[sensitivity_data[GROUP_COLUMN] == GROUP_A][
        ARTEFACT_OUTCOME
    ].to_numpy(dtype=float)
    sens_b = sensitivity_data[sensitivity_data[GROUP_COLUMN] == GROUP_B][
        ARTEFACT_OUTCOME
    ].to_numpy(dtype=float)
    sens_statistic, sens_p = welch_t_test(sens_a, sens_b)

    family_result = next(r for r in raw_results if r["outcome"] == ARTEFACT_OUTCOME)
    print(f"  n ({GROUP_A})      = {len(sens_a)}")
    print(f"  n ({GROUP_B})          = {len(sens_b)}")
    print(f"  mean ({GROUP_A})   = {sens_a.mean():.3f}")
    print(f"  mean ({GROUP_B})       = {sens_b.mean():.3f}")
    print(f"  Welch t statistic                    = {sens_statistic:.4f}")
    print(f"  p-value (unadjusted, descriptive)    = {sens_p:.6f}")
    print(
        f"  For reference, the family analysis of {ARTEFACT_OUTCOME} gave "
        f"raw p = {family_result['p_raw']:.6f},"
    )
    print(
        f"  adjusted p = {family_result['p_adjusted']:.6f}, verdict "
        f"'{'significant' if family_result['significant'] else 'not significant'}', "
        "and that verdict stands."
    )


if __name__ == "__main__":
    main()
