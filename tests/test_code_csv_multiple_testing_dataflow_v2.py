from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path

import pytest

from sc_referee.scientific_checks import code_csv_multiple_testing_adapter_v1 as old_adapter
from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v2 import (
    _CLOSED_REASONS,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v2 import (
    MultipleTestingDataflowResult,
    analyze_code_csv_multiple_testing_dataflow,
)

_CASES = Path("evaluation/development/blind-envelope-10-2026-08-24/cases")
_MUT = Path("evaluation/development/multitest-recall-recon-e10/mut")
_P2 = "104493a5d99796a002c0"
_P3 = "3ff45fce2a45e0959fdb"


def _inputs(case_id: str, source: Path | None = None) -> dict[str, object]:
    case = _CASES / case_id
    profile = json.loads((case / "profile_1_2_0.json").read_text(encoding="utf-8"))
    authority = profile["semantic_role_authority"]["authorized_test_family"]
    path = authority["material_input_path"]
    csv_content = (case / "project" / path).read_bytes()
    rows = list(csv.reader(io.StringIO(csv_content.decode("utf-8"))))
    header = tuple(rows[0])
    group_column = authority["group_contrast_column"]
    group_index = header.index(group_column)
    counts = Counter(row[group_index] for row in rows[1:])
    group_values = tuple(sorted(counts, key=lambda value: value.encode("utf-8")))
    return {
        "content": (source or case / "project" / "analysis.py").read_bytes(),
        "authorized_path": path,
        "group_column": group_column,
        "outcome_columns": tuple(authority["outcome_columns"]),
        "csv_header": header,
        "group_values": group_values,
        "csv_content": csv_content,
    }


def _run(case_id: str, source: Path | None = None) -> MultipleTestingDataflowResult:
    return analyze_code_csv_multiple_testing_dataflow(**_inputs(case_id, source))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("PROBE_nestedtable.py", "candidate"),
        ("PROBE_dicttable.py", "candidate"),
        ("PROBE_pathparam.py", "candidate"),
        ("PROBE_namedalpha.py", "candidate"),
        ("PROBE_astype.py", "candidate"),
        ("PROBE_boolmask.py", "candidate"),
        ("PROBE_query.py", "candidate"),
        ("PROBE_enumerate.py", "candidate"),
        ("PROBE_helpertest.py", "candidate"),
        ("PROBE_floatp.py", "candidate"),
        ("PROBE_roundp.py", "pvalue-scalar-cast-or-rounding-unsupported"),
        ("PROBE_ternary.py", "candidate"),
        ("NEGSIM_A.py", "correction-family-lineage-unresolved"),
        ("NEGSIM_B.py", "unresolved-manual-correction-present"),
        ("NEGSIM_C.py", "candidate"),
    ],
)
def test_recon_probe_and_negsim_matrix(name: str, expected: str) -> None:
    result = _run(_P2, _MUT / name)
    if expected == "candidate":
        assert result.reason is None
        assert result.facts is not None
        assert result.facts.correction_classification == "none"
        assert result.facts.family_size == 5
        assert result.facts.conclusion_positions == (0, 1, 2, 3, 4)
        assert result.facts.corrected_positions == ()
    else:
        assert result.facts is None
        assert result.reason == expected


@pytest.mark.parametrize(
    ("case_id", "name", "expected"),
    [
        (_P2, "P2_m1.py", "candidate"),
        (_P2, "P2_m2.py", "candidate"),
        (_P2, "P2_m3.py", "candidate"),
        (_P2, "P2_m4.py", "candidate"),
        (_P2, "P2_m5.py", "candidate"),
        (_P2, "P2_m6.py", "candidate"),
        (_P2, "P2_m7.py", "candidate"),
        (_P2, "P2_m8.py", "candidate"),
        (_P3, "P3_s1.py", "candidate"),
        (_P3, "P3_s2.py", "candidate"),
        (_P3, "P3_s3.py", "candidate"),
        (_P3, "P3_s4.py", "candidate"),
        (_P3, "P3_s5.py", "candidate"),
        (_P3, "P3_s6.py", "candidate"),
        (_P3, "P3_s7.py", "extra-registered-test-outside-authorized-family"),
        (_P3, "P3_s8.py", "candidate"),
    ],
)
def test_p2_p3_mutation_ladders(case_id: str, name: str, expected: str) -> None:
    result = _run(case_id, _MUT / name)
    if expected == "candidate":
        assert result.facts is not None and result.reason is None
    else:
        assert result.reason == expected and result.facts is None


