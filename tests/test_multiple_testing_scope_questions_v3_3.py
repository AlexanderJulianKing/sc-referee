from __future__ import annotations

import ast
import hashlib
import json
import runpy
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest

from sc_referee.core.ids import canonical_json, sha256_digest
from sc_referee.multiple_testing_scope_attestations_v1 import (
    ATTESTATION_PROFILE,
    ATTESTATION_PROFILE_VERSION,
    CERTAINTY_BASIS,
    COMPLETE_OPTION,
    parse_attestation_bytes,
)
from sc_referee.multiple_testing_scope_attestations_v3_3 import apply_attestation
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_3 import (
    analyze_code_csv_multiple_testing_dataflow,
)
from sc_referee.scientific_checks.multiple_testing_scope_questions_v1 import (
    ScopeQuestionRecords,
    SourceSpan,
    build_scope_question_records,
    locate_correction_scope_witness,
)
from sc_referee.scientific_checks.multiple_testing_scope_questions_v3_3 import (
    APGuidedRecheckContext,
    existing_complete_coverage_recheck,
)

_SWEEP = Path("evaluation/development/multitest-code-slice-v3_3/prototype-sweep").resolve()
_HARNESS = runpy.run_path(str(_SWEEP / "harness.py"))
all_cases = cast(Callable[[], tuple[Any, ...]], _HARNESS["all_cases"])
current_question_keys = cast(Callable[[], frozenset[str]], _HARNESS["current_question_keys"])
inputs = cast(Callable[..., dict[str, Any]], _HARNESS["inputs"])
reference_case = cast(Callable[[str], Any], _HARNESS["reference_case"])

_CONSUMPTION_ORACLE = Path(
    "evaluation/development/multitest-code-slice-v3_2/audit-fix-r1-oracle"
).resolve()
_FIXTURE_SOURCES = runpy.run_path(str(_CONSUMPTION_ORACLE / "fixture_sources.py"))
attestation_fixture_sources = cast(
    Callable[[], dict[str, tuple[str, bytes]]],
    _FIXTURE_SOURCES["attestation_fixture_sources"],
)
_ATTESTATION_ORACLE = json.loads(
    (_CONSUMPTION_ORACLE / "EXPECTED_ROWS.json").read_text(encoding="utf-8")
)
_ATTESTATION_ROWS = {row["fixture_name"]: row for row in _ATTESTATION_ORACLE["attestation_rows"]}
_ATTESTATION_SOURCES = attestation_fixture_sources()


def _context(values: dict[str, object]) -> APGuidedRecheckContext:
    return APGuidedRecheckContext(
        authorized_path=str(values["authorized_path"]),
        group_column=str(values["group_column"]),
        outcome_columns=tuple(values["outcome_columns"]),
        csv_header=tuple(values["csv_header"]),
        group_values=tuple(values["group_values"]),
        csv_content=bytes(values["csv_content"]),
    )


def test_no_attestation_question_census_is_exactly_25() -> None:
    before = current_question_keys()
    assert len(before) == 25
    observed: set[str] = set()
    for case in all_cases():
        values = inputs(case)
        content = values.pop("content")
        result = analyze_code_csv_multiple_testing_dataflow(content, **values)
        witness = locate_correction_scope_witness(
            content,
            qualifying_reason=result.reason or "",
            authorized_count=len(values["outcome_columns"]),
            outcome_columns=values["outcome_columns"],
        )
        if witness is not None:
            observed.add(case.key)
    # spec-30 remains an analyzer-level diagnostic only. The three terminal/helper movers had no
    # MT scope question, so the source-derived census remains exactly 25.
    assert observed - before == {"corpus:spec-30"}
    observed.remove("corpus:spec-30")
    assert not (before - observed)
    assert len(observed) == 25
    assert sum(key.startswith("E") for key in observed) == 16
    assert sum(key.startswith("corpus:") for key in observed) == 9


def test_ap_attestation_oracle_rows_are_exact_and_independent() -> None:
    assert len(_ATTESTATION_ROWS) == 3
    assert set(_ATTESTATION_ROWS) == set(_ATTESTATION_SOURCES)
    assert {row["derivation"]["design_clause"] for row in _ATTESTATION_ROWS.values()} == {
        "§11.2 — failed guided AP proof",
        "§6 rule 1 and §11.2 answer-removal equivalence",
        "§6 rule 4 and §11.2 answer-removal equivalence",
    }


@pytest.mark.parametrize(
    "case_key",
    (
        "E16:P2:7a43fa7b50f1b99e5034",
        "E16:P3:5a9c5b4377c33916d672",
        "E16:P4:9ced761b41ef93485acf",
    ),
)
def test_terminal_and_helper_proofs_never_become_answer_guided_clearance(
    case_key: str,
) -> None:
    values = inputs(reference_case(case_key))
    content = values.pop("content")
    result = analyze_code_csv_multiple_testing_dataflow(content, **values)
    assert result.reason is None
    assert result.facts is not None
    assert result.facts.correction_classification == "none"
    proof = existing_complete_coverage_recheck(
        content,
        source_span=SourceSpan(1, 1, 1, 2),
        authorized_count=len(values["outcome_columns"]),
        outcome_columns=tuple(values["outcome_columns"]),
        ap_context=_context(values),
    )
    assert proof.status == "unverified"
    assert proof.corrected_positions == ()


