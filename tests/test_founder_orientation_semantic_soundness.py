"""Soundness and compositional-coverage tests for founder-orientation semantic v3.

The historical wrong-answer sources are imported from the frozen v2 suite so
the v3 assertions exercise byte-identical counterexamples rather than a
second, drifting paraphrase of that corpus.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import replace

import pytest

from sc_referee.parsers.python_ast import PARSER_ID as PYTHON_PARSER_ID
from sc_referee.parsers.python_ast import PARSER_VERSION as PYTHON_PARSER_VERSION
from sc_referee.scientific_checks.founder_orientation_semantic import (
    SemanticResolution,
    resolve_founder_orientation_semantic,
)
from tests.test_founder_orientation_soundness import (
    _COUNTEREXAMPLE_REPORT,
    DIRECT_OPERAND,
    REPAIRED_OPERAND,
    ROUND_FOUR_COUNTEREXAMPLES,
    ROUND_THREE_COMPANIONS,
    ROUND_THREE_COUNTEREXAMPLES,
    ROUND_TWO_COMPANIONS,
    ROUND_TWO_COUNTEREXAMPLES,
    ROUND_TWO_RULES,
    V226_COUNTEREXAMPLES,
    WRONG_ANSWER_SHAPES,
    _inspection_context,
    _named_transform_workflow,
)


def _resolution(source: str, companions: Mapping[str, str] | None = None) -> SemanticResolution:
    context = _inspection_context(
        _COUNTEREXAMPLE_REPORT,
        {"analysis.py": source, **dict(companions or {})},
    )
    # The frozen v2 fixture deliberately flattens its selected report to
    # ``report.md`` even though the byte-identical counterexample sources
    # write ``results/report.md``.  V3 requires an exact sink path, so make
    # that synthetic artifact binding explicit without rewriting the source
    # corpus shared with the frozen suite.
    base_records = []
    for record in context.base_records:
        if record.ref != context.selected_artifact_ref:
            base_records.append(record)
            continue
        payload = json.loads(record.canonical_payload)
        payload["path"] = "results/report.md"
        base_records.append(type(record).from_record(record.ref, payload))
    context = replace(context, base_records=tuple(base_records))
    return resolve_founder_orientation_semantic(
        context,
        direct_operand=DIRECT_OPERAND,
        repaired_operand=REPAIRED_OPERAND,
        parser_id=PYTHON_PARSER_ID,
        parser_version=PYTHON_PARSER_VERSION,
    )


_SELECTOR_FORMS = (
    "return 1 * flag",
    "return 0 + (1 - 0) * flag",
    "return 1 * flag + 0 * (1 - flag)",
    "return 1 if flag else 0",
    "return [0, 1][flag]",
)


def _selector_workflow(return_statement: str, *, repaired: bool) -> str:
    panel = "1 - int(row['founder'])" if repaired else "int(row['founder'])"
    return f"""import csv
from pathlib import Path


def selector(left, right):
    flag = left == right
    {return_statement}


rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
score = sum(selector(int(row['call']), {panel}) for row in rows)
report = f'Of 4 markers, 3 agree. Agreement rate 0.750000. Score {{score}}.'
Path('results/report.md').write_text(report)
"""


@pytest.mark.parametrize("return_statement", _SELECTOR_FORMS)
@pytest.mark.parametrize(("repaired", "expected"), [(False, "direct"), (True, "repaired")])
def test_selector_algebra_is_recovered_extensionally(
    return_statement: str, repaired: bool, expected: str
) -> None:
    resolution = _resolution(_selector_workflow(return_statement, repaired=repaired))
    assert resolution.state == "unique"
    assert resolution.orientation == expected
    assert resolution.certificate is not None


@pytest.mark.parametrize("cast", ["int", "bool"])
def test_named_intermediates_and_flag_casts_are_ordinary_bindings(cast: str) -> None:
    source = f"""import csv
from pathlib import Path


def selector(left, right):
    flag = {cast}(left == right)
    low = 0
    gap = 1 - low
    weighted = low + gap * flag
    return weighted


rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
score = 0
for row in rows:
    left = int(row['call'])
    staged = int(row['founder'])
    right = 1 - staged
    weight = selector(left, right)
    score = score + weight