@pytest.mark.parametrize(
    ("case_id", "expected"),
    [
        ("ebbb8a5dbc2664257144", "authorized-reader-lineage-unavailable"),
        (_P2, "candidate"),
        (_P3, "candidate"),
        ("7296b0e2cf7faeefca64", "candidate"),
        ("c51d08801b3d0ba4e532", "candidate"),
        ("f4cf62caeb8ad68dc5b3", "candidate"),
        ("cb2e207276a0dc3247bb", "covered-negative"),
        ("9be74afbe9659bd50580", "unresolved-decision-threshold"),
        ("b787314c170f8f690060", "unresolved-manual-correction-present"),
        ("60f96fabb7129d662b23", "extra-registered-test-outside-authorized-family"),
        ("8d83210468ecde012e4a", "test-battery-cardinality-unresolved"),
        ("4907932548f745afe942", "authorized-family-test-census-incomplete"),
        ("6d2fdc67ab98bc0e0e6e", "authorized-family-test-census-incomplete"),
        ("dfc9f20a94ecefc7f7b5", "test-battery-cardinality-unresolved"),
        ("e1bce32a32e3b2df475e", "unresolved-decision-threshold"),
    ],
)
def test_opened_e10_analyzer_diagnostic(case_id: str, expected: str) -> None:
    first = _run(case_id)
    second = _run(case_id)
    assert first == second
    if expected == "candidate":
        assert first.reason is None
        assert first.facts is not None
        assert first.facts.correction_classification in {"none", "strict_subset"}
    elif expected == "covered-negative":
        assert first.reason is None
        assert first.facts is not None
        assert first.facts.correction_classification == "complete"
    else:
        assert first.reason == expected
        assert first.facts is None


@pytest.mark.parametrize(
    ("statement", "argument"),
    [
        ("DECLARED_OUTCOMES.append({arg})", '"extra"'),
        ("DECLARED_OUTCOMES.remove({arg})", '"particle_d90_um"'),
        ("DECLARED_OUTCOMES.pop({arg})", "0"),
        ("DECLARED_OUTCOMES.insert(0, {arg})", '"extra"'),
        ("DECLARED_OUTCOMES.extend([{arg}])", '"extra"'),
        ("DECLARED_OUTCOMES.clear()", ""),
        ("DECLARED_OUTCOMES.sort()", ""),
        ("DECLARED_OUTCOMES.reverse()", ""),
        ("DECLARED_OUTCOMES.__setitem__(0, {arg})", '"extra"'),
    ],
)
@pytest.mark.parametrize("source_name", ["PROBE_query.py", "PROBE_nestedtable.py"])
def test_immutable_sequence_mutation_matrix(
    tmp_path: Path, statement: str, argument: str, source_name: str
) -> None:
    source = (_MUT / source_name).read_text(encoding="utf-8")
    injected = source.replace(
        "def main():\n    frame = load_data()",
        "def main():\n    frame = load_data()\n    " + statement.format(arg=argument),
    )
    path = tmp_path / "analysis.py"
    path.write_text(injected, encoding="utf-8")
    assert _run(_P2, path).reason == "analysis-scope-structure-unsupported"


@pytest.mark.parametrize(
    "consumer",
    [
        'COPY = DECLARED_OUTCOMES + ["extra"]',
        'print(f"{DECLARED_OUTCOMES}")',
        "print(format(DECLARED_OUTCOMES))",
        'print("{}".format(DECLARED_OUTCOMES))',
        'print("particle_d90_um" in DECLARED_OUTCOMES)',
    ],
)
def test_read_only_consumer_fixtures_execute_without_supplying_family_facts(
    tmp_path: Path, consumer: str
) -> None:
    source = (_MUT / "PROBE_query.py").read_text(encoding="utf-8")
    if consumer.startswith("COPY"):
        source = source.replace("def load_data():", consumer + "\n\n\ndef load_data():")
    else:
        source = source.replace(
            "def main():\n    frame = load_data()",
            "def main():\n    frame = load_data()\n    " + consumer,
        )
    path = tmp_path / "consumer.py"
    path.write_text(source, encoding="utf-8")
    result = _run(_P2, path)
    assert result.facts is not None
    assert result.facts.family_size == 5


