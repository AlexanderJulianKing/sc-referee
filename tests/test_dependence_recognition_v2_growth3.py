from __future__ import annotations

import os
import re
import runpy
import subprocess
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation import lean_pipeline as evaluation_pipeline

from sc_referee.dependence_recognition_v2.adapter import (
    DependenceRecognitionV2ShadowAdapter,
)
from sc_referee.dependence_recognition_v2.certificate import (
    verify_dependence_growth_certificate,
)
from sc_referee.dependence_recognition_v2.python_analyzer import (
    _trusted_v2_authorizations,
    analyze_dependence_growth_python,
    discharge_dependence_growth_analysis,
)
from scripts.lean_pipeline import (
    default_dependence_free_config,
    default_dependence_free_d_config,
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


def _execute(source: str, data: bytes, tmp_path: Path) -> None:
    if not _RUNTIME.is_file():
        pytest.fail(f"required dependence runtime is absent: {_RUNTIME}")
    root = tmp_path / "case"
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


def _sink_source() -> str:
    return (
        _source()
        .replace("import csv", "import csv\nimport statistics")
        .replace(
            '    REPORT.write_text(str(result), encoding="utf-8")',
            "    summary = statistics.mean(left)\n"
            '    rendered = "mean={mean:.2f}; result={result}".format('
            "mean=summary, result=result)\n"
            '    REPORT.write_text(rendered, encoding="utf-8")',
        )
    )


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (_ADVERSE, "evaluation_candidate"),
        (b"unit_id,arm,value\nu1,A,1\nu2,A,2\nu3,B,3\nu4,B,4\n", "covered_negative"),
    ],
)
def test_sink_bound_positive_fixtures_execute_and_certify(
    data: bytes, expected: str, tmp_path: Path
) -> None:
    source = _sink_source()
    _execute(source, data, tmp_path)
    assert _inspect(source, data)["outcome"] == expected


def test_multisite_operand_helper_has_distinct_call_path_evidence(tmp_path: Path) -> None:
    source = (
        _source()
        .replace("def main():", "def select(groups, key):\n    return groups[key]\n\ndef main():")
        .replace(
            "    left = groups[LEFT]\n    right = groups[RIGHT]",
            "    left = select(groups, LEFT)\n    right = select(groups, RIGHT)",
        )
    )
    _execute(source, _ADVERSE, tmp_path)
    analysis = analyze_dependence_growth_python(_context(source, _ADVERSE))
    assert analysis.certificate is not None
    sites = {
        (item.call_span, item.call_path_id)
        for item in analysis.certificate.alpha_renames
        if item.function_name == "select"
    }
    assert len(sites) == 2
    assert _inspect(source)["outcome"] == "evaluation_candidate"


def test_kernel_rejects_identical_multisite_identity_and_rename_collision() -> None:
    source = (
        _source()
        .replace("def main():", "def select(groups, key):\n    return groups[key]\n\ndef main():")
        .replace(
            "    left = groups[LEFT]\n    right = groups[RIGHT]",
            "    left = select(groups, LEFT)\n    right = select(groups, RIGHT)",
        )
    )
    context = _context(source, _ADVERSE)
    proposal = analyze_dependence_growth_python(context)
    discharged = discharge_dependence_growth_analysis(proposal, context)
    assert discharged.verified_certificate is not None
    certificate = proposal.certificate
    assert certificate is not None
    renames = list(certificate.alpha_renames)
    second = next(index for index, item in enumerate(renames) if "select:3" in item.call_path_id)
    first = next(item for item in renames if "select:2" in item.call_path_id)
    renames[second] = replace(
        renames[second], call_path_id=first.call_path_id, call_span=first.call_span
    )
    failures: list[str] = []
    assert (
        verify_dependence_growth_certificate(
            replace(certificate, alpha_renames=tuple(renames)),
            trusted_group_facts=(discharged.verified_certificate.fact,),
            trusted_authorizations=_trusted_v2_authorizations(context),
            source_bytes=context.documents[0].content,
            _failure_reasons=failures,
        )
        is None
    )
    assert failures == ["rename-injectivity"]
    author_collision = _source().replace(
        "def main():", "def main():\n    __dependence_v2_1_collision = 1"
    )
    assert _inspect(author_collision)["abstention_reasons"] == ["function-rename-collision"]


