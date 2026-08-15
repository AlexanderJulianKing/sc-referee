"""Growth-9 amended vocabulary, argument-hoist, and checkpoint regressions."""

from __future__ import annotations

import ast
import os
import re
import runpy
import subprocess
from pathlib import Path
from typing import Any, cast

import pytest

from sc_referee.dependence_recognition_v2.adapter import DependenceRecognitionV2ShadowAdapter
from sc_referee.dependence_recognition_v2.python_analyzer import _flatten_functions, _module_parts
from scripts.lean_pipeline import (
    ENVELOPE_CONFIGS,
    default_dependence_free_j1_config,
    default_dependence_free_j2_config,
)

_BASE = runpy.run_path(str(Path(__file__).with_name("test_dependence_recognition_v2.py")))
_source = _BASE["_source"]
_context = _BASE["_context"]
_ADVERSE = _BASE["_ADVERSE"]
_RUNTIME = Path(
    os.environ.get(
        "DEPENDENCE_SANDBOX_PYTHON",
        "/Users/alexanderking/Desktop/random_stuff/sc-referee-pilot-runtime/"
        "scipy114-venv/bin/python",
    )
)


def _inspect(source: str) -> dict[str, Any]:
    return DependenceRecognitionV2ShadowAdapter().inspect(_context(source, _ADVERSE))


