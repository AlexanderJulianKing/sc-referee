from __future__ import annotations

import ast
import copy
import hashlib
import json
import re
import runpy
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest

import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v2_2 as dataflow

_LADDER_ROOT = Path("evaluation/development/multitest-code-slice-v2_2/e12-ladders")
_HARNESS = runpy.run_path(str(_LADDER_ROOT / "h.py"))
_FA = runpy.run_path(str(_LADDER_ROOT / "fa.py"))
_ANALYZE = cast(Callable[..., Any], _HARNESS["analyze_envelope"])
_CLASSIFY = cast(Callable[[Any], tuple[str, str]], _HARNESS["classify"])
_E12 = cast(Path, _HARNESS["E12"])

_FROZEN_V2_1 = {
    "src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_v2_1.py": (
        "19036239ff85ed725d82de2d447bf214bda075101e7574935f6c3465c8dc960a"
    ),
    "src/sc_referee/scientific_checks/code_csv_multiple_testing_adapter_v2_1.py": (
        "e47b6a409c91675530f594375de060ee5190e8e1331c680d3c6b9384167104f8"
    ),
    "src/sc_referee/scientific_checks/integration_multiple_testing_v2_1.py": (
        "9caa6f7b0743816abf9ebe51f562741d3722847697969fa243131b3af68e0317"
    ),
    "src/sc_referee/detectors/bounded_code_csv_multiple_testing_conflict_v2_1.py": (
        "78ab2993054cc4b0ec3abb8f1905f627511aa0d66fe8bdf95de235f11bc91153"
    ),
    "docs/implementation/MULTITEST-CODE-SLICE-2.1-DESIGN-2026-08-25.md": (
        "d468fba746b6eb741f5cc47abc6bd5e5e529ff3e63988f80ec8c3a8c208e4165"
    ),
    "evaluation/development/multitest-open-corpus-v1/adapter_replay_records_v2_1.json": (
        "7c37669c8ccfdb0b754aa03ee1dbcee1dac78fa4bb44105e17c5d1886aaed502"
    ),
}


def _run(case: Path, source: str) -> Any:
    return _ANALYZE(
        case,
        source.encode("utf-8"),
        fn=dataflow.analyze_code_csv_multiple_testing_dataflow,
    )


def _result(case: Path, source: str) -> tuple[str, str]:
    return _CLASSIFY(_run(case, source))


def test_frozen_v2_1_replay_anchor_is_byte_immutable() -> None:
    for raw_path, expected in _FROZEN_V2_1.items():
        assert hashlib.sha256(Path(raw_path).read_bytes()).hexdigest() == expected


def test_development_ledger_is_canonical_and_pins_executed_fixtures() -> None:
    path = Path("evaluation/development/multitest-code-slice-v2_2/DEVELOPMENT_LEDGER.json")
    payload = path.read_bytes()
    ledger = json.loads(payload)
    assert json.dumps(ledger, sort_keys=True, separators=(",", ":")).encode() == payload.rstrip(
        b"\n"
    )
    assert ledger["fixture_count"] == len(_FA["FIXTURES"]) == 6
    for record, (_label, _case, source) in zip(ledger["fixtures"], _FA["FIXTURES"], strict=True):
        assert record["source_sha256"] == "sha256:" + hashlib.sha256(source.encode()).hexdigest()


@pytest.mark.parametrize(
    ("index", "expected"),
    [
        (0, ("abstain", "unresolved-manual-correction-present")),
        (1, ("covered", "complete")),
        (2, ("abstain", "unresolved-manual-correction-present")),
        (3, ("abstain", "analysis-scope-structure-unsupported")),
        (4, ("covered", "complete")),
        (5, ("abstain", "unresolved-pvalue-consumer")),
    ],
)
def test_recon_false_accusation_fixtures_execute(index: int, expected: tuple[str, str]) -> None:
    _label, case, source = _FA["FIXTURES"][index]
    assert _result(case, source) == expected


def test_d2_refuses_lazy_family_call() -> None:
    case = _E12 / "e28a9537b07c74d21838"
    source = (case / "project" / "analysis.py").read_text(encoding="utf-8")
    source = source.replace("ALPHA = 0.05", "ALPHA = 0.05\nRUN_TEST = True")
    source = source.replace(
        "float(compare(rack[column], block[column]).pvalue)",
        "float((compare(rack[column], block[column]) if RUN_TEST else None).pvalue)",
    )
    assert _result(case, source) == ("abstain", "test-battery-cardinality-unresolved")


