from __future__ import annotations

import os
import re
import runpy
import subprocess
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft7Validator
from sc_referee_evaluation import lean_pipeline as evaluation_pipeline

from sc_referee.core.ids import semantic_digest, sha256_digest
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
    default_dependence_free_e1_config,
    default_dependence_free_e2_config,
    default_dependence_free_f1_config,
    default_dependence_free_f2_config,
    default_dependence_free_g1_config,
    default_dependence_free_g2_config,
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


def test_kernel_rejects_swapped_positive_rename_mapping_at_rename_obligation() -> None:
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
    first, second = next(
        (left, right)
        for left in range(len(renames))
        for right in range(left + 1, len(renames))
        if renames[left].original_name == renames[right].original_name
        and renames[left].call_path_id != renames[right].call_path_id
    )
    renames[first] = replace(renames[first], fresh_name=renames[second].fresh_name)
    renames[second] = replace(
        renames[second], fresh_name=certificate.alpha_renames[first].fresh_name
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
    one_observed_group = b"unit_id,arm,value\nu1,A,1\nu2,A,2\n"
    assert _inspect(phantom, one_observed_group)["abstention_reasons"] == [
        "defaultdict-key-not-proven"
    ]
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
        expected = (
            "augmented-assignment-not-modeled" if factory == "int" else "group-container-not-list"
        )
        assert _inspect(refused)["abstention_reasons"] == [expected]


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
            "sink-call-not-whitelisted",
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
    assert _inspect(sink_helper)["outcome"] == "evaluation_candidate"


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


@pytest.mark.parametrize(
    ("statement", "reason"),
    [
        ("left: list = [0.0]", "operand-name-rebound"),
        ("left += [0.0]", "augmented-assignment-not-modeled"),
        ("(left := [0.0])", "named-expression-not-modeled"),
        ("del left", "delete-not-modeled"),
    ],
)
def test_unmodeled_operand_rebinding_statements_abstain(statement: str, reason: str) -> None:
    source = _source().replace(
        "    right = groups[RIGHT]", f"    {statement}\n    right = groups[RIGHT]"
    )
    payload = _inspect(source)
    assert payload["outcome"] == "unsupported"
    assert payload["abstention_reasons"] == [reason]


def test_group_kernel_live_syntax_guard_rejects_annotated_rebind() -> None:
    context = _context(_source(), _ADVERSE)
    analysis = analyze_dependence_growth_python(context)
    discharged = discharge_dependence_growth_analysis(analysis, context)
    verified = discharged.verified_certificate
    assert analysis.certificate is not None
    assert verified is not None
    certificate = replace(
        analysis.certificate,
        certificate_id=verified.certificate_id,
        operand_bindings=verified.operand_bindings,
        conclusion=verified.conclusion,
    )
    unsafe_bytes = context.documents[0].content.replace(
        b"    left = groups[LEFT]", b"    left = groups[LEFT]; left: list = [0.0]"
    )
    unsafe_digest = sha256_digest(unsafe_bytes)
    unsafe_certificate = replace(
        certificate,
        source_digest=unsafe_digest,
        source_extent=(0, len(unsafe_bytes)),
    )
    unsafe_certificate = replace(
        unsafe_certificate,
        certificate_id="dependence-growth-certificate:"
        + semantic_digest(
            {
                "source_digest": unsafe_digest,
                "fact": verified.fact.evidence_id,
                "bindings": [
                    {
                        "position": item.position,
                        "argument_name": item.argument_name,
                        "group_key": item.group_key,
                    }
                    for item in unsafe_certificate.operand_bindings
                ],
                "conclusion": unsafe_certificate.conclusion,
            }
        ),
    )
    assert (
        verify_dependence_growth_certificate(
            unsafe_certificate,
            trusted_group_facts=(verified.fact,),
            trusted_authorizations=_trusted_v2_authorizations(context),
            source_bytes=unsafe_bytes,
        )
        is None
    )
    reader_rebind = context.documents[0].content.replace(
        b"        rows = list(csv.DictReader(handle))",
        b"        rows = list(csv.DictReader(handle))\n    rows: list = rows[:4]",
    )
    reader_digest = sha256_digest(reader_rebind)
    reader_certificate = replace(
        certificate,
        source_digest=reader_digest,
        source_extent=(0, len(reader_rebind)),
    )
    reader_certificate = replace(
        reader_certificate,
        certificate_id="dependence-growth-certificate:"
        + semantic_digest(
            {
                "source_digest": reader_digest,
                "fact": verified.fact.evidence_id,
                "bindings": [
                    {
                        "position": item.position,
                        "argument_name": item.argument_name,
                        "group_key": item.group_key,
                    }
                    for item in reader_certificate.operand_bindings
                ],
                "conclusion": reader_certificate.conclusion,
            }
        ),
    )
    assert (
        verify_dependence_growth_certificate(
            reader_certificate,
            trusted_group_facts=(verified.fact,),
            trusted_authorizations=_trusted_v2_authorizations(context),
            source_bytes=reader_rebind,
        )
        is None
    )


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
    unknown_name = _source().replace(
        '    REPORT.write_text(str(result), encoding="utf-8")',
        '    rendered = mystery(result)\n    REPORT.write_text(str(rendered), encoding="utf-8")',
    )
    unknown_payload = _inspect(unknown_name)
    assert unknown_payload["abstention_reasons"] == ["sink-call-not-whitelisted"]
    assert "function-globals-read" not in unknown_payload["abstention_reasons"]
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


@pytest.mark.parametrize(
    "expression",
    ["min(left)", "max(left)", "round(sum(left), 2)", "abs(sum(left))"],
)
def test_scalar_sink_callable_whitelist_certifies(expression: str, tmp_path: Path) -> None:
    source = _source().replace(
        '    REPORT.write_text(str(result), encoding="utf-8")',
        f"    summary = {expression}\n"
        '    REPORT.write_text(str(result) + str(summary), encoding="utf-8")',
    )
    _execute(source, _ADVERSE, tmp_path)
    assert _inspect(source)["outcome"] == "evaluation_candidate"


def test_fresh_sorted_subscript_certifies_symmetrically(tmp_path: Path) -> None:
    source = _source().replace(
        '    REPORT.write_text(str(result), encoding="utf-8")',
        "    smallest = sorted(left)[0]\n"
        '    REPORT.write_text(str(result) + str(smallest), encoding="utf-8")',
    )
    _execute(source, _ADVERSE, tmp_path)
    analysis = analyze_dependence_growth_python(_context(source, _ADVERSE))
    assert analysis.certificate is not None
    discharged = discharge_dependence_growth_analysis(analysis, _context(source, _ADVERSE))
    assert discharged.verified_certificate is not None
    assert _inspect(source)["outcome"] == "evaluation_candidate"


def test_unused_bare_operand_alias_reports_identity_reason() -> None:
    source = _source().replace(
        '    REPORT.write_text(str(result), encoding="utf-8")',
        '    unused_alias = left\n    REPORT.write_text(str(result), encoding="utf-8")',
    )
    assert _inspect(source)["abstention_reasons"] == ["sink-aliases-operand-object"]


def test_container_holding_operand_object_is_not_sink_bound(tmp_path: Path) -> None:
    source = _source().replace(
        '    REPORT.write_text(str(result), encoding="utf-8")',
        '    nested = [left]\n    REPORT.write_text(str(result) + str(nested), encoding="utf-8")',
    )
    _execute(source, _ADVERSE, tmp_path)
    assert _inspect(source)["abstention_reasons"] == ["sink-classification-unresolved"]


def test_batches_a_through_f_full_sorted_observed_sets_and_rq6_guard(project_root: Path) -> None:
    expected_by_batch = {
        "batch-a": {
            "112bd1e61aa4fc1bec86": ["module-constant-not-closed"],
            "6da5419523f5f9dbedf9": ["function-return-shape"],
            "76373b4a2b2f380d43da": ["unsupported-import-form"],
            "a520ddbd23df9d699e60": ["dataclass-use-not-modeled"],
            "d1d4ed0e518ad533a2dc": ["reader-form-unsupported"],
            "e2ecaca2651276963b12": ["unsupported-import-form"],
        },
        "batch-b": {
            "3c2b93c9545d8518e1f3": ["function-globals-read"],
            "446cab155cd792398f9d": ["count-predicate-not-closed", "reader-form-unsupported"],
            "6a3bc02816cb70ee4042": ["import-use-outside-grammar"],
            "8b01b6d08e58aa5cce6f": ["raise-guard-not-modeled"],
            "ae04f2973df030f612b9": ["function-globals-read"],
            "bf08b2218ca9cef1db2d": [
                "count-predicate-not-closed",
                "raise-guard-not-modeled",
            ],
        },
        "batch-c": {
            "0815b8de6b7fd34cdbfc": ["import-use-outside-grammar"],
            "41cfd59360a1ca24ca4b": ["function-return-shape", "raise-guard-not-modeled"],
            "5eeb6e5adc4fc675c771": ["module-collection-use-not-modeled"],
            "822e4d560d778dc26fb0": ["unsupported-import-form"],
            "b98cd6e8d9f893450053": ["import-use-outside-grammar"],
            "d674ebb8c31ed83be287": ["group-accumulator-not-total"],
        },
        "batch-d": {
            "396f4dceee2b19f08009": ["dataclass-use-not-modeled"],
            "465d8368b0cdc3b167fd": ["module-collection-use-not-modeled"],
            "6e47ef090eb8989d547d": ["function-return-shape"],
            "7da68ec265e1bb2f6640": ["raise-guard-not-modeled"],
            "f75b02bd61e813195904": ["unsupported-import-form"],
        },
        "batch-e1": {
            "407236062264ca895ef3": ["import-use-outside-grammar"],
            "47b6fb6bf1d4fbcefd7c": ["reader-form-unsupported"],
            "7afb4508b0d957f51ca7": ["function-return-shape"],
            "acea1e7265fd2ac91a43": [
                "function-globals-read",
                "raise-guard-not-modeled",
            ],
            "d3f093e9da995ca1027a": ["group-accumulator-not-total"],
            "f203d7292f9530cbdf48": ["raise-guard-not-modeled"],
        },
        "batch-e2": {
            "102f7842bc112abba84f": ["raise-guard-not-modeled"],
            "128c2bd7128bc67b5964": ["function-argument-not-simple"],
            "18f0af8326d59d579c43": [
                "function-return-shape",
                "raise-guard-not-modeled",
            ],
            "c38b4b95d2ca5a382f67": [
                "function-closure",
                "function-return-shape",
            ],
            "e57e3c73264eda49b3cc": ["raise-guard-not-modeled"],
            "fa5259eb594c121b4dac": ["function-argument-not-simple"],
        },
        "batch-f1": {
            "99fa42046e8fc8cc47de": ["function-return-shape"],
            "9d4a9dcdc2ab130e6736": ["function-return-shape"],
            "c2db115846830b7d908c": ["raise-guard-not-modeled"],
            "ca3125c6ca6002055d70": ["import-use-outside-grammar"],
            "ce821630fbd906ad6d07": ["module-constant-not-closed"],
            "f68415be40b9234987de": ["raise-guard-not-modeled"],
        },
        "batch-f2": {
            "605c4c08512e4489cc9a": [
                "count-predicate-not-closed",
                "raise-guard-not-modeled",
            ],
            "7fa9d7c060555eac5a49": ["unsupported-import-form"],
            "b24355b160cf4665b929": ["raise-guard-not-modeled"],
            "b511aff6f2e4b54ee5ce": ["function-globals-read"],
            "d288f3b6bbda69d32acf": ["module-constant-not-closed"],
            "e0b267c13e8a30d07b48": ["function-globals-read", "function-return-shape"],
        },
    }
    for batch, expected in expected_by_batch.items():
        root = (
            project_root
            / "evaluation/development/dependence-growth-loop"
            / batch
            / "authoring/cases"
        )
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
            assert payload["abstention_reasons"] == reasons, (batch, slug, payload)
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
    assert payload["abstention_reasons"] == ["import-use-outside-grammar"]


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


def test_growth4_inert_imports_and_literal_path_division_are_closed(tmp_path: Path) -> None:
    future_source = "from __future__ import annotations\n" + _source()
    _execute(future_source, _ADVERSE, tmp_path / "future")
    assert _inspect(future_source)["outcome"] == "evaluation_candidate"
    other_future = future_source.replace("annotations", "division", 1)
    assert _inspect(other_future)["abstention_reasons"] == ["unsupported-import-form"]

    unused_dataclass = _source().replace(
        "import csv", "import csv\nfrom dataclasses import dataclass"
    )
    _execute(unused_dataclass, _ADVERSE, tmp_path / "unused-dataclass")
    assert _inspect(unused_dataclass)["outcome"] == "evaluation_candidate"
    used_dataclass = unused_dataclass.replace(
        "def main():", "@dataclass\nclass Marker:\n    value: int\n\ndef main():"
    )
    assert _inspect(used_dataclass)["abstention_reasons"] == ["dataclass-use-not-modeled"]
    plain_class = _source().replace("def main():", "class Marker:\n    pass\n\ndef main():")
    assert _inspect(plain_class)["abstention_reasons"] == ["function-entry-not-closed"]

    divided_paths = (
        _source()
        .replace('INPUT = Path("inputs/data.csv")', 'INPUT = Path("inputs") / "data.csv"')
        .replace(
            'REPORT = Path("results/report.md")',
            'REPORT = Path("results") / "" / "report.md"',
        )
    )
    _execute(divided_paths, _ADVERSE, tmp_path / "divided")
    assert _inspect(divided_paths)["outcome"] == "evaluation_candidate"
    named_segment = divided_paths.replace(
        'INPUT = Path("inputs") / "data.csv"',
        'SEGMENT = "data.csv"\nINPUT = Path("inputs") / SEGMENT',
    )
    assert _inspect(named_segment)["abstention_reasons"] == ["module-constant-not-closed"]
    wrong_path = divided_paths.replace(
        'INPUT = Path("inputs") / "data.csv"', 'INPUT = Path("inputs") / "other.csv"'
    )
    assert _inspect(wrong_path)["abstention_reasons"] == ["group-domain-binding-mismatch"]


@pytest.mark.parametrize(
    ("declarations", "left", "right"),
    [
        ('BANDS = ("A", "B")', "BANDS[0]", "BANDS[1]"),
        ('BANDS = {"left": "A", "right": "B"}', 'BANDS["left"]', 'BANDS["right"]'),
    ],
)
def test_growth5_collection_constants_fold_only_plain_subscript_reads(
    declarations: str, left: str, right: str
) -> None:
    source = (
        _source()
        .replace('LEFT = "A"', f"{declarations}\nLEFT = {left}")
        .replace('RIGHT = "B"', f"RIGHT = {right}")
    )
    assert _inspect(source)["outcome"] == "evaluation_candidate"
    if declarations.startswith("BANDS = ("):
        membership = source.replace(
            "    result =",
            "    known = LEFT in BANDS\n    result =",
        ).replace("str(result),", "str(result) + str(known),")
        assert _inspect(membership)["outcome"] == "evaluation_candidate"
    refused = source.replace("def main():", "COPY = BANDS\n\ndef main():")
    assert _inspect(refused)["abstention_reasons"] == ["module-collection-use-not-modeled"]


@pytest.mark.parametrize("name", ["fmean", "mean", "stdev", "median", "variance"])
def test_growth5_direct_statistics_imports_are_sink_bound_only(name: str) -> None:
    source = (
        _source()
        .replace(
            "from scipy import stats", f"from scipy import stats\nfrom statistics import {name}"
        )
        .replace(
            '    REPORT.write_text(str(result), encoding="utf-8")',
            f"    summary = {name}(left)\n"
            '    REPORT.write_text(str(result) + str(summary), encoding="utf-8")',
        )
    )
    assert _inspect(source)["outcome"] == "evaluation_candidate"
    bad_import = source.replace(f"from statistics import {name}", "from statistics import mode")
    assert _inspect(bad_import)["abstention_reasons"] == ["unsupported-import-form"]


def test_growth5_leading_module_and_function_docstrings_are_inert() -> None:
    module_docstring = '"""Module documentation."""\n' + _source().replace(
        "main()\n", 'if __name__ == "__main__":\n    main()\n'
    )
    assert _inspect(module_docstring)["outcome"] == "evaluation_candidate"

    function_docstring = _source().replace(
        "def main():", 'def main():\n    """Function documentation."""'
    )
    assert _inspect(function_docstring)["outcome"] == "evaluation_candidate"


def test_growth5_nonleading_string_and_docstring_only_module_keep_closed_behavior() -> None:
    nonleading = _source().replace("    result =", '    "not a docstring"\n    result =')
    assert _inspect(nonleading)["abstention_reasons"] == ["sink-classification-unresolved"]
    assert _inspect('"""Documentation only."""\n')["abstention_reasons"] == [
        "reader-form-unsupported"
    ]


def test_growth5_harmless_annotations_lower_but_operand_aliases_still_refuse() -> None:
    annotation_only = _source().replace("    result =", "    note: str\n    result =")
    assert _inspect(annotation_only)["outcome"] == "evaluation_candidate"
    sink_bound = (
        _source()
        .replace("from scipy import stats", "from scipy import stats\nfrom statistics import mean")
        .replace(
            '    REPORT.write_text(str(result), encoding="utf-8")',
            "    summary: float = mean(left)\n"
            '    REPORT.write_text(str(result) + str(summary), encoding="utf-8")',
        )
    )
    assert _inspect(sink_bound)["outcome"] == "evaluation_candidate"
    sink_scalar = _source().replace(
        '    REPORT.write_text(str(result), encoding="utf-8")',
        '    n: int = 0\n    REPORT.write_text(str(result) + str(n), encoding="utf-8")',
    )
    assert _inspect(sink_scalar)["outcome"] == "evaluation_candidate"
    operand_alias = _source().replace(
        "    right = groups[RIGHT]",
        "    shadow = left\n    shadow: list = []\n    right = groups[RIGHT]",
    )
    assert _inspect(operand_alias)["abstention_reasons"] == ["annotated-assignment-not-modeled"]


@pytest.mark.parametrize("replacement", ["rows[:4]", "[]", "rows[:6]"])
def test_growth5_partition_seed_rejects_annotated_reader_frame_rebinds(
    replacement: str,
) -> None:
    data = b"unit_id,arm,value\nu1,A,1\nu2,A,2\nu3,B,3\nu4,B,4\nu1,A,5\nu5,A,6\nu6,B,7\nu7,B,8\n"
    source = _source().replace(
        "        rows = list(csv.DictReader(handle))",
        f"        rows = list(csv.DictReader(handle))\n    rows: list = {replacement}",
    )
    payload = _inspect(source, data)
    assert payload["outcome"] == "unsupported"
    assert payload["abstention_reasons"] == ["operand-name-rebound"]


def test_growth5_partition_seed_rejects_annotated_group_rebind_specifically() -> None:
    source = _source().replace(
        "    left = groups[LEFT]",
        '    groups: dict = {"A": [0.0], "B": [1.0]}\n    left = groups[LEFT]',
    )
    assert _inspect(source)["abstention_reasons"] == ["operand-name-rebound"]


def test_growth6_multi_name_from_imports_are_individually_closed() -> None:
    statistics_source = (
        _source()
        .replace(
            "from scipy import stats",
            "from scipy import stats\nfrom statistics import mean, stdev",
        )
        .replace(
            '    REPORT.write_text(str(result), encoding="utf-8")',
            "    summary = mean(left)\n"
            '    REPORT.write_text(str(result) + str(summary), encoding="utf-8")',
        )
    )
    assert _inspect(statistics_source)["outcome"] == "evaluation_candidate"
    assert _inspect(statistics_source.replace("mean, stdev", "mean, mode"))[
        "abstention_reasons"
    ] == ["unsupported-import-form"]

    scipy_source = (
        _source()
        .replace("from scipy import stats", "from scipy.stats import ttest_ind, mannwhitneyu")
        .replace("stats.ttest_ind", "ttest_ind")
    )
    assert _inspect(scipy_source)["outcome"] == "evaluation_candidate"
    assert _inspect(scipy_source.replace("mannwhitneyu", "wilcoxon"))["abstention_reasons"] == [
        "unsupported-import-form"
    ]

    assert _inspect(
        _source().replace("from pathlib import Path", "from pathlib import Path, PurePath")
    )["abstention_reasons"] == ["unsupported-import-form"]


def test_growth6_typing_imports_are_future_gated_and_annotation_only() -> None:
    source = "from __future__ import annotations\n" + _source().replace(
        "from scipy import stats", "from scipy import stats\nfrom typing import List, Optional"
    ).replace("    result =", "    note: Optional[List[str]]\n    result =")
    assert _inspect(source)["outcome"] == "evaluation_candidate"
    docstring_source = '"""Module documentation."""\n' + source
    assert _inspect(docstring_source)["outcome"] == "evaluation_candidate"
    assert _inspect(source.replace("from __future__ import annotations\n", ""))[
        "abstention_reasons"
    ] == ["unsupported-import-form"]
    misplaced = _source().replace(
        "import csv",
        "import csv\nfrom __future__ import annotations\nfrom typing import Dict",
    )
    assert _inspect(misplaced)["abstention_reasons"] == ["unsupported-import-form"]
    live = source.replace("    result =", "    marker = List\n    result =")
    assert _inspect(live)["abstention_reasons"] == ["import-use-outside-grammar"]


@pytest.mark.parametrize("method", ["move_to_end(LEFT)", "popitem()"])
def test_growth6_ordered_dict_reuses_plain_dict_proof_and_specific_methods_abstain(
    method: str,
) -> None:
    source = (
        _source()
        .replace("import csv", "import csv\nfrom collections import defaultdict, OrderedDict")
        .replace("    groups = {}", "    groups = OrderedDict()")
    )
    assert _inspect(source)["outcome"] == "evaluation_candidate"
    sorted_unpack = source.replace(
        "    left = groups[LEFT]\n    right = groups[RIGHT]",
        "    (_, left), (_, right) = sorted(groups.items())",
    )
    assert _inspect(sorted_unpack)["outcome"] == "evaluation_candidate"
    specific = source.replace(
        "    left = groups[LEFT]", f"    groups.{method}\n    left = groups[LEFT]"
    )
    assert _inspect(specific)["abstention_reasons"] == ["group-accumulator-not-total"]


@pytest.mark.parametrize(
    ("factory", "author_range", "reviewer", "hostile", "escalation", "suffix"),
    [
        (default_dependence_free_e1_config, range(51, 57), 24, 25, 17, "batch-e1"),
        (default_dependence_free_e2_config, range(57, 63), 26, 27, 18, "batch-e2"),
        (default_dependence_free_f1_config, range(63, 69), 28, 29, 19, "batch-f1"),
        (default_dependence_free_f2_config, range(69, 75), 30, 31, 20, "batch-f2"),
        (default_dependence_free_g1_config, range(75, 81), 32, 33, 21, "batch-g1"),
        (default_dependence_free_g2_config, range(81, 87), 34, 35, 22, "batch-g2"),
    ],
)
def test_batch_e_through_g_configs_clone_batch_d_structure_with_fresh_seats(
    factory: Any,
    author_range: range,
    reviewer: int,
    hostile: int,
    escalation: int,
    suffix: str,
) -> None:
    config = factory()
    baseline = default_dependence_free_d_config()
    assert config.pipeline_relative.as_posix().endswith(suffix)
    assert sorted(config.authors) == [
        f"actor:dependence-free-{suffix}-author-opus-{item}" for item in author_range
    ]
    assert config.reviewer.participant_id.endswith(f"fable-{reviewer}")
    assert config.hostile_answer_key_reviewer is not None
    assert config.hostile_answer_key_reviewer.participant_id.endswith(f"fable-{hostile}")
    assert config.escalation_reviewer.participant_id.endswith(f"opus-{escalation}")
    for field in (
        "dependence_v2_development_shadow",
        "dependence_v2_lock_line",
        "enforce_cli_review_json_schema",
        "stateless_review_per_case",
        "development_loop",
        "author_case_requirements",
        "allowed_import_roots",
    ):
        assert getattr(config, field) == getattr(baseline, field)


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
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {"ok": {"type": "boolean"}},
    }
    result = evaluation_pipeline._call_cli(
        config, participant, "prompt", "session", tmp_path / "capture", response_schema=schema
    )
    assert result["transport_error"] is None
    emitted = __import__("json").loads(observed[observed.index("--json-schema") + 1])
    assert "$schema" not in emitted
    Draft7Validator.check_schema(emitted)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert default_dependence_free_d_config().development_loop
    assert not default_dependence_free_config().enforce_cli_review_json_schema