def _execute(source: str, root: Path) -> None:
    if not _RUNTIME.is_file():
        pytest.fail(f"required growth-9 runtime is absent: {_RUNTIME}")
    (root / "inputs").mkdir(parents=True)
    (root / "results").mkdir()
    (root / "workflow").mkdir()
    (root / "inputs/data.csv").write_bytes(_ADVERSE)
    (root / "workflow/analysis.py").write_text(source, encoding="ascii")
    completed = subprocess.run(
        [str(_RUNTIME), "-I", "workflow/analysis.py"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode()


def _helper_source(
    arguments: str, definition: str = "def fmt(a, result):\n    return str(a) + str(result)"
) -> str:
    rewritten = _source().replace("str(result)", f"fmt({arguments})")
    return rewritten.replace("def main():", f"{definition}\n\ndef main():")


def _battery() -> dict[str, tuple[str, str, list[str]]]:
    reader_copy = _source().replace(
        "rows = list(csv.DictReader(handle))",
        "rows = [dict(row) for row in csv.DictReader(handle)]",
    )
    list_constant = (
        _source()
        .replace('LEFT = "A"\nRIGHT = "B"', 'ORDER = ["A", "B"]')
        .replace("groups[LEFT]", "groups[ORDER[0]]")
        .replace("groups[RIGHT]", "groups[ORDER[1]]")
    )
    sink_builtins = _source().replace(
        "str(result)", "str(tuple(left)) + str(any(left)) + str(all(right)) + str(result)"
    )
    raise_guard = _source().replace(
        "    groups = {}", "    if not rows:\n        raise ValueError('empty')\n    groups = {}"
    )
    return {
        "A-reader-dict-copy": (reader_copy, "evaluation_candidate", []),
        "B-list-module-constant": (list_constant, "evaluation_candidate", []),
        "C-builtins-on-sink": (sink_builtins, "evaluation_candidate", []),
        "D-raise-guard-wall": (raise_guard, "unsupported", ["raise-guard-not-modeled"]),
        "E-pure-expression-hoist": (
            _helper_source("len(left), result"),
            "evaluation_candidate",
            [],
        ),
        "F-subscript-container-hoist": (
            _helper_source("groups['A'], result"),
            "unsupported",
            ["sink-aliases-operand-object"],
        ),
        "G-bare-container-hoist": (
            _helper_source(
                "left, len(right) + 0, result",
                "def fmt(a, b, result):\n    return str(a) + str(b) + str(result)",
            ),
            "unsupported",
            ["sink-aliases-operand-object"],
        ),
        "H-non-S3-nested-call": (
            _helper_source("print(result), result"),
            "unsupported",
            ["function-argument-not-simple"],
        ),
        "I-starred-call": (
            _helper_source(
                "*[result, result]",
                "def fmt(a, b):\n    return str(a) + str(b)",
            ),
            "unsupported",
            ["function-argument-starred"],
        ),
    }


@pytest.mark.parametrize("case_id", sorted(_battery()))
def test_growth9_amended_fixture_battery_executes_and_pins_observed_outcome(
    case_id: str, tmp_path: Path
) -> None:
    source, outcome, reasons = _battery()[case_id]
    _execute(source, tmp_path / case_id)
    payload = _inspect(source)
    assert payload["outcome"] == outcome
    assert payload["abstention_reasons"] == reasons


def test_growth9_argument_hoists_preserve_left_to_right_source_order() -> None:
    source = _helper_source("len(left), max(right)")
    imports, constants, functions, executable = _module_parts(ast.parse(source))
    flattened, _renames, _dead = _flatten_functions(executable, functions, constants, imports)
    hoists = [
        statement
        for statement in flattened
        if isinstance(statement, ast.Assign)
        and isinstance(statement.targets[0], ast.Name)
        and statement.targets[0].id.startswith("__dependence_v2_argument_")
    ]
    assert [cast(ast.Call, statement.value).func.id for statement in hoists] == ["len", "max"]
    names = [
        ast.unparse(cast(ast.Call, statement.value).args[0]).rsplit("_", 1)[-1]
        for statement in hoists
    ]
    assert names == ["left", "right"]


def test_growth9_batch_i_target_cases_pin_honest_next_walls(project_root: Path) -> None:
    expected = {
        "125813c0f228fcecd435": ["raise-guard-not-modeled"],
        "1469a50a5381493a261b": ["group-accumulator-not-total"],
        "256ce9b8dd475ee95a97": ["count-domain-not-row-bound"],
        "5f4ec238d04074266e32": ["reader-form-unsupported"],
        "6aac19a2a2aa18f85740": ["raise-guard-not-modeled"],
        # Tuple-unpacked procedure results remain outside this round; see the
        # explicit growth-9 fuel-order entry in SCHEMA_GAP_REGISTER.md.
        "ce7daed01bb0fa178e26": ["procedure-call-unresolved"],
    }
    root = project_root / "evaluation/development/dependence-growth-loop"
    cases = {
        case.name: case
        for batch in ("batch-i1", "batch-i2")
        for case in (root / batch / "authoring/cases").iterdir()
        if case.name in expected
    }
    assert set(cases) == set(expected)
    for slug, reasons in expected.items():
        case = cases[slug]
        description = (case / "data-description.md").read_text(encoding="utf-8")
        match = re.search(r"(?mi)^Independent unit column:[ \t]*([^\r\n]+)", description)
        assert match is not None
        payload = DependenceRecognitionV2ShadowAdapter().inspect(
            _context(
                (case / "workflow/analysis.py").read_text(encoding="utf-8"),
                (case / "data/input.csv").read_bytes(),
                unit_column=match.group(1).strip(),
                data_path="data/input.csv",
            )
        )
        assert payload["abstention_reasons"] == reasons, (slug, payload)


@pytest.mark.parametrize(
    "factory,suffix,authors,reviewer,hostile,escalation",
    [
        (default_dependence_free_j1_config, "batch-j1", range(111, 117), 44, 45, 27),
        (default_dependence_free_j2_config, "batch-j2", range(117, 123), 46, 47, 28),
    ],
)
def test_growth9_batch_j_checkpoint_envelopes_are_ready_and_unrun(
    project_root: Path,
    factory: Any,
    suffix: str,
    authors: range,
    reviewer: int,
    hostile: int,
    escalation: int,
) -> None:
    config = factory()
    assert config.pipeline_relative.as_posix().endswith(suffix)
    assert not (project_root / config.pipeline_relative).exists()
    assert sorted(config.authors) == sorted(
        f"actor:dependence-free-{suffix}-author-opus-{ordinal}" for ordinal in authors
    )
    assert config.reviewer.participant_id.endswith(f"fable-{reviewer}")
    assert config.hostile_answer_key_reviewer is not None
    assert config.hostile_answer_key_reviewer.participant_id.endswith(f"fable-{hostile}")
    assert config.escalation_reviewer.participant_id.endswith(f"opus-{escalation}")
    assert ENVELOPE_CONFIGS[f"dependence-free-{suffix.removeprefix('batch-')}"] is factory
