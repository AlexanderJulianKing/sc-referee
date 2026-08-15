"""Growth-2 symbolic count, path-folding, and development-lock regressions."""

from __future__ import annotations

import json
import re
import subprocess
from collections import Counter
from dataclasses import replace
from pathlib import Path

import pytest
from sc_referee_evaluation.lean_pipeline import (
    _dependence_v2_observer,
    _description_v2_authority_lock,
)

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.dependence_recognition.adapter import DependenceRecognitionShadowAdapter
from sc_referee.dependence_recognition.python_analyzer import _trusted_authorizations
from sc_referee.dependence_recognition_v2.adapter import DependenceRecognitionV2ShadowAdapter
from sc_referee.dependence_recognition_v2.authority_lock import (
    V2_PROCEDURES,
    apply_dependence_v2_authorization_lock,
    build_dependence_v2_authorization_lock,
)
from sc_referee.dependence_recognition_v2.certificate import verify_count_dependence_certificate
from sc_referee.dependence_recognition_v2.count_domain import (
    prove_count_procedure_domain_with_reason,
)
from sc_referee.dependence_recognition_v2.ir import CountDependenceCertificate
from sc_referee.dependence_recognition_v2.python_analyzer import (
    analyze_dependence_growth_python,
)
from sc_referee.scientific_checks.core import FrozenBaseRecord, RecordRef
from scripts.lean_pipeline import (
    default_dependence_free_b_config,
    default_dependence_free_c_config,
)
from tests.test_dependence_free_envelope import (
    _fixture_config,
    _freeze_fixture_inputs,
    _isolated_root,
)
from tests.test_dependence_recognition_v2 import _context, _require_runtime


def _binomial_source(*, n: str = "len(rows)", k: str | None = None) -> str:
    success = k or 'sum(1 for row in rows if row["success"] == "yes")'
    return f"""import csv
import os
from pathlib import Path
from scipy import stats

INPUT = os.path.join("inputs", "data.csv")
REPORT = os.path.join("results", "report.md")
P = 0.5

def main():
    with Path(INPUT).open(newline="", encoding="ascii") as handle:
        rows = list(csv.DictReader(handle))
    n = {n}
    k = {success}
    result = stats.binomtest(k, n, p=P, alternative="two-sided")
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    Path(REPORT).write_text(str(result), encoding="utf-8")

main()
"""


def _fisher_source(*, table: str = "[[a, b], [c, d]]") -> str:
    return f"""import csv
from pathlib import Path
from scipy import stats

def main():
    with Path("inputs/data.csv").open(newline="", encoding="ascii") as handle:
        rows = list(csv.DictReader(handle))
    a = sum(1 for row in rows if row["arm"] == "A" and row["success"] == "yes")
    b = sum(1 for row in rows if row["arm"] == "A" and row["success"] == "no")
    c = sum(1 for row in rows if row["arm"] == "B" and row["success"] == "yes")
    d = sum(1 for row in rows if row["arm"] == "B" and row["success"] == "no")
    table = {table}
    result = stats.fisher_exact(table, alternative="two-sided")
    Path("results/report.md").write_text(str(result), encoding="utf-8")

main()
"""


def _inspect(source: str, data: bytes) -> dict[str, object]:
    return DependenceRecognitionV2ShadowAdapter().inspect(_context(source, data))


