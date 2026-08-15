"""Growth-7 procedure-census, helper, set, keyword, and batch regressions."""

from __future__ import annotations

import ast
import json
import os
import re
import runpy
import subprocess
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation.lean_pipeline import _registered_dependence_callable_set_v2

from sc_referee.dependence_recognition_v2.adapter import DependenceRecognitionV2ShadowAdapter
from sc_referee.dependence_recognition_v2.authority_lock import (
    V2_PROCEDURE_VARIANTS,
    V2_PROCEDURES,
    build_dependence_v2_authorization_lock,
    verify_dependence_v2_authorization_lock,
)
from sc_referee.dependence_recognition_v2.python_analyzer import (
    _DISTRIBUTION_HELPER_METHODS,
    _GROUP_PROCEDURES,
    analyze_dependence_growth_python,
)
from sc_referee.scientific_checks.core import FrozenBaseRecord, RecordRef
from scripts.lean_pipeline import (
    ENVELOPE_CONFIGS,
    default_dependence_free_h1_config,
    default_dependence_free_h2_config,
)

_BASE = runpy.run_path(str(Path(__file__).with_name("test_dependence_recognition_v2.py")))
_source = _BASE["_source"]
_context = _BASE["_context"]
_ADVERSE = _BASE["_ADVERSE"]
_COVERED = _BASE["_COVERED"]
_RUNTIME = Path(
    os.environ.get(
        "DEPENDENCE_SANDBOX_PYTHON",
        "/Users/alexanderking/Desktop/random_stuff/sc-referee-pilot-runtime/"
        "scipy114-venv/bin/python",
    )
)


def _inspect(source: str, data: bytes = _ADVERSE, *, set_authority: bool = False) -> dict[str, Any]:
    context = _context(source, data)
    if set_authority:
        records: list[FrozenBaseRecord] = []
        for record in context.base_records:
            value = json.loads(record.canonical_payload)
            if record.ref.record_type == "procedure":
                continue
            if record.ref.record_type == "human_method_authorization":
                value["procedure_ref"] = {
                    "record_type": "procedure",
                    "record_id": "procedure-v2:test",
                }
            records.append(FrozenBaseRecord.from_record(record.ref, value))
        procedure_calls = sorted(
            (
                node
                for node in ast.walk(ast.parse(source))
                if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in {"mannwhitneyu", "ttest_ind"}
            ),
            key=lambda node: (node.lineno, node.col_offset),
        )
        procedures = []
        for call in procedure_calls:
            assert isinstance(call.func, ast.Attribute)
            if call.func.attr == "mannwhitneyu":
                procedures.append("scipy.stats.mannwhitneyu")
                continue
            equal_var = next(
                (keyword.value for keyword in call.keywords if keyword.arg == "equal_var"),
                None,
            )
            procedures.append(
                "scipy.stats.ttest_ind:welch"
                if isinstance(equal_var, ast.Constant) and equal_var.value is False
                else "scipy.stats.ttest_ind"
            )
        records.append(
            FrozenBaseRecord.from_record(
                RecordRef("procedure", "procedure-v2:test"),
                {
                    "record_type": "procedure",
                    "record_id": "procedure-v2:test",
                    "resolved_callables": list(dict.fromkeys(procedures)),
                },
            )
        )
        context = __import__("dataclasses").replace(context, base_records=tuple(records))
    return DependenceRecognitionV2ShadowAdapter().inspect(context)


def _multi_source(*, reverse: bool = False, same_callable: bool = False) -> str:
    """Build two calls whose results both reach the sole report sink.

    That last property is the sensitive difference from independent review probes
    that computed a second result but reported only the first: the latter correctly
    abstain as ``sink-flow-escapes`` before procedure-variant reasoning matters.
    """

    second = "stats.ttest_ind" if same_callable else "stats.mannwhitneyu"
    arguments = "right, left" if reverse else "left, right"
    return (
        _source()
        .replace(
            "    result = stats.ttest_ind(left, right)",
            f"    result = stats.ttest_ind(left, right)\n    robustness = {second}({arguments})",
        )
        .replace("str(result)", 'str(result) + "\\n" + str(robustness)')
    )


