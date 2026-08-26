#!/usr/bin/env python3
"""Sensory panel analysis: current oat drink formulation vs reformulation.

Design
------
Sixty trained-naive consumer panellists, one session, each panellist tasting
exactly one formulation (30 per formulation) blind under red light. The
panellist is the unit of the study, so every row of ``panel_data.csv`` is an
independent unit and the two groups are independent samples.

Declared outcome family (fixed order, all five declared together as one family)
-------------------------------------------------------------------------------
1. overall_liking   nine-point hedonic scale, 1-9
2. sweetness        unstructured line scale, 0-100
3. thickness        unstructured line scale, 0-100
4. cereal_off_note  unstructured line scale, 0-100
5. purchase_intent  seven-point scale, 1-7

Multiplicity control
--------------------
Family-wise error is controlled by the laboratory's own resampling procedure,
implemented by hand below and not by any ready-made multiple-comparison
routine: a max-statistic (max-T) label-permutation reference distribution.
The formulation labels are shuffled across panellists a number of times fixed
in advance (N_SHUFFLES); each panellist keeps their own five ratings and only
the formulation label moves. Each shuffle contributes exactly one value to the
reference distribution: the largest absolute test statistic over the whole
family of five outcomes from that shuffle. Each observed statistic is then
compared against that single family-maximum distribution.

Test statistic
--------------
Welch's two-sample t statistic (unequal variances not assumed equal). It is
unitless, so the five outcomes -- which sit on three different scales -- are
directly comparable inside one family maximum.
"""

from __future__ import annotations

import csv
import math
import os
import random

# ---------------------------------------------------------------------------
# Declared analysis constants, fixed in advance of looking at any result.
# ---------------------------------------------------------------------------

DATA_FILE = "panel_data.csv"

GROUP_COLUMN = "group"
GROUP_REFERENCE = "current"          # current formulation
GROUP_COMPARISON = "reformulation"   # reformulated enzyme treatment

# The five declared outcomes, in the declared sensory-plan order. This order is
# the order of the family and the order of the printed results.
OUTCOMES = [
    ("overall_liking", "Overall liking", "9-point hedonic (1-9)"),
    ("sweetness", "Sweetness intensity", "line scale (0-100)"),
    ("thickness", "Thickness in the mouth", "line scale (0-100)"),
    ("cereal_off_note", "Cereal off-note intensity", "line scale (0-100)"),
    ("purchase_intent", "Purchase intent", "7-point scale (1-7)"),
]

N_SHUFFLES = 5000   # number of label shuffles, fixed in advance
RANDOM_SEED = 20260826
ALPHA = 0.05        # conventional five percent level


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_panel_data(path):
    """Read the panel table. Returns (labels, values).

    ``labels`` is the formulation label of each panellist, in file order.
    ``values`` maps each declared outcome name to that outcome's ratings, in
    the same panellist order, so a panellist's five ratings stay tied together
    by their shared position.
    """
    labels = []
    values = {name: [] for name, _, _ in OUTCOMES}

    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = [c for c in [GROUP_COLUMN] + list(values) if c not in reader.fieldnames]
        if missing:
            raise ValueError("data file is missing declared column(s): %s" % ", ".join(missing))

        for row_number, row in enumerate(reader, start=2):
            label = row[GROUP_COLUMN].strip()
            if label not in (GROUP_REFERENCE, GROUP_COMPARISON):
                raise ValueError(
                    "row %d: unexpected value in '%s': %r" % (row_number, GROUP_COLUMN, label)
                )
            labels.append(label)
            for name, _, _ in OUTCOMES:
                cell = row[name].strip()
                if cell == "":
                    raise ValueError("row %d: blank value in declared outcome '%s'" % (row_number, name))
                values[name].append(float(cell))

    if not labels:
        raise ValueError("data file contains no panellist rows")
    return labels, values


# ---------------------------------------------------------------------------
# Test statistic
# ---------------------------------------------------------------------------

def mean(xs):
    return sum(xs) / len(xs)


def variance(xs):
    """Sample variance with the usual n-1 denominator."""
    if len(xs) < 2:
        raise ValueError("need at least two observations to compute a variance")
    m = mean(xs)
    return sum((x - m) ** 2 for x in xs) / (len(xs) - 1)


def welch_t(group_a, group_b):
    """Welch's two-sample t statistic for group_b minus group_a.

    Sign convention: positive means the comparison group (reformulation) sits
    above the reference group (current formulation).
    """
    n_a, n_b = len(group_a), len(group_b)
    se_squared = variance(group_a) / n_a + variance(group_b) / n_b
    if se_squared <= 0.0:
        # No spread in either group: no evidence of a shift, statistic is zero.
        return 0.0
    return (mean(group_b) - mean(group_a)) / math.sqrt(se_squared)


def statistic_for_outcome(outcome_values, labels):
    """Welch t for one outcome, given a (possibly shuffled) label vector."""
    ref, comp = [], []
    for value, label in zip(outcome_values, labels):
        if label == GROUP_REFERENCE:
            ref.append(value)
        else:
            comp.append(value)
    return welch_t(ref, comp)


# ---------------------------------------------------------------------------
# Max-statistic permutation procedure (implemented by hand)
# ---------------------------------------------------------------------------