def test_d2_eager_call_with_unresolved_sibling_consumer() -> None:
    case = _E12 / "e28a9537b07c74d21838"
    source = (case / "project" / "analysis.py").read_text(encoding="utf-8")
    source = source.replace(
        "float(compare(rack[column], block[column]).pvalue)",
        "float(unresolved_consumer(compare(rack[column], block[column]).pvalue))",
    )
    assert _result(case, source) == ("abstain", "unresolved-pvalue-consumer")


def test_d2_p3_preserves_untouched_census_and_one_to_six_to_six_bijection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = _E12 / "e28a9537b07c74d21838"
    observed: dict[str, list[int]] = {"census": [], "bindings": [], "preserved": []}
    original_census = dataflow._mt_call_census
    original_normalize = dataflow._mt22_d2_normalize_family_calls
    original_preserved = dataflow._mt22_d2_occurrences_preserved

    def census_spy(*args: Any, **kwargs: Any) -> Any:
        result, reason = original_census(*args, **kwargs)
        observed["census"].append(0 if result is None else len(result))
        return result, reason

    def normalize_spy(*args: Any, **kwargs: Any) -> Any:
        result = original_normalize(*args, **kwargs)
        observed["bindings"].append(len(result.occurrence_keys))
        return result

    def preserved_spy(scope: tuple[ast.stmt, ...], expected: tuple[str, ...]) -> bool:
        passed = original_preserved(scope, expected)
        observed["preserved"].append(len(expected) if passed else -1)
        return passed

    monkeypatch.setattr(dataflow, "_mt_call_census", census_spy)
    monkeypatch.setattr(dataflow, "_mt22_d2_normalize_family_calls", normalize_spy)
    monkeypatch.setattr(dataflow, "_mt22_d2_occurrences_preserved", preserved_spy)
    assert _result(case, (case / "project" / "analysis.py").read_text()) == (
        "candidate",
        "none",
    )
    assert observed == {"census": [6], "bindings": [6], "preserved": [6]}


def test_d3_unrelated_same_length_table_stays_unresolved() -> None:
    _label, case, source = _FA["FIXTURES"][2]
    assert _result(case, source) == ("abstain", "unresolved-manual-correction-present")


@pytest.mark.parametrize(
    "mutation",
    [
        "alias-mutation",
        "rebind",
        "delete",
        "subscript-store",
        "helper-escape",
    ],
)
def test_d5_mutation_refuses_membership_oracle(mutation: str) -> None:
    _label, case, source = _FA["FIXTURES"][4]
    insertion = ""
    if mutation == "alias-mutation":
        insertion = "\nCORRECTED_ALIAS = CORRECTED\nCORRECTED_ALIAS.add('tnss_total')\n"
    elif mutation == "rebind":
        insertion = "\nCORRECTED = {'tnss_total'}\n"
    elif mutation == "delete":
        insertion = "\ndel CORRECTED\n"
    elif mutation == "subscript-store":
        insertion = "\nCORRECTED[0] = 'tnss_total'\n"
    else:
        insertion = "\ndef observe(value):\n    return len(value)\n\nobserve(CORRECTED)\n"
    source = source.replace("\ndef main():", insertion + "\ndef main():")
    assert _result(case, source) == (
        "abstain",
        "analysis-scope-structure-unsupported",
    )


def test_d5_frozenset_is_not_a_membership_oracle() -> None:
    _label, case, source = _FA["FIXTURES"][4]
    source = source.replace("CORRECTED = {", "CORRECTED = frozenset({", 1).replace(
        "\n\n\ndef main():", ")\n\n\ndef main():", 1
    )
    assert _result(case, source) == ("abstain", "pderived-conclusion-family-incomplete")


@pytest.mark.parametrize("domain", ["CORRECTED", "sorted(CORRECTED)"])
def test_d5_set_never_supplies_family_iteration_order(domain: str) -> None:
    _label, case, source = _FA["FIXTURES"][4]
    source = source.replace("for column, label in OUTCOMES:", f"for column in {domain}:")
    source = source.replace(
        'print(f"{label}: p = {p_used:.4f} -> {verdict}")',
        'print(f"{column}: p = {p_used:.4f} -> {verdict}")',
    )
    assert _result(case, source) == ("abstain", "test-battery-cardinality-unresolved")