def _ttest_variant_pair_source(*, first_welch: bool, second_welch: bool) -> str:
    first_suffix = ", equal_var=False" if first_welch else ""
    second_suffix = ", equal_var=False" if second_welch else ""
    return (
        _source()
        .replace(
            "    result = stats.ttest_ind(left, right)",
            f"    result = stats.ttest_ind(left, right{first_suffix})\n"
            f"    robustness = stats.ttest_ind(left, right{second_suffix})",
        )
        .replace("str(result)", 'str(result) + "\\n" + str(robustness)')
    )


def _execute(source: str, data: bytes, root: Path) -> str:
    if not _RUNTIME.is_file():
        pytest.fail(f"required growth-7 runtime is absent: {_RUNTIME}")
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
    return (root / "results/report.md").read_text(encoding="utf-8")


def test_growth7_registration_wins_and_registry_classes_are_disjoint() -> None:
    assert not (_GROUP_PROCEDURES | V2_PROCEDURES) & _DISTRIBUTION_HELPER_METHODS


def test_growth7_development_lock_translation_uses_the_reviewed_set_census() -> None:
    source = _multi_source().replace(
        "    robustness = stats.mannwhitneyu(left, right)",
        "    critical = stats.t.ppf(0.975, 10)\n    robustness = stats.mannwhitneyu(left, right)",
    )
    assert _registered_dependence_callable_set_v2(source) == (
        ("scipy.stats.ttest_ind", "scipy.stats.mannwhitneyu"),
        "lock-minted",
    )
    welch = _source().replace(
        "stats.ttest_ind(left, right)", "stats.ttest_ind(left, right, equal_var=False)"
    )
    assert _registered_dependence_callable_set_v2(welch)[0] == ("scipy.stats.ttest_ind:welch",)


def test_growth7_single_call_degenerate_seed_is_byte_exact_baseline() -> None:
    certificate = analyze_dependence_growth_python(_context(_source(), _ADVERSE)).certificate
    assert certificate is not None
    assert certificate.resolved_callables == ("scipy.stats.ttest_ind",)
    assert certificate.operand_slice_statement_tokens == (
        "flattened-statement:sha256:70d5c0a24c7eef8557fb6b2dffa1fc0e2aef37c3828e282bd1cfad362aaf3cea",
        "flattened-statement:sha256:27ed9c3d9ef754a52ce976a184ab3486c8663d9f76ca88351a9e1f5721668f0c",
        "flattened-statement:sha256:e8bc895c42e17c009b33688d23fc696240e1ea550af40a6ef64160ddc63c2a7d",
        "flattened-statement:sha256:02b31b90e03469ac21a81c8800c107369ebd721f58a4cd9942ddadce7d067142",
        "flattened-statement:sha256:e7542cad6d76b056c7ea95c3b8fbb84574af279e01e775654d8d1fdb1db0e32f",
        "flattened-statement:sha256:8ebc9fe532e769411731dfd10ef3e0b3eb785aa8eb2f945defb1d931a365c7a1",
    )


def test_growth7_sink_bound_helper_and_helper_chain_certify(tmp_path: Path) -> None:
    source = (
        _source()
        .replace(
            "    result = stats.ttest_ind(left, right)",
            "    result = stats.ttest_ind(left, right)\n"
            "    critical = stats.t.ppf(0.975, 10)\n"
            "    tail = stats.norm.sf(critical)",
        )
        .replace("str(result)", "str(result) + str(critical) + str(tail)")
    )
    _execute(source, _ADVERSE, tmp_path / "helper-chain")
    assert _inspect(source)["outcome"] == "evaluation_candidate"


def test_growth7_helper_into_operand_and_inline_helper_refuse() -> None:
    reaches = _source().replace(
        "    result = stats.ttest_ind(left, right)",
        "    critical = stats.t.ppf(0.975, 10)\n"
        "    through_alias = critical\n"
        "    result = stats.ttest_ind(through_alias, right)",
    )
    assert _inspect(reaches)["abstention_reasons"] == ["distribution-helper-reaches-operand"]


@pytest.mark.parametrize(
    "source",
    [
        _source().replace(
            "stats.ttest_ind(left, right)", "stats.ttest_ind(stats.t.ppf(0.975, 10), right)"
        ),
        _source().replace("str(result)", "str(result) + str(stats.t.ppf(0.975, 10))"),
        _source()
        .replace(
            "    result = stats.ttest_ind(left, right)",
            "    critical = 2 * stats.t.ppf(0.975, 10)\n    result = stats.ttest_ind(left, right)",
        )
        .replace("str(result)", "str(result) + str(critical)"),
    ],
)
def test_growth7_inline_helper_positions_refuse(source: str) -> None:
    assert _inspect(source)["abstention_reasons"] == ["distribution-helper-not-bound"]