@pytest.mark.parametrize(
    "statement",
    [
        "DECLARED_OUTCOMES = ['particle_d90_um']",
        "del DECLARED_OUTCOMES[0]",
        "DECLARED_OUTCOMES[0] = 'extra'",
        "DECLARED_OUTCOMES[:] = []",
        "ALIAS = DECLARED_OUTCOMES\n    ALIAS.pop()",
    ],
)
def test_admission_negative_matrix(tmp_path: Path, statement: str) -> None:
    source = (_MUT / "PROBE_query.py").read_text(encoding="utf-8")
    injected = source.replace(
        "def main():\n    frame = load_data()",
        "def main():\n    frame = load_data()\n    " + statement,
    )
    path = tmp_path / "analysis.py"
    path.write_text(injected, encoding="utf-8")
    assert _run(_P2, path).reason == "analysis-scope-structure-unsupported"


def test_off_slice_outcome_sequence_consumer_is_not_inspected(tmp_path: Path) -> None:
    source = (
        (_MUT / "PROBE_query.py")
        .read_text(encoding="utf-8")
        .replace(
            "def main():\n    frame = load_data()",
            "def main():\n    frame = load_data()\n    unknown_consumer(DECLARED_OUTCOMES)",
        )
    )
    path = tmp_path / "analysis.py"
    path.write_text(source, encoding="utf-8")
    assert _run(_P2, path).facts is not None


def test_annassign_and_a5_rebinding_execute(tmp_path: Path) -> None:
    assert _run(_P2, _MUT / "PROBE_annassign.py").facts is not None

    named = (_MUT / "PROBE_namedalpha.py").read_text(encoding="utf-8")
    rebound = named.replace(
        "def main():\n    frame = load_data()",
        "def main():\n    frame = load_data()\n    ALPHA = 0.05 / len(DECLARED_OUTCOMES)",
    )
    rebound_path = tmp_path / "rebound.py"
    rebound_path.write_text(rebound, encoding="utf-8")
    assert _run(_P2, rebound_path).reason == "unresolved-decision-threshold"


@pytest.mark.parametrize(
    ("alpha_binding", "comparison", "helper"),
    [
        ("ALPHA = 0.05", "result.pvalue < 0.05 / 3", ""),
        ("ALPHA = 0.05", "result.pvalue < 1 - (1 - 0.05) ** (1 / 3)", ""),
        (
            "ALPHA = 0.05",
            "result.pvalue < make_threshold()",
            "def make_threshold():\n    return 0.05\n\n\n",
        ),
        ("ALPHA = 0.05 / 3", "result.pvalue < ALPHA", ""),
        ("ALPHA = float(0.05)", "result.pvalue < ALPHA", ""),
        ("ALPHA = 0.05", "0.05 / 3 > result.pvalue", ""),
    ],
)
def test_computed_thresholds_remain_exclusive_to_order_15(
    tmp_path: Path,
    alpha_binding: str,
    comparison: str,
    helper: str,
) -> None:
    source = (_MUT / "PROBE_query.py").read_text(encoding="utf-8")
    source = source.replace("ALPHA = 0.05", alpha_binding, 1)
    source = source.replace("def load_data():", helper + "def load_data():", 1)
    source = source.replace("result.pvalue < 0.05", comparison, 1)
    path = tmp_path / "computed-threshold.py"
    path.write_text(source, encoding="utf-8")
    result = _run(_P2, path)
    assert result.facts is None
    assert result.reason == "unresolved-decision-threshold"


@pytest.mark.parametrize(
    "consumer",
    [
        "enumerate(DECLARED_OUTCOMES, 1, start=2)",
        "sum(DECLARED_OUTCOMES, 1, start=2)",
        "zip(DECLARED_OUTCOMES, DECLARED_OUTCOMES)",
    ],
)
def test_retired_read_only_allowlist_does_not_inspect_off_slice_consumers(
    tmp_path: Path, consumer: str
) -> None:
    source = (_MUT / "PROBE_query.py").read_text(encoding="utf-8")
    source = source.replace(
        "def main():\n    frame = load_data()",
        f"def main():\n    frame = load_data()\n    print({consumer})",
    )
    path = tmp_path / "consumer-over-admission.py"
    path.write_text(source, encoding="utf-8")
    assert _run(_P2, path).facts is not None


def test_reversed_is_an_exact_read_only_builtin(tmp_path: Path) -> None:
    source = (_MUT / "PROBE_query.py").read_text(encoding="utf-8")
    source = source.replace(
        "def main():\n    frame = load_data()",
        "def main():\n    frame = load_data()\n    print(list(reversed(DECLARED_OUTCOMES)))",
    )
    path = tmp_path / "reversed.py"
    path.write_text(source, encoding="utf-8")
    assert _run(_P2, path).facts is not None


