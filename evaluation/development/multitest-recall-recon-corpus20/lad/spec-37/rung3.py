"""Two injectable anaesthetic protocols for feline ovariohysterectomy.

Six outcomes are compared between protocols. The two safety outcomes (lowest mean
arterial pressure and apnoea events) were pre-designated and go through a Holm
correction at a five-percent family level; the four efficacy outcomes are read
against five percent as they come out of the test.
"""

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

DATA = "data.csv"
GROUP = "protocol"
ARM_A = "protocol_a"
ARM_B = "protocol_b"

OUTCOMES = [
    "induction_time_s",
    "recovery_time_min",
    "lowest_map_mmhg",
    "lowest_temp_c",
    "rescue_analgesia_score",
    "apnoea_events",
]

SAFETY = ["lowest_map_mmhg", "apnoea_events"]
EFFICACY = [name for name in OUTCOMES if name not in SAFETY]

ALPHA = 0.05
CORRECTION = "holm"


def compare(cats, outcome):
    a = cats.loc[cats[GROUP] == ARM_A, outcome].to_numpy()
    b = cats.loc[cats[GROUP] == ARM_B, outcome].to_numpy()
    result = stats.ttest_ind(a, b, equal_var=False)
    return {
        "outcome": outcome,
        "mean_a": a.mean(),
        "mean_b": b.mean(),
        "diff": b.mean() - a.mean(),
        "p_raw": float(result.pvalue),
    }


def main():
    cats = pd.read_csv(DATA)
    print("Cats analysed: %d (%s %d, %s %d)" % (
        len(cats),
        ARM_A, int((cats[GROUP] == ARM_A).sum()),
        ARM_B, int((cats[GROUP] == ARM_B).sum()),
    ))
    print()

    tests = {name: compare(cats, name) for name in OUTCOMES}

    # Family-wide control over the two pre-designated safety outcomes.
    safety_p = [tests[name]["p_raw"] for name in SAFETY]
    reject, p_adj, _, _ = multipletests(safety_p, alpha=ALPHA, method=CORRECTION)
    for name, adj, rej in zip(SAFETY, p_adj, reject):
        tests[name]["p_used"] = float(adj)
        tests[name]["significant"] = bool(rej)
        tests[name]["basis"] = "%s-adjusted" % CORRECTION

    for name in EFFICACY:
        tests[name]["p_used"] = tests[name]["p_raw"]
        tests[name]["significant"] = tests[name]["p_raw"] < ALPHA
        tests[name]["basis"] = "raw"

    header = "%-24s %11s %11s %9s %9s  %s" % (
        "outcome", ARM_A, ARM_B, "diff", "p", "verdict")
    print(header)
    print("-" * len(header))
    for name in OUTCOMES:
        row = tests[name]
        print(f"{name:-24s} {row['mean_a']:11.3f} {row['mean_b']:11.3f} {row['diff']:9.3f} {row['p_used']:9.4f}  " + ("significant" if row["significant"] else "not significant"))

    print()
    print("Differences are %s minus %s. Verdicts use alpha = %.2f." % (
        ARM_B, ARM_A, ALPHA))
    print("Safety outcomes carry adjusted p-values.")

    wins_b = [n for n in OUTCOMES if tests[n]["significant"] and tests[n]["diff"] < 0]
    wins_a = [n for n in OUTCOMES if tests[n]["significant"] and tests[n]["diff"] > 0]
    print()
    print("Significant and lower under %s: %s" % (ARM_B, ", ".join(wins_b) or "none"))
    print("Significant and higher under %s: %s" % (ARM_B, ", ".join(wins_a) or "none"))


if __name__ == "__main__":
    main()