@pytest.mark.parametrize("method", ["rvs", "pdf"])
def test_growth7_contested_distribution_methods_refuse(method: str) -> None:
    source = _source().replace(
        "    result = stats.ttest_ind(left, right)",
        f"    noise = stats.norm.{method}(1.0)\n    result = stats.ttest_ind(left, right)",
    )
    assert _inspect(source)["abstention_reasons"] == ["procedure-set-member-unregistered"]


def test_growth7_pure_contested_census_and_count_mixture_refuse() -> None:
    contested = _source().replace(
        "    result = stats.ttest_ind(left, right)", "    result = stats.norm.rvs(1.0)"
    )
    assert _inspect(contested)["abstention_reasons"] == ["procedure-census-unresolved"]
    mixed = _source().replace(
        "    result = stats.ttest_ind(left, right)",
        "    count = stats.binomtest(1, 2)\n    result = stats.ttest_ind(left, right)",
    )
    assert _inspect(mixed)["abstention_reasons"] == ["procedure-set-count-member-unsupported"]


@pytest.mark.parametrize(
    "data,outcome", [(_ADVERSE, "evaluation_candidate"), (_COVERED, "covered_negative")]
)
def test_growth7_joint_procedure_set_quantifies_shared_operands(
    data: bytes, outcome: str, tmp_path: Path
) -> None:
    source = _multi_source()
    _execute(source, data, tmp_path / outcome)
    payload = _inspect(source, data, set_authority=True)
    assert payload["outcome"] == outcome
    assert payload["payload"]["resolved_callables"] == [
        "scipy.stats.ttest_ind",
        "scipy.stats.mannwhitneyu",
    ]


def test_growth7_plain_and_welch_variants_share_operands_and_preserve_runtime_keywords(
    tmp_path: Path,
) -> None:
    data = b"unit_id,arm,value\nu1,A,1\nu1,A,2\nu2,A,100\nu3,B,3\nu4,B,4\n"
    plain = _source()
    welch = plain.replace(
        "stats.ttest_ind(left, right)", "stats.ttest_ind(left, right, equal_var=False)"
    )
    source = _ttest_variant_pair_source(first_welch=False, second_welch=True)

    plain_report = _execute(plain, data, tmp_path / "plain")
    welch_report = _execute(welch, data, tmp_path / "welch")
    pair_report = _execute(source, data, tmp_path / "plain-welch")
    assert pair_report.splitlines() == [plain_report, welch_report]
    assert plain_report != welch_report

    payload = _inspect(source, data, set_authority=True)
    assert payload["outcome"] == "evaluation_candidate"
    assert payload["payload"]["resolved_callables"] == [
        "scipy.stats.ttest_ind",
        "scipy.stats.ttest_ind:welch",
    ]


def test_growth7_two_welch_calls_share_operands_and_preserve_runtime_keywords(
    tmp_path: Path,
) -> None:
    data = b"unit_id,arm,value\nu1,A,1\nu1,A,2\nu2,A,100\nu3,B,3\nu4,B,4\n"
    welch = _source().replace(
        "stats.ttest_ind(left, right)", "stats.ttest_ind(left, right, equal_var=False)"
    )
    source = _ttest_variant_pair_source(first_welch=True, second_welch=True)

    welch_report = _execute(welch, data, tmp_path / "single-welch")
    pair_report = _execute(source, data, tmp_path / "welch-welch")
    assert pair_report.splitlines() == [welch_report, welch_report]

    payload = _inspect(source, data, set_authority=True)
    assert payload["outcome"] == "evaluation_candidate"
    assert payload["payload"]["resolved_callables"] == [
        "scipy.stats.ttest_ind:welch",
        "scipy.stats.ttest_ind:welch",
    ]


def test_growth7_unreported_second_variant_is_a_sink_flow_escape() -> None:
    source = _ttest_variant_pair_source(first_welch=False, second_welch=True).replace(
        'str(result) + "\\n" + str(robustness)', "str(result)"
    )
    assert _inspect(source, set_authority=True)["abstention_reasons"] == ["sink-flow-escapes"]