def test_fresh_concatenation_requires_matching_container_kind(tmp_path: Path) -> None:
    baseline = (_MUT / "PROBE_query.py").read_text(encoding="utf-8")
    mismatched = baseline.replace(
        "def load_data():",
        'COPY = DECLARED_OUTCOMES + ("extra",)\n\n\ndef load_data():',
    )
    mismatch_path = tmp_path / "mismatched-concat.py"
    mismatch_path.write_text(mismatched, encoding="utf-8")
    assert _run(_P2, mismatch_path).facts is not None

    matched = baseline.replace(
        "def load_data():",
        'COPY = DECLARED_OUTCOMES + ["extra"]\n\n\ndef load_data():',
    )
    match_path = tmp_path / "matched-concat.py"
    match_path.write_text(matched, encoding="utf-8")
    assert _run(_P2, match_path).facts is not None


def test_helper_reader_path_does_not_manufacture_a_filtered_call_site_frame(
    tmp_path: Path,
) -> None:
    source = (
        (_MUT / "PROBE_pathparam.py")
        .read_text(encoding="utf-8")
        .replace(
            "    return frame\n",
            '    return frame[frame["batch_id"] == "missing"]\n',
        )
    )
    path = tmp_path / "filtered-reader.py"
    path.write_text(source, encoding="utf-8")
    assert _run(_P2, path).reason == "selected-group-row-completeness-unproven"


@pytest.mark.parametrize(
    ("source_name", "old", "new", "expected"),
    [
        (
            "PROBE_dicttable.py",
            "OUTCOME_LABELS[outcome]",
            "OUTCOME_LABELS.get(outcome)",
            "candidate",
        ),
        (
            "PROBE_astype.py",
            ".astype(float)",
            ".astype(dtype=float)",
            "test-operand-lineage-unresolved",
        ),
        (
            "PROBE_astype.py",
            ".astype(float)",
            ".astype(TYPE)",
            "test-operand-lineage-unresolved",
        ),
        (
            "PROBE_boolmask.py",
            "frame[GROUP_COLUMN] == GROUP_A",
            'frame["batch_id"] == GROUP_A',
            "test-operand-lineage-unresolved",
        ),
        (
            "PROBE_boolmask.py",
            "frame[GROUP_COLUMN] == GROUP_A",
            '(frame[GROUP_COLUMN] == GROUP_A) & (frame["batch_id"] == "x")',
            "selected-group-row-completeness-unproven",
        ),
        (
            "PROBE_pathparam.py",
            "frame = load_data()",
            "frame = load_data(None)",
            "authorized-reader-lineage-unavailable",
        ),
        (
            "PROBE_query.py",
            "DECLARED_OUTCOMES = [",
            "DECLARED_OUTCOMES: factory() = [",
            "test-battery-cardinality-unresolved",
        ),
    ],
)
def test_closed_admission_near_misses_execute(
    tmp_path: Path, source_name: str, old: str, new: str, expected: str
) -> None:
    source = (_MUT / source_name).read_text(encoding="utf-8").replace(old, new, 1)
    path = tmp_path / "near-miss.py"
    path.write_text(source, encoding="utf-8")
    result = _run(_P2, path)
    if expected == "candidate":
        assert result.facts is not None
        assert result.reason is None
    else:
        assert result.facts is None
        assert result.reason == expected


def test_row_derived_threshold_and_round_negative_are_refused(tmp_path: Path) -> None:
    nested = (_MUT / "PROBE_nestedtable.py").read_text(encoding="utf-8")
    for label in ("D90", "Snap", "Melt", "Gloss", "Bitter"):
        nested = nested.replace(f'"{label}"', "0.05")
    nested = nested.replace("result.pvalue < 0.05", "result.pvalue < label")
    path = tmp_path / "row-threshold.py"
    path.write_text(nested, encoding="utf-8")
    assert _run(_P2, path).reason == "unresolved-decision-threshold"

    rounded = (
        (_MUT / "PROBE_roundp.py")
        .read_text(encoding="utf-8")
        .replace("round(result.pvalue, 4)", "round(result.pvalue, -1)")
    )
    round_path = tmp_path / "round-negative.py"
    round_path.write_text(rounded, encoding="utf-8")
    assert _run(_P2, round_path).reason == "unresolved-manual-correction-present"


