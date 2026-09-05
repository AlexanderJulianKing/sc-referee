"""Fixture sources for the strict MT 3.2 AP(C, POS) prototype sweep."""

from __future__ import annotations

import hashlib
import json
import runpy
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from harness import REPO, Outcome, reference_case

ROOT = Path(__file__).resolve().parent
V3_SWEEP = REPO / "evaluation/development/multitest-code-slice-v3_0/prototype-sweep"
V3_MATRIX = REPO / "evaluation/development/multitest-code-slice-v3/FIXTURE_MATRIX.json"
V31_ROOT = REPO / "evaluation/development/multitest-code-slice-v3_1"


@dataclass(frozen=True)
class Fixture:
    name: str
    case_key: str
    source: bytes
    baseline: Outcome
    expected: Outcome | None
    correct_analysis: bool
    category: str
    design_clause: str
    source_origin: str
    expected_gate: str | None = None
    expected_gate_reason: str | None = None


def _outcome(value: list[object]) -> Outcome:
    if len(value) == 2:
        return Outcome(str(value[0]), str(value[1]))
    detail = cast(dict[str, object], value[2])
    count = detail.get("authorized_count")
    return Outcome(
        str(value[0]),
        str(value[1]),
        tuple(int(item) for item in cast(list[object], detail["corrected_positions"])),
        None if count is None else int(cast(int, count)),
    )


def _replace_once(source: str, old: str, new: str, name: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"{name}: replacement anchor count is {source.count(old)}")
    return source.replace(old, new)


def cumulative_v3_fixtures() -> tuple[Fixture, ...]:
    """Load the frozen 71-row B1-B5/merge/closure matrix and verify its sources."""

    results = json.loads((V3_SWEEP / "results.json").read_text(encoding="utf-8"))
    fixtures: list[Fixture] = []
    for row in results["fixtures"]:
        source_path = V3_SWEEP / row["source_path"]
        source = source_path.read_bytes()
        if hashlib.sha256(source).hexdigest() != row["source_sha256"]:
            raise ValueError(f"frozen fixture digest mismatch: {row['name']}")
        fixtures.append(
            Fixture(
                row["name"],
                row["case_key"],
                source,
                _outcome(row["outcome"]),
                _outcome(row["outcome"]),
                bool(row["correct_analysis"]),
                "frozen-v3-original",
                "3.0 sections 4.1 and 6.4-6.5",
                source_path.relative_to(REPO).as_posix(),
            )
        )

    namespace = runpy.run_path(
        str(REPO / "tests/test_code_csv_multiple_testing_record_model_v3.py")
    )
    audit_sets = (
        ("_AUDIT_FIX_R1_EXPECTED_ROWS", "_audit_fix_r1_source", "audit-fix-r1"),
        ("_AUDIT_FIX_R2_EXPECTED_ROWS", "_audit_fix_r2_source", "audit-fix-r2"),
        ("_AUDIT_FIX_R3_EXPECTED_ROWS", "_audit_fix_r3_source", "audit-fix-r3"),
    )
    for rows_name, source_name, category in audit_sets:
        rows = cast(list[dict[str, Any]], namespace[rows_name])
        source_for = cast(Callable[[str], tuple[str, bytes]], namespace[source_name])
        for row in rows:
            if row["expected_outcome"] != "abstain":
                # The R3 bare-transport positive is already one of the original 48 rows.
                continue
            case_key, source = source_for(row["fixture_name"])
            if "sha256:" + hashlib.sha256(source).hexdigest() != row["fixture_source_sha256"]:
                raise ValueError(f"frozen audit fixture digest mismatch: {row['fixture_name']}")
            fixtures.append(
                Fixture(
                    row["fixture_name"],
                    case_key,
                    source,
                    Outcome("abstain", row["expected_reason"]),
                    Outcome("abstain", row["expected_reason"]),
                    True,
                    category,
                    row["derivation"]["design_clause"],
                    row["derivation"]["audit_probe_shape"],
                )
            )
    matrix = json.loads(V3_MATRIX.read_text(encoding="utf-8"))
    if len(fixtures) != 71 or [item.name for item in fixtures] != matrix["fixture_names"]:
        raise ValueError("the cumulative v3 fixture population is not the frozen 71-row matrix")
    if sum(item.correct_analysis for item in fixtures) != 62:
        raise ValueError("the cumulative v3 correct-fixture count is not 62")
    return tuple(fixtures)


