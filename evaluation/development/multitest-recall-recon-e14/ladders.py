"""Executed one-construct ladders from the five sealed E14 misses."""

from __future__ import annotations

import hashlib
import json

from h import E14, adapter_envelope


def _replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"ladder replacement expected exactly once: {old[:70]!r}")
    return source.replace(old, new)


def p2_rungs() -> list[tuple[str, str, str]]:
    source = (E14 / "4fc0f5c1ef2d0e2cd5b6/project/analysis.py").read_text(encoding="utf-8")
    report = """    print()
    print("Verdicts by outcome (p < 0.05 means bedding significantly "
          "affected the outcome):")
    for label, result in results:
        state = "SIGNIFICANT" if result["significant"] else "NOT SIGNIFICANT"
        print(f"  {label}: p = {result['p_value']:.4f} -> {state}")
"""
    no_second_report = _replace_once(source, report, "")
    no_collection = _replace_once(
        no_second_report,
        "        results.append((label, result))\n",
        "",
    )
    return [
        ("P2-r0-real", "sealed source", source),
        (
            "P2-r1-no-second-report",
            "delete only the second pass over the result collection",
            no_second_report,
        ),
        (
            "P2-r2-no-family-collection",
            "delete only the now-unused family-container insertion",
            no_collection,
        ),
    ]


def p3_rungs() -> list[tuple[str, str, str]]:
    source = (E14 / "502687d9137dab93ff99/project/analysis.py").read_text(encoding="utf-8")
    old = """        "mean_uncoated": u.mean(),
        "mean_hydrophilic": h.mean(),
        "difference": h.mean() - u.mean(),
        "p_value": ttest_ind(u, h, equal_var=False).pvalue,
    }
    for outcome in OUTCOMES
    for u, h in [(uncoated[outcome], hydrophilic[outcome])]
}"""
    new = """        "mean_uncoated": uncoated[outcome].mean(),
        "mean_hydrophilic": hydrophilic[outcome].mean(),
        "difference": hydrophilic[outcome].mean() - uncoated[outcome].mean(),
        "p_value": ttest_ind(
            uncoated[outcome], hydrophilic[outcome], equal_var=False
        ).pvalue,
    }
    for outcome in OUTCOMES
}"""
    single_generator = _replace_once(source, old, new)
    no_direction_control = _replace_once(
        single_generator,
        """        direction = "lower" if result["difference"] < 0 else "higher"
        print(f"- {OUTCOME_LABELS[outcome]}: the coating significantly affects "
              f"this outcome (p = {result['p_value']:.4f}); the coated coupons "
              f"are {direction} than the uncoated coupons.")""",
        """        print(f"- {OUTCOME_LABELS[outcome]}: the coating significantly affects "
              f"this outcome (p = {result['p_value']:.4f}).")""",
    )
    assigned_verdict = _replace_once(
        no_direction_control,
        """    if result["p_value"] < ALPHA:
        print(f"- {OUTCOME_LABELS[outcome]}: the coating significantly affects "
              f"this outcome (p = {result['p_value']:.4f}).")
    else:
        print(f"- {OUTCOME_LABELS[outcome]}: the coating does not significantly "
              f"affect this outcome (p = {result['p_value']:.4f}).")""",
        """    if result["p_value"] < ALPHA:
        conclusion = "significantly affects"
    else:
        conclusion = "does not significantly affect"
    print(f"- {OUTCOME_LABELS[outcome]}: the coating {conclusion} "
          f"this outcome (p = {result['p_value']:.4f}).")""",
    )
    return [
        ("P3-r0-real", "sealed source", source),
        (
            "P3-r1-inline-singleton-binding-generator",
            "inline only the singleton binding generator",
            single_generator,
        ),
        (
            "P3-r2-delete-non-p-direction-control",
            "delete only the direction ternary whose record-field origin is conservatively joined",
            no_direction_control,
        ),
        (
            "P3-r3-single-emission-control",
            "refactor only the two print branches to the already-admitted assigned-verdict form",
            assigned_verdict,
        ),
    ]


def _uniform_p4(source: str) -> str:
    old = """        if test == "welch":
            test_name = "Welch t-test"
            p_value = stats.ttest_ind(values_a, values_b, equal_var=False).pvalue
        elif test == "mann-whitney":
            test_name = "Mann-Whitney U"
            p_value = stats.mannwhitneyu(
                values_a, values_b, alternative="two-sided"
            ).pvalue
        else:
            raise ValueError("Unknown test for outcome " + column)
"""
    new = """        test_name = "Welch t-test"
        p_value = stats.ttest_ind(values_a, values_b, equal_var=False).pvalue
"""
    return _replace_once(source, old, new)


def p4_rungs() -> list[tuple[str, str, str]]:
    source = (E14 / "cccde3c60f936e077f80/project/analysis.py").read_text(encoding="utf-8")
    selector_uniform = _replace_once(
        source,
        '("faecal_egg_count_epg", "Faecal strongyle egg count (epg)", "mann-whitney")',
        '("faecal_egg_count_epg", "Faecal strongyle egg count (epg)", "welch")',
    )
    direct_uniform = _uniform_p4(selector_uniform)
    return [
        ("P4-r0-real", "sealed source", source),
        (
            "P4-r1-uniform-selector-values",
            "change only the one non-Welch table selector",
            selector_uniform,
        ),
        (
            "P4-r2-direct-uniform-test-call",
            "replace only the now-dead API-dispatch branch by its selected call",
            direct_uniform,
        ),
    ]