report = f'Of 4 markers, 3 agree. Agreement rate 0.750000. Score {{score}}.'
Path('results/report.md').write_text(report)
"""
    resolution = _resolution(source)
    assert resolution.state == "unique"
    assert resolution.orientation == "repaired"


def test_context_sensitive_reader_selector_and_writer_summaries_compose() -> None:
    source = """import csv
from pathlib import Path


def read_rows(path):
    lines = path.read_text(encoding='ascii').splitlines()
    return [dict(row) for row in csv.DictReader(lines)]


def selector(left, right):
    flag = left == right
    return 0 + (1 - 0) * flag


def write_report(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding='ascii')
    print(payload, end='')
    return len(payload)


rows = read_rows(Path('inputs/markers.csv'))
score = 0
for row in rows:
    observed = int(row['call'])
    panel = 1 - int(row['founder'])
    weight = selector(observed, panel)
    score = score + weight
report = f'Of 4 markers, 3 agree. Agreement rate 0.750000. Score {score}.'
written = write_report(Path('results/report.md'), report)
"""
    resolution = _resolution(source)
    assert resolution.state == "unique"
    assert resolution.orientation == "repaired"


def test_an_irrelevant_ordinary_construct_does_not_poison_the_slice() -> None:
    source = (
        _selector_workflow("return 1 * flag", repaired=True)
        + """

def unused_diagnostic(value):
    try:
        return {'ordinary': value}.get('ordinary')
    except LookupError:
        return None
"""
    )
    resolution = _resolution(source)
    assert resolution.state == "unique"
    assert resolution.orientation == "repaired"


def test_an_irrelevant_unmodelled_value_does_not_poison_the_slice() -> None:
    source = _selector_workflow("return 1 * flag", repaired=True).replace(
        "rows = list(csv.DictReader(Path('inputs/markers.csv').open()))",
        "diagnostic = {'ordinary': 37}\n"
        "rows = list(csv.DictReader(Path('inputs/markers.csv').open()))",
    )
    resolution = _resolution(source)
    assert resolution.state == "unique"
    assert resolution.orientation == "repaired"


def test_an_opaque_global_effect_from_an_allowlisted_module_abstains() -> None:
    source = _selector_workflow("return 1 * flag", repaired=True).replace(
        "rows = list(csv.DictReader(Path('inputs/markers.csv').open()))",
        "csv.field_size_limit(1)\nrows = list(csv.DictReader(Path('inputs/markers.csv').open()))",
    )
    resolution = _resolution(source)
    assert resolution.state != "unique"
    assert resolution.operand_value is None


def test_an_opaque_control_join_on_the_certified_slice_abstains() -> None:
    source = """import csv
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
panel = [int(row['founder']) for row in rows]
if rows:
    panel = [1 - value for value in panel]
score = sum(1 if int(row['call']) == panel[index] else 0 for index in range(len(rows)))
report = f'Of 4 markers, 3 agree. Agreement rate 0.750000. Score {score}.'
Path('results/report.md').write_text(report)
"""
    resolution = _resolution(source)
    assert resolution.state != "unique"
    assert resolution.operand_value is None


@pytest.mark.parametrize(
    "return_statement",
    [
        "return [0, 1][2 * flag]",
        "return 1 if (1 + flag) else 0",
        "return int(2 * flag)",
    ],
)
def test_truthiness_and_index_coercions_do_not_invent_a_predicate(
    return_statement: str,
) -> None:
    resolution = _resolution(_selector_workflow(return_statement, repaired=True))
    assert resolution.state != "unique"
    assert resolution.operand_value is None


def test_loop_control_transfer_before_the_accumulation_abstains() -> None:
    source = _selector_workflow("return 1 * flag", repaired=True).replace(
        "score = sum(selector(int(row['call']), 1 - int(row['founder'])) for row in rows)",
        """score = 0
