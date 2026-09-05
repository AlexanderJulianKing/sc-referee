"""Executed false-accusation fixtures for the proposed deltas.

Each fixture is a CORRECT analysis (the whole authorized family is corrected, or the
correction is real but unresolvable) written in the idiom the delta admits. The required
outcome is `covered` or `abstain` - never `candidate`.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import h  # noqa: E402
import patched  # noqa: E402

P6 = h.E12 / "68d1a6f5b1ab70f2650a"  # allergy_spray_trial.csv, 5 outcomes
P3 = h.E12 / "e28a9537b07c74d21838"  # guinea_pig_hay_study.csv, 6 outcomes

HEAD_P6 = '''"""FA fixture."""
from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "allergy_spray_trial.csv"
GROUP_COL = "group"
ARM_A = "corticosteroid"
ARM_B = "antihistamine"
ALPHA = 0.05
OUTCOMES = [
    ("tnss_total", "Total nasal symptom score"),
    ("pnif_l_min", "Peak nasal inspiratory flow"),
    ("disturbed_nights", "Nights with disturbed sleep"),
    ("tos_total", "Total ocular symptom score"),
    ("rqlq_total", "Rhinoconjunctivitis QoL total"),
]
'''

# ---------------------------------------------------------------------------------
# FA-3: delta 3 (len(OUTCOMES) admitted as the exact family size) must not turn a
# CORRECT whole-family hand Bonferroni into a strict_subset accusation.
# ---------------------------------------------------------------------------------
FA3 = HEAD_P6 + '''

def main():
    df = pd.read_csv(DATA_FILE)
    n_comparisons = len(OUTCOMES)
    for column, label in OUTCOMES:
        a = df.loc[df[GROUP_COL] == ARM_A, column]
        b = df.loc[df[GROUP_COL] == ARM_B, column]
        result = stats.ttest_ind(a, b, equal_var=False)
        p_used = min(1.0, float(result.pvalue) * n_comparisons)
        verdict = "significant" if p_used < ALPHA else "not significant"
        print(f"{label}: corrected p = {p_used:.4f} -> {verdict}")


if __name__ == "__main__":
    main()
'''

# ---------------------------------------------------------------------------------
# FA-3b: the multiplier is len() of a container that is NOT the authorized family.
# Must still fail closed.
# ---------------------------------------------------------------------------------
FA3B = HEAD_P6 + '''
REPORTED = ["tnss_total", "pnif_l_min", "disturbed_nights"]


def main():
    df = pd.read_csv(DATA_FILE)
    n_comparisons = len(REPORTED)
    for column, label in OUTCOMES:
        a = df.loc[df[GROUP_COL] == ARM_A, column]
        b = df.loc[df[GROUP_COL] == ARM_B, column]
        result = stats.ttest_ind(a, b, equal_var=False)
        p_used = min(1.0, float(result.pvalue) * n_comparisons)
        verdict = "significant" if p_used < ALPHA else "not significant"
        print(f"{label}: corrected p = {p_used:.4f} -> {verdict}")


if __name__ == "__main__":
    main()
'''

# ---------------------------------------------------------------------------------
# FA-5: delta 5 (closed set literal admitted for membership) must not fire when the
# set is mutated anywhere in the module.
# ---------------------------------------------------------------------------------
FA5 = HEAD_P6 + '''
CORRECTED = {"tnss_total", "pnif_l_min"}


def widen():
    CORRECTED.add("disturbed_nights")
    CORRECTED.add("tos_total")
    CORRECTED.add("rqlq_total")


def main():
    df = pd.read_csv(DATA_FILE)
    widen()
    n_comparisons = len(OUTCOMES)
    for column, label in OUTCOMES:
        a = df.loc[df[GROUP_COL] == ARM_A, column]
        b = df.loc[df[GROUP_COL] == ARM_B, column]
        result = stats.ttest_ind(a, b, equal_var=False)
        if column in CORRECTED:
            p_used = min(1.0, float(result.pvalue) * n_comparisons)
        else:
            p_used = float(result.pvalue)
        verdict = "significant" if p_used < ALPHA else "not significant"
        print(f"{label}: p = {p_used:.4f} -> {verdict}")


if __name__ == "__main__":
    main()
'''

# ---------------------------------------------------------------------------------
# FA-5b: same shape, set NOT mutated but covering the WHOLE family. Correct analysis;
# must come back covered (complete), never a candidate.
# ---------------------------------------------------------------------------------
FA5B = HEAD_P6 + '''
CORRECTED = {"tnss_total", "pnif_l_min", "disturbed_nights", "tos_total", "rqlq_total"}


def main():
    df = pd.read_csv(DATA_FILE)
    n_comparisons = len(OUTCOMES)
    for column, label in OUTCOMES:
        a = df.loc[df[GROUP_COL] == ARM_A, column]
        b = df.loc[df[GROUP_COL] == ARM_B, column]
        result = stats.ttest_ind(a, b, equal_var=False)
        if column in CORRECTED:
            p_used = min(1.0, float(result.pvalue) * n_comparisons)
        else:
            p_used = float(result.pvalue)
        verdict = "significant" if p_used < ALPHA else "not significant"
        print(f"{label}: p = {p_used:.4f} -> {verdict}")


if __name__ == "__main__":
    main()
'''

# ---------------------------------------------------------------------------------
# FA-6: delta 6 (second terminal-helper pass) must not erase a correction hidden in a
# helper that LOOKS like presentation. The helper multiplies before formatting.
# ---------------------------------------------------------------------------------
FA6 = HEAD_P6 + '''

def show_p(p):
    return "<0.001" if p < 0.001 else f"{min(1.0, p * 5):.3f}"


def render(label, p):
    print(f"{label}: p = {show_p(p)}")


def main():
    df = pd.read_csv(DATA_FILE)
    for column, label in OUTCOMES:
        a = df.loc[df[GROUP_COL] == ARM_A, column]
        b = df.loc[df[GROUP_COL] == ARM_B, column]
        result = stats.ttest_ind(a, b, equal_var=False)
        p_used = min(1.0, float(result.pvalue) * 5)
        render(label, p_used)
        print("significant" if p_used < ALPHA else "not significant")


if __name__ == "__main__":
    main()
'''

# ---------------------------------------------------------------------------------
# FA-2: delta 2 (family-test hoist) applied to a CORRECT analysis whose battery is an
# inline comprehension and whose whole family is corrected in one call.
# ---------------------------------------------------------------------------------
FA2 = '''"""FA fixture."""
from pathlib import Path

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

DATA_FILE = Path(__file__).resolve().parent / "guinea_pig_hay_study.csv"
GROUP_COLUMN = "group"
RACK = "hay_rack"
BLOCK = "forage_block"
ALPHA = 0.05
OUTCOMES = [
    ("hay_intake_g_day", "Daily hay dry matter intake"),
    ("body_weight_g", "End-of-study body weight"),
    ("faecal_output_g_day", "Daily faecal output"),
    ("faecal_particle_mm", "Median faecal particle size"),
    ("chewing_min_day", "Time spent chewing per day"),
    ("occlusal_angle_deg", "Cheek tooth occlusal angle"),
]


def compare(rack_values, block_values):
    return stats.ttest_ind(rack_values, block_values, equal_var=False)


def main():
    data = pd.read_csv(DATA_FILE)
    rack = data[data[GROUP_COLUMN] == RACK]
    block = data[data[GROUP_COLUMN] == BLOCK]

    results = [
        {
            "column": column,
            "label": label,
            "p_value": float(compare(rack[column], block[column]).pvalue),
        }
        for column, label in OUTCOMES
    ]

    adjusted = multipletests(
        [item["p_value"] for item in results], alpha=ALPHA, method="holm"
    )[1]
    for item, p_adj in zip(results, adjusted):
        item["p_adjusted"] = float(p_adj)

    for item in results:
        verdict = "significant" if item["p_adjusted"] < ALPHA else "not significant"
        print(f"{item['label']}: Holm p = {item['p_adjusted']:.4f} -> {verdict}")


if __name__ == "__main__":
    main()
'''

FIXTURES = [
    ("FA-2  delta2: inline-comprehension battery, WHOLE family Holm", P3, FA2),
    ("FA-3  delta3: whole-family hand Bonferroni, x len(OUTCOMES)", P6, FA3),
    ("FA-3b delta3: multiplier is len() of a NON-family container", P6, FA3B),
    ("FA-5  delta5: membership set MUTATED before use", P6, FA5),
    ("FA-5b delta5: membership set covers the WHOLE family", P6, FA5B),
    ("FA-6  delta6: 'presentation' helper that secretly corrects", P6, FA6),
]


def main() -> None:
    base = patched.analyzer("")
    new = patched.analyzer("2356")
    for label, case, source in FIXTURES:
        b = h.classify(h.analyze_envelope(case, source.encode(), fn=base))
        n = h.classify(h.analyze_envelope(case, source.encode(), fn=new))
        flag = "  <== FALSE ACCUSATION" if n[0] == "candidate" else ""
        print(f"{label:<62}\n    baseline {b}\n    delta    {n}{flag}")


if __name__ == "__main__":
    main()