def test_defaultdict_list_certifies_and_phantom_key_abstains(tmp_path: Path) -> None:
    source = (
        _source()
        .replace("import csv", "import csv\nfrom collections import defaultdict")
        .replace("    groups = {}", "    groups = defaultdict(list)")
        .replace('groups.setdefault(row["arm"], []).append', 'groups[row["arm"]].append')
    )
    _execute(source, _ADVERSE, tmp_path / "list")
    assert _inspect(source)["outcome"] == "evaluation_candidate"
    phantom = source.replace("left = groups[LEFT]", 'left = groups["missing"]')
    _execute(phantom, _ADVERSE, tmp_path / "phantom")
    assert _inspect(phantom)["abstention_reasons"] == ["defaultdict-key-not-proven"]
    unpacked = source.replace(
        "    left = groups[LEFT]\n    right = groups[RIGHT]",
        "    (_, left), (_, right) = sorted(groups.items())",
    )
    _execute(unpacked, _ADVERSE, tmp_path / "unpacked")
    assert _inspect(unpacked)["abstention_reasons"] == ["defaultdict-key-not-proven"]
    for factory in ("set", "int"):
        refused = source.replace("defaultdict(list)", f"defaultdict({factory})")
        if factory == "set":
            refused = refused.replace(
                'groups[row["arm"]].append(float(row["value"]))',
                'groups[row["arm"]].add(float(row["value"]))',
            )
            refused = refused.replace("left = groups[LEFT]", "left = list(groups[LEFT])")
            refused = refused.replace("right = groups[RIGHT]", "right = list(groups[RIGHT])")
        else:
            refused = refused.replace(
                'groups[row["arm"]].append(float(row["value"]))',
                'groups[row["arm"]] += int(float(row["value"]))',
            )
            refused = refused.replace("left = groups[LEFT]", "left = [groups[LEFT]]")
            refused = refused.replace("right = groups[RIGHT]", "right = [groups[RIGHT]]")
        _execute(refused, _ADVERSE, tmp_path / factory)
        assert _inspect(refused)["abstention_reasons"] == ["group-container-not-list"]


@pytest.mark.parametrize(
    ("replacement", "reason"),
    [
        (
            "    summary = statistics.mean(left)\n    left.append(summary)\n"
            '    REPORT.write_text(str(result) + str(summary), encoding="utf-8")',
            "sink-mutates-operand-name",
        ),
        (
            "    summary = statistics.mean(left)\n    rendered = set([summary])\n"
            '    REPORT.write_text(str(result) + str(rendered), encoding="utf-8")',
            "sink-helper-call",
        ),
        (
            "    summary = sorted(left, key=str)\n"
            '    REPORT.write_text(str(result) + str(summary), encoding="utf-8")',
            "sink-call-keyword-argument",
        ),
        (
            "    summary = statistics.mean(left)\n"
            '    Path("results/other.md").write_text(str(summary), encoding="utf-8")\n'
            '    REPORT.write_text(str(result), encoding="utf-8")',
            "sink-writes-outside-report",
        ),
    ],
)
def test_sink_routes_abstain_with_granular_reason(
    replacement: str, reason: str, tmp_path: Path
) -> None:
    source = (
        _source()
        .replace("import csv", "import csv\nimport statistics")
        .replace('    REPORT.write_text(str(result), encoding="utf-8")', replacement)
    )
    _execute(source, _ADVERSE, tmp_path)
    assert _inspect(source)["abstention_reasons"] == [reason]


def test_conditional_procedure_and_depth_four_abstain(tmp_path: Path) -> None:
    conditional = _source().replace(
        "    result = stats.ttest_ind(left, right)",
        "    if len(left) > 0:\n        result = stats.ttest_ind(left, right)",
    )
    _execute(conditional, _ADVERSE, tmp_path / "conditional")
    assert _inspect(conditional)["abstention_reasons"] == ["sink-controls-operand-flow"]
    deep = _source().replace(
        "def main():",
        "def h4():\n    return 1\n\ndef h3():\n    h4()\n\ndef h2():\n    h3()\n\n"
        "def h1():\n    h2()\n\ndef main():\n    h1()",
    )
    _execute(deep, _ADVERSE, tmp_path / "deep")
    assert _inspect(deep)["abstention_reasons"] == ["function-inline-depth-exceeded"]

    sink_helper = (
        _source()
        .replace(
            "def main():",
            'def render(value):\n    return "result={}".format(value)\n\ndef main():',
        )
        .replace(
            '    REPORT.write_text(str(result), encoding="utf-8")',
            '    rendered = render(result)\n    REPORT.write_text(rendered, encoding="utf-8")',
        )
    )
    _execute(sink_helper, _ADVERSE, tmp_path / "sink-helper")
    assert _inspect(sink_helper)["abstention_reasons"] == ["sink-helper-call"]