for row in rows:
    break
    score = score + selector(int(row['call']), 1 - int(row['founder']))""",
    )
    resolution = _resolution(source)
    assert resolution.state != "unique"
    assert resolution.operand_value is None


def test_a_competing_selected_report_write_abstains() -> None:
    source = (
        _selector_workflow("return 1 * flag", repaired=True)
        + "\nPath('results/report.md').write_text('replacement')\n"
    )
    resolution = _resolution(source)
    assert resolution.state != "unique"
    assert resolution.operand_value is None


def test_a_same_suffix_write_outside_the_selected_artifact_does_not_bind() -> None:
    source = _selector_workflow("return 1 * flag", repaired=True).replace(
        "Path('results/report.md').write_text(report)",
        "Path('/tmp/results/report.md').write_text(report)",
    )
    resolution = _resolution(source)
    assert resolution.state != "unique"
    assert resolution.operand_value is None


def test_a_conditional_competing_selected_report_write_abstains() -> None:
    source = (
        _selector_workflow("return 1 * flag", repaired=True)
        + "\nif unresolved_condition:\n"
        + "    Path('results/report.md').write_text('possible replacement')\n"
    )
    resolution = _resolution(source)
    assert resolution.state != "unique"
    assert resolution.operand_value is None


def test_an_unresolved_write_like_effect_after_the_sink_abstains() -> None:
    source = (
        _selector_workflow("return 1 * flag", repaired=True)
        + "\nPath(report).write_text('possible replacement')\n"
    )
    resolution = _resolution(source)
    assert resolution.state != "unique"
    assert resolution.operand_value is None


@pytest.mark.parametrize(
    "panel_expression",
    [
        "int(row['founder']) ^ 1",
        "abs(int(row['founder']) - 1)",
        "int(not int(row['founder']))",
    ],
)
def test_a_binary_only_recode_without_a_proved_binary_domain_abstains(
    panel_expression: str,
) -> None:
    source = _selector_workflow("return 1 * flag", repaired=True).replace(
        "1 - int(row['founder'])", panel_expression
    )
    resolution = _resolution(source)
    assert resolution.state != "unique"
    assert resolution.operand_value is None


def test_a_definition_time_default_that_requires_environment_replay_abstains() -> None:
    source = _selector_workflow("return low + (1 - low) * flag", repaired=True).replace(
        "def selector(left, right):",
        "LOW = 0\n\ndef selector(left, right, low=LOW):",
    )
    resolution = _resolution(source)
    assert resolution.state != "unique"
    assert resolution.operand_value is None


@pytest.mark.parametrize("case", sorted(ROUND_TWO_COUNTEREXAMPLES))
def test_every_round_two_counterexample_abstains_or_matches_runtime(case: str) -> None:
    companion = ROUND_TWO_COMPANIONS.get(case)
    resolution = _resolution(
        ROUND_TWO_COUNTEREXAMPLES[case],
        {"companion.py": companion} if companion is not None else None,
    )
    runtime_orientation = ROUND_TWO_RULES[case][1]
    assert resolution.state != "unique" or resolution.orientation == runtime_orientation


@pytest.mark.parametrize("case", sorted(ROUND_THREE_COUNTEREXAMPLES))
def test_every_round_three_counterexample_abstains(case: str) -> None:
    resolution = _resolution(ROUND_THREE_COUNTEREXAMPLES[case], ROUND_THREE_COMPANIONS.get(case))
    assert resolution.state != "unique"
    assert resolution.operand_value is None


@pytest.mark.parametrize("case", sorted(ROUND_FOUR_COUNTEREXAMPLES))
def test_every_round_four_counterexample_abstains(case: str) -> None:
    resolution = _resolution(ROUND_FOUR_COUNTEREXAMPLES[case])
    assert resolution.state != "unique"
    assert resolution.operand_value is None


@pytest.mark.parametrize("case", sorted(V226_COUNTEREXAMPLES))
def test_every_v226_counterexample_abstains(case: str) -> None:
    resolution = _resolution(V226_COUNTEREXAMPLES[case])
    assert resolution.state != "unique"
    assert resolution.operand_value is None


@pytest.mark.parametrize("shape", sorted(WRONG_ANSWER_SHAPES))
def test_the_original_named_transform_family_never_returns_direct(shape: str) -> None:
    definition, call = WRONG_ANSWER_SHAPES[shape]
    resolution = _resolution(_named_transform_workflow(definition, call))
    assert resolution.orientation in {None, "repaired"}
    if resolution.orientation is None:
        assert resolution.state != "unique"