@pytest.mark.parametrize(
    "shadow",
    [
        "def unused(ALPHA):\n    return None\n\n",
        "def unused():\n    ALPHA = 0.01\n    return None\n\n",
        "def unused():\n    import decimal as ALPHA\n    return None\n\n",
        "def unused():\n    try:\n        pass\n    except Exception as ALPHA:\n        pass\n\n",
    ],
)
def test_a5_syntax_wide_binder_census_executes(tmp_path: Path, shadow: str) -> None:
    source = (_MUT / "PROBE_namedalpha.py").read_text(encoding="utf-8")
    source = source.replace("def load_data():", shadow + "def load_data():")
    path = tmp_path / "binder.py"
    path.write_text(source, encoding="utf-8")
    assert _run(_P2, path).reason == "unresolved-decision-threshold"


def test_a5_source_decimal_and_product_rule_execute(tmp_path: Path) -> None:
    source = (_MUT / "PROBE_namedalpha.py").read_text(encoding="utf-8")
    exponent = source.replace("ALPHA = 0.05", "ALPHA = 5e-2", 1)
    exponent_path = tmp_path / "exponent.py"
    exponent_path.write_text(exponent, encoding="utf-8")
    assert _run(_P2, exponent_path).facts is not None

    bonferroni = source.replace("ALPHA = 0.05", "ALPHA = 0.01", 1)
    bonferroni_path = tmp_path / "bonferroni.py"
    bonferroni_path.write_text(bonferroni, encoding="utf-8")
    assert _run(_P2, bonferroni_path).reason == "unresolved-decision-threshold"


def _function_source(path: Path, name: str) -> bytes:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    node = next(
        item for item in ast.walk(tree) if isinstance(item, ast.FunctionDef) and item.name == name
    )
    return "\n".join(source.splitlines()[node.lineno - 1 : node.end_lineno]).encode()


def test_historical_v1_hierarchy_guard_is_unchanged_while_v2_is_versioned() -> None:
    old = _function_source(
        Path("src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_v1.py"),
        "_hierarchy_guard",
    )
    new = _function_source(
        Path("src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_v2.py"),
        "_hierarchy_guard",
    )
    assert new != old
    assert hashlib.sha256(old).hexdigest() == (
        "6a367d7c4c48b832864bfb6f66c2b3ca372582aa017fbd903561a20749342f00"
    )


@pytest.mark.parametrize(
    "name",
    [
        "PROBE_nestedtable.py",
        "PROBE_dicttable.py",
        "PROBE_pathparam.py",
        "PROBE_namedalpha.py",
        "PROBE_astype.py",
        "PROBE_boolmask.py",
        "PROBE_query.py",
        "PROBE_floatp.py",
        "PROBE_roundp.py",
        "PROBE_ternary.py",
        "NEGSIM_A.py",
        "NEGSIM_B.py",
        "NEGSIM_C.py",
    ],
)
def test_delta_predicates_are_invariant_to_prose_and_noncallee_names(
    tmp_path: Path, name: str
) -> None:
    path = _MUT / name
    baseline = _run(_P2, path)
    source = path.read_text(encoding="utf-8")
    mutated = source.replace(
        "Conching temperature and dark chocolate quality",
        "bonferroni holm sidak benjamini_hochberg primary exploratory score",
    )
    for old, new in (
        ("difference", "bonferroni"),
        ("header", "holm"),
        ("missing", "sidak"),
    ):
        mutated = mutated.replace(old, new)
    mutated += (
        "\n# prose-only report mutation: correction primary exploratory score\n"
        "# bonferroni holm sidak benjamini_hochberg\n"
    )
    changed = tmp_path / name
    changed.write_text(mutated, encoding="utf-8")
    assert _run(_P2, changed) == baseline


def test_historical_v1_source_anchor() -> None:
    expected = {
        "code_csv_multiple_testing_dataflow_v1.py": "44a4ad39dbcb2c37a2b3532bf0dc85c7144199fb71094a312b55ab8ddf900b1a",
        "code_csv_multiple_testing_adapter_v1.py": "3e8b474432d4c1d7ea1471f7dce4aec42dac4921380ebaf5110d978d62e90aa2",
    }
    root = Path("src/sc_referee/scientific_checks")
    for name, digest in expected.items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
    detector = Path("src/sc_referee/detectors/bounded_code_csv_multiple_testing_conflict_v1.py")
    assert hashlib.sha256(detector.read_bytes()).hexdigest() == (
        "76d7ec5c6ca0a44e2a0842adbfac7494af09429f3ddf20ed6a161f3da212124b"
    )


def test_closed_reason_set_includes_only_the_two_delta_reasons() -> None:
    assert _CLOSED_REASONS - old_adapter._CLOSED_REASONS == {
        "analysis-scope-structure-unsupported",
        "pvalue-scalar-cast-or-rounding-unsupported",
    }