@pytest.mark.parametrize("value", ["99.0", "-1000000.0"])
def test_alias_then_mutate_variants_permanently_abstain(value: str, tmp_path: Path) -> None:
    source = _source().replace(
        '    REPORT.write_text(str(result), encoding="utf-8")',
        f"    shadow = left\n    shadow.append({value})\n"
        '    REPORT.write_text(str(result) + str(shadow), encoding="utf-8")',
    )
    _execute(source, _ADVERSE, tmp_path)
    payload = _inspect(source)
    assert payload["outcome"] == "unsupported"
    assert payload["abstention_reasons"] == ["sink-aliases-operand-object"]


def test_sink_flow_escape_unknown_method_and_raising_sink_routes(tmp_path: Path) -> None:
    escaped = _source().replace(
        '    REPORT.write_text(str(result), encoding="utf-8")',
        '    summary = sum(left)\n    rows[0]["summary"] = summary\n'
        '    REPORT.write_text(str(result) + str(summary), encoding="utf-8")',
    )
    _execute(escaped, _ADVERSE, tmp_path / "escape")
    assert _inspect(escaped)["abstention_reasons"] == ["sink-flow-escapes"]
    unknown = _source().replace(
        '    REPORT.write_text(str(result), encoding="utf-8")',
        '    rendered = "x".encode()\n'
        '    REPORT.write_text(str(result) + str(rendered), encoding="utf-8")',
    )
    _execute(unknown, _ADVERSE, tmp_path / "unknown")
    assert _inspect(unknown)["abstention_reasons"] == ["sink-call-not-whitelisted"]
    raising = _source().replace(
        '    REPORT.write_text(str(result), encoding="utf-8")',
        "    ratio = 1 / len(left)\n"
        '    REPORT.write_text(str(result) + str(ratio), encoding="utf-8")',
    )
    _execute(raising, _ADVERSE, tmp_path / "raising-capable")
    # The expression can raise for an empty operand; flow certification makes
    # no claim about that value-level execution behavior.
    assert _inspect(raising)["outcome"] == "evaluation_candidate"

    wording_branch = _source().replace(
        '    REPORT.write_text(str(result), encoding="utf-8")',
        '    summary = sum(left)\n    if summary > 0:\n        wording = "positive"\n'
        '    else:\n        wording = "nonpositive"\n'
        '    REPORT.write_text(str(result) + wording, encoding="utf-8")',
    )
    _execute(wording_branch, _ADVERSE, tmp_path / "wording")
    assert _inspect(wording_branch)["outcome"] == "evaluation_candidate"


@pytest.mark.parametrize("expression", ["sorted(left)", "list(left)", "left[:]"])
def test_fresh_scalar_container_principle_is_uniform(expression: str, tmp_path: Path) -> None:
    source = _source().replace(
        '    REPORT.write_text(str(result), encoding="utf-8")',
        f"    copied = {expression}\n"
        '    REPORT.write_text(str(result) + str(copied), encoding="utf-8")',
    )
    _execute(source, _ADVERSE, tmp_path)
    assert _inspect(source)["outcome"] == "evaluation_candidate"


def test_container_holding_operand_object_is_not_sink_bound(tmp_path: Path) -> None:
    source = _source().replace(
        '    REPORT.write_text(str(result), encoding="utf-8")',
        '    nested = [left]\n    REPORT.write_text(str(result) + str(nested), encoding="utf-8")',
    )
    _execute(source, _ADVERSE, tmp_path)
    assert _inspect(source)["abstention_reasons"] == ["sink-classification-unresolved"]


