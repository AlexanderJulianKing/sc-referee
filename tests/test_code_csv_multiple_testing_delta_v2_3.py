from __future__ import annotations

import ast
import copy
import hashlib
import json
import re
import runpy
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest

import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v2_3 as dataflow

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

_FROZEN_V2_2 = {
    "src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_v2_2.py": (
        "c34c7ab4872923aeb4271e537905cda9c519646bfa996ad1e99ef149c11cc325"
    ),
    "src/sc_referee/scientific_checks/code_csv_multiple_testing_adapter_v2_2.py": (
        "155770410e48a238df81cc87b521c8ac2bf526ce7bdf03c49c372c9bb5da7337"
    ),
    "src/sc_referee/scientific_checks/integration_multiple_testing_v2_2.py": (
        "f63fdb3918dfd36410f39d313781e9a334e604bd51aa81ff858a5a6ecee54f4d"
    ),
    "src/sc_referee/detectors/bounded_code_csv_multiple_testing_conflict_v2_2.py": (
        "8bcee3d46ee089e5587378f111779ba37f38968c590fa875f0a883fce296f92c"
    ),
    "docs/implementation/MULTITEST-CODE-SLICE-2.2-DESIGN-2026-08-26.md": (
        "64041f538ef64b4f1307702fa7c43b594dc745e10a93a30e572cdda8492a0a39"
    ),
    "evaluation/development/blind-envelope-12-2026-08-26/adapter_replay_records_v2_2.json": (
        "f8b7808b3baee264e9c496e2e899686af235e72c37b9647ce4255d10adbb02d8"
    ),
    "evaluation/development/multitest-code-slice-v2_2/DEVELOPMENT_LEDGER.json": (
        "70d408017bcf8d5fdefd9d033828a07425997e043831d352b4abcff7bc03573b"
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


def test_frozen_v2_2_replay_anchor_is_byte_immutable() -> None:
    for raw_path, expected in _FROZEN_V2_2.items():
        assert hashlib.sha256(Path(raw_path).read_bytes()).hexdigest() == expected


def test_v2_3_development_artifact_manifest_is_canonical_and_complete() -> None:
    root = Path("evaluation/development/multitest-code-slice-v2_3")
    payload = (root / "MANIFEST.json").read_bytes()
    manifest = json.loads(payload)
    assert json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode() == payload.rstrip(
        b"\n"
    )
    for relative, expected in manifest["files"].items():
        assert hashlib.sha256((root / relative).read_bytes()).hexdigest() == expected


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


_E13 = Path("evaluation/development/blind-envelope-13-2026-08-26/cases")
_E13_HARNESS = runpy.run_path("evaluation/development/multitest-recall-recon-e13/h.py")
_E13_ANALYZE = cast(Callable[..., Any], _E13_HARNESS["analyze_envelope"])


def _e13_result(case_id: str, source: str) -> tuple[str, str]:
    result = _E13_ANALYZE(
        _E13 / case_id,
        source.encode(),
        fn=dataflow.analyze_code_csv_multiple_testing_dataflow,
    )
    return _CLASSIFY(result)


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("mutated", "authorized-reader-lineage-unavailable"),
        ("conditional", "authorized-reader-lineage-unavailable"),
        ("aliased", "authorized-reader-lineage-unavailable"),
        ("nonconstant", "authorized-reader-lineage-unavailable"),
        ("reassigned", "authorized-reader-lineage-unavailable"),
        ("cross-function", "authorized-reader-lineage-unavailable"),
        ("second-reader", "additional-accepted-reader-present"),
        ("escaped", "authorized-reader-lineage-unavailable"),
    ],
)
def test_d13_a_refusal_matrix(mutation: str, expected: str) -> None:
    case = _E13 / "80091f37c722eba28e18"
    source = (case / "project" / "analysis.py").read_text(encoding="utf-8")
    if mutation == "mutated":
        source = source.replace(
            "    frame = pd.read_csv(path)", "    path += ''\n    frame = pd.read_csv(path)"
        )
    elif mutation == "conditional":
        source = source.replace(
            "    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_FILE)",
            "    if True:\n        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_FILE)",
        )
    elif mutation == "aliased":
        source = source.replace(
            "    frame = pd.read_csv(path)",
            "    reader_path = path\n    frame = pd.read_csv(reader_path)",
        )
    elif mutation == "nonconstant":
        source = source.replace(
            "os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_FILE)",
            "os.path.join(os.path.dirname(os.path.abspath(__file__)), choose_file())",
        )
    elif mutation == "reassigned":
        source = source.replace(
            "    frame = pd.read_csv(path)", "    frame = pd.read_csv(path)\n    path = DATA_FILE"
        )
    elif mutation == "cross-function":
        source = source.replace(
            "def load_data():",
            "def reader_path():\n    return os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_FILE)\n\n\ndef load_data():",
        ).replace(
            "    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_FILE)",
            "    path = reader_path()",
        )
    elif mutation == "second-reader":
        source = source.replace(
            "    frame = pd.read_csv(path)",
            "    pd.read_csv('other.csv')\n    frame = pd.read_csv(path)",
        )
    else:
        source = source.replace(
            "    frame = pd.read_csv(path)", "    print(path)\n    frame = pd.read_csv(path)"
        )
    assert _e13_result("80091f37c722eba28e18", source) == ("abstain", expected)


def test_d13_a_exact_local_bindings_admit_both_path_productions() -> None:
    expected = {
        "80091f37c722eba28e18": ("candidate", "strict_subset"),
        "b7d38f6e9284abfd3ee6": ("abstain", "correction-family-lineage-unresolved"),
    }
    for case_id, outcome in expected.items():
        source = (_E13 / case_id / "project" / "analysis.py").read_text(encoding="utf-8")
        assert _e13_result(case_id, source) == outcome


