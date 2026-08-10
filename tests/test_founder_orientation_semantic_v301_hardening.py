"""Executable adversarial regressions for founder semantic v3.0.1 lowering."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path

import pytest

from sc_referee.scientific_checks.founder_orientation_semantic import (
    resolve_founder_orientation_semantic,
)
from sc_referee.scientific_checks.profiles import scientific_check_release_registry
from tests.test_founder_orientation_semantic_pilots import _with_bound_csv
from tests.test_founder_orientation_semantic_soundness import _resolution
from tests.test_founder_orientation_soundness import (
    DIRECT_OPERAND,
    REPAIRED_OPERAND,
    _inspection_context,
)

_FOUNDER_CHECK = "check:founder-orientation-before-hmm-emission"
_CSV = "call,founder\n0,0\n1,1\n0,0\n1,0\n"


def _runtime_context(tmp_path: Path, source: str, *, csv_text: str = _CSV):
    (tmp_path / "inputs").mkdir()
    (tmp_path / "results").mkdir()
    (tmp_path / "inputs" / "markers.csv").write_text(csv_text, encoding="utf-8")
    workflow = tmp_path / "analysis.py"
    workflow.write_text(source, encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, str(workflow)],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert completed.returncode == 0, completed.stderr
    report = (tmp_path / "results" / "report.md").read_text(encoding="ascii")
    context = _inspection_context(report, {"analysis.py": source})
    records = []
    for record in context.base_records:
        if record.ref != context.selected_artifact_ref:
            records.append(record)
            continue
        payload = json.loads(record.canonical_payload)
        payload["path"] = "results/report.md"
        records.append(type(record).from_record(record.ref, payload))
    context = replace(context, base_records=tuple(records))
    return _with_bound_csv(context, csv_text.encode("utf-8"), path="inputs/markers.csv")


def _assert_released_adapters_match_or_abstain(
    tmp_path: Path,
    source: str,
    *,
    runtime_orientation: str,
) -> None:
    context = _runtime_context(tmp_path, source)
    registry = scientific_check_release_registry()
    module = next(item for item in registry.modules if item.manifest.check_id == _FOUNDER_CHECK)
    assert {item.adapter_version for item in module.adapters} == {"2.2.6", "3.1.1"}
    evaluation = next(
        item for item in registry.evaluate(context).modules if item.check_id == _FOUNDER_CHECK
    )
    expected = REPAIRED_OPERAND if runtime_orientation == "repaired" else DIRECT_OPERAND
    applicable = [
        observation
        for observation in evaluation.observations
        if observation.applicability == "applicable"
    ]
    assert all(
        observation.observed_operand is not None
        and str(observation.observed_operand.value) == expected
        for observation in applicable
    )
    if evaluation.state == "applicable":
        assert applicable
    semantic = next(item for item in module.adapters if item.adapter_version == "3.1.1")
    semantic_observation = semantic.inspect(context)
    assert semantic_observation.applicability != "applicable" or (
        semantic_observation.observed_operand is not None
        and str(semantic_observation.observed_operand.value) == expected
    )


def _report_expression(score: str) -> str:
    return (
        f"score = {score}\n"
        "rate = score / 4\n"
        "report = f'[selected-result] Of 4 markers, {score} agree. "
        "Agreement rate {rate:.6f}. Score {score}.'\n"
        "Path('results/report.md').write_text(report, encoding='ascii')\n"
    )


@pytest.mark.parametrize(
    "selector",
    [
        "1 if int(row['call']) == recode_base - int(row['founder']) else 0",
        "1 * (int(row['call']) == recode_base - int(row['founder']))",
    ],
)
def test_s1_list_pop_selector_forms_both_abstain(tmp_path: Path, selector: str) -> None:
    source = f"""import csv
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
recode_bases = [1, 0]
recode_bases.pop(0)
recode_base = recode_bases[0]
{_report_expression(f"sum({selector} for row in rows)")}"""
    _assert_released_adapters_match_or_abstain(tmp_path, source, runtime_orientation="direct")


def test_selected_field_is_independent_of_a_repaired_diagnostic_fold(
    tmp_path: Path,
) -> None:
    source = """import csv
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
diagnostic = sum(1 * (int(row['call']) == 1 - int(row['founder'])) for row in rows)
actual_selected_result = 3
report = (
    f'Repaired diagnostic count: {diagnostic}\\n'
    f'[selected-result] Of 4 markers, {actual_selected_result} agree. '
    f'Agreement rate 0.750000. Score {actual_selected_result}.'
)
Path('results/report.md').write_text(report, encoding='ascii')
"""
    _assert_released_adapters_match_or_abstain(tmp_path, source, runtime_orientation="direct")


def test_a1_walrus_is_a_semantic_module_ban(tmp_path: Path) -> None:
    source = """import csv
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
marker = (ordinary := 0)
""" + _report_expression("sum(1 * (int(row['call']) == int(row['founder'])) for row in rows)")
    _assert_released_adapters_match_or_abstain(tmp_path, source, runtime_orientation="direct")


def test_a2_loop_carried_flag_abstains(tmp_path: Path) -> None:
    source = """import csv
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
score = 0
use_repair = 1
for row in rows:
    panel = int(row['founder']) if use_repair == 0 else 1 - int(row['founder'])
    score = score + 1 * (int(row['call']) == panel)
    use_repair = 0