def test_batch_c_full_sorted_observed_sets_and_rq6_guard(project_root: Path) -> None:
    expected = {
        "0815b8de6b7fd34cdbfc": ["module-constant-not-closed"],
        "41cfd59360a1ca24ca4b": ["module-constant-not-closed"],
        "5eeb6e5adc4fc675c771": ["module-constant-not-closed"],
        "822e4d560d778dc26fb0": ["unsupported-import-form"],
        "b98cd6e8d9f893450053": ["module-constant-not-closed"],
        "d674ebb8c31ed83be287": ["function-entry-not-closed", "sink-helper-call"],
    }
    root = project_root / "evaluation/development/dependence-growth-loop/batch-c/authoring/cases"
    for slug, reasons in expected.items():
        case = root / slug
        description = (case / "data-description.md").read_text(encoding="utf-8")
        unit = re.search(r"(?mi)^Independent unit column:[ \t]*([^\r\n]+)", description)
        assert unit is not None
        payload = DependenceRecognitionV2ShadowAdapter().inspect(
            _context(
                (case / "workflow/analysis.py").read_text(encoding="ascii"),
                (case / "data/input.csv").read_bytes(),
                unit_column=unit.group(1).strip(),
                data_path="data/input.csv",
            )
        )
        assert payload["abstention_reasons"] == reasons
    rq6 = project_root / (
        "evaluation/development/dependence-growth-loop/batch-b/authoring/cases/6a3bc02816cb70ee4042"
    )
    unit = re.search(
        r"(?mi)^Independent unit column:[ \t]*([^\r\n]+)",
        (rq6 / "data-description.md").read_text(encoding="utf-8"),
    )
    assert unit is not None
    payload = DependenceRecognitionV2ShadowAdapter().inspect(
        _context(
            (rq6 / "workflow/analysis.py").read_text(encoding="ascii"),
            (rq6 / "data/input.csv").read_bytes(),
            unit_column=unit.group(1).strip(),
            data_path="data/input.csv",
        )
    )
    assert payload["outcome"] not in {"evaluation_candidate", "covered_negative"}
    assert payload["abstention_reasons"] == ["module-constant-not-closed"]


def test_batch_d_config_and_claude_schema_option_are_closed() -> None:
    config = default_dependence_free_d_config()
    assert config.envelope_id == "development-dependence-growth-loop-batch-d-v1"
    assert config.pipeline_relative.as_posix().endswith("batch-d")
    assert config.dependence_v2_development_shadow
    assert config.dependence_v2_lock_line
    assert config.enforce_cli_review_json_schema
    assert sorted(config.authors) == [
        f"actor:dependence-free-batch-d-author-opus-{item}" for item in range(45, 51)
    ]
    assert config.reviewer.participant_id.endswith("fable-22")
    assert config.hostile_answer_key_reviewer is not None
    assert config.hostile_answer_key_reviewer.participant_id.endswith("fable-23")
    assert config.escalation_reviewer.participant_id.endswith("opus-16")
    help_text = subprocess.run(
        [str(config.cli_binary), "--help"], capture_output=True, text=True, check=True
    ).stdout
    assert "--json-schema" in help_text


def test_batch_d_transport_passes_schema_without_changing_default(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config = default_dependence_free_d_config()
    participant = config.reviewer
    observed: list[str] = []

    def fake_run(argv: list[str], **_: object) -> subprocess.CompletedProcess[bytes]:
        observed.extend(argv)
        payload = {
            "is_error": False,
            "session_id": "session",
            "modelUsage": {participant.model_id: {}},
            "result": '{"ok":true}',
        }
        return subprocess.CompletedProcess(
            argv, 0, str.encode(__import__("json").dumps(payload)), b""
        )

    monkeypatch.setattr(evaluation_pipeline.subprocess, "run", fake_run)
    schema = {"type": "object", "properties": {"ok": {"type": "boolean"}}}
    result = evaluation_pipeline._call_cli(
        config, participant, "prompt", "session", tmp_path / "capture", response_schema=schema
    )
    assert result["transport_error"] is None
    assert observed[observed.index("--json-schema") + 1] == evaluation_pipeline.canonical_json(
        schema
    )
    assert default_dependence_free_d_config().development_loop
    assert not default_dependence_free_config().enforce_cli_review_json_schema