def test_growth7_same_callable_degenerate_and_divergence_gates() -> None:
    assert _inspect(_multi_source(same_callable=True), set_authority=True)["outcome"] == (
        "evaluation_candidate"
    )
    assert _inspect(_multi_source(reverse=True), set_authority=True)["abstention_reasons"] == [
        "procedure-set-operands-diverge"
    ]
    literal = _multi_source().replace(
        "stats.mannwhitneyu(left, right)", "stats.mannwhitneyu([1.0], right)"
    )
    assert _inspect(literal, set_authority=True)["abstention_reasons"] == [
        "procedure-set-operands-diverge"
    ]
    same_reversed = _multi_source(reverse=True, same_callable=True)
    assert _inspect(same_reversed, set_authority=True)["abstention_reasons"] == [
        "procedure-set-operands-diverge"
    ]
    same_literal = _multi_source(same_callable=True).replace(
        "    robustness = stats.ttest_ind(left, right)",
        "    robustness = stats.ttest_ind([1.0], right)",
    )
    assert _inspect(same_literal, set_authority=True)["abstention_reasons"] == [
        "procedure-set-operands-diverge"
    ]


@pytest.mark.parametrize(
    "replacement",
    [
        "stats.ttest_ind(left, right, equal_var=LEFT)",
        "stats.ttest_ind(left, right, nan_policy='omit')",
        "stats.ttest_ind(left, right, trim=0.2)",
        "stats.mannwhitneyu(left, right, method='bad')",
    ],
)
def test_growth7_keyword_registry_refuses_nonliteral_or_intake_affecting_options(
    replacement: str,
) -> None:
    source = _source().replace("stats.ttest_ind(left, right)", replacement)
    assert _inspect(source)["abstention_reasons"] == ["procedure-keyword-not-closed"]


@pytest.mark.parametrize(
    "replacement",
    [
        "stats.ttest_ind(left, right, equal_var=True, alternative='greater')",
        "stats.ttest_ind(left, right, equal_var=False, alternative='less')",
        "stats.mannwhitneyu(left, right, alternative='two-sided', method='exact')",
    ],
)
def test_growth7_intake_neutral_literal_keywords_are_admitted(replacement: str) -> None:
    source = _source().replace("stats.ttest_ind(left, right)", replacement)
    assert _inspect(source, set_authority=True)["outcome"] == "evaluation_candidate"


def test_growth7_welch_adverse_clean_runtime_differential(tmp_path: Path) -> None:
    ordinary = _source()
    welch = ordinary.replace(
        "stats.ttest_ind(left, right)", "stats.ttest_ind(left, right, equal_var=False)"
    )
    data = b"unit_id,arm,value\nu1,A,1\nu1,A,2\nu2,A,100\nu3,B,3\nu4,B,4\n"
    assert _execute(ordinary, data, tmp_path / "ordinary") != _execute(
        welch, data, tmp_path / "welch"
    )
    assert _inspect(welch, data, set_authority=True)["outcome"] == "evaluation_candidate"
    clean = data.replace(b"u1,A,2", b"u5,A,2")
    assert _inspect(welch, clean, set_authority=True)["outcome"] == "covered_negative"


def test_growth7_v2_lock_set_form_is_digest_closed(tmp_path: Path) -> None:
    lock = build_dependence_v2_authorization_lock(
        case_id="case:growth7",
        snapshot_digest="sha256:" + "1" * 64,
        intake_recorded_at="2026-08-15T00:00:00Z",
        procedure=("scipy.stats.ttest_ind", "scipy.stats.mannwhitneyu"),
        unit_column="unit_id",
        input_path="data/input.csv",
        input_content_digest="sha256:" + "2" * 64,
    )
    path = tmp_path / "lock.json"
    path.write_text(json.dumps(lock), encoding="utf-8")
    verified = verify_dependence_v2_authorization_lock(
        path,
        expected_case_id="case:growth7",
        expected_snapshot_digest="sha256:" + "1" * 64,
        expected_intake_recorded_at="2026-08-15T00:00:00Z",
        material_input_digests={"data/input.csv": "sha256:" + "2" * 64},
        frozen_input_headers={"data/input.csv": ("unit_id",)},
    )
    assert verified.records[1]["resolved_callables"] == [
        "scipy.stats.ttest_ind",
        "scipy.stats.mannwhitneyu",
    ]
    assert "scipy.stats.ttest_ind:welch" in V2_PROCEDURE_VARIANTS