def test_retained_client_schema_rejection_is_preserved_and_retried_once(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config = default_dependence_free_d_config()
    participant = config.reviewer
    prompt = "prompt"
    session_id = "session"
    capture = tmp_path / "capture"
    capture.mkdir()
    stdout = b""
    stderr = (evaluation_pipeline._CLAUDE_SCHEMA_META_REJECTION + "\n").encode()
    record = {
        "participant_id": participant.participant_id,
        "session_id": session_id,
        "prompt_digest": evaluation_pipeline.sha256_digest(prompt),
        "transport_error": "provider_cli_exit_code:1",
        "stdout_digest": evaluation_pipeline.sha256_digest(stdout),
        "stderr_digest": evaluation_pipeline.sha256_digest(stderr),
    }
    (capture / "capture.json").write_text(
        evaluation_pipeline.canonical_json(record) + "\n", encoding="utf-8"
    )
    (capture / "stdout.bin").write_bytes(stdout)
    (capture / "stderr.bin").write_bytes(stderr)
    original = {path.name: path.read_bytes() for path in capture.iterdir() if path.is_file()}
    calls = 0

    def fake_run(argv: list[str], **_: object) -> subprocess.CompletedProcess[bytes]:
        nonlocal calls
        calls += 1
        payload = {
            "is_error": False,
            "session_id": session_id,
            "modelUsage": {participant.model_id: {}},
            "result": '{"ok":true}',
        }
        return subprocess.CompletedProcess(
            argv, 0, str.encode(__import__("json").dumps(payload)), b""
        )

    monkeypatch.setattr(evaluation_pipeline.subprocess, "run", fake_run)
    result = evaluation_pipeline._call_cli(
        config,
        participant,
        prompt,
        session_id,
        capture,
        response_schema={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
        },
    )
    assert result["transport_error"] is None
    assert calls == 1
    assert {
        path.name: path.read_bytes() for path in capture.iterdir() if path.is_file()
    } == original
    assert (capture / "schema-compatible-retry/capture.json").is_file()
