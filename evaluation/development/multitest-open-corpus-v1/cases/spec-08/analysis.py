"""Lung function and inflammation after a heavy wildfire smoke deployment.

36 deployed wildland firefighters against 36 station-based colleagues from the same
agency. The six outcomes are treated as one family and corrected for multiplicity
with multipy (https://puolival.github.io/multipy/), which implements the
Benjamini-Hochberg linear step-up procedure controlling the false discovery rate.
See requirements.txt.
"""

import numpy as np
import pandas as pd
from multipy.fdr import lsu
from scipy import stats

FDR = 0.05

OUTCOMES = [
    "fev1_l",
    "fvc_l",
    "feno_ppb",
    "crp_mg_l",
    "carboxyhaemoglobin_pct",
    "symptom_score",
]


def adjusted_from_package(pvalues, index):
    """Smallest FDR level at which multipy's step-up procedure rejects this outcome.

    multipy.fdr.lsu returns accept/reject flags rather than adjusted p-values, so the
    adjusted value is recovered by bisecting on q: the flag is monotone in q, and the
    level where it flips is the adjusted p-value of the Benjamini-Hochberg procedure.
    """
    if not lsu(pvalues, q=1.0)[index]:
        return 1.0
    low, high = 0.0, 1.0
    for _ in range(60):
        mid = (low + high) / 2
        if lsu(pvalues, q=mid)[index]:
            high = mid
        else:
            low = mid
    return high


def main():
    data = pd.read_csv("data.csv")
    station = data[data["deployment"] == "station"]
    wildland = data[data["deployment"] == "wildland"]

    raw = np.array([stats.ttest_ind(station[o], wildland[o], equal_var=False).pvalue
                    for o in OUTCOMES])
    reject = lsu(raw, q=FDR)
    adjusted = [adjusted_from_package(raw, i) for i in range(len(OUTCOMES))]

    print(f"n = {len(station)} station-based, {len(wildland)} wildland")
    print(f"Family = all {len(OUTCOMES)} outcomes; multipy linear step-up, FDR = {FDR}\n")
    print(f"{'outcome':<26}{'station':>10}{'wildland':>10}{'raw p':>10}"
          f"{'adj p':>10}  multipy decision")
    for outcome, p, p_adj, rejected in zip(OUTCOMES, raw, adjusted, reject):
        decision = "significant" if rejected else "not significant"
        print(f"{outcome:<26}{station[outcome].mean():>10.2f}{wildland[outcome].mean():>10.2f}"
              f"{p:>10.4f}{p_adj:>10.4f}  {decision}")

    survivors = [o for o, r in zip(OUTCOMES, reject) if r]
    print(f"\nOutcomes multipy keeps at FDR {FDR}: {', '.join(survivors)}")


if __name__ == "__main__":
    main()
