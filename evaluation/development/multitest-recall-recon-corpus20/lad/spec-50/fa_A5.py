"""Sensor-driven ventilation against conventional minimum ventilation in two
adjacent broiler houses.

80 sampling records across one cycle, 40 per strategy. Six outcomes were
measured, four air-quality, one welfare, one energy, and the six raw p-values are
held together as a single family. The multiplicity correction is done with
multipy, a package written for multiple hypothesis testing, controlling the false
discovery rate at 5 percent across all six. Only multipy's decisions are allowed
to support a claim of a difference. Package version is pinned in requirements.txt.
"""

import numpy as np
import pandas as pd
from multipy.fdr import lsu
from scipy import stats

FDR_Q = 0.05

OUTCOMES = [
    ("ammonia_ppm", "ammonia (ppm)", 1),
    ("co2_ppm", "carbon dioxide (ppm)", 0),
    ("dust_pm10_mg_m3", "dust PM10 (mg/m3)", 2),
    ("litter_moisture_pct", "litter moisture (%)", 1),
    ("footpad_score", "footpad score (0-4)", 2),
    ("heating_kwh_per_1000_birds", "heating (kWh/1000 birds)", 0),
]


def adjusted_p(pvals, index, iterations=60):
    """Smallest FDR level at which multipy still rejects this outcome.

    multipy.fdr.lsu returns reject or accept decisions, not adjusted p-values, so
    the adjusted value is read off the procedure itself: bisect on q and find the
    lowest level at which the procedure still calls this outcome significant.
    Decisions from lsu are monotone in q, so the bisection is well defined.
    """
    if not lsu(pvals, q=1.0)[index]:
        return 1.0
    low, high = 0.0, 1.0
    for _ in range(iterations):
        mid = (low + high) / 2.0
        if lsu(pvals, q=mid)[index]:
            high = mid
        else:
            low = mid
    return high


def fmt_p(p):
    return f"{p:.2e}" if p < 1e-4 else f"{p:.5f}"


def main():
    data = pd.read_csv("data.csv")
    conventional = data[data["strategy"] == "conventional"]
    sensor = data[data["strategy"] == "sensor_driven"]
    print(f"Records: conventional n={len(conventional)}, sensor_driven n={len(sensor)}")
    print("Test: two-sample Welch t-test on the difference in means, two sided.")

    raw_p = []
    means_conv, means_sensor = [], []
    for column, _label, _dp in OUTCOMES:
        a = conventional[column]
        b = sensor[column]
        raw_p.append(stats.ttest_ind(a, b, equal_var=False).pvalue)
        means_conv.append(a.mean())
        means_sensor.append(b.mean())

    raw_p = np.asarray(raw_p)

    # One family, six p-values, Benjamini-Hochberg linear step-up from multipy.
    significant = lsu(raw_p, q=FDR_Q)
    adjusted = np.array([adjusted_p(raw_p, i) for i in range(len(raw_p))])

    print(f"Correction: multipy.fdr.lsu, the Benjamini-Hochberg linear step-up "
          f"procedure, false discovery rate q = {FDR_Q:.2f}")
    print(f"Family: all {len(OUTCOMES)} outcomes below, corrected together.\n")

    header = (f"{'outcome':<26}{'conventional':>14}{'sensor':>10}{'diff':>10}"
              f"{'raw p':>12}{'adjusted':>11}  multipy decision")
    print(header)
    print("-" * len(header))
    for (column, label, dp), m_conv, m_sensor, p_raw, p_adj, sig in zip(
        OUTCOMES, means_conv, means_sensor, raw_p, adjusted, significant
    ):
        decision = "significant" if sig else "not significant"
        print(f"{label:<26}{m_conv:>14.{dp}f}{m_sensor:>10.{dp}f}"
              f"{m_conv - m_sensor:>10.{dp}f}{p_raw:>12.5f}{p_adj:>11.5f}"
              f"  {decision}")

    print()
    print(f"{int(significant.sum())} of {len(OUTCOMES)} outcomes are called "
          f"significant at FDR {FDR_Q:.0%}. No claim of a difference is made for any "
          f"outcome multipy did not reject.")


if __name__ == "__main__":
    main()
