"""Named source fixtures for the MT 3.0 prototype sweep."""

from __future__ import annotations

from dataclasses import dataclass

from harness import CaseRef, Outcome, all_cases, reference_case


@dataclass(frozen=True)
class Fixture:
    name: str
    case: CaseRef
    source: str
    expected: Outcome
    correct_analysis: bool


def _replace(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"fixture anchor is not unique: {old[:70]!r}")
    return source.replace(old, new)


def _fixture(
    name: str,
    case: CaseRef,
    source: str,
    expected: Outcome,
    *,
    correct: bool = True,
) -> Fixture:
    return Fixture(name, case, source, expected, correct)


def _corpus(spec: str) -> CaseRef:
    matches = [case for case in all_cases() if case.envelope is None and case.role == spec]
    if len(matches) != 1:
        raise ValueError(f"corpus case {spec} is not unique")
    return matches[0]


def _d14_fixtures() -> list[Fixture]:
    case = reference_case("E14", "P3")
    source = case.source_path.read_text(encoding="utf-8")
    old = """        "mean_uncoated": u.mean(),
        "mean_hydrophilic": h.mean(),
        "difference": h.mean() - u.mean(),
        "p_value": ttest_ind(u, h, equal_var=False).pvalue,
    }
    for outcome in OUTCOMES
    for u, h in [(uncoated[outcome], hydrophilic[outcome])]
}"""
    direct = """        "mean_uncoated": uncoated[outcome].mean(),
        "mean_hydrophilic": hydrophilic[outcome].mean(),
        "difference": hydrophilic[outcome].mean() - uncoated[outcome].mean(),
        "p_value": ttest_ind(
            uncoated[outcome], hydrophilic[outcome], equal_var=False
        ).pvalue,
    }
    for outcome in OUTCOMES
}"""
    source = _replace(source, old, direct)
    source = _replace(
        source,
        """        direction = "lower" if result["difference"] < 0 else "higher"
        print(f"- {OUTCOME_LABELS[outcome]}: the coating significantly affects "
              f"this outcome (p = {result['p_value']:.4f}); the coated coupons "
              f"are {direction} than the uncoated coupons.")""",
        """        print(f"- {OUTCOME_LABELS[outcome]}: the coating significantly affects "
              f"this outcome (p = {result['p_value']:.4f}).")""",
    )
    source = _replace(
        source,
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
    eligible = _replace(
        source,
        """        "mean_uncoated": uncoated[outcome].mean(),
        "mean_hydrophilic": hydrophilic[outcome].mean(),
        "difference": hydrophilic[outcome].mean() - uncoated[outcome].mean(),
        "p_value": ttest_ind(
            uncoated[outcome], hydrophilic[outcome], equal_var=False
        ).pvalue,
    }
    for outcome in OUTCOMES
}""",
        """        "mean_uncoated": u.mean(),
        "mean_hydrophilic": h.mean(),
        "difference": h.mean() - u.mean(),
        "p_value": min(1.0, ttest_ind(u, h, equal_var=False).pvalue * 4),
    }
    for outcome in OUTCOMES
    for u, h in [(uncoated[outcome], hydrophilic[outcome])]
}""",
    )
    complete = Outcome("covered", "complete", (0, 1, 2, 3), 4)
    unresolved = Outcome("abstain", "test-battery-cardinality-unresolved")
    variants = [
        ("correct-d14-a-whole-family-hand-bonferroni", eligible, complete),
        (
            "correct-d14-a-call-component-refused",
            eligible.replace(
                "[(uncoated[outcome], hydrophilic[outcome])]",
                "[(identity(uncoated[outcome]), hydrophilic[outcome])]",
            ).replace(
                "coupons = pd.read_csv(CSV_PATH)",
                "def identity(value):\n    return value\n\n\ncoupons = pd.read_csv(CSV_PATH)",
            ),
            unresolved,
        ),
        (
            "correct-d14-a-two-row-generator-refused",
            eligible.replace(
                "[(uncoated[outcome], hydrophilic[outcome])]",
                "[(uncoated[outcome], hydrophilic[outcome]), "
                "(uncoated[outcome], hydrophilic[outcome])]",
            ),
            unresolved,
        ),
        (
            "correct-d14-a-filtered-generator-refused",
            eligible.replace(
                "for u, h in [(uncoated[outcome], hydrophilic[outcome])]",
                "for u, h in [(uncoated[outcome], hydrophilic[outcome])] if outcome",
            ),
            unresolved,
        ),
        (
            "correct-d14-a-container-kind-mismatch-refused",
            eligible.replace(
                "for u, h in [(uncoated[outcome], hydrophilic[outcome])]",
                "for [u, h] in [(uncoated[outcome], hydrophilic[outcome])]",
            ),
            unresolved,
        ),
        (
            "correct-d14-a-arithmetic-component-refused",
            eligible.replace(
                "[(uncoated[outcome], hydrophilic[outcome])]",
                "[(uncoated[outcome] + 0, hydrophilic[outcome])]",
            ),
            unresolved,
        ),
    ]
    return [_fixture(name, case, text, expected) for name, text, expected in variants]


def _record_sources() -> list[Fixture]:
    case = reference_case("E14", "P2")
    base = case.source_path.read_text(encoding="utf-8")
    append = "        results.append((label, result))"
    post = """    for label, result in results:
        state = "SIGNIFICANT" if result["significant"] else "NOT SIGNIFICANT"
        print(f"  {label}: p = {result['p_value']:.4f} -> {state}")"""
    mutation = Outcome("abstain", "record-family-mutation-unresolved")
    lineage = Outcome("abstain", "record-family-lineage-unresolved")
    rows = [
        _fixture(
            "correct-record-raw-adjusted-field-merge",
            case,
            base.replace(
                append,
                '        result["adjusted"] = adjust_elsewhere(result["p_value"])\n' + append,
            ),
            lineage,
        ),
        _fixture(
            "correct-record-flag-polarity-inverted",
            case,
            base.replace('if result["significant"]', 'if not result["significant"]'),
            Outcome("abstain", "record-decision-polarity-unresolved"),
        ),
        _fixture(
            "correct-record-conditional-construction",
            case,
            base.replace(append, "        if validate_record(result):\n    " + append),
            mutation,
        ),
        _fixture(
            "correct-record-loop-carried-store",
            case,
            base.replace(
                '        result["significant"] = result["p_value"] < ALPHA',
                '        result["significant"] = False\n'
                '        result["significant"] = result["p_value"] < ALPHA',
            ),
            mutation,
        ),
        _fixture(
            "correct-record-alias-mutation",
            case,
            base.replace("    results = []", "    results = []\n    alias = results").replace(
                append, append + '\n        alias.append({"note": label})'
            ),
            mutation,
        ),
        _fixture(
            "correct-record-collection-reassigned",
            case,
            base.replace("    results = []", "    results = []\n    results = list(results)"),
            mutation,
        ),
        _fixture(
            "correct-record-heterogeneous-schema",
            case,
            base.replace(append, append + '\n        results.append((label, {"other": 1}))'),
            lineage,
        ),
        _fixture(
            "correct-record-two-competing-nested-records",
            case,
            base.replace(
                append, '        results.append((label, result, {"p": result["p_value"]}))'
            ),
            lineage,
        ),
        _fixture(
            "correct-record-opaque-cross-function-return",
            case,
            base.replace(
                "    results = []",
                "    results = []\n    opaque(results)",
            ),
            mutation,
        ),
        _fixture(
            "correct-record-duplicate-raw-vs-adjusted-emissions",
            case,
            base.replace(post, post + '\n        print(result["p_value"] < adjusted_cutoff())'),
            Outcome("abstain", "record-duplicate-conclusion-ambiguous"),
        ),
    ]
    candidate = Outcome("candidate", "none", (), 6)
    positives = [
        _fixture("positive-record-dict-flag-fold", case, base, candidate, correct=False),
        _fixture(
            "positive-record-tuple-wrapper-duplicate-emission",
            case,
            base,
            candidate,
            correct=False,
        ),
        _fixture(
            "positive-record-r4-raw-family",
            _corpus("spec-15"),
            _corpus("spec-15").source_path.read_text(encoding="utf-8"),
            candidate,
            correct=False,
        ),
    ]
    return [*rows, *positives]


def _subset_fixtures() -> list[Fixture]:
    case = reference_case("E14", "P5")
    base = case.source_path.read_text(encoding="utf-8")
    unresolved = Outcome("abstain", "record-subset-position-unresolved")
    rows = [
        _fixture(
            "correct-record-subset-off-by-one",
            case,
            base.replace("results[:N_PRIMARY]", "results[:N_PRIMARY + 1]", 1),
            unresolved,
        ),
        _fixture(
            "correct-record-subset-negative-bound",
            case,
            base.replace("results[:N_PRIMARY]", "results[-N_PRIMARY:]", 1),
            unresolved,
        ),
        _fixture(
            "correct-record-subset-nonunit-step",
            case,
            base.replace("results[:N_PRIMARY]", "results[:N_PRIMARY:2]", 1),
            unresolved,
        ),
        _fixture(
            "correct-record-subset-dynamic-bound",
            case,
            base.replace("results[:N_PRIMARY]", "results[:choose_n()]", 1),
            unresolved,
        ),
        _fixture(
            "correct-record-subset-pderived-filter",
            case,
            base.replace(
                "results[:N_PRIMARY]",
                '[item for item in results if item["p_raw"] < ALPHA][:N_PRIMARY]',
                1,
            ),
            Outcome("abstain", "hierarchical-gatekeeping-present"),
        ),
        _fixture(
            "correct-record-subset-correction-position-mismatch",
            reference_case("E12", "P5"),
            reference_case("E12", "P5")
            .source_path.read_text(encoding="utf-8")
            .replace(
                '[row["p_raw"] for row in primary]',
                '[row["p_raw"] for row in results[:1]]',
            ),
            Outcome("abstain", "correction-family-lineage-unresolved"),
        ),
    ]
    positives = [
        _fixture(
            "positive-record-prefix-holm-strict-subset",
            case,
            base,
            Outcome("candidate", "strict_subset", (0, 1), 6),
            correct=False,
        ),
        _fixture(
            "positive-record-static-flag-holm-strict-subset",
            reference_case("E12", "P5"),
            reference_case("E12", "P5").source_path.read_text(encoding="utf-8"),
            Outcome("candidate", "strict_subset", (0, 1), 7),
            correct=False,
        ),
    ]
    return [*rows, *positives]


def _mixed_fixtures() -> list[Fixture]:
    raw_case = reference_case("E14", "P4")
    raw = raw_case.source_path.read_text(encoding="utf-8")
    subset_case = reference_case("E14", "P5")
    subset = subset_case.source_path.read_text(encoding="utf-8")
    refusal = Outcome("abstain", "family-test-api-dispatch-unresolved")
    rows = [
        _fixture(
            "correct-mixed-api-complete-holm",
            subset_case,
            subset.replace("N_PRIMARY = 2", "N_PRIMARY = 6"),
            Outcome("covered", "complete", (0, 1, 2, 3, 4, 5), 6),
        ),
        _fixture(
            "correct-mixed-api-unregistered-arm",
            raw_case,
            raw.replace("stats.mannwhitneyu(", "stats.kruskal("),
            refusal,
        ),
        _fixture(
            "correct-mixed-api-dynamic-selector",
            raw_case,
            raw.replace('test == "welch"', "test == choose_test()"),
            refusal,
        ),
        _fixture(
            "correct-mixed-api-double-test-one-position",
            raw_case,
            raw.replace(
                '            test_name = "Welch t-test"',
                "            stats.mannwhitneyu(values_a, values_b)\n"
                '            test_name = "Welch t-test"',
            ),
            Outcome("abstain", "multiple-registered-tests-for-family-member"),
        ),
        _fixture(
            "correct-mixed-api-operand-mismatch",
            raw_case,
            raw.replace(
                'values_a, values_b, alternative="two-sided"',
                'values_a, values_a, alternative="two-sided"',
            ),
            Outcome("abstain", "test-operand-lineage-unresolved"),
        ),
        _fixture(
            "correct-mixed-api-live-scientific-gate",
            raw_case,
            raw.replace(
                "        mean_a = values_a.mean()",
                "        if p_value < 0.01:\n            continue\n\n        mean_a = values_a.mean()",
            ),
            Outcome("abstain", "hierarchical-gatekeeping-present"),
        ),
        _fixture(
            "correct-mixed-api-alias-rebound",
            raw_case,
            raw.replace("def compare_outcomes", "stats = shadow_stats\n\n\ndef compare_outcomes"),
            Outcome("abstain", "api-resolution-ambiguous"),
        ),
    ]
    positives = [
        _fixture(
            "positive-mixed-api-raw-family",
            raw_case,
            raw,
            Outcome("candidate", "none", (), 7),
            correct=False,
        ),
        _fixture(
            "positive-mixed-api-prefix-holm",
            subset_case,
            subset,
            Outcome("candidate", "strict_subset", (0, 1), 6),
            correct=False,
        ),
    ]
    return [*rows, *positives]


def _dataframe_fixtures() -> list[Fixture]:
    complete_case = reference_case("E12", "N1")
    complete = complete_case.source_path.read_text(encoding="utf-8")
    sidak_case = reference_case("E12", "N2")
    sidak = sidak_case.source_path.read_text(encoding="utf-8")
    raw_case = reference_case("E12", "P1")
    raw = raw_case.source_path.read_text(encoding="utf-8")
    table_reason = Outcome("abstain", "dataframe-pvalue-table-unresolved")
    rows = [
        _fixture(
            "correct-dataframe-whole-family-default-multipletests",
            complete_case,
            complete,
            Outcome("covered", "complete", (0, 1, 2, 3, 4), 5),
        ),
        _fixture(
            "correct-dataframe-hand-sidak",
            sidak_case,
            sidak,
            Outcome("abstain", "unresolved-decision-threshold"),
        ),
        _fixture(
            "correct-dataframe-live-panel-gate",
            raw_case,
            raw.replace(
                "summary = pd.DataFrame(",
                "if min(mpt_p, jitter_p, sff_p, vfi_p, dryness_p) < 0.01:\n"
                "    raise RuntimeError('panel gate')\n\nsummary = pd.DataFrame(",
            ),
            Outcome("abstain", "hierarchical-gatekeeping-present"),
        ),
        _fixture(
            "correct-dataframe-alias-escape",
            raw_case,
            raw.replace(
                'print(summary.to_string(index=False, float_format=lambda v: f"{v:.4f}"))',
                'consume(summary)\nprint(summary.to_string(index=False, float_format=lambda v: f"{v:.4f}"))',
            ),
            table_reason,
        ),
        _fixture(
            "correct-dataframe-row-sort",
            raw_case,
            raw.replace(
                "summary = summary.drop",
                'summary = summary.sort_values("p_value")\nsummary = summary.drop',
            ),
            table_reason,
        ),
        _fixture(
            "correct-dataframe-dynamic-loc-store",
            raw_case,
            raw.replace(
                'summary["conclusion"] = [verdict(p) for p in summary["p_value"]]',
                'summary.loc[summary["p_value"] < ALPHA, "conclusion"] = "significant"',
            ),
            table_reason,
        ),
        _fixture(
            "correct-dataframe-raw-adjusted-column-merge",
            complete_case,
            complete.replace(
                'results["p_adjusted"] = p_adjusted',
                'results["p_adjusted"] = p_adjusted\n'
                '    results["p_used"] = results["p_adjusted"].where('
                'results["p_raw"] < 0.05, results["p_raw"])',
            ),
            table_reason,
        ),
        _fixture(
            "correct-dataframe-export-sibling",
            raw_case,
            raw.replace(
                'print(summary.to_string(index=False, float_format=lambda v: f"{v:.4f}"))',
                'summary.to_csv("p.csv")\nprint(summary.to_string(index=False, float_format=lambda v: f"{v:.4f}"))',
            ),
            Outcome("abstain", "unresolved-pvalue-consumer"),
        ),
        _fixture(
            "correct-dataframe-isna-helper-hidden-correction",
            raw_case,
            raw.replace(
                "def verdict(p_value):",
                "def verdict(p_value):\n    p_value = hidden_adjust(p_value)",
            ),
            Outcome("abstain", "unresolved-pvalue-consumer"),
        ),
        _fixture(
            "correct-dataframe-format-lambda-arithmetic",
            raw_case,
            raw.replace('lambda v: f"{v:.4f}"', 'lambda v: f"{v * 100:.4f}"'),
            table_reason,
        ),
    ]
    positives = [
        _fixture(
            "positive-dataframe-raw-family",
            raw_case,
            raw,
            Outcome("candidate", "none", (), 5),
            correct=False,
        ),
        _fixture(
            "positive-dataframe-prefix-holm",
            reference_case("E11", "P5"),
            reference_case("E11", "P5").source_path.read_text(encoding="utf-8"),
            Outcome("candidate", "strict_subset", (0, 1), 7),
            correct=False,
        ),
    ]
    return [*rows, *positives]


def fixtures() -> tuple[Fixture, ...]:
    result = (
        *_d14_fixtures(),
        *_record_sources(),
        *_subset_fixtures(),
        *_mixed_fixtures(),
        *_dataframe_fixtures(),
    )
    if len(result) != 48 or len({item.name for item in result}) != 48:
        raise ValueError("fixture catalog must contain 39 correct and nine positive unique rows")
    if sum(item.correct_analysis for item in result) != 39:
        raise ValueError("fixture catalog must contain exactly 39 correct fixtures")
    return result