def family_maximum_distribution(values, labels, n_shuffles, seed):
    """Build the reference distribution of family maxima.

    For each of ``n_shuffles`` shuffles, the formulation labels are permuted
    across panellists while each panellist keeps their own five ratings. All
    five declared statistics are recomputed and only the single largest
    absolute statistic across the whole family is recorded. The returned list
    therefore holds exactly ``n_shuffles`` numbers, one per shuffle.
    """
    rng = random.Random(seed)
    shuffled_labels = list(labels)
    outcome_names = [name for name, _, _ in OUTCOMES]

    maxima = []
    for _ in range(n_shuffles):
        rng.shuffle(shuffled_labels)
        family_max = 0.0
        for name in outcome_names:
            t = abs(statistic_for_outcome(values[name], shuffled_labels))
            if t > family_max:
                family_max = t
        maxima.append(family_max)
    return maxima


def family_wise_p_value(observed_statistic, maxima):
    """Proportion of shuffles whose family maximum equals or exceeds |observed|.

    This is the family-wise adjusted significance value for one outcome: the
    observed statistic is judged against the whole family's maximum, not
    against its own outcome-specific null.
    """
    observed_absolute = abs(observed_statistic)
    hits = sum(1 for m in maxima if m >= observed_absolute)
    return hits / len(maxima)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    labels, values = load_panel_data(os.path.join(here, DATA_FILE))

    n_reference = sum(1 for label in labels if label == GROUP_REFERENCE)
    n_comparison = len(labels) - n_reference

    # Observed statistics on the real, unshuffled labels.
    observed = {}
    group_means = {}
    for name, _, _ in OUTCOMES:
        observed[name] = statistic_for_outcome(values[name], labels)
        ref = [v for v, l in zip(values[name], labels) if l == GROUP_REFERENCE]
        comp = [v for v, l in zip(values[name], labels) if l == GROUP_COMPARISON]
        group_means[name] = (mean(ref), mean(comp))

    maxima = family_maximum_distribution(values, labels, N_SHUFFLES, RANDOM_SEED)

    adjusted = {name: family_wise_p_value(observed[name], maxima) for name, _, _ in OUTCOMES}

    # --- output -----------------------------------------------------------
    print("Oat drink sensory panel: current formulation vs reformulation")
    print("=" * 78)
    print("Panellists (the unit of the study): %d" % len(labels))
    print("  %-14s n = %d" % (GROUP_REFERENCE, n_reference))
    print("  %-14s n = %d" % (GROUP_COMPARISON, n_comparison))
    print()
    print("Declared outcome family: %d outcomes, tested together as one family."
          % len(OUTCOMES))
    print("Test statistic: Welch's two-sample t (reformulation minus current).")
    print("Multiplicity control: label-shuffling max-statistic permutation,")
    print("  number of shuffles fixed in advance = %d" % N_SHUFFLES)
    print("  random seed = %d (the run reproduces exactly)" % RANDOM_SEED)
    print("  reference distribution = %d family maxima (one per shuffle)" % len(maxima))
    print("  significance level = %.2f, family-wise across all %d declared outcomes"
          % (ALPHA, len(OUTCOMES)))
    print()

    header = "%-4s %-24s %10s %10s %10s %10s  %s" % (
        "#", "Outcome", "current", "reform.", "Welch t", "FWE p", "Verdict",
    )
    print(header)
    print("-" * len(header))
    for index, (name, label, scale) in enumerate(OUTCOMES, start=1):
        ref_mean, comp_mean = group_means[name]
        p_adjusted = adjusted[name]
        verdict = "significant" if p_adjusted < ALPHA else "not significant"
        print("%-4d %-24s %10.2f %10.2f %10.3f %10.4f  %s" % (
            index, label, ref_mean, comp_mean, observed[name], p_adjusted, verdict,
        ))
    print("-" * len(header))
    print("Means are on each outcome's own scale, in the declared order:")
    for index, (name, label, scale) in enumerate(OUTCOMES, start=1):
        print("  %d. %-24s %s" % (index, label, scale))
    print()
    print("FWE p is the proportion of the %d shuffled family maxima that equal or"
          % N_SHUFFLES)
    print("exceed the outcome's observed |Welch t|. It is already adjusted for all")
    print("%d declared outcomes, so it is read directly against %.2f with no further"
          % (len(OUTCOMES), ALPHA))
    print("correction.")
    print()
    sorted_maxima = sorted(maxima)
    critical = sorted_maxima[int(math.ceil((1.0 - ALPHA) * len(sorted_maxima))) - 1]
    print("Family-maximum reference distribution: min %.3f, median %.3f, max %.3f."
          % (sorted_maxima[0], sorted_maxima[len(sorted_maxima) // 2], sorted_maxima[-1]))
    print("Its %.0f%% point is %.3f, the family-wise critical value for |Welch t|."
          % ((1.0 - ALPHA) * 100, critical))

    n_significant = sum(1 for name, _, _ in OUTCOMES if adjusted[name] < ALPHA)
    print()
    print("Declared outcomes reaching family-wise significance: %d of %d."
          % (n_significant, len(OUTCOMES)))


if __name__ == "__main__":
    main()