def _nested_d6_source(*, cutoff: str) -> tuple[Path, str]:
    _label, case, source = _FA["FIXTURES"][1]
    source = source.replace(
        "def main():",
        (
            "def verdict(p):\n"
            f"    return 'significant' if p < {cutoff} else 'not significant'\n\n"
            "def render(label, p):\n"
            "    print(f'{label}: {verdict(p)}')\n\n\n"
            "def main():"
        ),
    )
    source = source.replace(
        "p_used = min(1.0, float(result.pvalue) * n_comparisons)",
        "p_used = float(result.pvalue)",
    )
    source = source.replace(
        'verdict = "significant" if p_used < ALPHA else "not significant"\n'
        '        print(f"{label}: corrected p = {p_used:.4f} -> {verdict}")',
        "render(label, p_used)",
    )
    return case, source


def test_d6_nested_computed_threshold_stays_unresolved() -> None:
    case, source = _nested_d6_source(cutoff="1 - (1 - ALPHA) ** (1 / 5)")
    assert _result(case, source) == ("abstain", "unresolved-decision-threshold")


def test_d6_verdict_product_rule_n5_stays_unresolved() -> None:
    case, source = _nested_d6_source(cutoff="0.01")
    assert _result(case, source) == ("abstain", "unresolved-decision-threshold")


def test_d6_transformer_is_structurally_idempotent() -> None:
    source = """
def verdict(p):
    return "significant" if p < 0.05 else "not significant"

print(verdict(p_value))
"""
    tree = ast.parse(source)
    helper = cast(ast.FunctionDef, tree.body[0])
    scope = (cast(ast.stmt, tree.body[1]),)
    resolver, reason = dataflow._resolver(tuple(tree.body))
    assert reason is None and resolver is not None
    once = dataflow._mt_v2_expand_terminal_helpers(scope, {"verdict": helper}, resolver)
    twice = dataflow._mt_v2_expand_terminal_helpers(
        copy.deepcopy(once), {"verdict": helper}, resolver
    )
    assert dataflow._mt22_canonical_terminal_scope(once) == (
        dataflow._mt22_canonical_terminal_scope(twice)
    )


def test_d2_d3_d5_d6_final_matches_executed_prototype_on_e12() -> None:
    prototype = runpy.run_path(str(_LADDER_ROOT / "mt_patched_2356.py"))[
        "analyze_code_csv_multiple_testing_dataflow"
    ]
    for item in cast(Callable[[Path], list[dict[str, str]]], _HARNESS["roles"])(_E12):
        case = _E12 / item["case_id"]
        final = _CLASSIFY(_ANALYZE(case, fn=dataflow.analyze_code_csv_multiple_testing_dataflow))
        reference = _CLASSIFY(_ANALYZE(case, fn=prototype))
        assert final == reference


@pytest.mark.parametrize(
    "case_id",
    [
        "e28a9537b07c74d21838",  # D2
        "54667dd7c39067c8c2c8",  # D6
        "68d1a6f5b1ab70f2650a",  # D3 + D5
    ],
)
def test_delta_predicates_are_prose_mutation_invariant(case_id: str) -> None:
    case = _E12 / case_id
    source = (case / "project" / "analysis.py").read_text(encoding="utf-8")
    baseline = _run(case, source)
    mutated = source.replace('"""', '"""', 1)
    mutated += "\n# bonferroni holm sidak benjamini_hochberg\n"
    if "header =" in mutated:
        mutated = re.sub(r"\bheader\b", "benjamini_hochberg", mutated)
    observed = _run(case, mutated)
    assert observed.reason == baseline.reason
    assert observed.facts == baseline.facts


def test_d5_structural_membership_literal_is_a_positive_control() -> None:
    case = _E12 / "68d1a6f5b1ab70f2650a"
    source = (case / "project" / "analysis.py").read_text(encoding="utf-8")
    baseline = _run(case, source)
    mutated = source.replace(
        'PRESCRIBING_RELEVANT = {"tnss_total", "pnif_l_min"}',
        'PRESCRIBING_RELEVANT = {"tnss_total"}',
    )
    observed = _run(case, mutated)
    assert baseline.facts is not None and observed.facts is not None
    assert baseline.facts.corrected_positions == (0, 1)
    assert observed.facts.corrected_positions == (0,)