rate = score / 4
report = f'[selected-result] Of 4 markers, {score} agree. Agreement rate {rate:.6f}. Score {score}.'
Path('results/report.md').write_text(report, encoding='ascii')
"""
    _assert_released_adapters_match_or_abstain(tmp_path, source, runtime_orientation="direct")


def test_a2b_filtered_comprehension_mutation_abstains(tmp_path: Path) -> None:
    source = """import csv
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
rows = [row for row in rows if not row.update({'founder': str(1 - int(row['founder']))})]
""" + _report_expression("sum(1 * (int(row['call']) == int(row['founder'])) for row in rows)")
    _assert_released_adapters_match_or_abstain(tmp_path, source, runtime_orientation="repaired")


def test_a3_dotdot_alias_is_the_selected_sink(tmp_path: Path) -> None:
    source = """import csv
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
direct = sum(1 * (int(row['call']) == int(row['founder'])) for row in rows)
direct_report = f'[selected-result] Of 4 markers, {direct} agree. Agreement rate {direct / 4:.6f}. Score {direct}.'
Path('results/report.md').write_text(direct_report, encoding='ascii')
repaired = sum(1 * (int(row['call']) == 1 - int(row['founder'])) for row in rows)
repaired_report = f'[selected-result] Of 4 markers, {repaired} agree. Agreement rate {repaired / 4:.6f}. Score {repaired}.'
Path('results/../results/report.md').write_text(repaired_report, encoding='ascii')
"""
    _assert_released_adapters_match_or_abstain(tmp_path, source, runtime_orientation="repaired")


def test_b2_nonliteral_default_is_definition_time_control(tmp_path: Path) -> None:
    source = """import csv
from pathlib import Path

def helper(value=(1 + 0)):
    return value

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
""" + _report_expression("sum(1 * (int(row['call']) == int(row['founder'])) for row in rows)")
    _assert_released_adapters_match_or_abstain(tmp_path, source, runtime_orientation="direct")


def test_runtime_callable_rebinding_is_opaque(tmp_path: Path) -> None:
    source = """import csv
from pathlib import Path

def panel(row):
    return 1 - int(row['founder'])

def direct_panel(row):
    return int(row['founder'])

panel = direct_panel
rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
""" + _report_expression("sum(1 * (int(row['call']) == panel(row)) for row in rows)")
    _assert_released_adapters_match_or_abstain(tmp_path, source, runtime_orientation="direct")


@pytest.mark.parametrize(
    "binding",
    [
        "match 'x':\n    case 'y' as int:\n        pass",
        "try:\n    pass\nexcept Exception as int:\n    pass",
        "if False:\n    class int:\n        pass",
    ],
)
def test_inherited_builtin_shadow_bans_cover_hidden_targets(tmp_path: Path, binding: str) -> None:
    source = f"""import csv
from pathlib import Path