def test_correct_static_local_reader_path_complete_correction() -> None:
    _label, case, source = _FA["FIXTURES"][1]
    source = source.replace(
        'DATA_FILE = Path(__file__).resolve().parent / "allergy_spray_trial.csv"',
        'CSV_NAME = "allergy_spray_trial.csv"',
    ).replace(
        "    df = pd.read_csv(DATA_FILE)",
        "    data_path = Path(__file__).resolve().parent / CSV_NAME\n"
        "    df = pd.read_csv(data_path)",
    )
    assert _result(case, source) == ("covered", "complete")


def test_positive_terminal_clone_n_position_fanout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: list[dataflow._Mt23TerminalClosure] = []
    original = dataflow._MtEngine._mt23_build_terminal_closure

    def spy(engine: dataflow._MtEngine) -> dataflow._Mt23TerminalClosure:
        closure = original(engine)
        observed.append(closure)
        return closure

    monkeypatch.setattr(dataflow._MtEngine, "_mt23_build_terminal_closure", spy)
    case = _E13 / "80091f37c722eba28e18"
    source = (case / "project" / "analysis.py").read_text(encoding="utf-8")
    result = _E13_ANALYZE(
        case,
        source.encode(),
        fn=dataflow.analyze_code_csv_multiple_testing_dataflow,
    )
    assert _CLASSIFY(result) == ("candidate", "strict_subset")
    assert result.facts.corrected_positions == (0, 1)
    assert len(observed) == 2
    assert observed[0] == observed[1]
    mapped = [match for match in observed[0].matches if match.decision is not None]
    assert {match.occurrence.family_position for match in mapped} == set(range(7))
    assert len({id(match.transport) for match in mapped}) == len(mapped)
    assert [item.ordinal for item in observed[0].occurrences] == list(
        range(len(observed[0].occurrences))
    )
    assert all(
        match.decision is not None
        and any(match.decision is item for item in ast.walk(match.transport))
        for match in mapped
    )


def test_correct_terminal_clone_family_position_collision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = dataflow._MtEngine._mt23_terminal_occurrences

    def competing(
        engine: dataflow._MtEngine,
    ) -> tuple[dataflow._Mt23TerminalOccurrence, ...]:
        occurrences = original(engine)
        selected = next(item for item in occurrences if item.decision_key is not None)
        return (*occurrences, replace(selected, ordinal=len(occurrences)))

    monkeypatch.setattr(dataflow._MtEngine, "_mt23_terminal_occurrences", competing)
    case = _E13 / "80091f37c722eba28e18"
    source = (case / "project" / "analysis.py").read_text(encoding="utf-8")
    assert _e13_result("80091f37c722eba28e18", source) == (
        "abstain",
        "unresolved-pvalue-consumer",
    )


def test_terminal_clone_complete_and_threshold_adversaries() -> None:
    _label, case, base = _FA["FIXTURES"][1]

    def helper(source: str, *, corrected: bool) -> str:
        source = source.replace(
            "\ndef main():",
            "\ndef verdict(p):\n"
            "    return 'significant' if p < ALPHA else 'not significant'\n\n\n"
            "def main():",
        )
        if not corrected:
            source = source.replace("ALPHA = 0.05", "ALPHA = 0.01")
            source = source.replace(
                "p_used = min(1.0, float(result.pvalue) * n_comparisons)",
                "p_used = float(result.pvalue)",
            )
        return source.replace(
            'verdict = "significant" if p_used < ALPHA else "not significant"\n'
            '        print(f"{label}: corrected p = {p_used:.4f} -> {verdict}")',
            'print("%s: p = %.4f -> %s" % (label, p_used, verdict(p_used)))',
        )

    assert _result(case, helper(base, corrected=True)) == ("covered", "complete")
    assert _result(case, helper(base, corrected=False)) == (
        "abstain",
        "unresolved-decision-threshold",
    )


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("hidden-correction", "unresolved-pvalue-consumer"),
        ("two-sinks", "unresolved-pvalue-consumer"),
        ("family-position-collision", "unresolved-pvalue-consumer"),
        ("computed-threshold", "unresolved-decision-threshold"),
        ("export-sibling", "unresolved-pvalue-consumer"),
    ],
)
def test_d13_b_adversary_matrix(mutation: str, expected: str) -> None:
    case = _E13 / "80091f37c722eba28e18"
    source = (case / "project" / "analysis.py").read_text(encoding="utf-8")
    if mutation == "hidden-correction":
        source = source.replace(
            "def verdict(p_value):",
            "def adjust(p):\n    return hidden_adjust(p)\n\n\ndef verdict(p_value):",
        ).replace(
            'return "SIGNIFICANT" if p_value < ALPHA else "not significant"',
            'return "SIGNIFICANT" if adjust(p_value) < ALPHA else "not significant"',
        )
    elif mutation in {"two-sinks", "family-position-collision"}:
        source = source.replace(
            'print("  verdict at alpha=%.2f  : %s (unadjusted p)" % (ALPHA, verdict(result["p_value"])))',
            'decision = verdict(result["p_value"])\n'
            '        print("  verdict at alpha=%.2f  : %s (unadjusted p)" % (ALPHA, decision))\n'
            '        print("  repeated verdict: %s" % decision)',
        )
    elif mutation == "computed-threshold":
        source = source.replace("p_value < ALPHA", "p_value < (1 - (1 - ALPHA) ** (1 / 7))")
    else:
        source = source.replace(
            "    print()\n\n\ndef main():",
            '    pd.DataFrame({"p": [result["p_value"]]}).to_csv("p.csv")\n    print()\n\n\ndef main():',
        )
    assert _e13_result("80091f37c722eba28e18", source) == ("abstain", expected)
