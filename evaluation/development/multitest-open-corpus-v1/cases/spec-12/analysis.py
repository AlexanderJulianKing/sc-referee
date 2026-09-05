"""Stool and blood markers in newly diagnosed coeliac disease.

The marker panel is exploratory, so the protocol split the subjects into a
discovery half and a validation half before any marker was measured. The
`cohort` column in data.csv records that split. It is fixed; nothing in this
script reassigns it.

Stage 1 screens all five markers in the discovery half. Screening results are
not findings.
Stage 2 tests only the markers that survived screening, in the validation half,
with a Holm-Bonferroni correction over that smaller family at a family-wide
five percent.
"""

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

FAMILY_WIDE_ALPHA = 0.05
SCREEN_ALPHA = 0.05

MARKERS = [
    "shannon_diversity",
    "faecal_calprotectin_ug_g",
    "scfa_butyrate_mmol_kg",
    "zonulin_ng_ml",
    "vitamin_d_nmol_l",
]


def compare(frame, marker):
    """Welch t-test of coeliac against healthy for one marker."""
    healthy = frame.loc[frame["status"] == "healthy", marker]
    coeliac = frame.loc[frame["status"] == "coeliac", marker]
    t_stat, p_value = stats.ttest_ind(healthy, coeliac, equal_var=False)
    return healthy.mean(), coeliac.mean(), p_value


def main():
    subjects = pd.read_csv("data.csv")
    discovery = subjects[subjects["cohort"] == "discovery"]
    validation = subjects[subjects["cohort"] == "validation"]

    print("Coeliac marker panel, pre-planned discovery / validation split")
    print(
        f"discovery: {len(discovery)} subjects "
        f"({(discovery['status'] == 'coeliac').sum()} coeliac)   "
        f"validation: {len(validation)} subjects "
        f"({(validation['status'] == 'coeliac').sum()} coeliac)"
    )
    print()

    # ---- Stage 1: screening ------------------------------------------------
    print("STAGE 1 - DISCOVERY HALF (screening only, not reported as findings)")
    print("These p-values decide only which markers go forward to validation.")
    print("No marker is called a finding on the strength of this stage.")
    print(f"{'marker':26s} {'healthy':>9s} {'coeliac':>9s} {'p':>11s}  carried forward")

    carried_forward = []
    for marker in MARKERS:
        healthy_mean, coeliac_mean, p_value = compare(discovery, marker)
        passes = p_value < SCREEN_ALPHA
        if passes:
            carried_forward.append(marker)
        print(
            f"{marker:26s} {healthy_mean:9.2f} {coeliac_mean:9.2f} "
            f"{p_value:11.4g}  {'yes' if passes else 'no'}"
        )

    print()
    print(f"markers carried forward: {len(carried_forward)} of {len(MARKERS)}")
    if not carried_forward:
        print("nothing survived screening; no validation family to test")
        return

    # ---- Stage 2: validation ----------------------------------------------
    print()
    print("STAGE 2 - VALIDATION HALF (this is where findings are decided)")
    print(f"validation family size: {len(carried_forward)} tests")
    print(f"Holm-Bonferroni correction, family-wide alpha = {FAMILY_WIDE_ALPHA}")

    raw_p = []
    means = {}
    for marker in carried_forward:
        healthy_mean, coeliac_mean, p_value = compare(validation, marker)
        means[marker] = (healthy_mean, coeliac_mean)
        raw_p.append(p_value)

    rejected, adjusted_p, _, _ = multipletests(
        raw_p, alpha=FAMILY_WIDE_ALPHA, method="holm"
    )

    print(
        f"{'marker':26s} {'healthy':>9s} {'coeliac':>9s} "
        f"{'raw p':>11s} {'Holm p':>11s}  verdict"
    )
    findings = []
    for marker, p_value, p_adj, is_finding in zip(
        carried_forward, raw_p, adjusted_p, rejected
    ):
        healthy_mean, coeliac_mean = means[marker]
        if is_finding:
            findings.append(marker)
        print(
            f"{marker:26s} {healthy_mean:9.2f} {coeliac_mean:9.2f} "
            f"{p_value:11.4g} {p_adj:11.4g}  "
            f"{'FINDING' if is_finding else 'not significant'}"
        )

    print()
    print(f"findings ({len(findings)}): {', '.join(findings) if findings else 'none'}")


if __name__ == "__main__":
    main()