{binding}
rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
{_report_expression("sum(1 * (int(row['call']) == int(row['founder'])) for row in rows)")}"""
    _assert_released_adapters_match_or_abstain(tmp_path, source, runtime_orientation="direct")


@pytest.mark.parametrize("companion", ["state = []\nstate.pop()\n", "if (\n"])
def test_cross_document_wildcard_effect_blocks_the_case(companion: str) -> None:
    source = """import csv
from pathlib import Path
rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
score = sum(1 * (int(row['call']) == int(row['founder'])) for row in rows)
report = f'[selected-result] Of 4 markers, {score} agree. Agreement rate 0.750000. Score {score}.'
Path('results/report.md').write_text(report)
"""
    resolution = _resolution(source, {"companion.py": companion})
    assert resolution.state != "unique"
    assert resolution.orientation is None


def test_unmodelled_assert_is_a_control_effect(tmp_path: Path) -> None:
    source = """import csv
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
assert rows is not None
""" + _report_expression("sum(1 * (int(row['call']) == int(row['founder'])) for row in rows)")
    _assert_released_adapters_match_or_abstain(tmp_path, source, runtime_orientation="direct")


@pytest.mark.parametrize(
    "cast",
    [
        "int(row['founder'])",
        "float(row['founder'])",
        "Decimal(row['founder'])",
        "Fraction(row['founder'])",
    ],
)
def test_binary_domain_discharge_keeps_supported_casts_sound(tmp_path: Path, cast: str) -> None:
    imports = "from decimal import Decimal\nfrom fractions import Fraction\n"
    source = f"""import csv
from pathlib import Path
{imports}
rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
score = sum(1 * (int(row['call']) == {cast}) for row in rows)
rate = score / 4
report = f'[selected-result] Of 4 markers, {{score}} agree. Agreement rate {{rate:.6f}}. Score {{score}}.'
Path('results/report.md').write_text(report, encoding='ascii')
"""
    _assert_released_adapters_match_or_abstain(tmp_path, source, runtime_orientation="direct")


def test_non_binary_compared_column_still_abstains(tmp_path: Path) -> None:
    source = """import csv
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
score = sum(1 * (int(row['call']) == 1 - int(row['founder'])) for row in rows)
rate = score / 4
report = f'[selected-result] Of 4 markers, {score} agree. Agreement rate {rate:.6f}. Score {score}.'
Path('results/report.md').write_text(report, encoding='ascii')
"""
    context = _runtime_context(
        tmp_path,
        source,
        csv_text="call,founder\n0,0\n1,1\n0,2\n1,0\n",
    )
    resolution = resolve_founder_orientation_semantic(
        context,
        direct_operand=DIRECT_OPERAND,
        repaired_operand=REPAIRED_OPERAND,
        parser_id="parser:python-ast-tokenize",
        parser_version="1.0.0",
    )
    assert resolution.state != "unique"
    assert resolution.orientation is None


def test_short_dictreader_row_raises_at_runtime_and_never_certifies(tmp_path: Path) -> None:
    source = """import csv
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
score = sum(1 * (int(row['call']) == int(row['founder'])) for row in rows)
report = f'[selected-result] Of 1 marker, {score} agree. Agreement rate 1.000000. Score {score}.'
Path('results/report.md').write_text(report)
"""
    (tmp_path / "inputs").mkdir()
    (tmp_path / "results").mkdir()
    (tmp_path / "inputs" / "markers.csv").write_text("call,founder\n0\n", encoding="ascii")
    workflow = tmp_path / "analysis.py"
    workflow.write_text(source, encoding="ascii")
    completed = subprocess.run(
        [sys.executable, str(workflow)],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert completed.returncode != 0
    resolution = _resolution(source)
    assert resolution.state != "unique"
    assert resolution.orientation is None


def test_nonfinite_float_and_decimal_context_paths_abstain(tmp_path: Path) -> None:
    source = """import csv