def laundering_adjacent_fixtures() -> tuple[Fixture, ...]:
    """Load the 16 independent 3.1 correction-witness/laundering controls."""

    matrix = json.loads((V31_ROOT / "FIXTURE_MATRIX.json").read_text(encoding="utf-8"))
    result: list[Fixture] = []
    for row in matrix["rows"]:
        source_path = (V31_ROOT / row["source_path"]).resolve()
        source = source_path.read_bytes()
        if "sha256:" + hashlib.sha256(source).hexdigest() != row["source_sha256"]:
            raise ValueError(f"v3.1 fixture digest mismatch: {row['name']}")
        result.append(
            Fixture(
                f"v31-{row['name']}",
                "E12:N1:45c4b9a19d0a630f1cb0",
                source,
                Outcome("abstain", row["reason"]),
                Outcome("abstain", row["reason"]),
                True,
                "v3.1-laundering-adjacent",
                str(row["design_clause"]),
                source_path.relative_to(REPO).as_posix(),
            )
        )
    if len(result) != 16:
        raise ValueError("the v3.1 laundering-adjacent population is not 16")
    return tuple(result)


def b5_expression_variants() -> tuple[Fixture, ...]:
    """Re-execute the cumulative seven-field by nine-expression B5 probe grid."""

    namespace = runpy.run_path(
        str(REPO / "tests/test_code_csv_multiple_testing_record_model_v3.py")
    )
    source_for = cast(
        Callable[[str, tuple[dict[str, str], ...]], tuple[str, bytes]],
        namespace["_audit_fixture_source"],
    )
    fields = (
        "p_adj",
        "p_adjusted",
        "p_corrected",
        "p_bonferroni",
        "p_used",
        "adjusted_p",
        "p",
    )
    expressions = (
        'min(1.0, result["p_value"] * len(OUTCOMES))',
        'result["p_value"] * 6',
        'result["p_value"] * len(OUTCOMES)',
        'len(OUTCOMES) * result["p_value"]',
        'result["p_value"] / (1 / len(OUTCOMES))',
        'result["p_value"] + result["p_value"]',
        'max(result["p_value"], 0.0)',
        'float(result["p_value"])',
        'round(result["p_value"], 4)',
    )
    result: list[Fixture] = []
    for field_index, field in enumerate(fields):
        for expression_index, expression in enumerate(expressions):
            name = f"correct-b5-field-{field_index + 1}-expression-{expression_index + 1}"
            recipe = (
                {
                    "name": name,
                    "anchor": '        result["significant"] = result["p_value"] < ALPHA\n',
                    "replacement": f'        result["{field}"] = {expression}\n'
                    f'        result["significant"] = result["{field}"] < ALPHA\n',
                },
            )
            case_key, source = source_for(name, recipe)
            result.append(
                Fixture(
                    name,
                    case_key,
                    source,
                    Outcome("abstain", "record-family-lineage-unresolved"),
                    Outcome("abstain", "record-family-lineage-unresolved"),
                    True,
                    "b5-expression-variant",
                    "3.0 section 6.5 cross-function/cross-field refusal",
                    f"field={field}; expression={expression}",
                )
            )
    if len(result) != 63:
        raise ValueError("the cumulative B5 field/expression grid is not 63")
    return tuple(result)


def _e15() -> tuple[str, str]:
    case = reference_case("E15:P6:81980e878c1bc8cc216b")
    return case.key, case.source_path.read_text(encoding="utf-8")


def _record_positive_source(*, subset: bool) -> tuple[str, str]:
    results = json.loads((V3_SWEEP / "results.json").read_text(encoding="utf-8"))
    row = next(
        item for item in results["fixtures"] if item["name"] == "positive-record-dict-flag-fold"
    )
    source = (V3_SWEEP / row["source_path"]).read_text(encoding="utf-8")
    start = source.index("\ndef compare_outcome(")
    end = source.index("\ndef main():", start)
    source = source[:start] + source[end:]
    old = (
        "        result = compare_outcome(straw, shavings, column)\n"
        '        result["significant"] = result["p_value"] < ALPHA\n'
    )
    if subset:
        source = _replace_once(
            source,
            "ALPHA = 0.05\n",
            "ALPHA = 0.05\nCORRECTED_OUTCOMES = [\n"
            '    "body_weight_kg",\n'
            '    "breast_yield_pct",\n'
            "]\n",
            "record-subset-constant",
        )
        fold = (
            "        if column in CORRECTED_OUTCOMES:\n"
            '            result["p_used"] = min(\n'
            '                1.0, result["p_value"] * len(OUTCOMES)\n'
            "            )\n"
            "        else:\n"
            '            result["p_used"] = result["p_value"]\n'
        )
    else:
        fold = (
            '        result["p_used"] = min(\n'
            '            1.0, result["p_value"] * len(OUTCOMES)\n'
            "        )\n"
        )
    new = (
        "        a = straw[column]\n"
        "        b = shavings[column]\n"
        "        test = stats.ttest_ind(a, b, equal_var=False)\n"
        "        result = {\n"
        '            "mean_straw": a.mean(),\n'
        '            "mean_shavings": b.mean(),\n'
        '            "difference": a.mean() - b.mean(),\n'
        '            "p_value": test.pvalue,\n'
        "        }\n" + fold + '        result["significant"] = result["p_used"] < ALPHA\n'
    )
    return row["case_key"], _replace_once(source, old, new, "record-fold")