def _execute(source: str, data: bytes, tmp_path: Path) -> None:
    case = tmp_path / semantic_digest({"source": source, "data": data.hex()}).removeprefix(
        "sha256:"
    )
    (case / "inputs").mkdir(parents=True)
    (case / "workflow").mkdir()
    (case / "results").mkdir()
    (case / "inputs/data.csv").write_bytes(data)
    (case / "workflow/analysis.py").write_text(source, encoding="ascii")
    completed = subprocess.run(
        [str(_require_runtime()), "-I", "workflow/analysis.py"],
        cwd=case,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def _context_with_v1_authority(source: str, data: bytes):  # type: ignore[no-untyped-def]
    context = _context(source, data, authority=False)
    legacy_ref = RecordRef("human_method_authorization", "authorization:legacy")
    return replace(
        context,
        base_records=(
            *context.base_records,
            FrozenBaseRecord.from_record(
                legacy_ref,
                {
                    "record_type": "human_method_authorization",
                    "record_id": legacy_ref.record_id,
                    "actor_id": "human:v1-owner",
                    "authority_state": "authorized",
                    "analysis_target_ref": {
                        "record_type": "analysis",
                        "record_id": "analysis:v2",
                    },
                    "procedure_ref": {
                        "record_type": "procedure",
                        "record_id": "procedure:v2",
                    },
                    "independent_unit_definition_id": "unit-definition:v1",
                    "authorized_key_columns": ["unit_id"],
                    "input_path": "inputs/data.csv",
                    "input_content_digest": sha256_digest(data),
                },
            ),
        ),
    )


def _count_kernel_inputs(
    source: str, data: bytes
) -> tuple[object, CountDependenceCertificate, object]:
    context = _context(source, data)
    analysis = analyze_dependence_growth_python(context)
    assert isinstance(analysis.certificate, CountDependenceCertificate)
    fact, reason = prove_count_procedure_domain_with_reason(
        context.material_inputs[0], obligation=analysis.certificate.obligation
    )
    assert reason is None
    assert fact is not None
    relevant = (
        fact.operands[1:2]
        if analysis.certificate.resolved_callable.endswith("binomtest")
        else fact.operands
    )
    repeated = {
        unit
        for proof in relevant
        for unit, count in Counter(proof.authorized_unit_ids).items()
        if count > 1
    }
    conclusion = "repeated_units" if repeated else "one_observation_per_unit"
    certificate = replace(analysis.certificate, conclusion=conclusion)
    certificate = replace(
        certificate,
        certificate_id="dependence-growth-count-certificate:"
        + semantic_digest(
            {
                "source_digest": certificate.source_digest,
                "fact": fact.evidence_id,
                "procedure": certificate.resolved_callable,
                "conclusion": conclusion,
            }
        ),
    )
    return context, certificate, fact


@pytest.mark.parametrize(
    ("source", "data", "outcome", "reason"),
    [
        (
            _binomial_source(),
            b"unit_id,success\nu1,yes\nu1,no\nu2,yes\n",
            "evaluation_candidate",
            "repeated-unit-rows-counted-as-independent-binomtest-trials",
        ),
        (
            _binomial_source(),
            b"unit_id,success\nu1,yes\nu2,no\nu3,yes\n",
            "covered_negative",
            "one-row-per-unit-in-proven-count-sets",
        ),
        (
            _fisher_source(),
            b"unit_id,arm,success\nu1,A,yes\nu1,A,yes\nu2,A,no\nu3,B,yes\nu4,B,no\n",
            "evaluation_candidate",
            "repeated-unit-rows-enter-independent-fisher-cells",
        ),
        (
            _fisher_source(),
            b"unit_id,arm,success\nu1,A,yes\nu2,A,no\nu3,B,yes\nu4,B,no\n",
            "covered_negative",
            "one-row-per-unit-in-proven-count-sets",
        ),
    ],
)
def test_executable_count_fixtures_reach_both_branches(
    source: str, data: bytes, outcome: str, reason: str, tmp_path: Path
) -> None:
    case = tmp_path / "case"
    (case / "inputs").mkdir(parents=True)
    (case / "workflow").mkdir()
    (case / "results").mkdir()
    (case / "inputs/data.csv").write_bytes(data)
    (case / "workflow/analysis.py").write_text(source, encoding="ascii")
    completed = subprocess.run(
        [str(_require_runtime()), "-I", "workflow/analysis.py"],
        cwd=case,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = _inspect(source, data)
    assert payload["outcome"] == outcome
    assert payload["reason_code"] == reason


@pytest.mark.parametrize(
    ("source", "data", "reason"),
    [
        (
            _fisher_source(),
            b"unit_id,arm,success\nu1,A,yes\nu1,B,no\nu2,A,no\nu3,B,yes\n",
            "unit-spans-multiple-cells",
        ),
        (
            _fisher_source(),
            b"unit_id,arm,success\nu1,A,yes\nu2,A,no\nu3,B,yes\nu4,B,no\nu5,A,maybe\n",
            "count-cells-not-partition",
        ),
        (
            _fisher_source(table="[[a, b], [c, len(rows) - a - b - c]]"),
            b"unit_id,arm,success\nu1,A,yes\nu2,A,no\nu3,B,yes\nu4,B,no\n",
            "count-cell-derived-by-arithmetic",
        ),
        (
            _binomial_source().replace(
                "    n = len(rows)",
                '    eligible = [row for row in rows if row["eligible"] == "yes"]\n'
                "    n = len(eligible)",
            ),
            b"unit_id,eligible,success\nu1,no,yes\nu2,yes,no\n",
            "count-success-not-subset",
        ),
        (
            _binomial_source(k='sum(1 for row in rows if row["success"] == "never")'),
            b"unit_id,success\nu1,yes\nu2,no\n",
            "count-set-degenerate",
        ),
        (
            _binomial_source(k='sum(1 for row in rows if row["success"] == 1)'),
            b"unit_id,success\nu1,1\nu2,0\n",
            "count-predicate-literal-not-string",
        ),
        (
            _binomial_source(n='len([float(row["value"]) for row in rows])'),
            b"unit_id,success,value\nu1,yes,1\nu2,no,2\n",
            "count-domain-not-row-bound",
        ),
    ],
)
def test_count_fail_closed_routes(source: str, data: bytes, reason: str, tmp_path: Path) -> None:
    _execute(source, data, tmp_path)
    payload = _inspect(source, data)
    assert payload["outcome"] == "unsupported"
    assert reason in payload["abstention_reasons"]


def test_empty_authorized_unit_cell_never_reaches_a_count_conclusion() -> None:
    payload = _inspect(
        _binomial_source(),
        b"unit_id,success\n,yes\nu2,no\n",
    )
    assert payload["outcome"] == "unsupported"
    assert payload["abstention_reasons"] == ["group-key-or-unit-cell-empty"]


def test_predeclared_t_group_of_bare_rows_is_a_proven_count_domain(tmp_path: Path) -> None:
    source = """import csv
from pathlib import Path
from scipy import stats
def main():
    with Path("inputs/data.csv").open(newline="", encoding="ascii") as handle:
        rows = list(csv.DictReader(handle))
    groups = {"A": [], "B": []}
    for row in rows:
        groups[row["arm"]].append(row)
    n = len(groups["A"])
    k = sum(1 for row in groups["A"] if row["success"] == "yes")
    result = stats.binomtest(k, n, p=0.5, alternative="two-sided")
    Path("results/report.md").write_text(str(result), encoding="utf-8")
main()
"""
    data = b"unit_id,arm,success\nu1,A,yes\nu1,A,no\nu2,B,yes\n"
    _execute(source, data, tmp_path)
    payload = _inspect(source, data)
    assert payload["outcome"] == "evaluation_candidate"

    doubled = source.replace(
        '    n = len(groups["A"])',
        '    for row in rows:\n        groups[row["arm"]].append(row)\n    n = len(groups["A"])',
    )
    refused = _inspect(doubled, b"unit_id,arm,success\nu1,A,yes\nu2,A,no\nu3,B,yes\n")
    assert refused["outcome"] == "unsupported"
    assert refused["abstention_reasons"] == ["count-multiple-increment-sites"]


def test_single_column_t_groups_do_not_supply_two_factor_cell_atoms(tmp_path: Path) -> None:
    source = """import csv
from pathlib import Path
from scipy import stats
def main():
    with Path("inputs/data.csv").open(newline="", encoding="ascii") as handle:
        rows = list(csv.DictReader(handle))
    groups = {"AY": [], "AN": [], "BY": [], "BN": []}
    for row in rows:
        groups[row["cell"]].append(row)
    a = len(groups["AY"])
    b = len(groups["AN"])
    c = len(groups["BY"])
    d = len(groups["BN"])
    table = [[a, b], [c, d]]
    result = stats.fisher_exact(table, alternative="two-sided")
    Path("results/report.md").write_text(str(result), encoding="utf-8")
main()
"""
    data = b"unit_id,cell\nu1,AY\nu2,AN\nu3,BY\nu4,BN\n"
    _execute(source, data, tmp_path)
    payload = _inspect(source, data)
    assert payload["outcome"] == "unsupported"
    assert payload["abstention_reasons"] == ["count-cells-not-factorial"]
    unexpected = _inspect(
        source,
        b"unit_id,cell\nu1,AY\nu2,AN\nu3,BY\nu4,BN\nu5,OTHER\n",
    )
    assert unexpected["outcome"] == "unsupported"
    assert unexpected["abstention_reasons"] == ["group-set-not-closed"]


def test_single_total_increment_site_is_admitted_but_two_sites_refuse(tmp_path: Path) -> None:
    source = """import csv
from pathlib import Path
from scipy import stats
def main():
    with Path("inputs/data.csv").open(newline="", encoding="ascii") as handle:
        rows = list(csv.DictReader(handle))
    n = len(rows)
    k = 0
    for row in rows:
        if row["success"] == "yes":
            k += 1
    result = stats.binomtest(k, n, p=0.5, alternative="two-sided")
    Path("results/report.md").write_text(str(result), encoding="utf-8")
main()
"""
    data = b"unit_id,success\nu1,yes\nu1,no\nu2,yes\n"
    _execute(source, data, tmp_path)
    assert _inspect(source, data)["outcome"] == "evaluation_candidate"
    two_sites = source.replace(
        "    result = stats.binomtest",
        '    for row in rows:\n        if row["success"] == "no":\n            k += 1\n'
        "    result = stats.binomtest",
    )
    assert _inspect(two_sites, data)["abstention_reasons"] == ["count-multiple-increment-sites"]
    assert _inspect(source.replace("k += 1", "k += 2"), data)["abstention_reasons"] == [
        "count-increment-not-total"
    ]


def test_nondefault_alternative_refuses() -> None:
    source = _binomial_source().replace('alternative="two-sided"', 'alternative="greater"')
    payload = _inspect(source, b"unit_id,success\nu1,yes\nu2,no\n")
    assert payload["abstention_reasons"] == ["procedure-alternative-not-default"]


@pytest.mark.parametrize(
    "source",
    [
        _binomial_source().replace("k, n, p=P", "k, n, P"),
        _binomial_source().replace(', alternative="two-sided"', ""),
    ],
)
def test_positional_constant_p_and_absent_default_alternative_are_admitted(
    source: str,
) -> None:
    payload = _inspect(source, b"unit_id,success\nu1,yes\nu2,no\n")
    assert payload["outcome"] == "covered_negative"


def test_posix_join_requires_literal_components_and_exact_frozen_paths() -> None:
    data = b"unit_id,success\nu1,yes\nu2,no\n"
    named_component = _binomial_source().replace(
        'INPUT = os.path.join("inputs", "data.csv")',
        'BASE = "inputs"\nINPUT = os.path.join(BASE, "data.csv")',
    )
    assert _inspect(named_component, data)["abstention_reasons"] == ["module-constant-not-closed"]
    wrong_reader = _binomial_source().replace(
        'os.path.join("inputs", "data.csv")',
        'os.path.join("inputs", "other.csv")',
    )
    assert _inspect(wrong_reader, data)["abstention_reasons"] == ["group-domain-binding-mismatch"]
    wrong_sink = _binomial_source().replace(
        'os.path.join("results", "report.md")',
        'os.path.join("results", "other.md")',
    )
    assert _inspect(wrong_sink, data)["abstention_reasons"] == ["report-composition-not-modeled"]


def test_collapsed_value_domain_abstains(tmp_path: Path) -> None:
    source = _binomial_source(n='len([float(row["value"]) for row in rows])')
    data = b"unit_id,success,value\nu1,yes,1\nu2,no,2\n"
    _execute(source, data, tmp_path)
    payload = _inspect(source, data)
    assert payload["outcome"] == "unsupported"
    assert payload["abstention_reasons"] == ["count-domain-not-row-bound"]


def test_real_batch_b_rq6_must_never_accuse(project_root: Path) -> None:
    root = (
        project_root
        / "evaluation/development/dependence-growth-loop/batch-b/authoring/cases"
        / "6a3bc02816cb70ee4042"
    )
    source = (root / "workflow/analysis.py").read_text(encoding="ascii")
    data = (root / "data/input.csv").read_bytes()
    payload = DependenceRecognitionV2ShadowAdapter().inspect(
        _context(source, data, unit_column="well_id", data_path="data/input.csv")
    )
    # If the statistics/defaultdict import wall is later lifted, the expected
    # refusal must become count-domain-not-row-bound; accusation remains forbidden.
    assert payload["outcome"] != "evaluation_candidate"


@pytest.mark.parametrize(
    "predicate",
    [
        'float(row["value"]) == 1.0',
        '"yes" in row["success"]',
        'row["success"] == ("y" + "es")',
    ],
)
def test_predicates_over_cast_membership_or_computed_literals_refuse(
    predicate: str, tmp_path: Path
) -> None:
    source = _binomial_source().replace('row["success"] == "yes"', predicate)
    data = b"unit_id,success,value\nu1,yes,1\nu2,no,2\n"
    _execute(source, data, tmp_path)
    payload = _inspect(source, data)
    assert payload["outcome"] == "unsupported"
    assert payload["abstention_reasons"] == ["count-predicate-not-closed"]


def test_overlapping_nonempty_fisher_cells_reach_neither_branch(tmp_path: Path) -> None:
    source = _fisher_source()
    source = source.replace('row["arm"] == "A"', 'row["arm"] != "B"')
    source = source.replace('row["arm"] == "B"', 'row["arm"] != "A"')
    data = b"unit_id,arm,success\nu1,A,yes\nu2,A,no\nu3,B,yes\nu4,B,no\nu5,C,yes\nu6,C,no\n"
    _execute(source, data, tmp_path)
    payload = _inspect(source, data)
    assert payload["outcome"] == "unsupported"
    assert payload["abstention_reasons"] == ["count-cells-not-partition"]


def test_nonfactorial_three_arm_table_abstains(tmp_path: Path) -> None:
    source = _fisher_source().replace(
        'row["arm"] == "B" and row["success"] == "no"',
        'row["arm"] == "C" and row["success"] == "no"',
    )
    data = b"unit_id,arm,success\nu1,A,yes\nu2,A,no\nu3,B,yes\nu4,C,no\n"
    _execute(source, data, tmp_path)
    payload = _inspect(source, data)
    assert payload["outcome"] == "unsupported"
    assert payload["abstention_reasons"] == ["count-cells-not-factorial"]


def test_sparse_factorial_fisher_table_clears(tmp_path: Path) -> None:
    source = _fisher_source()
    data = b"unit_id,arm,success\nu1,A,yes\nu2,A,no\nu3,B,yes\n"
    _execute(source, data, tmp_path)
    payload = _inspect(source, data)
    assert payload["outcome"] == "covered_negative"
    assert payload["reason_code"] == "one-row-per-unit-in-proven-count-sets"


def test_kernel_independently_rejects_nonfactorial_fisher_atoms() -> None:
    source = _fisher_source().replace(
        'row["arm"] == "B" and row["success"] == "no"',
        'row["arm"] == "C" and row["success"] == "no"',
    )
    data = b"unit_id,arm,success\nu1,A,yes\nu2,A,no\nu3,B,yes\nu4,C,no\n"
    context, certificate, fact = _count_kernel_inputs(source, data)
    failures: list[str] = []
    assert (
        verify_count_dependence_certificate(
            certificate,
            trusted_count_facts=(fact,),
            trusted_authorizations=_trusted_authorizations(context),
            source_bytes=source.encode("ascii"),
            _failure_reasons=failures,
        )
        is None
    )
    assert failures == ["count-cells-factorial"]


def test_module_constant_alternative_is_rejected_by_the_analyzer() -> None:
    source = (
        _binomial_source()
        .replace(
            "P = 0.5",
            'P = 0.5\nALTERNATIVE = "two-sided"',
        )
        .replace('alternative="two-sided"', "alternative=ALTERNATIVE")
    )
    payload = _inspect(source, b"unit_id,success\nu1,yes\nu2,no\n")
    assert payload["outcome"] == "unsupported"
    assert payload["abstention_reasons"] == ["procedure-alternative-not-default"]


def test_guarded_increment_nonbyte_predicate_is_visible_to_wall_scan() -> None:
    source = _binomial_source().replace(
        '    k = sum(1 for row in rows if row["success"] == "yes")',
        '    k = 0\n    for row in rows:\n        if float(row["value"]) > 1.0:\n'
        "            k += 1",
    )
    payload = _inspect(source, b"unit_id,success,value\nu1,yes,2\nu2,no,1\n")
    assert payload["outcome"] == "unsupported"
    assert "count-predicate-not-closed" in payload["abstention_reasons"]


def test_stale_evaluation_build_tree_is_absent(project_root: Path) -> None:
    completed = subprocess.run(
        ["git", "ls-files", "--", "evaluation/build"],
        cwd=project_root,
        capture_output=True,
        check=True,
        text=True,
    )
    assert completed.stdout == ""


def test_count_kernel_accepts_then_refuses_single_field_corruptions() -> None:
    source = _binomial_source()
    data = b"unit_id,success\nu1,yes\nu1,no\nu2,yes\n"
    context, certificate, fact = _count_kernel_inputs(source, data)
    failures: list[str] = []
    assert (
        verify_count_dependence_certificate(
            certificate,
            trusted_count_facts=(fact,),
            trusted_authorizations=_trusted_authorizations(context),
            source_bytes=source.encode("ascii"),
            _failure_reasons=failures,
        )
        is not None
    )
    assert failures == []

    mutations = (
        ("authority-binding", replace(certificate, authority_record_id="authorization:wrong")),
        ("count-source-semantic-replay", replace(certificate, sink_token="wrong-token")),
        (
            "authority-binding",
            replace(
                certificate,
                obligation=replace(certificate.obligation, content_digest=sha256_digest(b"wrong")),
            ),
        ),
        ("conclusion-equation", replace(certificate, conclusion="one_observation_per_unit")),
        ("certificate-identity", replace(certificate, certificate_id="wrong")),
    )
    for expected, corrupted in mutations:
        failures = []
        assert (
            verify_count_dependence_certificate(
                corrupted,
                trusted_count_facts=(fact,),
                trusted_authorizations=_trusted_authorizations(context),
                source_bytes=source.encode("ascii"),
                _failure_reasons=failures,
            )
            is None
        )
        assert failures == [expected]

    failures = []
    assert (
        verify_count_dependence_certificate(
            certificate,
            trusted_count_facts=(replace(fact, row_count=fact.row_count + 1),),
            trusted_authorizations=_trusted_authorizations(context),
            source_bytes=source.encode("ascii"),
            _failure_reasons=failures,
        )
        is None
    )
    assert failures == ["count-fact-closure"]


@pytest.mark.parametrize(
    ("source", "data", "obligation"),
    [
        (
            _binomial_source().replace(
                "    n = len(rows)",
                '    eligible = [row for row in rows if row["eligible"] == "yes"]\n'
                "    n = len(eligible)",
            ),
            b"unit_id,eligible,success\nu1,no,yes\nu2,yes,no\n",
            "count-subset-partition",
        ),
        (
            _fisher_source(),
            b"unit_id,arm,success\nu1,A,yes\nu1,B,no\nu2,A,no\nu3,B,yes\n",
            "count-unit-nonspanning",
        ),
    ],
)
def test_count_kernel_itself_enforces_set_and_unit_gates(
    source: str, data: bytes, obligation: str
) -> None:
    context, certificate, fact = _count_kernel_inputs(source, data)
    failures: list[str] = []
    assert (
        verify_count_dependence_certificate(
            certificate,
            trusted_count_facts=(fact,),
            trusted_authorizations=_trusted_authorizations(context),
            source_bytes=source.encode("ascii"),
            _failure_reasons=failures,
        )
        is None
    )
    assert failures == [obligation]


def test_batch_b_and_batch_c_are_distinct_development_shadow_envelopes() -> None:
    batch_b = default_dependence_free_b_config()
    batch_c = default_dependence_free_c_config()
    assert batch_b.dependence_v2_lock_line is False
    assert batch_c.dependence_v2_lock_line is True
    assert batch_c.dependence_v2_development_shadow is True
    assert batch_c.envelope_id == "development-dependence-growth-loop-batch-c-v1"
    assert str(batch_c.pipeline_relative).endswith("dependence-growth-loop/batch-c")
    assert sorted(batch_c.authors) == [
        f"actor:dependence-free-batch-c-author-opus-{ordinal}" for ordinal in range(39, 45)
    ]
    assert batch_c.reviewer.participant_id.endswith("reviewer-fable-20")
    assert batch_c.hostile_answer_key_reviewer is not None
    assert batch_c.hostile_answer_key_reviewer.participant_id.endswith("hostile-fable-21")
    assert batch_c.escalation_reviewer.participant_id.endswith("escalation-opus-15")
    assert "One trial is: one row" in batch_c.author_case_requirements
    changed = {
        "envelope_id",
        "pipeline_relative",
        "authors",
        "author_roles",
        "reviewer",
        "hostile_answer_key_reviewer",
        "escalation_reviewer",
        "author_case_requirements",
        "dependence_v2_lock_line",
    }
    assert {key: value for key, value in batch_b.__dict__.items() if key not in changed} == {
        key: value for key, value in batch_c.__dict__.items() if key not in changed
    }


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_count_trial_declaration_mints_only_on_the_exact_closed_line(
    tmp_path: Path, newline: str
) -> None:
    case = tmp_path / "case"
    (case / "workflow").mkdir(parents=True)
    (case / "data").mkdir()
    source = _binomial_source().replace("inputs/data.csv", "data/input.csv")
    data = b"unit_id,success\nu1,yes\nu2,no\n"
    (case / "workflow/analysis.py").write_text(source, encoding="ascii")
    (case / "data/input.csv").write_bytes(data)
    description = (
        "One row is: one trial"
        + newline
        + "Independent unit column: unit_id"
        + newline
        + "One trial is: one row"
        + newline
    )
    (case / "data-description.md").write_text(description, encoding="utf-8", newline="")
    value, reason, column = _description_v2_authority_lock(
        case_id="case:12345678",
        case_root=case,
        intake_row={
            "expected_audit_snapshot_digest": sha256_digest(b"snapshot"),
            "file_digests": {"data/input.csv": sha256_digest(data)},
        },
        intake_recorded_at="2026-08-14T00:00:00Z",
        description_path="data-description.md",
        input_path="data/input.csv",
    )
    assert value is not None
    assert reason == "lock-minted"
    assert column == "unit_id"

    (case / "data-description.md").write_text(
        description.replace("One trial is: one row", "One trial is: one record"),
        encoding="utf-8",
    )
    value, reason, _column = _description_v2_authority_lock(
        case_id="case:12345678",
        case_root=case,
        intake_row={
            "expected_audit_snapshot_digest": sha256_digest(b"snapshot"),
            "file_digests": {"data/input.csv": sha256_digest(data)},
        },
        intake_recorded_at="2026-08-14T00:00:00Z",
        description_path="data-description.md",
        input_path="data/input.csv",
    )
    assert value is None
    assert reason == "count-procedure-trial-declaration-missing"


def test_v2_lock_procedure_registry_is_exactly_the_reviewed_four() -> None:
    assert V2_PROCEDURES == {
        "scipy.stats.ttest_ind",
        "scipy.stats.mannwhitneyu",
        "scipy.stats.binomtest",
        "scipy.stats.fisher_exact",
    }


def test_authority_step_freezes_count_lock_only_under_locks_v2(
    tmp_path: Path, project_root: Path
) -> None:
    from sc_referee_evaluation.lean_pipeline import step_authority, step_intake

    isolated = _isolated_root(tmp_path, project_root)
    config = replace(
        _fixture_config(("rq1",)),
        pipeline_relative=Path("evaluation/development-fixtures/growth2-lock-line"),
        dependence_v2_development_shadow=True,
        dependence_v2_lock_line=True,
    )
    _freeze_fixture_inputs(isolated, config)
    incoming = (
        isolated
        / config.pipeline_relative
        / "authoring/incoming/controller:nonmeasurement-fixture.json"
    )
    attempt = json.loads(incoming.read_text(encoding="utf-8"))
    payload = json.loads(attempt["raw_response"])
    case = payload["cases"][0]
    case["input_csv"] = "unit_id,success\nu1,yes\nu1,no\nu2,yes\n"
    case["analysis_py"] = (
        _binomial_source()
        .replace(
            'os.path.join("inputs", "data.csv")',
            'os.path.join("data", "input.csv")',
        )
        .replace(
            'Path(REPORT).write_text(str(result), encoding="utf-8")',
            'Path(REPORT).write_text(f"[selected-result] {result}\\n", encoding="utf-8")',
        )
    )
    case["report_md"] = (
        "[selected-result] BinomTestResult(k=2, n=3, alternative='two-sided', "
        "statistic=0.6666666666666666, pvalue=1.0)\n"
    )
    case["data_description"] = (
        "One row is: one trial row.\nIndependent unit column: unit_id\nOne trial is: one row\n"
    )
    attempt["raw_response"] = json.dumps(payload)
    incoming.write_text(json.dumps(attempt), encoding="utf-8")
    step_intake(isolated, config)
    ledger = step_authority(isolated, config)
    entry = ledger["entries"][0]
    assert entry["authority_state"] == "unresolved_or_withheld"
    assert entry["v2_authority_state"] == "authorized"
    assert entry["v2_frozen_lock_relative"].startswith("authority/locks-v2/")
    assert not (isolated / config.pipeline_relative / "authority/locks").exists()


def test_v2_lock_records_cannot_change_the_v1_per_case_outcome(tmp_path: Path) -> None:
    source = _binomial_source()
    data = b"unit_id,success\nu1,yes\nu1,no\nu2,yes\n"
    context = _context_with_v1_authority(source, data)
    before = DependenceRecognitionShadowAdapter().inspect(context)
    lock = build_dependence_v2_authorization_lock(
        case_id="case:12345678",
        snapshot_digest=context.snapshot_digest,
        intake_recorded_at="2026-08-14T00:00:00Z",
        procedure="scipy.stats.binomtest",
        unit_column="unit_id",
        input_path="inputs/data.csv",
        input_content_digest=sha256_digest(data),
    )
    lock_path = tmp_path / "lock.json"
    lock_path.write_text(json.dumps(lock), encoding="utf-8")
    extended = apply_dependence_v2_authorization_lock(
        context,
        lock_path,
        expected_case_id="case:12345678",
        expected_intake_recorded_at="2026-08-14T00:00:00Z",
    )
    after = DependenceRecognitionShadowAdapter().inspect(extended)
    assert after == before


def test_development_observer_applies_the_v2_lock_to_the_same_frozen_context(
    tmp_path: Path,
) -> None:
    source = _binomial_source()
    data = b"unit_id,success\nu1,yes\nu1,no\nu2,yes\n"
    context = _context_with_v1_authority(source, data)
    lock = build_dependence_v2_authorization_lock(
        case_id="case:12345678",
        snapshot_digest=context.snapshot_digest,
        intake_recorded_at="2026-08-14T00:00:00Z",
        procedure="scipy.stats.binomtest",
        unit_column="unit_id",
        input_path="inputs/data.csv",
        input_content_digest=sha256_digest(data),
    )
    lock_path = tmp_path / "lock.json"
    lock_path.write_text(json.dumps(lock), encoding="utf-8")
    payloads: list[dict[str, object]] = []
    observer = _dependence_v2_observer(
        default_dependence_free_b_config(),
        payloads,
        lock_path=lock_path,
        expected_case_id="case:12345678",
        expected_intake_recorded_at="2026-08-14T00:00:00Z",
    )
    assert observer is not None
    observer(context)
    assert len(payloads) == 1
    assert payloads[0]["outcome"] == "evaluation_candidate"
    assert (
        payloads[0]["reason_code"] == "repeated-unit-rows-counted-as-independent-binomtest-trials"
    )


def test_missing_count_trial_line_is_a_named_controller_side_abstention() -> None:
    payloads: list[dict[str, object]] = []
    observer = _dependence_v2_observer(
        default_dependence_free_b_config(),
        payloads,
        authority_refusal_reason="count-procedure-trial-declaration-missing",
    )
    assert observer is not None
    observer(_context(_binomial_source(), b"unit_id,success\nu1,yes\nu2,no\n"))
    assert payloads[0]["outcome"] == "unsupported"
    assert payloads[0]["abstention_reasons"] == ["count-procedure-trial-declaration-missing"]


_FROZEN_BATCH_REASONS = {
    "batch-a/112bd1e61aa4fc1bec86": ("unsupported-import-form",),
    "batch-a/a520ddbd23df9d699e60": ("unsupported-import-form",),
    "batch-b/446cab155cd792398f9d": (
        "count-predicate-not-closed",
        "module-constant-not-closed",
    ),
    "batch-b/3c2b93c9545d8518e1f3": (
        "function-entry-not-closed",
        "function-globals-read",
    ),
    "batch-b/6a3bc02816cb70ee4042": ("module-constant-not-closed",),
    "batch-b/8b01b6d08e58aa5cce6f": (
        "function-entry-not-closed",
        "function-globals-read",
        "sink-helper-call",
    ),
    "batch-b/ae04f2973df030f612b9": ("module-constant-not-closed",),
    "batch-b/bf08b2218ca9cef1db2d": (
        "count-predicate-not-closed",
        "module-constant-not-closed",
    ),
}


@pytest.mark.parametrize(("locator", "expected"), sorted(_FROZEN_BATCH_REASONS.items()))
def test_frozen_count_cases_keep_full_sorted_reason_sets(
    project_root: Path, locator: str, expected: tuple[str, ...]
) -> None:
    batch, slug = locator.split("/")
    root = (
        project_root
        / "evaluation/development/dependence-growth-loop"
        / batch
        / "authoring/cases"
        / slug
    )
    description = (root / "data-description.md").read_text(encoding="utf-8")
    match = re.search(r"(?mi)^Independent unit column:[ \t]*([^\r\n]+)", description)
    assert match is not None
    source = (root / "workflow/analysis.py").read_text(encoding="ascii")
    data = (root / "data/input.csv").read_bytes()
    payload = DependenceRecognitionV2ShadowAdapter().inspect(
        _context(
            source,
            data,
            unit_column=match.group(1).strip(),
            data_path="data/input.csv",
        )
    )
    assert tuple(payload["abstention_reasons"]) == expected