from decimal import Decimal, getcontext
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
nonfinite = float('nan')
getcontext().prec = 1
score = sum(1 * (Decimal(int(row['call'])) == Decimal(1) - Decimal(row['founder'])) for row in rows)
rate = score / 4
report = f'[selected-result] Of 4 markers, {score} agree. Agreement rate {rate:.6f}. Score {score}. {nonfinite}'
Path('results/report.md').write_text(report, encoding='ascii')
"""
    _assert_released_adapters_match_or_abstain(tmp_path, source, runtime_orientation="repaired")


def test_return_inside_a_nonempty_symbolic_loop_abstains(tmp_path: Path) -> None:
    source = """import csv
from pathlib import Path

def first_score(rows):
    for row in rows:
        return 1 * (int(row['call']) == int(row['founder']))
    return 0

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
score = first_score(rows)
rate = score / 4
report = f'[selected-result] Of 4 markers, {score} agree. Agreement rate {rate:.6f}. Score {score}.'
Path('results/report.md').write_text(report, encoding='ascii')
"""
    _assert_released_adapters_match_or_abstain(tmp_path, source, runtime_orientation="direct")


def test_b6_huge_power_is_bounded_and_the_workflow_still_executes(
    tmp_path: Path,
) -> None:
    source = """import csv
from pathlib import Path

huge = 2 ** 1000000
rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
""" + _report_expression("sum(1 * (int(row['call']) == int(row['founder'])) for row in rows)")
    started = time.monotonic()
    _assert_released_adapters_match_or_abstain(tmp_path, source, runtime_orientation="direct")
    assert time.monotonic() - started < 5


def test_helper_count_budget_abstains_without_quadratic_scanning(tmp_path: Path) -> None:
    helpers = "\n".join(f"def helper_{index}():\n    return {index}" for index in range(257))
    source = (
        "import csv\nfrom pathlib import Path\n"
        + helpers
        + "\nrows = list(csv.DictReader(Path('inputs/markers.csv').open()))\n"
        + _report_expression("sum(1 * (int(row['call']) == int(row['founder'])) for row in rows)")
    )
    started = time.monotonic()
    _assert_released_adapters_match_or_abstain(tmp_path, source, runtime_orientation="direct")
    assert time.monotonic() - started < 5


def test_ast_node_budget_returns_without_quadratic_scanning() -> None:
    prefix = "\n".join(f"ordinary_{index} = {index}" for index in range(7_000))
    source = (
        prefix
        + "\n"
        + """
import csv
from pathlib import Path
rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
score = sum(1 * (int(row['call']) == int(row['founder'])) for row in rows)
report = f'[selected-result] Of 4 markers, {score} agree. Agreement rate 0.750000. Score {score}.'
Path('results/report.md').write_text(report)
"""
    )
    started = time.monotonic()
    resolution = _resolution(source)
    assert resolution.state != "unique"
    assert resolution.orientation is None
    assert time.monotonic() - started < 2


def test_source_byte_budget_precedes_python_parsing() -> None:
    source = "#" + ("x" * 2_000_000)
    started = time.monotonic()
    resolution = _resolution(source)
    assert resolution.state != "unique"
    assert resolution.orientation is None
    assert time.monotonic() - started < 1


def test_unconditional_raise_and_nonterminating_loop_never_reach_a_certificate() -> None:
    suffix = """
import csv
from pathlib import Path
rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
score = sum(1 * (int(row['call']) == int(row['founder'])) for row in rows)
report = f'[selected-result] Of 4 markers, {score} agree. Agreement rate 0.750000. Score {score}.'
Path('results/report.md').write_text(report)
"""
    for prefix in ("raise RuntimeError('stop')\n", "while True:\n    pass\n"):
        started = time.monotonic()
        resolution = _resolution(prefix + suffix)
        assert resolution.state != "unique"
        assert resolution.orientation is None
        assert time.monotonic() - started < 1


def test_public_resolver_keeps_csv_refinement_disabled() -> None:
    context = _inspection_context("report", {"analysis.py": "pass\n"})
    resolution = resolve_founder_orientation_semantic(
        context,
        direct_operand=DIRECT_OPERAND,
        repaired_operand=REPAIRED_OPERAND,
        parser_id="parser:python-ast-tokenize",
        parser_version="1.0.0",
    )
    assert resolution.orientation is None
