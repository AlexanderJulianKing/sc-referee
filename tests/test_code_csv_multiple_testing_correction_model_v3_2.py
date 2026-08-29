from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v3_2 import (
    CLOSED_MULTIPLE_TESTING_ABSTENTION_REASONS,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_2 import (
    analyze_correction_model,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3 import (
    MultipleTestingDataflowResult,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3 import (
    analyze_code_csv_multiple_testing_dataflow as frozen_v3_analyze,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_2 import (
    analyze_code_csv_multiple_testing_dataflow,
)

_SWEEP = Path("evaluation/development/multitest-code-slice-v3_2/prototype-sweep").resolve()
sys.path.insert(0, str(_SWEEP))
try:
    from fixture_catalog import Fixture, all_fixtures, new_ap_fixtures
    from harness import Outcome, all_cases, inputs, reference_case
finally:
    sys.path.remove(str(_SWEEP))

_RESULTS = json.loads((_SWEEP / "results.json").read_text(encoding="utf-8"))
_EXPECTED_FIXTURES = {row["name"]: row for row in _RESULTS["fixtures"]}


def _outcome(result: MultipleTestingDataflowResult) -> list[object]:
    if result.reason is not None:
        return ["abstain", result.reason]
    assert result.facts is not None
    state = "covered" if result.facts.correction_classification == "complete" else "candidate"
    return [
        state,
        result.facts.correction_classification,
        {
            "authorized_count": result.facts.family_size,
            "corrected_positions": list(result.facts.corrected_positions),
        },
    ]


def _synthetic_baseline(value: Outcome) -> MultipleTestingDataflowResult:
    assert value.state == "abstain"
    return MultipleTestingDataflowResult(None, value.reason_or_classification)


def _model(fixture: Fixture) -> Any:
    case = reference_case(fixture.case_key)
    values = inputs(case, fixture.source)
    content = values.pop("content")
    if fixture.category == "v3.1-laundering-adjacent":
        baseline = _synthetic_baseline(fixture.baseline)
    else:
        baseline = frozen_v3_analyze(content, **values)
    return analyze_correction_model(
        content,
        baseline=baseline,
        outcome_columns=values.pop("outcome_columns"),
        **values,
    )


def test_closed_reason_set_remains_the_frozen_61_member_set() -> None:
    assert len(CLOSED_MULTIPLE_TESTING_ABSTENTION_REASONS) == 61


@pytest.mark.parametrize("fixture", all_fixtures(), ids=lambda item: item.name)
def test_all_170_design_fixtures_match_the_independent_sweep(fixture: Fixture) -> None:
    expected = _EXPECTED_FIXTURES[fixture.name]
    assert fixture.expected is not None
    model = _model(fixture)
    assert model.outcome.as_json() == expected["outcome"]
    assert model.changed is expected["changed"]
    assert model.attempted is expected["attempted"]
    assert model.model == expected["ap_model"]
    assert list(model.corrected_positions) == expected["corrected_positions"]


@pytest.mark.parametrize(
    "fixture",
    [item for item in new_ap_fixtures() if item.correct_analysis],
    ids=lambda item: item.name,
)
def test_ap_correct_refusal_fixtures_are_exact(fixture: Fixture) -> None:
    model = _model(fixture)
    assert model.outcome.as_json() == fixture.expected.as_json()
    assert model.outcome.state != "candidate"


@pytest.mark.parametrize(
    ("name", "gate", "gate_reason"),
    [
        (
            "correct-ap-cross-function-record-flow-gate",
            "cross-function-record-flow",
            None,
        ),
        (
            "correct-ap-frozen-record-merge-gate",
            "_record_merge_reason",
            "record-family-lineage-unresolved",
        ),
    ],
)
def test_ap_gate_name_fixtures_are_exact(
    name: str,
    gate: str,
    gate_reason: str | None,
) -> None:
    fixture = next(item for item in new_ap_fixtures() if item.name == name)
    model = _model(fixture)
    assert model.detail.get("gate") == gate
    assert model.detail.get("gate_reason") == gate_reason


def _fresh_attack_sources() -> tuple[tuple[str, bytes], ...]:
    base = next(
        item for item in new_ap_fixtures() if item.name == "positive-ap-subset-capped-family-name"
    ).source

    def replace(old: bytes, new: bytes) -> bytes:
        assert base.count(old) == 1
        return base.replace(old, new, 1)

    coincidental = next(
        item for item in new_ap_fixtures() if item.name == "correct-ap-unrelated-same-length-factor"
    ).source
    return (
        (
            "correct-ap-same-field-restore-post-fold",
            replace(
                b"            p_used = p_corrected\n",
                b"            p_corrected = p_corrected\n            p_used = p_corrected\n",
            ),
        ),
        (
            "correct-ap-aliased-fold",
            replace(
                b"            p_corrected = min(p_raw * FAMILY_SIZE, 1.0)\n",
                b"            p_alias = p_raw\n"
                b"            p_corrected = min(p_alias * FAMILY_SIZE, 1.0)\n",
            ),
        ),
        (
            "correct-ap-non-contract-predicate-positions",
            replace(
                b"        is_primary = column in PRIMARY_OUTCOMES\n",
                b'        is_primary = column.startswith("mean")\n',
            ),
        ),
        (
            "correct-ap-wrong-cap-polarity",
            replace(
                b"            p_corrected = min(p_raw * FAMILY_SIZE, 1.0)\n",
                b"            p_corrected = max(p_raw * FAMILY_SIZE, 1.0)\n",
            ),
        ),
        (
            "correct-ap-double-correction",
            replace(
                b"            p_used = p_corrected\n",
                b"            p_corrected = min(p_corrected * FAMILY_SIZE, 1.0)\n"
                b"            p_used = p_corrected\n",
            ),
        ),
        ("correct-ap-coincidental-length-len", coincidental),
    )


@pytest.mark.parametrize(
    ("name", "source"),
    _fresh_attack_sources(),
    ids=[name for name, _ in _fresh_attack_sources()],
)
def test_six_fresh_ap_attacks_are_named_exact_refusals(name: str, source: bytes) -> None:
    del name
    case = reference_case("E15:P6:81980e878c1bc8cc216b")
    values = inputs(case, source)
    content = values.pop("content")
    result = analyze_code_csv_multiple_testing_dataflow(content, **values)
    assert result.reason == "unresolved-manual-correction-present"
    assert result.facts is None


def test_cumulative_false_accusation_sweeps_remain_non_candidates() -> None:
    fixtures = all_fixtures()
    groups = {
        "corpus-correct": [
            case for case in all_cases() if case.envelope is None and case.labeled_correct
        ],
        "opened-negatives": [
            case for case in all_cases() if case.envelope is not None and case.labeled_correct
        ],
    }
    assert len(groups["corpus-correct"]) == 25
    assert len(groups["opened-negatives"]) == 54
    for cases in groups.values():
        assert not [
            case.key
            for case in cases
            if _outcome(
                analyze_code_csv_multiple_testing_dataflow(
                    (values := inputs(case)).pop("content"), **values
                )
            )[0]
            == "candidate"
        ]

    correct = [item for item in fixtures if item.correct_analysis]
    assert len(correct) == 154
    assert not [item.name for item in correct if _model(item).outcome.state == "candidate"]
    categories = Counter(item.category for item in fixtures)
    assert categories["b5-expression-variant"] == 63
    assert categories["v3.1-laundering-adjacent"] == 16
    assert sum(item.correct_analysis for item in new_ap_fixtures()) == 13


def test_final_source_analyzer_has_exactly_the_two_approved_movements() -> None:
    expected = {row["key"]: row for row in _RESULTS["cases"]}
    adapter_only_first_reasons = {
        "E10:N7:6d2fdc67ab98bc0e0e6e": "authorized-family-test-census-incomplete",
        "corpus:spec-30": "unresolved-manual-correction-present",
    }
    movements: list[str] = []
    for case in all_cases():
        values = inputs(case)
        content = values.pop("content")
        actual = _outcome(analyze_code_csv_multiple_testing_dataflow(content, **values))
        frozen = _outcome(frozen_v3_analyze(content, **values))
        row = expected[case.key]
        if case.key in adapter_only_first_reasons:
            assert actual == ["abstain", adapter_only_first_reasons[case.key]], case.key
        else:
            assert actual[:2] == row["outcome"][:2], case.key
        if actual != frozen:
            movements.append(case.key)
    assert movements == ["E15:P6:81980e878c1bc8cc216b", "corpus:spec-28"]
