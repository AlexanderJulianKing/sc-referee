"""Growth-8 sink-helper, constant-substitution, and frozen-lane regressions."""

from __future__ import annotations

import os
import re
import runpy
import subprocess
from pathlib import Path
from typing import Any

import pytest

from sc_referee.dependence_recognition_v2.adapter import DependenceRecognitionV2ShadowAdapter
from sc_referee.dependence_recognition_v2.python_analyzer import (
    analyze_dependence_growth_python,
)
from scripts.lean_pipeline import (
    ENVELOPE_CONFIGS,
    default_dependence_free_i1_config,
    default_dependence_free_i2_config,
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


def _inspect(source: str, data: bytes = _ADVERSE) -> dict[str, Any]:
    return DependenceRecognitionV2ShadowAdapter().inspect(_context(source, data))


def _execute(source: str, data: bytes, root: Path) -> None:
    if not _RUNTIME.is_file():
        pytest.fail(f"required growth-8 runtime is absent: {_RUNTIME}")
    (root / "inputs").mkdir(parents=True)
    (root / "results").mkdir()
    (root / "workflow").mkdir()
    (root / "inputs/data.csv").write_bytes(data)
    (root / "workflow/analysis.py").write_text(source, encoding="ascii")
    completed = subprocess.run(
        [str(_RUNTIME), "-I", "workflow/analysis.py"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode()


def _with_helper(definition: str, report_expression: str) -> str:
    return (
        _source()
        .replace("def main():", f"{definition}\n\ndef main():")
        .replace("str(result)", report_expression)
    )


def _helper_battery() -> dict[str, tuple[str, str, list[str]]]:
    benign = "def fmt(value):\n    return 'Result: ' + str(value)"
    assigned = (
        _source()
        .replace("def main():", f"{benign}\n\ndef main():")
        .replace(
            '    REPORT.write_text(str(result), encoding="utf-8")',
            '    rendered = fmt(result)\n    REPORT.write_text(rendered, encoding="utf-8")',
        )
    )
    constant = (
        _source()
        .replace("REPORT = Path", 'PREFIX = "Result: "\nREPORT = Path')
        .replace(
            "def main():",
            "def fmt(value):\n    return PREFIX + str(value)\n\ndef main():",
        )
        .replace("str(result)", "fmt(result)")
    )
    shadowed_constant = (
        _source()
        .replace("REPORT = Path", 'PREFIX = "module: "\nREPORT = Path')
        .replace(
            "def main():",
            "def fmt(PREFIX, value):\n    return PREFIX + str(value)\n\ndef main():",
        )
        .replace("str(result)", "fmt('local: ', result)")
    )
    data_name = (
        _source()
        .replace("REPORT = Path", "CACHE = []\nREPORT = Path")
        .replace(
            "def main():",
            "def fmt(value):\n    return str(CACHE) + str(value)\n\ndef main():",
        )
        .replace("str(result)", "fmt(result)")
    )
    second_write = _with_helper(
        "def fmt(value):\n    REPORT.write_text('early', encoding='utf-8')\n    return str(value)",
        "fmt(result)",
    )
    return {
        "A-assigned-benign": (assigned, "evaluation_candidate", []),
        "B-direct-benign": (
            _with_helper(benign, "fmt(result)"),
            "evaluation_candidate",
            [],
        ),
        "C-nested-benign": (
            _with_helper(
                "def inner(value):\n"
                "    return str(value)\n\n"
                "def outer(value):\n"
                "    return 'Result: ' + inner(value)",
                "outer(result)",
            ),
            "evaluation_candidate",
            [],
        ),
        "D-multisite-benign": (
            _with_helper(benign, "fmt(result) + fmt(result)"),
            "evaluation_candidate",
            [],
        ),
        "E-module-constant": (constant, "evaluation_candidate", []),
        "F-constant-shadowed-by-parameter": (
            shadowed_constant,
            "evaluation_candidate",
            [],
        ),
        "G-operand-element-read": (
            _with_helper(
                "def fmt(values, outcome):\n    return str(values[0]) + str(outcome)",
                "fmt(left, result)",
            ),
            "unsupported",
            ["sink-classification-unresolved"],
        ),
        "H-operand-alias": (
            _with_helper(
                "def fmt(values, outcome):\n"
                "    alias = values\n"
                "    return str(alias) + str(outcome)",
                "fmt(left, result)",
            ),
            "unsupported",
            ["sink-aliases-operand-object"],
        ),
        "I-early-clear": (
            _with_helper(
                "def fmt(values, outcome):\n"
                "    values.clear()\n"
                "    return str(values) + str(outcome)",
                "fmt(left, result)",
            ),
            "unsupported",
            ["sink-mutates-operand-name"],
        ),
        "J-early-append": (
            _with_helper(
                "def fmt(values, outcome):\n"
                "    values.append(0.0)\n"
                "    return str(values) + str(outcome)",
                "fmt(left, result)",
            ),
            "unsupported",
            ["sink-mutates-operand-name"],
        ),
        "K-early-pop": (
            _with_helper(
                "def fmt(values, outcome):\n"
                "    values.pop()\n"
                "    return str(values) + str(outcome)",
                "fmt(left, result)",
            ),
            "unsupported",
            ["sink-mutates-operand-name"],
        ),
        "L-second-write": (second_write, "unsupported", ["sink-writes-outside-report"]),
        "M-module-data-name": (data_name, "unsupported", ["module-constant-not-closed"]),
        "N-default-parameter": (
            _with_helper(
                "def fmt(value, prefix='Result: '):\n    return prefix + str(value)",
                "fmt(result)",
            ),
            "unsupported",
            ["function-default-params"],
        ),
        "O-keyword-call": (
            _with_helper(benign, "fmt(value=result)"),
            "unsupported",
            ["function-argument-not-simple"],
        ),
        "P-two-branch-return-detached": (
            _with_helper(
                "def fmt(value):\n"
                "    if value.pvalue < 0.05:\n"
                "        return 'small'\n"
                "    else:\n"
                "        return 'large'",
                "fmt(result)",
            ),
            "unsupported",
            ["function-return-shape"],
        ),
        "Q-early-return-detached": (
            _with_helper(
                "def fmt(value):\n"
                "    if value.pvalue < 0.05:\n"
                "        return 'small'\n"
                "    return 'large'",
                "fmt(result)",
            ),
            "unsupported",
            ["function-return-shape"],
        ),
    }


@pytest.mark.parametrize("case_id", sorted(_helper_battery()))
def test_growth8_helper_form_battery_executes_and_pins_actual_outcome(
    case_id: str, tmp_path: Path
) -> None:
    source, outcome, reasons = _helper_battery()[case_id]
    _execute(source, _ADVERSE, tmp_path / case_id)
    payload = _inspect(source)
    assert payload["outcome"] == outcome
    assert payload["abstention_reasons"] == reasons


def test_growth8_sink_multisite_uses_existing_distinct_call_path_evidence() -> None:
    source = _helper_battery()["D-multisite-benign"][0]
    proposal = analyze_dependence_growth_python(_context(source, _ADVERSE))
    assert proposal.certificate is not None
    sites = {
        (item.call_span, item.call_path_id)
        for item in proposal.certificate.alpha_renames
        if item.function_name == "fmt"
    }
    assert len(sites) == 2


def test_growth8_batches_h1_h2_pin_all_measurable_reason_sets(project_root: Path) -> None:
    expected = {
        "batch-h1": {
            "46f08f48dfee5b1142a4": ["unsupported-import-form"],
            "95b0d17896ce31b504a0": ["import-use-outside-grammar"],
            "a7abfa9adc44baaea6d6": ["unsupported-import-form"],
            "cc45f160070a5cdcd6b9": ["import-use-outside-grammar"],
            "d8e451762e6f79802f9f": ["function-globals-read"],
            "e1c190d24275becc0db4": ["unsupported-import-form"],
        },
        "batch-h2": {
            "0fa763234c3e29b7b57e": ["unsupported-import-form"],
            "2c76f6934e057bc62ce3": ["module-constant-not-closed"],
            "4da6848cdd3a5d975d87": [
                "count-predicate-not-closed",
                "function-globals-read",
                "function-return-shape",
            ],
            "78bfad17cf5492340eb0": [
                "function-default-params",
                "function-globals-read",
                "function-return-shape",
            ],
            "892d8dfacbc80c013262": ["function-argument-not-simple"],
            "c80463fdc728955797e6": ["reader-form-unsupported"],
        },
    }
    growth_root = project_root / "evaluation/development/dependence-growth-loop"
    for batch, cases in expected.items():
        for slug, reasons in cases.items():
            case = growth_root / batch / "authoring/cases" / slug
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
            assert payload["abstention_reasons"] == reasons, (batch, slug, payload)


@pytest.mark.parametrize(
    "factory,suffix,authors,reviewer,hostile,escalation",
    [
        (default_dependence_free_i1_config, "batch-i1", range(99, 105), 40, 41, 25),
        (default_dependence_free_i2_config, "batch-i2", range(105, 111), 42, 43, 26),
    ],
)
def test_growth8_batch_i_envelopes_have_fresh_seats(
    factory: Any,
    suffix: str,
    authors: range,
    reviewer: int,
    hostile: int,
    escalation: int,
) -> None:
    config = factory()
    assert config.pipeline_relative.as_posix().endswith(suffix)
    assert sorted(config.authors) == sorted(
        f"actor:dependence-free-{suffix}-author-opus-{ordinal}" for ordinal in authors
    )
    assert config.reviewer.participant_id.endswith(f"fable-{reviewer}")
    assert config.hostile_answer_key_reviewer is not None
    assert config.hostile_answer_key_reviewer.participant_id.endswith(f"fable-{hostile}")
    assert config.escalation_reviewer.participant_id.endswith(f"opus-{escalation}")
    assert ENVELOPE_CONFIGS[f"dependence-free-{suffix.removeprefix('batch-')}"] is factory