@pytest.mark.parametrize(
    "factory,suffix,authors,reviewer,hostile,escalation",
    [
        (default_dependence_free_h1_config, "batch-h1", range(87, 93), 36, 37, 23),
        (default_dependence_free_h2_config, "batch-h2", range(93, 99), 38, 39, 24),
    ],
)
def test_growth7_batch_h_envelopes_have_fresh_seats(
    factory: Any,
    suffix: str,
    authors: range,
    reviewer: int,
    hostile: int,
    escalation: int,
) -> None:
    config = factory()
    assert config.pipeline_relative.as_posix().endswith(suffix)
    assert sorted(config.authors) == [
        f"actor:dependence-free-{suffix}-author-opus-{item}" for item in authors
    ]
    assert config.reviewer.participant_id.endswith(f"fable-{reviewer}")
    assert config.hostile_answer_key_reviewer is not None
    assert config.hostile_answer_key_reviewer.participant_id.endswith(f"fable-{hostile}")
    assert config.escalation_reviewer.participant_id.endswith(f"opus-{escalation}")
    assert ENVELOPE_CONFIGS[f"dependence-free-{suffix.removeprefix('batch-')}"] is factory


def test_growth7_batch_g_cases_pin_full_observed_reason_sets(project_root: Path) -> None:
    """Pin 59 measurable cases from a 60-case A--G lifetime denominator.

    Batch D case ``dc2b31d5da33d148736a`` was retained at intake after its
    then-forbidden ``__future__`` import, so it has no materialized case directory
    and cannot be statically re-measured. It remains the sixtieth lifetime case.
    """

    batch_names = ("a", "b", "c", "d", "e1", "e2", "f1", "f2", "g1", "g2")
    growth_root = project_root / "evaluation/development/dependence-growth-loop"
    measurable_count = sum(
        len(tuple((growth_root / f"batch-{batch}" / "authoring/cases").iterdir()))
        for batch in batch_names
    )
    intake_d = json.loads(
        (growth_root / "batch-d/authoring/INTAKE_LEDGER.json").read_text(encoding="utf-8")
    )
    refused = [
        entry
        for entry in intake_d["entries"]
        if entry["intake_admission_state"] == "refused_but_case_retained"
    ]
    assert measurable_count == 59
    assert intake_d["case_count"] == 6
    assert [entry["case_id"] for entry in refused] == ["case:dc2b31d5da33d148736a"]
    assert not (growth_root / "batch-d/authoring/cases/dc2b31d5da33d148736a").exists()

    expected = {
        "batch-g1": {
            "2ddf508d135fd7fce5df": ["raise-guard-not-modeled"],
            "30108f0d34292b11cab8": ["function-argument-not-simple"],
            "58960ceebfb9cb96d1e0": ["import-use-outside-grammar"],
            "8b55946a92793ebcd387": ["function-return-shape"],
            "aec630c60b86af0d2a96": [
                "count-predicate-not-closed",
                "module-constant-not-closed",
            ],
            "be2cd19d5dfaf5bcdd56": ["import-use-outside-grammar"],
        },
        "batch-g2": {
            "2cb900277aeb9722b368": ["module-constant-not-closed"],
            "34c19f723e535aa477ad": ["unsupported-import-form"],
            "93d89748fb42073e79bd": [
                "count-predicate-not-closed",
                "import-use-outside-grammar",
            ],
            "a8b660a9685f13f0187f": ["raise-guard-not-modeled"],
            "ae33434a6064f4251cbc": ["import-use-outside-grammar"],
            "ff99e13110aad17a7fd0": ["group-accumulator-not-total"],
        },
    }
    for batch, cases in expected.items():
        root = (
            project_root
            / "evaluation/development/dependence-growth-loop"
            / batch
            / "authoring/cases"
        )
        for slug, reasons in cases.items():
            case = root / slug
            description = (case / "data-description.md").read_text(encoding="utf-8")
            match = re.search(r"(?mi)^Independent unit column:[ \t]*([^\r\n]+)", description)
            assert match is not None
            payload = DependenceRecognitionV2ShadowAdapter().inspect(
                _context(
                    (case / "workflow/analysis.py").read_text(encoding="ascii"),
                    (case / "data/input.csv").read_bytes(),
                    unit_column=match.group(1).strip(),
                    data_path="data/input.csv",
                )
            )
            assert payload["abstention_reasons"] == reasons, (batch, slug, payload)
