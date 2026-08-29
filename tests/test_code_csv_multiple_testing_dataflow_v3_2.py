from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

import sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_2 as ap
import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3 as frozen_v3
import sc_referee.scientific_checks.code_csv_multiple_testing_record_model_v3 as frozen_record
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_2 import (
    analyze_code_csv_multiple_testing_dataflow,
)

_SWEEP = Path("evaluation/development/multitest-code-slice-v3_2/prototype-sweep").resolve()
sys.path.insert(0, str(_SWEEP))
try:
    from fixture_catalog import Fixture, new_ap_fixtures
    from harness import inputs, reference_case
finally:
    sys.path.remove(str(_SWEEP))

_POSITIVE_AP = tuple(
    item
    for item in new_ap_fixtures()
    if item.expected is not None and item.expected.state in {"candidate", "covered"}
)


def _surrogate(fixture: Fixture) -> tuple[bytes, dict[str, object]]:
    case = reference_case(fixture.case_key)
    values = inputs(case, fixture.source)
    content = values.pop("content")
    outcomes = values["outcome_columns"]
    tree = frozen_v3._bounded_parse(content)
    resolver, reason = frozen_v3._resolver(
        tuple(item for item in tree.body if not frozen_v3._is_docstring(item))
    )
    assert resolver is not None and reason is None
    folds, rejected = ap._folds(
        tree,
        source=content,
        resolver=resolver,
        outcome_columns=outcomes,
    )
    threshold = ap._threshold_fold(
        tree,
        source=content,
        resolver=resolver,
        outcome_columns=outcomes,
    )
    if threshold is not None:
        folds.append(threshold)
    assert not rejected
    assert len(folds) == 1
    p_names, p_keys = frozen_record._p_lineage(tree, resolver)
    transports = ap._transport_targets(
        tree,
        folds[0],
        p_names=p_names,
        p_keys=p_keys,
        outcome_columns=outcomes,
    )
    return ap._surrogate_bytes(tree, folds[0], transports), values


@pytest.mark.parametrize("fixture", _POSITIVE_AP, ids=lambda item: item.name)
def test_ap_normalization_is_idempotent_on_every_positive_form(fixture: Fixture) -> None:
    surrogate, values = _surrogate(fixture)
    first = analyze_code_csv_multiple_testing_dataflow(fixture.source, **values)
    repeat = analyze_code_csv_multiple_testing_dataflow(fixture.source, **values)
    assert first == repeat
    frozen_surrogate = frozen_v3.analyze_code_csv_multiple_testing_dataflow(surrogate, **values)
    second_pass = ap.analyze_correction_model(
        surrogate,
        baseline=frozen_surrogate,
        outcome_columns=values["outcome_columns"],
        authorized_path=values["authorized_path"],
        group_column=values["group_column"],
        csv_header=values["csv_header"],
        group_values=values["group_values"],
        csv_content=values["csv_content"],
    )
    assert not second_pass.changed
    assert second_pass.corrected_positions == ()
    assert second_pass.model is None


def test_correction_span_is_added_without_changing_family_evidence() -> None:
    fixture = next(
        item for item in _POSITIVE_AP if item.name == "positive-ap-subset-capped-family-name"
    )
    case = reference_case(fixture.case_key)
    values = inputs(case, fixture.source)
    content = values.pop("content")
    result = analyze_code_csv_multiple_testing_dataflow(content, **values)
    assert result.reason is None and result.facts is not None
    assert result.facts.correction_classification == "strict_subset"
    assert result.facts.corrected_positions == (0, 1, 3)
    assert sum(span.role == "correction" for span in result.facts.evidence_spans) == 1
    assert all(
        span.family_position is None
        for span in result.facts.evidence_spans
        if span.role == "correction"
    )


def test_frozen_global_censuses_and_record_merge_guard_are_delegated() -> None:
    assert ap.mt is frozen_v3
    assert ap.rm is frozen_record
    assert ap.rm._record_merge_reason is frozen_record._record_merge_reason
    assert ast.dump(ast.parse("x = 1"), include_attributes=False) == ast.dump(
        frozen_v3._bounded_parse(b"x = 1\n"), include_attributes=False
    )