def _full_primary_source(source: str) -> str:
    start = source.index("PRIMARY_OUTCOMES = [")
    end = source.index("]\n\n# Number of comparisons", start) + 2
    block = (
        "PRIMARY_OUTCOMES = [\n"
        '    "mean_lifespan_d",\n'
        '    "total_brood_size_eggs",\n'
        '    "pumping_rate_pumps_per_min",\n'
        '    "thrashing_rate_bends_per_min",\n'
        '    "body_length_um",\n'
        '    "age_at_first_egg_h",\n'
        '    "defecation_interval_s",\n'
        '    "crawling_speed_um_per_s",\n'
        "]\n"
    )
    return source[:start] + block + source[end:]


def new_ap_fixtures() -> tuple[Fixture, ...]:
    """Return AP-specific positive controls and design-derived refusal attacks."""

    key, base = _e15()
    correction = "p_corrected = min(p_raw * FAMILY_SIZE, 1.0)"
    fixtures: list[Fixture] = []

    def add(
        name: str,
        source: str,
        expected: Outcome | None,
        correct: bool,
        clause: str,
        *,
        expected_gate: str | None = None,
        expected_gate_reason: str | None = None,
    ) -> None:
        fixtures.append(
            Fixture(
                name,
                key,
                source.encode(),
                Outcome("abstain", "unresolved-manual-correction-present"),
                expected,
                correct,
                "ap-v3.2",
                clause,
                "generated from sealed E15 P6",
                expected_gate,
                expected_gate_reason,
            )
        )

    add(
        "positive-ap-subset-capped-family-name",
        base,
        Outcome("candidate", "strict_subset", (0, 1, 3), 8),
        False,
        "4.1 capped product; 5.2 strict subset",
    )
    add(
        "positive-ap-subset-bare-product",
        _replace_once(base, correction, "p_corrected = p_raw * FAMILY_SIZE", "bare-product"),
        Outcome("candidate", "strict_subset", (0, 1, 3), 8),
        False,
        "4.1 bare product",
    )
    add(
        "positive-ap-subset-reversed-product",
        _replace_once(base, correction, "p_corrected = min(FAMILY_SIZE * p_raw, 1.0)", "reverse"),
        Outcome("candidate", "strict_subset", (0, 1, 3), 8),
        False,
        "4.1 commuted product",
    )
    add(
        "positive-ap-subset-literal-factor",
        _replace_once(base, correction, "p_corrected = min(p_raw * 8, 1.0)", "literal"),
        Outcome("candidate", "strict_subset", (0, 1, 3), 8),
        False,
        "4.2 exact integer N",
    )
    numpy_source = _replace_once(
        base, "import pandas as pd\n", "import numpy as np\nimport pandas as pd\n", "numpy-import"
    )
    numpy_source = _replace_once(
        numpy_source,
        correction,
        "p_corrected = np.minimum(p_raw * FAMILY_SIZE, 1.0)",
        "numpy-cap",
    )
    add(
        "positive-ap-subset-numpy-minimum",
        numpy_source,
        Outcome("candidate", "strict_subset", (0, 1, 3), 8),
        False,
        "4.1 numpy.minimum cap",
    )
    add(
        "positive-ap-complete-capped-family-name",
        _full_primary_source(base),
        Outcome("covered", "complete", tuple(range(8)), 8),
        True,
        "5.1 complete AP coverage",
    )

    spec = reference_case("corpus:spec-28")
    division_source = spec.source_path.read_text(encoding="utf-8")
    division_source = _replace_once(
        division_source,
        "\n\nimport pandas as pd\n",
        "\n\n# ruff: noqa: UP031 -- retained as an AST-evidence fixture\n\nimport pandas as pd\n",
        "division-fixture-lint-boundary",
    )
    fixtures.append(
        Fixture(
            "positive-ap-complete-division-threshold",
            spec.key,
            division_source.encode("utf-8"),
            spec.baseline,
            Outcome("covered", "complete", tuple(range(4)), 4),
            True,
            "ap-v3.2",
            "4.3 exact family-alpha division",
            "frozen corpus spec-28",
        )
    )
    threshold_subset = division_source
    threshold_subset = _replace_once(
        threshold_subset,
        "N_OUTCOMES = 4\n",
        'N_OUTCOMES = 4\nCORRECTED = ["dmft_count", "new_lesions"]\n',
        "threshold-subset-table",
    )
    threshold_subset = _replace_once(
        threshold_subset,
        '        decision = "supported" if test.pvalue < PER_OUTCOME_ALPHA else "not supported"\n',
        "        if col in CORRECTED:\n"
        "            decision = (\n"
        '                "supported"\n'
        "                if test.pvalue < FAMILY_ALPHA / N_OUTCOMES\n"
        '                else "not supported"\n'
        "            )\n"
        "        else:\n"
        '            decision = "supported" if test.pvalue < FAMILY_ALPHA else "not supported"\n',
        "threshold-subset-decision",
    )
    fixtures.append(
        Fixture(
            "positive-ap-subset-division-threshold",
            spec.key,
            threshold_subset.encode(),
            spec.baseline,
            Outcome("candidate", "strict_subset", (0, 1), 4),
            False,
            "ap-v3.2",
            "4.3 exact family-alpha division; 5.2 strict subset",
            "generated from frozen corpus spec-28",
        )
    )
    for subset, name, expected in (
        (
            False,
            "positive-ap-record-cross-field-complete",
            Outcome("covered", "complete", tuple(range(6)), 6),
        ),
        (
            True,
            "positive-ap-record-cross-field-subset",
            Outcome("candidate", "strict_subset", (0, 1), 6),
        ),
    ):
        record_key, record_source = _record_positive_source(subset=subset)
        fixtures.append(
            Fixture(
                name,
                record_key,
                record_source.encode(),
                Outcome("abstain", "record-family-lineage-unresolved"),
                expected,
                not subset,
                "ap-v3.2",
                "4.4 exact same-owner cross-field fold",
                "generated from the frozen record positive",
            )
        )

    unrelated = _replace_once(
        base,
        "FAMILY_SIZE = len(OUTCOMES)\n",
        "FAMILY_SIZE = len(OUTCOMES)\nOTHER_TABLE = list(range(8))\n",
        "unrelated-table",
    )
    unrelated = _replace_once(
        unrelated,
        correction,
        "p_corrected = min(p_raw * len(OTHER_TABLE), 1.0)",
        "unrelated-factor",
    )
    add(
        "correct-ap-unrelated-same-length-factor",
        unrelated,
        Outcome("abstain", "unresolved-manual-correction-present"),
        True,
        "4.2 factor must resolve from the contract outcome table",
    )
    alias = _replace_once(
        base,
        "FAMILY_SIZE = len(OUTCOMES)\n",
        "FAMILY_SIZE = len(OUTCOMES)\nFACTOR_ALIAS = FAMILY_SIZE\n",
        "factor-alias",
    )
    alias = _replace_once(
        alias, correction, "p_corrected = min(p_raw * FACTOR_ALIAS, 1.0)", "alias-use"
    )
    add(
        "correct-ap-factor-alias-refused",
        alias,
        Outcome("abstain", "unresolved-manual-correction-present"),
        True,
        "4.2 exact binding form",
    )
    add(
        "correct-ap-computed-factor-refused",
        _replace_once(
            base, correction, "p_corrected = min(p_raw * (4 + 4), 1.0)", "computed-factor"
        ),
        Outcome("abstain", "unresolved-manual-correction-present"),
        True,
        "4.2 no arithmetic factor",
    )
    rebound = _replace_once(
        base,
        "results = []\n",
        "factor = 8\n    factor = FAMILY_SIZE\n    results = []\n",
        "rebound-factor",
    )
    rebound = _replace_once(
        rebound, correction, "p_corrected = min(p_raw * factor, 1.0)", "rebound-use"
    )
    add(
        "correct-ap-factor-rebound-refused",
        rebound,
        Outcome("abstain", "pderived-conclusion-family-incomplete"),
        True,
        "4.2 one binding in the parsed module",
    )
    duplicate = _replace_once(
        base,
        "            p_corrected = min(p_raw * FAMILY_SIZE, 1.0)\n",
        "            p_corrected = min(p_raw * FAMILY_SIZE, 1.0)\n"
        "            p_second = p_raw * FAMILY_SIZE  # noqa: F841 -- second-fold evidence\n",
        "duplicate-fold",
    )
    add(
        "correct-ap-two-correction-folds-refused",
        duplicate,
        Outcome("abstain", "unresolved-manual-correction-present"),
        True,
        "4.4 single reaching correction fold",
    )
    unknown = _replace_once(
        base,
        "def compare_outcomes(control, exposed):\n",
        "def choose_primary(column):\n    return column.startswith('x')\n\n\ndef compare_outcomes(control, exposed):\n",
        "unknown-helper",
    )
    unknown = _replace_once(
        unknown,
        "is_primary = column in PRIMARY_OUTCOMES",
        "is_primary = choose_primary(column)",
        "unknown-selector",
    )
    add(
        "correct-ap-unresolved-position-selector",
        unknown,
        Outcome("abstain", "unresolved-manual-correction-present"),
        True,
        "4.5 exact structural C",
    )
    unresolved = _replace_once(
        base,
        "import pandas as pd\n",
        "import pandas as pd\nimport project_correction_helper\n",
        "unresolved-import",
    )
    unresolved = _replace_once(
        unresolved,
        "            p_used = p_corrected\n",
        "            project_correction_helper.audit(p_corrected)\n"
        "            p_used = p_corrected\n",
        "unresolved-consumer",
    )
    add(
        "correct-ap-unresolved-correction-consumer",
        unresolved,
        Outcome("abstain", "unresolved-manual-correction-present"),
        True,
        "4.6 total forward accounting",
    )
    terminal = _replace_once(
        base,
        "from scipy import stats\n",
        "from scipy import stats\nfrom statsmodels.stats.multitest import multipletests\n",
        "correction-terminal-import",
    )
    terminal = _replace_once(
        terminal,
        "            p_used = p_corrected\n",
        "            multipletests([p_raw])\n            p_used = p_corrected\n",
        "correction-terminal",
    )
    add(
        "correct-ap-correction-terminal-sibling",
        terminal,
        Outcome("abstain", "unresolved-manual-correction-present"),
        True,
        "3 global correction census",
    )

    frozen_record = json.loads((V3_SWEEP / "results.json").read_text(encoding="utf-8"))
    frozen_record_row = next(
        item
        for item in frozen_record["fixtures"]
        if item["name"] == "positive-record-dict-flag-fold"
    )
    cross_function = (V3_SWEEP / frozen_record_row["source_path"]).read_text(encoding="utf-8")
    cross_function = _replace_once(
        cross_function,
        '        result["significant"] = result["p_value"] < ALPHA\n',
        '        result["p_used"] = min(1.0, result["p_value"] * len(OUTCOMES))\n'
        '        result["significant"] = result["p_used"] < ALPHA\n',
        "cross-function-record-fold",
    )
    fixtures.append(
        Fixture(
            "correct-ap-cross-function-record-flow-gate",
            frozen_record_row["case_key"],
            cross_function.encode("utf-8"),
            Outcome("abstain", "record-family-lineage-unresolved"),
            Outcome("abstain", "record-family-lineage-unresolved"),
            True,
            "ap-v3.2",
            "4.6 helper-return records remain cross-function flow",
            "generated from the frozen record positive",
            "cross-function-record-flow",
        )
    )

    merge_source = _replace_once(
        base,
        "        significant = p_used < ALPHA\n",
        "        p_merge = (p_raw * FAMILY_SIZE) if is_primary else p_raw\n"
        "        significant = p_used < ALPHA\n",
        "ap-record-merge-gate",
    )
    add(
        "correct-ap-frozen-record-merge-gate",
        merge_source,
        Outcome("abstain", "unresolved-manual-correction-present"),
        True,
        "4.1 frozen _record_merge_reason re-run",
        expected_gate="_record_merge_reason",
        expected_gate_reason="record-family-lineage-unresolved",
    )

    return tuple(fixtures)


def all_fixtures() -> tuple[Fixture, ...]:
    return (
        *cumulative_v3_fixtures(),
        *b5_expression_variants(),
        *laundering_adjacent_fixtures(),
        *new_ap_fixtures(),
    )