def _uniform_p5(source: str) -> str:
    old = """    if test == "welch":
        # Continuous outcome, groups not assumed to share a variance.
        statistic, p_value = stats.ttest_ind(a, b, equal_var=False)
        test_name = "Welch t-test"
    elif test == "mwu":
        # Small bounded count outcome, so a rank-based test is used instead.
        statistic, p_value = stats.mannwhitneyu(a, b, alternative="two-sided")
        test_name = "Mann-Whitney U"
    else:
        raise ValueError("unknown test: %r" % test)
"""
    new = """    statistic, p_value = stats.ttest_ind(a, b, equal_var=False)
    test_name = "Welch t-test"
"""
    return _replace_once(source, old, new)


def p5_rungs() -> list[tuple[str, str, str]]:
    source = (E14 / "5e33841b96d85ffe67be/project/analysis.py").read_text(encoding="utf-8")
    selector_uniform = _replace_once(
        source,
        '("vomiting_episodes_24h", "Vomiting episodes, 0-24 h", "count", "mwu")',
        '("vomiting_episodes_24h", "Vomiting episodes, 0-24 h", "count", "welch")',
    )
    direct_uniform = _uniform_p5(selector_uniform)
    return [
        ("P5-r0-real", "sealed source", source),
        (
            "P5-r1-uniform-selector-values",
            "change only the one non-Welch table selector",
            selector_uniform,
        ),
        (
            "P5-r2-direct-uniform-test-call",
            "replace only the now-dead API-dispatch branch by its selected call",
            direct_uniform,
        ),
    ]


def p6_rungs() -> list[tuple[str, str, str]]:
    source = (E14 / "94786af7eca95fff6d78/project/analysis.py").read_text(encoding="utf-8")
    full_factor = _replace_once(
        source,
        "    n_comparisons = len(CORRECTED_OUTCOMES)",
        "    n_comparisons = len(OUTCOMES)",
    )
    subset_list = """CORRECTED_OUTCOMES = [
    "borg_exertion",
    "neck_shoulder_vas_mm",
    "wrist_hand_vas_mm",
    "mean_heart_rate_bpm",
]"""
    subset_set = """CORRECTED_OUTCOMES = {
    "borg_exertion",
    "neck_shoulder_vas_mm",
    "wrist_hand_vas_mm",
    "mean_heart_rate_bpm",
}"""
    no_set_iteration = _replace_once(
        full_factor,
        '''        f"Hand correction applied to the headline outcomes "
        f"({', '.join(CORRECTED_OUTCOMES)}): "
        f"p x {n_comparisons}, capped at 1.0."''',
        '''        f"Hand correction applied to four headline outcomes: "
        f"p x {n_comparisons}, capped at 1.0."''',
    )
    membership_set = _replace_once(no_set_iteration, subset_list, subset_set)
    complete_set = _replace_once(
        membership_set,
        subset_set,
        """CORRECTED_OUTCOMES = {
    "borg_exertion",
    "neck_shoulder_vas_mm",
    "wrist_hand_vas_mm",
    "rooms_per_shift",
    "mean_heart_rate_bpm",
    "trunk_flexion_over60_pct",
    "step_count",
    "recovery_need_score",
}""",
    )
    return [
        ("P6-r0-real", "sealed source", source),
        (
            "P6-r1-full-family-factor-control",
            "change only the manual factor from subset size 4 to full family size 8",
            full_factor,
        ),
        (
            "P6-r2-membership-only-container",
            "remove only the membership container's presentation iteration",
            no_set_iteration,
        ),
        (
            "P6-r3-set-membership-oracle",
            "change only the corrected-membership List to Set",
            membership_set,
        ),
        (
            "P6-r4-complete-family-control",
            "add only the four previously uncorrected members to the correction set",
            complete_set,
        ),
    ]


def execute() -> dict[str, object]:
    output: dict[str, object] = {"adapter_version": "2.3.0", "ladders": {}}
    specs = (
        ("P2", "4fc0f5c1ef2d0e2cd5b6", p2_rungs),
        ("P3", "502687d9137dab93ff99", p3_rungs),
        ("P4", "cccde3c60f936e077f80", p4_rungs),
        ("P5", "5e33841b96d85ffe67be", p5_rungs),
        ("P6", "94786af7eca95fff6d78", p6_rungs),
    )
    for role, case_id, factory in specs:
        rows = []
        for rung, mutation, source in factory():
            observed = adapter_envelope(E14 / case_id, source.encode("utf-8"))
            rows.append(
                {
                    "rung": rung,
                    "mutation": mutation,
                    "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
                    **observed,
                }
            )
        output["ladders"][role] = rows  # type: ignore[index]
    return output


if __name__ == "__main__":
    print(json.dumps(execute(), indent=2, sort_keys=True))