def _records(content: bytes, outcomes: tuple[str, ...]) -> ScopeQuestionRecords:
    witness = locate_correction_scope_witness(
        content,
        qualifying_reason="unresolved-manual-correction-present",
        authorized_count=len(outcomes),
        outcome_columns=outcomes,
    )
    assert witness is not None
    return build_scope_question_records(
        witness,
        run_id="audit:multiple-testing-ap-answer-removal-test",
        created_at="2026-08-29T00:00:00Z",
        source_snapshot_digest="sha256:" + "1" * 64,
        authority_binding_digest="sha256:" + "2" * 64,
        analysis_ref={"record_type": "file_record", "record_id": "file:analysis"},
        contract_ref={
            "record_type": "scientific_contract",
            "record_id": "scientific-contract:multiple-testing",
        },
        detector_manifest_digest="sha256:" + "3" * 64,
    )


def _node_span(node: ast.AST) -> SourceSpan:
    assert hasattr(node, "lineno")
    return SourceSpan(
        node.lineno,
        node.col_offset + 1,
        node.end_lineno or node.lineno,
        (node.end_col_offset or node.col_offset + 1) + 1,
    )


def _factor_span(content: bytes, correction_span: SourceSpan) -> SourceSpan:
    tree = ast.parse(content)
    roots = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.expr) and _node_span(node) == correction_span
    ]
    assert len(roots) == 1
    factors = [
        node
        for node in ast.walk(roots[0])
        if isinstance(node, ast.Name) and node.id == "FAMILY_SIZE"
    ]
    assert len(factors) == 1
    return _node_span(factors[0])


def _loaded_complete_answer(
    records: ScopeQuestionRecords,
    content: bytes,
) -> Any:
    question = records.question
    extensions = question["extensions"]
    factor_span = _factor_span(content, records.witness.source_span)
    value = {
        "profile": ATTESTATION_PROFILE,
        "profile_version": ATTESTATION_PROFILE_VERSION,
        "answers": [
            {
                "question_id": question["question_id"],
                "source_snapshot_digest": extensions["x-source-snapshot-digest"],
                "analysis_content_digest": extensions["x-analysis-content-digest"],
                "question_evidence_digest": extensions["x-question-evidence-digest"],
                "authority_binding_digest": extensions["x-authority-binding-digest"],
                "answer": COMPLETE_OPTION,
                "respondent": {
                    "actor_kind": "human",
                    "actor_id": "human:mt32-answer-removal-fixture",
                },
                "certainty": {"level": "explicit", "basis": CERTAINTY_BASIS},
                "timestamp_status": "unavailable",
                "supersedes_answer_digest": None,
                "claimed_correction": {
                    "path": "analysis.py",
                    "analysis_content_digest": sha256_digest(content),
                    "source_span": records.witness.source_span.to_dict(),
                    "factor": {
                        "kind": "contract_family_size",
                        "value": records.witness.authorized_count,
                        "source_span": factor_span.to_dict(),
                    },
                },
            }
        ],
    }
    return parse_attestation_bytes(canonical_json(value).encode())


@pytest.mark.parametrize(
    "name",
    (
        "answer-removal-equivalence-ap-proving",
        "answer-removal-equivalence-ap-failing",
    ),
)
def test_ap_answer_removal_equivalence_uses_distinct_entry_points(name: str) -> None:
    row = _ATTESTATION_ROWS[name]
    case_key, source = _ATTESTATION_SOURCES[name]
    assert "sha256:" + hashlib.sha256(source).hexdigest() == row["fixture_source_sha256"]
    values = inputs(reference_case(case_key), source)
    content = values.pop("content")
    outcomes = tuple(values["outcome_columns"])
    records = _records(content, outcomes)

    # Guided execution enters through the answer-bearing attestation application.
    application = apply_attestation(
        _loaded_complete_answer(records, content),
        question=records.question,
        initial_concern=records.concern,
        analysis_content=content,
        outcome_columns=outcomes,
        created_at="2026-08-29T00:00:00Z",
        ap_context=_context(values),
    )
    assert application.guided_proof is not None

    # Answer removal is a separate entry point whose proof root comes from the source-derived
    # question witness; no LoadedAttestation or claimed correction enters this invocation.
    answer_removed = existing_complete_coverage_recheck(
        content,
        source_span=records.witness.source_span,
        authorized_count=len(outcomes),
        outcome_columns=outcomes,
        ap_context=_context(values),
    )
    expected_positions = tuple(row["expected_corrected_positions"])
    assert application.guided_proof.status == row["expected_proof_status"]
    assert application.guided_proof.corrected_positions == expected_positions
    assert answer_removed.status == row["expected_proof_status"]
    assert answer_removed.corrected_positions == expected_positions
    assert application.guided_proof.proof_digest == answer_removed.proof_digest
    # Mutation-kill: adding any answer-guided-only corrected position breaks this equality (or
    # forces the application back to unverified) while the independent proof stays unchanged.
    assert application.guided_proof == answer_removed
    assert application.lock_receipt["guided_proof"]["answer_removal_equivalent"] is True
